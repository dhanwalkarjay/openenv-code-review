from __future__ import annotations

import json
import re
import ast
from typing import Any, Callable, Dict, List

from env.environment import CodeReviewEnv


ActionDict = Dict[str, Any]


def build_prompt(observation: Dict[str, Any], task_type: str) -> str:
    """Build a compact instruction prompt for code-fix generation."""
    previous_step = observation.get("previous_step_output")
    previous_step_str = json.dumps(previous_step) if previous_step is not None else "null"
    return (
        "You are a Python code-refactoring agent in an RL training loop.\n"
        "Your task is to fix the buggy function so it passes the hidden tests.\n"
        "Return ONLY the corrected Python function.\n"
        "Do not return markdown, JSON, comments outside the function, explanations, or prose.\n"
        "The first token of your answer should normally be 'def'.\n"
        f"TASK_TYPE:{task_type}\n"
        f"Instruction:\n{observation['instruction']}\n\n"
        f"Buggy code:\n{observation['buggy_code']}\n\n"
        f"Current code:\n{observation['current_code']}\n\n"
        f"Previous step output:\n{previous_step_str}\n"
    )


def format_prompt_for_model(tokenizer: Any, prompt: str) -> str:
    chat_template = getattr(tokenizer, "chat_template", None)
    if not chat_template:
        return prompt

    messages = [
        {
            "role": "system",
            "content": (
                "You fix Python functions. Return only valid Python code for the corrected "
                "function, with no markdown or explanation."
            ),
        },
        {
            "role": "user",
            "content": prompt,
        },
    ]

    try:
        return tokenizer.apply_chat_template(  # type: ignore[attr-defined]
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )
    except Exception:
        return prompt


def completion_to_text(completion: Any) -> str:
    if isinstance(completion, str):
        return completion
    if isinstance(completion, list):
        chunks: List[str] = []
        for item in completion:
            if isinstance(item, dict) and "content" in item:
                chunks.append(str(item["content"]))
            else:
                chunks.append(str(item))
        return "\n".join(chunks)
    return str(completion)


def _extract_json(text: str) -> Dict[str, Any]:
    text = text.strip()
    if not text:
        return {}

    try:
        parsed = json.loads(text)
        return parsed if isinstance(parsed, dict) else {}
    except Exception:
        pass

    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return {}

    try:
        parsed = json.loads(match.group(0))
        return parsed if isinstance(parsed, dict) else {}
    except Exception:
        return {}


def _syntax_ok(code: str) -> bool:
    try:
        ast.parse(code)
        return True
    except Exception:
        return False


def _extract_code_block(text: str) -> str:
    match = re.search(r"```(?:python|py)?\s*(.*?)```", text, flags=re.IGNORECASE | re.DOTALL)
    if match:
        return match.group(1).strip()
    return text.strip()


def _extract_python_function(text: str) -> str:
    """Best-effort cleanup for model completions that include chatter.

    The environment only needs a corrected function. We accept a full module if
    it parses, otherwise keep the first function definition that parses.
    """
    text = _extract_code_block(text)
    text = text.replace("<|endoftext|>", "").strip()

    # Strip common chat prefixes without relying on a specific model template.
    text = re.sub(r"^\s*(assistant|answer|fixed code|corrected code)\s*:\s*", "", text, flags=re.IGNORECASE)

    if _syntax_ok(text):
        return text

    def_match = re.search(r"(?m)^def\s+\w+\s*\([^)]*\)\s*:", text)
    if not def_match:
        return ""

    candidate = text[def_match.start():].strip()
    lines = candidate.splitlines()
    best = ""
    for end in range(len(lines), 0, -1):
        chunk = "\n".join(lines[:end]).rstrip()
        if _syntax_ok(chunk):
            best = chunk
            break

    return best


def parse_action(completion_text: str) -> ActionDict:
    parsed = _extract_json(completion_text)
    reviewer_issues: List[str] = []

    if parsed:
        reviewer_raw = parsed.get("reviewer_issues", [])
        if isinstance(reviewer_raw, str):
            reviewer_issues = [reviewer_raw]
        elif isinstance(reviewer_raw, list):
            reviewer_issues = [str(x) for x in reviewer_raw if str(x).strip()]
        raw_code = parsed.get("fixed_code", "")
    else:
        raw_code = completion_text

    fixed_code = _extract_python_function(str(raw_code))
    if not fixed_code or not _syntax_ok(fixed_code):
        raise ValueError("completion did not contain valid Python code")

    return {
        "reviewer_issues": [str(x).strip() for x in reviewer_issues if str(x).strip()],
        "fixed_code": fixed_code,
    }


def extract_task_type(prompt_text: str, default_task_type: str = "easy") -> str:
    match = re.search(r"TASK_TYPE:([a-zA-Z0-9_\-]+)", prompt_text)
    if not match:
        return default_task_type
    return match.group(1)


def rollout_reward_for_completion(
    completion_text: str,
    task_type: str,
) -> float:
    """Compute reward from the current completion only.

    Keeping reward focused on the submitted fix gives GRPO a clearer learning
    signal than diluting it with no-op rollouts.
    """
    env = CodeReviewEnv()
    obs = env.reset(task_type=task_type)

    action = parse_action(completion_text)
    _, reward, _, _ = env.step(action)
    return float(reward)


def build_grpo_reward_fn(max_rollout_steps: int = 2) -> Callable[..., List[float]]:
    """Return TRL-compatible reward function callable."""

    def reward_fn(*args: Any, completions: Any = None, prompts: Any = None, **kwargs: Any) -> List[float]:
        if completions is None:
            if len(args) >= 2:
                prompts = args[0]
                completions = args[1]
            elif len(args) == 1:
                completions = args[0]
            else:
                completions = []

        rewards: List[float] = []
        _ = max_rollout_steps  # Kept for backward-compatible call sites.

        task_types_from_kwargs = kwargs.get("task_type")

        for idx, completion in enumerate(completions):
            completion_text = completion_to_text(completion)

            if isinstance(task_types_from_kwargs, list) and idx < len(task_types_from_kwargs):
                task_type = str(task_types_from_kwargs[idx])
            elif isinstance(prompts, list) and idx < len(prompts):
                task_type = extract_task_type(completion_to_text(prompts[idx]))
            else:
                task_type = "easy"

            rewards.append(
                rollout_reward_for_completion(
                    completion_text=completion_text,
                    task_type=task_type,
                )
            )

        return rewards

    return reward_fn


def evaluate_completion(task_type: str, completion_text: str) -> Dict[str, Any]:
    env = CodeReviewEnv()
    obs = env.reset(task_type=task_type)
    action = parse_action(completion_text)
    next_obs, reward, done, info = env.step(action)
    return {
        "task_type": task_type,
        "reward": float(reward),
        "done": done,
        "info": info,
        "state": next_obs,
        "action": action,
    }
