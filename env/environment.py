from typing import Dict, List, Set

from env.grader import grade_episode
from env.models import Action, EpisodeState, Observation, Reward
from env.tasks import TASKS

class CodeReviewEnv:
    def __init__(self):
        self.state_data = EpisodeState()
        self._seen_action_signatures: Set[str] = set()
        self.history: Set[str] = set()
        self.progress: List[str] = []

    def reset(self, task_type="easy"):
        if task_type not in TASKS:
            task_type = "easy"

        self.state_data = EpisodeState(active_task=TASKS[task_type])
        self._seen_action_signatures = set()
        self.history = set()
        self.progress = []
        self.state_data.progress = []
        self.state_data.steps_taken = 0
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
            progress=self.progress,
            steps_taken=len(self.progress),
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

        self.progress.append(action.comment)
        self.state_data.progress = list(self.progress)
        self.state_data.steps_taken = len(self.progress)

        reward = 0.0
        reward_components: Dict[str, float] = {
            "repetition_penalty": 0.0,
            "ground_truth_match": 0.0,
            "suggested_fix_bonus": 0.0,
            "useless_penalty": 0.0,
        }

        # Penalize repeated actions.
        normalized_comment = action.comment.strip().lower()
        if normalized_comment in self.history:
            reward -= 0.2
            reward_components["repetition_penalty"] = -0.2
        else:
            self.history.add(normalized_comment)

        # Reward matching against task ground truth descriptions.
        ground_truth = [finding.description for finding in task.expected_findings]
        for gt in ground_truth:
            if gt.lower() in action.comment.lower():
                reward += 0.4
                reward_components["ground_truth_match"] += 0.4

        # Bonus for any concrete suggested fix text.
        if action.suggested_fix:
            reward += 0.2
            reward_components["suggested_fix_bonus"] = 0.2

        # Penalize low-value actions that gain no score.
        if reward == 0:
            reward -= 0.1
            reward_components["useless_penalty"] = -0.1

        episode_grade = grade_episode(self.state_data.actions, task)
        self.state_data.matched_finding_ids = sorted(list(episode_grade.matched_findings))
        self.state_data.last_grade = episode_grade.score

        reward_obj = Reward(value=max(min(reward, 1.0), -1.0), components=reward_components)

        if episode_grade.score >= 0.85 or self.state_data.step_count >= task.max_steps:
            self.state_data.done = True

        return self.state(), reward_obj.value, self.state_data.done, {
            "score": episode_grade.score,
            "coverage": episode_grade.coverage,
            "precision": episode_grade.precision,
            "line_accuracy": episode_grade.line_accuracy,
            "fix_quality": episode_grade.fix_quality,
            "matched_findings": episode_grade.matched_findings,
            "reward_components": reward_obj.components,
        }

    def state(self):
        observation = self._build_observation().model_dump()
        return {
            **observation,
            "progress": list(self.progress),
            "steps_taken": len(self.progress),
        }

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