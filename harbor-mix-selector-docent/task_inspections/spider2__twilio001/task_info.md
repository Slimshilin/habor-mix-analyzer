# Task Info: spider2/twilio001

## Basic Info
- **Benchmark**: spider2
- **Task**: twilio001
- **Checksum**: 891831f358683a63c17f1b0d49e808785fc8bd5b0529d50ac68108f183371e68
- **Result**: 4/18 (22%) — 4 successes, 14 failures, 0 infra exceptions
- **Gemini verdict**: accept (medium difficulty)
- **Author**: Yonghui Liu (Yonghui.Liu@anu.edu.au)
- **Tags**: dbt, duckdb, data-engineering, sql

## Task Description (instruction.md, verbatim)
```
# twilio001

## Task Description

Aggregate messaging data for Twilio, one at the phone number level and another
at the account level, including details like inbound/outbound message counts,
message statuses, and total spend.

## Environment

You are working with a dbt (data build tool) project that transforms data in a
DuckDB database. The project is located in `/workspace` with the following
structure:

- `dbt_project.yml` - dbt project configuration
- `profiles.yml` - Database connection profile (DuckDB)
- `models/` - SQL transformation models
- `*.duckdb` - Source database containing raw data

## Objective

Complete or fix the dbt models to produce the correct table outputs. Run
`dbt run` to execute the transformations.

## Execution Requirements

- Working directory: `/workspace`
- Run `dbt deps` first if there's a `packages.yml` file (to install dependencies)
- Run `dbt run` to execute all models
- The database file (`*.duckdb`) contains both source data and will store your model outputs
- You can inspect tables using: `duckdb <database>.duckdb -c "SELECT * FROM table_name LIMIT 10;"`
```

The instruction text is **deliberately abstract**: it never names the two output
tables, never names columns, never quantifies "details like". The scope is set
entirely by `models/twilio.yml` (a dbt schema YAML file shipped in the
workspace) and the gold DuckDB. So discoverability of the schema yaml and the
seed/staging tables is the entire challenge.

## Environment
- Image: `python:3.11-slim` + `dbt-duckdb>=1.7.0`, `duckdb>=0.9.0`, `pandas`,
  plus `openai/tiktoken/tenacity/gymnasium/rich`.
- Working dir: `/workspace` (pre-populated dbt project).
- Source DB: a DuckDB file under `/workspace` containing seed/source tables.
- Agent timeout: 1800 s. Verifier timeout: 600 s.

## Verifier (`/tests/test_dbt.py`, called from `test.sh`)
- Compares the agent's DuckDB output against `/tests/gold.duckdb`.
- Two condition tables (per `models/twilio.yml`):
  - `twilio__account_overview`
  - `twilio__number_overview`
- Comparison policy (from observed trajectories): equality of selected columns
  per table, with row-order tolerance (sorted compare).

## Trial distribution (18 trials, 4/18 success)
| Run id | Agent | Model | Steps | Reward |
|---|---|---|---|---|
| f954a649 | claude-code | claude-opus-4-6 | 35 | 0 |
| 4e95972e | claude-code | claude-opus-4-6 | 29 | 0 |
| 4546d1e9 | claude-code | claude-opus-4-6 | 40 | 0 |
| 26357997 | codex | gpt-5.4 | 61 | 0 |
| 381ddd12 | codex | gpt-5.4 | 71 | 0 |
| **9b5bb0fa** | **codex** | **gpt-5.4** | **86** | **1** |
| **90366d08** | **gemini-cli** | **gemini-3.1-pro-preview** | **57** | **1** |
| 6ca91a93 | gemini-cli | gemini-3.1-pro-preview | 36 | 0 |
| **68dadb7f** | **gemini-cli** | **gemini-3.1-pro-preview** | **33** | **1** |
| edb209f0 | terminus-2 | claude-opus-4-6 | – | 0 |
| 9084d5c4 | terminus-2 | claude-opus-4-6 | – | 0 |
| 87f0fad8 | terminus-2 | claude-opus-4-6 | – | 0 |
| af58812a | terminus-2 | gemini-3.1-pro-preview | – | 0 |
| **1e81f958** | **terminus-2** | **gemini-3.1-pro-preview** | – | **1** |
| 41a70726 | terminus-2 | gemini-3.1-pro-preview | – | 0 |
| ba43df53 | terminus-2 | gpt-5.4 | – | 0 |
| 2481a4bf | terminus-2 | gpt-5.4 | – | 0 |
| dc828a9c | terminus-2 | gpt-5.4 | – | 0 |

Per-agent success rate:
- claude-code (opus-4-6): 0/3
- codex (gpt-5.4): 1/3
- gemini-cli (gemini-3.1-pro): 2/3
- terminus-2 (opus-4-6): 0/3
- terminus-2 (gemini-3.1-pro): 1/3
- terminus-2 (gpt-5.4): 0/3
Total: **4/18**.

## Key files in this directory
- `task_info.md` — this file: ground-truth task surface (instruction, verifier, env, trials).
- `task_inspection.md` — per-trajectory analysis, surface-vs-root-cause, fix
  proposals, and final verdict on whether failures point to the task or to
  agent capability bottlenecks.

## Docent links
- Collection dashboard: https://docent.transluce.org/dashboard/640e920a-aef3-4b7c-9487-69899ef19e9d
- Per-run links are listed in `task_inspection.md`.
