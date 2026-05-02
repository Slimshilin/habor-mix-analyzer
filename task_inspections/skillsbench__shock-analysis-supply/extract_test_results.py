"""Extract test results for all 18 runs of shock-analysis-supply."""
from docent.sdk.client import Docent
import json, re

COLLECTION_ID = "640e920a-aef3-4b7c-9487-69899ef19e9d"
TASK_CHECKSUM = "8c3ecac360dd6d2bf70f21915668c0595a38654cd039f75d02eac123541502f8"

client = Docent()

def dql(query):
    result = client.execute_dql(collection_id=COLLECTION_ID, dql=query)
    cols = result["columns"]
    return [dict(zip(cols, row)) for row in result["rows"]]

run_ids = [r["id"] for r in dql(f"""
    SELECT id FROM agent_runs
    WHERE metadata_json->>'task_checksum' = '{TASK_CHECKSUM}'
""")]
print(f"Found {len(run_ids)} runs\n")

summary = []
for run_id in run_ids:
    rows2 = dql(f"SELECT id, metadata_json FROM agent_runs WHERE id = '{run_id}'")
    meta = rows2[0]["metadata_json"]
    run = meta.get("run", {})
    atif = meta.get("atif", {})
    agent_info = atif.get("agent", {})

    model = agent_info.get("model_name", run.get("model", "unknown"))
    agent = agent_info.get("name", run.get("agent", "unknown"))
    reward = run.get("reward", "?")
    exception = run.get("exception_type", None)
    test_stdout = run.get("test_stdout", "")

    passed, failed = [], []
    if test_stdout:
        for line in test_stdout.split("\n"):
            m = re.search(r"test_outputs\.py::(\w+) (PASSED|FAILED)", line)
            if m:
                (passed if m.group(2) == "PASSED" else failed).append(m.group(1))

    summary.append({
        "run_id": run_id,
        "model": model,
        "agent": agent,
        "reward": reward,
        "exception": exception,
        "n_passed": len(passed),
        "n_failed": len(failed),
        "passed": passed,
        "failed": failed,
        "test_stdout": test_stdout,
    })

    failure_detail = ""
    if failed and test_stdout:
        fail_section = re.search(
            r"=====+ FAILURES =====+(.*?)=====+ (PASSES|short test summary)", test_stdout, re.DOTALL
        )
        if fail_section:
            failure_detail = fail_section.group(1)[:2000]

    print(f"{'='*60}")
    print(f"Run: {run_id[:8]}... | Model: {model} | Agent: {agent}")
    print(f"Reward: {reward} | Exception: {exception}")
    print(f"Passed ({len(passed)}): {', '.join(passed)}")
    print(f"Failed ({len(failed)}): {', '.join(failed)}")
    if failure_detail:
        print(f"Failure detail:\n{failure_detail}")

# Summary table
print("\n\n" + "="*80)
print("SUMMARY TABLE")
print("="*80)
print(f"{'RUN':10} {'MODEL':35} {'AGENT':15} {'PASS':5} {'FAIL':5} {'FAILED_TESTS'}")
print("-"*120)
for s in sorted(summary, key=lambda x: (-x["n_passed"], x["model"])):
    print(f"{s['run_id'][:8]} {s['model']:35} {s['agent']:15} {s['n_passed']:5} {s['n_failed']:5} {', '.join(s['failed'])}")

# Count by failure type
from collections import Counter
all_failures = [t for s in summary for t in s["failed"]]
print("\nFailure frequency:")
for test, cnt in Counter(all_failures).most_common():
    print(f"  {test}: {cnt}")
