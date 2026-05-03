"""Dump per-run metadata + test stdouts for all 18 teleport runs."""
from docent.sdk.client import Docent
import os, json

OUT = os.path.dirname(os.path.abspath(__file__))
COL = "640e920a-aef3-4b7c-9487-69899ef19e9d"
RUN_IDS = [
    "e4d82317-9e57-4d65-a1c1-69186ff156d5",
    "c875aa2e-219c-474b-b918-fa58ac026d39",
    "5db1b402-08f3-433d-b21c-4952335ecd2d",
    "a6bd191b-a2e1-42dc-9d46-3d6f768cc009",
    "3201fb14-6307-45eb-a9d8-742fe194904f",
    "291f680b-4b19-4564-b744-6e0dc207d1c9",
    "4aef1e57-ac02-4cf4-888a-36f70e4585d0",
    "22f80a22-90fd-4237-84ba-c057bf891525",
    "c08801f8-6980-43fd-8560-0ac7b98c9cec",
    "cf286d60-e421-45ec-9243-b537d9aaa897",
    "315401c2-9ad1-48ff-a7e3-2cf219593e75",
    "8645bf19-58ce-4e66-b696-7985e73d31d6",
    "7097c8b6-5c72-41b8-98e8-b0003067bac3",
    "6c4bff86-e43e-4118-ad0b-494eb215710f",
    "0e6c4aa6-fa14-4835-afc8-bd6224809f98",
    "ad5ac085-a8ee-4b23-a5da-dd64c8771295",
]

client = Docent.from_url(f"https://docent.transluce.org/dashboard/{COL}")

stdout_dir = os.path.join(OUT, "test_stdouts")
os.makedirs(stdout_dir, exist_ok=True)

quoted = ",".join(f"'{r}'" for r in RUN_IDS)
res = client.execute_dql(
    collection_id=COL,
    dql=(
        "SELECT id, "
        "metadata_json->'run'->>'agent' AS agent, "
        "metadata_json->'run'->>'model' AS model, "
        "metadata_json->'run'->>'exception_type' AS exception, "
        "metadata_json->'run'->>'reward' AS reward, "
        "metadata_json->'run'->>'role' AS role, "
        "metadata_json->'run'->>'test_stdout' AS test_stdout, "
        "metadata_json->>'n_succ' AS n_succ "
        f"FROM agent_runs WHERE id IN ({quoted})"
    ),
)
cols = res["columns"]
summary = []
for row in res["rows"]:
    rec = dict(zip(cols, row))
    rid = rec["id"]
    agent = rec.get("agent") or "unknown"
    model = (rec.get("model") or "unknown").replace("/", "_")
    stdout = rec.get("test_stdout") or ""
    fname = os.path.join(stdout_dir, f"{rid}__{agent}__{model}.txt")
    with open(fname, "w") as f:
        f.write(stdout)
    summary.append(
        {
            "id": rid,
            "agent": agent,
            "model": rec.get("model"),
            "exception": rec.get("exception"),
            "reward": rec.get("reward"),
            "role": rec.get("role"),
            "stdout_len": len(stdout),
            "file": fname,
        }
    )
    print(f"{rid[:8]} agent={agent:14s} model={(rec.get('model') or '?'):30s} reward={rec.get('reward')} exc={rec.get('exception')} stdout={len(stdout)}")

print(f"\nFound {len(summary)} of {len(RUN_IDS)} runs")
missing = set(RUN_IDS) - {r["id"] for r in summary}
if missing:
    print(f"MISSING: {missing}")

with open(os.path.join(OUT, "runs_summary.json"), "w") as f:
    json.dump(summary, f, indent=2)
