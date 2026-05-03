"""Dump per-run metadata + test stdouts for all 18 vuls runs."""
from docent.sdk.client import Docent
import os, json

OUT = os.path.dirname(os.path.abspath(__file__))
COL = "640e920a-aef3-4b7c-9487-69899ef19e9d"
RUN_IDS = [
    "d3ec08e4-5ed6-4f99-a06c-9c6bece11b8d",
    "8e63cfcb-56b6-4f1f-abbe-1f261fac4709",
    "884a3495-1561-425f-a519-5589ef14ac2e",
    "25e11d86-4b91-425d-b3aa-2dfb0adb5f1a",
    "8090e1f2-72cc-4765-a213-42138aecac3a",
    "98cf9be8-6efb-4af2-aedd-ae64d4c7e9bb",
    "11a8e3ca-2172-4208-9f02-bd0b0131657b",
    "6e5c4d68-00b4-4bc7-9550-e225c513b92b",
    "935b273d-9be6-4fd1-95ed-05e48917e397",
    "b2b27972-6c98-4ed0-a2ea-beebb930ed1d",
    "2bf4556d-8d15-49fe-be10-d490e62c5703",
    "1d292b62-5b62-4ecb-b36b-134e356e74df",
    "4bc7d10e-c2c9-450d-a9c7-3ba4c915312c",
    "a2590785-c8be-40bf-9728-c20e3993a838",
    "893f17d3-a5a9-4945-a9dc-3427628fa27a",
    "8a2cc8c4-6043-4187-b8af-4052ffa70a04",
    "0131b9a4-0867-4ce0-bafc-6246e07dce47",
    "b0a4652a-9fba-4a71-ad1b-02c3260470bd",
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
