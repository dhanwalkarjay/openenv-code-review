# Training an LLM to Fix Python Bugs with GRPO + OpenEnv

**TL;DR:** I built a reinforcement learning environment where a small LLM (Qwen2.5-0.5B) learns to fix Python bugs using real test-execution feedback as reward. Reward improves from **0.2 → 1.0+ over 80 GRPO steps**, demonstrating measurable learning.

> This project shows how reinforcement learning can transform code generation from **static prediction → adaptive learning system**.

---

## 🚨 The Problem with Static Code Training

Most LLMs learn code fixes from static datasets — pairs of (buggy code, fixed code).
The issue:

* No feedback loop
* No execution verification
* Can produce code that *looks* correct but fails in practice

👉 What we really need is:

1. Try a fix
2. Run real tests
3. Get penalized for failure
4. Improve over time

That’s **reinforcement learning** — and that’s what I built.

---

## 🏗️ The Environment

I designed an **OpenEnv-compatible RL environment**:

```python
# Reset environment
obs = env.reset(task_type="hard")

# Agent proposes a fix
obs, reward, done, info = env.step({
    "fixed_code": "def safe_div(a, b):\n    if b==0: return 0\n    return a/b"
})
```

### Key Idea

👉 **Reward comes from real Python test execution**
—not from a learned reward model.

This makes the system:

* Verifiable
* Reliable
* Hard to game

---

## 🎯 Reward Design

I use **three independent reward signals**:

* `reward_tests_pass` → correctness
* `reward_syntax_valid` → valid Python (+0.2 / -0.3)
* `reward_no_trivial_hack` → penalizes shortcuts (-0.3)

👉 Final reward typically ranges:

```text
-0.5 → failed attempts  
+1.2 → fully correct solution  
```

This prevents reward hacking and forces real problem solving.

---

## 🧪 Procedural Task Generation

Instead of fixed tasks, I generate:

👉 **procedurally generated diverse tasks**

Across bug types:

* Index errors
* Syntax bugs
* Division by zero
* None handling
* Loop errors
* Comparison bugs
* Initialization mistakes

```python
from env.task_generator import generate_curriculum
curriculum = generate_curriculum(n=20, seed=42)
```

👉 Result: agent must **learn patterns**, not memorize solutions.

---

## ⚙️ Training vs Live Demo

This project uses a **two-phase RL setup**:

### 🧠 Offline Training (Real Learning)

* GRPO (Group Relative Policy Optimization)
* Hugging Face TRL + Unsloth
* Runs in Colab (GPU)

Produces:

* Reward curves
* Training logs
* Learned policy

---

### ⚡ Live Demo (Hugging Face Space)

The Space demonstrates:

* Environment interaction
* Step-by-step agent decisions
* Real-time reward feedback

⚠️ Important:

* No model weight updates happen in the UI
* Only inference + environment loop

👉 This keeps the demo fast and interactive.

---

## 🧠 Training with GRPO

Setup:

* **Model:** Qwen2.5-0.5B-Instruct (QLoRA, 4-bit)
* **LoRA:** r=16
* **Steps:** 80
* **Generations per prompt:** 4
* **Hardware:** A10G (~$3 cost)

Training loop:

```text
Prompt → Generate 4 fixes → env.step() → reward
→ GRPO update → repeat
```

👉 The model learns directly from execution feedback.

---

## 📊 Results

### 📈 Reward Curve

![Reward Curve](https://huggingface.co/dhanwalkarjay/openenv-code-review-model/resolve/main/reward_curve.png)

👉 Reward improves from ~0.2 → 1.0+

---

### 🧪 Baseline vs Trained

| Model     | Reward |
| --------- | ------ |
| Untrained | ~0.2   |
| Trained   | ~1.0+  |

👉 **+400% improvement**

---

### 🧪 Before / After Examples

#### Easy — Index Error

```python
# Buggy
def get_third_item(items):
    return items[3]

# Trained model
def get_third_item(items):
    return items[2]  # ✅
```

---

#### Hard — Division by Zero

```python
# Buggy
def safe_div(a, b):
    return a / b

# Trained model
def safe_div(a, b):
    if b == 0:
        return 0
    return a / b  # ✅
```

---

#### Bonus — Elegant Rewrite

```python
# Buggy
def sum_to_n(n):
    total = 0
    for i in range(n):
        total += i
    return total

# Trained model
def sum_to_n(n):
    return sum(range(n + 1))  # cleaner solution ✅
```

---

### 📊 Performance

* 5/6 tasks solved fully
* 1 partial due to token truncation (not learning failure)

---

## 🚀 Try It Yourself

👉 **Live Demo:**
https://huggingface.co/spaces/dhanwalkarjay/openenv-code-review

👉 **Trained Model:**
https://huggingface.co/dhanwalkarjay/openenv-code-review-model

👉 **Training Notebook:**
https://colab.research.google.com/drive/1GZ-SkkKCNRhTqPjtRerHVhq23rRvvtvL

👉 **Experiment Tracking (W&B):**
https://wandb.ai/jaydhanwalkar123-g-h-raisoni-skill-tech-university-nagpur/openenv-code-review

---

## 💡 What I Learned

1. **Reward design is critical**
   Early reward bugs completely broke learning

2. **Multiple reward signals prevent cheating**
   Single reward = exploitable

3. **Environment bugs can destroy training**
   Shared state caused incorrect evaluation

4. **GRPO is efficient**
   Real learning in ~10 minutes of compute

---

## 🎯 Why This Matters

This system demonstrates how I can build:

* Self-improving AI code reviewers
* Autonomous debugging agents
* Learning-based developer tools

👉 Moving beyond static LLMs → **adaptive intelligent systems**

---

## 🏁 Conclusion

I showed that:

* LLMs can learn from execution feedback
* RL + environments unlock real improvement
* Small models can learn efficiently

> This is a step toward **AI systems that improve themselves through interaction**, not just training data.

---

*Built for OpenEnv Hackathon India 2026 — Theme #3 (World Modeling / Professional Tasks)*
