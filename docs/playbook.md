# Phase 0 → Phase 1 Playbook

Two parts:
1. **Recruitment templates** — to source 5–10 California teachers as Phase 1 pilot testers
2. **Prompt patches** — to fix the most likely Phase 0 failure modes

---

# Part 1: Recruitment

The bottleneck for Phase 1 is real California teachers willing to use a beta
tool and tell you the truth. Cast wide; expect a high non-response rate.

## 1.1 Personal network (start here)

Highest signal-to-noise. If you know any CA teachers personally, send the DM
template below first.

```
Hey [name],

Working on a side project — an AI lesson planner specifically built for CA
standards (auto-aligns to ELD, LCAP, the whole thing). Most existing tools
are national and treat CA as an afterthought.

It's at the "5 testers and a working prototype" stage. Would you be up for
trying it on one lesson and telling me what's wrong with it? 15 min max,
totally OK to say no.

If you know any other CA teachers who'd give honest feedback, would
appreciate a referral too. No pressure.
```

**Goal:** 5 CA teachers from your network within a week.
**Ask each of them for 2 referrals.**

## 1.2 r/Teachers (after personal network)

Long, transparent post. Not a pitch — an ask for help. Teachers smell
marketing instantly.

```
Title: I'm building an AI lesson planner specifically for California — would
5 CA teachers help me test it?

I'm an indie developer (not a teacher) building a tool that auto-aligns
plans to CA-CCSS, ELD standards, and LCAP priorities — the stuff
MagicSchool / Eduaide / Chalkie don't handle well because they're national.

I have a working prototype. I need 5 CA teachers (any K-12 grade, any
subject) who'd be willing to:
- Generate one lesson plan for a topic you actually need to teach
- Tell me bluntly what's wrong with it
- Take ~15 minutes total

In exchange:
- Free Pro tier for 6 months when I launch (~$72 value)
- Your feedback shapes the product

I'm not going to pretend this is altruistic — your input makes the tool
better, which makes the tool worth paying for, which makes my side hustle
viable. Mutual benefit, I think.

Comment or DM if you're in. Happy to answer questions about the project
first.
```

**Goal:** 5+ CA teachers within 2 weeks. Expect ~10% conversion from comments
to actual testers.

## 1.3 CA teacher Facebook groups

Short, in-group tone. Lead with "California" — it's the differentiator.

```
Hey CA teachers — I'm a developer building an AI lesson planner that's
actually built around CA standards (ELD integration, LCAP tagging, the
whole California-specific mess). Looking for 5 of you to test it on one
lesson and tell me what's wrong with it. ~15 min. DM me if interested.
```

**Goal:** Don't expect much from FB groups. Volume play.

## 1.4 Credential program emails (longer-term)

If you went to or know a CA credential program, a short email to the program
director is a high-leverage move — they often have alumni networks of
teachers actively writing lesson plans for the credential portfolio.

## 1.5 Tester intake form

For every tester, capture before they start:
- Grade(s) and subject(s) they teach
- District (just to confirm CA)
- Curriculum they currently use (Wonders / Benchmark / Bridges / district-built / other)
- ~% English Learners in their class
- Whether they have IEP students

After the test:
- What surprised you? (open)
- What was wrong? (open — most valuable answer)
- Would you use this again? (yes / probably / probably not / no)
- **Would you pay $12/mo for this if it had: [list of features]?** (this is the only conversion signal that matters)

Skip everything else. Don't ask "rate the lesson plan 1-10" — useless data.

---

# Part 2: Prompt patches

If Phase 0 plans don't clear the rubric, the failure usually maps to one of
three failure modes. Apply the matching patch, rerun the same case, rescore.

## 2.1 Failure mode: Generic ELD (rubric dim #3 = 0)

**Symptom:** ELD section reads like ELL boilerplate any non-CA tool would
produce. Sentence frames are generic. Moves don't reference Part I/II/III
distinctions. Doesn't differentiate by proficiency level.

**Diagnosis:** Stage 3 prompt isn't anchoring concretely enough in the class
context's proficiency levels.

**Patch in `poppy/prompts.py:eld_prompt`:** add to the system prompt before the
existing critical rules:

```
PROFICIENCY-LEVEL CALIBRATION IS NON-NEGOTIABLE.
When the class context names specific levels, your moves and frames must
explicitly differentiate. Example:
  - For Emerging: "yes/no" or "either/or" frames with high visual support
  - For Expanding: "open" frames with sentence stems requiring 1-2 ideas
  - For Bridging: paragraph frames or open prompts with academic register

If a frame works for "all ELs", you have not done your job. Specify which
level it serves.
```

**Validation:** Sentence frames should be tagged by level, OR the ELD section
should explicitly call out which moves serve Emerging vs. Expanding vs.
Bridging students.

---

## 2.2 Failure mode: Boilerplate differentiation (rubric dim #4 = 0 or 1)

**Symptom:** EL/IEP/GATE supports are identical across plans, ignore the
specific class context, or differentiate students who aren't in the class.

**Diagnosis:** Stage 5 prompt isn't enforcing the class-context tie.

**Patch in `poppy/prompts.py:activities_prompt`:** add to the system prompt:

```
DIFFERENTIATION MUST BE STUDENT-SPECIFIC.
Re-read the class context before drafting differentiation. For each named
group:
  - If the context names a count (e.g., "2 IEP students with reading goals
    at 3rd-grade level"), your support must address that specific count and
    those specific goals.
  - If a group is NOT mentioned (e.g., no GATE in the class), set that
    differentiation field to an empty string. Do not invent students.
  - "Provide visual supports" / "give more time" / "reduce complexity" are
    not differentiation. They are placeholders. Replace them with concrete,
    lesson-specific scaffolds.
```

Also add to the schema's `Activities.differentiation_iep` field description:

> "Specific. Empty string if class context indicates no IEP students."

**Validation:** A class context with "no IEPs" should produce an empty
`differentiation_iep` field. Differentiation text should reference numbers
and specific goals from the class context.

---

## 2.3 Failure mode: Wrong / hallucinated standards (rubric dim #2 = 0)

**Symptom:** Stage 6 rejects the plan with a `HallucinationError`, OR the
plan passes Stage 6 but cites a code that's a stretch for the lesson.

**Diagnosis:** Stage 2 (scaffold) prompt isn't constraining the model tightly
enough to the corpus.

**Patches (apply progressively):**

### 2.3a — Tighten the scaffold system prompt

In `poppy/prompts.py:scaffold_prompt`, replace the bullet on inventing codes
with stronger language:

```
- Cite ONLY codes that appear character-for-character in the standards
  corpus below. If you cannot find a good fit, cite the closest available
  code and call out the limitation in the structure overview. NEVER emit a
  code in `standards_cited` that is not in the corpus. This is verified
  programmatically and an invalid code rejects the entire plan.
```

### 2.3b — Add a one-shot example

If 2.3a doesn't fix it, prepend to the user message a worked example showing
correct citation:

```
Example of correct citation (do not copy verbatim — pick fresh codes for the
actual lesson):

  Topic: "comparing two characters in a story"
  → standards_cited: ["CCSS.ELA-LITERACY.RL.5.3"]
  Reasoning: RL.5.3 is the only corpus standard about comparing characters
  in a story. Other RL.5.* codes are about textual evidence (.1) or are
  not in the corpus.

Now scaffold the actual request:
```

### 2.3c — Drop to retrieval-only candidates

If 2.3a + 2.3b still produce wrong codes, change Stage 2 to require the model
to pick FROM the candidates list specifically, not from the broader corpus.
Update the system prompt:

```
You may cite ONLY codes from the candidate list provided in the user
message. If none of the candidates fit, return an empty `standards_cited`
list and explain in the structure overview why no candidate matched.
```

This trades flexibility for accuracy. Use only if the broader-corpus version
keeps producing bad cites.

---

## 2.4 Triage cheat-sheet

| Rubric dimension scoring 0 or 1 | Apply patch |
|---|---|
| #1 Objective specificity | Add SWBAT examples to scaffold prompt |
| #2 Standards fit | §2.3 (a → b → c progression) |
| #3 ELD authenticity | §2.1 |
| #4 Differentiation | §2.2 |
| #5 Activities specificity | Add "include exact teacher questions and student tasks" to activities prompt |
| #6 LCAP relevance | Reduce max priorities allowed in lcap prompt to 2; sharpen rationale instruction |
| #7 Coherence | Pass Stage 5 the success criteria explicitly so the assessment ties back |

---

## 2.5 Decision tree

After scoring 5 plans:

- **All 5 score ≥10/14, no zeros on #2 or #3** → Greenlight Phase 1. Build
  Streamlit wrapper, send the personal-network DM template.
- **Specific dimension consistently fails** → Apply matching patch from
  above. Rerun same 5 cases. Rescore. Iterate.
- **Plans are mediocre across the board** → Don't try to fix everything at
  once. Pick the highest-leverage failure (usually #3 or #5) and fix it
  first. Then re-evaluate.
- **Plans are bad and prompt patches don't help** → The model likely needs
  better grounding. Options: expand the standards corpus, add a few-shot
  example with a known-good plan, or surface the failure mode to a CA
  teacher friend for prompt expertise.
