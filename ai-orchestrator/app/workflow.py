from __future__ import annotations

import json
import os
from typing import Dict, List

from pydantic import ValidationError

from .agents import (
    AGENT_SYSTEM_PROMPTS,
    STAGE_MODELS,
    build_user_message,
    make_assistant_agent,
)
from .schemas import Artifact, StageName, StageOutput, WorkflowRequest, WorkflowResult

# Pipeline order: plan → implement → validate → gate
STAGES: List[StageName] = ["architect", "worker", "tester", "reviewer"]


def _fallback_response(stage: StageName) -> str:
    """Deterministic scaffold output used when ANTHROPIC_API_KEY is missing."""
    return json.dumps(
        {
            "assumptions": [
                f"Fallback mode active for stage '{stage}': ANTHROPIC_API_KEY missing or autogen-ext[anthropic] not installed.",
                "Set ANTHROPIC_API_KEY in ai-orchestrator/.env to enable live Claude agents.",
            ],
            "decisions": [
                "Pipeline schema and contract can be validated in fallback mode.",
                "Reviewer will block all PRs in fallback mode until live agents are enabled.",
            ],
            "artifacts": [
                {
                    "name": "scaffold-note",
                    "content": f"BLOCKED — stage '{stage}' ran in fallback mode. No Claude API key configured.",
                }
            ],
            "open_questions": [
                "Is ANTHROPIC_API_KEY set in ai-orchestrator/.env?",
                "Are autogen-ext[anthropic] packages installed?",
            ],
            "confidence_score": 0.1,
        }
    )


async def _run_stage_with_agent(
    stage: StageName,
    user_message: str,
    api_key: str,
) -> str:
    """
    Create a dedicated AssistantAgent for the stage backed by a Claude model,
    send it the user message, and return the raw text of its reply.

    Model assignments:
      architect → claude-opus   (reads everything, plans without code)
      worker    → claude-sonnet (implements the plan, writes tests)
      tester    → claude-haiku  (fast validation of coverage rules)
      reviewer  → claude-opus   (final gate, blocks or approves)
    """
    from autogen_agentchat.messages import TextMessage
    from autogen_core import CancellationToken
    from autogen_ext.models.anthropic import AnthropicChatCompletionClient

    model_name = STAGE_MODELS[stage]
    model_client = AnthropicChatCompletionClient(model=model_name, api_key=api_key)
    agent = make_assistant_agent(stage, model_client)

    response = await agent.on_messages(
        [TextMessage(content=user_message, source="user")],
        cancellation_token=CancellationToken(),
    )

    reply = response.chat_message.content
    return reply if isinstance(reply, str) else json.dumps(reply)


async def run_workflow(request: WorkflowRequest) -> WorkflowResult:
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    use_agents = bool(api_key)

    if use_agents:
        try:
            import autogen_ext.models.anthropic  # noqa: F401
        except ImportError:
            use_agents = False

    outputs: List[StageOutput] = []

    for stage in STAGES:
        prior_json = json.dumps([item.model_dump() for item in outputs], ensure_ascii=True)
        user_message = build_user_message(
            stage=stage,
            task_id=request.task_id,
            user_prompt=request.prompt,
            product_context=request.product_context,
            prior_json=prior_json,
        )

        if use_agents:
            try:
                raw = await _run_stage_with_agent(stage, user_message, api_key)
            except Exception as exc:
                # Surface the real error as an artifact rather than silently falling back.
                raw = json.dumps({
                    "assumptions": [f"Agent call failed: {exc}"],
                    "decisions": [],
                    "artifacts": [{"name": "error", "content": str(exc)}],
                    "open_questions": ["Check ANTHROPIC_API_KEY, model name, and network access."],
                    "confidence_score": 0.0,
                })
        else:
            raw = _fallback_response(stage)

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
