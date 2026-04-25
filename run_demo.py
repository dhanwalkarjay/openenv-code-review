from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict

from env.environment import CodeReviewEnv, TASKS
from env.policy import candidate_actions_for_task, load_policy


def run_task(task_type: str, policy_path: Path) -> Dict[str, Any]:
    task = TASKS[task_type]

    baseline_env = CodeReviewEnv()
    baseline_env.reset(task_type)
    baseline_obs, baseline_reward, _, baseline_info = baseline_env.step({"fixed_code": task.buggy_code})

    policy = load_policy(policy_path)
    q_values = policy.get("tasks", {}).get(task_type, {}).get("q_values", {})
    actions = candidate_actions_for_task(task)
    trained_action = max(actions, key=lambda item: q_values.get(item["action_id"], 0.0))

    trained_env = CodeReviewEnv()
    trained_env.reset(task_type)
    trained_obs, trained_reward, _, trained_info = trained_env.step(
        {"fixed_code": trained_action["fixed_code"]}
    )

    improvement = float(trained_reward) - float(baseline_reward)
    return {
        "task_type": task_type,
        "instruction": task.instruction,
        "buggy_code": task.buggy_code,
        "baseline": {
            "reward": float(baseline_reward),
            "tests": f"{baseline_info.get('tests_passed', 0)}/{baseline_info.get('tests_total', 0)}",
            "output": baseline_obs.get("current_code", ""),
        },
        "trained": {
            "action_id": trained_action["action_id"],
            "reward": float(trained_reward),
            "tests": f"{trained_info.get('tests_passed', 0)}/{trained_info.get('tests_total', 0)}",
            "output": trained_obs.get("current_code", ""),
        },
        "improvement": improvement,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run before/after local RL code repair demo.")
    parser.add_argument("--task", type=str, default="medium", choices=list(TASKS.keys()))
    parser.add_argument("--policy", type=str, default="artifacts/rl_policy.json")
    parser.add_argument("--output", type=str, default="artifacts/demo_report.json")
    args = parser.parse_args()

    report = run_task(args.task, Path(args.policy))
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print("OpenEnv local RL demo")
    print(f"Task: {report['task_type']} - {report['instruction']}")
    print("\nBuggy code:")
    print(report["buggy_code"])
    print("\nBaseline output")
    print(f"Reward: {report['baseline']['reward']:.3f} | tests: {report['baseline']['tests']}")
    print(report["baseline"]["output"])
    print("\nTrained output")
    print(
        f"Action: {report['trained']['action_id']} | "
        f"Reward: {report['trained']['reward']:.3f} | tests: {report['trained']['tests']}"
    )
    print(report["trained"]["output"])
    print(f"\nReward improvement: {report['improvement']:+.3f}")
    print(f"Report: {output}")


if __name__ == "__main__":
    main()
