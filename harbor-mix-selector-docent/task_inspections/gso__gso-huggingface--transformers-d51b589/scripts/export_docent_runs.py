from __future__ import annotations

import json
import re
from pathlib import Path

from docent.sdk.client import Docent


COLLECTION_ID = "640e920a-aef3-4b7c-9487-69899ef19e9d"
FRONTEND = "https://docent.transluce.org"
RUN_IDS = [
    "236f65af-f4cd-40ce-bdda-d1a4a719fc2d",
    "d7d08d07-0af4-4c9d-b715-b058252ac31b",
    "d95b48df-8509-4eea-8562-35bb9efb5ebd",
    "4953ac7f-8f89-4db5-8b3e-fc3cf6134761",
    "451754ae-9652-4e51-ac51-f3a9dcdd23dc",
    "ae213a72-87f0-40b4-afae-c6693a9c065a",
    "ba991cb0-ef99-4ea7-bd3a-03e6d4a1d986",
    "1ffa220f-5c84-402c-9da5-e3d91f48ebed",
    "d7d0c912-41d0-49ac-9484-c7073c9e4a53",
    "80a830ba-136e-4023-abe1-93a01901d1a6",
    "0ab62377-6255-48a1-a244-a50e75ad27d8",
    "aee198f4-7530-480f-915a-debb9cf5ea75",
    "d1ad3d5d-9274-4e02-b8e7-7cacdeb6203a",
    "9148ca56-d8af-42fd-a253-7030afa91ba9",
    "eb6dd332-1f62-4e73-9ce5-80fe1ae2d8dc",
    "3cf78940-cbca-4487-878d-49aa7f4de6ec",
    "70a74a59-3a34-498c-b9f4-0c2067cb2648",
    "4ad8a3b8-a9dd-494b-b583-05ec1f06afd0",
]

ROOT = Path(__file__).resolve().parents[1]
TRAJ_DIR = ROOT / "trajectories"
STDOUT_DIR = ROOT / "test_stdout"
TASK_DIR = ROOT / "task_files"


def jsonable(obj):
    if hasattr(obj, "model_dump"):
        return obj.model_dump(mode="json")
    if hasattr(obj, "dict"):
        return obj.dict()
    if isinstance(obj, dict):
        return {k: jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [jsonable(v) for v in obj]
    if hasattr(obj, "__dict__"):
        return {k: jsonable(v) for k, v in vars(obj).items()}
    return obj


def content_to_text(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            data = jsonable(item)
            if isinstance(data, dict):
                if data.get("type") == "text":
                    parts.append(data.get("text", ""))
                elif data.get("type") == "reasoning":
                    parts.append("[reasoning]\n" + (data.get("reasoning") or data.get("summary") or ""))
                else:
                    parts.append(json.dumps(data, ensure_ascii=False))
            else:
                parts.append(str(data))
        return "\n".join(part for part in parts if part)
    return str(content)


def safe_stem(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", text)


def write_task_files(task: dict) -> None:
    TASK_DIR.mkdir(parents=True, exist_ok=True)
    for key, name in {
        "instruction": "instruction.md",
        "test_sh": "test.sh",
        "solve_sh": "solve.sh",
        "task_toml": "task.toml",
        "dockerfile": "Dockerfile",
    }.items():
        value = task.get(key)
        if value is not None:
            (TASK_DIR / name).write_text(str(value), encoding="utf-8")
    (TASK_DIR / "task_payload.json").write_text(json.dumps(task, indent=2, sort_keys=True), encoding="utf-8")


def main() -> None:
    client = Docent.from_url(f"{FRONTEND}/dashboard/{COLLECTION_ID}")
    TRAJ_DIR.mkdir(parents=True, exist_ok=True)
    STDOUT_DIR.mkdir(parents=True, exist_ok=True)

    summaries = []
    task_written = False
    for idx, run_id in enumerate(RUN_IDS, start=1):
        run = client.get_agent_run(COLLECTION_ID, run_id)
        metadata = client.get_agent_run_metadata(COLLECTION_ID, run_id)
        run_meta = metadata.get("run", {})
        task = metadata.get("task", {})
        if task and not task_written:
            write_task_files(task)
            task_written = True

        transcript_count = len(run.transcripts)
        message_count = sum(len(t.messages) for t in run.transcripts)
        summary = {
            "idx": idx,
            "run_id": run_id,
            "url": f"{FRONTEND}/dashboard/{COLLECTION_ID}/agent_run/{run_id}",
            "agent": run_meta.get("agent"),
            "model": run_meta.get("model"),
            "role": run_meta.get("role"),
            "reward": run_meta.get("reward"),
            "trial_id": run_meta.get("trial_id"),
            "exception_type": run_meta.get("exception_type"),
            "total_steps": run_meta.get("total_steps"),
            "transcript_count": transcript_count,
            "message_count": message_count,
        }
        summaries.append(summary)

        stem = safe_stem(f"{idx:02d}_{run_meta.get('agent')}_{run_meta.get('model')}_{run_id[:8]}")
        (STDOUT_DIR / f"{stem}.txt").write_text(run_meta.get("test_stdout") or "", encoding="utf-8")
        (ROOT / f"metadata_{stem}.json").write_text(json.dumps(metadata, indent=2, sort_keys=True), encoding="utf-8")

        md = [
            f"# Run {idx:02d}: {run_meta.get('agent')} / {run_meta.get('model')}",
            "",
            f"- URL: {FRONTEND}/dashboard/{COLLECTION_ID}/agent_run/{run_id}",
            f"- Reward: {run_meta.get('reward')}",
            f"- Trial: {run_meta.get('trial_id')}",
            f"- Exception: {run_meta.get('exception_type')}",
            f"- Total steps: {run_meta.get('total_steps')}",
            "",
        ]
        raw = jsonable(run)
        for transcript in run.transcripts:
            md.extend([f"## Transcript `{transcript.name}` / `{transcript.id}`", ""])
            for block_idx, message in enumerate(transcript.messages):
                text = content_to_text(message.content)
                tool_calls = jsonable(getattr(message, "tool_calls", None) or [])
                md.extend([f"### Block {block_idx}: {message.role}", ""])
                if tool_calls:
                    md.extend(["Tool calls:", "```json", json.dumps(tool_calls, indent=2), "```", ""])
                md.extend([text, ""])

        (TRAJ_DIR / f"{stem}.md").write_text("\n".join(md), encoding="utf-8")
        (TRAJ_DIR / f"{stem}.json").write_text(json.dumps({"summary": summary, "run": raw}, indent=2), encoding="utf-8")

    (ROOT / "run_summaries.json").write_text(json.dumps(summaries, indent=2), encoding="utf-8")
    print(json.dumps(summaries, indent=2))


if __name__ == "__main__":
    main()
