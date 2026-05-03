"""Page through solve_sh in 7000-char chunks to bypass SDK truncation."""
from docent.sdk.client import Docent
import os

OUT = os.path.dirname(os.path.abspath(__file__))
COL = "640e920a-aef3-4b7c-9487-69899ef19e9d"
RUN = "e4d82317-9e57-4d65-a1c1-69186ff156d5"

client = Docent.from_url(f"https://docent.transluce.org/dashboard/{COL}")

chunks = []
offset = 1
chunk_size = 7000
while True:
    res = client.execute_dql(
        collection_id=COL,
        dql=(
            f"SELECT SUBSTRING(metadata_json->'task'->>'solve_sh' FROM {offset} FOR {chunk_size}) AS chunk, "
            f"LENGTH(metadata_json->'task'->>'solve_sh') AS total_len "
            f"FROM agent_runs WHERE id = '{RUN}' LIMIT 1"
        ),
    )
    chunk, total = res["rows"][0]
    if not chunk:
        break
    chunks.append(chunk)
    print(f"offset={offset} got={len(chunk)} total_len={total}")
    if offset + len(chunk) - 1 >= total:
        break
    offset += len(chunk)

full = "".join(chunks)
with open(os.path.join(OUT, "gold_patch_full_solve_sh.txt"), "w") as f:
    f.write(full)
print(f"FULL LEN: {len(full)}")
