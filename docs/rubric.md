# Phase 0 Evaluation Rubric

Score every plan generated against these seven dimensions. Each dimension is
scored **0**, **1**, or **2** for a maximum of **14**. The rubric is the
throttle: don't move on to Phase 1 until plans clear the bar.

## Pass thresholds

- **4 of 5 plans must score ≥10/14**, AND
- **No plan scores 0** on dimensions #2 (standards fit) or #3 (ELD authenticity)

#3 is the moat. Generic ELD = the product doesn't work. Treat a 0 there as a
hard fail, not a single bad plan to average out.

---

## Dimensions

### 1. Objective specificity (0–2)
Is the SWBAT objective specific, measurable, and tied to a higher-order verb?

- **0** — Vague or non-measurable ("Students will understand theme")
- **1** — Specific but the verb is low-level ("identify", "list") for a 5th-grade lesson
- **2** — Specific, measurable, higher-order verb that matches the standard ("compare two characters' motivations using textual evidence")

### 2. Standards fit (0–2)
Do the cited standards actually fit what the lesson does, and are the codes correct?

- **0** — Standards are wrong, hallucinated codes appear (Stage 6 should catch these — if you're scoring this, the gate failed), or 5+ standards are cited (lesson is unfocused)
- **1** — Standards are reasonable but a tighter pick exists, or one citation is a stretch
- **2** — Each cited standard is the most-specific applicable code for what the lesson actually does

### 3. ELD authenticity (0–2) — THE MOAT
Are the ELD moves real, classroom-ready CA ELD work, or generic ELL boilerplate?

- **0** — Generic ("provide visuals", "use sentence frames" — no specifics) or boilerplate any non-CA tool would emit
- **1** — Some specificity but doesn't match the proficiency levels in the class context, or only Part I is addressed when Part II would help
- **2** — Concrete moves anchored in CA ELD Part I/II/III. Sentence frames are calibrated to the class's actual proficiency mix. SDAIE strategies are lesson-specific, not pulled from a generic list.

### 4. Differentiation (0–2)
Does differentiation match the actual students described in class context?

- **0** — Generic, identical for every plan, ignores class context, or differentiates students that aren't in the class (GATE supports for a class with no GATE)
- **1** — Real differentiation but only addresses one group well (e.g., good EL supports, weak IEP supports)
- **2** — Concrete, student-specific supports for every group named in class context. References specific accommodations from the IEP context, calibrates EL supports to proficiency, extends GATE meaningfully (depth/complexity, not just "more problems")

### 5. Activities specificity (0–2)
Are the activities concrete enough that a teacher can run this lesson tomorrow without modification?

- **0** — Generic activity stubs ("students discuss the text") with no actual prompts, problems, or texts named
- **1** — Some sections concrete, others vague — typically warm-up and assessment are skimped on
- **2** — Every section includes specific teacher questions, specific student tasks, specific time allocations that sum to the lesson duration

### 6. LCAP relevance (0–2)
Are the LCAP tags accurate to what the lesson does, or pad?

- **0** — All 8 priorities tagged (meaningless), or tags don't match the lesson, or rationale is platitudes
- **1** — Reasonable tags but rationale is generic
- **2** — 1–3 priorities that genuinely apply, student groups match the actual class, rationale references specific lesson elements

### 7. Coherence (0–2)
Does the plan hold together — objective → activities → assessment all align, ELD moves are woven in (not bolted on)?

- **0** — Internal contradictions (assessment doesn't measure the objective; activities don't advance the success criteria; ELD section reads like a separate document)
- **1** — Mostly coherent with one rough seam (e.g., assessment is shallower than the objective demands)
- **2** — Tight loop. Every section serves the objective. ELD moves appear inside the activities where they belong.

---

## Scoring sheet

For each plan you generate, fill in:

```
Plan: <case name>
Date: ___
Scorer: ___

Dimension                          Score (0/1/2)  Notes
1. Objective specificity            ___
2. Standards fit                    ___
3. ELD authenticity                 ___           ← critical
4. Differentiation                  ___
5. Activities specificity           ___
6. LCAP relevance                   ___
7. Coherence                        ___
                                    -------
Total                               ___ / 14
```

If a dimension fails (0), apply the matching prompt patch from
`docs/playbook.md` Part 2 before re-running.
