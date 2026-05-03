from __future__ import annotations

import json
import re
from pathlib import Path


OUT = Path(__file__).parent
STDOUT_DIR = OUT / "test_stdout"


def extract_failure(text: str) -> dict:
    failed = re.findall(r"FAILED .*?(tests/models/test_dependencies_schema.py::\S+)", text)
    expected = re.findall(r"E\s+Expected: (.+)", text)
    actual = re.findall(r"E\s+Actual: (.+)", text)
    diffs = re.findall(r"E\s+At index 0 diff: (.+)", text)
    summary = re.findall(r"=+ ([^=]*failed[^=]*passed[^=]*) =+", text)
    return {
        "failed_tests": sorted(set(failed)),
        "expected": expected[:5],
        "actual": actual[:5],
        "diffs": diffs[:5],
        "summary": summary[-1:] if summary else [],
        "reward_line": re.findall(r"Reward: \d+", text)[-1:] or [],
    }


def main() -> None:
    runs = json.loads((OUT / "run_metadata.json").read_text(encoding="utf-8"))["runs"]
    rows = []
    for run in runs:
        stdout = (STDOUT_DIR / f"{run['id']}.txt").read_text(encoding="utf-8")
        info = extract_failure(stdout)
        passed = len(re.findall(r"PASSED .*?tests/models/test_dependencies_schema.py::", stdout))
        failed = len(re.findall(r"FAILED .*?tests/models/test_dependencies_schema.py::", stdout))
        rows.append(
            {
                "id": run["id"],
                "agent": run["agent"],
                "model": run["model"],
                "reward": run["reward"],
                "passed_marker_count": passed,
                "failed_marker_count": failed,
                **info,
            }
        )
    (OUT / "failure_summary.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
    for row in rows:
        print(
            row["id"][:8],
            row["agent"],
            row["model"],
            "reward=" + row["reward"],
            "failed=" + ",".join(row["failed_tests"] or ["none"]),
        )
        for item in row["expected"][:1] + row["actual"][:1] + row["diffs"][:1]:
            print("  ", item)


if __name__ == "__main__":
    main()
