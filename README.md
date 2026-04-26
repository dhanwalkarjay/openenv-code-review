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

> **A reinforcement learning environment where an agent learns to fix Python bugs using real execution-based reward signals — not static supervision.**

[![HF Space](https://img.shields.io/badge/🤗%20Space-Live%20Demo-blue)](https://huggingface.co/spaces/dhanwalkarjay/openenv-code-review)
[![Model](https://img.shields.io/badge/🤗%20Model-Trained%20Weights-purple)](https://huggingface.co/dhanwalkarjay/openenv-code-review-model)
[![OpenEnv](https://img.shields.io/badge/OpenEnv-Compatible-green)](https://github.com/huggingface/openenv)

---

## 🎯 Problem

Traditional LLM-based code tools generate fixes **without feedback**. They:

* Don’t verify correctness via execution
* Don’t improve over time
* Repeat mistakes across tasks

👉 In short: **they don’t learn — they predict.**

---

## 💡 Solution

We build a **reinforcement learning environment** where an agent:

```
State → Action → Execute Tests → Reward → Learn → Improve
```

Instead of guessing fixes, the agent:

* Tries solutions
* Gets real feedback from test execution
* Learns which fixes actually work

---

## 🏗️ Environment Design

### Core Loop

1. Receive buggy Python code
2. Propose a fix (`fixed_code`)
3. Execute test cases
4. Compute reward
5. Update policy
6. Repeat

---

### 🧠 State

* Buggy code
* Task difficulty (easy / medium / hard)

### ⚡ Action

* Modified code (fix attempt)

### 🎯 Reward (Multi-Signal)

| Signal            | Purpose              |
| ----------------- | -------------------- |
| Test pass rate    | Correctness          |
| Syntax validity   | Prevent invalid code |
| Anti-hack penalty | Avoid trivial cheats |

---

### 🧪 Procedural Task Generation

Instead of fixed problems, we generate tasks dynamically:

* Off-by-one errors
* Syntax bugs
* Division by zero
* None handling
* Loop mistakes
* Comparison bugs
* Initialization issues

👉 Result: **diverse, scalable training environment**

---

## ⚙️ Training vs Live Demo

This project uses a **two-phase RL setup**:

### 🧠 1. Offline Training (Real RL)

* Algorithm: **GRPO (Group Relative Policy Optimization)**
* Framework: **Hugging Face TRL + Unsloth**
* Runs in **Google Colab (GPU)**
* Produces:

  * Reward curves
  * Training logs
  * Improved policy

---

### ⚡ 2. Live Demo (Hugging Face Space)

The Space provides:

* Environment interaction
* Step-by-step agent behavior
* Real-time reward feedback

⚠️ Important:

* No heavy model training happens in the UI
* Only inference + environment reward loop
* Lightweight policy updates for visualization

---

## 📊 Training Results

**Model:** Qwen2.5-0.5B-Instruct (LoRA)
**Algorithm:** GRPO
**Steps:** 80

### 📈 Reward Curve

![Reward Curve](artifacts/grpo_run/reward_curve.png)

👉 Reward improves from ~0.2 → 1.0+

---

### 🧪 Before vs After

| Scenario        | Result                       |
| --------------- | ---------------------------- |
| Before Training | ❌ Fails tests (~0.2 reward)  |
| After Training  | ✅ Passes tests (~1.0 reward) |

---

### 📊 Training Summary

```
Baseline reward: ~0.19  
Trained reward:  ~1.02  
Improvement:     +400%  
Tasks solved:    5/6  
```

---

## 📈 Evidence of Learning

The agent demonstrates real RL behavior:

* Reward increases over time
* Exploration → exploitation transition
* Stable convergence

### Artifacts:

* `artifacts/grpo_run/reward_curve.png`
* `artifacts/grpo_run/training_summary.json`

👉 Confirms **actual learning**, not static outputs.

---

## 🚀 Live Demo

👉 https://huggingface.co/spaces/dhanwalkarjay/openenv-code-review

Try:

* Select a task
* Click **“Watch Agent Learn”**
* Observe step-by-step improvement

---

## 🧠 Training (Reproducible)

Run training yourself:

👉 https://colab.research.google.com/drive/1GZ-SkkKCNRhTqPjtRerHVhq23rRvvtvL

### Setup

* GRPO + TRL + Unsloth
* Runs on Colab GPU (~45 min)

---

## 🛠️ Local Setup

```bash
git clone https://github.com/dhanwalkarjay/openenv-code-review
cd openenv-code-review
pip install -r requirements-runtime.txt
uvicorn backend.api.main:app --host 0.0.0.0 --port 7860
```

---

## 🔌 API Example

```python
import requests

BASE = "http://localhost:7860"

obs = requests.post(f"{BASE}/reset", json={"task_type": "easy"}).json()

result = requests.post(f"{BASE}/step", json={
    "fixed_code": "def safe_div(a,b):\n if b==0:return 0\n return a/b"
}).json()

print(result["reward"])
```

---

## 📁 Project Structure

```
openenv-code-review/
├── env/
├── backend/
├── artifacts/
├── train_grpo_colab.py
├── README.md
```

---

## 🔗 Links

* 🤗 Space: https://huggingface.co/spaces/dhanwalkarjay/openenv-code-review
* 🧠 Model: https://huggingface.co/dhanwalkarjay/openenv-code-review-model
* 💻 GitHub: https://github.com/dhanwalkarjay/openenv-code-review
* 📓 Colab: https://colab.research.google.com/drive/1GZ-SkkKCNRhTqPjtRerHVhq23rRvvtvL
* 📊 W&B: https://wandb.ai/jaydhanwalkar123-g-h-raisoni-skill-tech-university-nagpur/openenv-code-review

---

## 🎥 Demo / Writeup

* 🎥 Demo Video: *(add YouTube link here)*
* 📝 Blog: https://github.com/dhanwalkarjay/openenv-code-review/blob/main/BLOG.md

---

## ✅ Submission Checklist

* [x] OpenEnv-compatible environment
* [x] RL training script (GRPO + TRL)
* [x] Real training evidence (reward curve)
* [x] Hugging Face Space deployed
* [x] Before/after comparison
* [x] Procedural task generator
* [x] Multi-signal reward
* [x] Blog/writeup included

---

## 🏁 Summary

> This project demonstrates how reinforcement learning can transform code generation from **static prediction → adaptive learning system**.

---
