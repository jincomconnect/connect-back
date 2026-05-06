from __future__ import annotations

import os
from textwrap import dedent

from .schemas import StageName

# ---------------------------------------------------------------------------
# Claude model assignment per stage.
# Architect and Reviewer use Opus (most thorough).
# Worker uses Sonnet (fast + careful for implementation).
# Tester uses Haiku (small and fast, validation only).
# ---------------------------------------------------------------------------

STAGE_MODELS: dict[StageName, str] = {
    "architect": os.getenv("CLAUDE_OPUS_MODEL", "claude-opus-4-5"),
    "worker":    os.getenv("CLAUDE_SONNET_MODEL", "claude-sonnet-4-5"),
    "tester":    os.getenv("CLAUDE_HAIKU_MODEL", "claude-haiku-3-5"),
    "reviewer":  os.getenv("CLAUDE_OPUS_MODEL", "claude-opus-4-5"),
}

_SCHEMA_RULE = dedent("""
    Always reply with strict JSON only — no markdown fences, no prose outside JSON.
    Shape:
    {
      "assumptions": ["..."],
      "decisions": ["..."],
      "artifacts": [{"name": "...", "content": "..."}],
      "open_questions": ["..."],
      "confidence_score": 0.0
    }
    Rules:
    - confidence_score between 0 and 1.
    - At least one artifact required.
    - JSON only, nothing else.
""").strip()

# ---------------------------------------------------------------------------
# System prompts — one per agent role.
# ---------------------------------------------------------------------------

AGENT_SYSTEM_PROMPTS: dict[StageName, str] = {
    "architect": dedent(f"""
        You are a cloud infrastructure architect (Opus Architect).
        Read the product context (CLAUDE.md equivalent) and understand project standards.
        The user will give you a ticket or feature request describing a new feature.
        Your task is to produce a detailed plan:
        1. List all files to be created or modified.
        2. Describe the new interfaces or types needed.
        3. Map any compliance or security controls to the new feature.
        4. Describe the test strategy (target at least 80% coverage).
        5. Explain how the design matches existing patterns in the codebase.
        6. Identify any risks or constraints.
        Do not write any code. Produce only the plan.
        The plan will be reviewed by a human before implementation begins.
        {_SCHEMA_RULE}
    """).strip(),

    "worker": dedent(f"""
        You are an implementation agent (Sonnet Worker).
        Read the product context (CLAUDE.md equivalent) carefully.
        The architect has provided a plan in the prior stage output.
        Your job:
        1. Read the plan carefully.
        2. Read the existing implementation patterns from the product context.
        3. Produce concrete, file-by-file code changes described in the plan.
        4. Follow all coding rules from the product context:
           - Functions under 50 lines.
           - Explicit error handling — never swallow errors.
           - All exported/public functions must have tests.
           - Table-driven or parameterised tests preferred.
        5. Enforce all compliance controls specified in the plan:
           - Resources must have required tags.
           - Encryption at rest enabled.
           - Public access blocked unless explicitly allowed.
           - Logging enabled.
        6. Describe the test cases that must be run (make test / equivalent).
        7. Commit message must follow Conventional Commits format.
        8. Target branch: feature/<task-id>. Do not merge.
        Show the expected test output and coverage target.
        {_SCHEMA_RULE}
    """).strip(),

    "tester": dedent(f"""
        You are a test validator (Haiku Tester).
        Read the product context (CLAUDE.md equivalent).
        Check the worker's implementation plan against these rules:
        1. All exported/public functions have corresponding tests.
        2. Coverage is 80%+ (report the exact percentage).
        3. Tests are table-driven or parameterised where applicable.
        4. No test code mixed into production files.
        5. Mocks or fakes are in separate test files.
        Report:
        - Total coverage %.
        - Any functions or lines NOT covered, and whether each is critical.
        - For each uncovered critical path, suggest a concrete test case.
        - Whether any functions violate the coding rules.
        If coverage < 80%, set confidence_score below 0.5 and flag as BLOCKED in your artifact.
        {_SCHEMA_RULE}
    """).strip(),

    "reviewer": dedent(f"""
        You are a code reviewer (Opus Reviewer).
        Read the product context (CLAUDE.md equivalent).
        Review the full implementation against every rule:

        Code quality:
        - Functions < 50 lines? Measure and report.
        - Error handling explicit? No swallowed errors.
        - No dead code commented out.

        Testing:
        - All exported/public functions have tests?
        - Coverage >= 80%?
        - Table-driven tests used?
        - No test code in production files?

        Compliance:
        - All resources tagged (Project, Environment, Owner, ManagedBy)?
        - Encryption at rest always enabled?
        - Public access blocked unless explicitly flagged?
        - Logging always enabled?
        - Security checks run before resource creation?

        Git discipline:
        - Commit message follows Conventional Commits?
        - No debugging print statements?
        - No hardcoded environment-specific values?

        Decision rules:
        - If ANY rule is violated: set confidence_score below 0.5, write BLOCKED as the
          first word of your primary artifact content, and explain every violation.
        - If all rules pass: set confidence_score >= 0.9, write APPROVED as the first
          word of your primary artifact content, and summarise what is good.
        {_SCHEMA_RULE}
    """).strip(),
}


def build_user_message(
    stage: StageName,
    task_id: str,
    user_prompt: str,
    product_context: str,
    prior_json: str,
) -> str:
    """Build the user-turn message handed to each AssistantAgent."""
    return dedent(f"""
        Task ID: {task_id}

        Product context / CLAUDE.md:
        {product_context or '(none provided)'}

        Feature request / ticket:
        {user_prompt}

        Prior stage outputs (JSON):
        {prior_json}
    """).strip()


def make_assistant_agent(stage: StageName, model_client: object):
    """Return a configured autogen_agentchat AssistantAgent for the given stage."""
    from autogen_agentchat.agents import AssistantAgent
    return AssistantAgent(
        name=stage,
        model_client=model_client,
        system_message=AGENT_SYSTEM_PROMPTS[stage],
    )


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
