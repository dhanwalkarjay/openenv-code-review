from typing import List

from env.models import Action, GraderResult, TaskSpec


KEYWORDS = {
    "style": ["space", "format", "docstring"],
    "performance": ["list comprehension", "optimize"],
    "bug": ["zero", "error", "exception"],
}


def semantic_match(pred: str, ground_truth: str) -> float:
    pred = pred.lower()
    score = 0.0

    for _, words in KEYWORDS.items():
        if any(w in pred for w in words):
            if any(w in ground_truth.lower() for w in words):
                score += 0.5

    if ground_truth.lower() in pred:
        score += 0.5

    return min(score, 1.0)


def grade(predictions: List[str], ground_truth: List[str]) -> float:
    if not predictions:
        return 0.0

    total = 0.0
    for gt in ground_truth:
        best = max([semantic_match(p, gt) for p in predictions], default=0.0)
        total += best

    epsilon = 0.01
    raw_score = total / len(ground_truth) if ground_truth else 0.0
    return min(max(raw_score, epsilon), 1.0 - epsilon)


def grade_episode(actions: List[Action], task: TaskSpec) -> GraderResult:
    if not actions:
        return GraderResult(
            score=0.01,
            coverage=0.0,
            precision=0.0,
            line_accuracy=0.0,
            fix_quality=0.0,
            matched_findings=[],
        )

    predictions = [f"{a.comment} {a.suggested_fix or ''}".strip() for a in actions]
    finding_ground_truth = [
        f"{finding.description} {' '.join(finding.keywords)}".strip()
        for finding in task.expected_findings
    ]

    semantic_score = grade(predictions, finding_ground_truth)

    matched_findings: List[str] = []
    for idx, finding in enumerate(task.expected_findings):
        gt_text = finding_ground_truth[idx]
        best = max([semantic_match(p, gt_text) for p in predictions], default=0.0)
        if best >= 0.5:
            matched_findings.append(finding.finding_id)

    coverage = len(matched_findings) / len(task.expected_findings)

    useful_predictions = 0
    for pred in predictions:
        if max([semantic_match(pred, gt) for gt in finding_ground_truth], default=0.0) >= 0.4:
            useful_predictions += 1
    precision = useful_predictions / len(predictions)

    line_hits = 0
    checked = 0
    for finding in task.expected_findings:
        relevant_actions = [
            action
            for action in actions
            if semantic_match(
                f"{action.comment} {action.suggested_fix or ''}".strip(),
                f"{finding.description} {' '.join(finding.keywords)}".strip(),
            )
            >= 0.5
        ]
        if not relevant_actions:
            continue
        checked += 1
        if any(abs(a.line_number - finding.expected_line) <= 1 for a in relevant_actions):
            line_hits += 1

    line_accuracy = (line_hits / checked) if checked else 0.0
    fix_quality = sum(1 for a in actions if a.suggested_fix and a.suggested_fix.strip()) / len(actions)

    epsilon = 0.01

    raw_score = (
        0.5 * semantic_score +
        0.2 * coverage +
        0.15 * precision +
        0.1 * line_accuracy +
        0.05 * fix_quality
    )

    score = min(max(raw_score, epsilon), 1.0 - epsilon)

    return GraderResult(
        score=score,
        coverage=coverage,
        precision=precision,
        line_accuracy=line_accuracy,
        fix_quality=fix_quality,
        matched_findings=sorted(matched_findings),
    )