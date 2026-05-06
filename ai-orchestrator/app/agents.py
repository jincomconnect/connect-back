from __future__ import annotations

import os
from textwrap import dedent

from .schemas import StageName


class AgentSpec:
    def __init__(self, stage: StageName, role: str, objective: str):
        self.stage = stage
        self.role = role
        self.objective = objective


AGENT_SPECS = {
    "research": AgentSpec(
        stage="research",
        role="Research agent",
        objective="Find constraints, user needs, and references that impact implementation.",
    ),
    "architect": AgentSpec(
        stage="architect",
        role="Architecture agent",
        objective="Define system boundaries, APIs, data flow, and delivery plan.",
    ),
    "design": AgentSpec(
        stage="design",
        role="Design agent",
        objective="Produce UX and UI specification with acceptance criteria.",
    ),
    "implement": AgentSpec(
        stage="implement",
        role="Implementation agent",
        objective="Translate specifications into implementation plan and concrete code-change proposal.",
    ),
    "test": AgentSpec(
        stage="test",
        role="Testing agent",
        objective="Design and run a test strategy to validate behavior and reduce regressions.",
    ),
}


def agent_prompt(stage: StageName, task_id: str, user_prompt: str, product_context: str, prior_json: str) -> str:
    spec = AGENT_SPECS[stage]

    schema_hint = dedent(
        """
        Return strict JSON with this shape:
        {
          "assumptions": ["..."],
          "decisions": ["..."],
          "artifacts": [{"name": "...", "content": "..."}],
          "open_questions": ["..."],
          "confidence_score": 0.0
        }

        Rules:
        - Keep confidence_score between 0 and 1.
        - Include at least one artifact.
        - No markdown fences.
        - JSON only.
        """
    ).strip()

    return dedent(
        f"""
        You are the {spec.role}.
        Objective: {spec.objective}
        Stage: {stage}
        Task ID: {task_id}

        Product context:
        {product_context or '(none)'}

        User request:
        {user_prompt}

        Prior stage outputs (JSON):
        {prior_json}

        {schema_hint}
        """
    ).strip()


def default_model() -> str:
    return os.getenv("OPENAI_MODEL", "gpt-4o-mini")
