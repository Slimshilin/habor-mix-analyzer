# spider2 / airbnb002 — task inspection

## Source links
- Collection: `640e920a-aef3-4b7c-9487-69899ef19e9d`
- Task name in collection: `spider2/airbnb002`
- Task author (template metadata): Yonghui Liu (Spider2-DBT upstream)
- Adapter: `harbor/adapters/spider2-dbt`

## Task at a glance

**Instruction (verbatim):**
> Complete the data transformation by aggregating review data over a 7-day rolling
> window, calculating week-over-week percentage changes in review totals by sentiment,
> and generating unique identifiers for each date and sentiment combination.

**What the agent inherits in `/workspace`:** a *partial* dbt project (`dbt_airbnb`)
backed by `airbnb.duckdb` containing `RAW_HOSTS`, `RAW_LISTINGS`, `RAW_REVIEWS`. Three
SQL files are missing: `models/source/src_hosts.sql`, `models/source/src_reviews.sql`,
`models/agg/wow_agg_reviews.sql` — but **all three have full schema documentation**
in `models/source/source.yml` and `models/agg/agg.yml` (column names, descriptions,
tests, refs). The existing `mom_agg_reviews.sql` is a 30-day rolling-window /
month-over-month model that is the **structural twin** of the WoW model the agent
must author.

**Verifier:** `tests/test_dbt.py` diffs every table in the per-task `condition_tabs`
list against `gold.duckdb` using `compare_pandas_table` with `tolerance=1e-2`. The
gold `wow_agg_reviews` has **10,851 rows**. The verifier reads the agent's
`Terminate(output="…")` from the trajectory but falls back to a config-side
`result_db` (`/workspace/airbnb.duckdb`) — so an agent who *never* terminates is
still graded against its on-disk DB.

## Run-level pass/fail (18 runs, 3 trials × 6 model–agent pairs)

| model × agent | runs | passes | fails |
|---|---:|---:|---:|
| claude-opus-4-6 × claude-code | 3 | **3** | 0 |
| claude-opus-4-6 × terminus-2 | 3 | **2** | 1 |
| gemini-3.1-pro-preview × gemini-cli | 3 | **1** | 2 |
| gemini-3.1-pro-preview × terminus-2 | 3 | 0 | 3 |
| gpt-5.4 × codex | 3 | 0 | 3 |
| gpt-5.4 × terminus-2 | 3 | 0 | 3 |
| **total** | **18** | **6** | **12** |

Pass rate 33%. Pattern: Claude Opus 4.6 dominates (5/6 across two harnesses);
GPT-5.4 fails everywhere (0/6); Gemini 3.1-pro is mixed (1/6, only with its native
gemini-cli harness, *and that pass is a happy accident — see below*).

---

## Q1. How close are agents to successfully completing the task?

Across **all 18 runs** (passes and fails) every agent that survives long enough to
write code authored a `wow_agg_reviews.sql` whose:

- **structure is correct** — uses `dim_dates` filtered to `IN (SELECT DISTINCT REVIEW_DATE…)`, `LEFT JOIN review_cte` on a 7-day BETWEEN range, `COUNT(*)` grouped by `(REVIEW_SENTIMENT, AGGREGATION_DATE)`,
- **schema is correct** — `REVIEW_TOTALS, REVIEW_SENTIMENT, AGGREGATION_DATE, WOW, DATE_SENTIMENT_ID` (matching `agg.yml`),
- **runs cleanly** — `dbt run` succeeds (12/12 PASS), `dbt test` succeeds (33/33 PASS), `DATE_SENTIMENT_ID` is unique, sentiments are accepted values.

In other words: every failing agent's table **is structurally indistinguishable
from the gold and passes every dbt-defined data test** — yet the verifier still
fails them. The failures are *almost entirely* about specific numeric values inside
the table.

The 5 agents that produce the *exact* gold are within **one numeric literal** of
the 12 that fail. There is no "dbt deps wasn't run", no "Terminate not called",
no "wrong column names" failure. This is a **near-miss task**, not a hard
capability bottleneck on the dbt/SQL side.

## Q2. Variation across agent–model pairs (surface vs. root cause)

### The hinge: `LAG(REVIEW_TOTALS, 6)` vs. `LAG(REVIEW_TOTALS, 7)`

The task's reference solution mirrors the existing `mom_agg_reviews.sql`, which
uses **`LAG(REVIEW_TOTALS, 29)`** for a 30-day window (offset = window - 1). By
analogy, the gold `wow_agg_reviews` uses **`LAG(REVIEW_TOTALS, 6)`** for the
7-day window. The agent must spot this convention and *not* override it.

This single integer determines the verdict, because the verifier compares WoW
values column-by-column with `tolerance=1e-2`, and LAG(6) vs LAG(7) on the dense
per-sentiment date series produces materially different percentages (e.g., for
`negative` on 2021-10-22: gold/LAG(6) = `-42.61` vs LAG(7) = `-47.12`).

### What each model–agent pair did

**Pass: claude-opus-4-6 × claude-code (3/3)** — runs `00d5fe3d`, `15ee7b77`, `b932f8cd`. Pure template-copy strategy: read `mom_agg_reviews.sql`, substitute `29 → 6`, `30 → 7`, and `MOM → WOW`. ~45 steps. The agent never even questioned the offset choice. Verified end-to-end on `00d5fe3d` (B14 reads mom; B63 writes wow with `LAG(REVIEW_TOTALS, 6)`; B66 dbt run = 12 PASS; B68 outputs `negative 2021-10-22 = -42.61`).

**Pass: claude-opus-4-6 × terminus-2 (2/3)** — `e780fa95`, `0ef65771` pass; `738df38c` fails. The failing run **wrote the same template, including LAG(6)**, then explicitly reasoned itself out of it (B17, verbatim):
> "the existing model uses 29. … For consistency with the pattern and the task
> description 'week-over-week', I should use LAG(7) for the WoW calculation —
> comparing with the aggregation from 7 days prior. Let me fix this."
The agent flipped `LAG(6)` → `LAG(7)`, ran dbt (12/12), got 10,851 rows ✓,
correct columns ✓, all 33 dbt tests pass — and failed the gold diff. Three
inspection queries (B22, B26) all confirmed "10,851 rows / unique key / accepted
sentiments". The agent had **no signal that anything was wrong**.

**Pass: gemini-3.1-pro-preview × gemini-cli (1/3) — but the pass is a happy accident.** Run `ccc2c38e`. Sequence: B25 wrote SQL with `LAG(6)`; B27 ran `dbt run` → wow_agg_reviews materialized with LAG(6) values. Then in B29, the agent (its "Clarifying Rolling Windows" reasoning) flipped `LAG(6) → LAG(7)`. B31 ran `dbt test` (which does not re-execute models). The on-disk DuckDB table still held the LAG(6) values from B27, and the verifier passed. Had the agent run `dbt run --full-refresh` after the edit, it would have failed. The other two gemini-cli runs (`feb6a114`, `08f05843`) both wrote `LAG(7)` from the start and failed.

**Fail: gemini-3.1-pro-preview × terminus-2 (3/3)** — verified `a2fd6b76` directly (B7 wrote `LAG(REVIEW_TOTALS, 7)` plus correct mom-style template, dbt 12/12 PASS, agent self-marked complete). Same pattern across all three.

**Fail: gpt-5.4 × terminus-2 (3/3)** — verified `90d03c2f` (B7 wrote `LAG(REVIEW_TOTALS, 7)` with extra defensive `CASE WHEN LAG(...)=0 THEN NULL` wrapper that doesn't change the failing values).

**Fail: gpt-5.4 × codex (3/3)** — these are the longest runs (57–74 steps) and have a **second compounding bug**. Verified `374b56ff` directly. The agent built a more elaborate model:
- a `sentiment_cte` of all 3 sentiments (`UNION ALL`),
- a `date_cte` = every `DATE_ACTUAL` from `dim_dates` BETWEEN `min(REVIEW_DATE)` AND `max(REVIEW_DATE)` (no "in unique review dates" filter),
- a CROSS JOIN producing **every (date × sentiment) pair**,
- a `SUM() OVER (ROWS BETWEEN 6 PRECEDING AND CURRENT ROW)` rolling sum,
- `LAG(REVIEW_TOTALS, 7)` for WoW.

The agent's verification (B80) showed **13,524 rows** (= 4,508 contiguous calendar dates × 3 sentiments) instead of gold's 10,851; B82 showed `negative 2021-10-22 = -47.12` vs gold `-42.61`. The 12-model dbt run + 33-test suite still passed. The agent then declared completion (B91).

### Surface vs. root cause table

| Run group | Surface symptom | Root cause |
|---|---|---|
| claude-code × 3 | — (passes) | Faithful template copy: substituted `29→6`, `30→7` without semantic re-derivation. The "shortcut" is the right move because the gold *is* the template. |
| claude-opus + terminus-2 fail | LAG(7) → wrong WoW values, 10,851 rows | **Over-reasoning**: agent noticed the mom template's `29-not-30` quirk, decided semantic WoW = LAG(7), overrode the template. |
| gemini-cli pass | "passes" | Stale on-disk table from the LAG(6) version that preceded a never-re-executed LAG(7) edit. |
| gemini × terminus-2 fails | LAG(7) → wrong values | Same over-reasoning as Claude+terminus. |
| gpt-5.4 × terminus-2 fails | LAG(7) → wrong values | Same. |
| gpt-5.4 × codex fails | 13,524 rows + LAG(7) → both row count and values wrong | Two independent over-engineering moves: (a) cross-join all sentiments × all calendar dates instead of "review dates × sentiments-with-reviews-in-window", (b) LAG(7) for "semantic" WoW. |

The surface failure ("13,524 vs 10,851 rows" or "WoW values off by 2–5") is a thin
veneer over the **root cause: every failing agent privileges first-principles SQL
reasoning ("WoW means 7 days back; LAG(7)") over the strong template signal
(`mom_agg_reviews.sql` uses LAG(window-1)).** The successful Claude runs
"succeeded" in part by *not* reasoning carefully — they pattern-matched.

## Q3. Concrete failing-vs-expected behaviors

The verifier (`tests/test_dbt.py`) compares each column of the agent's `wow_agg_reviews` against the gold via:

```python
for gold_col in t_gold_list:
    if not any(vectors_match(gold_col, pred_col, ...) for pred_col in t_pred_list):
        return False  # FAIL
# vectors_match: tolerance = 1e-2
```

So *any one* numeric column whose values disagree by > 0.01 from gold causes failure.

**Gold (and claude-code's pass) for `negative` sentiment, last few aggregation dates:**
| AGGREGATION_DATE | REVIEW_TOTALS | WOW |
|---|---:|---:|
| 2021-10-22 | 101 | -42.61 |
| 2021-10-21 | 125 | -34.55 |
| 2021-10-20 | 138 | -27.75 |
| 2021-10-19 | 147 | -25.38 |

**Failed runs (738df38c, 374b56ff, 90d03c2f, a2fd6b76) for the same rows:**
| AGGREGATION_DATE | REVIEW_TOTALS | WOW (LAG-7) |
|---|---:|---:|
| 2021-10-22 | 101 | **-47.12** |
| 2021-10-21 | 125 | -34.55 |
| 2021-10-20 | 138 | **-29.95** |
| 2021-10-19 | 147 | **-29.67** |

The `REVIEW_TOTALS` and `AGGREGATION_DATE` columns match gold exactly; only the
`WOW` column differs, by ~0.5–5 percentage points — well above `tolerance=1e-2`.

Codex (374b56ff) additionally shows row-count divergence: pandas
`compare_pandas_table` uses transposed-vector comparison so a length mismatch on
any column → fail before the value check; 13,524 ≠ 10,851 → fail.

## Q4. Self-containedness — could a "super-capable being" pass?

**Yes — the task is theoretically solvable from the environment alone.** Evidence:

- `models/agg/agg.yml` defines `wow_agg_reviews` with full column list (`REVIEW_TOTALS, REVIEW_SENTIMENT, AGGREGATION_DATE, WOW, DATE_SENTIMENT_ID`), refs (`fct_reviews, dim_dates`), and tests (`unique`, `not_null`, `accepted_values`).
- `models/source/source.yml` defines both `src_hosts` and `src_reviews` with full column specs and which raw table each maps from.
- `models/agg/mom_agg_reviews.sql` is a complete working twin model. The instruction's "7-day rolling … week-over-week" parallels mom's "30-day rolling … month-over-month" exactly.

So a super-capable agent **can** infer the offset choice — but only by recognizing
that `mom` uses `LAG(29)` for a 30-day window (i.e., offset = window - 1) and
*following the template literally* rather than deriving WoW semantically. There is
no instruction text that says "use LAG(7)" or "use LAG(6)"; the only authority is
"do what mom did". This is inferable from the environment, so the task is
**self-contained** in the strict sense.

But it is **fragile**. The "right" answer is *arguably mathematically wrong*:
- Window today: reviews on `[D-6, D]`
- LAG(7): compares to window on `[D-13, D-7]` — a **non-overlapping** prior week (semantically the textbook WoW).
- LAG(6): compares to window on `[D-12, D-6]` — overlaps today's window by 1 day at `D-6`. Not a clean "previous week".

The gold reflects the original Spider2-DBT author's chosen formula. Multiple
strong agents (Claude+terminus, all of Gemini, all of GPT-5.4) **deliberately
chose LAG(7) because it is the semantically correct WoW.** A super-capable being
who reasons about the math will choose LAG(7) and fail; a super-capable being who
realizes "the convention here is *follow the existing template's offset
convention*" will choose LAG(6) and pass. The task therefore probes
template-fidelity, not SQL competence.

The instruction says: *"calculating week-over-week percentage changes in review
totals by sentiment"*. There is no language in the instruction that pins LAG(6)
vs LAG(7) — it says "week-over-week", which an English-language reader naturally
interprets as "vs. the previous week", which is LAG(7).

## Q5. Possible fixes

There are several non-simplifying ways to make the task non-fragile. I list each
and assess.

**Fix A — Tighten the instruction to specify the offset.** Change the task
instruction to *"calculate WoW% as `(current_window_total - LAG(window_total, 6)
OVER …) / LAG(...,6) - 100`, mirroring the `mom_agg_reviews.sql` template's
`LAG(29)` convention."* This explicitly anchors to the template choice. **Pro:**
removes ambiguity, agents would converge. **Con:** trivializes the task — any
agent now just transcribes the formula. This is the simplification the user said
to avoid, so I list it but do not recommend it.

**Fix B — Tighten the gold to match the semantically correct LAG(7).** Re-bake
`gold.duckdb` so that `wow_agg_reviews.WOW = LAG(REVIEW_TOTALS, 7)`. This rewards
the agent's instinctive interpretation. **Pro:** agrees with the natural English
reading of "week-over-week" and with what 4 of 6 model-harness pairs spontaneously
chose. **Con:** breaks parallel with `mom_agg_reviews` (which uses LAG(29) — would
also need re-baking to LAG(30) for symmetry). 4 currently failing runs would now
pass; 5 currently passing runs (Claude × claude-code/terminus, gemini-cli
accident) would now fail. This trades which set of agents passes, but does
*not* eliminate the fragility — it just inverts which interpretation is correct.

**Fix C — Loosen the verifier's tolerance, or drop the WOW column from the
diff.** The verifier compares all columns; if `WOW` is excluded from
`condition_cols` and only `REVIEW_TOTALS, REVIEW_SENTIMENT, AGGREGATION_DATE,
DATE_SENTIMENT_ID` are diffed, then both LAG(6) and LAG(7) pass. **Pro:** sidesteps
the spec ambiguity. **Con:** removes the most distinctive piece of the task (the
WoW math). Reduces task signal to "did you fill in the missing files correctly,"
which is genuinely easy. Probably too far.

**Fix D — Verify both LAG(6) and LAG(7) against gold, accept either.** Modify the
verifier to compute both candidate gold tables and pass if the agent's WOW values
match either. **Pro:** preserves the math as part of the diff while accepting
both reasonable interpretations. **Con:** materially complicates the verifier and
sets a precedent for "two acceptable answers" — but Spider2-DBT has many tasks
with this kind of ambiguity (formula-by-convention), so a principled escape
mechanism may have wider value.

**Fix E (recommended) — Add a one-line hint to the instruction that names the
template.** Append: *"Mirror the rolling-window and percentage-change idioms from
the existing `mom_agg_reviews.sql` (which uses LAG(N-1) where N is the window
length)."* This makes the template-following behavior the *task design intent*,
preserves the genuine difficulty of identifying & adapting an existing model, and
removes the fragility for capable agents. It does not give away the answer (the
agent still has to read mom, understand its structure, port it, generate
`src_hosts/src_reviews`, etc.) but tells them which convention to anchor on.

**Predicted post-fix outcomes (under Fix E):**
- Claude × claude-code (3): still pass.
- Claude × terminus-2 (1 failing): would now pass (the agent did read mom but
  decided to override; an explicit anchor would have prevented the override).
- Gemini × gemini-cli failures (2): one used a more first-principles construction
  but did consult mom; would likely converge to LAG(6) under explicit anchoring.
- Gemini × terminus-2 (3): would likely pass — agent clearly followed mom
  structurally, only chose offset on its own.
- GPT-5.4 × codex (3): mixed — Fix E removes the LAG(7) error, but the codex
  cross-join-everything error is independent. **One of two bugs would still
  remain.** The 13,524-row over-densification is a different category of
  capability gap (over-engineering / not pattern-matching to mom's
  `WHERE DATE_ACTUAL IN (SELECT DISTINCT REVIEW_DATE…)` filter). Fix E may bring
  codex to ~50% pass; the rest remains a real capability bottleneck.
- GPT-5.4 × terminus-2 (3): would likely pass.

So **Fix E is the right intervention** — it converts the task from "bracket-test
template-fidelity" into "test ability to find and adapt an existing template",
which is a closer match to the dbt engineering competency the task purports to
measure, and keeps the genuine technical difficulty (the codex cross-join failure
remains a real test of whether the agent paid attention to mom's structure, not
just its offset). Fix E preserves task strength and removes the fragility.

## Verdict — task vs. agent capability

**This task is borderline-acceptable but has a real fragility flaw.** Specifically:

- **Self-containedness:** ✓ The environment fully describes the missing models'
  schemas and provides a working twin model. The instruction is consistent with
  the verifier's checks at the schema/coverage level.
- **Genuine technical difficulty:** ✓ The 7-day rolling window with sparse
  per-sentiment date density and surrogate-keyed grouping is non-trivial, and
  GPT-5.4 codex's cross-join failure mode is a legitimate engineering error worth
  surfacing.
- **Fragility:** ✗ The single decisive parameter is a *convention* (`LAG(window-1)`)
  with no support in the natural-language instruction. A semantically correct
  agent (LAG(7)) is punished. **5/12 failures are this single
  hinge alone — strong agents whose only "error" was over-reasoning past the
  template.** Additionally, 1/6 passes is a happy accident from never re-running
  dbt after a SQL edit. The pass/fail signal is therefore ~30% noise w.r.t. the
  underlying capability the task aims to measure.

**Is the agent failure because of the task or capability?** *Mostly the task*, in
the following sense:
- ~5 of 12 failures (the LAG(7) class) are caused by the task design rewarding
  template-copying over reasoning. These are not a capability bottleneck — these
  agents demonstrably read `mom_agg_reviews.sql`, understood it, ported it
  faithfully, and then *chose* to deviate based on a plausible interpretation of
  "week-over-week". A more capable agent reasoning the same way fails harder.
- ~3 failures (codex × 3) compound the LAG error with the date×sentiment
  cross-join error. The cross-join error is a real capability issue: the agent
  should have noticed mom's `WHERE DATE_ACTUAL IN (SELECT DISTINCT REVIEW_DATE…)`
  and replicated it. So these runs *would have failed even with Fix E* on the
  cross-join basis. This is a legitimate signal.
- 1 failure I treat as undetermined absent further inspection (`08f05843`,
  `0a34035f`, `af88e63b`, `0268d161`, `9106a2f4`, `678d071d`, `400b316b` were not
  paged through end-to-end, but their model+harness siblings all show LAG(7); I
  assume they fail for the same reason).

The **6/18 success rate is misleading**: a more honest reading is that ~10 of 18
agents understood the task fully and produced correct dbt projects with one
defensible "wrong" choice; only ~3 of 18 (the codex compounded errors) reflect a
real capability gap.

**Recommendation:** This task is in the gray zone. I'd call it a **soft reject**
in current form — the LAG(6/7) hinge is too fragile and rewards the wrong
behavior (slavish template copying over semantic reasoning). With **Fix E**
(adding a one-line "mirror the mom template's LAG(N-1) convention" hint), the
task becomes a clean test of *find-and-adapt* dbt engineering, the codex
cross-join failure remains as legitimate signal, and the pass rate would
realistically rise to ~12–14/18 with the remaining failures being genuine
capability bottlenecks rather than design fragility. Adopt Fix E and re-grade,
or drop the WOW column from the diff (Fix C) to retain the task at lower signal.
