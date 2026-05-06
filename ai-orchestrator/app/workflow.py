from __future__ import annotations

import json
import os
from typing import Dict, List

from pydantic import ValidationError

from .agents import agent_prompt, default_model
from .schemas import Artifact, StageName, StageOutput, WorkflowRequest, WorkflowResult

STAGES: List[StageName] = ["research", "architect", "design", "implement", "test"]


class LLMRunner:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY", "")
        self.model_name = default_model()

    async def run(self, prompt: str) -> str:
        # AutoGen client is loaded lazily so local development can run without AI credentials.
        if not self.api_key:
            return self._fallback_response(prompt)

        try:
            from autogen_ext.models.openai import OpenAIChatCompletionClient
        except ImportError:
            return self._fallback_response(prompt)

        client = OpenAIChatCompletionClient(model=self.model_name, api_key=self.api_key)
        result = await client.create(messages=[{"role": "user", "content": prompt}])
        content = result.content

        if isinstance(content, str):
            return content
        if isinstance(content, list):
            chunks = [item.get("text", "") for item in content if isinstance(item, dict)]
            return "\n".join(chunks).strip() or self._fallback_response(prompt)

        return self._fallback_response(prompt)

    def _fallback_response(self, prompt: str) -> str:
        # Deterministic scaffold output for bootstrapping the system before model credentials are ready.
        return json.dumps(
            {
                "assumptions": [
                    "This is scaffold mode because OPENAI_API_KEY is missing or AutoGen client is unavailable.",
                    "Team can iterate prompts and schemas before enabling live model calls.",
                ],
                "decisions": [
                    "Proceed with artifact-driven multi-agent pipeline.",
                    "Keep approval gate between design and implementation.",
                ],
                "artifacts": [
                    {
                        "name": "scaffold-note",
                        "content": "Generated deterministic stage output in fallback mode.",
                    }
                ],
                "open_questions": [
                    "Which model and cost budget should be enforced in production?",
                    "Should implement stage be allowed write tools or patch proposals only?",
                ],
                "confidence_score": 0.42,
            }
        )


async def run_workflow(request: WorkflowRequest) -> WorkflowResult:
    runner = LLMRunner()
    outputs: List[StageOutput] = []

    for stage in STAGES:
        prior_json = json.dumps([item.model_dump() for item in outputs], ensure_ascii=True)
        prompt = agent_prompt(
            stage=stage,
            task_id=request.task_id,
            user_prompt=request.prompt,
            product_context=request.product_context,
            prior_json=prior_json,
        )

        raw = await runner.run(prompt)
        stage_output = _parse_stage_output(stage, raw)
        outputs.append(stage_output)

    summary = _summarize(outputs)
    return WorkflowResult(
        task_id=request.task_id,
        created_at=WorkflowResult.now_iso(),
        stages=outputs,
        summary=summary,
    )


def _parse_stage_output(stage: StageName, raw: str) -> StageOutput:
    try:
        parsed: Dict = json.loads(raw)
    except json.JSONDecodeError:
        parsed = {
            "assumptions": ["Model did not return valid JSON; used parser fallback."],
            "decisions": ["Preserve original text as artifact for inspection."],
            "artifacts": [{"name": "raw-output", "content": raw[:3000] or "(empty)"}],
            "open_questions": ["Why did the model return non-JSON output?"],
            "confidence_score": 0.2,
        }

    parsed.setdefault("assumptions", [])
    parsed.setdefault("decisions", [])
    parsed.setdefault("artifacts", [{"name": "empty-artifact", "content": "No artifact returned."}])
    parsed.setdefault("open_questions", [])
    parsed.setdefault("confidence_score", 0.3)

    try:
        return StageOutput(stage=stage, **parsed)
    except ValidationError:
        return StageOutput(
            stage=stage,
            assumptions=["Stage schema validation failed; using safe fallback."],
            decisions=["Normalize malformed stage output."],
            artifacts=[Artifact(name="malformed-output", content=raw[:3000] or "(empty)")],
            open_questions=["Inspect prompt and enforce stricter JSON schema."],
            confidence_score=0.1,
        )


def _summarize(outputs: List[StageOutput]) -> str:
    confidence = sum(item.confidence_score for item in outputs) / max(1, len(outputs))
    decisions = sum(len(item.decisions) for item in outputs)
    questions = sum(len(item.open_questions) for item in outputs)
    return (
        f"Workflow complete across {len(outputs)} stages. "
        f"Average confidence: {confidence:.2f}. "
        f"Decisions captured: {decisions}. Open questions: {questions}."
    )
