# Task Inspection: dacode / dacode-plot-line-013

**Benchmark:** dacode  
**Task ID:** dacode-plot-line-013  
**Task Checksum:** fe9355e698d91249761bee6958d542dd223aa1658eca1717c1707d4bd3dae798  
**Score:** 1/18  
**Gemini Audit:** accept  
**Analyst:** Claude Sonnet 4.6 (initial), Claude Opus 4.7 (re-verification)  
**Date:** 2026-05-01  

---

## Task Description

**Instruction (verbatim from metadata):**
> All input files are under `/app`. Save your output file(s) under `/app/output`.
>
> Calculate a 30-day moving average of orders by store, and then visually represent this data using a line plot. Save the resulting plot as result.jpg with a size of (10,4). The title of the plot should be "30-Day Moving Average of Orders", and the legend title should be "store_id".
> Save the code to produce the plot in `/app/output/plot.py`.

**Environment:** `/app` contains `orders.csv` (1615 orders from 2016-01-01 to 2018-12-28, schema: `order_id, customer_id, order_status, order_date, required_date, shipped_date, store_id, staff_id`), plus several other CSV files (`stores.csv`, `order_items.csv`, `products.csv`, etc.)

**Verifier:** Extracts plot metadata and data from generated `plot.py`, compares to gold `result.npy` / `result.jpg` / `plot.json`. Reports:
```
Result = {'img': bool, 'data': bool, 'scale_data': bool, 'figsize': bool, 'graph_title': bool, 'legend_title': bool, 'score': float}
```
Verifier options: `keys: ['figsize', 'graph_title', 'legend_title'], hardness: 'Medium'`

---

## Verdict

**REJECT.** Three independent quality issues compound to make this task untrustworthy:

1. **Verifier scoring flaw.** Full score (1.0) is awarded based on `scale_data=True` alone, even though the successful run also reports `img=False` and `data=False` — i.e., neither the image nor the exact data array matches the gold. The verifier uses a lenient `(img OR data OR scale_data) AND keys_match` formula, which means scoring confirms only that values fall in approximately the right shape/range, not that the agent actually produced the correct moving average.

2. **Instruction ambiguity rewards naive code.** "30-day moving average of orders by store" doesn't specify whether missing calendar days should be treated as zero. The gold uses 30-observation rolling on the sparse order-day series — which is the literal "first thing you'd type" without thinking about gaps. The 6 GPT-5.4 runs explicitly noticed the calendar gaps and zero-filled them (the more standard, more thoughtful approach for "30-day moving average"), and were penalized for it. The task systematically rewards less careful reasoning.

3. **Audit error.** The Gemini auditor's published rationale for accepting this task — that "the successful trial explicitly created a `pd.date_range` and reindexed the data to ensure 0-order days were included" — is factually wrong. The successful trial did the OPPOSITE. The auditor described the approach used by every failing GPT-5.4 run as the one that succeeded. Whatever reasoning underlay the accept verdict cannot be relied on.

---

## Final Answer: Task vs. Agent Bottleneck

**The failure is PRIMARILY a task quality problem for the wrong-scale failures (6/17 failing runs), and partially an agent capability issue for the NaN failures (11/17 failing runs).**

- **11 failing runs**: NaN issue from missing `min_periods=1` — this IS a real agent shortcoming, but easily fixed and not the interesting part.
- **6 failing runs (all gpt-5.4)**: Implemented a mathematically more rigorous approach (standard calendar-day zero-filling), yet failed because the gold uses a non-standard interpretation. This is primarily a **task quality problem**.
- **1 successful run**: "Succeeded" by accident — the agent did NOT reindex to the full calendar, happened to use `min_periods=1`, and the resulting sparse-data rolling average matched the gold's scale range. But even this run has `data: False` and `img: False`.

---

## Section 1: How Close Were Agents to Completing the Task?

**Very close on metadata checks; diverged critically on data computation.**

All 18 runs correctly:
- Read `orders.csv` and identified the relevant columns
- Set `figsize=(10,4)` → `figsize: True` for all runs
- Set title "30-Day Moving Average of Orders" → `graph_title: True` for all runs
- Set legend title "store_id" → `legend_title: True` for all runs

The singular discriminator was `scale_data`: True (score=1.0) vs False (score=0.0).

| Failure Pattern | Runs | Root Cause |
|---|---|---|
| NaN in matrix (first 29 rows) | 11 | `rolling(window=30)` without `min_periods=1` on zero-filled data |
| Wrong scale (0–1.5 range vs gold 0.8–2.4) | 6 | `rolling(window=30, min_periods=1)` WITH zero-fill |
| Exact data mismatch (but scale OK) | 1 (successful run) | Approach matches gold scale by accident; `data: False` |

---

## Section 2: How Agent-Model Performances Vary

### Run-by-run table

| Agent Run ID | Model | Agent | Reward | Matrix Shape | NaN? | scale_data | Notes |
|---|---|---|---|---|---|---|---|
| **43d88d74** | claude-opus-4-6 | claude-code | **1.0** | **(3, 623)** | No | **True** | No zero-fill; rolling(30, min_periods=1) on sparse data |
| f784779b | claude-opus-4-6 | claude-code | 0.0 | (3, 1074) | Yes | False | asfreq("D") + rolling(30), no min_periods |
| ff771200 | claude-opus-4-6 | claude-code | 0.0 | (3, 1093) | Yes | False | reindex + rolling(30), no min_periods |
| 472efc04 | claude-opus-4-6 | terminus-2 | 0.0 | (3, 1093) | Yes | False | pivot + reindex + rolling(30), no min_periods |
| 5479cd6f | claude-opus-4-6 | terminus-2 | 0.0 | (3, 1093) | Yes | False | per-store loop + rolling(30), no min_periods |
| 67b83ea5 | claude-opus-4-6 | terminus-2 | 0.0 | (3, 1093) | Yes | False | pivot + reindex + rolling(30), no min_periods |
| 69311873 | gpt-5.4 | codex | 0.0 | (3, 1093) | No | False | reindex + rolling(30, min_periods=1), values 0–2 |
| 8a6c7e94 | gpt-5.4 | terminus-2 | 0.0 | (3, 1093) | No | False | same as codex pattern |
| b2e80292 | gpt-5.4 | terminus-2 | 0.0 | (3, 1093) | No | False | same as codex pattern |
| d632d1d9 | gpt-5.4 | terminus-2 | 0.0 | (3, 1093) | No | False | same as codex pattern |
| b2ed399d | gpt-5.4 | codex | 0.0 | (3, 1093) | No | False | same as codex pattern |
| e2c6d207 | gpt-5.4 | codex | 0.0 | (3, 1074) | No | False | same, per-store date range |
| 32ba0bc0 | gemini-3.1-pro | terminus-2 | 0.0 | (3, 1093) | Yes | False | pivot + reindex + rolling(30), no min_periods |
| 8294c287 | gemini-3.1-pro | terminus-2 | 0.0 | (3, 1093) | Yes | False | unstack + reindex + rolling(30), no min_periods |
| b18f1dc9 | gemini-3.1-pro | terminus-2 | 0.0 | (3, 1093) | Yes | False | pivot + reindex + rolling(30), no min_periods |
| 4bbb6330 | gemini-3.1-pro | gemini-cli | 0.0 | (3, 1093) | Yes | False | resample('D') + rolling(30), no min_periods |
| 4cf406ee | gemini-3.1-pro | gemini-cli | 0.0 | (3, 1093) | Yes | False | pivot + reindex + rolling(30), no min_periods |
| 040f9fa6 | gemini-3.1-pro | gemini-cli | 0.0 | (3, 1093) | Yes | False | pivot + reindex + rolling(30), no min_periods |

### Model-level patterns

- **GPT-5.4 (all 6 runs)**: Universally used `min_periods=1` AND `fill_value=0` reindexing — the most mathematically careful approach. All 6 uniformly failed because the zero-fill produces values in the 0–1.5 range vs gold's 0.8–2.4 range. GPT-5.4 was the most internally consistent model, all runs producing nearly identical code and identical output sizes. The 3 terminus-2 runs are literally the same code.

- **Gemini (all 6 runs)**: Universally forgot `min_periods=1`. All used reindexing + `rolling(window=30)`. NaN in first 29 rows. Some used `plot.rolling()` directly on a pivot table; others grouped per-store. All produced matrix shape (3, 1093) with NaN leading rows.

- **Claude-opus (terminus-2, 3 runs)**: Behaved like Gemini — used reindexing + `rolling(window=30)` without `min_periods`, producing NaN.

- **Claude-opus (claude-code, 3 runs)**: One unique success. The successful run happened to skip reindexing and use `min_periods=1`. The two failing runs used reindexing with no `min_periods` (NaN).

### Surface reason vs. root cause

**Surface reason:** Agents either produced NaN values (incomplete rolling window) or produced y-values in the wrong scale range.

**Root cause (NaN failures):** Agents understood the need to fill in missing calendar dates (correct reasoning) but used `rolling(window=30)` with default `min_periods=30`, causing NaN for the first 29 rows. This is a minor pandas API knowledge gap — a capable agent should know to set `min_periods=1` or drop NaNs. However, this is NOT the fundamental reason the task has 1/18 success rate, because the 6 gpt-5.4 runs correctly used `min_periods=1` and STILL failed.

**Root cause (wrong-scale failures):** Agents (GPT-5.4) implemented the textbook-correct approach: zero-fill missing calendar days → compute 30-day rolling average. This correctly computes "average daily orders over a 30-calendar-day window." But the gold data uses a different approach: compute rolling average on ONLY the observed order days (no zero-filling), which gives DIFFERENT y-values in a DIFFERENT scale (0.8–2.4 vs 0–1.5). The root cause is **task ambiguity / gold standard mismatch**, not agent capability failure.

---

## Section 3: Concrete Agent Behaviors vs. Verifier

### The passing approach (43d88d74)

```python
# Aggregates to daily counts on SPARSE data (no zero-fill)
daily_orders = orders.groupby(["store_id", "order_date"]).size().reset_index(name="order_count")
daily_orders = daily_orders.sort_values(["store_id", "order_date"])

# Rolling window on SPARSE data — only order-days in the window
daily_orders["moving_avg"] = (
    daily_orders.groupby("store_id")["order_count"]
    .transform(lambda x: x.rolling(window=30, min_periods=1).mean())
)
```

**Effect:** A store with ~200 order-days across 1093 calendar days averages the last 30 ORDER DAYS (not 30 calendar days). With ~2.5 orders per active day, the rolling average is 2–2.5 → y-range 0.8–2.4 (matching gold scale). `scale_data=True`. Score=1.0.

### The failing approach — NaN category (example: 472efc04)

```python
# Correct aggregation
pivot = order_counts.pivot_table(index='order_date', columns='store_id', values='order_count', fill_value=0)

# CORRECT: Fills missing calendar days with 0
date_range = pd.date_range(start=pivot.index.min(), end=pivot.index.max(), freq='D')
pivot = pivot.reindex(date_range, fill_value=0)

# WRONG: No min_periods → NaN for first 29 rows
moving_avg = pivot.rolling(window=30).mean()
```

**Effect:** The reindexed DataFrame has 1093 rows (one per calendar day). `rolling(window=30)` with default `min_periods=30` produces NaN for days 1–29 of each store. The verifier's extracted matrix is shape (3, 1093) with NaN values. `scale_data=False`. Score=0.0.

**What the test checks:**
The verifier runs `plot_process.py` which re-executes the agent's `plot.py`, extracts line data from the matplotlib figure, and compares the (3, N) array to the gold `result.npy`. NaN values fail the scale comparison outright.

### The failing approach — wrong scale (example: 69311873/gpt-5.4/codex)

```python
# Correct aggregation
daily_orders = orders.groupby(["store_id", "order_date"]).size().rename("orders").reset_index()

# Fills EVERY calendar day (even zero-order days) with 0
date_range = pd.date_range(daily_orders["order_date"].min(), daily_orders["order_date"].max(), freq="D")
# [reindex to full date range with fill_value=0]

# Rolling with min_periods=1 — no NaN
moving_avg = daily_orders.groupby("store_id")["orders"].transform(
    lambda series: series.rolling(window=30, min_periods=1).mean()
)
```

**Effect:** With zero-filled calendar (1093 days), most days have 0 orders. A 30-day window averages ~6 active days × ~2 orders + 24 zero days / 30 = ~0.4–0.5 orders/day. Values range 0–2 (mostly 0–1). Gold expects 0.8–2.4. `scale_data=False`. Score=0.0.

**Verifier data comparison:**
- Gold ytick range (from successful run): `['0.8', '1.0', '1.2', '1.4', '1.6', '1.8', '2.0', '2.2', '2.4']`
- Failing gpt-5.4 ytick range: `['−0.25', '0.00', '0.25', '0.50', '0.75', '1.00', '1.25', '1.50', '1.75', '2.00', '2.25']`

These are fundamentally different scales from the same data, showing the two approaches are not equivalent.

---

## Section 4: Task Quality Analysis

### 4a. What the verifier actually checks

The verifier report for the successful run:
```
Result = {'img': False, 'data': False, 'scale_data': True, 'figsize': True, 'graph_title': True, 'legend_title': True, 'score': 1.0}
```

**Critical observation: `img=False` and `data=False` yet `score=1.0`.** The verifier awards full credit based solely on `scale_data=True`. The likely scoring formula (consistent with DABench convention) is:

```
score = 1.0  iff  (img OR data OR scale_data) AND all_listed_keys_True
```

This is a deliberately lenient OR-of-correctness-checks design — meant to accommodate slight numerical differences (different scales, slight rounding, color palette differences) while still rewarding correct work. The intent is reasonable, but the consequence in this task is severe:

- `img=False` for the successful run: pixel-level image comparison fails.
- `data=False` for the successful run: exact data comparison fails.
- `scale_data=True` for the successful run: shape/scale-normalized comparison passes.

**The score does not actually confirm the agent computed the correct moving average.** It confirms only that the curve shape, after normalization, is similar to the gold. Whether `scale_data` checks "values within an expected y-range" or "shapes match after min-max normalization," it cannot distinguish the gold's sparse-rolling approach from any other approach that happens to produce a shape with comparable peaks/valleys at comparable positions. A coincidentally similar curve could pass; a differently-computed-but-shape-different curve cannot.

The deeper issue: when `scale_data` is the ONLY True correctness check, the verifier is implicitly telling us the agent did something different from the gold. Treating that as a perfect score (1.0, identical to a hypothetical run where all three checks passed) is misleading both for benchmarking and for downstream analysis like HaborMix selection.

### 4b. The "30-day moving average" ambiguity

The instruction says: "Calculate a 30-day moving average of orders by store."

**Standard data science interpretation:**
- Count orders per store per calendar day (including zero-order days = 0)
- Compute rolling average over a 30-calendar-day window
- This is a "30-calendar-day moving average of daily order volume"

**What the gold data implements:**
- Count orders per store per order-day (only days with orders)
- Apply `rolling(window=30, min_periods=1)` on the sparse series
- This is a "30-observation moving average" where each observation is an order-day
- The window covers a variable calendar span (~60–150 days) depending on order frequency

These two computations produce **fundamentally different numerical results** on the same data:
- Standard approach: ~0.4–0.7 orders/calendar-day
- Gold approach: ~1.0–2.5 orders/order-day

The instruction gives no basis for an agent to know which interpretation is expected. An agent who notices there are calendar gaps in the data (as all 6 gpt-5.4 agents did) and carefully handles them produces the MORE STANDARD answer — and fails.

**Worth emphasizing the inversion:** the gold's approach is NOT a sophisticated alternative interpretation — it's the literal "first thing you'd type" without thinking about gaps:

```python
orders.groupby(['store_id', 'order_date']).size().groupby('store_id').rolling(30, min_periods=1).mean()
```

That single line IS the gold approach. The 6 GPT-5.4 agents wrote ~15 additional lines of code to handle the calendar gap problem — and the verifier punished them for thinking. This is the inverse of what a well-designed benchmark should reward. The Gemini auditor's framing of the 1/18 success rate as "high ceiling for reasoning" inverts cause and effect: the rate isn't high because reasoning is hard, it's high because reasoning is penalized.

### 4c. Can an agent infer the correct approach from the environment?

**No.** There is nothing in:
- The instruction text (doesn't specify zero-fill vs sparse)
- `orders.csv` structure (looks like standard time series data)
- `README.md` in `/app` (not inspected by most agents, and reportedly doesn't specify computation method)
- Any other file in the environment

that tells an agent whether to zero-fill missing calendar days. The gold's approach (30-row rolling on sparse data) is actually the LESS obvious interpretation; the standard approach (fill zeros + calendar rolling) is more natural for "30-day" phrasing.

### 4d. Is the task theoretically self-contained and achievable?

**Technically yes** — a very capable agent who happens to apply `rolling(window=30, min_periods=1)` on un-zero-filled daily order counts will pass. But this passes for the WRONG reason: because it produces values in the right scale range, not because it computes the exact gold answer (which even the successful run doesn't, with `data: False`).

A "super capable being" analyzing the task would likely argue for the standard calendar-day approach (zero-fill) as more statistically correct — and fail. The task is theoretically solvable only by someone who:
1. Happens to use the non-standard sparse-data approach, AND
2. Uses `min_periods=1` to avoid NaN, AND
3. The resulting y-values fall in the scale range the verifier accepts

This combination requires luck as much as capability. Notably, the same model (claude-opus-4-6) running through claude-code succeeded once and failed twice on this exact task — and the SUCCESSFUL run wasn't the most thorough one. It was the one that did the simplest thing.

### 4e. Gemini audit error

The Gemini auditor stated:
> "The successful trial (a0c6dbbc) explicitly created a `pd.date_range` and reindexed the data to ensure 0-order days were included."

**This is factually incorrect.** The successful run's actual code (verified from transcript):
```python
daily_orders = orders.groupby(["store_id", "order_date"]).size().reset_index(name="order_count")
daily_orders = daily_orders.sort_values(["store_id", "order_date"])
daily_orders["moving_avg"] = (
    daily_orders.groupby("store_id")["order_count"]
    .transform(lambda x: x.rolling(window=30, min_periods=1).mean())
)
```

**No `pd.date_range`. No `reindex`. No zero-fill for missing calendar days.**

The auditor described exactly the approach that FAILS (which all 6 gpt-5.4 agents used). The actual successful approach is the OPPOSITE: work on sparse order-days only. The auditor's error suggests the audit was superficial and relied on the verifier output interpretation rather than inspecting the actual agent trajectory.

---

## Section 5: Proposed Fixes

### Problem 1: Instruction ambiguity about zero-filling

**Option A (instruction fix):** Add explicit guidance:
> "Note: Some dates in `orders.csv` may have no orders for certain stores. For the purposes of this moving average, treat days with no orders as having an order count of 0, and compute the 30-day moving average over all calendar days."

→ This would align the task with the standard interpretation. The gold data would then need to be regenerated using the zero-fill approach. Most failing agents would then pass.

**Option B (alternative instruction fix):** Add explicit guidance in the OTHER direction:
> "Note: Compute the moving average using only the dates present in the data (do not add rows for missing dates)."

→ This makes the non-standard approach explicit. Agents wouldn't need to guess. The gold data would remain as-is.

**Recommendation:** Option A is preferred, as it aligns with the standard "30-day moving average" interpretation and rewards the more thoughtful agents (GPT-5.4) who correctly handled calendar gaps.

### Problem 2: Scoring based on scale_data alone

The verifier currently gives score=1.0 when `scale_data=True`, even when `data=False` (exact values don't match). This should be tightened:
- Either require `data=True` as well (exact match), OR
- Accept the current scale-based scoring but acknowledge it doesn't test exact computation

If Option A's instruction fix is applied AND the gold is regenerated with zero-fill approach, the scale_data check would discriminate correctly. With zero-fill, the successful approach and the gold would be on the same scale, and `data=True` would be achievable.

### Problem 3: min_periods=1 as hidden requirement

Even if the instruction is fixed per Option A, agents using `rolling(window=30).mean()` without `min_periods=1` will produce NaN for the first 29 rows. This IS a legitimate test of pandas proficiency. However, the instruction could optionally hint: "Ensure your moving average values are defined from the start of the time series."

### Conclusion on fixes

The most complete fix involves:
1. Clarifying the instruction to specify that missing dates should be filled with 0
2. Regenerating the gold data using the standard approach (fill_value=0 + rolling(30, min_periods=1) or rolling('30D'))
3. Updating the verifier to check `data=True` (or at minimum, use a tighter scale tolerance)

With these fixes, the task becomes genuinely discriminating: agents that know to zero-fill AND use min_periods=1 will succeed; agents that skip either step will fail. The failure would then be attributable to agent capability (pandas time series knowledge) rather than task ambiguity.

---

## Appendix: Agent Code Patterns Across All 18 Runs

### Pattern 1: Sparse rolling (successful — 1 run)
```python
# No reindexing, rolling on sparse order-day data
daily_orders = orders.groupby(["store_id", "order_date"]).size().reset_index(name="order_count")
daily_orders["moving_avg"] = (
    daily_orders.groupby("store_id")["order_count"]
    .transform(lambda x: x.rolling(window=30, min_periods=1).mean())
)
```
Result: y-range 0.8–2.4, scale_data=True, score=1.0 ✓

### Pattern 2: Zero-fill + NaN (11 failing runs — all gemini, claude-terminus)
```python
# Reindex to full calendar, but NO min_periods
pivot = pivot.reindex(date_range, fill_value=0)
moving_avg = pivot.rolling(window=30).mean()  # ← NaN for first 29 rows
```
Result: (3, 1093) matrix with NaN, scale_data=False, score=0.0 ✗

### Pattern 3: Zero-fill + min_periods=1 (6 failing runs — all gpt-5.4)
```python
# Reindex to full calendar, with min_periods=1 to avoid NaN
pivot = pivot.reindex(date_range, fill_value=0)
moving_avg = pivot.rolling(window=30, min_periods=1).mean()  # ← values 0–1.5
```
Result: (3, 1093) matrix with values 0–2 (mostly 0–1), scale_data=False, score=0.0 ✗

---

*Analysis based on inspection of all 18 agent run trajectories from the Docent collection (640e920a-aef3-4b7c-9487-69899ef19e9d).*
