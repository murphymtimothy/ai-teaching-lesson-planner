"""Pydantic schemas for pipeline I/O.

Each LLM stage emits a structured object validated against one of these models.
"""

from typing import Literal

from pydantic import BaseModel, Field


class PlanInput(BaseModel):
    grade: int = Field(description="Grade level (K=0, 1-12)")
    subject: Literal["ELA", "Math", "ELD"] = Field(description="Primary content area")
    topic: str = Field(description="What the lesson is about, in the teacher's own words")
    duration_minutes: int = Field(description="Lesson length in minutes")
    class_context: str = Field(
        description=(
            "Free-text class profile: enrollment, EL count and proficiency levels, "
            "IEP/504 students, GATE, behavioral notes. Used to drive differentiation."
        )
    )


class ScaffoldOutput(BaseModel):
    objective: str = Field(
        description=(
            "Student-facing learning objective in SWBAT form (Students Will Be Able To...). "
            "Must be specific, measurable, and tied to a verb from Bloom's higher levels."
        )
    )
    big_idea: str = Field(
        description="One-sentence enduring understanding the lesson advances."
    )
    success_criteria: list[str] = Field(
        description=(
            "3-5 observable, student-facing 'I can' statements that tell students what mastery "
            "looks like."
        )
    )
    standards_cited: list[str] = Field(
        description=(
            "Standard codes this lesson directly targets. Codes MUST be selected from the "
            "California-adopted standards corpus provided in the prompt — do not invent codes."
        )
    )
    structure_overview: str = Field(
        description=(
            "One paragraph (3-5 sentences) describing how the lesson flows from warm-up through "
            "closure, calibrated to the duration."
        )
    )


class ELDMoves(BaseModel):
    part_i_moves: list[str] = Field(
        description=(
            "ELD Part I (Interacting in Meaningful Ways) moves: collaborative, interpretive, or "
            "productive. Each entry is a concrete, classroom-ready move — not a generic strategy "
            "name. Include who does what."
        )
    )
    part_ii_moves: list[str] = Field(
        description=(
            "ELD Part II (Learning About How English Works) moves: structuring cohesive texts, "
            "expanding/enriching ideas, or connecting/condensing ideas. Concrete and lesson-specific."
        )
    )
    part_iii_moves: list[str] = Field(
        description=(
            "ELD Part III (Using Foundational Literacy Skills) moves, when applicable. Empty list "
            "if the lesson does not call for foundational-skills work at this grade."
        )
    )
    sdaie_strategies: list[str] = Field(
        description=(
            "Specially Designed Academic Instruction in English strategies tailored to the lesson "
            "(e.g., realia, graphic organizer X with this content, contextualized vocabulary preview)."
        )
    )
    sentence_frames: list[str] = Field(
        description=(
            "3-6 sentence frames calibrated to the lesson's discourse demands. Match the EL "
            "proficiency levels in the class context. Each frame should be usable verbatim."
        )
    )
    eld_standards_cited: list[str] = Field(
        description="ELD standard codes from the corpus that anchor these moves."
    )


class LCAPTags(BaseModel):
    priorities: list[int] = Field(
        description=(
            "LCAP State Priorities (1-8) this lesson advances. 1=Basic Services, "
            "2=Implementation of State Standards, 3=Parental Involvement, 4=Pupil Achievement, "
            "5=Pupil Engagement, 6=School Climate, 7=Course Access, 8=Other Pupil Outcomes. "
            "Be selective — typically 1-3 priorities apply, not all of them."
        )
    )
    student_groups: list[str] = Field(
        description=(
            "LCFF student groups this lesson particularly serves: 'English Learners', "
            "'Students with Disabilities', 'Foster Youth', 'Low-Income', 'Homeless Youth', "
            "'African American', 'Hispanic/Latino', 'GATE'. Pick groups actually impacted."
        )
    )
    rationale: str = Field(
        description=(
            "1-2 sentences explaining how the lesson advances each cited priority and group. "
            "This is what an admin would read on an observation form."
        )
    )


class Activities(BaseModel):
    materials: list[str] = Field(
        description="Concrete materials needed (texts, manipulatives, handouts, anchors)."
    )
    warm_up: str = Field(
        description=(
            "Opening activity (5-10 min) that activates prior knowledge or hooks attention. "
            "Include the prompt students see and what the teacher does."
        )
    )
    i_do: str = Field(
        description=(
            "Direct instruction segment. Concrete teacher script or modeling steps — what does "
            "the teacher say and demonstrate? Specific, not generic."
        )
    )
    we_do: str = Field(
        description=(
            "Guided practice. The teacher and class work through an example together. Include "
            "the specific problem or text and the questioning sequence."
        )
    )
    you_do: str = Field(
        description=(
            "Independent or small-group practice. Specific task, what students produce, how "
            "long it takes."
        )
    )
    assessment: str = Field(
        description=(
            "How the teacher checks for mastery against the success criteria. Could be exit "
            "ticket, performance task, observation protocol — be specific."
        )
    )
    differentiation_el: str = Field(
        description=(
            "Concrete supports for English Learners at the proficiency levels described in "
            "class context. Specific scaffolds, not 'provide visuals'."
        )
    )
    differentiation_iep: str = Field(
        description=(
            "Concrete supports for IEP/504 students given the goals/accommodations implied by "
            "class context. Specific. Empty if class context indicates no IEP students."
        )
    )
    differentiation_gate: str = Field(
        description=(
            "Concrete extensions for GATE/advanced students. Depth, complexity, novelty — not "
            "just 'more of the same'. Empty if class context indicates no GATE students."
        )
    )


class FullPlan(BaseModel):
    """Complete output of the pipeline. Sum of all stages."""

    input: PlanInput
    candidate_standards: list[str]
    scaffold: ScaffoldOutput
    eld: ELDMoves
    lcap: LCAPTags
    activities: Activities
    verified: bool
    cost_usd: float
