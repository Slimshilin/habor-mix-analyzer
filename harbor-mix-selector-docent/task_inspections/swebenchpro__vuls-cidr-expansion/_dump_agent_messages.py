"""Dump per-run last assistant messages and bash blocks looking for `enumerateHosts` / `hosts` / `iplib`.

The goal is to capture what each agent actually wrote without scrolling 18 trajectories by hand.
"""
from docent.sdk.client import Docent
import os, json, re, sys

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

# Try messages api via MCP-equivalent call
out_dir = os.path.join(OUT, "agent_messages")
os.makedirs(out_dir, exist_ok=True)

for rid in RUN_IDS:
    try:
        msgs = client.get_agent_run_messages(collection_id=COL, agent_run_id=rid)
    except Exception as e:
        print(f"{rid[:8]} failed: {e}")
        continue
    fname = os.path.join(out_dir, f"{rid}.json")
    with open(fname, "w") as f:
        json.dump(msgs, f, indent=2, default=str)
    print(f"{rid[:8]} wrote {len(msgs)} message bundle")
