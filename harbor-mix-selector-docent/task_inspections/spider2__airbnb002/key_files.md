# Key files for spider2 / airbnb002

The task is from the **Spider2-DBT** benchmark (in Harbor as `spider2-dbt`) and is built
from a generic adapter template, so the files below are *templates* — the runtime
populates `dbt_project/`, `tests/config.json`, and `gold.duckdb` per task.

## Adapter / template (in this repo / Harbor)

- Template instruction: `/home/shilin/T-Bench/harbor/adapters/spider2-dbt/template/instruction.md`
- Template task.toml: `/home/shilin/T-Bench/harbor/adapters/spider2-dbt/template/task.toml`
- Verifier wrapper: `/home/shilin/T-Bench/harbor/adapters/spider2-dbt/template/tests/test.sh`
- **Verifier core** (gold-vs-result table comparison): `/home/shilin/T-Bench/harbor/adapters/spider2-dbt/template/tests/test_dbt.py`
- Dockerfile: `/home/shilin/T-Bench/harbor/adapters/spider2-dbt/template/environment/Dockerfile`
- Adapter that builds per-task dirs: `/home/shilin/T-Bench/harbor/adapters/spider2-dbt/adapter.py`

## Per-task task instance (only visible inside the agent container)

Path inside container: `/workspace/`

- `/workspace/airbnb.duckdb` — DuckDB source DB; agent must populate output tables here
- `/workspace/dbt_project.yml` — name `dbt_airbnb`, profile `airbnb`
- `/workspace/profiles.yml` — DuckDB at `./airbnb.duckdb`, schema `main`
- `/workspace/packages.yml` — declares `dbt_utils` (referenced via `dbt_utils.surrogate_key`)
- `/workspace/models/source/src_listings.sql` — present
- `/workspace/models/source/src_hosts.sql` — **MISSING** (referenced via YAML / `ref('src_hosts')`)
- `/workspace/models/source/src_reviews.sql` — **MISSING** (referenced by `fct_reviews`)
- `/workspace/models/fact/fct_reviews.sql` — present, refs `src_reviews`
- `/workspace/models/dim/dim_dates.sql`, `dim_hosts.sql`, `dim_listings.sql`, `dim_listings_hosts.sql` — present
- `/workspace/models/agg/daily_agg_reviews.sql` — present
- `/workspace/models/agg/monthly_agg_reviews.sql` — present
- `/workspace/models/agg/mom_agg_reviews.sql` — present (month-over-month, last-30 rolling, uses LAG(REVIEW_TOTALS,29))
- `/workspace/models/agg/wow_agg_reviews.sql` — **MISSING** — agent must create this
  (7-day rolling totals of REVIEW_TOTALS by REVIEW_SENTIMENT × AGGREGATION_DATE,
   plus WoW % via LAG(.., 6) and a `DATE_SENTIMENT_ID` surrogate key)

## Verifier inputs (inside container, populated per-task)

- `/tests/config.json` — points to `gold_db`, lists `condition_tabs` (tables to diff)
  and per-table `condition_cols` / `ignore_orders`. (Exact contents not in repo —
  carried in the task package.)
- `/tests/test_dbt.py` — the Python diff that calls `compare_pandas_table` per
  table listed in `condition_tabs`. Compares numeric columns with `tolerance=1e-2`.
  Resolves the agent's submitted `Terminate(output="<file>.duckdb")` and falls back
  to the configured `result_db`.
- The gold DB ships with a `wow_agg_reviews` table of **10,851 rows** (per the
  Gemini audit note).
