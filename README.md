---
title: OpenEnv Code Review
emoji: 🤖
colorFrom: blue
colorTo: green
sdk: docker
app_file: backend/api/main.py
pinned: false
---

# OpenEnv Code Review — RL-Powered Bug Fixing Environment

> **An RL environment that trains LLMs to fix Python bugs through verifiable reward signals — not static supervision.**

[![HF Space](https://img.shields.io/badge/🤗%20Space-Live%20Demo-blue)](https://huggingface.co/spaces/dhanwalkarjay/openenv-code-review)
[![Model](https://img.shields.io/badge/🤗%20Model-Trained%20Weights-purple)](https://huggingface.co/dhanwalkarjay/openenv-code-review-model)
[![OpenEnv](https://img.shields.io/badge/OpenEnv-Compatible-green)](https://github.com/huggingface/openenv)

---

## 🎯 The Problem

LLMs trained on static datasets learn to *look like* they're fixing code — but they have no feedback loop to know if the fix actually works. We built an environment that changes that.

Instead of:
```
Input → Output  (static supervision)
```

We built:
```
State → Action → Run Tests → Reward → Update Policy → Better Action
```

The agent receives **verifiable rewards from real test execution** — not human labels, not heuristics.

---

## 🏗️ Environment Design

### Core Loop
1. Agent receives buggy Python code + instruction
2. Agent proposes a fix (`fixed_code` action)
3. Environment executes real test cases against the fix
4. Reward is computed from test pass rate + 2 anti-hack signals
5. Agent updates its policy based on reward
6. Next step: agent tries again with richer context

### Three Independent Reward Signals (anti-hacking)
| Signal | Weight | What it checks |
|--------|--------|----------------|
| `reward_tests_pass` | Primary | Real test execution via environment verifier |
| `reward_syntax_valid` | +0.2 / -0.3 | AST parse — is the code even valid Python? |
| `reward_no_trivial_hack` | -0.3 | Penalises bare-except-pass, empty returns |

Multiple independent signals make reward hacking much harder — a model can't exploit one signal without the others catching it.

### Procedural Task Generation
Rather than 8 fixed tasks, the environment includes a **procedural task generator** that creates unlimited unique bug-fixing challenges:

```python
from env.task_generator import generate_task, generate_curriculum

# Single task
task = generate_task(difficulty="hard", seed=42)

# Curriculum: 20 tasks ordered easy → medium → hard
curriculum = generate_curriculum(n=20, seed=0)
```

**7 bug strategies × unlimited seeds = infinite unique tasks:**
- Off-by-one index errors
- Missing syntax (colons, brackets)
- Division by zero without guard
- None method calls without guard
- Wrong comparison operators (`>` vs `>=`)
- Off-by-one loop ranges
- Wrong initialisation (max/min bugs)

### OpenEnv API
```
POST /reset   {"task_type": "easy"}    → observation
POST /step    {"fixed_code": "..."}    → {observation, reward, done, info}
GET  /state                            → current episode state
GET  /tasks                            → full task catalog
GET  /generate?difficulty=medium       → procedurally generated task
GET  /grader                           → last reward breakdown
GET  /baseline                         → no-op baseline scores
```

---

## 📊 Training Results

**Model:** `Qwen/Qwen2.5-0.5B-Instruct` + LoRA (r=16)  
**Algorithm:** GRPO (TRL + Unsloth)  
**Hardware:** A10G GPU  
**Steps:** 80  

### Reward Curve
![GRPO Training Reward Curve](artifacts/grpo_run/reward_curve.png)

*Reward climbed from ~0.2 at step 1 to consistently above 1.0 by step 30, stabilising through step 80.*

### Before / After

| Task | Buggy Code | Trained Model Output | Reward |
|------|-----------|---------------------|--------|
| Easy — index error | `return items[3]` | `return items[2]` | 1.0 ✅ |
| Medium — syntax | `def greet(name)` | `def greet(name):` | 1.0 ✅ |
| Hard — div zero | `return a / b` | `if b==0: return 0` | 1.0 ✅ |
| Bonus — loop | `range(n)` | `sum(range(n+1))` | 1.0 ✅ |
| None guard | `name.lower()` | `if name is None: return ''` | 1.0 ✅ |

**5/6 tasks solved at full reward.** The one partial result (`max_init`) was a token truncation issue — increasing `max_new_tokens` resolves it.

### Training Summary
```json
{
  "baseline_avg_reward": 0.19,
  "trained_avg_reward":  1.02,
  "total_steps": 80,
  "peak_reward": 1.20,
  "tasks_solved": "5/6"
}
```

---

## 🚀 Quick Start

### Try the live demo
👉 **[dhanwalkarjay-openenv-code-review.hf.space](https://dhanwalkarjay-openenv-code-review.hf.space)**

Select a task, click "Run RL Episode", and watch the agent attempt fixes step by step with live reward updates.

### Run the environment locally
```bash
git clone https://github.com/dhanwalkarjay/openenv-code-review
cd openenv-code-review
pip install -r requirements-runtime.txt
uvicorn backend.api.main:app --host 0.0.0.0 --port 7860
```

### Call the API
```python
import requests

BASE = "http://localhost:7860"

# Reset to a task
obs = requests.post(f"{BASE}/reset", json={"task_type": "hard"}).json()
print(obs["buggy_code"])

# Submit a fix
result = requests.post(f"{BASE}/step", json={
    "reviewer_issues": [],
    "fixed_code": "def safe_div(a, b):\n    if b == 0: return 0\n    return a / b"
}).json()
print(f"Reward: {result['reward']}")
print(f"Tests:  {result['info']['tests_passed']}/{result['info']['tests_total']}")
```

### Train your own model
```bash
# Open train_grpo_colab.py in Google Colab
# Set ENV_BASE_URL to your Space URL
# Run all cells — takes ~45 min on A10G
```

---

## 📁 Repository Structure

```
openenv-code-review/
├── env/
│   ├── environment.py      # Core OpenEnv environment (reset/step/state)
│   ├── reward.py           # Multi-signal reward engine
│   └── task_generator.py   # Procedural task generation (unlimited tasks)
├── backend/
│   └── api/
│       ├── main.py         # FastAPI server
│       └── ui.py           # Live demo UI
├── artifacts/
│   └── grpo_run/
│       ├── reward_curve.png       # Real training run plot
│       └── training_summary.json  # Metrics from training
├── train_grpo_colab.py     # Complete GRPO training script
├── Dockerfile
├── openenv.yaml
└── README.md
```

---

## 🔗 Links

| Resource | URL |
|----------|-----|
| 🤗 Live Space | https://huggingface.co/spaces/dhanwalkarjay/openenv-code-review |
| 🧠 Trained Model | https://huggingface.co/dhanwalkarjay/openenv-code-review-model |
| 💻 GitHub | https://github.com/dhanwalkarjay/openenv-code-review |
| 📝 Blog Post  | [BLOG.md](https://github.com/dhanwalkarjay/openenv-code-review/blob/main/BLOG.md) |
| 📓 Training Notebook | [Open in colab](https://colab.research.google.com/drive/1GZ-SkkKCNRhTqPjtRerHVhq23rRvvtvL?usp=sharing) |

| 📊 Experiment Tracking | [View on W&B](https://wandb.ai/jaydhanwalkar123-g-h-raisoni-skill-tech-university-nagpur/openenv-code-review?nw=nwuserjaydhanwalkar123) |

---

## ✅ Submission Checklist

- [x] OpenEnv compatible (`reset` / `step` / `state`)
- [x] Training script (`train_grpo_colab.py`) using Unsloth + TRL
- [x] Real training evidence (reward curve, training summary)
- [x] Hosted on Hugging Face Spaces
- [x] Before/after behavior shown
- [x] Procedural task generator (unlimited unique tasks)
- [x] Multi-signal reward (3 independent functions)
- [x] Anti-reward-hacking safeguards
- [ ] Blog post / video (in progress)