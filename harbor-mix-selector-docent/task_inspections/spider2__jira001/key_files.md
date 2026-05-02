# Key Files for spider2/jira001

The Harbor task itself is **generated** by `Spider2DBTAdapter` from upstream Spider2-DBT data; it is registered in `harbor/registry.json` (`datasets/spider2-dbt/jira001`) but the actual files are pulled from a Hugging Face dataset at run time, so they are not present in the local working tree. The relevant files used to generate / verify the task all live in the adapter template, plus the upstream dbt project that the adapter copies into `/workspace/`.

## Adapter and template (Harbor side)

| Path | Why it matters |
|---|---|
| `/home/shilin/T-Bench/harbor/adapters/spider2-dbt/adapter.py` | `Spider2DBTAdapter._prepare_task_directory` shows how the task dir is built: copies `examples/<task>/` into `environment/dbt_project/`, copies `evaluation_suite/gold/<task>/<gold_db>` into `tests/gold.duckdb`, writes `tests/config.json` with `condition_tabs`/`condition_cols`/`ignore_orders` from `spider2_eval.jsonl`. |
| `/home/shilin/T-Bench/harbor/adapters/spider2-dbt/template/instruction.md` | The instruction template — agents see `## Task Description\n{instruction}` plus a fixed Environment / Objective / Execution Requirements block. |
| `/home/shilin/T-Bench/harbor/adapters/spider2-dbt/template/task.toml` | difficulty=medium, agent timeout 1800s, verifier timeout 600s. |
| `/home/shilin/T-Bench/harbor/adapters/spider2-dbt/template/environment/Dockerfile` | `python:3.11-slim` + `dbt-duckdb>=1.7.0` + `duckdb>=0.9.0` + pandas. Note the docker image pulls in DuckDB ~1.10 which is implicated in the `int_jira__pivot_daily_field_history` crash described below. |
| `/home/shilin/T-Bench/harbor/adapters/spider2-dbt/template/tests/test_dbt.py` | The verifier. Reads `/tests/config.json`, parses agent's `Terminate(output="...duckdb")` from `/logs/agent/spider-agent-dbt.trajectory.json`; if missing, falls back to `result_db` from config. Calls `duckdb_match(result_db, gold_db, condition_tabs, condition_cols, ignore_orders)`. The check is column-by-column: for each gold column it checks **whether some predicted column matches** (set membership over columns at the `condition_cols` indices). If any gold column has no match, returns 0. |
| `/home/shilin/T-Bench/harbor/adapters/spider2-dbt/template/tests/test.sh` | Wrapper that runs `python3 /tests/test_dbt.py` and writes 0/1 to `/logs/verifier/reward.txt`. **Does not** run dbt for the agent. |
| `/home/shilin/T-Bench/harbor/adapters/spider2-dbt/template/solution/solve.sh` | Oracle: just copies all gold tables verbatim into the result duckdb. Confirms the verifier is a pure table-equality check. |

## Generated task content (per Docent transcripts and the upstream Spider2 dbt-jira project)

These live inside the agent's container at `/workspace/` (built by the adapter from `examples/jira001/`). Inferred from the trajectories:

| Path | Role |
|---|---|
| `/workspace/dbt_project.yml` | dbt project config. Defines vars `project`, `user`, `component`, `jira_epic_identifier`, `jira_schema`, etc. (Fivetran "jira" package). |
| `/workspace/profiles.yml` | duckdb profile pointing at `*.duckdb` in `/workspace/`. |
| `/workspace/packages.yml` | Pulls `fivetran/jira` (sourced from `dbt_packages/jira_source/...`). |
| `/workspace/models/jira.yml` | **The 31-column contract** for `jira__project_enhanced`. Documents 30 columns (project_id, project_description, project_key, project_lead_user_id, project_name, permission_scheme_id, project_category_id, project_lead_user_name, project_lead_email, epics, components, count_closed_issues, count_open_issues, count_open_assigned_issues, plus avg/median × {close_time, assigned_close_time, age_currently_open, age_currently_open_assigned} × {seconds, days}). The 31st gold column (`_fivetran_synced`, a Fivetran passthrough) is NOT documented here — it is preserved in gold by selecting `project.*` from staging. |
| `/workspace/models/jira__issue_enhanced.sql` | Existing model — not what the verifier checks. |
| `/workspace/models/jira__user_enhanced.sql` | Existing model — same. |
| `/workspace/models/jira__daily_issue_field_history.sql` | Existing model. Depends transitively on the broken pivot model. |
| `/workspace/models/intermediate/int_jira__project_metrics.sql` | **All avg/median close-time and age metrics already implemented here**, in both seconds and days. The right `jira__project_enhanced.sql` just selects from this. |
| `/workspace/models/intermediate/int_jira__issue_join.sql`, `int_jira__issue_epic.sql`, `int_jira__issue_users.sql`, `int_jira__issue_type_parents.sql` | Other intermediate models (used as inputs). |
| `/workspace/models/intermediate/field_history/int_jira__pivot_daily_field_history.sql` | **Buggy under DuckDB ≥ ~1.10.** Fails with INTERNAL Error: `Failed to bind column reference "field_id" [320.0]: inequal types (VARCHAR != DATE)` because of a `row_number() over (partition by valid_starting_on, issue_id, field_id)` inside a CTE chain. This crash blocks the initial `dbt run`. None of the trajectories needed this output to satisfy the verifier (only `jira__project_enhanced` is checked), but every agent had to either fix it, work around it, or stub it. |
| `/workspace/models/jira__project_enhanced.sql` | **Does not exist initially.** Agents must create it. |
| `/tests/gold.duckdb` | Reference DB containing `jira__project_enhanced` with shape (3, 31). The 31st column not in `jira.yml` is `_fivetran_synced`. Not visible inside the agent container. |
| `/tests/config.json` | `{ result_db: "/workspace/jira_db.duckdb", gold_db: "/tests/gold.duckdb", condition_tabs: ["jira__project_enhanced"], condition_cols: [[]], ignore_orders: [...] }`. |

## What the gold table contains (reverse-engineered from the success trajectories)

3 rows, 31 columns. Project rows: `TP / Test Project`, `TCP / Scooby Doo`, `TBTP / <third>`. Epics for project 10001 = `"just for testing"` (= `summary` of the raw `epic` row, NOT `name`). Metrics for `TBTP` are NULL where it has no closed issues (gold does **not** coalesce to 0).

The 31 columns, in observed order in the success run (gemini-cli 2cfbb7b0):

```
project_description, project_id, project_key, project_lead_user_id, project_name,
project_category_id, permission_scheme_id, _fivetran_synced,
project_lead_user_name, project_lead_email,
epics, components,
count_closed_issues, count_open_issues, count_open_assigned_issues,
avg_close_time_seconds, avg_assigned_close_time_seconds,
avg_age_currently_open_seconds, avg_age_currently_open_assigned_seconds,
median_close_time_seconds, median_age_currently_open_seconds,
median_assigned_close_time_seconds, median_age_currently_open_assigned_seconds,
avg_close_time_days, avg_assigned_close_time_days,
avg_age_currently_open_days, avg_age_currently_open_assigned_days,
median_close_time_days, median_age_currently_open_days,
median_assigned_close_time_days, median_age_currently_open_assigned_days
```

`_fivetran_synced` is the column that is documented nowhere in `jira.yml` and is the most-common reason failure runs end up at (3, 30) instead of (3, 31). Agents that did `select project.*` got it for free; agents that enumerated `project.project_id, project.project_name, ...` lost it.
