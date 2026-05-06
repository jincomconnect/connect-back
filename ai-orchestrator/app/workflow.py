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


def _sandbox_stage_response(
    stage: StageName,
    prompt: str,
    product_context: str,
    prior_stages: List[StageOutput],
) -> StageOutput:
    """
    Return a structured description of what the given stage *would* do,
    without calling any Claude model. Confidence is always 0.0 to signal
    that no real analysis was performed.
    """
    _prior = ", ".join(s.stage for s in prior_stages) if prior_stages else "none"
    _ctx_note = f"Product context provided ({len(product_context)} chars)." if product_context else "No product context supplied."

    _stage_plans: dict[StageName, dict] = {
        "architect": {
            "assumptions": [
                f"Would analyse the prompt: '{prompt[:120]}{'...' if len(prompt) > 120 else ''}'",
                _ctx_note,
                "Would identify key system components, boundaries, and dependencies.",
                "Would decide on high-level patterns (layering, data flow, API surface).",
            ],
            "decisions": [
                "Select appropriate architecture pattern (e.g. layered, hexagonal, event-driven).",
                "Define module responsibilities and inter-service contracts.",
                "Specify data models and storage strategy.",
                "Document cross-cutting concerns: auth, logging, error handling.",
            ],
            "artifacts": [
                {
                    "name": "architecture-plan",
                    "content": (
                        "[SANDBOX] Would produce an architecture plan including:\n"
                        "  - Component diagram and data-flow description\n"
                        "  - API contract definitions (routes, request/response shapes)\n"
                        "  - Data model schemas\n"
                        "  - Tech stack recommendations with rationale"
                    ),
                }
            ],
            "open_questions": [
                "What are the scalability requirements?",
                "Are there existing patterns in the codebase that must be followed?",
                "What external services or APIs will be integrated?",
            ],
        },
        "worker": {
            "assumptions": [
                f"Would consume architect output (prior stages: {_prior}).",
                "Would translate architecture decisions into concrete implementation.",
                f"Prompt intent: '{prompt[:120]}{'...' if len(prompt) > 120 else ''}'",
            ],
            "decisions": [
                "Write feature code following architecture plan file structure.",
                "Implement unit tests alongside each module.",
                "Follow project coding standards inferred from product context.",
                "Produce migration scripts or schema changes if data models changed.",
            ],
            "artifacts": [
                {
                    "name": "implementation-plan",
                    "content": (
                        "[SANDBOX] Would produce implementation artifacts:\n"
                        "  - Source files for each module identified by architect\n"
                        "  - Unit test files (co-located or in __tests__ / tests/)\n"
                        "  - Database migration scripts (if applicable)\n"
                        "  - Updated dependency list (requirements.txt / package.json)"
                    ),
                }
            ],
            "open_questions": [
                "Which existing files need modification vs new files?",
                "Are there shared utilities or helpers to reuse?",
                "What test framework and coverage threshold is expected?",
            ],
        },
        "tester": {
            "assumptions": [
                f"Would validate worker output (prior stages: {_prior}).",
                "Would check test coverage completeness and edge-case handling.",
                "Would verify API contracts match architect spec.",
            ],
            "decisions": [
                "Run static analysis to surface obvious defects.",
                "Check that every public function/route has at least one test.",
                "Flag missing error-path tests (400s, 500s, auth failures).",
                "Validate schema consistency between layers.",
            ],
            "artifacts": [
                {
                    "name": "test-validation-report",
                    "content": (
                        "[SANDBOX] Would produce a validation report:\n"
                        "  - Coverage analysis per module\n"
                        "  - List of untested edge cases\n"
                        "  - Schema drift findings\n"
                        "  - PASS / FAIL verdict per acceptance criterion"
                    ),
                }
            ],
            "open_questions": [
                "What is the minimum acceptable coverage percentage?",
                "Are integration or E2E tests in scope for this task?",
                "Should performance benchmarks be included?",
            ],
        },
        "reviewer": {
            "assumptions": [
                f"Would gate the entire pipeline (prior stages: {_prior}).",
                "Would weigh confidence scores from all prior stages.",
                "Would enforce project-level standards and PR conventions.",
            ],
            "decisions": [
                "Verify all open questions from prior stages are addressed or explicitly deferred.",
                "Check security posture: input validation, auth, secrets management.",
                "Assess whether implementation matches architect intent.",
                "Issue APPROVED or BLOCKED verdict with rationale.",
            ],
            "artifacts": [
                {
                    "name": "review-summary",
                    "content": (
                        "[SANDBOX] APPROVED (dry-run placeholder)\n"
                        "Would produce a review summary:\n"
                        "  - Stage-by-stage confidence assessment\n"
                        "  - Security checklist results\n"
                        "  - Required changes before merge (blockers)\n"
                        "  - Recommended improvements (non-blocking)"
                    ),
                }
            ],
            "open_questions": [
                "Are there any compliance or audit requirements?",
                "Has the feature been demoed or reviewed by a product stakeholder?",
            ],
        },
    }

    plan = _stage_plans[stage]
    return StageOutput(
        stage=stage,
        assumptions=plan["assumptions"],
        decisions=plan["decisions"],
        artifacts=[Artifact(**a) for a in plan["artifacts"]],
        open_questions=plan["open_questions"],
        confidence_score=0.0,
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
    # Sandbox runs without any API key — skip agent setup entirely.
    if request.sandbox:
        outputs: List[StageOutput] = []
        for stage in STAGES:
            outputs.append(_sandbox_stage_response(
                stage,
                prompt=request.prompt,
                product_context=request.product_context,
                prior_stages=outputs,
            ))
        summary = "[SANDBOX / DRY-RUN] " + _summarize(outputs) + " No Claude agents were invoked; this is a plan of what would happen."
        return WorkflowResult(
            task_id=request.task_id,
            created_at=WorkflowResult.now_iso(),
            stages=outputs,
            summary=summary,
            sandbox=True,
        )

    # Prefer the key supplied in the request body (entered by the user in the UI)
    # so the key never needs to live in .env or be committed to source control.
    api_key = (request.api_key or "").strip() or os.getenv("ANTHROPIC_API_KEY", "")
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
                stage_output = _parse_stage_output(stage, raw)
            else:
                stage_output = _parse_stage_output(stage, raw)
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
        sandbox=False,
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
