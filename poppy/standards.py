"""Hardcoded grade-5 standards corpus for Phase 0.

Source of truth for Stage 1 retrieval and Stage 6 verification.
Texts are the official California-adopted versions from CDE-published documents.
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Standard:
    framework: str  # "CCSS-ELA" | "CCSS-Math" | "ELD"
    code: str
    grade: int
    subject: str  # "ELA" | "Math" | "ELD"
    topic_tags: tuple[str, ...]
    text: str

    def to_prompt_line(self) -> str:
        return f"  {self.code} ({self.subject}): {self.text}"


STANDARDS: tuple[Standard, ...] = (
    # ELA — Reading Literature
    Standard(
        framework="CCSS-ELA",
        code="CCSS.ELA-LITERACY.RL.5.1",
        grade=5,
        subject="ELA",
        topic_tags=("textual evidence", "inference", "close reading", "quote", "comprehension"),
        text=(
            "Quote accurately from a text when explaining what the text says explicitly "
            "and when drawing inferences from the text."
        ),
    ),
    Standard(
        framework="CCSS-ELA",
        code="CCSS.ELA-LITERACY.RL.5.3",
        grade=5,
        subject="ELA",
        topic_tags=(
            "character", "setting", "compare and contrast", "theme", "motivation",
            "narrative", "story elements",
        ),
        text=(
            "Compare and contrast two or more characters, settings, or events in a story or drama, "
            "drawing on specific details in the text (e.g., how characters interact)."
        ),
    ),
    # ELA — Writing
    Standard(
        framework="CCSS-ELA",
        code="CCSS.ELA-LITERACY.W.5.1",
        grade=5,
        subject="ELA",
        topic_tags=("opinion writing", "argument", "persuasion", "reasons", "point of view"),
        text=(
            "Write opinion pieces on topics or texts, supporting a point of view with reasons "
            "and information."
        ),
    ),
    # ELA — Speaking & Listening
    Standard(
        framework="CCSS-ELA",
        code="CCSS.ELA-LITERACY.SL.5.1",
        grade=5,
        subject="ELA",
        topic_tags=(
            "discussion", "collaboration", "speaking", "listening", "academic conversation",
            "group work",
        ),
        text=(
            "Engage effectively in a range of collaborative discussions (one-on-one, in groups, "
            "and teacher-led) with diverse partners on grade 5 topics and texts, building on "
            "others' ideas and expressing their own clearly."
        ),
    ),
    # Math — Number & Operations: Fractions
    Standard(
        framework="CCSS-Math",
        code="CCSS.MATH.CONTENT.5.NF.B.4",
        grade=5,
        subject="Math",
        topic_tags=(
            "fractions", "multiply fractions", "fraction multiplication", "area model",
            "fraction by fraction", "fraction by whole number",
        ),
        text=(
            "Apply and extend previous understandings of multiplication to multiply a fraction "
            "or whole number by a fraction."
        ),
    ),
    Standard(
        framework="CCSS-Math",
        code="CCSS.MATH.CONTENT.5.NF.B.7",
        grade=5,
        subject="Math",
        topic_tags=("fractions", "divide fractions", "fraction division", "unit fractions"),
        text=(
            "Apply and extend previous understandings of division to divide unit fractions by "
            "whole numbers and whole numbers by unit fractions."
        ),
    ),
    # Math — Number & Operations in Base Ten
    Standard(
        framework="CCSS-Math",
        code="CCSS.MATH.CONTENT.5.NBT.B.6",
        grade=5,
        subject="Math",
        topic_tags=("division", "long division", "place value", "whole number division", "quotient"),
        text=(
            "Find whole-number quotients of whole numbers with up to four-digit dividends and "
            "two-digit divisors, using strategies based on place value, the properties of "
            "operations, and/or the relationship between multiplication and division."
        ),
    ),
    # Math — Geometry
    Standard(
        framework="CCSS-Math",
        code="CCSS.MATH.CONTENT.5.G.A.1",
        grade=5,
        subject="Math",
        topic_tags=("coordinate plane", "ordered pairs", "axes", "graphing", "geometry"),
        text=(
            "Use a pair of perpendicular number lines, called axes, to define a coordinate "
            "system, with the intersection of the lines (the origin) arranged to coincide with "
            "the 0 on each line and a given point in the plane located by using an ordered pair "
            "of numbers, called coordinates."
        ),
    ),
    # ELD — Part I (Interacting in Meaningful Ways)
    Standard(
        framework="ELD",
        code="ELD.PI.5.1",
        grade=5,
        subject="ELD",
        topic_tags=("collaborative discussion", "exchanging ideas", "academic conversation", "speaking"),
        text=(
            "Exchanging information and ideas with others through oral collaborative discussions "
            "on a range of social and academic topics."
        ),
    ),
    Standard(
        framework="ELD",
        code="ELD.PI.5.6",
        grade=5,
        subject="ELD",
        topic_tags=("close reading", "literary text", "informational text", "comprehension", "language"),
        text=(
            "Reading closely literary and informational texts and viewing multimedia to determine "
            "how meaning is conveyed explicitly and implicitly through language."
        ),
    ),
    # ELD — Part II (Learning About How English Works)
    Standard(
        framework="ELD",
        code="ELD.PII.5.1",
        grade=5,
        subject="ELD",
        topic_tags=("text structure", "organization", "argument structure", "writing"),
        text=(
            "Understanding text structure: Apply analysis of the organizational structure of "
            "different text types (e.g., how arguments are organized) to comprehending texts "
            "and writing texts."
        ),
    ),
    Standard(
        framework="ELD",
        code="ELD.PII.5.6",
        grade=5,
        subject="ELD",
        topic_tags=("connecting ideas", "compound sentences", "complex sentences", "syntax", "writing"),
        text=(
            "Connecting ideas: Combine clauses in a wide variety of ways (e.g., creating compound "
            "and complex sentences) to make connections between and join ideas."
        ),
    ),
)


STANDARDS_BY_CODE: dict[str, Standard] = {s.code: s for s in STANDARDS}


def all_codes() -> set[str]:
    return set(STANDARDS_BY_CODE.keys())


def standards_corpus_text() -> str:
    """Render the entire standards corpus as a multi-line string for prompts."""
    by_subject: dict[str, list[Standard]] = {}
    for s in STANDARDS:
        by_subject.setdefault(s.subject, []).append(s)

    sections: list[str] = []
    for subject in ("ELA", "Math", "ELD"):
        entries = by_subject.get(subject, [])
        if not entries:
            continue
        sections.append(f"{subject}:")
        for s in entries:
            sections.append(s.to_prompt_line())
    return "\n".join(sections)
