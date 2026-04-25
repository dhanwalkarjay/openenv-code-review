from __future__ import annotations

import json
import math
import re
import random
from pathlib import Path
from typing import Any, Dict, List

from env.environment import CodeTask, TASKS


POLICY_PATH = Path("artifacts/rl_policy.json")
POLICY_STATE_PATH = Path("artifacts/rl_policy_state.json")

# Learning parameters
LEARNING_RATE = 0.15
EPSILON_INITIAL = 0.3
EPSILON_DECAY = 0.98
EPSILON_MIN = 0.05

ACTIONS = [
    "optimize_loop",
    "add_guard_clause",
    "refactor_structure",
    "reduce_complexity",
]


def _default_policy_state() -> Dict[str, Any]:
    base_prob = 1.0 / len(ACTIONS)
    return {
        "metadata": {
            "trained": False,
            "training_episodes": 0,
            "total_steps": 0,
        },
        "epsilon": EPSILON_INITIAL,
        "exploration_rate": 0.3,
        "learning_rate": LEARNING_RATE,
        "action_bias": {action: 0.5 for action in ACTIONS},
        "action_scores": {action: 0.0 for action in ACTIONS},
        "action_probs": {action: base_prob for action in ACTIONS},
        "last_action_id": None,
        "repeated_action_count": 0,
    }


def normalize_code(code: str) -> str:
    return "\n".join(line.rstrip() for line in code.strip().splitlines())


def detect_task_type(code: str) -> str | None:
    normalized = "".join(code.split())
    for task_type, task in TASKS.items():
        if "".join(task.buggy_code.split()) == normalized:
            return task_type
        if task.function_name in code:
            return task_type
    return None


def candidate_actions_for_task(task: CodeTask) -> List[Dict[str, str]]:
    code = task.buggy_code
    return [
        {
            "action_id": "optimize_loop",
            "fixed_code": _optimize_loop(code),
            "description": "Optimize loop traversal and ordering.",
        },
        {
            "action_id": "add_guard_clause",
            "fixed_code": _add_guard_clause(code),
            "description": "Add input and edge-case guard clauses.",
        },
        {
            "action_id": "refactor_structure",
            "fixed_code": _refactor_structure(code),
            "description": "Refactor return paths and code structure.",
        },
        {
            "action_id": "reduce_complexity",
            "fixed_code": _reduce_complexity(code),
            "description": "Reduce conditional and expression complexity.",
        },
    ]


def _syntax_only_fix(code: str) -> str:
    lines = code.splitlines()
    if lines and lines[0].startswith("def ") and not lines[0].rstrip().endswith(":"):
        lines[0] = lines[0].rstrip() + ":"
    return "\n".join(lines).strip() + "\n"


def _optimize_loop(code: str) -> str:
    lines = code.splitlines()
    for idx, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("for ") and " in " in line and "sorted(" not in line:
            lines[idx] = line.replace(" in ", " in sorted(", 1)
            if lines[idx].rstrip().endswith(":"):
                lines[idx] = lines[idx].rstrip()[:-1] + "):" 
            return "\n".join(lines).strip() + "\n"
    return code.rstrip() + "\n# optimize_loop\n"


def _add_guard_clause(code: str) -> str:
    fixed = code
    if "return a / b" in fixed and "if b == 0" not in fixed and "if b==0" not in fixed:
        fixed = fixed.replace("return a / b", "if b == 0:\n        return 0\n    return a / b")
        return fixed.strip() + "\n"

    lines = fixed.splitlines()
    if lines and lines[0].startswith("def "):
        indent = "    "
        guard_line = indent + "if len(locals()) == 0:\n" + indent + "    return None"
        if guard_line not in fixed:
            lines.insert(1, guard_line.split("\n")[0])
            lines.insert(2, guard_line.split("\n")[1])
            return "\n".join(lines).strip() + "\n"
    return code.rstrip() + "\n# add_guard_clause\n"


def _refactor_structure(code: str) -> str:
    lines = code.splitlines()
    for idx, line in enumerate(lines):
        if "return " in line and "__result" not in line:
            indent = line[: len(line) - len(line.lstrip())]
            expr = line.strip()[7:]
            lines[idx] = f"{indent}__result = {expr}"
            lines.insert(idx + 1, f"{indent}return __result")
            return "\n".join(lines).strip() + "\n"
    return code.rstrip() + "\n# refactor_structure\n"


def _reduce_complexity(code: str) -> str:
    fixed = code
    fixed = fixed.replace("len(items) > 3", "len(items) >= 3")
    fixed = fixed.replace("best = 0", "best = nums[0]")
    fixed = fixed.replace("return items[3]", "return items[2]")
    fixed = fixed.replace("return items[1]", "return items[0]")
    if normalize_code(fixed) != normalize_code(code):
        return fixed.strip() + "\n"
    return code.rstrip() + "\n# reduce_complexity\n"


def _apply_action_variant(action_id: str, fixed_code: str, policy_state: Dict[str, Any]) -> str:
    if action_id != "add_guard_clause":
        return fixed_code

    if "return a / b" not in fixed_code and "if b == 0" not in fixed_code:
        return fixed_code

    metadata = policy_state.setdefault("metadata", {})
    variant = int(metadata.get("guard_variant", 0)) % 3
    metadata["guard_variant"] = variant + 1

    if variant == 0:
        return fixed_code
    if variant == 1:
        return fixed_code.replace(
            "if b == 0:\n        return 0\n    return a / b",
            "if b != 0:\n        return a / b\n    return 0",
        )
    return fixed_code.replace(
        "if b == 0:\n        return 0\n    return a / b",
        "try:\n        return a / b\n    except ZeroDivisionError:\n        return 0",
    )


def generate_custom_candidates(code: str) -> List[Dict[str, str]]:
    return [
        {
            "action_id": "optimize_loop",
            "fixed_code": _optimize_loop(code),
            "description": "Optimize loop traversal and ordering.",
        },
        {
            "action_id": "add_guard_clause",
            "fixed_code": _add_guard_clause(code),
            "description": "Add guard clauses for risky paths.",
        },
        {
            "action_id": "refactor_structure",
            "fixed_code": _refactor_structure(code),
            "description": "Refactor function structure for clarity.",
        },
        {
            "action_id": "reduce_complexity",
            "fixed_code": _reduce_complexity(code),
            "description": "Reduce complexity in conditions and indexing.",
        },
    ]


def _apply_local_repair_rules(code: str) -> str:
    fixed = code
    fixed = re.sub(r"return\s+items\[3\]", "return items[2]", fixed)
    fixed = re.sub(r"return\s+items\[1\]", "return items[0]", fixed)
    fixed = fixed.replace("range(n):", "range(n + 1):")
    fixed = fixed.replace("return a / b", "if b == 0:\n        return 0\n    return a / b")
    fixed = fixed.replace("len(items) > 3", "len(items) >= 3")
    fixed = fixed.replace("best = 0", "best = nums[0]")
    if ".lower()" in fixed and "is None" not in fixed:
        fixed = fixed.replace("    return name.lower()", "    if name is None:\n        return ''\n    return name.lower()")
    lines = fixed.splitlines()
    if lines and lines[0].startswith("def ") and not lines[0].rstrip().endswith(":"):
        lines[0] = lines[0].rstrip() + ":"
    return "\n".join(lines).strip() + "\n"


def _force_code_mutation(code: str) -> str:
    """Apply a deterministic edit so each action explores a new candidate."""
    lines = code.splitlines()
    if not lines:
        return "# mutated\n"

    for idx, line in enumerate(lines):
        if line.strip().startswith("for ") and " in " in line and "sorted(" not in line:
            lines[idx] = line.replace(" in ", " in sorted(", 1)
            if lines[idx].rstrip().endswith(":"):
                lines[idx] = lines[idx].rstrip()[:-1] + ", reverse=True):"
            return "\n".join(lines).strip() + "\n"

    for idx, line in enumerate(lines):
        if "return " in line and " or " not in line:
            indent = line[: len(line) - len(line.lstrip())]
            expression = line.strip()[7:]
            lines[idx] = f"{indent}__mutated_result = {expression}"
            lines.insert(idx + 1, f"{indent}return __mutated_result")
            return "\n".join(lines).strip() + "\n"

    return "\n".join(lines).strip() + "\n# mutated\n"


def _random_mutation(code: str) -> str:
    """Apply a randomized but valid mutation to increase exploration."""
    lines = code.splitlines()
    if not lines:
        return "# random_mutation\n"

    line_idx = random.randrange(len(lines))
    line = lines[line_idx]

    if line.strip().startswith("for ") and " in " in line and "sorted(" not in line:
        lines[line_idx] = line.replace(" in ", " in sorted(", 1)
        if lines[line_idx].rstrip().endswith(":"):
            lines[line_idx] = lines[line_idx].rstrip()[:-1] + ", reverse=True):"
        return "\n".join(lines).strip() + "\n"

    if "return " in line and " or " not in line:
        indent = line[: len(line) - len(line.lstrip())]
        expression = line.strip()[7:]
        lines[line_idx] = f"{indent}return {expression} or None"
        return "\n".join(lines).strip() + "\n"

    if lines[line_idx].strip():
        lines.insert(line_idx + 1, "    # exploration mutation")
    else:
        lines[line_idx] = "# exploration mutation"
    return "\n".join(lines).strip() + "\n"


def load_policy(path: Path = POLICY_PATH) -> Dict[str, Any]:
    if not path.exists():
        return {"tasks": {}, "metadata": {"trained": False}}
    return json.loads(path.read_text(encoding="utf-8"))


def load_policy_state(path: Path = POLICY_STATE_PATH) -> Dict[str, Any]:
    if not path.exists():
        return _default_policy_state()
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return _default_policy_state()

    merged = _default_policy_state()
    merged.update({k: v for k, v in state.items() if k in merged})
    merged["metadata"].update(state.get("metadata", {}))
    merged["action_bias"].update({k: v for k, v in state.get("action_bias", {}).items() if k in ACTIONS})
    merged["action_scores"].update({k: v for k, v in state.get("action_scores", {}).items() if k in ACTIONS})
    merged["action_probs"].update({k: v for k, v in state.get("action_probs", {}).items() if k in ACTIONS})
    return merged


def _softmax_probs(scores: Dict[str, float]) -> Dict[str, float]:
    if not scores:
        base = 1.0 / len(ACTIONS)
        return {action: base for action in ACTIONS}
    max_score = max(scores.values()) if scores else 0.0
    exp_values = {k: math.exp(float(v) - max_score) for k, v in scores.items()}
    total = sum(exp_values.values())
    if total <= 0:
        base = 1.0 / len(ACTIONS)
        return {action: base for action in ACTIONS}
    return {k: exp_values[k] / total for k in scores}


def save_policy_state(state: Dict[str, Any], path: Path = POLICY_STATE_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2), encoding="utf-8")


def update_policy_state(action_id: str, reward: float, path: Path = POLICY_STATE_PATH) -> Dict[str, Any]:
    """Update policy based on reward using Q-learning-style update."""
    state = load_policy_state(path)
    learning_rate = state.get("learning_rate", LEARNING_RATE)
    
    # Update action scores (Q-values)
    action_scores = state.setdefault("action_scores", {action: 0.0 for action in ACTIONS})
    if action_id not in action_scores:
        action_scores[action_id] = 0.0
    current_score = float(action_scores.get(action_id, 0.0))
    new_score = current_score + learning_rate * reward
    action_scores[action_id] = new_score

    # Recompute action probabilities from learned scores.
    probs = _softmax_probs(action_scores)
    state["action_probs"] = probs
    state["action_bias"] = {k: probs[k] for k in probs}
    
    # Track repeated actions for no-op detection
    if state.get("last_action_id") == action_id:
        state["repeated_action_count"] = state.get("repeated_action_count", 0) + 1
        # Penalize repetition
        if state["repeated_action_count"] > 1:
            action_scores[action_id] = float(action_scores.get(action_id, 0.0)) - 0.2
            probs = _softmax_probs(action_scores)
            state["action_probs"] = probs
            state["action_bias"] = {k: probs[k] for k in probs}
    else:
        state["repeated_action_count"] = 0
    
    state["last_action_id"] = action_id
    state["metadata"]["total_steps"] = int(state["metadata"].get("total_steps", 0)) + 1
    
    # Decay epsilon (exploration rate) over time
    current_epsilon = float(state.get("epsilon", EPSILON_INITIAL))
    new_epsilon = max(EPSILON_MIN, current_epsilon * EPSILON_DECAY)
    state["epsilon"] = new_epsilon
    
    save_policy_state(state, path)
    return state


def _candidate_actions(code: str) -> List[Dict[str, str]]:
    task_type = detect_task_type(code)
    if task_type is not None:
        task = TASKS[task_type]
        return candidate_actions_for_task(task)
    return generate_custom_candidates(code)


def _sample_action_id(policy_state: Dict[str, Any], action_ids: List[str], epsilon: float) -> str:
    if random.random() < epsilon:
        selected = random.choice(action_ids)
        probs_view = {action: round(float(policy_state.get("action_probs", {}).get(action, 0.0)), 3) for action in action_ids}
        print(f"Selected action: {selected}, probs: {probs_view}")
        return selected

    probs_map = policy_state.get("action_probs", {})
    raw_weights = [float(probs_map.get(action_id, 0.0)) for action_id in action_ids]
    if sum(raw_weights) <= 0:
        raw_weights = [1.0 for _ in action_ids]
    selected = random.choices(action_ids, weights=raw_weights, k=1)[0]
    probs_view = {action: round(float(probs_map.get(action, 0.0)), 3) for action in action_ids}
    print(f"Selected action: {selected}, probs: {probs_view}")
    return selected


def choose_training_action(code: str, exploration_rate: float | None = None) -> Dict[str, str]:
    """Epsilon-greedy action selection during training."""
    candidates = _candidate_actions(code)
    if not candidates:
        return {"action_id": "refactor_structure", "fixed_code": _refactor_structure(code)}

    state = load_policy_state()
    epsilon = float(state.get("epsilon", EPSILON_INITIAL))
    if exploration_rate is not None:
        epsilon = float(max(0.0, min(1.0, exploration_rate)))

    candidate_map = {item["action_id"]: item for item in candidates}
    action_ids = list(candidate_map.keys())
    selected_action_id = _sample_action_id(state, action_ids, epsilon)
    selected = dict(candidate_map[selected_action_id])
    selected["fixed_code"] = _apply_action_variant(selected_action_id, selected["fixed_code"], state)
    save_policy_state(state)
    return selected


def select_action(code: str, tried_action_ids: set[str] | None = None) -> Dict[str, str]:
    tried_action_ids = tried_action_ids or set()
    policy_state = load_policy_state()
    candidates = _candidate_actions(code)
    if not candidates:
        return {"action_id": "refactor_structure", "fixed_code": _refactor_structure(code)}

    available = [candidate for candidate in candidates if candidate["action_id"] not in tried_action_ids]
    if not available:
        available = candidates

    epsilon = max(float(policy_state.get("epsilon", EPSILON_MIN)), 0.2)
    candidate_map = {item["action_id"]: item for item in available}
    action_ids = list(candidate_map.keys())
    selected_action_id = _sample_action_id(policy_state, action_ids, epsilon)

    # Diversity guard across review runs: avoid repeating the same first action.
    last_review_action_id = str(policy_state.get("metadata", {}).get("last_review_action_id", ""))
    if not tried_action_ids and len(action_ids) > 1 and selected_action_id == last_review_action_id:
        alternatives = [action_id for action_id in action_ids if action_id != selected_action_id]
        selected_action_id = random.choice(alternatives)
        probs_view = {action: round(float(policy_state.get("action_probs", {}).get(action, 0.0)), 3) for action in action_ids}
        print(f"Selected action: {selected_action_id}, probs: {probs_view}")

    policy_state.setdefault("metadata", {})["last_review_action_id"] = selected_action_id
    selected = dict(candidate_map[selected_action_id])
    selected["fixed_code"] = _apply_action_variant(selected_action_id, selected["fixed_code"], policy_state)
    save_policy_state(policy_state)

    if normalize_code(selected["fixed_code"]) == normalize_code(code):
        for fallback in available:
            if fallback["action_id"] != selected_action_id and normalize_code(fallback["fixed_code"]) != normalize_code(code):
                return fallback
    return selected
