from __future__ import annotations

import json
import re
from pathlib import Path

from docent.sdk.client import Docent


COLLECTION_ID = "640e920a-aef3-4b7c-9487-69899ef19e9d"
FRONTEND = "https://docent.transluce.org"
RUN_IDS = [
    "19b9442d-ae8a-4e77-992c-29d50736bc54",
    "980b7fda-8273-42fc-8dc0-271f3046b965",
    "f713d415-a3f8-4377-87a7-15a4584df8d1",
    "832fb29d-1b98-417a-85b1-9346ebe93981",
    "6f9577a6-64b2-4946-9920-f24d7c976e58",
    "b2a38d2d-e444-43c2-bed8-73650a2a0e79",
    "d8872b3a-a8ac-49c3-97fb-17101a59a24f",
    "2e70536e-a5ac-42b8-9913-566e35132f6b",
    "86156a24-2210-4405-8490-ddc11664cabc",
    "35fbb005-8e97-4e31-b687-2a9705f57875",
    "cf90d6d7-21bf-4e04-8a05-24d640329ff5",
    "1f7ea0fc-62db-4fd7-8c6d-002fec298bd9",
    "ef123134-3265-40cf-bb31-fc70ba11d480",
    "27264558-50cf-4cb7-93ce-850b8f9a6295",
    "e4a59aff-4ad8-4d19-a6e6-f842c96b3766",
    "1ace91ca-0bf5-4a6c-a298-6614f8a81cf3",
    "4fc922a1-8180-4651-a352-66bbbdb5a428",
    "6f69a5bb-f1ab-457d-b4cd-66567cb87f5a",
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
