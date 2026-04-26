# Training an LLM to Fix Python Bugs with GRPO + OpenEnv

**TL;DR:** We built an RL environment where a small LLM (Qwen2.5-0.5B) learns to fix Python bugs by receiving real test-execution feedback as reward. Reward climbed from 0.2 → 1.0+ over 80 GRPO steps. The environment generates unlimited unique tasks procedurally.

---

## The Problem with Static Code Training

Most LLMs learn to fix code from static datasets — they see (buggy code, fixed code) pairs and learn to imitate. The problem: the model has no feedback loop. It can produce output that *looks* correct without knowing if it actually passes tests.

What we really want is an agent that:
1. Attempts a fix
2. Runs real tests
3. Gets penalised for wrong answers
4. Learns to do better

That's reinforcement learning — and that's exactly what we built.

---

## The Environment

We built an **OpenEnv-compatible** environment with a clean RL interface:

```python
# Reset to a new task
obs = env.reset(task_type="hard")
# obs contains: buggy_code, instruction, tests_total

# Agent proposes a fix
obs, reward, done, info = env.step({
    "fixed_code": "def safe_div(a, b):\n    if b==0: return 0\n    return a/b"
})
# reward: 1.0 if all tests pass, -0.5 if nothing works
```

The key insight: **reward comes from running real Python test cases**, not from a learned reward model. This makes it verifiable and hard to game.

### Three Independent Reward Signals

To prevent reward hacking, we use three independent reward functions:

- `reward_tests_pass` — does the code actually pass the test suite?
- `reward_syntax_valid` — is the code even valid Python? (+0.2 / -0.3)
- `reward_no_trivial_hack` — penalises `except: pass` and other shortcuts (-0.3)

A model that exploits one signal still gets penalised by the others.

### Procedural Task Generation

Instead of 8 fixed tasks, we built a **procedural generator** that creates unlimited unique bug-fixing challenges across 7 bug strategies:

```python
from env.task_generator import generate_curriculum

# 20 tasks ordered easy → medium → hard (curriculum learning)
curriculum = generate_curriculum(n=20, seed=42)
```

This means the agent can't memorise tasks — it has to actually learn to fix bugs.

---

## Training with GRPO

We used **GRPO** (Group Relative Policy Optimisation) from TRL, accelerated with Unsloth:

- **Model:** Qwen/Qwen2.5-0.5B-Instruct (4-bit QLoRA)
- **LoRA:** r=16, target: q/k/v/o projections
- **Steps:** 80
- **Generations per prompt:** 4 (GRPO scores all 4, updates toward best)
- **Hardware:** A10G GPU (~$3 of HF credits)

The training loop connects directly to the live environment — the model generates code, the environment executes it, the reward flows back:

```
Prompt → Qwen generates 4 fixes → env.step() scores each
→ GRPO updates weights toward higher-reward fixes
→ repeat
```

---

## Results

The reward curve tells the story clearly:

![Reward curve](https://huggingface.co/dhanwalkarjay/openenv-code-review-model/resolve/main/reward_curve.png)

Reward climbs from ~0.2 at step 1 to consistently above 1.0 by step 30. The model learned in under 10 minutes of GPU time.

### Before / After Examples

**Easy — index error:**
```python
# Buggy
def get_third_item(items):
    return items[3]   # wrong index

# Trained model
def get_third_item(items):
    return items[2]   # correct ✅
```

**Hard — division by zero:**
```python
# Buggy
def safe_div(a, b):
    return a / b      # crashes when b=0

# Trained model
def safe_div(a, b):
    if b == 0:
        return 0
    return a / b      # correct ✅
```

**Bonus — elegant rewrite:**
```python
# Buggy (off-by-one loop)
def sum_to_n(n):
    total = 0
    for i in range(n):   # misses n
        total += i
    return total

# Trained model
def sum_to_n(n):
    return sum(range(n + 1))   # cleaner than reference solution ✅
```

5/6 tasks solved at full reward (1.0). The one partial result was a token truncation issue, not a learning failure.

---

## Try It

**Live demo:** https://huggingface.co/spaces/dhanwalkarjay/openenv-code-review

Select any task, click "Run RL Episode", and watch the agent attempt fixes step by step with live reward updates and a real-time graph.

**Trained model:** https://huggingface.co/dhanwalkarjay/openenv-code-review-model

**Training script:** `train_grpo_colab.py` in the GitHub repo — open in Colab, point it at the Space URL, run all cells.

**Experiment Tracking:** [View on W&B](https://wandb.ai/jaydhanwalkar123-g-h-raisoni-skill-tech-university-nagpur/openenv-code-review?nw=nwuserjaydhanwalkar123) 

---

## What We Learned

1. **Reward design is the hardest part.** Our first reward function was backwards — correct fixes got -0.5, garbage got +0.7. Three debugging sessions later we had it right.

2. **Multiple reward signals matter.** Single reward = easy to hack. Three independent signals = the model actually has to solve the task.

3. **Shared server state is dangerous.** Our environment used a single `env` object — every `/step` call evaluated whatever task was last reset. Classic bug that made training useless until fixed.

4. **GRPO is surprisingly efficient.** 80 steps, 4 generations each, A10G GPU, ~$3 of compute. The model genuinely learned to fix bugs it had never seen.

---

*Built for the OpenEnv Hackathon India 2026 — Theme #3 (World Modeling / Professional Tasks)*