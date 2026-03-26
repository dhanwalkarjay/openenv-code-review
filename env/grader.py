from typing import Dict, List, Set

from env.models import Action, GraderResult, TaskSpec


def _matches_finding(action: Action, keywords: List[str]) -> bool:
    text = f"{action.comment} {action.suggested_fix or ''}".lower()
    return any(keyword.lower() in text for keyword in keywords)


def grade_episode(actions: List[Action], task: TaskSpec) -> GraderResult:
    if not actions:
        return GraderResult(
            score=0.0,
            coverage=0.0,
            precision=0.0,
            line_accuracy=0.0,
            fix_quality=0.0,
            matched_findings=[],
        )

    finding_to_actions: Dict[str, List[Action]] = {f.finding_id: [] for f in task.expected_findings}
    matched_action_indexes: Set[int] = set()

    for idx, action in enumerate(actions):
        for finding in task.expected_findings:
            if _matches_finding(action, finding.keywords):
                finding_to_actions[finding.finding_id].append(action)
                matched_action_indexes.add(idx)

    matched_findings = sorted([fid for fid, vals in finding_to_actions.items() if vals])
    coverage = len(matched_findings) / len(task.expected_findings)
    precision = len(matched_action_indexes) / len(actions)

    line_hits = 0
    checked = 0
    fix_hits = 0
    for finding in task.expected_findings:
        candidates = finding_to_actions[finding.finding_id]
        if not candidates:
            continue
        checked += 1
        if any(abs(a.line_number - finding.expected_line) <= 1 for a in candidates):
            line_hits += 1
        if any(a.suggested_fix and len(a.suggested_fix.strip()) >= 12 for a in candidates):
            fix_hits += 1

    line_accuracy = (line_hits / checked) if checked else 0.0
    fix_quality = (fix_hits / checked) if checked else 0.0

    score = (0.5 * coverage) + (0.2 * precision) + (0.15 * line_accuracy) + (0.15 * fix_quality)

    return GraderResult(
        score=min(max(score, 0.0), 1.0),
        coverage=coverage,
        precision=precision,
        line_accuracy=line_accuracy,
        fix_quality=fix_quality,
        matched_findings=matched_findings,
    )