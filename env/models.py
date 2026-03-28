from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class Action(BaseModel):
    comment: str = Field(min_length=5, max_length=500)
    line_number: int = Field(ge=1)
    suggested_fix: Optional[str] = Field(default=None, max_length=800)
    label: Literal["style", "performance", "bug", "security", "maintainability"] = "maintainability"
    confidence: float = Field(default=0.7, ge=0.0, le=1.0)


class Observation(BaseModel):
    task_id: str
    task_type: Literal["easy", "medium", "hard"]
    title: str
    objective: str
    code: str
    step_count: int
    max_steps: int
    discovered_findings: List[str]
    remaining_findings: int
    progress: List[str] = Field(default_factory=list)
    steps_taken: int = 0


class Reward(BaseModel):
    value: float = Field(ge=-1.0, le=1.0)
    components: Dict[str, float]


class FindingSpec(BaseModel):
    finding_id: str
    description: str
    expected_line: int = Field(ge=1)
    keywords: List[str]


class TaskSpec(BaseModel):
    task_id: str
    task_type: Literal["easy", "medium", "hard"]
    title: str
    objective: str
    code: str
    max_steps: int = Field(ge=1)
    expected_findings: List[FindingSpec]


class EpisodeState(BaseModel):
    active_task: Optional[TaskSpec] = None
    step_count: int = 0
    done: bool = False
    actions: List[Action] = Field(default_factory=list)
    matched_finding_ids: List[str] = Field(default_factory=list)
    last_grade: float = 0.0
    progress: List[str] = Field(default_factory=list)
    steps_taken: int = 0


class GraderResult(BaseModel):
    score: float = Field(ge=0.0, le=1.0)
    coverage: float = Field(ge=0.0, le=1.0)
    precision: float = Field(ge=0.0, le=1.0)
    line_accuracy: float = Field(ge=0.0, le=1.0)
    fix_quality: float = Field(ge=0.0, le=1.0)
    matched_findings: List[str]


class StepResult(BaseModel):
    observation: Observation
    reward: float
    done: bool
    info: Dict[str, Any]