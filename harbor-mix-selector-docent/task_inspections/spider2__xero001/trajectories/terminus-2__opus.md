# Trajectory analysis: spider2 / xero001 — terminus-2 + anthropic/claude-opus-4-6

Three runs of `terminus-2` with `anthropic/claude-opus-4-6`. All three finished cleanly (no
timeouts, no exceptions), all three produced a model that ran in dbt, and all three were
graded `reward = 0.0` by the verifier. Failure mode is purely "wrong answer" — different
specific wrong answers per run, with substantial overlap in the underlying mistakes.

The verifier checks the multisets (per column) of `account_name, account_code, account_id,
account_type, account_class, net_amount` against gold (1170 rows; 60 distinct months
2019-10..2024-09; account_class counts ASSET=519, LIABILITY=472, EQUITY=179; equity rows
only `Dividends Declared/Paid` (60), `Owner A Share Capital` (60), `Retained Earnings`
(59) — **no `Current Year Earnings` rows in gold despite the YAML mentioning it**).

---

## Run 1 — `17702052-ae7c-4205-b9c9-716b9d65108f`

**39 messages. Final state: dbt-clean, 1574 rows, includes `Current Year Earnings`, applies `* -1` to REVENUE/EXPENSE; marks complete.**

### Trajectory
1. Reads `dbt_project.yml`, `profiles.yml`, every model file in `/workspace/models`,
   `xero.yml` schema, `stg_xero__organization.sql` and the columns macro. *Discovers the
   YAML spec for `xero__balance_sheet_report`.*
2. Inspects the source DuckDB. Confirms `financial_year_end_month=12, day=31` and the
   account_class taxonomy.
3. Writes a model with three CTEs: `balance_sheet_accounts` (ASSET/EQUITY/LIABILITY,
   journal_month <= date_month), `revenue_expense_current_year` (CYE, journal_month
   between fiscal_year_start and date_month, with `net_amount * -1`), and
   `revenue_expense_prior_years` (Retained Earnings, journal_month < fiscal_year_start,
   `net_amount * -1`). Computes per-row `fiscal_year_start` via `EXTRACT(year, ...)` arithmetic.
4. First run fails: `Conversion Error: date field value out of range: "2018-13-01"` — the
   fiscal-year-start branch tries to build month 13 when `financial_year_end_month=12`.
5. Patches with an explicit `when ... = 12 then '<year>-01-01'` branch. Model runs.
6. Sanity-prints monthly totals; notes "The balance sheet doesn't balance" but rationalises
   it as fine because `dbt test` (which only checks the unique-combination YAML test, not
   accounting validity) passes. Marks task complete.

### Final SQL (key parts)
```sql
revenue_expense_current_year:
  inner join ledger
    on journal_month <= date_month
   and journal_month >= fiscal_year_start
  net_amount * -1 as net_amount

revenue_expense_prior_years:
  inner join ledger
    on journal_month < fiscal_year_start
  net_amount * -1 as net_amount
```
Result has 1574 rows. At 2020-12-01 it shows **both** Current Year Earnings (369541.45)
and Retained Earnings (46493.14). Months covered start 2019-10 (correct) but end at the
calendar spine's last month (~2026-04 — too long).

### Surface failure
- Emits **both** `Current Year Earnings` and `Retained Earnings` rows. Gold has only
  `Retained Earnings`, so the `account_name` multiset has ~60 extra CYE entries that no
  gold column can match.
- Row count 1574 vs gold 1170 (404 extra rows = CYE rows + extra months past 2024-09).
- Likely also: `account_code` produced as VARCHAR (`cast(null as varchar)`) where gold has
  INTEGER + nulls; `net_amount` magnitudes differ by sign-and-bucketing.

### Root cause
**(a) misunderstood spec + (b) cargo-cult from P&L template.** Followed the YAML
*literally* — the YAML lies because it documents `Current Year Earnings` as a category
that gold doesn't actually contain. Sign-flipping `* -1` was copied from the P&L
template without checking whether balance-sheet ledger sums need it. Skipped any check
against the calendar's reasonable date range — the first 9 months of 2019 and everything
after late-2024 should not produce rows.

### Architectural progress: ~70%
Calendar-spine + general-ledger join, cumulative summation by `journal_month <=
date_month`, fiscal-year boundary case, EQUITY reclassification with
null-id/code/type — all structurally there. Just produced the literal YAML
interpretation rather than the gold's interpretation, and did not self-validate against any
plausibility check (e.g. ledger row count ≈ months × accounts).

---

## Run 2 — `579643bf-8f90-4b44-8f25-b1177a705471`

**~40 messages. Final state: dbt-clean, 1170 rows (matches gold count!), no Current Year Earnings, no `*-1` flip; marks complete.**

### Trajectory
1. Same opening exploration as run 1 — reads all models, schema YAML, organization
   staging, packages.
2. First attempt at the model has nested-Jinja-inside-string bug:
   `dbt.dateadd("...{{ dbt.type_string() }}...")` doesn't get re-rendered →
   `Parser Error: syntax error at or near "{"`.
3. Reads the compiled SQL from `target/compiled/...`, diagnoses the nested-Jinja issue,
   rewrites with pure SQL (`make_date(year(current_date), financial_year_end_month, ...)
   + interval '1 day'`) for the fiscal-year boundary. Model runs.
4. Sanity-checks output:
   - `count = 1170`, **exactly the gold row count**.
   - `select distinct account_name, account_class` shows only ASSET / LIABILITY
     accounts (no `Current Year Earnings`) plus the three EQUITY accounts including
     `Retained Earnings`. **All structural multisets superficially match gold.**
   - Independently verifies BMO Business cumulative balance with a window
     function on `xero__general_ledger` — matches.
   - Notices the calendar spine has 88 months but report has 79 (no rows for Jan–Sep 2019,
     because no journals before Oct 2019); accepts this as correct.
5. Runs full `dbt run + dbt test` — 23/23 models, 21/21 tests. Marks complete.

### Final SQL (key parts)
```sql
fiscal_year_info:
  cast(make_date(
    case when make_date(year(current_date), fy_end_month, fy_end_day) < current_date
         then year(current_date)
         else year(current_date) - 1
    end,
    fy_end_month, fy_end_day) + interval '1 day' as date) as current_fiscal_year_start

revenue_expense_accounts:
  case when journal_date < current_fiscal_year_start
       then 'Retained Earnings' else 'Current Year Earnings' end as account_name
  ledger.net_amount   -- NO * -1
  -- account_code/account_id/account_type cast as TEXT null

cumulative:
  inner join monthly_aggregated on monthly_aggregated.date_month <= calendar.date_month
```
Because the data ends in 2021-03 and `current_date` is in 2024+, **all** REVENUE/EXPENSE
journal_dates are `< current_fiscal_year_start`, so every reclassified row becomes
`Retained Earnings` and zero CYE rows are produced — which incidentally matches gold's
account_name multiset closely.

### Surface failure
- **Sign convention.** Did NOT apply `*-1` to net_amount anywhere. As a result
  `LIABILITY` totals are negative, `Retained Earnings` is negative (e.g. -47596.22), and
  the magnitudes do not match gold's expected sign-convention at all. Multiset of
  `net_amount` will completely miss.
- **Date range.** Report covers 79 months (2019-10 through 2026-04). Gold covers only
  60 months (2019-10 through 2024-09). 19 extra months × ~21 accounts = ~400 extra rows of
  carried-forward balances. The total stays at 1170 because... wait — the count *is* 1170
  on first measurement, then later in the run prints rows up through 2026 with same
  carried balance. **The 1170 match is a coincidence of asymmetric date coverage and the
  inner-join semantics dropping early-month no-journal accounts; it's not because the
  agent matched the gold's date range.** When recomputed for `account_name='BMO Business'`
  alone, output goes 79 rows long, gold has 60.
- account_code is TEXT in this run too (gold is INTEGER).

### Root cause
**(a) misunderstood spec + (e) "tests pass = task done" closure bias.** The agent's
self-check (Assets ≈ Liabilities + Equity? cumulative matches a window function?) only
validated *internal accounting consistency*, not the spec's expected sign convention. The
1170 row count match was treated as confirmation when it was a coincidence. The agent
never:
- Checked the date range against gold's date range (no access, but didn't even check
  against any reasonable cutoff like "today's calendar month" or "max(journal_date)").
- Flipped signs even though the P&L template right next to it does `net_amount * -1`.

### Architectural progress: ~80%
Best of the three. Got the dense calendar × account cross-section right (with
`monthly_aggregated.date_month <= calendar.date_month` cumulative join), produced exactly
one EQUITY reclassification name (Retained Earnings only), accidentally matched the
account-name multiset in shape. Two missing pieces would have made it pass: sign flip
(or correct sign convention) and a max-date cutoff at the last actually-needed
balance-sheet month.

---

## Run 3 — `b0c4d4c6-fb17-4abb-bc5b-57e260a7ede5`

**33 messages. Final state: dbt-clean, 1574 rows, includes Current Year Earnings (26 rows), no `*-1` flip; marks complete.**

### Trajectory
1. Identical opening exploration. Reads everything, finds the YAML, the P&L template, the
   organization columns macro. Notes "the net_amount for REVENUE/EXPENSE should NOT be
   multiplied by -1 (unlike P&L)" — explicit choice this time, not an oversight.
2. Writes the model in one shot with deeply nested `dbt.dateadd(month, 1,
   dbt.dateadd(month, fy_end_month, dbt.dateadd(year, -1, date_trunc('year', date_month))))`
   for the per-row fiscal-year start. Compiles and runs first try.
3. Sanity-checks the data — 1574 rows, distinct account_classes are ASSET / LIABILITY /
   EQUITY (no REVENUE/EXPENSE leaking), 21 distinct account_names including Current Year
   Earnings (26 rows) and Retained Earnings (76 rows).
4. Validates the accounting equation: per-month
   `assets + liabilities + equity ≈ 0` to floating-point precision. Concludes everything
   is correct, marks complete.

### Final SQL (key parts)
```sql
balance_sheet_accounts:
  inner join ledger on date_trunc('month', journal_date) <= calendar.date_month
  where account_class in ('ASSET','EQUITY','LIABILITY')
  sum(ledger.net_amount) as net_amount   -- NO * -1

income_statement_accounts:
  case when date_trunc('month', journal_date) >=
         (per-row fiscal_year_start computed by nested dateadds, with separate branch
          for fy_end_month=12 → date_trunc('year', calendar.date_month))
       then 'Current Year Earnings' else 'Retained Earnings' end
  sum(ledger.net_amount) as net_amount   -- NO * -1
```

### Surface failure
- Same `Current Year Earnings` mismatch as run 1 (gold has none; this run has 26 CYE rows).
- Same sign-convention mismatch as run 2 (no `*-1`). Total per month = 0, but gold uses
  the opposite sign convention so the `net_amount` multiset will not match.
- Row count 1574 vs gold 1170 — extra rows from CYE category and from the cumulative
  carry-forward extending beyond gold's 2024-09 cutoff.
- account_code is TEXT (gold is INTEGER + nulls).

### Root cause
**(a) misunderstood spec + (e) self-validation captured the wrong invariant.** Run 3 is the
most disciplined trajectory of the three: it correctly identified that REVENUE/EXPENSE
should NOT use `*-1`, computed the fiscal-year boundary properly, *and* validated the
accounting equation. But the invariant it validated (assets + liabilities + equity = 0
under double-entry signs) is necessarily true for any cumulative sum of a balanced ledger,
regardless of whether the sign is flipped or the YAML's CYE/RE categorization is what gold
actually wants. The verification was self-consistent but not specification-aware, and the
agent had no way to query gold semantics from `xero.duckdb`.

### Architectural progress: ~75%
Cleanest SQL, correct fiscal-year math, balance equation holds. Missing the same two
things as run 1: (i) follow the YAML literally → emits CYE rows that gold doesn't have,
(ii) didn't flip sign to match gold's convention, (iii) didn't bound the date range.

---

## Cross-run patterns

| Aspect | Run 1 | Run 2 | Run 3 |
|---|---|---|---|
| Read xero.yml schema | yes | yes | yes |
| Read stg_xero__organization | yes | yes | yes |
| Cumulative `date_month <= journal_month` join | yes | yes | yes |
| Per-row fiscal-year boundary | yes (Jinja) | yes (make_date + interval) | yes (nested dateadds) |
| Emits Current Year Earnings | YES (wrong) | no (lucky from cutoff date) | YES (wrong) |
| Emits Retained Earnings | yes | yes | yes |
| Sign flip `* -1` on REVENUE/EXPENSE | YES (matches P&L template) | no | no (explicit choice) |
| Bounds date range to gold's 2019-10..2024-09 | no | no | no |
| account_code as INTEGER vs TEXT | TEXT | TEXT | TEXT |
| Self-check beyond `dbt test` | minimal | per-account window match | accounting equation |
| Final row count | 1574 | 1170 (coincidence) | 1574 |
| Agent confidence at completion | high | high | high |

All three converged on **the same architectural skeleton** (calendar spine left/inner
joined to general ledger with a `<=` cumulative condition, EQUITY reclassification of
REVENUE/EXPENSE), differing only in fiscal-year arithmetic style and in 1-2 small
modeling choices (sign flip; CYE vs. RE only). The convergence makes sense: the YAML
walks the agent through the structure, the P&L template provides the join idiom, and the
remaining freedom is in details whose ground truth isn't in the workspace.
