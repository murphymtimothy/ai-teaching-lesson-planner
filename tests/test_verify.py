"""Stage 6 verification tests.

This is the most important test file in the project. Stage 6 is the deterministic
hard gate that catches hallucinated standard codes before they reach a teacher's
lesson plan. A bug here corrupts every plan we generate.
"""

from __future__ import annotations

import re

import pytest

from poppy.pipeline import HallucinationError, retrieve, verify
from poppy.schemas import ELDMoves, PlanInput, ScaffoldOutput
from poppy.standards import STANDARDS, all_codes


def _scaffold(codes: list[str]) -> ScaffoldOutput:
    return ScaffoldOutput(
        objective="SWBAT do something measurable.",
        big_idea="Students learn things.",
        success_criteria=["I can do X.", "I can do Y."],
        standards_cited=codes,
        structure_overview="Warm-up, then practice, then assess.",
    )


def _eld(codes: list[str]) -> ELDMoves:
    return ELDMoves(
        part_i_moves=["move 1"],
        part_ii_moves=["move 2"],
        part_iii_moves=[],
        sdaie_strategies=["strategy 1"],
        sentence_frames=["___ because ___"],
        eld_standards_cited=codes,
    )


def test_verify_accepts_valid_codes():
    scaffold = _scaffold(["CCSS.ELA-LITERACY.RL.5.3", "CCSS.ELA-LITERACY.W.5.1"])
    eld = _eld(["ELD.PI.5.1"])
    assert verify(scaffold, eld) is True


def test_verify_rejects_unknown_code():
    scaffold = _scaffold(["CCSS.ELA-LITERACY.RL.5.3", "CCSS.ELA-LITERACY.RL.99.1"])
    eld = _eld(["ELD.PI.5.1"])
    with pytest.raises(HallucinationError) as exc:
        verify(scaffold, eld)
    assert "RL.99.1" in str(exc.value)


def test_verify_rejects_unknown_eld_code():
    scaffold = _scaffold(["CCSS.ELA-LITERACY.RL.5.3"])
    eld = _eld(["ELD.PI.5.1", "ELD.PIV.5.99"])
    with pytest.raises(HallucinationError) as exc:
        verify(scaffold, eld)
    assert "PIV.5.99" in str(exc.value)


def test_verify_rejects_typo_in_code():
    """Common failure mode: model produces a real-sounding-but-typo'd code."""
    scaffold = _scaffold(["CCSS.ELA-LITERACY.RL.5.1.A"])  # extra .A suffix
    eld = _eld(["ELD.PI.5.1"])
    with pytest.raises(HallucinationError):
        verify(scaffold, eld)


def test_verify_empty_lists_pass():
    """Empty cited lists should not raise — the pipeline shouldn't produce them,
    but Stage 6's job is to catch hallucinations, not enforce non-emptiness."""
    scaffold = _scaffold([])
    eld = _eld([])
    assert verify(scaffold, eld) is True


def test_all_corpus_codes_match_format():
    """Code-format conformance: every standard code in the corpus matches its
    framework's expected pattern. A typo here makes Stage 6 reject correct cites.
    """
    patterns = {
        "CCSS-ELA": re.compile(r"^CCSS\.ELA-LITERACY\.[A-Z]{1,3}\.\d+\.\d+$"),
        "CCSS-Math": re.compile(r"^CCSS\.MATH\.CONTENT\.\d+\.[A-Z]+\.[A-Z]\.\d+$"),
        "ELD": re.compile(r"^ELD\.P(I|II|III)\.\d+\.\d+$"),
    }
    for s in STANDARDS:
        pattern = patterns[s.framework]
        assert pattern.match(s.code), f"{s.code} does not match {s.framework} pattern"


def test_corpus_no_duplicate_codes():
    codes = [s.code for s in STANDARDS]
    assert len(codes) == len(set(codes)), "Duplicate codes in standards corpus"


def test_retrieve_finds_relevant_standards():
    plan_input = PlanInput(
        grade=5,
        subject="ELA",
        topic="character motivation and theme",
        duration_minutes=45,
        class_context="test",
    )
    candidates = retrieve(plan_input)
    cited_codes = {s.code for s in candidates}
    assert "CCSS.ELA-LITERACY.RL.5.3" in cited_codes


def test_retrieve_falls_back_when_no_overlap():
    """Even with a topic that matches no tags, retrieve returns subject-matching standards."""
    plan_input = PlanInput(
        grade=5,
        subject="Math",
        topic="zzzzzzzzzz xxxxxxxxx",  # nonsense
        duration_minutes=45,
        class_context="test",
    )
    candidates = retrieve(plan_input)
    assert len(candidates) > 0
    assert all(s.subject == "Math" for s in candidates)
