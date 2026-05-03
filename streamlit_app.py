"""Phase 1 Streamlit interface — public-link tool to hand to teacher testers.

Run:
    pip install -e ".[web]"
    streamlit run streamlit_app.py
"""

from __future__ import annotations

import os
import time
from datetime import datetime
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from poppy.pipeline import HallucinationError, run_pipeline
from poppy.render import to_markdown
from poppy.schemas import PlanInput


# Load API key from .env. override=True so a pre-set empty
# ANTHROPIC_API_KEY in the shell doesn't shadow the file value.
load_dotenv(override=True)


PRESETS: dict[str, dict] = {
    "ELA — theme through character motivation": dict(
        grade=5,
        subject="ELA",
        topic="theme through character motivation in a short story",
        duration_minutes=45,
        class_context=(
            "28 students. 6 English Learners at the Expanding (Intermediate) "
            "proficiency level, primarily Spanish home language. 2 students "
            "with IEPs (one with a reading goal at 3rd-grade text level, one "
            "with attention/executive-functioning goals). No identified GATE "
            "students."
        ),
    ),
    "Math — fraction multiplication": dict(
        grade=5,
        subject="Math",
        topic="multiplying fractions using area models",
        duration_minutes=60,
        class_context=(
            "24 students. 4 newcomer ELs (Emerging — Mandarin, Vietnamese, "
            "and Spanish home languages). 3 GATE students. No IEPs."
        ),
    ),
    "ELA — opinion writing": dict(
        grade=5,
        subject="ELA",
        topic="opinion writing on whether school recess should be longer",
        duration_minutes=90,
        class_context=(
            "30 students. 8 ELs spanning all proficiency levels: 2 Emerging, "
            "4 Expanding, 2 Bridging. 1 IEP (writing goal at grade level with "
            "extended time accommodation). 2 GATE."
        ),
    ),
}


STAGE_LABELS = {
    "retrieve": "Retrieving relevant California standards",
    "scaffold": "Drafting objective + success criteria",
    "eld": "Designing ELD overlay (Part I/II/III + sentence frames)",
    "lcap": "Tagging LCAP priorities + student groups",
    "activities": "Writing warm-up, I-do/we-do/you-do, assessment, differentiation",
    "verify": "Verifying every cited standard against the corpus",
}


# ─── Page config ──────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Poppy — California Lesson Planner (preview)",
    page_icon="🌼",
    layout="wide",
)

st.title("Poppy")
st.caption(
    "California-native AI lesson planner — Phase 1 preview. "
    "All plans auto-align to CA-CCSS, CA-NGSS, and CA ELD standards. Currently "
    "supports grade 5 (ELA / Math) — more grades and subjects coming."
)


# ─── Sidebar: API key sanity check + presets ─────────────────────────────────

with st.sidebar:
    st.subheader("Status")
    if os.environ.get("ANTHROPIC_API_KEY"):
        st.success("API key loaded")
    else:
        st.error("No ANTHROPIC_API_KEY found. Set it in .env and restart.")

    st.divider()

    st.subheader("Quick presets")
    st.caption("Click a preset to populate the form below.")
    for name in PRESETS:
        if st.button(name, use_container_width=True):
            st.session_state["preset"] = PRESETS[name]
            st.rerun()


# ─── Input form ──────────────────────────────────────────────────────────────

defaults = st.session_state.get(
    "preset",
    dict(grade=5, subject="ELA", topic="", duration_minutes=45, class_context=""),
)

st.subheader("Lesson request")

col1, col2, col3 = st.columns([1, 1, 1])
with col1:
    grade = st.number_input(
        "Grade",
        min_value=0,
        max_value=12,
        value=defaults["grade"],
        help="Phase 1 supports grade 5; other grades will produce best-effort output.",
    )
with col2:
    subject = st.selectbox(
        "Subject",
        options=["ELA", "Math", "ELD"],
        index=["ELA", "Math", "ELD"].index(defaults["subject"]),
    )
with col3:
    duration = st.number_input(
        "Duration (minutes)",
        min_value=10,
        max_value=180,
        value=defaults["duration_minutes"],
        step=5,
    )

topic = st.text_input(
    "Topic / focus",
    value=defaults["topic"],
    placeholder="e.g., theme through character motivation in a short story",
)

class_context = st.text_area(
    "Class context",
    value=defaults["class_context"],
    placeholder=(
        "Enrollment, EL counts and proficiency levels, IEP/504 students, "
        "GATE students. The more concrete you are, the better the differentiation."
    ),
    height=100,
)

generate = st.button(
    "Generate lesson plan",
    type="primary",
    disabled=not (topic and class_context and os.environ.get("ANTHROPIC_API_KEY")),
)


# ─── Generation ──────────────────────────────────────────────────────────────

if generate:
    plan_input = PlanInput(
        grade=int(grade),
        subject=subject,
        topic=topic.strip(),
        duration_minutes=int(duration),
        class_context=class_context.strip(),
    )

    progress_box = st.empty()
    status_lines: list[str] = []

    def on_progress(stage: str, status: str) -> None:
        label = STAGE_LABELS.get(stage, stage)
        if status == "started":
            status_lines.append(f"⏳ {label}…")
        else:  # done
            if status_lines and status_lines[-1].startswith("⏳"):
                status_lines[-1] = f"✅ {label}"
        progress_box.markdown("  \n".join(status_lines))

    started = time.monotonic()
    try:
        plan = run_pipeline(plan_input, on_progress=on_progress)
    except HallucinationError as e:
        progress_box.error(f"Stage 6 rejected the plan: {e}")
        st.stop()
    except Exception as e:
        progress_box.error(f"Generation failed: {e}")
        raise
    elapsed = time.monotonic() - started

    progress_box.success(
        f"Generated in {elapsed:.0f}s · "
        f"cost ${plan.cost_usd:.4f} · "
        f"Stage 6 verification {'passed' if plan.verified else 'FAILED'}"
    )

    # Persist to disk for the operator (us)
    out_dir = Path("outputs") / "phase1_runs"
    out_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = out_dir / f"{timestamp}_{subject.lower()}.json"
    json_path.write_text(plan.model_dump_json(indent=2), encoding="utf-8")

    # Render plan
    md = to_markdown(plan)
    st.divider()
    st.download_button(
        label="Download as markdown",
        data=md,
        file_name=f"lesson_plan_{timestamp}.md",
        mime="text/markdown",
    )
    st.markdown(md)


# ─── Footer ──────────────────────────────────────────────────────────────────

st.divider()
st.caption(
    "Built for California teachers. Plans are AI-generated; review before "
    "running with students. Feedback welcome."
)
