"""Dump per-run model/agent/reward/test_stdout for all 18 trial runs."""
from docent.sdk.client import Docent
import os, json

OUT = os.path.dirname(os.path.abspath(__file__))
os.makedirs(os.path.join(OUT, "test_stdouts"), exist_ok=True)
COL = "640e920a-aef3-4b7c-9487-69899ef19e9d"

RUN_IDS = [
    "21da9bb6-e49f-4de7-a7d5-4db9337a9149",
    "ccaa50e9-e115-41bc-86d7-6ccfcb07c6a0",
    "9e8da770-fb5d-4d1f-8027-abe012817bf5",
    "512520b0-c555-423c-83a8-76e03c8af5cf",
    "aec30231-a728-4634-bb78-1ea690044f60",
    "c1579e91-1190-4d5b-b6dc-d84e3065f5ce",
    "d9961e66-509f-4c9d-9fed-9caaa5e4b543",
    "3cee04c0-6088-4925-8930-1575713b8f9d",
    "e5662348-4405-4893-a84f-b3d734928059",
    "299da343-f4dc-4e70-8d2b-b21ee926475a",
    "f1261115-9fb4-4b57-a464-08121d54796b",
    "b553ccdd-3653-4ebb-a090-6ddbde351d82",
    "dfc96d46-15ae-4a4d-b4f6-0a9b544609e6",
    "68700f01-dfb4-491b-851c-79e1856c2ea7",
    "66a3c025-f9c5-4f89-b2d2-8b519b41bf47",
    "99826d2d-82e9-4732-b088-1a0fb591f801",
    "3fab2ac0-d827-473c-9460-966b18ea154c",
    "dc90550f-b733-476c-878c-972c8313bbd1",
]

client = Docent.from_url(f"https://docent.transluce.org/dashboard/{COL}")

ids_csv = ",".join(f"'{r}'" for r in RUN_IDS)
res = client.execute_dql(
    collection_id=COL,
    dql=(
        "SELECT id, "
        "metadata_json->'run'->>'agent'  AS agent, "
        "metadata_json->'run'->>'model'  AS model, "
        "metadata_json->'run'->>'reward' AS reward, "
        "metadata_json->'run'->>'role'   AS role, "
        "metadata_json->'run'->>'trial_id' AS trial_id, "
        "metadata_json->>'task_name' AS task_name, "
        "metadata_json->>'task_checksum' AS task_checksum "
        f"FROM agent_runs WHERE id IN ({ids_csv})"
    ),
)
cols = res["columns"]
summary = []
for row in res["rows"]:
    d = dict(zip(cols, row))
    summary.append(d)

with open(os.path.join(OUT, "runs_summary.json"), "w") as f:
    json.dump(summary, f, indent=2)
print(f"wrote {os.path.join(OUT, 'runs_summary.json')} ({len(summary)} rows)")

# Pull verifier stdout per run
for run_id in RUN_IDS:
    res = client.execute_dql(
        collection_id=COL,
        dql=(
            "SELECT metadata_json->'run'->>'test_stdout' AS test_stdout, "
            "metadata_json->'run'->>'agent' AS agent, "
            "metadata_json->'run'->>'model' AS model, "
            "metadata_json->'run'->>'reward' AS reward, "
            "metadata_json->'run'->>'exception_type' AS exception_type "
            f"FROM agent_runs WHERE id = '{run_id}' LIMIT 1"
        ),
    )
    if not res["rows"]:
        continue
    d = dict(zip(res["columns"], res["rows"][0]))
    fname = os.path.join(OUT, "test_stdouts", f"{run_id}__verifier.txt")
    with open(fname, "w") as f:
        f.write(f"# agent={d.get('agent')} model={d.get('model')} reward={d.get('reward')} exc={d.get('exception_type')}\n\n")
        f.write(d.get("test_stdout") or "(no test_stdout)")
    print(f"wrote {fname} ({len(d.get('test_stdout') or '')} chars)")
