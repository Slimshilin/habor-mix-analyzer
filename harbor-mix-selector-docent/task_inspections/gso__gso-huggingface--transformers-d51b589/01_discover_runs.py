from __future__ import annotations

import json
from pathlib import Path

from docent.sdk.client import Docent


COLLECTION_ID = "640e920a-aef3-4b7c-9487-69899ef19e9d"
TASK_NAME = "gso/gso-huggingface--transformers-d51b589"
INSTANCE_ID = "huggingface__transformers-d51b589"

ROOT = Path(__file__).resolve().parent


def main() -> None:
    client = Docent.from_url(f"https://docent.transluce.org/dashboard/{COLLECTION_ID}")
    query = f"""
    SELECT id AS run_id,
           metadata_json->>'task_name' AS task_name,
           metadata_json->'task'->>'instance_id' AS instance_id,
           metadata_json->'run'->>'agent' AS agent,
           metadata_json->'run'->>'model' AS model,
           metadata_json->'run'->>'role' AS role,
           metadata_json->'run'->>'reward' AS reward,
           metadata_json->'run'->>'trial_id' AS trial_id,
           metadata_json->'run'->>'opt_commit' AS opt_commit,
           metadata_json->'run'->>'patch_size' AS patch_size
    FROM agent_runs
    WHERE metadata_json->>'task_name' = '{TASK_NAME}'
       OR metadata_json->'task'->>'instance_id' = '{INSTANCE_ID}'
       OR metadata_json::text LIKE '%d51b589%'
    ORDER BY agent, model, run_id
    """
    rows = client.execute_dql(COLLECTION_ID, query)
    columns = rows["columns"] if isinstance(rows, dict) else getattr(rows, "columns", [])
    raw_rows = rows["rows"] if isinstance(rows, dict) else getattr(rows, "rows", rows)
    json_rows = [
        row.model_dump(mode="json")
        if hasattr(row, "model_dump")
        else dict(zip(columns, row))
        if not isinstance(row, dict)
        else row
        for row in raw_rows
    ]
    (ROOT / "discovered_runs.json").write_text(json.dumps(json_rows, indent=2), encoding="utf-8")
    print(json.dumps(json_rows, indent=2))


if __name__ == "__main__":
    main()
