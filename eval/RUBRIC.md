# Planck AI evaluation rubric

**Written and committed before the first API call.** Every definition below was
fixed in advance so no metric could be shaped after seeing results. The commit
that adds this file precedes the commit that adds any result.

## Golden set

30 questions, evenly spread across the four capabilities the agent advertises:

| Category | n | What it tests |
|---|---|---|
| `code` | 8 | Deterministic computation the agent should execute, not estimate |
| `web` | 8 | Facts the model cannot reliably answer from parameters alone |
| `multi_step` | 7 | Two or more dependent operations in one question |
| `document` | 7 | Reading a named PDF or URL and answering from its contents |

Each question is fixed before running and carries:

- `expected_tool` — the tool that *should* fire, decided in advance from the
  question type, not from what the agent did.
- `answer_check` — how to verify the final answer, or `null` when the question
  has no single checkable target.

## Metrics

### 1. Tool-selection accuracy — primary
Fraction of questions where `expected_tool` appears in the trajectory's tool
calls. Read mechanically off the trajectory. No judgment.

A question where the model could answer from memory still counts as a miss if
it skipped the tool: the agent runs in web mode, whose purpose is grounded
answers, and an ungrounded answer is a failure of that contract even when the
text happens to be right.

### 2. Median end-to-end latency — instrumentation only
Wall-clock seconds from request to final response chunk. Median over all
completed questions, reported with p90. Measured on a home broadband
connection against free-tier provider endpoints; it is a property of that
setup, not of the agent alone, and is reported as such.

### 3. Task success — reported on the checkable subset ONLY
Only questions carrying an `answer_check` count toward this number, and the
subset size is always reported alongside it. Two check kinds, both mechanical:

- `exact` — the normalised target string appears in the final answer.
  Normalisation: lowercase; strip markdown emphasis (`*`, `_`, backticks);
  replace every Unicode space (including U+202F narrow no-break space) with a
  plain space; delete commas and spaces *between digits*; collapse remaining
  whitespace.

  **Amendment, made during the pilot and before any scored run.** The original
  wording said only "strip commas in digit groups, collapse whitespace". The
  3-question pilot showed the model returns `**832\u202f040**` — markdown
  emphasis and a narrow no-break space inside the number — which the original
  rule would have scored as wrong for a correct answer. Both are presentation,
  not content, so normalising them is within what the rule was for. Recorded
  here rather than applied silently.
- `all_of` — every string in the list appears, normalised the same way.

**No LLM-as-judge.** A model grading another model's output is a weak number
and does not survive being asked about it. Questions without a mechanical
check are excluded from this metric and still counted in the others.

### 4. Fault-injection completion — mechanical definition
The primary provider is disabled before the run. A question counts as
**completed** if the agent produced a final `response` chunk without an
`error` chunk.

Completed means *produced a final answer*, not *produced a good answer*.
Quality under failover is reported separately by applying metrics 1 and 3 to
the fault-injection trajectories, so the completion number stays objective.

## Rules fixed in advance

1. **One attempt per question.** No re-runs, no best-of-n. A question that
   fails on a rate limit is recorded as `rate_limited` and excluded from every
   metric, with the count reported.
2. **Trajectories are appended to disk as each question finishes**, so a
   failure part-way through cannot silently reshape the sample.
3. **The golden set is frozen** once the first question runs. Questions are
   never edited, dropped or added after seeing a result.
4. **Both runs use the same golden set** in the same order.
5. Every reported number carries its denominator.

## What this rubric deliberately does not claim

- Not a benchmark of the underlying models. It measures *this agent's*
  orchestration: tool routing, the loop, and the failover path.
- 30 questions is small. Differences of a few points are noise, and the
  numbers are reported as a characterisation of one system, not a ranking.
- Latency depends on free-tier queueing and will vary between runs.
