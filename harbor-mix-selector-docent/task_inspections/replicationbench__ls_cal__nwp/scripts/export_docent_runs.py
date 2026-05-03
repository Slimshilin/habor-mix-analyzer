from __future__ import annotations

import json
import re
from pathlib import Path

from docent.sdk.client import Docent


COLLECTION_ID = "640e920a-aef3-4b7c-9487-69899ef19e9d"
FRONTEND = "https://docent.transluce.org"
RUN_IDS = [
    "59f970f4-3a44-4847-a3e3-44b11c7576fb",
    "3835c984-9ad6-48ce-a1f4-357b9e1cd307",
    "456ddd09-ca17-488f-b312-d169e4ddc32d",
    "5dfb31c6-c0bd-4806-8967-f925ef0d4ede",
    "76918009-469a-4131-b763-e41d7e03c95f",
    "e6075cbc-8a13-4664-ade0-839637996f86",
    "01c8a98e-4dbf-49d4-bda5-1464ea2a85d1",
    "02501ee6-75ee-43a8-bef9-a0411c3cd63a",
    "fe264e03-2683-4fdb-9a9e-4b7ff7275af6",
    "6ee66b74-5d13-4aab-a3d6-9de751c89725",
    "f00e76b7-cad5-40c2-9e12-0bece4077730",
    "67ca71ae-c3a4-4b8c-854a-18c93c974f65",
    "05795219-84c5-490e-a216-25349b253a67",
    "2279415c-31b0-48b9-80d3-a625326852c2",
    "2c525c6e-9b38-4e19-8304-bd26f56bc8d1",
    "dfd339ac-6ec5-4b88-925d-eaaa8f91ed94",
    "37742491-90ed-4e66-9618-45a732eb9715",
    "49bd7bec-c7ca-4a0e-9b8a-5e7dcb646143",
]

ROOT = Path(__file__).resolve().parents[1]
RUN_DIR = ROOT / "runs"
TASK_DIR = ROOT / "task_files"
EXPECTED = [264.3, 57.4, 157.6, 1157.2, 302.3]


def _jsonable(obj):
    if hasattr(obj, "model_dump"):
        return obj.model_dump(mode="json")
    if hasattr(obj, "dict"):
        return obj.dict()
    if hasattr(obj, "__dict__"):
        return {k: _jsonable(v) for k, v in vars(obj).items()}
    if isinstance(obj, (list, tuple)):
        return [_jsonable(x) for x in obj]
    if isinstance(obj, dict):
        return {k: _jsonable(v) for k, v in obj.items()}
    return obj


def _content_to_text(content):
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            data = _jsonable(item)
            if isinstance(data, dict):
                if data.get("type") == "text":
                    parts.append(data.get("text", ""))
                elif data.get("type") == "reasoning":
                    parts.append("[reasoning]\n" + (data.get("reasoning") or data.get("summary") or ""))
                else:
                    parts.append(json.dumps(data, ensure_ascii=False))
            else:
                parts.append(str(data))
        return "\n".join(p for p in parts if p)
    return str(content)


def _extract_result(stdout: str):
    match = re.search(r"Result (\[[^\n]+?\]) differs from expected", stdout)
    if not match:
        return None
    return json.loads(match.group(1))


def _write_task_files(task: dict):
    suffixes = {
        "instruction": "instruction.md",
        "test_sh": "test.sh",
        "solve_sh": "solve.sh",
        "task_toml": "task.toml",
        "dockerfile": "Dockerfile",
    }
    for key, name in suffixes.items():
        (TASK_DIR / name).write_text(task.get(key, ""), encoding="utf-8")


def main():
    client = Docent.from_url(f"{FRONTEND}/dashboard/{COLLECTION_ID}")
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    TASK_DIR.mkdir(parents=True, exist_ok=True)
    summaries = []
    task_written = False

    for idx, run_id in enumerate(RUN_IDS, start=1):
        run = client.get_agent_run(COLLECTION_ID, run_id)
        metadata = client.get_agent_run_metadata(COLLECTION_ID, run_id)
        run_meta = metadata.get("run", {})
        if not task_written:
            _write_task_files(metadata.get("task", {}))
            task_written = True

        transcript = run.transcripts[0]
        messages = []
        md = [
            f"# Run {idx:02d}: {run_meta.get('agent')} / {run_meta.get('model')}",
            "",
            f"- Docent: {FRONTEND}/dashboard/{COLLECTION_ID}/agent_run/{run_id}",
            f"- Role: {run_meta.get('role')}",
            f"- Reward: {run_meta.get('reward')}",
            f"- Trial: {run_meta.get('trial_id')}",
            "",
        ]
        for block_idx, msg in enumerate(transcript.messages):
            text = _content_to_text(msg.content)
            tool_calls = [_jsonable(tc) for tc in (getattr(msg, "tool_calls", None) or [])]
            messages.append(
                {
                    "block_idx": block_idx,
                    "role": msg.role,
                    "content": text,
                    "tool_calls": tool_calls,
                    "metadata": _jsonable(msg.metadata),
                }
            )
            md.append(f"## Block {block_idx}: {msg.role}")
            if tool_calls:
                md.append("")
                md.append("Tool calls:")
                md.append("```json")
                md.append(json.dumps(tool_calls, indent=2))
                md.append("```")
            md.append("")
            md.append(text)
            md.append("")

        test_stdout = run_meta.get("test_stdout") or ""
        prediction = _extract_result(test_stdout)
        deltas = None
        if isinstance(prediction, list) and len(prediction) == len(EXPECTED):
            deltas = [p - e for p, e in zip(prediction, EXPECTED)]
        summary = {
            "idx": idx,
            "run_id": run_id,
            "url": f"{FRONTEND}/dashboard/{COLLECTION_ID}/agent_run/{run_id}",
            "agent": run_meta.get("agent"),
            "model": run_meta.get("model"),
            "role": run_meta.get("role"),
            "reward": run_meta.get("reward"),
            "trial_id": run_meta.get("trial_id"),
            "prediction": prediction,
            "expected": EXPECTED,
            "deltas": deltas,
            "exception_type": run_meta.get("exception_type"),
        }
        summaries.append(summary)

        stem = f"{idx:02d}_{run_meta.get('agent')}_{run_meta.get('model')}_{run_id[:8]}"
        safe_stem = re.sub(r"[^A-Za-z0-9_.-]+", "_", stem)
        (RUN_DIR / f"{safe_stem}.md").write_text("\n".join(md), encoding="utf-8")
        (RUN_DIR / f"{safe_stem}.json").write_text(
            json.dumps({"summary": summary, "metadata": metadata, "messages": messages}, indent=2),
            encoding="utf-8",
        )

    (ROOT / "run_summaries.json").write_text(json.dumps(summaries, indent=2), encoding="utf-8")
    print(json.dumps(summaries, indent=2))


if __name__ == "__main__":
    main()
