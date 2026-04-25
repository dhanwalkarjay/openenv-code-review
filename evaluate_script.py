from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import mean
from typing import Any, Dict, List

from env.environment import CodeReviewEnv, TASKS
from env.policy import candidate_actions_for_task, load_policy


def evaluate_noop() -> Dict[str, Any]:
    results: List[Dict[str, Any]] = []
    for task_type, task in TASKS.items():
        env = CodeReviewEnv()
        env.reset(task_type)
        obs, reward, done, info = env.step({"fixed_code": task.buggy_code})
        results.append(
            {
                "task_type": task_type,
                "policy": "baseline_noop",
                "reward": float(reward),
                "tests_passed": info.get("tests_passed", 0),
                "tests_total": info.get("tests_total", 0),
                "done": done,
                "final_code": obs.get("current_code", ""),
            }
        )
    return summarize(results)


def evaluate_trained(policy_path: Path) -> Dict[str, Any]:
    policy = load_policy(policy_path)
    results: List[Dict[str, Any]] = []
    for task_type, task in TASKS.items():
        q_values = policy.get("tasks", {}).get(task_type, {}).get("q_values", {})
        actions = candidate_actions_for_task(task)
        action = max(actions, key=lambda item: q_values.get(item["action_id"], 0.0))
        env = CodeReviewEnv()
        env.reset(task_type)
        obs, reward, done, info = env.step({"fixed_code": action["fixed_code"]})
        results.append(
            {
                "task_type": task_type,
                "policy": "trained_reward_policy",
                "action_id": action["action_id"],
                "reward": float(reward),
                "tests_passed": info.get("tests_passed", 0),
                "tests_total": info.get("tests_total", 0),
                "done": done,
                "final_code": obs.get("current_code", ""),
            }
        )
    return summarize(results)


def summarize(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        "average_reward": mean(item["reward"] for item in results),
        "tests_passed": sum(int(item["tests_passed"]) for item in results),
        "tests_total": sum(int(item["tests_total"]) for item in results),
        "success_rate": mean(1.0 if item["tests_passed"] == item["tests_total"] else 0.0 for item in results),
        "tasks": results,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate baseline vs trained OpenEnv policy.")
    parser.add_argument("--policy", type=str, default="artifacts/rl_policy.json")
    parser.add_argument("--output", type=str, default="artifacts/eval_report.json")
    args = parser.parse_args()

    baseline = evaluate_noop()
    trained = evaluate_trained(Path(args.policy))
    improvement = trained["average_reward"] - baseline["average_reward"]
    report = {
        "baseline": baseline,
        "trained": trained,
        "improvement": improvement,
        "improvement_percent": (improvement / max(abs(baseline["average_reward"]), 0.1)) * 100.0,
    }

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("Evaluation complete")
    print(f"Baseline reward: {baseline['average_reward']:.3f}")
    print(f"Trained reward: {trained['average_reward']:.3f}")
    print(f"Improvement: {improvement:+.3f}")
    print(f"Report: {output}")


if __name__ == "__main__":
    main()
