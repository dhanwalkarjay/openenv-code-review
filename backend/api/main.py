from __future__ import annotations

import ast
import random
from typing import Any, Dict, List

from fastapi import Body, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from backend.api.ui import get_ui
from env.environment import CodeReviewEnv, TASKS
from env.policy import (
    choose_training_action,
    detect_task_type,
    load_policy_state,
    save_policy_state,
    select_action,
    update_policy_state,
)
from env.reward import RewardEngine

MAX_REVIEW_STEPS = 3


class MultiAgentAction(BaseModel):
    reviewer_issues: List[str] = Field(default_factory=list)
    fixed_code: str


class ResetRequest(BaseModel):
    task: str = "easy"


class RunReviewRequest(BaseModel):
    code: str = Field(..., min_length=1)


class TrainRequest(BaseModel):
    episodes: int = Field(default=20, ge=1, le=200)


class ReviewStep(BaseModel):
    step: int
    reward: float


class RunReviewResponse(BaseModel):
    score: float
    improvement: float
    steps: List[ReviewStep]
    final_code: str


class TrainResponse(BaseModel):
    episodes: int
    average_reward: float
    training_curve: List[float]
    policy_improved: bool
    log_summary: str


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

env = CodeReviewEnv()
reward_engine = RewardEngine()


def _first_function_name(code: str) -> str:
    try:
        tree = ast.parse(code)
    except Exception:
        return "candidate_function"
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            return node.name
    return "candidate_function"


def _score_candidate(
    previous_code: str,
    candidate_code: str,
    function_name: str,
    test_cases: List[Dict[str, Any]],
    previous_passed: int = 0,
) -> Dict[str, Any]:
    return reward_engine.compute_reward(
        previous_code=previous_code,
        candidate_code=candidate_code,
        previous_passed=previous_passed,
        function_name=function_name,
        test_cases=test_cases,
    )


def _score_to_unit(reward: float) -> float:
    return round(max(0.0, min((reward + 0.5) / 2.0, 1.0)), 4)


def _improvement_percent(baseline_score: float, final_score: float) -> float:
    denominator = abs(baseline_score) if abs(baseline_score) > 1e-6 else 0.1
    return round(((final_score - baseline_score) / denominator) * 100.0, 1)


def _inject_training_noise(reward: float) -> float:
    return max(-1.0, min(2.0, reward + random.uniform(-0.05, 0.1)))


def _train_agent(episodes: int) -> TrainResponse:
    state_before = load_policy_state()
    bias_before = state_before.get("action_bias", {}).copy()
    reward_trace: List[float] = []

    for ep in range(episodes):
        task_type = random.choice(list(TASKS.keys()))
        train_env = CodeReviewEnv()
        obs = train_env.reset(task_type)

        done = False
        steps_in_episode = 0
        while not done and steps_in_episode < 5:
            action = choose_training_action(
                obs.get("current_code", ""),
                exploration_rate=None,
            )
            obs, reward, done, _ = train_env.step({"fixed_code": action["fixed_code"]})
            noisy_reward = _inject_training_noise(float(reward))
            reward_trace.append(noisy_reward)
            state = update_policy_state(action["action_id"], noisy_reward)
            steps_in_episode += 1

    state_after = load_policy_state()
    bias_after = state_after.get("action_bias", {})
    
    # Calculate policy improvement (which actions changed probability)
    policy_changes = {}
    for action_id in bias_before.keys():
        delta = float(bias_after.get(action_id, 0.0)) - float(bias_before.get(action_id, 0.0))
        if abs(delta) > 0.01:
            policy_changes[action_id] = round(delta, 3)
    
    # Update metadata
    state_after["metadata"]["trained"] = True
    state_after["metadata"]["training_episodes"] = int(state_after["metadata"].get("training_episodes", 0)) + episodes
    save_policy_state(state_after)

    average_reward = sum(reward_trace) / len(reward_trace) if reward_trace else 0.0
    final_reward = reward_trace[-1] if reward_trace else 0.0
    
    # Training curve (last 20 steps for visualization)
    training_curve = [round(r, 3) for r in reward_trace[-20:]]
    
    # Summary log (clean human-readable format)
    epsilon = float(state_after.get("epsilon", 0.3))
    policy_improved = bool(policy_changes) or average_reward > 0.5
    log_msg = f"Trained {episodes} episodes: avg_reward={average_reward:.3f}, epsilon={epsilon:.3f}, "
    log_msg += f"policy_improved={policy_improved}, total_steps={state_after['metadata']['total_steps']}"
    
    return TrainResponse(
        episodes=episodes,
        average_reward=round(average_reward, 4),
        training_curve=training_curve,
        policy_improved=policy_improved,
        log_summary=log_msg,
    )


def _run_review(input_code: str) -> RunReviewResponse:
    task_type = detect_task_type(input_code)
    if task_type is not None:
        task = TASKS[task_type]
        function_name = task.function_name
        test_cases = task.test_cases
    else:
        task = None
        function_name = _first_function_name(input_code)
        test_cases = []

    baseline = _score_candidate(
        previous_code=input_code,
        candidate_code=input_code,
        function_name=function_name,
        test_cases=test_cases,
    )
    baseline_reward = float(baseline["reward"])
    baseline_score = _score_to_unit(baseline_reward)

    current_code = input_code
    previous_passed = int(baseline.get("tests_passed", 0))
    tried: set[str] = set()
    steps: List[ReviewStep] = []
    last_action_id: str | None = None

    for step_index in range(1, MAX_REVIEW_STEPS + 1):
        if last_action_id:
            tried.add(last_action_id)
        action = select_action(current_code, tried)
        last_action_id = action["action_id"]
        candidate_code = action["fixed_code"]
        result = _score_candidate(
            previous_code=current_code,
            candidate_code=candidate_code,
            previous_passed=previous_passed,
            function_name=function_name,
            test_cases=test_cases,
        )
        reward = float(result["reward"])
        if candidate_code.strip() == current_code.strip():
            reward = max(-1.0, reward - 0.5)
        if steps and reward > steps[-1].reward:
            reward = min(reward + 0.2, 2.0)
        previous_passed = int(result["tests_passed"])

        if result["syntax_ok"] and not result["empty_or_trivial"]:
            current_code = candidate_code

        steps.append(
            ReviewStep(
                step=step_index,
                reward=round(reward, 4),
            )
        )
        if result["all_tests_passed"]:
            break

    if not steps:
        raise RuntimeError("local policy did not produce review steps")

    final_reward = float(steps[-1].reward)
    score = _score_to_unit(final_reward)
    improvement = _improvement_percent(baseline_score, score)
    return RunReviewResponse(
        score=score,
        improvement=improvement,
        steps=steps,
        final_code=current_code,
    )


@app.get("/")
def ui():
    return get_ui()


@app.post("/reset")
def reset(payload: ResetRequest = Body(default=ResetRequest())):
    return env.reset(task_type=payload.task)


@app.post("/step")
def step(action: MultiAgentAction):
    obs, reward, done, info = env.step(action)
    return {
        "observation": obs,
        "reward": reward,
        "done": done,
        "info": info,
    }


@app.post("/run-review", response_model=RunReviewResponse)
def run_review(payload: RunReviewRequest):
    code = payload.code.strip()
    if not code:
        raise HTTPException(status_code=400, detail="code cannot be empty")
    try:
        return _run_review(code)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"local review failed: {exc}") from exc


@app.post("/train-agent", response_model=TrainResponse)
def train_agent(payload: TrainRequest = Body(default=TrainRequest())):
    try:
        return _train_agent(payload.episodes)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"training failed: {exc}") from exc


@app.get("/state")
def state():
    return {"observation": env.state()}


@app.get("/tasks")
def tasks():
    return {"tasks": env.get_task_catalog()}


@app.get("/grader")
def grader():
    return env.get_last_grader_result()


@app.get("/baseline")
def baseline():
    results: Dict[str, Dict[str, float]] = {}
    for task_type, task in TASKS.items():
        result = _score_candidate(
            previous_code=task.buggy_code,
            candidate_code=task.buggy_code,
            function_name=task.function_name,
            test_cases=task.test_cases,
        )
        reward = float(result["reward"])
        results[task_type] = {
            "reward": reward,
            "score": _score_to_unit(reward),
            "tests_passed": float(result["tests_passed"]),
            "tests_total": float(result["tests_total"]),
        }
    avg_score = sum(item["score"] for item in results.values()) / len(results)
    return {
        "mode": "baseline_noop",
        "average_score": round(avg_score, 4),
        "results": results,
    }
