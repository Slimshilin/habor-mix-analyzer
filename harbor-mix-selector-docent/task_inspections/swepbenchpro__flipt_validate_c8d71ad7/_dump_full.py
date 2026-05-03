"""Dump full task fields & verifier config for the flipt-validate (c8d71ad7) instance."""
from docent.sdk.client import Docent
import os

OUT = os.path.dirname(os.path.abspath(__file__))
COL = "640e920a-aef3-4b7c-9487-69899ef19e9d"
RUN = "e5662348-4405-4893-a84f-b3d734928059"  # codex run, best so far

client = Docent.from_url(f"https://docent.transluce.org/dashboard/{COL}")

# Cast jsonb to text and write directly. Long fields - get full content as separate queries
candidate_keys = [
    "instruction", "solve_sh", "test_sh", "task_toml", "dockerfile",
    "config_json", "config", "before_repo_set_cmd",
    "fail_to_pass", "pass_to_pass", "selected_test_files_to_run",
    "gold_patch", "test_patch", "patch", "golden_patch",
    "FAIL_TO_PASS", "PASS_TO_PASS",
]

for k in candidate_keys:
    try:
        sub = client.execute_dql(
            collection_id=COL,
            dql=(
                f"SELECT metadata_json->'task'->>'{k}' AS v "
                f"FROM agent_runs WHERE id = '{RUN}' LIMIT 1"
            ),
        )
        v = sub["rows"][0][0] if sub["rows"] else None
        if not v:
            continue
        fname = os.path.join(OUT, f"_task_{k}.txt")
        with open(fname, "w") as f:
            f.write(v)
        print(f"wrote {fname} ({len(v)} chars)")
    except Exception as e:
        print(f"skip task->{k}: {e}")

# Top-level metadata fields too
for k in ["agent_name", "model_name", "model", "agent", "scoring",
          "score", "reward", "exit_status", "trial_id", "task_id",
          "instance_id", "passed_tests", "failed_tests", "fail_to_pass",
          "pass_to_pass", "test_results", "verifier_output"]:
    try:
        sub = client.execute_dql(
            collection_id=COL,
            dql=(
                f"SELECT metadata_json->>'{k}' AS v "
                f"FROM agent_runs WHERE id = '{RUN}' LIMIT 1"
            ),
        )
        v = sub["rows"][0][0] if sub["rows"] else None
        if not v:
            continue
        fname = os.path.join(OUT, f"_meta_{k}.txt")
        with open(fname, "w") as f:
            f.write(v)
        print(f"wrote {fname} ({len(v)} chars)")
    except Exception as e:
        print(f"skip top->{k}: {e}")
