from __future__ import annotations

import json
from pathlib import Path

from docent.sdk.client import Docent


COLLECTION_ID = "640e920a-aef3-4b7c-9487-69899ef19e9d"
TASK_NAME = "featurebench-modal/mlflow__mlflow.93dab383.test_judge_tool_search_traces.cad8fc4b.lv1"
OUT = Path(__file__).parent


def write_json(path: Path, obj) -> None:
    path.write_text(json.dumps(obj, indent=2, sort_keys=True), encoding="utf-8")


def main() -> None:
    client = Docent.from_url(f"https://docent.transluce.org/dashboard/{COLLECTION_ID}")

    runs_query = f"""
    SELECT
      id,
      metadata_json->'run'->>'agent' AS agent,
      metadata_json->'run'->>'model' AS model,
      metadata_json->'run'->>'reward' AS reward,
      metadata_json->'run'->>'exception_type' AS exception_type,
      metadata_json->'run'->>'trial_id' AS trial_id,
      metadata_json->>'task_checksum' AS task_checksum,
      metadata_json->>'n_succ' AS n_succ
    FROM agent_runs
    WHERE metadata_json->>'task_name' = '{TASK_NAME}'
    ORDER BY agent, model, id
    """
    runs_result = client.execute_dql(COLLECTION_ID, runs_query)
    columns = runs_result["columns"]
    runs = [dict(zip(columns, row)) for row in runs_result["rows"]]
    write_json(OUT / "run_metadata.json", {"columns": columns, "runs": runs})

    if not runs:
        raise SystemExit("No runs found")

    first_run = runs[0]["id"]
    payload_query = f"""
    SELECT
      metadata_json->>'task_name' AS task_name,
      metadata_json->>'benchmark' AS benchmark,
      metadata_json->>'task_checksum' AS task_checksum,
      metadata_json->'task'->>'instruction' AS instruction,
      metadata_json->'task'->>'test_sh' AS test_sh,
      metadata_json->'task'->>'solve_sh' AS solve_sh,
      metadata_json->'task'->>'dockerfile' AS dockerfile,
      metadata_json->'task'->>'task_toml' AS task_toml
    FROM agent_runs
    WHERE id = '{first_run}'
    """
    payload_result = client.execute_dql(COLLECTION_ID, payload_query)
    payload = dict(zip(payload_result["columns"], payload_result["rows"][0]))
    write_json(OUT / "task_payload.json", payload)

    stdout_dir = OUT / "test_stdout"
    stdout_dir.mkdir(exist_ok=True)
    stdout_query = f"""
    SELECT id, metadata_json->'run'->>'test_stdout' AS test_stdout
    FROM agent_runs
    WHERE metadata_json->>'task_name' = '{TASK_NAME}'
    ORDER BY id
    """
    stdout_result = client.execute_dql(COLLECTION_ID, stdout_query)
    for run_id, stdout in stdout_result["rows"]:
        (stdout_dir / f"{run_id}.txt").write_text(stdout or "", encoding="utf-8")

    transcript_query = f"""
    SELECT id, agent_run_id, name, metadata_json
    FROM transcripts
    WHERE agent_run_id IN ({",".join("'" + run["id"] + "'" for run in runs)})
    ORDER BY agent_run_id, name
    """
    transcripts_result = client.execute_dql(COLLECTION_ID, transcript_query)
    write_json(
        OUT / "transcripts_index.json",
        {
            "columns": transcripts_result["columns"],
            "rows": transcripts_result["rows"],
        },
    )


if __name__ == "__main__":
    main()
