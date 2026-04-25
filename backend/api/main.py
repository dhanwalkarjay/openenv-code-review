from typing import Dict, List

from fastapi import Body, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from backend.api.ui import get_ui
from env.environment import CodeReviewEnv, TASKS


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
        "info": info
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
    # Baseline: unchanged code policy (no-op fixer).
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
