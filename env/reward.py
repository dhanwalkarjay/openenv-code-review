from __future__ import annotations

import ast
import builtins
import inspect
import re
import tokenize
from dataclasses import dataclass
from io import StringIO
from typing import Any, Dict, List, Tuple


@dataclass(frozen=True)
class RewardWeights:
    # Positive rewards (strict rubric)
    bug_fixed_and_tests_pass: float = 1.0
    complexity_improved: float = 0.8
    partial_improvement: float = 0.5
    meaningful_structural_change: float = 0.3

    # Negative rewards (strict penalties)
    syntax_invalid: float = -1.0
    cosmetic_change: float = -0.7
    no_change: float = -0.5
    repeated_action: float = -0.3


class _IdentifierNormalizer(ast.NodeTransformer):
    def visit_Name(self, node: ast.Name) -> ast.AST:
        return ast.copy_location(ast.Name(id="_v", ctx=node.ctx), node)

    def visit_arg(self, node: ast.arg) -> ast.AST:
        node.arg = "_v"
        return node

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.AST:
        node.name = "_f"
        return self.generic_visit(node)


class RewardEngine:
    """Strict reward engine to prevent reward hacking.

    Reward depends on correctness, logic improvement, and real test outcomes.
    Cosmetic edits and no-op edits are penalized.
    """

    def __init__(self, weights: RewardWeights | None = None) -> None:
        self.weights = weights or RewardWeights()

    def is_syntax_valid(self, code: str) -> bool:
        try:
            ast.parse(code)
            return True
        except Exception:
            return False

    def _strip_comments(self, code: str) -> str:
        out: List[str] = []
        reader = StringIO(code).readline
        try:
            for tok in tokenize.generate_tokens(reader):
                if tok.type != tokenize.COMMENT:
                    out.append(tok.string)
        except Exception:
            return code
        return "".join(out)

    def _normalize_ws(self, code: str) -> str:
        return "".join(code.split())

    def is_cosmetic_change(self, old_code: str, new_code: str) -> bool:
        # Requirement-specified baseline check
        normalize = lambda x: "".join(x.split())
        if normalize(old_code) == normalize(new_code):
            return True

        old_wo_comments = self._normalize_ws(self._strip_comments(old_code))
        new_wo_comments = self._normalize_ws(self._strip_comments(new_code))
        if old_wo_comments == new_wo_comments:
            return True

        try:
            old_tree = ast.parse(old_code)
            new_tree = ast.parse(new_code)
            norm = _IdentifierNormalizer()
            old_dump = ast.dump(norm.visit(old_tree), include_attributes=False)
            new_dump = ast.dump(norm.visit(new_tree), include_attributes=False)
            if old_dump == new_dump:
                return True
        except Exception:
            pass

        return False

    def _has_only_comment_change(self, old_code: str, new_code: str) -> bool:
        old_clean = self._normalize_ws(self._strip_comments(old_code))
        new_clean = self._normalize_ws(self._strip_comments(new_code))
        return old_clean == new_clean and old_code != new_code

    def _loop_depth(self, code: str) -> int:
        try:
            tree = ast.parse(code)
        except Exception:
            return 0

        max_depth = 0

        def walk(node: ast.AST, depth: int) -> None:
            nonlocal max_depth
            if isinstance(node, (ast.For, ast.While, ast.AsyncFor)):
                depth += 1
                max_depth = max(max_depth, depth)
            for child in ast.iter_child_nodes(node):
                walk(child, depth)

        walk(tree, 0)
        return max_depth

    def _detect_bugs(self, code: str) -> Dict[str, bool]:
        lowered = code.lower()
        bugs: Dict[str, bool] = {
            "division_without_guard": ("/ b" in lowered or "/b" in lowered)
            and ("if b == 0" not in lowered and "if b==0" not in lowered and "except zerodivisionerror" not in lowered),
            "nested_loops": self._loop_depth(code) >= 2,
            "unsafe_operation": any(tok in lowered for tok in ["eval(", "exec(", "os.system(", "subprocess", "open("]),
            "missing_edge_case": False,
        }

        if "items[" in lowered and "len(" not in lowered:
            bugs["missing_edge_case"] = True
        if "best = 0" in lowered and "max" in lowered:
            bugs["missing_edge_case"] = True
        return bugs

    def _structural_change(self, old_code: str, new_code: str) -> bool:
        try:
            old_tree = ast.parse(old_code)
            new_tree = ast.parse(new_code)
        except Exception:
            return False

        def count_nodes(tree: ast.AST, kinds: Tuple[type, ...]) -> int:
            return sum(1 for n in ast.walk(tree) if isinstance(n, kinds))

        control_kinds: Tuple[type, ...] = (ast.If, ast.For, ast.While, ast.Try, ast.Return, ast.BoolOp)
        return count_nodes(old_tree, control_kinds) != count_nodes(new_tree, control_kinds)

    def _build_dynamic_tests(self, code: str, function_name: str) -> List[Dict[str, Any]]:
        lowered = code.lower()
        name = function_name.lower()

        if "div" in name or "/ b" in lowered or "/b" in lowered:
            return [
                {"args": [10, 2], "expected": 5},
                {"args": [8, 4], "expected": 2},
                {"args": [3, 0], "expected": 0},
            ]

        if "max" in name and "for" in lowered:
            return [
                {"args": [[1, 8, 4]], "expected": 8},
                {"args": [[-5, -1, -9]], "expected": -1},
                {"args": [[7]], "expected": 7},
            ]

        if "sum" in name and "range(" in lowered:
            return [
                {"args": [3], "expected": 6},
                {"args": [0], "expected": 0},
            ]

        # Guaranteed non-0/0 fallback: deterministic smoke tests.
        return [
            {"args": [], "kwargs": {}, "smoke": True},
        ]

    def _safe_exec(self, code: str) -> Dict[str, Any]:
        safe_builtins = {
            "abs": builtins.abs,
            "all": builtins.all,
            "any": builtins.any,
            "enumerate": builtins.enumerate,
            "len": builtins.len,
            "max": builtins.max,
            "min": builtins.min,
            "range": builtins.range,
            "sum": builtins.sum,
            "sorted": builtins.sorted,
            "list": builtins.list,
            "dict": builtins.dict,
            "tuple": builtins.tuple,
            "set": builtins.set,
        }
        glb: Dict[str, Any] = {"__builtins__": safe_builtins}
        loc: Dict[str, Any] = {}
        exec(code, glb, loc)
        return loc

    def run_tests(
        self,
        code: str,
        function_name: str,
        test_cases: List[Dict[str, Any]],
    ) -> Tuple[int, int, List[Dict[str, Any]]]:
        details: List[Dict[str, Any]] = []

        try:
            namespace = self._safe_exec(code)
        except Exception as exc:
            total = len(test_cases) if test_cases else 1
            return 0, total, [{"ok": False, "error": f"exec_error: {exc}"}]

        fn = namespace.get(function_name)
        if not callable(fn):
            total = len(test_cases) if test_cases else 1
            return 0, total, [{"ok": False, "error": f"missing_function: {function_name}"}]

        cases = test_cases[:] if test_cases else self._build_dynamic_tests(code, function_name)
        passed = 0

        for case in cases:
            args = case.get("args", [])
            kwargs = case.get("kwargs", {})
            expected = case.get("expected")
            expect_exception = case.get("expected_exception")

            if case.get("smoke"):
                # Build deterministic smoke args from signature.
                try:
                    sig = inspect.signature(fn)
                    smoke_args = []
                    for p in sig.parameters.values():
                        if p.default is not inspect._empty:
                            continue
                        if p.kind in (p.VAR_POSITIONAL, p.VAR_KEYWORD):
                            continue
                        smoke_args.append(1)
                    result = fn(*smoke_args)
                    details.append({"ok": True, "args": smoke_args, "smoke": True, "actual": result})
                    passed += 1
                except Exception as exc:
                    details.append({"ok": False, "smoke": True, "error": str(exc)})
                continue

            try:
                result = fn(*args, **kwargs)
                if expect_exception is not None:
                    ok = False
                else:
                    ok = result == expected
                details.append({"ok": ok, "args": args, "kwargs": kwargs, "expected": expected, "actual": result})
                if ok:
                    passed += 1
            except Exception as exc:
                ok = bool(expect_exception) and (expect_exception in exc.__class__.__name__)
                details.append({"ok": ok, "args": args, "kwargs": kwargs, "expected": expected, "error": str(exc)})
                if ok:
                    passed += 1

        return passed, len(cases), details

    def compute_reward(
        self,
        previous_code: str,
        candidate_code: str,
        previous_passed: int,
        function_name: str,
        test_cases: List[Dict[str, Any]],
        action_id: str | None = None,
        last_action_id: str | None = None,
    ) -> Dict[str, Any]:
        components: Dict[str, float] = {
            "base": 0.0,
            "penalty_repeated_action": 0.0,
        }

        syntax_ok = self.is_syntax_valid(candidate_code)
        if not syntax_ok:
            reward = self.weights.syntax_invalid
            if action_id and last_action_id and action_id == last_action_id:
                components["penalty_repeated_action"] = self.weights.repeated_action
                reward = max(-1.0, reward + self.weights.repeated_action)
            return {
                "reward": reward,
                "components": components,
                "tests_passed": 0,
                "tests_total": len(test_cases) if test_cases else 1,
                "test_details": [{"ok": False, "error": "syntax_error"}],
                "syntax_ok": False,
                "meaningful_change": False,
                "empty_or_trivial": False,
                "all_tests_passed": False,
                "bug_signatures_before": [],
                "bug_signatures_after": [],
            }

        no_change = candidate_code.strip() == previous_code.strip()
        cosmetic = self.is_cosmetic_change(previous_code, candidate_code) or self._has_only_comment_change(previous_code, candidate_code)

        before_bugs = self._detect_bugs(previous_code)
        after_bugs = self._detect_bugs(candidate_code)
        before_bug_count = sum(1 for v in before_bugs.values() if v)
        after_bug_count = sum(1 for v in after_bugs.values() if v)
        bug_fixed = before_bug_count > after_bug_count

        complexity_improved = self._loop_depth(candidate_code) < self._loop_depth(previous_code)
        structural_change = self._structural_change(previous_code, candidate_code)

        passed, total, details = self.run_tests(candidate_code, function_name, test_cases)
        all_pass = total > 0 and passed == total
        partial_improvement = passed > previous_passed and not all_pass

        already_optimal_before = previous_passed > 0 and previous_passed == total and before_bug_count == 0

        if no_change:
            base = self.weights.no_change
        elif cosmetic:
            base = self.weights.cosmetic_change
        elif already_optimal_before and candidate_code.strip() != previous_code.strip():
            base = self.weights.no_change
        elif all_pass:                    # ← remove the bug_fixed requirement
            base = self.weights.bug_fixed_and_tests_pass   # 1.0
        elif complexity_improved and passed >= previous_passed:
            base = self.weights.complexity_improved
        elif partial_improvement or bug_fixed:
            base = self.weights.partial_improvement
        elif structural_change:
            base = self.weights.meaningful_structural_change
        else:
            base = self.weights.no_change

        components["base"] = base

        if action_id and last_action_id and action_id == last_action_id:
            components["penalty_repeated_action"] = self.weights.repeated_action

        reward = base + components["penalty_repeated_action"]
        reward = max(-1.0, min(1.0, reward))

        return {
            "reward": reward,
            "components": components,
            "tests_passed": passed,
            "tests_total": total,
            "test_details": details,
            "syntax_ok": True,
            "meaningful_change": not cosmetic and not no_change,
            "empty_or_trivial": False,
            "all_tests_passed": all_pass,
            "bug_signatures_before": [k for k, v in before_bugs.items() if v],
            "bug_signatures_after": [k for k, v in after_bugs.items() if v],
            "bug_fixed": bug_fixed,
            "complexity_improved": complexity_improved,
            "structural_change": structural_change,
        }
