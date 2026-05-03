# Poppy — Phase 0

AI lesson planner for California teachers. **Phase 0** is the runnable
pipeline only — no UI, no database, no auth. The goal is to validate AI quality
before building anything else.

> Working name. The California golden poppy is the state flower. Easy to
> rename later — single find-and-replace.

## What this does

Given a grade, subject, topic, and class context, runs a 6-stage pipeline that
generates a complete lesson plan aligned to California standards:

1. **Retrieve** — keyword-match the topic against the 12 hardcoded grade-5 standards
2. **Scaffold** — objective, success criteria, targeted standards (Sonnet 4.6)
3. **ELD overlay** — Part I/II/III moves, sentence frames calibrated to EL proficiency (Sonnet 4.6)
4. **LCAP classify** — tag to LCAP State Priorities + LCFF student groups (Sonnet 4.6)
5. **Activities** — warm-up, I-do/we-do/you-do, assessment, differentiation (Sonnet 4.6)
6. **Verify** — deterministic gate: reject any cited standard not in the corpus

## Quick start

### 1. Set up the venv (Windows)

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
```

### 2. Get an Anthropic API key

If you don't already have one:

1. Go to <https://console.anthropic.com/>
2. Sign up (or sign in)
3. Add a payment method (Phase 0 uses ~$1 for the full eval — set a $5 cap to be safe)
4. Settings → API Keys → Create Key
5. Copy the key (starts with `sk-ant-`)

Then create a `.env` file:

```bash
cp .env.example .env
# edit .env and paste your key
```

### 3. Run the verification tests

These don't hit the API — they verify Stage 6 (the deterministic gate) works:

```bash
python -m pytest tests/ -v
```

All 9 tests should pass. If any fail, do not proceed.

### 4. Generate a lesson plan

```bash
python run.py --case ela
```

This runs all 6 stages against test case `ela` (5th grade ELA — theme through
character motivation). Takes ~60–90 seconds. Output prints to terminal and
saves to `outputs/plan_ela.json`.

Other cases:

```bash
python run.py --case math       # 5th grade fraction multiplication
python run.py --case opinion    # 5th grade opinion writing
python run.py --all             # run all three sequentially (~$1 total)
```

### 5. Score the output

Open `docs/rubric.md`. Score the generated plan against the 7 dimensions.
Phase 0 passes when 4 of 5 plans score ≥10/14 with no zeros on dimensions
#2 (standards fit) or #3 (ELD authenticity).

## What's next

If plans pass the rubric → build Phase 1 (Streamlit wrapper, recruit 5 CA
teachers using `docs/playbook.md` Part 1).

If plans fail a dimension → apply the matching patch from `docs/playbook.md`
Part 2, rerun, rescore.

## Project layout

```
.
├── poppy/                      # The package
│   ├── pipeline.py             # Orchestrates the 6 stages
│   ├── schemas.py              # Pydantic models for stage I/O
│   ├── standards.py            # 12 hardcoded grade-5 standards
│   ├── prompts.py              # Per-stage prompt templates
│   ├── llm.py                  # Anthropic client wrapper + cost tracking
│   └── render.py               # Pretty-print plans to terminal
├── tests/test_verify.py        # Stage 6 unit tests
├── docs/
│   ├── spec.md                 # Full product spec
│   ├── playbook.md             # Recruitment + prompt-patch cookbook
│   └── rubric.md               # 7-dimension evaluation rubric
├── outputs/                    # Generated plans land here (gitignored)
└── run.py                      # CLI entry point
```

## Cost

Each plan costs ~$0.10–0.20 with Sonnet 4.6. Phase 0's full evaluation (3 test
cases) is well under $1. Set a $5 monthly cap on the Anthropic console as a
safety net.

## Out of scope

Authentication, database, web UI, payments, multi-grade, multi-day units,
curriculum companion (Wonders / Benchmark / Bridges), History-Social Science
framework, NGSS. All Phase 2.
