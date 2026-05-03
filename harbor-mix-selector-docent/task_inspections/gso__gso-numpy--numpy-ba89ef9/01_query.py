"""DQL queries used during this task inspection.

These were primarily driven via the Docent MCP `execute_dql` tool while
exploring the run; this file captures the queries for reference / reproduction.
"""

# Run metadata for the 18 trajectories tied to the audit URLs.
RUNS_META_DQL = """
SELECT id AS run_id,
       metadata_json->'task_name' AS task_name,
       metadata_json->'run'->>'agent' AS agent,
       metadata_json->'run'->>'model' AS model,
       metadata_json->'run'->>'role' AS role
FROM agent_runs
WHERE id IN (...18 ids...)
"""

# Task instruction, dockerfile, test_sh, solve_sh sit on every run; one row is enough.
TASK_FIELDS_DQL = """
SELECT metadata_json->'task'->>'instruction' AS instruction,
       metadata_json->'task'->>'test_sh' AS test_sh,
       metadata_json->'task'->>'solve_sh' AS solve_sh,
       metadata_json->'task'->>'dockerfile' AS dockerfile
FROM agent_runs
WHERE id = '191225fc-9e49-4f59-9100-216c6a5a6d23'
"""

# Compare the agent's End Patch Output vs. the oracle's End Commit Output for
# success vs. failure runs to ground the relative-grader story.
EVAL_LOG_BOUNDARIES_DQL = """
SELECT id AS run_id,
       POSITION('End Patch Output'  IN metadata_json->'run'->>'test_stdout') AS end_patch_pos,
       POSITION('End Commit Output' IN metadata_json->'run'->>'test_stdout') AS end_commit_pos,
       SUBSTRING(metadata_json->'run'->>'test_stdout' FROM POSITION('End Patch Output' IN metadata_json->'run'->>'test_stdout') - 200 FOR 250) AS at_end_patch
FROM agent_runs
WHERE id IN (
  '191225fc-9e49-4f59-9100-216c6a5a6d23',  -- success
  '127d0978-dbfd-4c6a-8314-e3637878390e'   -- failure
)
"""
