---
title: OpenEnv Code Review
emoji: 🤖
colorFrom: blue
colorTo: green
sdk: docker
app_file: backend/api/main.py
pinned: false
---

# OpenEnv Code Review — RL Training Environment

An OpenEnv-compatible environment for training LLMs to fix Python bugs 
using reinforcement learning with verifiable rewards (GRPO + Unsloth).

## Environment

8 Python bug-fixing tasks with real test-case execution as the reward signal:

| Task | Bug Type | Tests |
|------|----------|-------|
| easy | Index error (items[3] → items[2]) | 3 |
| medium | Missing colon syntax error | 2 |
| hard | Division by zero | 3 |
| bonus | Off-by-one loop | 3 |
| list_len | Wrong comparison operator | 3 |
| none_lower | None not handled before .lower() | 3 |
| max_init | Wrong max initialization | 3 |
| first_item | Wrong index for first item | 2 |

OpenEnv contract: `POST /reset` → `POST /step` → `GET /state`

## Training Results

| Metric | Value |
|--------|-------|
| Model | Qwen/Qwen2.5-0.5B-Instruct |
| Algorithm | GRPO (TRL + Unsloth) |
| Steps | 80 |
| Baseline avg reward | 0.20 (step 1) |
| Trained avg reward | 1.00+ (steps 30-80) |
| Tasks solved | 5/6 |

![Reward curve](artifacts/grpo_run/reward_curve.png)

## Before / After Examples

**Fix index error (easy)**
```python
# Buggy
def get_third_item(items):
    return items[3]

# Fixed by trained model
def get_third_item(items):
    return items[2]
```

**Fix division by zero (hard)**
```python
# Buggy
def safe_div(a, b):
    return a / b

# Fixed by trained model  
def safe_div(a, b):
    if b == 0:
        return 0
    return a / b
```

**Elegant rewrite (bonus)**
```python
# Buggy
def sum_to_n(n):
    total = 0
    for i in range(n):   # off by one
        total += i
    return total

# Fixed by trained model
def sum_to_n(n):
    return sum(range(n + 1))  # cleaner than reference solution!
```

## Reward Design

3 independent reward functions to prevent hacking:
- `reward_tests_pass` — calls live environment verifier (+1.0 all pass)
- `reward_syntax_valid` — AST parse check (+0.2 / -0.3)
- `reward_no_trivial_hack` — penalizes bare except/pass patterns (-0.3)

## Links
- 🤗 Space: https://huggingface.co/spaces/dhanwalkarjay/openenv-code-review
- 📓 Training script: `train_grpo_colab.py`
- 📝 Blog: [ADD YOUR HF BLOG URL HERE]

## Run the environment
```bash
POST /reset  {"task_type": "easy"}
POST /step   {"fixed_code": "..."}
GET  /state
GET  /tasks
```

## Minimum Requirements Checklist
- ✅ OpenEnv compatible (reset/step/state)
- ✅ Training script (Unsloth + TRL GRPO)  
- ✅ Reward curves from real run
- ✅ Hosted on Hugging Face Spaces
- ✅ Before/after behavior shown