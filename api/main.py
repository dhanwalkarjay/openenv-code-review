from fastapi import FastAPI
from env.environment import CodeReviewEnv
from env.models import Action
from baseline.run import run_baseline

app = FastAPI()
env = CodeReviewEnv()

@app.get("/")
def home():
    return {"message": "OpenEnv Code Review Environment"}

@app.get("/reset")
def reset(task: str = "easy"):
    return {"observation": env.reset(task), "done": False}

@app.post("/step")
def step(action: Action):
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
def baseline(model: str = "gpt-4o-mini"):
    try:
        return run_baseline(model=model)
    except Exception as exc:
        return {
            "error": str(exc),
            "hint": "Set OPENAI_API_KEY before calling /baseline.",
        }