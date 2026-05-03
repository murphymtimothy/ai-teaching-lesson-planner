"""Six-stage pipeline orchestrator.

Stage 1: retrieve  (keyword overlap, deterministic)
Stage 2: scaffold  (Sonnet 4.6, forced tool-use structured output)
Stage 3: eld       (Sonnet 4.6)
Stage 4: lcap      (Sonnet 4.6)
Stage 5: activities(Sonnet 4.6)
Stage 6: verify    (deterministic; raises on hallucinated codes)
"""

from __future__ import annotations

import re
from typing import Callable, Optional

import anthropic

from poppy import prompts
from poppy.llm import CostMeter, call_structured


ProgressCallback = Callable[[str, str], None]
"""Optional callback for UI progress updates. Called as `cb(stage_name, status)`
where status is one of: 'started', 'done'."""
from poppy.schemas import (
    Activities,
    ELDMoves,
    FullPlan,
    LCAPTags,
    PlanInput,
    ScaffoldOutput,
)
from poppy.standards import STANDARDS, STANDARDS_BY_CODE, Standard, all_codes, standards_corpus_text


class HallucinationError(RuntimeError):
    """Raised by Stage 6 when a cited standard code is not in the corpus."""


def retrieve(plan_input: PlanInput, top_k: int = 6) -> list[Standard]:
    """Stage 1: rank corpus standards by keyword overlap with the topic.

    Scoring: 2 points per topic_tag substring hit, +3 for subject match,
    +1 for any topic word appearing in the standard text.
    """
    topic_lower = plan_input.topic.lower()
    topic_words = set(re.findall(r"[a-z]{4,}", topic_lower))

    scored: list[tuple[int, Standard]] = []
    for standard in STANDARDS:
        score = 0
        for tag in standard.topic_tags:
            if tag.lower() in topic_lower:
                score += 2
        if standard.subject == plan_input.subject or (
            plan_input.subject == "ELA" and standard.subject == "ELD"
        ):
            score += 3
        text_words = set(re.findall(r"[a-z]{4,}", standard.text.lower()))
        score += len(topic_words & text_words)
        if score > 0:
            scored.append((score, standard))

    scored.sort(key=lambda x: x[0], reverse=True)
    if not scored:
        # Fallback: subject match only
        return [s for s in STANDARDS if s.subject == plan_input.subject][:top_k]
    return [s for _, s in scored[:top_k]]


def verify(scaffold: ScaffoldOutput, eld: ELDMoves) -> bool:
    """Stage 6: hard gate. Reject any cited code not in the standards corpus.

    This is the most important code in the project — a hallucinated code
    in a teacher's lesson plan kills trust.
    """
    valid = all_codes()
    cited = set(scaffold.standards_cited) | set(eld.eld_standards_cited)
    invalid = cited - valid
    if invalid:
        raise HallucinationError(
            f"Stage 6 rejected the plan. The following standard codes are not in the "
            f"corpus: {sorted(invalid)}. Valid codes are: {sorted(valid)}"
        )
    return True


def run_pipeline(
    plan_input: PlanInput,
    client: anthropic.Anthropic | None = None,
    on_progress: Optional[ProgressCallback] = None,
) -> FullPlan:
    """Execute all six stages and return a validated FullPlan.

    `on_progress` is an optional callback invoked at each stage boundary so a
    UI (Streamlit, etc.) can show a live status. Phase 0 CLI ignores it.
    """
    if client is None:
        client = anthropic.Anthropic()

    def progress(stage: str, status: str) -> None:
        if on_progress is not None:
            on_progress(stage, status)

    cost = CostMeter()
    corpus = standards_corpus_text()

    # Stage 1: retrieve
    progress("retrieve", "started")
    candidates = retrieve(plan_input)
    progress("retrieve", "done")

    # Stage 2: scaffold
    progress("scaffold", "started")
    scaffold_system, scaffold_user = prompts.scaffold_prompt(plan_input, candidates, corpus)
    scaffold = call_structured(
        client,
        stage="scaffold",
        system=scaffold_system,
        user=scaffold_user,
        schema=ScaffoldOutput,
        tool_name="emit_scaffold",
        tool_description="Emit the lesson plan scaffold (objective, big idea, success criteria, standards, structure).",
        cost=cost,
    )
    progress("scaffold", "done")

    # Stage 3: ELD
    progress("eld", "started")
    eld_system, eld_user = prompts.eld_prompt(plan_input, scaffold, corpus)
    eld = call_structured(
        client,
        stage="eld",
        system=eld_system,
        user=eld_user,
        schema=ELDMoves,
        tool_name="emit_eld_overlay",
        tool_description="Emit ELD Part I/II/III moves, SDAIE strategies, and sentence frames.",
        cost=cost,
    )
    progress("eld", "done")

    # Stage 4: LCAP
    progress("lcap", "started")
    lcap_system, lcap_user = prompts.lcap_prompt(plan_input, scaffold)
    lcap = call_structured(
        client,
        stage="lcap",
        system=lcap_system,
        user=lcap_user,
        schema=LCAPTags,
        tool_name="emit_lcap_tags",
        tool_description="Emit LCAP State Priorities and LCFF student groups served by this lesson.",
        cost=cost,
    )
    progress("lcap", "done")

    # Stage 5: Activities
    progress("activities", "started")
    act_system, act_user = prompts.activities_prompt(plan_input, scaffold, eld)
    activities = call_structured(
        client,
        stage="activities",
        system=act_system,
        user=act_user,
        schema=Activities,
        tool_name="emit_activities",
        tool_description="Emit the warm-up, I-do, We-do, You-do, assessment, and differentiation activities.",
        cost=cost,
    )
    progress("activities", "done")

    # Stage 6: verify (raises on bad codes)
    progress("verify", "started")
    verified = verify(scaffold, eld)
    progress("verify", "done")

    return FullPlan(
        input=plan_input,
        candidate_standards=[s.code for s in candidates],
        scaffold=scaffold,
        eld=eld,
        lcap=lcap,
        activities=activities,
        verified=verified,
        cost_usd=cost.cost_usd,
    )
