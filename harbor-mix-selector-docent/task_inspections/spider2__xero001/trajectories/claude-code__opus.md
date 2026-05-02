# spider2/xero001 — claude-code (claude-opus-4-6) trajectory analysis

Three claude-code runs against the Xero balance-sheet dbt task (collection
`640e920a-aef3-4b7c-9487-69899ef19e9d`). All three runs are short-to-medium
length (~30 turns) and all three terminate with the agent claiming success
after `dbt run` and `dbt test` pass. None of them ran the verifier; their
own success criterion is that dbt's `unique_combination_of_columns` test
passes — a *much* weaker check than the gold-row comparison the verifier
does.

The gold table has 1170 rows over ASSET (519) / LIABILITY (472) / EQUITY
(179). Within EQUITY: Dividends Declared/Paid (60), Owner A Share Capital
(60), **Retained Earnings (59)** — and **no Current Year Earnings rows at
all**, despite the schema YAML telling the agent to bucket prior-FY P&L as
Retained Earnings and current-FY P&L as Current Year Earnings.

This makes the YAML a trap: the schema description and the verifier
disagree, and trusting the schema (which is the natural thing to do)
loses points.

---

## Run 1 — `10da9d48-aa2e-40ef-9fb4-8df5bf7f7fd2`

**Final SQL:** `union all` of (a) ASSET/EQUITY/LIABILITY ledger entries with
their full account metadata, and (b) REVENUE/EXPENSE entries reclassified
into 'Retained Earnings'/'Current Year Earnings' by comparing
`ledger.journal_date` to a `current_fiscal_year_start_date` derived from
`current_date` (today). Then `monthly_amounts` aggregates by
`(date_month, account_*)`, cross-joined with the calendar spine and unique
account list, then `sum(...) over (partition by account_name, account_id,
source_relation order by date_month)` for the cumulative running total. No
`* -1` applied to net_amount.

**Architecture present:** cumulative window function ✔, calendar spine
cross-join ✔, FY bucketing logic ✔, organization join for FY end month ✔.
Self-check confirmed Assets+Liabilities+Equity ≈ 0 across months → agent
felt good and stopped.

**Surface failure (vs gold):**
1. **No `* -1` on net_amount.** P&L template has `sum(net_amount * -1)`,
   the agent reasoned about it but kept signs raw, so every ASSET row has
   wrong sign relative to the gold (gold uses Xero's display convention,
   which is `* -1` for the way the data sits in this ledger).
2. **Cross-product over the entire calendar.** Output has 1760 rows
   (≈19 accounts × 79 months × 1 source) — gold has 1170, only
   activity-bearing months. Many `net_amount = 0` rows for months before
   the first journal entry exist in the model; verifier would reject every
   extra row.
3. Accidentally got the "no Current Year Earnings" piece right — but for
   the *wrong* reason. Because the agent used `current_date` (2026) to
   define the FY start, and all journal data is 2019–2021, *every* P&L
   entry falls before the "current FY", so they all collapse into Retained
   Earnings. The agent wrote logic for both buckets but only one ever
   fires given the year gap.

**Root cause:** (b) cargo-cult plus (a) misread of spec. Followed the YAML
literally for the FY bucketing rule, but anchored "current FY" to
`current_date` instead of to each row's `date_month`. Did not consider
that the verifier might want a sparser table.

**Architectural progress:** ~70%. Gets running totals, FY logic, and
calendar spine. Misses sign convention and densification policy.

---

## Run 2 — `3ae6795b-2226-4420-9422-91fd50c0e4f1`

**Final SQL:** Same overall shape as run 1 — classifies each ledger row
into bucket up front, monthly aggregates, then a `left join` of
`all_account_months` to `monthly_totals` on `date_month >= date_month`
with `sum(...)` group-by — i.e. cumulative via correlated-aggregate join
rather than window function. Critically ends with
`select * from final where net_amount != 0`. No `* -1`.

**Architecture present:** cumulative aggregation ✔ (via join, not
windows), calendar spine cross-join ✔, FY bucketing ✔, FY-end-month logic
✔, `where net_amount != 0` filter ✔ (this is closer to gold's sparse shape
than run 1).

**Surface failure (vs gold):**
1. **No `* -1`.** Same sign issue as run 1 — Assets are positive,
   Liabilities negative, Equity negative; gold's convention is the
   opposite for at least some classes (`Dividends Declared/Paid` 30000
   in agent vs. `* -1` of that in gold display).
2. Same `current_date`-anchored FY start, so again no Current Year
   Earnings ever materializes — it's all Retained Earnings. By coincidence
   matches gold's column set, but only because the data is stale.
3. **Row count is 1383 (vs gold 1170).** Filtering on `net_amount != 0`
   helped trim, but still includes some near-zero floating-point
   residues. Reports 19 distinct accounts × 79 months. Still includes
   accounts in months where the agent's cumulative-from-monthly-total
   computation produced nonzero noise that wouldn't appear in gold.

**Root cause:** mostly (b) cargo-cult — copies the P&L's structure,
including `where account_class in (...)` and `sum(net_amount)` style, but
strips the `* -1` and never thinks about it again. No diagnostic
comparison to gold or even row-count sanity check vs. expectations.
Self-check is just "does the unique-key dbt test pass" → trivially yes.

**Architectural progress:** ~75%. Cumulative join, FY logic, sparse
filtering, calendar spine — only missing sign and a tighter densification
rule.

---

## Run 3 — `712c2d01-8465-4f36-b32c-956e94cb5b4f`

**Final SQL:** The most ambitious of the three. Three separate CTEs:
`bs_accounts` (cumulative ASSET/EQUITY/LIABILITY via
`journal_month <= calendar.date_month`), `retained_earnings`
(REVENUE/EXPENSE with `journal_date < fiscal_year_start`), and
`current_year_earnings` (REVENUE/EXPENSE with
`journal_date >= fiscal_year_start AND journal_month <= date_month`).
`fiscal_year_start` is computed *per row* from `calendar.date_month`,
not from `current_date` — so each reporting month has its own FY start.
Initial version applied `* -1` on the earnings CTEs; balance check showed
total ≠ 0 ($832k off in Dec 2020), so the agent **diagnosed it,
fixed it** by removing the `* -1`, re-ran, confirmed monthly totals = 0,
and stopped.

**Architecture present:** cumulative aggregation ✔, calendar spine ✔,
**per-row dynamic FY start** ✔ (only run that does this), separate
Retained vs. Current Year Earnings ✔, organization variable correctly
plumbed through `dbt_project.yml`, balance-equation self-check ✔ used to
debug.

**Surface failure (vs gold):**
1. **Has Current Year Earnings rows.** Because the FY start is anchored
   to each `date_month`, this run actually produces Current Year Earnings
   that change month-to-month, e.g. Dec 2020 Current Year Earnings =
   $369,541.45. Gold has zero such rows — every P&L entry in gold ends
   up in Retained Earnings. So this run is *closer to the spec* but
   *farther from gold* on the equity bucketing.
2. **No `* -1`** in the final version. Removed during the
   balance-equation debugging step. Means signs disagree with gold
   convention.
3. Row count 1574, denser than runs 1/2. Both Retained and Current Year
   Earnings rows exist for every month with activity → many extra rows
   the gold doesn't have.

**Root cause:** (a) misread of spec — the most diligent reading, but the
spec itself is a trap. Plus (b) cargo-cult on the sign issue: removed
`* -1` because Assets+Liabilities+Equity didn't sum to zero, instead of
recognizing that the gold convention applies the flip to *every* class
(or that the gold's reference value for Assets is positive and the model
needs `* -1` on liabilities/equity instead). The balance check it ran is
agnostic to global sign — `(A + L + E) = 0` holds either way.

**Architectural progress:** ~85%. The strongest architecture of the
three. Only needed (i) the sign convention pinned to gold and (ii) the
spec-vs-gold disagreement on Current Year Earnings to know not to
materialize them.

---

## Cross-run patterns

| Concern | Run 1 | Run 2 | Run 3 |
| --- | --- | --- | --- |
| Read xero.yml schema | yes | yes | yes |
| Discovered CYE/RE spec | yes | yes | yes |
| Inspected stg_xero__organization | yes | yes | yes |
| Cumulative running sum | window | left-join inequality | left-join inequality |
| Calendar spine cross-join | yes | yes | yes |
| FY bucketing | yes (anchored to current_date) | yes (anchored to current_date) | yes (anchored per row) |
| `* -1` on net_amount | no | no | no (had it, removed) |
| Self-check | balance eq | none beyond uniqueness | balance eq, debugged |
| Ran the verifier | no | no | no |
| Sparse vs dense output | dense (1760) | sparse (1383, !=0 filter) | dense (1574) |
| Has Current Year Earnings rows | no (data too old) | no (data too old) | yes |
| dbt test passes | yes | yes | yes |

**Common threads:**

- All three did the *exploration* work the task expected — read the YAML,
  inspected `xero_organization_data`, understood the staging-model layout
  and the P&L template. None of them skipped exploration.
- All three trusted the YAML's "Current Year Earnings" / "Retained
  Earnings" rule; the task's gold table contradicts the YAML by including
  only Retained Earnings. None of them noticed that the YAML and the gold
  could disagree, because they never ran the verifier or compared row
  counts to any reference.
- All three stripped or never added the P&L template's `* -1` sign flip
  — runs 1 and 2 simply forgot, run 3 actively removed it after a
  balance-equation diagnostic gave a misleading green light.
- All three terminated on `dbt run` + `dbt test` PASS rather than on
  agreement with a gold artifact. The unique-key dbt test is trivially
  satisfied by any reasonable bucketing.
- Run 3 is architecturally the strongest (per-row FY anchor, both
  buckets present, balance-equation debugging) but is *farther* from gold
  than runs 1/2 because gold has no Current Year Earnings rows.

**Why all three fail:** the verifier compares against a gold table that
follows a specific Xero export convention (sign and bucket choices). The
agents have no access to gold and use the YAML as their oracle. The YAML
is a faithful description of *Fivetran's published Xero balance-sheet
model* but the gold here was apparently generated with different
sign/bucketing assumptions. Without access to a reference row or the
verifier, the gap is invisible to the agent's own diagnostics.
