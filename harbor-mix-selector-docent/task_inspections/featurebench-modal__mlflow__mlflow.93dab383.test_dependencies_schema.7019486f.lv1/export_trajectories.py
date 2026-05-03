from __future__ import annotations

import json
from pathlib import Path

from docent.sdk.client import Docent


COLLECTION_ID = "640e920a-aef3-4b7c-9487-69899ef19e9d"
OUT = Path(__file__).parent


def clean(text: object) -> str:
    if text is None:
        return ""
    return str(text).replace("\r\n", "\n")


def main() -> None:
    client = Docent.from_url(f"https://docent.transluce.org/dashboard/{COLLECTION_ID}")
    runs = json.loads((OUT / "run_metadata.json").read_text(encoding="utf-8"))["runs"]
    traj_dir = OUT / "trajectories"
    traj_dir.mkdir(exist_ok=True)

    for run in runs:
        run_id = run["id"]
        agent_run = client.get_agent_run(COLLECTION_ID, run_id)
        json_path = traj_dir / f"{run_id}.json"
        json_path.write_text(
            json.dumps(agent_run.model_dump(mode="json"), indent=2, sort_keys=True),
            encoding="utf-8",
        )

        md = [
            f"# Trajectory `{run_id}`",
            "",
            f"- Agent: `{run['agent']}`",
            f"- Model: `{run['model']}`",
            f"- Reward: `{run['reward']}`",
            f"- Trial: `{run['trial_id']}`",
            f"- URL: https://docent.transluce.org/dashboard/{COLLECTION_ID}/agent_run/{run_id}",
            "",
        ]
        for transcript in agent_run.transcripts:
            md.extend([f"## Transcript `{transcript.name}` / `{transcript.id}`", ""])
            for i, message in enumerate(transcript.messages):
                role = getattr(message, "role", type(message).__name__)
                content = clean(getattr(message, "content", ""))
                metadata = getattr(message, "metadata", None)
                md.extend([f"### Message {i}: `{role}`", ""])
                if metadata:
                    md.extend(["Metadata:", "```json", json.dumps(metadata, indent=2, sort_keys=True), "```", ""])
                md.extend(["```text", content, "```", ""])

        (traj_dir / f"{run_id}.md").write_text("\n".join(md), encoding="utf-8")


if __name__ == "__main__":
    main()
