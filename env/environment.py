from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from env.reward import RewardEngine


@dataclass
class CodeTask:
    task_id: str
    title: str
    instruction: str
    buggy_code: str
    fixed_code: str
    function_name: str
    test_cases: List[Dict[str, Any]]
    max_steps: int = 3


@dataclass
class EpisodeData:
    task: Optional[CodeTask] = None
    original_code: str = ""
    current_code: str = ""
    step_count: int = 0
    max_steps: int = 4
    done: bool = False
    tests_passed: int = 0
    tests_total: int = 0
    total_reward: float = 0.0
    last_step_reward: Optional[float] = None
    history: List[Dict[str, Any]] = field(default_factory=list)


TASKS: Dict[str, CodeTask] = {
    "easy": CodeTask(
        task_id="arena-001",
        title="Fix index error",
        instruction="Fix the index error so the function returns the third item safely.",
        buggy_code=(
            "def get_third_item(items):\n"
            "    return items[3]\n"
        ),
        fixed_code=(
            "def get_third_item(items):\n"
            "    return items[2]\n"
        ),
        function_name="get_third_item",
        test_cases=[
            {"args": [[1, 2, 3, 4]], "expected": 3},
            {"args": [[9, 8, 7, 6]], "expected": 7},
            {"args": [[0, 1, 2, 3, 4]], "expected": 2},
        ],
        max_steps=3,
    ),
    "medium": CodeTask(
        task_id="arena-002",
        title="Fix syntax error",
        instruction="Fix the missing colon so the function runs.",
        buggy_code=(
            "def greet(name)\n"
            "    return 'hi ' + name\n"
        ),
        fixed_code=(
            "def greet(name):\n"
            "    return 'hi ' + name\n"
        ),
        function_name="greet",
        test_cases=[
            {"args": ["Ada"], "expected": "hi Ada"},
            {"args": ["Bob"], "expected": "hi Bob"},
        ],
        max_steps=3,
    ),
    "hard": CodeTask(
        task_id="arena-003",
        title="Fix division by zero",
        instruction="Return 0 when the denominator is zero.",
        buggy_code=(
            "def safe_div(a, b):\n"
            "    return a / b\n"
        ),
        fixed_code=(
            "def safe_div(a, b):\n"
            "    if b == 0:\n"
            "        return 0\n"
            "    return a / b\n"
        ),
        function_name="safe_div",
        test_cases=[
            {"args": [10, 2], "expected": 5},
            {"args": [3, 0], "expected": 0},
            {"args": [8, 4], "expected": 2},
        ],
        max_steps=3,
    ),
    "bonus": CodeTask(
        task_id="arena-004",
        title="Fix off-by-one loop",
        instruction="Return the sum of numbers from 0 through n inclusive.",
        buggy_code=(
            "def sum_to_n(n):\n"
            "    total = 0\n"
            "    for i in range(n):\n"
            "        total += i\n"
            "    return total\n"
        ),
        fixed_code=(
            "def sum_to_n(n):\n"
            "    total = 0\n"
            "    for i in range(n + 1):\n"
            "        total += i\n"
            "    return total\n"
        ),
        function_name="sum_to_n",
        test_cases=[
            {"args": [3], "expected": 6},
            {"args": [1], "expected": 1},
            {"args": [0], "expected": 0},
        ],
        max_steps=3,
    ),
    "list_len": CodeTask(
        task_id="arena-005",
        title="Fix length check",
        instruction="Return True when the list has at least three items.",
        buggy_code=(
            "def has_three(items):\n"
            "    return len(items) > 3\n"
        ),
        fixed_code=(
            "def has_three(items):\n"
            "    return len(items) >= 3\n"
        ),
        function_name="has_three",
        test_cases=[
            {"args": [[1, 2, 3]], "expected": True},
            {"args": [[1, 2]], "expected": False},
            {"args": [[1, 2, 3, 4]], "expected": True},
        ],
        max_steps=3,
    ),
    "none_lower": CodeTask(
        task_id="arena-006",
        title="Handle None before lower",
        instruction="Return an empty string when name is None, otherwise lowercase it.",
        buggy_code=(
            "def normalize_name(name):\n"
            "    return name.lower()\n"
        ),
        fixed_code=(
            "def normalize_name(name):\n"
            "    if name is None:\n"
            "        return ''\n"
            "    return name.lower()\n"
        ),
        function_name="normalize_name",
        test_cases=[
            {"args": ["ADA"], "expected": "ada"},
            {"args": [None], "expected": ""},
            {"args": ["Bob"], "expected": "bob"},
        ],
        max_steps=3,
    ),
    "max_init": CodeTask(
        task_id="arena-007",
        title="Fix max initialization",
        instruction="Return the maximum value, including when all values are negative.",
        buggy_code=(
            "def max_value(nums):\n"
            "    best = 0\n"
            "    for n in nums:\n"
            "        if n > best:\n"
            "            best = n\n"
            "    return best\n"
        ),
        fixed_code=(
            "def max_value(nums):\n"
            "    best = nums[0]\n"
            "    for n in nums:\n"
            "        if n > best:\n"
            "            best = n\n"
            "    return best\n"
        ),
        function_name="max_value",
        test_cases=[
            {"args": [[1, 4, 2]], "expected": 4},
            {"args": [[-5, -2, -9]], "expected": -2},
            {"args": [[7]], "expected": 7},
        ],
        max_steps=3,
    ),
    "first_item": CodeTask(
        task_id="arena-008",
        title="Fix first item",
        instruction="Return the first item in the list.",
        buggy_code=(
            "def first_item(items):\n"
            "    return items[1]\n"
        ),
        fixed_code=(
            "def first_item(items):\n"
            "    return items[0]\n"
        ),
        function_name="first_item",
        test_cases=[
            {"args": [[5, 6, 7]], "expected": 5},
            {"args": [["a", "b"]], "expected": "a"},
        ],
        max_steps=3,
    ),
}


class MultiAgentCodeRefinementEnv:
    """OpenEnv-compatible multi-agent code refinement environment.

    Contract:
    - reset()
    - step(action)
    - state()

    Per-step roles:
    - Reviewer Agent: identifies issues
    - Fixer Agent: proposes improved code
    - Evaluator Agent: computes verifiable reward
    """

    def __init__(self) -> None:
        self._reward_engine = RewardEngine()
        self._episode = EpisodeData()
        self._last_info: Dict[str, Any] = {}

    def reset(self, task_type: str = "easy") -> Dict[str, Any]:
        if task_type not in TASKS:
            task_type = "easy"
        task = TASKS[task_type]

        self._episode = EpisodeData(
            task=task,
            original_code=task.buggy_code,
            current_code=task.buggy_code,
            step_count=0,
            max_steps=max(3, min(task.max_steps, 5)),
            done=False,
            tests_passed=0,
            tests_total=len(task.test_cases),
            total_reward=0.0,
            last_step_reward=None,
            history=[],
        )
        self._last_info = {
            "reward_components": {},
            "tests_passed": 0,
            "tests_total": len(task.test_cases),
            "all_tests_passed": False,
        }
        return self.state()

    def _default_reviewer(self, code: str) -> List[str]:
        issues: List[str] = []
        if "[:-1]" in code:
            issues.append("Potential off-by-one bug due to slicing nums[:-1].")
        if " / b" in code and "if b == 0" not in code:
            issues.append("Possible division-by-zero without guard.")
        if ".lower()" in code and "None" not in code:
            issues.append("Calling lower() without None handling.")
        if not issues:
            issues.append("No obvious syntax errors; run tests to verify behavior.")
        return issues

    def _normalize_action(self, action: Any) -> Tuple[List[str], str]:
        if hasattr(action, "model_dump"):
            action_dict = action.model_dump()
        elif isinstance(action, dict):
            action_dict = action
        else:
            action_dict = {}

        reviewer_raw = action_dict.get("reviewer_issues", [])
        if isinstance(reviewer_raw, str):
            reviewer_issues = [reviewer_raw]
        elif isinstance(reviewer_raw, list):
            reviewer_issues = [str(item) for item in reviewer_raw if str(item).strip()]
        else:
            reviewer_issues = []

        fixed_code = str(action_dict.get("fixed_code", "")).strip()
        return reviewer_issues, fixed_code

    def step(self, action: Any) -> Tuple[Dict[str, Any], float, bool, Dict[str, Any]]:
        if self._episode.done:
            return self.state(), 0.0, True, {"message": "episode already done"}

        if self._episode.task is None:
            self.reset("easy")

        task = self._episode.task
        assert task is not None

        self._episode.step_count += 1
        reviewer_issues, fixed_code = self._normalize_action(action)

        if not reviewer_issues:
            reviewer_issues = self._default_reviewer(self._episode.current_code)

        if not fixed_code:
            fixed_code = self._episode.current_code

        result = self._reward_engine.compute_reward(
            previous_code=self._episode.current_code,
            candidate_code=fixed_code,
            previous_passed=self._episode.tests_passed,
            function_name=task.function_name,
            test_cases=task.test_cases,
        )

        # Prevent state corruption from invalid/trivial actions.
        if result["syntax_ok"] and not result["empty_or_trivial"]:
            self._episode.current_code = fixed_code

        base_reward = float(result["reward"])
        improvement_bonus = 0.0
        if self._episode.last_step_reward is not None and base_reward > self._episode.last_step_reward:
            improvement_bonus = 0.2
            result["components"]["improvement_bonus"] = improvement_bonus

        step_reward = max(min(base_reward + improvement_bonus, 2.0), -1.0)
        result["reward"] = step_reward

        self._episode.tests_passed = result["tests_passed"]
        self._episode.tests_total = result["tests_total"]
        self._episode.total_reward += step_reward
        self._episode.last_step_reward = base_reward

        step_record = {
            "step": self._episode.step_count,
            "reviewer_output": reviewer_issues,
            "fixer_output": fixed_code,
            "reward": result["reward"],
            "reward_components": result["components"],
            "tests_passed": result["tests_passed"],
            "tests_total": result["tests_total"],
            "syntax_ok": result["syntax_ok"],
        }
        self._episode.history.append(step_record)

        self._episode.done = (
            self._episode.step_count >= self._episode.max_steps
            or bool(result["all_tests_passed"])
        )

        self._last_info = {
            "reward_components": result["components"],
            "tests_passed": result["tests_passed"],
            "tests_total": result["tests_total"],
            "all_tests_passed": result["all_tests_passed"],
            "test_details": result["test_details"],
            "syntax_ok": result["syntax_ok"],
            "meaningful_change": result["meaningful_change"],
            "bug_signatures_before": result["bug_signatures_before"],
            "bug_signatures_after": result["bug_signatures_after"],
        }

        return self.state(), float(result["reward"]), self._episode.done, self._last_info

    def state(self) -> Dict[str, Any]:
        if self._episode.task is None:
            return {}

        previous_step_output = self._episode.history[-1] if self._episode.history else None

        return {
            "task_id": self._episode.task.task_id,
            "title": self._episode.task.title,
            "instruction": self._episode.task.instruction,
            "buggy_code": self._episode.original_code,
            "current_code": self._episode.current_code,
            "previous_step_output": previous_step_output,
            "step_count": self._episode.step_count,
            "max_steps": self._episode.max_steps,
            "tests_passed": self._episode.tests_passed,
            "tests_total": self._episode.tests_total,
            "total_reward": self._episode.total_reward,
            "history": self._episode.history,
            "done": self._episode.done,
        }

    def get_task_catalog(self) -> List[Dict[str, Any]]:
        return [
            {
                "task_type": key,
                "task_id": task.task_id,
                "title": task.title,
                "instruction": task.instruction,
                "buggy_code": task.buggy_code,
                "fixed_code": task.fixed_code,
                "max_steps": task.max_steps,
                "action_schema": {
                    "type": "object",
                    "required": ["fixed_code"],
                    "properties": {
                        "reviewer_issues": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                        "fixed_code": {"type": "string"},
                    },
                },
            }
            for key, task in TASKS.items()
        ]

    def get_last_grader_result(self) -> Dict[str, Any]:
        return {
            "step_count": self._episode.step_count,
            "tests_passed": self._episode.tests_passed,
            "tests_total": self._episode.tests_total,
            "total_reward": self._episode.total_reward,
            "last_info": self._last_info,
        }


# Backward-compatible alias used by API and inference wiring.
CodeReviewEnv = MultiAgentCodeRefinementEnv
