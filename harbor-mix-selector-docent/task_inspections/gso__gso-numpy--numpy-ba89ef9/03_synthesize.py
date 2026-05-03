"""Aggregate per-run analyses into a verdict view."""
import json
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).parent
manifest = json.loads((HERE / "run_ids.json").read_text())
runs = {r["id"]: r for r in manifest["runs"]}
results = json.loads((HERE / "all_results.json").read_text())
retry_path = HERE / "retry_results.json"
if retry_path.exists():
    results = results + json.loads(retry_path.read_text())


def text_of(field):
    if field is None:
        return ""
    if isinstance(field, dict):
        return field.get("text", "")
    return field


def find_agent_run_id(out):
    # Pull the agent_run_id from the first citation we can find.
    for v in out.values():
        if isinstance(v, dict):
            cits = v.get("citations") or []
            for c in cits:
                tgt = (c.get("target") or {}).get("item") or {}
                arid = tgt.get("agent_run_id")
                if arid:
                    return arid
    return None


# Map results purely via citation-extracted agent_run_id (no positional fallback).
by_run = {}
for r in results:
    out = r.get("output") or {}
    if not out:
        continue
    arid = find_agent_run_id(out)
    if arid:
        by_run[arid] = out

print("=== Per-run breakdown ===")
status_count = Counter()
closeness_count = Counter()
strategy_count = defaultdict(list)
bottleneck_count = Counter()

for rid, meta in runs.items():
    out = by_run.get(rid) or {}
    status = out.get("status", "?")
    closeness = out.get("closeness", "?")
    label = f"{meta['agent']}/{meta['model']}"
    print(f"\n--- {rid[:8]}  {label}  expected={meta['role']}  graded={status} closeness={closeness}")
    print("  approach :", text_of(out.get("approach_summary"))[:240])
    print("  strategy :", text_of(out.get("optimization_strategy"))[:240])
    print("  rebuilt  :", out.get("rebuilt_and_measured", ""))
    if status == "failure":
        print("  surface  :", text_of(out.get("surface_reason"))[:240])
        print("  rootcause:", text_of(out.get("root_cause"))[:240])
    print("  overfit  :", text_of(out.get("overfit_risk"))[:200])
    print("  task/agt :", text_of(out.get("agent_vs_task_bottleneck"))[:240])

    status_count[status] += 1
    closeness_count[closeness] += 1
    strategy_text = text_of(out.get("optimization_strategy")).lower()
    bucket = "other"
    if "ufunc_at" in strategy_text or "ufunc_object.c" in strategy_text or "fast iter" in strategy_text or "strided" in strategy_text:
        bucket = "C-level ufunc_at fast path (oracle-style)"
    elif "bincount" in strategy_text:
        bucket = "np.bincount substitution"
    elif "cython" in strategy_text or ".pyx" in strategy_text:
        bucket = "cython rewrite"
    elif "monkey" in strategy_text or "wrapper" in strategy_text or "python" in strategy_text and "rewrite" in strategy_text:
        bucket = "python-level wrapper / monkey-patch"
    elif "simd" in strategy_text:
        bucket = "SIMD tweak"
    elif "no patch" in strategy_text or "empty" in strategy_text:
        bucket = "no patch"
    strategy_count[bucket].append(f"{rid[:8]} ({label}, {status})")

    bottle_text = text_of(out.get("agent_vs_task_bottleneck")).lower()
    if "task" in bottle_text and "agent" not in bottle_text:
        bottleneck_count["task"] += 1
    elif "agent" in bottle_text and "task" not in bottle_text:
        bottleneck_count["agent"] += 1
    elif "agent" in bottle_text and "task" in bottle_text:
        bottleneck_count["agent (mostly)"] += 1
    else:
        bottleneck_count["unknown"] += 1


print("\n=== Aggregate ===")
print("status counts    :", dict(status_count))
print("closeness counts :", dict(closeness_count))
print("bottleneck votes :", dict(bottleneck_count))
print("\n=== Strategy buckets ===")
for k, v in strategy_count.items():
    print(f"  {k} ({len(v)}):")
    for r in v:
        print("   -", r)
