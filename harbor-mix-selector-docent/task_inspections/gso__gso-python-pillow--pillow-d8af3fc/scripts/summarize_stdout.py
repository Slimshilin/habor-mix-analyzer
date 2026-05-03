from __future__ import annotations

import json
import re
import statistics
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STDOUT_DIR = ROOT / "test_stdout"


def section_times(text: str, section: str) -> dict[str, list[float]]:
    start = f">>>>> Start {section} Output"
    end = f">>>>> End {section} Output"
    if start not in text:
        return {}
    body = text.split(start, 1)[1]
    if end in body:
        body = body.split(end, 1)[0]
    current = None
    times: dict[str, list[float]] = {}
    for line in body.splitlines():
        test_match = re.match(r">>>>> Test (\d+)", line)
        if test_match:
            current = test_match.group(1)
            times[current] = []
            continue
        time_match = re.match(r"Execution time: ([0-9.]+)s", line)
        if time_match and current is not None:
            times[current].append(float(time_match.group(1)))
    return times


def medians(times: dict[str, list[float]]) -> dict[str, float]:
    return {test: statistics.median(values) for test, values in times.items() if values}


def geomean(values: list[float]) -> float | None:
    if not values or any(value <= 0 for value in values):
        return None
    product = 1.0
    for value in values:
        product *= value
    return product ** (1.0 / len(values))


def summarize_file(path: Path) -> dict:
    text = path.read_text(encoding="utf-8", errors="replace")
    patch_size = None
    patch_size_match = re.search(r"Patch size: (\d+) bytes", text)
    if patch_size_match:
        patch_size = int(patch_size_match.group(1))
    result_match = re.search(r"opt_commit: (True|False), reward: ([01])", text)
    base = medians(section_times(text, "Base"))
    patch = medians(section_times(text, "Patch"))
    commit = medians(section_times(text, "Commit"))
    common_base_patch = sorted(set(base) & set(patch), key=int)
    common_commit_patch = sorted(set(commit) & set(patch), key=int)
    speedups = [base[test] / patch[test] for test in common_base_patch if patch[test] > 0]
    commit_ratios = [commit[test] / patch[test] for test in common_commit_patch if patch[test] > 0]
    failures = []
    for pattern in (
        r"Traceback \(most recent call last\):.*?(?=\nRunning test|\n>>>>> Start|\Z)",
        r"ValueError: [^\n]+",
        r"AssertionError: [^\n]+",
        r">>>>> Tests Failed[^\n]*",
    ):
        failures.extend(re.findall(pattern, text, flags=re.S))
    return {
        "file": path.name,
        "patch_size": patch_size,
        "opt_commit": None if not result_match else result_match.group(1) == "True",
        "reward": None if not result_match else int(result_match.group(2)),
        "tests_in_base": len(base),
        "tests_in_patch": len(patch),
        "tests_in_commit": len(commit),
        "patch_vs_base_geomean_speedup": geomean(speedups),
        "commit_vs_patch_geomean_ratio": geomean(commit_ratios),
        "median_base": base,
        "median_patch": patch,
        "median_commit": commit,
        "failures": failures[:5],
    }


def main() -> None:
    rows = [summarize_file(path) for path in sorted(STDOUT_DIR.glob("*.txt"))]
    (ROOT / "timing_summary.json").write_text(json.dumps(rows, indent=2, sort_keys=True), encoding="utf-8")
    compact = [
        {
            "file": row["file"],
            "reward": row["reward"],
            "patch_size": row["patch_size"],
            "patch_vs_base_geomean_speedup": row["patch_vs_base_geomean_speedup"],
            "commit_vs_patch_geomean_ratio": row["commit_vs_patch_geomean_ratio"],
            "failures": row["failures"],
        }
        for row in rows
    ]
    print(json.dumps(compact, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
