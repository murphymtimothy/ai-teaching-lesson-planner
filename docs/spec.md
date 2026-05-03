# Poppy — Product Spec

> Working name. California-state-flower placeholder. Final name TBD; trademark
> check happens pre-launch.

## 1. Overview

### 1.1 Problem
California teachers spend 5–10 hours/week on lesson planning. Existing AI
planners (MagicSchool, Eduaide, Chalkie, Flint K12, Kuraplan) are national tools
that handle California's distinctive requirements — ELD integration, LCAP
priority alignment, History-Social Science framework, state-adopted curriculum
companion plans — as afterthoughts.

### 1.2 Audience
California K-12 public school teachers. Primary v1 audience: elementary and
middle school teachers using state-adopted curricula (Wonders, Benchmark
Advance, Bridges in Mathematics).

### 1.3 Solution
An AI lesson planner that is **California-native by default**: every plan
auto-aligns to CA-CCSS, CA-NGSS, CA ELD standards, the History-Social Science
Framework, and (Phase 2+) the most widely-adopted state curricula. Plans are
generated fresh per request — not stitched from stock content — using the
standards corpus only as grounding for retrieval and as a hard verification
gate against hallucinated codes.

### 1.4 Distribution / business model
Freemium for individual teachers. $12/mo or $99/yr Pro tier (priced between
Edcafe at $8 and MagicSchool at $15+). District licensing in year 2 once usage
data exists.

### 1.5 The differentiator
"The only AI lesson planner built for California's actual standards." Every
plan is observation-ready and audit-ready out of the box: standards tagged,
LCAP priorities marked, ELD moves integrated (not appendixed), differentiation
calibrated to the actual class roster.

---

## 2. Architecture

### 2.1 Six-stage pipeline

| Stage | Job | Method |
|---|---|---|
| 1. Retrieve | Pull candidate standards for the topic | Keyword overlap (Phase 0) → pgvector RAG (Phase 2) |
| 2. Scaffold | Objective, big idea, success criteria, standards | Sonnet 4.6 + adaptive thinking + tool-use structured output |
| 3. ELD overlay | Concrete Part I/II/III moves, SDAIE, sentence frames | Sonnet 4.6 |
| 4. LCAP classify | Tag to LCAP priorities + LCFF student groups | Sonnet 4.6 |
| 5. Activities | Warm-up, I-do/we-do/you-do, assessment, differentiation | Sonnet 4.6 |
| 6. Verify | Hard-reject plans with codes not in the corpus | Pure Python, deterministic |

Stage 6 is non-negotiable. A single hallucinated code in a teacher's plan kills
trust permanently.

### 2.2 Why six stages instead of one prompt
Single-shot prompts produce shallow plans where every section feels like
boilerplate, and they hallucinate standard codes ~5% of the time even with
careful prompting. Splitting the work gives each stage a focused prompt with
the prior stage's output as constraint, which empirically yields tighter
coherence and lets Stage 6 run as a deterministic gate.

---

## 3. Data model (Phase 0 → Phase 2)

### 3.1 Phase 0 (current — in-memory only)
- 12 hardcoded grade-5 standards (4 ELA, 4 Math, 4 ELD) in `poppy/standards.py`
- No persistence — pipeline output is JSON serialized to `outputs/`

### 3.2 Phase 2 (production)
- Postgres + pgvector
- Tables: `users`, `districts`, `lesson_plans`, `standards`, `alignments`,
  `lcap_tags`, `templates`, `curricula`, `curriculum_units`
- Standards table stores the full CA framework corpus with embeddings for
  retrieval. Each standard: `framework`, `code`, `grade`, `subject`, `text`,
  `topic_tags`, `embedding`.

---

## 4. AI design decisions

### 4.1 Model choice
**Sonnet 4.6 across all 4 LLM stages** for Phase 0. Cost per plan ~$0.10–0.20.
Sonnet 4.6 hits the right speed/quality balance for an evaluation phase where
we need throughput across 5+ teacher tests, not maximum reasoning depth on a
single plan.

**Phase 2 cost optimization:** drop Stage 4 (LCAP classify) to Haiku 4.5 once
teacher feedback confirms quality holds. Re-evaluate Stage 3 (ELD overlay)
similarly. Keep Sonnet 4.6+ for Stage 2 (scaffold) and Stage 5 (activities).
Promote to Opus 4.7 only if rubric scoring on the moat dimensions (#3 ELD
authenticity, #5 activities specificity) flatlines below threshold and prompt
patches don't move it.

### 4.2 Structured output
Tool-use forced via `tool_choice={"type": "tool", "name": "..."}` with the
Pydantic-derived JSON schema as `input_schema`. More reliable than `output_format`
for our nested objects, and works uniformly across all model versions.

### 4.3 Adaptive thinking
`thinking: {"type": "adaptive"}` on all stages. Default `effort` (high). Total
latency per plan: ~60–90s.

### 4.4 Prompt caching
**Skipped for Phase 0.** Standards corpus is ~600 tokens — under Opus 4.7's
4096-token cache minimum. Re-evaluate at Phase 2 once the corpus is the full CA
framework set (will be tens of thousands of tokens, easily cacheable).

---

## 5. UI / UX (Phase 2)

CLI only in Phase 0. Phase 2 surfaces:

1. **Onboard** — district + grades + subjects.
2. **Dashboard** — recents + new plan CTA.
3. **Generator wizard** — 3-step form (grade/subject → topic/duration → class context).
4. **Plan view** — editable sections with right-hand panel showing standards,
   ELD moves, LCAP tags. Each section has "regenerate" so teachers don't lose
   the rest when one part doesn't land.
5. **Export** — Google Docs, Word, PDF, observation-ready single-pager.

Stack (Phase 2): FastAPI + HTMX + Jinja + Tailwind + Alpine.js. Supabase for
auth/Postgres/pgvector/storage. Stripe. Hosted on Railway or Fly.io.

---

## 6. Curriculum companion (Phase 2+)

The wedge that takes Poppy from "good CA tool" to "indispensable CA tool":
companion plans for state-adopted curricula like Wonders, Benchmark Advance,
and Bridges. Teachers don't replace the curriculum — they layer Poppy's plans
on top to handle ELD scaffolds, IEP differentiation, pre-teaching, intervention,
extension, and quick assessments their packaged curriculum underprovides.

### 6.1 IP stance
We never reproduce copyrighted material. We use only publicly available
metadata: curriculum names, unit/week/lesson identifiers, the standards each
unit targets (often in CDE adoption documents), theme names, pacing. We
generate fresh ELD scaffolds, fresh differentiation, fresh extensions —
referenced TO the unit, not extracted FROM it. Position: *"Companion plans for
your Wonders / Bridges / Benchmark unit, tailored to your class."*

### 6.2 Sources we will use
- CDE adoption reports (publicly published)
- Publishers' marketing-facing scope-and-sequence (publicly available)
- District pacing guides published online
- Standards crosswalks the publishers themselves publish

### 6.3 Sources we will NOT use
- Teacher's edition content
- Stories, passages, problems from the curriculum
- Copyrighted scope-and-sequence text verbatim

---

## 7. Phase 0 → 1 → 2 plan

| Phase | Goal | Done when |
|---|---|---|
| 0 (current) | Validate AI quality with no infra | 4/5 plans score ≥10 on rubric, no zeros on dim #2 or #3 |
| 1 | Validate with real CA teachers | 5+ teachers pilot via Streamlit; ≥40% say "I'd pay $12/mo" |
| 2 | Production MVP | FastAPI app, Stripe live, 25 paid users |

---

## 8. Testing

### 8.1 Unit tests
- `tests/test_verify.py` — Stage 6 verification gate. **Critical**.
- Integration test (Phase 1+) — pipeline runs end-to-end on a fixture without
  errors.

### 8.2 Manual evaluation
- Apply the 7-dimension rubric (`docs/rubric.md`) to every Phase 0 plan
- Track scores per dimension over prompt iterations to know which patches help

### 8.3 Teacher validation (Phase 1)
- 5 CA teachers via personal network, r/Teachers, CA teacher Facebook groups
- Watch them use it. Note where they pause, where they edit, where they skip
- Closing question: "Would you pay $12/mo for this?"

---

## 9. Risks

- **Hallucinated codes.** Mitigation: Stage 6 hard gate + tests.
- **Generic ELD output.** Mitigation: rubric dimension #3, prompt-patch
  cookbook in `docs/playbook.md` Part 2.
- **Over-architected MVP.** Mitigation: Phase 0 is CLI only — no UI, no auth,
  no DB, no Stripe.
- **Curriculum companion IP risk.** Mitigation: §6 stance, pre-launch legal
  review.
- **Side-hustle scope creep.** Mitigation: explicit out-of-scope list per phase.

---

## 10. Out of scope for Phase 0
Authentication, accounts, database, Stripe, web UI, library/save, real
embeddings retrieval, curriculum companion, History-Social Science, NGSS,
multi-grade, multi-day units, full LCAP reporting.

---

## 11. Open questions

- Final product name (Poppy is placeholder)
- Class-context data privacy: how much PII can teachers paste into the
  generator? FERPA implications for any storage. Phase 1 minimum: don't store
  per-student data, only aggregate counts.
- Free-tier observer-summary export — does it ship in free, or is it the Pro
  hook?
- District sales motion — wait until year 2 with usage data, or run a
  parallel small-district pilot in year 1?
