from typing import Any, Dict, List

from fastapi import Body, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
import httpx
import os

from backend.api.ui import get_ui
from env.environment import CodeReviewEnv, TASKS
from env.policy import load_policy_state, normalize_code, select_action, update_policy_state


class MultiAgentAction(BaseModel):
    reviewer_issues: List[str] = Field(default_factory=list)
    fixed_code: str


class ResetRequest(BaseModel):
    task_type: str = "easy"


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

env = CodeReviewEnv()


async def _generate_model_fix(
    current_code: str,
    instruction: str,
    attempt_id: int,
    temperature: float,
) -> str | None:
    hf_token = os.environ.get("HF_TOKEN", "")
    if not hf_token:
        return None

    model_id = "dhanwalkarjay/openenv-code-review-model"
    system_prompt = (
        "You are an expert Python debugger. "
        "Given buggy Python code, return ONLY corrected Python code. "
        "No explanations and no markdown fences."
    )
    user_prompt = (
        f"Instruction: {instruction}\n"
        f"Attempt: {attempt_id}\n\n"
        "Current code:\n"
        f"{current_code}\n\n"
        "Return an improved fix candidate."
    )

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"https://api-inference.huggingface.co/models/{model_id}/v1/chat/completions",
                headers={"Authorization": f"Bearer {hf_token}"},
                json={
                    "model": model_id,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "max_tokens": 300,
                    "temperature": temperature,
                },
            )
        if resp.status_code == 200:
            fixed_code = resp.json()["choices"][0]["message"]["content"]
            return fixed_code.replace("```python", "").replace("```", "").strip()
    except Exception:
        return None
    return None


@app.get("/")
def ui():
    return get_ui()


@app.post("/reset")
def reset(payload: ResetRequest = Body(default=ResetRequest())):
    return env.reset(task_type=payload.task_type)


@app.post("/step")
def step(action: MultiAgentAction):
    obs, reward, done, info = env.step(action)
    return {
        "observation": obs,
        "reward": reward,
        "done": done,
        "info": info,
    }


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
    results: Dict[str, float] = {}
    for task in TASKS.keys():
        obs = env.reset(task_type=task)
        total_reward = 0.0
        for _ in range(obs["max_steps"]):
            obs, reward, done, _ = env.step(
                {
                    "reviewer_issues": ["No-op baseline reviewer."],
                    "fixed_code": obs["current_code"],
                }
            )
            total_reward += reward
            if done:
                break
        results[task] = round(total_reward, 4)
    return {
        "mode": "baseline_noop",
        "results": results,
        "note": "Use training_script.py to generate before/after and reward curve.",
    }

@app.get("/generate")
def generate(difficulty: str = "medium", seed: int = None):
    from env.task_generator import generate_task
    import random
    s = seed if seed is not None else random.randint(0, 100_000)
    task = generate_task(difficulty=difficulty, seed=s)
    if task is None:
        return {"error": "Could not generate task"}
    return {
        "task_id":    task.task_id,
        "difficulty": task.difficulty,
        "instruction":task.instruction,
        "buggy_code": task.buggy_code,
        "bug_type":   task.bug_type,
        "tests":      task.tests,
    }


@app.post("/demo-fix")
async def demo_fix(payload: dict = Body(...)):
    """Model generation endpoint used by the UI for iterative code fixes.

    This endpoint should not mutate the shared global env episode state.
    """
    task_type = payload.get("task_type", "easy")
    attempt_id = int(payload.get("attempt_id", 1))
    temperature = float(payload.get("temperature", 0.1))
    temperature = max(0.0, min(1.2, temperature))
    current_code = str(payload.get("current_code", "") or "").strip()
    instruction = str(payload.get("instruction", "") or "").strip()
    score_candidate = bool(payload.get("score_candidate", False))

    if not current_code or not instruction:
        obs = env.reset(task_type=task_type)
        current_code = current_code or obs["current_code"]
        instruction = instruction or obs["instruction"]

    hf_token = os.environ.get("HF_TOKEN", "")
    model_id = "dhanwalkarjay/openenv-code-review-model"

    system_prompt = (
        "You are an expert Python debugger. "
        "Given a buggy Python function, return ONLY the corrected Python code. "
        "No explanation. No markdown fences. Just valid Python."
    )
    user_prompt = (
        f"Instruction: {instruction}\n"
        f"Attempt: {attempt_id}\n\n"
        "Current code:\n"
        f"{current_code}\n\n"
        "Return an improved fix candidate."
    )

    fixed_code = None

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"https://api-inference.huggingface.co/models/{model_id}/v1/chat/completions",
                headers={"Authorization": f"Bearer {hf_token}"},
                json={
                    "model": model_id,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "max_tokens": 300,
                    "temperature": temperature,
                },
            )
        if resp.status_code == 200:
            fixed_code = resp.json()["choices"][0]["message"]["content"]
            fixed_code = fixed_code.replace("```python", "").replace("```", "").strip()
    except Exception:
        pass

    # Honest fallback: keep current code unchanged when inference fails.
    if not fixed_code:
        fixed_code = current_code

    reward = None
    done = None
    info: Dict[str, Any] = {}
    if score_candidate:
        # Use a temporary env so shared episode state is unaffected.
        temp_env = CodeReviewEnv()
        temp_env.reset(task_type=task_type)
        _, reward, done, info = temp_env.step({
            "reviewer_issues": [],
            "fixed_code": fixed_code,
        })

    return {
        "task_type": task_type,
        "instruction": instruction,
        "current_code": current_code,
        "fixed_code": fixed_code,
        "reward": reward,
        "tests_passed": info.get("tests_passed"),
        "tests_total": info.get("tests_total"),
        "all_tests_passed": info.get("all_tests_passed"),
        "done": done,
    }


@app.post("/run-rl-episode")
async def run_rl_episode(payload: dict = Body(...)):
    """Run a real RL-like episode: action -> tests -> reward -> policy update."""
    task_type = str(payload.get("task_type", "easy"))
    max_steps = int(payload.get("max_steps", 3))
    max_steps = max(1, min(5, max_steps))

    obs = env.reset(task_type=task_type)
    instruction = obs.get("instruction", "")
    temperatures = [0.15, 0.25, 0.35, 0.45, 0.55]
    tried_action_ids: set[str] = set()
    history: List[Dict[str, Any]] = []

    for step_idx in range(max_steps):
        current_code = str(obs.get("current_code", ""))
        temperature = temperatures[min(step_idx, len(temperatures) - 1)]

        model_candidate = await _generate_model_fix(
            current_code=current_code,
            instruction=instruction,
            attempt_id=step_idx + 1,
            temperature=temperature,
        )

        source = "model"
        action_id = "model_output"
        candidate_code = (model_candidate or "").strip() or current_code

        # If model is unchanged/empty, explore with local RL policy actions.
        if normalize_code(candidate_code) == normalize_code(current_code):
            action = select_action(current_code, tried_action_ids=tried_action_ids)
            action_id = str(action.get("action_id", "policy_action"))
            tried_action_ids.add(action_id)
            candidate_code = str(action.get("fixed_code", current_code))
            source = "policy"

        previous_code = current_code
        obs, reward, done, info = env.step({"reviewer_issues": [], "fixed_code": candidate_code})

        # Online policy update from reward signal.
        policy_state = update_policy_state(action_id, float(reward))

        output_code = str(obs.get("current_code", candidate_code))
        improved = normalize_code(output_code) != normalize_code(previous_code)

        history.append(
            {
                "step": step_idx + 1,
                "source": source,
                "action_id": action_id,
                "temperature": temperature,
                "input_code": previous_code,
                "candidate_code": candidate_code,
                "output_code": output_code,
                "reward": float(reward),
                "tests_passed": int(info.get("tests_passed", 0)),
                "tests_total": int(info.get("tests_total", 0)),
                "all_tests_passed": bool(info.get("all_tests_passed", False)),
                "improved": improved,
                "epsilon": float(policy_state.get("epsilon", 0.0)),
            }
        )

        if done:
            break

    policy_state = load_policy_state()
    return {
        "task_type": task_type,
        "title": obs.get("title"),
        "instruction": instruction,
        "buggy_code": obs.get("buggy_code"),
        "final_code": obs.get("current_code"),
        "final_reward": float(obs.get("last_step_reward", history[-1]["reward"] if history else 0.0)),
        "total_reward": float(obs.get("total_reward", 0.0)),
        "tests_passed": int(obs.get("tests_passed", 0)),
        "tests_total": int(obs.get("tests_total", 0)),
        "done": bool(obs.get("done", False)),
        "history": history,
        "policy": {
            "epsilon": float(policy_state.get("epsilon", 0.0)),
            "total_steps": int(policy_state.get("metadata", {}).get("total_steps", 0)),
        },
    }