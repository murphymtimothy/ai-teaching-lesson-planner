"""Pretty-print a FullPlan.

Two surfaces:
- `render(plan, console)` — terminal output via rich (used by run.py)
- `to_markdown(plan)` — pure markdown string (used by streamlit_app.py and exports)
"""

from __future__ import annotations

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

from poppy.schemas import FullPlan


def render(plan: FullPlan, console: Console | None = None) -> None:
    if console is None:
        console = Console()

    # Header
    header = (
        f"**Grade {plan.input.grade} {plan.input.subject}** · "
        f"{plan.input.duration_minutes} min · "
        f"{plan.input.topic}"
    )
    console.print()
    console.print(Panel(Markdown(header), title="Lesson Plan", border_style="cyan"))

    # Class context
    console.print(f"\n[dim]Class context:[/dim] {plan.input.class_context}")

    # Scaffold
    console.print()
    console.rule("[bold]Scaffold")
    console.print(f"[bold]Objective:[/bold] {plan.scaffold.objective}")
    console.print(f"[bold]Big idea:[/bold] {plan.scaffold.big_idea}")
    console.print(f"\n[bold]Success criteria:[/bold]")
    for sc in plan.scaffold.success_criteria:
        console.print(f"  • {sc}")
    console.print(f"\n[bold]Standards targeted:[/bold]")
    for code in plan.scaffold.standards_cited:
        console.print(f"  • {code}")
    console.print(f"\n[bold]Structure:[/bold] {plan.scaffold.structure_overview}")

    # ELD overlay
    console.print()
    console.rule("[bold]ELD Overlay")
    if plan.eld.part_i_moves:
        console.print("[bold]Part I — Interacting in Meaningful Ways:[/bold]")
        for m in plan.eld.part_i_moves:
            console.print(f"  • {m}")
    if plan.eld.part_ii_moves:
        console.print("\n[bold]Part II — How English Works:[/bold]")
        for m in plan.eld.part_ii_moves:
            console.print(f"  • {m}")
    if plan.eld.part_iii_moves:
        console.print("\n[bold]Part III — Foundational Literacy:[/bold]")
        for m in plan.eld.part_iii_moves:
            console.print(f"  • {m}")
    if plan.eld.sdaie_strategies:
        console.print("\n[bold]SDAIE strategies:[/bold]")
        for s in plan.eld.sdaie_strategies:
            console.print(f"  • {s}")
    if plan.eld.sentence_frames:
        console.print("\n[bold]Sentence frames:[/bold]")
        for f in plan.eld.sentence_frames:
            console.print(f"  → {f}")
    console.print(f"\n[bold]ELD standards cited:[/bold] {', '.join(plan.eld.eld_standards_cited)}")

    # LCAP
    console.print()
    console.rule("[bold]LCAP Tagging")
    console.print(f"[bold]Priorities:[/bold] {', '.join(map(str, plan.lcap.priorities))}")
    console.print(f"[bold]Student groups:[/bold] {', '.join(plan.lcap.student_groups)}")
    console.print(f"[bold]Rationale:[/bold] {plan.lcap.rationale}")

    # Activities
    console.print()
    console.rule("[bold]Activities")
    if plan.activities.materials:
        console.print(f"[bold]Materials:[/bold]")
        for m in plan.activities.materials:
            console.print(f"  • {m}")
    console.print(f"\n[bold]Warm-up:[/bold]\n{plan.activities.warm_up}")
    console.print(f"\n[bold]I do:[/bold]\n{plan.activities.i_do}")
    console.print(f"\n[bold]We do:[/bold]\n{plan.activities.we_do}")
    console.print(f"\n[bold]You do:[/bold]\n{plan.activities.you_do}")
    console.print(f"\n[bold]Assessment:[/bold]\n{plan.activities.assessment}")

    console.print()
    console.rule("[bold]Differentiation")
    console.print(f"[bold]English Learners:[/bold]\n{plan.activities.differentiation_el}")
    if plan.activities.differentiation_iep:
        console.print(f"\n[bold]IEP / 504:[/bold]\n{plan.activities.differentiation_iep}")
    if plan.activities.differentiation_gate:
        console.print(f"\n[bold]GATE / Extension:[/bold]\n{plan.activities.differentiation_gate}")

    # Footer
    console.print()
    table = Table(show_header=False, show_edge=False, box=None)
    table.add_column(style="dim")
    table.add_column()
    table.add_row("Stage 6 verification", "[green]passed[/green]" if plan.verified else "[red]FAILED[/red]")
    table.add_row("Candidates retrieved", ", ".join(plan.candidate_standards))
    table.add_row("Cost (this run)", f"${plan.cost_usd:.4f}")
    console.print(table)
    console.print()


def to_markdown(plan: FullPlan) -> str:
    """Serialize a FullPlan to a teacher-readable markdown document."""
    p = plan
    lines: list[str] = []

    lines.append(f"# Lesson Plan — Grade {p.input.grade} {p.input.subject}")
    lines.append("")
    lines.append(f"**Topic:** {p.input.topic}  ")
    lines.append(f"**Duration:** {p.input.duration_minutes} minutes  ")
    lines.append(f"**Class context:** {p.input.class_context}")
    lines.append("")

    # Scaffold
    lines.append("## Scaffold")
    lines.append("")
    lines.append(f"**Objective:** {p.scaffold.objective}")
    lines.append("")
    lines.append(f"**Big idea:** {p.scaffold.big_idea}")
    lines.append("")
    lines.append("**Success criteria:**")
    for sc in p.scaffold.success_criteria:
        lines.append(f"- {sc}")
    lines.append("")
    lines.append("**Standards targeted:**")
    for code in p.scaffold.standards_cited:
        lines.append(f"- `{code}`")
    lines.append("")
    lines.append(f"**Structure:** {p.scaffold.structure_overview}")
    lines.append("")

    # ELD
    lines.append("## ELD Overlay")
    lines.append("")
    if p.eld.part_i_moves:
        lines.append("### Part I — Interacting in Meaningful Ways")
        for m in p.eld.part_i_moves:
            lines.append(f"- {m}")
        lines.append("")
    if p.eld.part_ii_moves:
        lines.append("### Part II — How English Works")
        for m in p.eld.part_ii_moves:
            lines.append(f"- {m}")
        lines.append("")
    if p.eld.part_iii_moves:
        lines.append("### Part III — Foundational Literacy Skills")
        for m in p.eld.part_iii_moves:
            lines.append(f"- {m}")
        lines.append("")
    if p.eld.sdaie_strategies:
        lines.append("### SDAIE Strategies")
        for s in p.eld.sdaie_strategies:
            lines.append(f"- {s}")
        lines.append("")
    if p.eld.sentence_frames:
        lines.append("### Sentence Frames")
        for f in p.eld.sentence_frames:
            lines.append(f"- {f}")
        lines.append("")
    lines.append(
        "**ELD standards cited:** "
        + ", ".join(f"`{c}`" for c in p.eld.eld_standards_cited)
    )
    lines.append("")

    # LCAP
    lines.append("## LCAP Tagging")
    lines.append("")
    lines.append(
        "**Priorities:** " + ", ".join(str(n) for n in p.lcap.priorities)
    )
    lines.append("")
    lines.append("**Student groups:** " + ", ".join(p.lcap.student_groups))
    lines.append("")
    lines.append(f"**Rationale:** {p.lcap.rationale}")
    lines.append("")

    # Activities
    lines.append("## Activities")
    lines.append("")
    if p.activities.materials:
        lines.append("### Materials")
        for m in p.activities.materials:
            lines.append(f"- {m}")
        lines.append("")
    lines.append("### Warm-up")
    lines.append(p.activities.warm_up)
    lines.append("")
    lines.append("### I do")
    lines.append(p.activities.i_do)
    lines.append("")
    lines.append("### We do")
    lines.append(p.activities.we_do)
    lines.append("")
    lines.append("### You do")
    lines.append(p.activities.you_do)
    lines.append("")
    lines.append("### Assessment")
    lines.append(p.activities.assessment)
    lines.append("")

    # Differentiation
    lines.append("## Differentiation")
    lines.append("")
    lines.append("### English Learners")
    lines.append(p.activities.differentiation_el)
    lines.append("")
    if p.activities.differentiation_iep:
        lines.append("### IEP / 504")
        lines.append(p.activities.differentiation_iep)
        lines.append("")
    if p.activities.differentiation_gate:
        lines.append("### GATE / Extension")
        lines.append(p.activities.differentiation_gate)
        lines.append("")

    # Footer
    lines.append("---")
    lines.append("")
    lines.append(
        f"*Stage 6 verification: {'passed' if p.verified else 'FAILED'} · "
        f"Generation cost: ${p.cost_usd:.4f}*"
    )

    return "\n".join(lines)
