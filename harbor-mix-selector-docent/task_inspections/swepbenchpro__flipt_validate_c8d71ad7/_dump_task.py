"""Dump task fields for the flipt-validate (c8d71ad7) instance to disk."""
from docent.sdk.client import Docent
import os

OUT = os.path.dirname(os.path.abspath(__file__))
COL = "640e920a-aef3-4b7c-9487-69899ef19e9d"
RUN = "e5662348-4405-4893-a84f-b3d734928059"  # codex run, best so far (5/8)

client = Docent.from_url(f"https://docent.transluce.org/dashboard/{COL}")
res = client.execute_dql(
    collection_id=COL,
    dql=(
        "SELECT metadata_json->'task'->>'instruction' AS instruction, "
        "metadata_json->'task'->>'solve_sh'    AS solve_sh, "
        "metadata_json->'task'->>'test_sh'     AS test_sh, "
        "metadata_json->'task'->>'task_toml'   AS task_toml, "
        "metadata_json->'task'->>'dockerfile'  AS dockerfile "
        f"FROM agent_runs WHERE id = '{RUN}' LIMIT 1"
    ),
)
cols = res["columns"]
row = res["rows"][0]
data = dict(zip(cols, row))
for k, v in data.items():
    fname = os.path.join(OUT, f"_raw_{k}.txt")
    with open(fname, "w") as f:
        f.write(v if v is not None else "")
    print(f"wrote {fname} ({len(v) if v else 0} chars)")
