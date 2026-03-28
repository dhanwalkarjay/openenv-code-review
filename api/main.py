import json
import subprocess

from fastapi import FastAPI
from api.ui import get_ui
from env.environment import CodeReviewEnv
from env.models import Action
from fastapi import Body

app = FastAPI()
env = CodeReviewEnv()

@app.get("/")
def ui():
    return get_ui()

@app.post("/reset")
def reset(task: str = Body(default="easy")):
    return env.reset(task)

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
def baseline():
    try:
        result = subprocess.run(
            ["python", "inference.py"],
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )

        output = result.stdout.strip()
        if not output and result.stderr.strip():
            return {
                "error": "inference.py produced no stdout",
                "stderr": result.stderr.strip(),
                "returncode": result.returncode,
            }

        try:
            parsed = json.loads(output.replace("'", '"'))
        except Exception:
            parsed = {"raw_output": output}

        if result.returncode != 0:
            parsed["returncode"] = result.returncode
            if result.stderr.strip():
                parsed["stderr"] = result.stderr.strip()

        return parsed
    except Exception as exc:
        return {"error": str(exc)}
