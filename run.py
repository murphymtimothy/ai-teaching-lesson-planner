"""CLI entry point for Phase 0 lesson plan generation.

Usage:
    python run.py --case ela
    python run.py --case math
    python run.py --case opinion
    python run.py --all
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console


# Force UTF-8 stdout so rich can render Unicode characters that the LLM
# legitimately produces (em-dashes, arrows, smart quotes) on Windows terminals
# that default to cp1252.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from poppy.pipeline import run_pipeline
from poppy.render import render
from poppy.schemas import PlanInput


# Phase 0 test cases — lifted directly from the prior chat sessions and the playbook.
CASES: dict[str, PlanInput] = {
    "ela": PlanInput(
        grade=5,
        subject="ELA",
        topic="theme through character motivation in a short story",
        duration_minutes=45,
        class_context=(
            "28 students. 6 English Learners at the Expanding (Intermediate) proficiency level, "
            "primarily Spanish home language. 2 students with IEPs (one with a reading goal "
            "currently on a 3rd-grade text level, one with attention/executive-functioning goals). "
            "No identified GATE students."
        ),
    ),
    "math": PlanInput(
        grade=5,
        subject="Math",
        topic="multiplying fractions using area models",
        duration_minutes=60,
        class_context=(
            "24 students. 4 newcomer English Learners (Emerging level, arrived in CA within the "
            "last 6 months — Mandarin, Vietnamese, and Spanish home languages). 3 students "
            "identified GATE who need extension. No IEPs in this section."
        ),
    ),
    "opinion": PlanInput(
        grade=5,
        subject="ELA",
        topic="opinion writing on whether school recess should be longer",
        duration_minutes=90,
        class_context=(
            "30 students. 8 English Learners spanning all proficiency levels: 2 Emerging, "
            "4 Expanding, 2 Bridging. 1 student with an IEP (writing goal at grade level with "
            "extended time accommodation). 2 GATE students."
        ),
    ),
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the Poppy lesson plan pipeline.")
    parser.add_argument(
        "--case",
        choices=sorted(CASES.keys()),
        help="Test case to run (defaults to 'ela' if --all not given)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run all three test cases sequentially",
    )
    parser.add_argument(
        "--no-save",
        action="store_true",
        help="Skip writing JSON output to outputs/",
    )
    args = parser.parse_args()

    # override=True so a pre-set empty ANTHROPIC_API_KEY in the shell environment
    # (e.g. inside Claude Code) doesn't shadow the value in .env
    load_dotenv(override=True)

    console = Console()
    cases_to_run: list[str]
    if args.all:
        cases_to_run = sorted(CASES.keys())
    elif args.case:
        cases_to_run = [args.case]
    else:
        cases_to_run = ["ela"]

    outputs_dir = Path(__file__).parent / "outputs"
    outputs_dir.mkdir(exist_ok=True)

    total_cost = 0.0
    for name in cases_to_run:
        plan_input = CASES[name]
        console.print(f"\n[cyan bold]Running case: {name}[/cyan bold]\n")
        with console.status("[cyan]Running 6-stage pipeline...[/cyan]", spinner="dots"):
            plan = run_pipeline(plan_input)

        # Save BEFORE rendering — rendering failures must not lose generated plans.
        if not args.no_save:
            out_path = outputs_dir / f"plan_{name}.json"
            out_path.write_text(plan.model_dump_json(indent=2), encoding="utf-8")

        render(plan, console)
        total_cost += plan.cost_usd

        if not args.no_save:
            console.print(f"[dim]Saved to {out_path.relative_to(Path(__file__).parent)}[/dim]\n")

    if len(cases_to_run) > 1:
        console.print(f"[bold]Total cost across {len(cases_to_run)} plans: ${total_cost:.4f}[/bold]")

    return 0


if __name__ == "__main__":
    sys.exit(main())
