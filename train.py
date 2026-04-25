# train.py
import json
import random
import matplotlib.pyplot as plt

from policy import Policy
from reward import compute_reward
from evaluator import evaluate_code

EPISODES = 50

policy = Policy()
rewards = []

code_sample = """
def divide(a, b):
    return a / b
"""

for episode in range(EPISODES):
    action = policy.select_action()

    new_code = policy.apply_action(code_sample, action)

    result = evaluate_code(new_code)
    reward = compute_reward(code_sample, new_code, result)

    policy.update(action, reward)

    rewards.append(reward)

    print(f"Episode {episode}: reward={reward}")

# save policy
with open("trained_policy.json", "w") as f:
    json.dump(policy.state, f)

# plot reward curve
plt.plot(rewards)
plt.xlabel("Episode")
plt.ylabel("Reward")
plt.title("Training Reward Curve")
plt.savefig("reward_curve.png")

print("Training complete")