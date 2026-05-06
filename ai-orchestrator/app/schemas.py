from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Literal

from pydantic import BaseModel, Field


StageName = Literal["research", "architect", "design", "implement", "test"]


class Artifact(BaseModel):
    name: str = Field(min_length=1)
    content: str = Field(min_length=1)


class StageOutput(BaseModel):
    stage: StageName
    assumptions: List[str] = Field(default_factory=list)
    decisions: List[str] = Field(default_factory=list)
    artifacts: List[Artifact] = Field(default_factory=list)
    open_questions: List[str] = Field(default_factory=list)
    confidence_score: float = Field(ge=0.0, le=1.0)


class WorkflowRequest(BaseModel):
    task_id: str = Field(min_length=1)
    prompt: str = Field(min_length=10)
    product_context: str = Field(default="")


class WorkflowResult(BaseModel):
    task_id: str
    created_at: str
    stages: List[StageOutput]
    summary: str

    @staticmethod
    def now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()
