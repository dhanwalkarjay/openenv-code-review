from typing import Dict, List, Set

from env.grader import grade_episode
from env.models import Action, EpisodeState, Observation, Reward
from env.tasks import TASKS

class CodeReviewEnv:
    def __init__(self):
        self.state_data = EpisodeState()
        self._seen_action_signatures: Set[str] = set()

    def reset(self, task_type="easy"):
        if task_type not in TASKS:
            task_type = "easy"

        self.state_data = EpisodeState(active_task=TASKS[task_type])
        self._seen_action_signatures = set()
        return self.state()

    def _build_observation(self) -> Observation:
        assert self.state_data.active_task is not None
        task = self.state_data.active_task
        discovered = list(self.state_data.matched_finding_ids)
        return Observation(
            task_id=task.task_id,
            task_type=task.task_type,
            title=task.title,
            objective=task.objective,
            code=task.code,
            step_count=self.state_data.step_count,
            max_steps=task.max_steps,
            discovered_findings=discovered,
            remaining_findings=max(len(task.expected_findings) - len(discovered), 0),
        )

    def step(self, action: Action):
        if self.state_data.done:
            return self.state(), 0.0, True, {}

        if self.state_data.active_task is None:
            self.reset("easy")

        task = self.state_data.active_task
        assert task is not None

        self.state_data.step_count += 1
        self.state_data.actions.append(action)

        reward_components: Dict[str, float] = {
            "new_finding": 0.0,
            "suggested_fix": 0.0,
            "precision": 0.0,
            "duplicate_penalty": 0.0,
            "line_penalty": 0.0,
            "loop_penalty": 0.0,
        }

        signature = f"{action.line_number}|{action.comment.strip().lower()}"
        if signature in self._seen_action_signatures:
            reward_components["duplicate_penalty"] = -0.15
        else:
            self._seen_action_signatures.add(signature)

        line_count = len(task.code.splitlines())
        if action.line_number > line_count:
            reward_components["line_penalty"] = -0.1

        episode_grade = grade_episode(self.state_data.actions, task)
        previous_matches = set(self.state_data.matched_finding_ids)
        current_matches = set(episode_grade.matched_findings)
        new_matches = len(current_matches - previous_matches)

        if new_matches > 0:
            reward_components["new_finding"] = 0.35 * new_matches

        if action.suggested_fix and len(action.suggested_fix.strip()) >= 12 and new_matches > 0:
            reward_components["suggested_fix"] = 0.1

        if len(action.comment.strip()) >= 24:
            reward_components["precision"] = 0.05

        self.state_data.matched_finding_ids = sorted(list(current_matches))
        self.state_data.last_grade = episode_grade.score

        if self.state_data.step_count >= task.max_steps and episode_grade.score < 0.85:
            reward_components["loop_penalty"] = -0.2

        reward_value = sum(reward_components.values())
        reward = Reward(value=max(min(reward_value, 1.0), -1.0), components=reward_components)

        if episode_grade.score >= 0.85 or self.state_data.step_count >= task.max_steps:
            self.state_data.done = True

        return self.state(), reward.value, self.state_data.done, {
            "score": episode_grade.score,
            "coverage": episode_grade.coverage,
            "precision": episode_grade.precision,
            "line_accuracy": episode_grade.line_accuracy,
            "fix_quality": episode_grade.fix_quality,
            "matched_findings": episode_grade.matched_findings,
            "reward_components": reward.components,
        }

    def state(self):
        return self._build_observation().model_dump()

    def get_last_grader_result(self):
        if self.state_data.active_task is None:
            return {
                "score": 0.0,
                "coverage": 0.0,
                "precision": 0.0,
                "line_accuracy": 0.0,
                "fix_quality": 0.0,
                "matched_findings": [],
            }
        return grade_episode(self.state_data.actions, self.state_data.active_task).model_dump()

    def get_task_catalog(self) -> List[Dict]:
        action_schema = Action.model_json_schema()
        return [
            {
                "task_id": task.task_id,
                "task_type": task.task_type,
                "title": task.title,
                "objective": task.objective,
                "max_steps": task.max_steps,
                "action_schema": action_schema,
            }
            for task in TASKS.values()
        ]