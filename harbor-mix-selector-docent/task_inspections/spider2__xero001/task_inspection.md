# Task Inspection: spider2 / xero001

**Status: in-progress** — populated as I iterate.

## 1. Task at a glance

| | |
|---|---|
| Benchmark / Task | `spider2` / `xero001` (Spider2-DBT subset) |
| Author | Yonghui Liu (Yonghui.Liu@anu.edu.au) |
| Difficulty | medium |
| Tags | dbt, duckdb, data-engineering, sql |
| Result | **0/18 (0% success)** |
| Gemini verdict | accept (with hand-wavy reasoning — see §6) |
| Docent collection | `640e920a-aef3-4b7c-9487-69899ef19e9d` |
| Agent timeout | 1800s |
| Verifier timeout | 600s |
| Source dataset | `huggingface.co/datasets/harborframework/harbor-datasets`, commit `45653d98` |

## 2. Trial roster (NOT 16 — actually 18)

The original brief listed 16 docent links; the collection actually contains **18 trials**.
The two missing from the brief are both `claude-code` + `claude-opus-4-6` runs (`3ae6795b…`, `712c2d01…`).
**Gemini's audit cited trajectory `565646a0-293e-46d7-a601-8621f5b69ab5` as a key piece of evidence — that ID does not exist in the docent collection.** I treat this as a fabricated citation; it weakens the audit's trustworthiness.

| Model | Agent | Run IDs | Steps |
|---|---|---|---|
| `claude-opus-4-6` | `claude-code` | 10da9d48, 3ae6795b, 712c2d01 | 46, 39, 46 |
| `anthropic/claude-opus-4-6` | `terminus-2` | 17702052, 579643bf, b0c4d4c6 | (NULL) |
| `gemini-3.1-pro-preview` | `gemini-cli` | 5bf93989, 8fce35d4, de0c0859 | 48, 27, 43 |
| `gemini/gemini-3.1-pro-preview` | `terminus-2` | 3fc24969, b7fbaf69, e28edee4 | (NULL) |
| `gpt-5.4` | `codex` | 2911c857, 59e1c4dc, b47330cb | 52, 42, 98 |
| `openai/gpt-5.4` | `terminus-2` | 82fbdf59, 878e666c, ab86a4a1 | (NULL) |

All 18 finished without exceptions and received `reward=0.0`. No timeouts, no infra errors. Failures are purely "wrong answer".

## 3. Instruction (verbatim)

The complete user-facing instruction the agent receives is **27 lines**, of which the *task-specific* part is exactly one sentence:

> "Create a balance sheet report that represents the balance sheet state for each account on a monthly basis."

The remaining lines are boilerplate about dbt / duckdb / `/workspace`, identical to every other spider2-dbt task.

## 4. Environment

- Docker: `python:3.11-slim` + `dbt-duckdb>=1.7.0` + `duckdb>=0.9.0` + pandas
- `/workspace` is a pre-loaded dbt project:
  - `dbt_project.yml` (profile `xero`, schema `main`, materialized `table`, declares `xero__using_bank_transaction=true`, `xero__using_credit_note=true`, plus 9 source-data identifiers and 9 staging-table refs as vars)
  - `profiles.yml` (DuckDB, path `./xero.duckdb`)
  - `xero.duckdb` — source DB. Tables present: 9 raw `xero_*_data` source tables (account, bank_transaction, contact, credit_note, invoice, invoice_line_item, journal, journal_line, organization).
  - `models/`:
    - `xero__general_ledger.sql` (already provided — joins journals × journal_lines × accounts + extras)
    - `xero__invoice_line_items.sql` (already provided)
    - `xero__profit_and_loss_report.sql` (already provided — useful template; aggregates REVENUE/EXPENSE × calendar)
    - `utilities/xero__calendar_spine.sql` (date_spine 2019-01-01 → today, monthly)
    - `xero.yml` — schema YAML that **already documents** `xero__balance_sheet_report` with full column descriptions (see §5)
  - `dbt_packages/` — `xero_source` (Fivetran), `fivetran_utils`, `dbt_utils`. Includes `stg_xero__organization` exposing `financial_year_end_month` and `financial_year_end_day`.

The instruction does not mention the target table name `xero__balance_sheet_report` directly, but **`xero.yml` does**, with a detailed description of every column the verifier checks. Agents who read the schema YAML get all the structural specs (which columns to populate, when to use Retained Earnings vs Current Year Earnings, fiscal-year boundary semantics) handed to them.

## 5. The schema YAML for `xero__balance_sheet_report` (the *real* spec)

Found in `models/xero.yml`:

```
description: >
  Each record represents the state of the balance sheet for a given account on a given month.
  Data Sources:
  - xero__calendar_spine
  - xero__general_ledger
  - organization

tests:
  - dbt_utils.unique_combination_of_columns:
      combination_of_columns: [source_relation, date_month, account_name]

columns:
  - account_name: For ASSET/EQUITY/LIABILITY use the ledger account_name.
                 Otherwise (REVENUE/EXPENSE) → 'Retained Earnings' if journal date is BEFORE the start
                 of the current fiscal year, 'Current Year Earnings' otherwise.
  - account_code: ledger code for ASSET/EQUITY/LIABILITY; null otherwise.
  - account_id:   ledger id for ASSET/EQUITY/LIABILITY; null otherwise.
  - account_type: ledger type for ASSET/EQUITY/LIABILITY; null otherwise.
  - account_class: ledger class for ASSET/EQUITY/LIABILITY; 'EQUITY' for everything else.
  - net_amount:  net balance amount, "aggregated based on the journal entries"
                 (the YAML does not literally use the words "cumulative" / "running sum")
```

This is more than enough information for an expert dbt engineer to implement, but the YAML doesn't explicitly say "running cumulative sum from the start of time" — that has to be inferred from "balance sheet" semantics (a balance sheet is a snapshot, not a flow). Profit/Loss is a flow statement, so the provided P&L model uses `sum(net_amount)` *within the month*; the missing balance-sheet model needs `sum() OVER (PARTITION BY account ORDER BY date_month ROWS UNBOUNDED PRECEDING)` for asset/liability/equity, plus separate fiscal-year roll-ups for retained vs. current earnings. None of this is hand-held in the instruction or YAML.

## 6. Verifier — and a serious soft spot

`/tests/test_dbt.py` runs `compare_pandas_table` against `tests/gold.duckdb::xero__balance_sheet_report`.

Gold table: **1170 rows × 8 cols**. Distinct values:
- 60 distinct `date_month` (2019-10-01 … 2024-09-01)
- account_class counts: ASSET=519, LIABILITY=472, EQUITY=179
- EQUITY accounts: `Dividends Declared/Paid` (60), `Owner A Share Capital` (60), `Retained Earnings` (59) — note **Current Year Earnings is NOT present in gold** even though the YAML documents it. (See §6.2.)

`tests/config.json`:
```json
{
  "condition_tabs": ["xero__balance_sheet_report"],
  "condition_cols": [[1, 2, 3, 4, 5, 7]],
  "ignore_orders": [true]
}
```
- Columns checked: `account_name, account_code, account_id, account_type, account_class, net_amount` (skips `date_month` index 0 and `source_relation` index 6).
- `ignore_order=true`.

### 6.1 The comparison logic is broken-shaped

`compare_pandas_table` (port of spider2-dbt's `duckdb_match`):

```python
t_gold_list = gold_cols.transpose().values.tolist()   # list of column-vectors
t_pred_list = pred_cols.transpose().values.tolist()
for gold_col in t_gold_list:
    if not any(vectors_match(gold_col, pred_col, ignore_order_=ignore_order)
               for pred_col in t_pred_list):
        return False
return True
```

When `ignore_order=True`, each column vector is sorted independently before comparison. This means:

1. **Row alignment is destroyed.** A pred column passes if it's a permutation of a gold column considered alone. The relationship between (account_id, net_amount) on the same row is *not* enforced.
2. **Column ordering is not enforced** — pred just needs to *contain* a column that matches each gold column.
3. **Date is not checked at all** — `condition_cols` excludes index 0.

So the verifier is effectively a multiset-of-values check, per column, ignoring row identity. For a passing answer:
- The multiset of `account_name` values must match (same name appearing the same number of times across all 1170 rows).
- The multiset of `net_amount` values must match exactly to ±0.01.

This is *easier* than a row-by-row check (you can scramble rows freely) but *harder* in another sense: every numeric balance must hit the exact gold value, with no slack on which row/account it's attached to. Because net_amount is a real number, near-misses are still wrong, and the agent has zero feedback about WHICH rows are off.

### 6.2 `Current Year Earnings` mismatch — the schema YAML lies

The YAML says: "if the journal date is before the start of the current fiscal year → 'Retained Earnings'; otherwise → 'Current Year Earnings'." But in the actual gold:

```
=== Equity account names ===
  account_name              count
  Dividends Declared/Paid   60
  Owner A Share Capital     60
  Retained Earnings         59
```

There is **no** `Current Year Earnings` row in gold. Why? The "current fiscal year" semantics depend on dataset's "current date" (the date_spine ends near today). In the gold, the latest month is 2024-09-01 and the organization's fiscal year ends Dec 31. Several plausible explanations:

(a) Gold was built so that "Current Year Earnings" is materialized differently — the rows for the current FY get bucketed under `Retained Earnings` until the year closes;
(b) Gold treats *every* completed FY's REVENUE/EXPENSE roll-up as Retained Earnings and the running 2024 partial year happens to net to ~0;
(c) Gold is just buggy / inconsistent with its own YAML doc and someone applied a different filter.

This is a real ambiguity that adds risk: agents who follow the YAML literally and produce both `Retained Earnings` and `Current Year Earnings` rows will fail because the multisets won't match. (The verifier checks `account_name` value multiset.)

### 6.3 Concrete failure modes the test will catch

Even an agent that does the architecturally right thing can fail on:

- **net_amount sign convention.** The provided P&L model multiplies by -1 (`coalesce(sum(ledger.net_amount * -1), 0)`); the balance sheet may or may not need the same flip per account class. Wrong sign → exactly zero overlap with gold's net_amount multiset → fail.
- **Cumulative window or not?** A balance sheet is cumulative. If the agent emits flow numbers per month (like the P&L), the multiset of net_amounts will not match.
- **Calendar-spine left-join semantics.** The P&L template does `left join ledger on calendar.date_month = trunc('month', journal_date)`. Copy-pasting that for the balance sheet gives flow numbers not running balances, plus produces NULL months for months with no activity (which isn't how a balance sheet works — the balance carries forward).
- **Where the spine starts.** Calendar starts at 2019-01-01, but the gold's earliest `date_month` is 2019-10-01 (clearly the first month with any ledger activity). Agents who include 2019-01..2019-09 will inflate row counts.
- **`source_relation` value handling.** Verifier excludes column 6, so OK to differ — but if the agent uses `source_relation` in the surrogate key and ends up with extra rows because of different relation tagging, the row counts on other columns will be wrong.
- **Retained Earnings vs Current Year Earnings.** As above — gold has no CYE rows. An agent generating CYE will fail.
- **`account_code` is INTEGER in gold (and `<NA>`/NaN where account_code is null).** If agent produces VARCHAR codes, comparison may fail (or pass if pandas coerces, but multisets will diverge for null vs. -inf values).

### 6.4 What "right answer" looks like (likely SQL skeleton)

```sql
-- ASSET/LIABILITY/EQUITY ledger accounts: cumulative by (account, source_relation), monthly snapshot
with bs_accounts as (
  select calendar.date_month,
         ledger.account_name, ledger.account_code, ledger.account_id,
         ledger.account_type, ledger.account_class, ledger.source_relation,
         sum(case when trunc('month', ledger.journal_date) <= calendar.date_month
                  then ledger.net_amount else 0 end) as net_amount
  from xero__calendar_spine calendar
  cross join (select distinct ... from xero__general_ledger
              where account_class in ('ASSET','LIABILITY','EQUITY')) accounts
  left join xero__general_ledger ledger
    on ledger.account_id = accounts.account_id
   and ledger.source_relation = accounts.source_relation
  group by 1,2,3,4,5,6,7
),
-- REVENUE/EXPENSE rolling into Retained Earnings (cumulative across all closed FYs)
retained as (
  select calendar.date_month,
         'Retained Earnings' as account_name, null::int as account_code,
         null as account_id, null as account_type,
         'EQUITY' as account_class, ledger.source_relation,
         sum(... pre-fiscal-year flows ...) as net_amount
  from ...
)
-- ... + Current Year Earnings ... + UNION ALL.
```

The exact handling of FY boundaries via `stg_xero__organization.financial_year_end_month/day` is the hardest part.

## 7. Per-trajectory analysis

Six sub-agents read all 18 trajectories (3 per `model × agent` combination); detailed per-run reports are in `trajectories/`. Cross-cutting findings (every trial, every agent):

| Aspect | Universally observed? | Notes |
|---|---|---|
| Read `models/xero.yml` schema doc | **18/18** | All trials located the YAML and read the column-level rule including the "Retained Earnings vs. Current Year Earnings" instruction. |
| Inspected `stg_xero__organization` for FY end | 14/18 | Two `terminus-2 + gpt-5.4` runs and one `terminus-2 + gemini` minor run skipped or guessed it because `duckdb` CLI was missing and they didn't fall back to Python. |
| Implemented cumulative running balance | **18/18** | Either `SUM() OVER (... ROWS UNBOUNDED PRECEDING)` or `INNER JOIN ON journal_month <= calendar.date_month`. |
| Computed per-row fiscal-year start from `current_date` | 12/18 | Most agents anchor "current FY" to `current_date` (today). Only `claude-code/opus run 3` and `gemini-cli/gemini run 3` correctly compute it per `date_month`. |
| Emitted `Current Year Earnings` rows | 9/18 | Every faithful YAML implementation emits CYE rows; gold has none. Agents who anchored FY to `current_date` (with data ending 2021 vs. wallclock 2025-2026) accidentally collapsed everything into RE — passing on the YAML/gold mismatch by luck, not skill. |
| Applied `* -1` sign flip from the P&L template | 9/18 | A coin flip. Half cargo-cult it from `xero__profit_and_loss_report.sql`; half (correctly) don't. **Gold uses no flip** — see §8. |
| Bound calendar spine to gold's `2024-09` cutoff | **0/18** | The provided spine extends to `current_date + 1 month` (≈ 2026-04 at run time). Gold stops at 2024-09 because that's when gold was generated. |
| Emitted `account_code` as INTEGER (vs TEXT) | 0/18 | Most agents `cast(null as varchar)` for the EQUITY rebucket → entire `account_code` column is TEXT. Gold's column is INTEGER + NaN. The verifier's per-column multiset check fails because string `'610'` ≠ int `610`. |
| Ran the harbor verifier | **0/18** | None looked in `/tests/`, none invoked `test_dbt.py`. |
| Counted output rows vs. any reference | 0/18 (only run 2 of `terminus-2/opus` got a coincidental 1170, treated it as confirmation). |
| Treated `dbt run`/`dbt test` PASS as success signal | **18/18** | `dbt test` only checks the unique-key constraint, which is trivially satisfied. |
| Hit timeout / exception / budget | 0/18 | All finished cleanly, all received `reward=0.0` from the verifier. |

**Two distinct strategies emerge:**
- **Pattern A — recognize the upstream package & copy verbatim** (6/6 Gemini runs across `gemini-cli` and `terminus-2`). Agents `curl` `https://raw.githubusercontent.com/.../fivetran/dbt_xero/.../xero__balance_sheet_report.sql` directly into `models/`. This is *the* canonical Fivetran balance-sheet model that the gold table itself was built from. They get architecture for free.
- **Pattern B — rewrite from scratch** (12 runs across Claude/Opus and GPT-5.4). Agents read the YAML, re-derive the CTE structure, and write SQL that resembles the upstream by convergent reasoning.

Both patterns fail with `reward=0.0`.

## 8. Hard evidence on the verifier-vs-environment mismatch

I queried gold (`tests/gold.duckdb`) directly:

### 8.1 Gold uses **no** sign flip
```
Accounts Receivable (ASSET):  raw cumulative sum gives  +49,381.37  ←  matches gold
                              `*-1` cargo-cult would give  -49,381.37 ←  not in gold
Retained Earnings (EQUITY):   raw signed sum is -47,596.22  ←  matches gold
```
Hence the P&L template's `sum(net_amount * -1)` is **wrong** for the balance-sheet model. The provided template actively misleads agents who copy patterns. 9 of 18 trials cargo-culted the flip and were guaranteed to fail on the `net_amount` multiset.

### 8.2 Gold is non-reproducible — its `date_month` cutoff is frozen at gold-generation time

- Source ledger has journals only between `2019-10-23` and `2021-03-17`.
- Gold has 60 distinct `date_month` values from `2019-10-01` to **`2024-09-01`** — 30 months of *flat carry-forward* of the 2021-03 closing balance, 20 accounts per month = 600 carry-forward rows.
- The provided `xero__calendar_spine.sql` has `end_date = dateadd(month, 1, current_date)`. So gold was generated with `current_date ≈ 2024-09-XX` (probably August 2024 when the dataset was assembled).
- When the agent runs the same dbt code in 2025-2026, the spine extends to `2026-04` → ~19 extra months × ~20 accounts = ~380 extra carry-forward rows. The `account_name` and `net_amount` multisets diverge by exactly those extra rows. **Gold cannot be reproduced by re-running the canonical SQL.**

This is the single biggest task-quality bug: **the same SQL produces a different answer every month**. The 6 agents that copy-pasted the upstream Fivetran model — i.e., did the *theoretically optimal* thing — still fail because the gold was a frozen 2024-09 snapshot.

### 8.3 Gold lies about the YAML
The schema YAML in `models/xero.yml` (which the agent is *meant* to use as its spec) explicitly documents `Current Year Earnings` rows:

> "if the journal date is before the start of the current fiscal year, it is categorized as 'Retained Earnings'. For accounts in the current fiscal year, it is categorized as 'Current Year Earnings'."

But gold contains zero CYE rows — only `Dividends Declared/Paid (60)`, `Owner A Share Capital (60)`, `Retained Earnings (59)`. The YAML's "current fiscal year" isn't well-defined when the data is 4 years old: under a `current_date`-anchored interpretation everything historical collapses into RE (gold-consistent); under a per-`date_month`-anchored interpretation (the more semantically correct one for a *historical* monthly balance sheet) you correctly produce CYE rows for every month inside that month's own fiscal year (gold-inconsistent).

Both interpretations are *defensible*. The YAML doesn't disambiguate. Gold picks one. 9/18 agents picked the other. **This is genuine spec ambiguity, not agent failure.**

### 8.4 The verifier itself is permissive in a misleading way

`compare_pandas_table` with `ignore_order=True` and `condition_cols=[1,2,3,4,5,7]`:
- For each gold column, it scans all of pred's columns (not just the column of the same index) for a multiset match.
- Row alignment is destroyed: gold and pred are compared column-by-column independently.
- Date column is excluded from the check.

So an agent could *theoretically* pass with a completely scrambled date column — but every numeric `net_amount` and integer `account_code` must hit gold's multiset to ±0.01. Combined with §8.1-§8.3, the bar is "every value, exact, no approximation, and you have to guess unspecified conventions correctly". This permissive-on-rows / strict-on-values asymmetry punishes near-correct answers more than it rewards them.

## 9. Verdict — task vs. agent capability

**The task fails on its own merits, in three independent ways. It is not predominantly an agent capability bottleneck.**

### Score
- Of the failure axes I observed, here is my attribution split:

| Failure axis | Why agents miss it | Task or agent? |
|---|---|---|
| **Calendar cutoff `2024-09`** is hard-coded in gold but `current_date`-driven in the env | An optimal agent runs the canonical Fivetran SQL — the spine extends to today → too many rows | **TASK** — non-reproducible gold, the answer literally changes monthly |
| **Sign convention (`* -1` or not)** unspecified | YAML doesn't specify; the only available code template (P&L) uses `* -1`, which is the WRONG choice for balance sheet | **TASK** — under-specified; the *only* template misleads |
| **Current Year Earnings vs. Retained Earnings** ambiguity | YAML says emit both; gold has only RE | **TASK** — YAML literally contradicts gold |
| **`account_code` INTEGER vs TEXT** | YAML doesn't specify type; agents default to `cast(null as varchar)` for null branch | **TASK** — under-specified; type info isn't in the YAML |
| Confidence on `dbt test` PASS | `dbt test` only validates the trivial unique-key constraint; agent confuses dbt-test green with task-correctness green | Agent + task — agent should be skeptical, but the task gives no failure signal of its own (no `tests/` visible to agent) |
| Skipped exploration of `/tests/` | `/tests/` is *outside* `/workspace`; the instruction does not mention a verifier. Even if the agent looked, the verifier reads gold from a path the agent can't see | **TASK** — gold/verifier are intentionally hidden, which is correct, but no other oracle is provided |
| Calendar spine starts 2019-01 (gold starts 2019-10) | Gold's start is data-driven (first journal); spine inflates count if not bounded | Mostly task (env design), partly agent (should bound to ledger activity) |

### Theoretical solvability
> *Can a super-capable agent solve this task given only the current instructions and environment?*

**No.** Even an oracle-perfect dbt engineer sitting in `/workspace` cannot recover the gold table because:

1. **The gold's calendar cutoff (`2024-09-01`) is a hidden constant** that depends on the system clock the day gold was generated, not on any signal in `/workspace`. Even if the agent knew "gold was generated some day in 2024", the precise month cutoff is not deducible.
2. **The YAML's CYE/RE rule is internally contradictory with gold** under any interpretation that produces CYE rows for historical months — and "current fiscal year" applied to a 2020 row most naturally means "the FY containing 2020" (per-row anchor), which produces CYE.
3. **Sign convention is underspecified.** Only context clue (P&L template) is *misleading*.

Gemini's audit claims "the instruction is concise but sufficient for an expert agent" — this is verifiably false. The provided instruction is *not* sufficient: it's a single sentence pointing the agent at an underspecified YAML that contradicts a non-reproducible gold.

### Where agent capability *does* matter (smaller, but real)
- All 18 agents could have run a Python `compare-against-gold` script if they thought to look outside `/workspace`. None did — but the verifier's `/tests/` is by design hidden, so this isn't truly available signal.
- Stronger agents should be skeptical of `dbt test` PASS as task-correctness; this is a real soft skill gap, but it would only have helped if the agent had an *alternative* oracle. They didn't.
- Run 2 of `terminus-2 + opus` accidentally got 1170 rows (matching gold's count). A more careful agent might have noticed (i) the upstream's `current_date` anchor is suspicious for a historical report, (ii) the calendar should be bounded by ledger activity, (iii) the P&L template's `*-1` should be questioned. But even doing all of these would not have produced the gold — gold's 2024-09 cutoff is unrecoverable.

### Conclusion
**The task should be REJECTED in its current form**, contradicting Gemini's verdict. The 0/18 success rate is a near-certain consequence of three independent specification/environment defects, not a clean signal about frontier-model SQL reasoning. Gemini's audit also cited a fabricated trajectory ID (`565646a0-…` does not exist in the collection of 18 runs), suggesting the audit was not grounded in actual evidence.

## 10. Proposed fixes (real fixes, not simplifications)

The task's *intent* is good — a real cumulative-balance / FY-rollup dbt challenge is worthwhile. Here are concrete fix paths, ranked by surgical-vs-invasive:

### Fix A — Pin the calendar spine to a fixed end_date (smallest fix; recommended)
Edit `models/utilities/xero__calendar_spine.sql` to use a hard-coded end date matching the gold:
```sql
{{ dbt_utils.date_spine(
    datepart="month",
    start_date="cast('2019-01-01' as date)",
    end_date="cast('2024-10-01' as date)"  -- was: dbt.dateadd('month',1,'current_date')
) }}
```
This makes gold reproducible. **Insufficient on its own** — also need fixes B and C below.

### Fix B — Disambiguate the YAML
Replace the column doc on `account_name` with one of:
1. (Match upstream Fivetran) "non-balance-sheet activity is rolled into 'Retained Earnings' (no Current Year Earnings is materialized in this report)."
2. (Match per-row FY semantics) Keep current text **but include a worked example** showing what 'current fiscal year' means when reporting a historical month.

Currently the spec is undecidable; agents have to guess. This is the spec-quality fix.

### Fix C — Document the sign convention in the YAML
Add to the `net_amount` description:
> "`net_amount` is the raw signed sum of ledger entries; assets and expenses appear as positive, equity/liabilities/revenues as negative. Do not apply the `* -1` flip used by `xero__profit_and_loss_report`."

Without this, even an expert sees one template (`*-1`) and has no way to know it's wrong here.

### Fix D — Strengthen the verifier from "multiset per column" to "multiset per row"
The current verifier accepts pred columns matching gold columns *independently*. Replace with:
```python
# join pred and gold on (date_month, account_name, account_class), then check net_amount per pair
```
This makes "near-correct but row-wise wrong" answers fail clearly and gives better failure messages. (Optional — not strictly necessary if A+B+C land.)

### Fix E (alternative to A) — Provide a static reference row count or sample in the instruction
Tell the agent "the gold has 1170 rows, with account_class distribution {ASSET: 519, LIABILITY: 472, EQUITY: 179}". Plus a 5-row sample. This gives an oracle for self-validation without leaking the answer. Agents who self-check (run 3 of claude-code/opus, run 2 of terminus-2/opus) would converge.

### Fix F — Acknowledge the verifier's existence in the instruction
Add a one-liner: "A verifier in `/tests/` will materialize-compare your `xero__balance_sheet_report` table against a gold standard. You may *not* read the gold, but be aware your output is matched on `[account_name, account_code, account_id, account_type, account_class, net_amount]` multisets."

This levels the playing field: agents currently treating `dbt test` as the success signal would explicitly know to validate output structure.

### Recommendation
Apply **A + B + C** together. Fix A alone reproduces gold but does nothing for the YAML/sign confusion. Fix B alone won't help with the cutoff drift. Fix C is cheap and high-value. Together they remove all three blocking bugs while preserving the task's challenge (cumulative window, FY math, calendar spine). Then **expect 2-4 of the 18 agent strategies to pass** — specifically the ones that: read the YAML, copy the upstream Fivetran model, and now have the right sign + cutoff. That'd give a real ~10-25% pass rate that genuinely measures dbt+SQL+accounting reasoning capability, instead of 0% measuring "can the agent guess three undocumented conventions correctly".

If we don't want to introduce the three fixes (e.g. because authors want to keep the unmodified upstream package), the only correct call is to **REJECT** the task: reward=0 across 18 frontier-model trials says nothing meaningful when all three failure modes are induced by task defects, not capability ceilings.

## 11. TL;DR for this audit

- **Failure cause:** **task itself**, not agent capability. Three independent task-quality bugs (non-reproducible gold's date cutoff, YAML/gold contradiction on Current Year Earnings, undocumented + actively misleading sign convention).
- **Closest agent:** `terminus-2 + claude-opus-4-6 run 2` — got the row count, account_class distribution, and "no CYE" property right, but failed on `account_code` type, `*-1` sign and date range. ~80% architectural progress.
- **Gemini audit:** cannot be relied on. Cited a fabricated trajectory ID, missed all three task-quality bugs, and conflated "agents tried hard" with "task is well-designed".
- **Recommendation:** **REJECT** as currently shipped. **ACCEPT WITH FIXES A+B+C** if revised.

