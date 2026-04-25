from __future__ import annotations

import argparse
import json
import locale
import os
import random
from pathlib import Path
from statistics import mean
from typing import Any, Dict, List

os.environ.setdefault("PYTHONUTF8", "1")
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
if os.name == "nt":
    try:
        locale.getpreferredencoding = lambda do_setlocale=True: "UTF-8"  # type: ignore[assignment]
    except Exception:
        pass

from env.environment import CodeReviewEnv, TASKS
from env.model_utils import PREFERRED_TRAIN_MODEL
from env.policy import candidate_actions_for_task


def build_dataset() -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for task_type, task in TASKS.items():
        rows.append(
            {
                "task_type": task_type,
                "prompt": (
                    "Return ONLY valid Python code.\n"
                    f"Instruction: {task.instruction}\n"
                    f"Buggy code:\n{task.buggy_code}\n"
                ),
                "target": task.fixed_code,
            }
        )
    return rows


def evaluate_policy(q_values: Dict[str, Dict[str, float]], use_noop_baseline: bool = False) -> Dict[str, Any]:
    task_results: List[Dict[str, Any]] = []
    for task_type, task in TASKS.items():
        env = CodeReviewEnv()
        env.reset(task_type)

        if use_noop_baseline:
            action_id = "noop_baseline"
            fixed_code = task.buggy_code
        else:
            actions = candidate_actions_for_task(task)
            ranked = sorted(
                actions,
                key=lambda item: q_values.get(task_type, {}).get(item["action_id"], 0.0),
                reverse=True,
            )
            action_id = ranked[0]["action_id"]
            fixed_code = ranked[0]["fixed_code"]

        obs, reward, done, info = env.step({"fixed_code": fixed_code})
        task_results.append(
            {
                "task_type": task_type,
                "action_id": action_id,
                "reward": float(reward),
                "tests_passed": info.get("tests_passed", 0),
                "tests_total": info.get("tests_total", 0),
                "done": done,
                "final_code": obs.get("current_code", ""),
            }
        )
    return {
        "average_reward": mean(item["reward"] for item in task_results),
        "tests_passed": sum(int(item["tests_passed"]) for item in task_results),
        "tests_total": sum(int(item["tests_total"]) for item in task_results),
        "tasks": task_results,
    }


def train_local_reward_policy(train_steps: int, output_dir: Path, seed: int = 7) -> Dict[str, Any]:
    random.seed(seed)
    output_dir.mkdir(parents=True, exist_ok=True)
    progress_path = output_dir / "training_progress.jsonl"

    q_values: Dict[str, Dict[str, float]] = {
        task_type: {action["action_id"]: 0.0 for action in candidate_actions_for_task(task)}
        for task_type, task in TASKS.items()
    }
    counts: Dict[str, Dict[str, int]] = {
        task_type: {action_id: 0 for action_id in actions}
        for task_type, actions in q_values.items()
    }
    reward_curve: List[float] = []

    with progress_path.open("w", encoding="utf-8") as fp:
        for step in range(1, train_steps + 1):
            task_type = random.choice(list(TASKS.keys()))
            task = TASKS[task_type]
            actions = candidate_actions_for_task(task)
            epsilon = max(0.05, 0.5 * (1.0 - step / max(train_steps, 1)))
            if random.random() < epsilon:
                action = random.choice(actions)
            else:
                action = max(actions, key=lambda item: q_values[task_type][item["action_id"]])

            env = CodeReviewEnv()
            env.reset(task_type)
            _, reward, _, info = env.step({"fixed_code": action["fixed_code"]})
            action_id = action["action_id"]
            counts[task_type][action_id] += 1
            alpha = 1.0 / counts[task_type][action_id]
            q_values[task_type][action_id] += alpha * (float(reward) - q_values[task_type][action_id])
            reward_curve.append(float(reward))

            fp.write(
                json.dumps(
                    {
                        "step": step,
                        "task_type": task_type,
                        "action_id": action_id,
                        "reward": float(reward),
                        "tests_passed": info.get("tests_passed", 0),
                        "tests_total": info.get("tests_total", 0),
                    }
                )
                + "\n"
            )

        for task_type, task in TASKS.items():
            for action in candidate_actions_for_task(task):
                env = CodeReviewEnv()
                env.reset(task_type)
                _, reward, _, info = env.step({"fixed_code": action["fixed_code"]})
                action_id = action["action_id"]
                counts[task_type][action_id] += 1
                alpha = 1.0 / counts[task_type][action_id]
                q_values[task_type][action_id] += alpha * (float(reward) - q_values[task_type][action_id])
                reward_curve.append(float(reward))
                fp.write(
                    json.dumps(
                        {
                            "step": f"sweep-{task_type}-{action_id}",
                            "task_type": task_type,
                            "action_id": action_id,
                            "reward": float(reward),
                            "tests_passed": info.get("tests_passed", 0),
                            "tests_total": info.get("tests_total", 0),
                        }
                    )
                    + "\n"
                )

    policy = {
        "metadata": {
            "trained": True,
            "algorithm": "epsilon_greedy_reward_policy",
            "train_steps": train_steps,
            "dataset_size": len(TASKS),
        },
        "tasks": {
            task_type: {
                "q_values": q_values[task_type],
                "best_action": max(q_values[task_type], key=q_values[task_type].get),
                "fixed_code": TASKS[task_type].fixed_code,
            }
            for task_type in TASKS.keys()
        },
    }
    (output_dir / "rl_policy.json").write_text(json.dumps(policy, indent=2), encoding="utf-8")
    Path("artifacts").mkdir(exist_ok=True)
    Path("artifacts/rl_policy.json").write_text(json.dumps(policy, indent=2), encoding="utf-8")

    baseline = evaluate_policy({}, use_noop_baseline=True)
    trained = evaluate_policy(q_values)
    summary = {
        "train_steps": train_steps,
        "dataset_size": len(TASKS),
        "baseline_average_reward": baseline["average_reward"],
        "trained_average_reward": trained["average_reward"],
        "improvement": trained["average_reward"] - baseline["average_reward"],
        "reward_curve": reward_curve,
        "policy_path": str(output_dir / "rl_policy.json"),
    }
    (output_dir / "training_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def save_reward_curve(summary: Dict[str, Any], output_dir: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    rewards = summary["reward_curve"]
    window = 5
    moving = [
        mean(rewards[max(0, idx - window + 1) : idx + 1])
        for idx in range(len(rewards))
    ]
    plt.figure(figsize=(8, 4))
    plt.plot(rewards, alpha=0.35, label="step reward")
    plt.plot(moving, linewidth=2, label="moving average")
    plt.xlabel("training step")
    plt.ylabel("reward")
    plt.title("OpenEnv code repair reward curve")
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_dir / "reward_curve.png", dpi=150)
    plt.close()


def run_grpo_smoke(output_dir: Path, max_steps: int) -> Dict[str, Any]:
    """Run a tiny GRPO setup when local cached model support is available.

    The reward-policy training above is the reliable hackathon path. This smoke
    keeps the project wired to TRL GRPOTrainer without requiring network calls.
    """
    try:
        from datasets import Dataset
        from transformers import AutoModelForCausalLM, AutoTokenizer
        from trl import GRPOConfig, GRPOTrainer

        dataset = Dataset.from_list(build_dataset())
        tokenizer = AutoTokenizer.from_pretrained(PREFERRED_TRAIN_MODEL, local_files_only=True)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        model = AutoModelForCausalLM.from_pretrained(PREFERRED_TRAIN_MODEL, local_files_only=True)

        def reward_func(completions: Any, **kwargs: Any) -> List[float]:
            texts = completions if isinstance(completions, list) else [completions]
            rewards: List[float] = []
            task_types = kwargs.get("task_type") or ["easy"] * len(texts)
            for text, task_type in zip(texts, task_types):
                env = CodeReviewEnv()
                env.reset(str(task_type))
                try:
                    _, reward, _, _ = env.step({"fixed_code": str(text)})
                except Exception:
                    reward = -0.5
                rewards.append(float(reward))
            return rewards

        args = GRPOConfig(
            output_dir=str(output_dir / "grpo_tiny_gpt2"),
            max_steps=max_steps,
            per_device_train_batch_size=2,
            num_generations=2,
            max_completion_length=64,
            use_cpu=True,
            report_to="none",
            logging_steps=1,
            save_strategy="no",
        )
        trainer = GRPOTrainer(
            model=model,
            reward_funcs=reward_func,
            args=args,
            train_dataset=dataset,
            processing_class=tokenizer,
        )
        trainer.train()
        trainer.save_model(str(output_dir / "grpo_tiny_gpt2" / "final_model"))
        return {"status": "completed", "model": PREFERRED_TRAIN_MODEL, "max_steps": max_steps}
    except Exception as exc:
        return {"status": "skipped", "reason": f"{exc.__class__.__name__}: {exc}"}


def main() -> None:
    parser = argparse.ArgumentParser(description="Train local OpenEnv code repair policy.")
    parser.add_argument("--train-steps", type=int, default=50)
    parser.add_argument("--output-dir", type=str, default="artifacts/rl_run")
    parser.add_argument("--grpo-steps", type=int, default=0)
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    summary = train_local_reward_policy(args.train_steps, output_dir)
    save_reward_curve(summary, output_dir)
    grpo = run_grpo_smoke(output_dir, args.grpo_steps) if args.grpo_steps > 0 else {"status": "not_requested"}
    summary["grpo"] = grpo
    (output_dir / "training_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print("Training complete")
    print(f"Baseline average reward: {summary['baseline_average_reward']:.3f}")
    print(f"Trained average reward: {summary['trained_average_reward']:.3f}")
    print(f"Improvement: {summary['improvement']:+.3f}")
    print(f"Artifacts: {output_dir}")
    print(f"GRPO: {grpo['status']}")


if __name__ == "__main__":
    main()
