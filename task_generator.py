"""
task_generator.py — Procedural bug task generator for OpenEnv Code Review.

Generates unlimited unique Python bug-fixing tasks programmatically.
This replaces the 8 hard-coded tasks with infinite curriculum-ready tasks.

Usage:
    from env.task_generator import generate_task, generate_curriculum
    task = generate_task(difficulty="medium", seed=42)
    curriculum = generate_curriculum(n=20, seed=0)
"""

from __future__ import annotations

import random
import textwrap
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# ── Data model ────────────────────────────────────────────────────────────────

@dataclass
class GeneratedTask:
    task_id: str
    difficulty: str          # easy | medium | hard
    bug_type: str            # human-readable bug category
    instruction: str
    buggy_code: str
    fixed_code: str
    function_name: str
    tests: List[Dict[str, Any]]
    max_steps: int = 3


# ── Bug strategy registry ─────────────────────────────────────────────────────
# Each strategy is a callable: (rng) -> GeneratedTask | None

def _off_by_one_index(rng: random.Random) -> GeneratedTask:
    """items[N+1] when items[N] is correct."""
    size = rng.randint(3, 8)
    target_idx = rng.randint(0, size - 2)
    wrong_idx  = target_idx + 1
    items_name = rng.choice(["items", "values", "nums", "data", "lst"])
    fn_names   = ["get_element", "fetch_item", "pick_value", "read_entry", "extract"]
    fn_name    = rng.choice(fn_names)

    buggy = textwrap.dedent(f"""\
        def {fn_name}({items_name}):
            return {items_name}[{wrong_idx}]
    """)
    fixed = textwrap.dedent(f"""\
        def {fn_name}({items_name}):
            return {items_name}[{target_idx}]
    """)

    # Build test cases
    tests = []
    for _ in range(3):
        lst = [rng.randint(0, 99) for _ in range(size)]
        tests.append({"args": [lst], "expected": lst[target_idx]})

    return GeneratedTask(
        task_id=f"gen-obi-{rng.randint(1000,9999)}",
        difficulty="easy",
        bug_type="off_by_one_index",
        instruction=f"Fix the index error so the function returns element at position {target_idx}.",
        buggy_code=buggy,
        fixed_code=fixed,
        function_name=fn_name,
        tests=tests,
    )


def _missing_colon(rng: random.Random) -> GeneratedTask:
    """Missing colon after def or if statement."""
    fn_name = rng.choice(["process", "transform", "compute", "handle", "evaluate"])
    param   = rng.choice(["x", "n", "val", "data", "item"])
    op      = rng.choice([
        (f"return {param} * 2",  f"{param} * 2",  lambda v: v * 2),
        (f"return {param} + 1",  f"{param} + 1",  lambda v: v + 1),
        (f"return {param} - 1",  f"{param} - 1",  lambda v: v - 1),
        (f"return abs({param})", f"abs({param})", lambda v: abs(v)),
    ])
    body, _, fn = op

    buggy = f"def {fn_name}({param})\n    {body}\n"
    fixed = f"def {fn_name}({param}):\n    {body}\n"

    tests = []
    for _ in range(3):
        v = rng.randint(-10, 10)
        tests.append({"args": [v], "expected": fn(v)})

    return GeneratedTask(
        task_id=f"gen-colon-{rng.randint(1000,9999)}",
        difficulty="easy",
        bug_type="missing_colon",
        instruction="Fix the syntax error — a colon is missing from the function definition.",
        buggy_code=buggy,
        fixed_code=fixed,
        function_name=fn_name,
        tests=tests,
    )


def _division_zero(rng: random.Random) -> GeneratedTask:
    """Division without zero guard."""
    fn_name  = rng.choice(["safe_divide", "ratio", "compute_rate", "avg_per", "divide"])
    a_param  = rng.choice(["a", "numerator", "total", "value"])
    b_param  = rng.choice(["b", "denominator", "count", "n"])
    fallback = rng.choice([0, -1, None])
    fb_str   = str(fallback)

    buggy = textwrap.dedent(f"""\
        def {fn_name}({a_param}, {b_param}):
            return {a_param} / {b_param}
    """)
    fixed = textwrap.dedent(f"""\
        def {fn_name}({a_param}, {b_param}):
            if {b_param} == 0:
                return {fb_str}
            return {a_param} / {b_param}
    """)

    def expected(a, b):
        if b == 0:
            return fallback
        return a / b

    tests = [
        {"args": [10, 2],  "expected": expected(10, 2)},
        {"args": [0, 5],   "expected": expected(0, 5)},
        {"args": [9, 0],   "expected": expected(9, 0)},
    ]

    return GeneratedTask(
        task_id=f"gen-divz-{rng.randint(1000,9999)}",
        difficulty="medium",
        bug_type="division_by_zero",
        instruction=f"Add a zero-division guard — return {fb_str} when {b_param} is zero.",
        buggy_code=buggy,
        fixed_code=fixed,
        function_name=fn_name,
        tests=tests,
    )


def _none_guard(rng: random.Random) -> GeneratedTask:
    """Method called on potentially None value."""
    strategies = [
        {
            "param": "name", "method": ".strip()", "fallback": "''",
            "buggy": "def clean(name):\n    return name.strip()\n",
            "fixed": "def clean(name):\n    if name is None:\n        return ''\n    return name.strip()\n",
            "fn": "clean",
            "tests": [
                {"args": ["  hello  "], "expected": "hello"},
                {"args": [None],        "expected": ""},
                {"args": ["world"],     "expected": "world"},
            ],
            "instruction": "Return empty string when name is None, otherwise strip whitespace.",
        },
        {
            "param": "text", "method": ".upper()", "fallback": "''",
            "buggy": "def shout(text):\n    return text.upper()\n",
            "fixed": "def shout(text):\n    if text is None:\n        return ''\n    return text.upper()\n",
            "fn": "shout",
            "tests": [
                {"args": ["hello"], "expected": "HELLO"},
                {"args": [None],    "expected": ""},
                {"args": ["ok"],    "expected": "OK"},
            ],
            "instruction": "Return empty string when text is None, otherwise uppercase it.",
        },
        {
            "param": "s", "method": ".split()", "fallback": "[]",
            "buggy": "def words(s):\n    return s.split()\n",
            "fixed": "def words(s):\n    if s is None:\n        return []\n    return s.split()\n",
            "fn": "words",
            "tests": [
                {"args": ["hello world"], "expected": ["hello", "world"]},
                {"args": [None],          "expected": []},
                {"args": ["one"],         "expected": ["one"]},
            ],
            "instruction": "Return an empty list when s is None, otherwise split the string.",
        },
    ]
    s = rng.choice(strategies)
    return GeneratedTask(
        task_id=f"gen-none-{rng.randint(1000,9999)}",
        difficulty="medium",
        bug_type="none_guard",
        instruction=s["instruction"],
        buggy_code=s["buggy"],
        fixed_code=s["fixed"],
        function_name=s["fn"],
        tests=s["tests"],
    )


def _wrong_comparison(rng: random.Random) -> GeneratedTask:
    """Wrong comparison operator (> vs >=, < vs <=, == vs !=)."""
    n = rng.randint(2, 6)
    strategies = [
        {
            "fn": "has_enough",
            "param": "items",
            "buggy_op": ">",
            "fixed_op": ">=",
            "val": n,
            "buggy": f"def has_enough(items):\n    return len(items) > {n}\n",
            "fixed": f"def has_enough(items):\n    return len(items) >= {n}\n",
            "tests": [
                {"args": [list(range(n))],     "expected": True},
                {"args": [list(range(n - 1))], "expected": False},
                {"args": [list(range(n + 1))], "expected": True},
            ],
            "instruction": f"Return True when the list has at least {n} items (fix the comparison operator).",
        },
        {
            "fn": "is_adult",
            "param": "age",
            "buggy_op": ">",
            "fixed_op": ">=",
            "val": 18,
            "buggy": "def is_adult(age):\n    return age > 18\n",
            "fixed": "def is_adult(age):\n    return age >= 18\n",
            "tests": [
                {"args": [18], "expected": True},
                {"args": [17], "expected": False},
                {"args": [25], "expected": True},
            ],
            "instruction": "Return True when age is 18 or older (fix the off-by-one comparison).",
        },
        {
            "fn": "is_zero",
            "param": "n",
            "buggy_op": "!=",
            "fixed_op": "==",
            "val": 0,
            "buggy": "def is_zero(n):\n    return n != 0\n",
            "fixed": "def is_zero(n):\n    return n == 0\n",
            "tests": [
                {"args": [0],  "expected": True},
                {"args": [1],  "expected": False},
                {"args": [-1], "expected": False},
            ],
            "instruction": "Return True only when n is zero (fix the comparison operator).",
        },
    ]
    s = rng.choice(strategies)
    return GeneratedTask(
        task_id=f"gen-cmp-{rng.randint(1000,9999)}",
        difficulty="easy",
        bug_type="wrong_comparison",
        instruction=s["instruction"],
        buggy_code=s["buggy"],
        fixed_code=s["fixed"],
        function_name=s["fn"],
        tests=s["tests"],
    )


def _wrong_loop_range(rng: random.Random) -> GeneratedTask:
    """range(n) vs range(n+1) off-by-one in accumulation."""
    fn_name = rng.choice(["sum_to", "count_up", "accumulate", "total_to"])
    param   = rng.choice(["n", "limit", "end", "top"])

    buggy = textwrap.dedent(f"""\
        def {fn_name}({param}):
            total = 0
            for i in range({param}):
                total += i
            return total
    """)
    fixed = textwrap.dedent(f"""\
        def {fn_name}({param}):
            total = 0
            for i in range({param} + 1):
                total += i
            return total
    """)

    def expected(v):
        return sum(range(v + 1))

    tests = []
    for v in [rng.randint(2, 8) for _ in range(3)]:
        tests.append({"args": [v], "expected": expected(v)})

    return GeneratedTask(
        task_id=f"gen-loop-{rng.randint(1000,9999)}",
        difficulty="medium",
        bug_type="off_by_one_loop",
        instruction=f"Fix the loop so it sums numbers from 0 through {param} inclusive.",
        buggy_code=buggy,
        fixed_code=fixed,
        function_name=fn_name,
        tests=tests,
    )


def _wrong_max_init(rng: random.Random) -> GeneratedTask:
    """max initialized to 0 instead of first element."""
    fn_name = rng.choice(["max_val", "find_max", "peak", "largest"])
    param   = rng.choice(["nums", "values", "data", "arr"])

    buggy = textwrap.dedent(f"""\
        def {fn_name}({param}):
            best = 0
            for n in {param}:
                if n > best:
                    best = n
            return best
    """)
    fixed = textwrap.dedent(f"""\
        def {fn_name}({param}):
            best = {param}[0]
            for n in {param}:
                if n > best:
                    best = n
            return best
    """)

    def expected(lst):
        return max(lst)

    all_neg  = [rng.randint(-20, -1) for _ in range(4)]
    mixed    = [rng.randint(-5, 5)   for _ in range(4)]
    all_pos  = [rng.randint(1, 20)   for _ in range(4)]

    tests = [
        {"args": [all_neg],  "expected": expected(all_neg)},
        {"args": [mixed],    "expected": expected(mixed)},
        {"args": [all_pos],  "expected": expected(all_pos)},
    ]

    return GeneratedTask(
        task_id=f"gen-max-{rng.randint(1000,9999)}",
        difficulty="hard",
        bug_type="wrong_initialisation",
        instruction="Fix the initialisation so the function works correctly even when all values are negative.",
        buggy_code=buggy,
        fixed_code=fixed,
        function_name=fn_name,
        tests=tests,
    )


def _missing_return(rng: random.Random) -> GeneratedTask:
    """Function missing a return in one branch."""
    val = rng.randint(1, 10)
    fn_name = rng.choice(["double_if_pos", "boost", "amplify", "scale"])

    buggy = textwrap.dedent(f"""\
        def {fn_name}(x):
            if x > 0:
                return x * {val}
    """)
    fixed = textwrap.dedent(f"""\
        def {fn_name}(x):
            if x > 0:
                return x * {val}
            return 0
    """)

    tests = [
        {"args": [3],  "expected": 3 * val},
        {"args": [-1], "expected": 0},
        {"args": [0],  "expected": 0},
    ]

    return GeneratedTask(
        task_id=f"gen-ret-{rng.randint(1000,9999)}",
        difficulty="medium",
        bug_type="missing_return",
        instruction="Add a return statement for the case when x is not positive.",
        buggy_code=buggy,
        fixed_code=fixed,
        function_name=fn_name,
        tests=tests,
    )


# ── Strategy registry by difficulty ──────────────────────────────────────────

EASY_STRATEGIES   = [_off_by_one_index, _missing_colon, _wrong_comparison]
MEDIUM_STRATEGIES = [_division_zero, _none_guard, _wrong_loop_range, _missing_return]
HARD_STRATEGIES   = [_wrong_max_init, _division_zero, _none_guard]

ALL_STRATEGIES = {
    "easy":   EASY_STRATEGIES,
    "medium": MEDIUM_STRATEGIES,
    "hard":   HARD_STRATEGIES,
}


# ── Public API ────────────────────────────────────────────────────────────────

def generate_task(
    difficulty: str = "medium",
    seed: Optional[int] = None,
) -> Optional[GeneratedTask]:
    """
    Generate a single unique bug-fixing task.

    Args:
        difficulty: "easy" | "medium" | "hard"
        seed: random seed for reproducibility (None = random)

    Returns:
        GeneratedTask or None if difficulty is invalid
    """
    if difficulty not in ALL_STRATEGIES:
        difficulty = "medium"

    rng = random.Random(seed)
    strategy = rng.choice(ALL_STRATEGIES[difficulty])
    try:
        return strategy(rng)
    except Exception:
        # Fallback to a different strategy on error
        for s in ALL_STRATEGIES[difficulty]:
            try:
                return s(rng)
            except Exception:
                continue
    return None


def generate_curriculum(
    n: int = 20,
    seed: int = 42,
) -> List[GeneratedTask]:
    """
    Generate n tasks in curriculum order: easy → medium → hard.

    This is designed for training scripts — the agent sees easy
    tasks first and progressively harder ones as training proceeds.

    Args:
        n:    total number of tasks
        seed: base random seed

    Returns:
        List of GeneratedTask ordered by difficulty
    """
    rng = random.Random(seed)
    tasks: List[GeneratedTask] = []

    # Distribution: 40% easy, 40% medium, 20% hard
    counts = {
        "easy":   max(1, int(n * 0.40)),
        "medium": max(1, int(n * 0.40)),
        "hard":   max(1, n - int(n * 0.40) - int(n * 0.40)),
    }

    for difficulty, count in counts.items():
        for i in range(count):
            task_seed = rng.randint(0, 999_999)
            task = generate_task(difficulty=difficulty, seed=task_seed)
            if task:
                tasks.append(task)

    # Sort: easy first, then medium, then hard
    order = {"easy": 0, "medium": 1, "hard": 2}
    tasks.sort(key=lambda t: order.get(t.difficulty, 1))
    return tasks


def task_to_env_format(task: GeneratedTask) -> dict:
    """Convert a GeneratedTask to the same dict format as env.reset()."""
    return {
        "task_id":      task.task_id,
        "title":        task.bug_type.replace("_", " ").title(),
        "instruction":  task.instruction,
        "buggy_code":   task.buggy_code,
        "current_code": task.buggy_code,
        "tests_passed": 0,
        "tests_total":  len(task.tests),
        "total_reward": 0.0,
        "done":         False,
        "step_count":   0,
        "max_steps":    task.max_steps,
        "history":      [],
    }


# ── Quick self-test ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=== Curriculum sample ===")
    curriculum = generate_curriculum(n=12, seed=42)
    for t in curriculum:
        print(f"  [{t.difficulty:6s}] {t.bug_type:25s}  {t.task_id}  fn={t.function_name}")

    print("\n=== Single task (hard, seed=7) ===")
    task = generate_task("hard", seed=7)
    if task:
        print(f"Bug type:    {task.bug_type}")
        print(f"Instruction: {task.instruction}")
        print("Buggy code:")
        print(task.buggy_code)
        print("Fixed code:")
        print(task.fixed_code)
        print(f"Tests:       {len(task.tests)} cases")

    print("\n=== Uniqueness check (10 easy tasks) ===")
    ids = set()
    for i in range(10):
        t = generate_task("easy", seed=i * 17)
        if t:
            ids.add(t.task_id)
            print(f"  seed={i*17:4d}  {t.task_id}  fn={t.function_name}")
    print(f"Unique IDs: {len(ids)}/10")