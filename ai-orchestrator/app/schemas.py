from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import List, Literal, Optional

from pydantic import BaseModel, Field


StageName = Literal["architect", "worker", "tester", "reviewer"]


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
    task_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
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
