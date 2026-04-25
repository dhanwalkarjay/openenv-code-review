---
title: OpenEnv Code Review
emoji: robot
colorFrom: blue
colorTo: green
sdk: docker
app_file: backend/api/main.py
pinned: false
---

# OpenEnv Local RL Code Repair

This project is a small, local, OpenEnv-style RL system for Python code repair.
It does not call hosted inference APIs from the demo path.

## Architecture

```text
Frontend
-> FastAPI backend
-> local RL repair policy
-> OpenEnv-style environment
-> reward engine
-> JSON response + reward graph
```

Environment contract:

- `reset(task_type)`
- `step(action)`
- `state()`

Action shape:

```json
{ "fixed_code": "def safe_div(a, b):\n    ..." }
```

## Reward

- `+1.0` all tests pass
- `+0.5` syntax correct
- `+0.3` measurable improvement
- `-0.5` syntax error
- `-0.2` no meaningful change

## Train

```powershell
.\.venv311\Scripts\python.exe training_script.py --train-steps 50 --output-dir artifacts/rl_run
```

Optional tiny TRL GRPO smoke run using cached `sshleifer/tiny-gpt2`:

```powershell
$env:PYTHONUTF8="1"
$env:PYTHONIOENCODING="utf-8"
.\.venv311\Scripts\python.exe training_script.py --train-steps 50 --grpo-steps 5 --output-dir artifacts/rl_run
```

Artifacts:

- `artifacts/rl_run/reward_curve.png`
- `artifacts/rl_run/training_summary.json`
- `artifacts/rl_run/training_progress.jsonl`
- `artifacts/rl_policy.json`

## Evaluate

```powershell
.\.venv311\Scripts\python.exe evaluate_script.py --policy artifacts/rl_policy.json --output artifacts/eval_report.json
```

## Demo

```powershell
.\.venv311\Scripts\python.exe run_demo.py --task medium --policy artifacts/rl_policy.json
```

## Run UI

```powershell
.\.venv311\Scripts\python.exe -m uvicorn backend.api.main:app --host 127.0.0.1 --port 8000
```

Open:

```text
http://127.0.0.1:8000
```
