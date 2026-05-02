# Task Info: spider2/social_media001

## Basic Info
- **Benchmark**: spider2
- **Task**: social_media001
- **Checksum**: 670ff38c73bcfdd48fd005a0f2b38d40998730ad2ce8a9f76bba4206f3729f47
- **Result**: 0/18 (0% success)
- **Gemini verdict**: accept
- **Difficulty**: medium (per task.toml)
- **Tags**: dbt, duckdb, data-engineering, sql

## Task Description
Complete a dbt project to generate a social media reporting dashboard covering **4 platforms**: Facebook, Instagram, LinkedIn, and Twitter.

## Environment
- Docker: python:3.11-slim + dbt-duckdb>=1.7.0 + duckdb>=0.9.0
- Working dir: `/workspace` (pre-populated dbt project)
- Source DB: `social_media.duckdb`
- Agent timeout: 1800s; Verifier timeout: 600s

## Instruction (verbatim)
```
Complete or fix the dbt models to produce the correct table outputs. Run dbt run to execute the transformations.
- Run dbt deps first if there's a packages.yml file
- Run dbt run to execute all models
- Inspect tables using: duckdb <database>.duckdb -c "SELECT * FROM table_name LIMIT 10;"
```

## Verifier
Runs `/tests/test_dbt.py` which compares 3 tables against `/tests/gold.duckdb`:

| Table | Columns Checked (indices) | Gold Shape |
|---|---|---|
| `social_media_reporting__instagram_posts_reporting` | [0,1,3,4,5,7,8,9,10] | (3, 11) |
| `social_media_reporting__twitter_posts_reporting` | [0,1,3,5,7] | (100, 13) |
| `social_media_reporting__rollup_report` | [1,2,3,4,6,8,9,10,11,12,13] | (180, 14) |

Note: Verifier stops at first failing table (sequential comparison).

## Trial Distribution
| Model | Agent | Run IDs |
|---|---|---|
| claude-opus-4-6 | claude-code | 655dbf55, 93ee02ec, 14ef67cb |
| claude-opus-4-6 | terminus-2 | 5fed6814, df7fc083, 2d4505d3 |
| gemini-3.1-pro-preview | gemini-cli | a1eb8e36, 7a638e46, 387fc8d0 |
| gemini-3.1-pro-preview | terminus-2 | bf690492, b54d6fff, f531e9e5 |
| gpt-5.4 | codex | f8521297, c36d91b4, 99898ba2 |
| gpt-5.4 | terminus-2 | dd2ff0ab, c5a1052c, 4dcb284a |
