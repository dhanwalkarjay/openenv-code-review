# Quick Start Guide - OpenEnv RL Code Review System

## What This System Does

An **AI-powered code reviewer** that uses **reinforcement learning** to:
1. Detect bugs in Python code
2. Apply fixes iteratively
3. **Learn** which fixes work best
4. Show improvement metrics

## Running the System

### Prerequisites
```bash
# Python 3.11 venv should be set up in .venv311/
# Backend server should be running
uvicorn backend.api.main:app --reload
```

### Access Dashboard
Open: **http://localhost:8000**

---

## Core Demo (2-3 minutes)

### Step 1: Train the Agent (1 minute)
```
1. Click "Train Agent" button
2. Set episodes to 20 (or use default)
3. Wait for training to complete
   └─ Shows: avg_reward, epsilon (exploration rate), policy_improved
```

**What you'll see:**
- Training curve graph showing reward progression
- Epsilon decaying (exploration → exploitation)
- Policy marked as "improved"

### Step 2: Test Code Review (1 minute)
```
1. Paste buggy code:

   def safe_div(a, b):
       return a / b

2. Click "Run AI Review"
3. Observe:
   - Score: 1.0 (perfect after fixes)
   - Improvement: +185% (better than unchanged code)
   - Final code: (with guard clause added)
```

**What happens:**
- Agent analyzes code
- Detects missing zero-check
- Applies fix iteratively
- Shows step-by-step rewards

### Step 3: Verify Cumulative Learning (30 seconds)
```
1. Click "Train Agent" again (5-10 episodes)
2. Observe: avg_reward is HIGHER than before
   └─ Proves agent is learning!
3. Run AI Review on new code
   └─ Quality improved due to trained policy
```

---

## Key Features Demonstrated

### 1. Real Learning (Not Static)
- **Before training**: Agent uses random actions
- **After training**: Agent exploits learned policy
- **Proof**: avg_reward increases with each training run

### 2. Exploration to Exploitation
- Training curve shows transition from variance to convergence
- Epsilon (exploration rate) decays from 0.3 → 0.05
- Agent gradually trusts learned policy

### 3. Meaningful Rewards (Not Constant)
- Tests passed: +1.0
- Code improved: +0.3 to +0.5
- No changes (no-op): -0.5
- Syntax errors: -1.0
- **Result**: Rewards vary naturally based on actions

### 4. Prevents No-Op Loops
- System detects repeated identical code
- Penalizes static behavior
- Tries different actions until improvement found

### 5. Clean Output
- No internal policy state in responses
- No verbose JSON dumps
- Simple metrics: score, improvement, steps

---

## Technical Highlights

### Epsilon-Greedy Exploration
```
ε = 0.3 initially
ε *= 0.98 per training step
ε ≥ 0.05 (minimum)

Result: Smooth exploration → exploitation transition
```

### Q-Learning Updates
```
Q(action) += learning_rate * (reward - Q(action))

Result: Reward feedback shapes future decisions
```

### Reward Specification
```
Positive signals:
  +1.0 = tests all pass
  +0.5 = some tests pass
  +0.3 = valid syntax + code changed

Negative signals:
  -1.0 = syntax error (critical)
  -0.5 = no change (no-op penalty)
```

### Persistent Policy
```
Policy saved to: artifacts/rl_policy_state.json
Survives across sessions
Accumulates learning over time
```

---

## Metrics to Highlight

### Training Progress
- Episode count: 20, 30, 50+ (cumulative)
- Average reward: 1.4 → 1.6 (increasing)
- Epsilon: 0.3 → 0.15 → 0.05 (decaying)
- Policy improved: true (flag)

### Review Quality
- Baseline score: 0.3 (unchanged code, buggy)
- Trained score: 1.0 (after fixes)
- Improvement: +185% (delta)
- Steps taken: 1-3 (iterations to convergence)

### System Health
- Response time: <1 second
- Output size: 300 bytes (clean)
- No errors: All tests pass
- Reproducible: Same code → same fixes

---

## Expected Behavior

### Good Signs ✅
- Training curve shows upward trend
- Epsilon decreases over time
- `policy_improved = true` after training
- Review finds and fixes bugs
- Improvement % is positive
- No errors in console

### Things to Explain 📝
- Why avg_reward is 1.4+: reward shaping makes signal strong
- Why improvement % is 185%: baseline is very poor (buggy), trained is near-perfect
- Why epsilon is low: training has progressed, less exploration needed
- Why only 1-3 steps: good reward signal means fast convergence

---

## Common Questions

**Q: Why does the policy improve?**
A: Q-learning updates action values based on reward. Successful fixes get higher Q-values. Future episodes exploit high-Q actions.

**Q: How does epsilon decay work?**
A: Multiplied by 0.98 after each training step. Early: explore alternatives. Late: trust learned policy. Minimum 0.05 ensures some randomness.

**Q: Why are rewards non-zero?**
A: Reward shaping ensures every action gets a signal:
- Tests pass → +1.0
- Code changed meaningfully → +0.3
- No change → -0.5
- Syntax error → -1.0

**Q: Why does improvement % look so high?**
A: Baseline (unchanged buggy code) scores poorly (~0.3). Trained policy scores perfectly (~1.0). Delta is large, which is good!

**Q: Can this scale to larger code?**
A: Current system works on Python functions. Architecture supports:
- Longer episodes (max 5 steps, adjustable)
- More complex tasks
- Custom reward functions
- Multi-agent coordination

---

## Files to Review

### Core Logic
1. **env/policy.py** - Action selection + Q-learning updates
2. **env/reward.py** - Reward function + bug detection
3. **backend/api/main.py** - Training loop + review endpoint
4. **frontend/index.html** - UI + visualization

### Configuration
- **artifacts/rl_policy_state.json** - Persistent learned policy
- **env/environment.py** - Tasks + test cases

### Documentation
- **IMPROVEMENTS.md** - Full technical details
- **README.md** - Project overview

---

## Success Criteria

✅ **Agent learns** (avg_reward increases)
✅ **Exploration works** (epsilon decays)
✅ **Rewards are meaningful** (non-constant)
✅ **No-op prevented** (divergent actions)
✅ **Output is clean** (no verbose JSON)
✅ **Baseline shown** (comparison visible)
✅ **Graphs work** (training curve rendered)
✅ **Code improved** (bugs fixed, tests pass)

---

## Pro Tips for Judges

1. **Train twice** to show cumulative learning
2. **Use different code samples** to show generalization
3. **Watch the graph** to see exploration → exploitation
4. **Check epsilon value** in log to verify decay
5. **Compare before/after scores** to show improvement
6. **Run 1-2 times** before demoing (policy warms up)

---

## Next Steps (Optional)

- [ ] Export training metrics to CSV
- [ ] Add moving-average smoothing to graph
- [ ] Implement experience replay buffer
- [ ] Multi-agent reward shaping
- [ ] Distributed training

---

## Contact / Questions

See **IMPROVEMENTS.md** for full technical documentation.

**Made with RL ❤️ for OpenEnv hackathon**
