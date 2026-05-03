"""Fan out a per-trajectory analysis for the 18 runs of gso-numpy--numpy-ba89ef9."""
import json
from docent.sdk.client import Docent
from docent.data_models.context_config import AgentRunContextConfig
from docent.data_models.metadata_util import INCLUDE_ALL_GLOB_FILTER

COLLECTION_ID = "640e920a-aef3-4b7c-9487-69899ef19e9d"

RUN_IDS = [
    "191225fc-9e49-4f59-9100-216c6a5a6d23",
    "b0aa979b-3fa3-41f5-bf68-dbe9a2df5598",
    "1abad4c5-9f78-4f0a-b197-40a1c81f119b",
    "519f16c9-e009-4c7a-aac8-39a456e25837",
    "679ade5d-a658-42a5-820f-a33d26e7b13f",
    "7b3d3ef1-ab92-43a8-b872-00feadc2838f",
    "d07c100a-3f15-4aec-9990-5e388530c111",
    "30511e77-9980-48bb-ab7e-abf7b57f50b0",
    "127d0978-dbfd-4c6a-8314-e3637878390e",
    "fa7f1bb3-235a-496a-9036-8343bd42f8b1",
    "5466cd23-0e3a-4a62-ac84-43a8fa7c09af",
    "25caae67-a01f-4554-92e4-2be7f1a3c0db",
    "ba359698-0027-44eb-a279-c74654ba5361",
    "7f33f099-58ec-4f05-a6de-00513dbb5d58",
    "41b24f84-09ec-4256-8024-aeec1b5984d8",
    "aadb3dcc-d44c-44b4-ac12-1e1d1b8749e0",
    "c49197b1-acd5-4036-9289-2ce98e0b8e92",
    "eba92257-9fa5-4c37-ad41-a907c3e41221",
]

PROMPT = [
    "You are reviewing one agent trajectory for the GSO performance-optimization task `numpy__numpy-ba89ef9`.",
    "TASK SETUP:",
    "- Repo: numpy/numpy at commit 9f1b3efef4 (just before the historical optimization).",
    "- The agent must speed up the inner loop `np.add.at(res, indices, vals)` (1M indices, length-1000 destination, float64) WITHOUT breaking functional equivalence and WITHOUT overfitting to that exact input.",
    "- Reference (oracle) fix lives in numpy/core/src/umath/ufunc_object.c (split ufunc_at into a fast strided-loop path that bypasses the buffered NpyIter when the trailing dim has unit stride for op2 and stride sizeof(itemtype) for op1's gathered slot) plus a small SIMD-cutoff tweak in loops_arithm_fp.dispatch.c.src. Patch ~4 KB, gives ~8x on Test 0.",
    "- Hidden grader: builds with agent patch, times 20 tests; builds with oracle commit, times 20 tests; reward=1 only if the agent's per-test timings are essentially within the oracle's speed band (functional equivalence is also checked via gso_test_*.py before timing).",
    "- Build is expensive (full numpy native rebuild ~minutes per attempt). Agents only have a fixed step budget.",
    "Here is the agent run to review:",
    "",
    {"role": "user", "content": ""},  # placeholder — replaced below
]

prompt_template = [
    "You are reviewing one agent trajectory for the GSO performance-optimization task `numpy__numpy-ba89ef9`.",
    "BACKGROUND:",
    "- Repo: numpy/numpy at commit 9f1b3efef4. The agent must speed up `np.add.at(res, indices, vals)` (1M random indices into length-1000 float64 destination) WITHOUT breaking equivalence and WITHOUT overfitting.",
    "- Reference fix: split `ufunc_at` in numpy/core/src/umath/ufunc_object.c into a fast strided-loop path that avoids the buffered NpyIter when the simple-stride preconditions hold; also a small SIMD cutoff in loops_arithm_fp.dispatch.c.src. Patch ~4KB, ~8x on Test 0.",
    "- Hidden grader: builds with agent patch, runs 20 timing tests; builds with oracle commit, runs 20 timing tests; sets reward=1 only when the agent's timings are essentially within the oracle's band (and functional equivalence holds in the gso_test_*.py phase).",
    "- Native rebuild is ~minutes per attempt; agents have bounded step budgets.",
    "Here is the trajectory to review:",
    "{run_id}",
    """
    Please return a structured analysis covering:
    (a) High-level approach the agent took (what files/functions did they zero in on?).
    (b) Did they actually rebuild numpy and re-time, or just edit blindly?
    (c) Which optimization strategy did they pick? Examples: cython numpy.add.at rewrite, np.bincount substitution, pure-Python wrapper, C-level ufunc_at fast path (oracle-style), CPython buffered-iter tweak, parallelization, vectorized scatter via __array_function__, monkey-patching, etc.
    (d) For failures: what is the *surface* reason (segfault, equivalence-check failure, no measurable speedup, build error, time out, wrong file edited, etc.) AND the *root cause* (poor codebase exploration, never read ufunc_object.c, didn't understand that the test compares against a hidden oracle, gave up after one rebuild, overfit to the prompt's example input only, etc.).
    (e) Was their final patch likely to overfit to the prompt's input? (e.g., special-casing 1M indices / length-1000 / float64).
    (f) Did the failure trace any task quality issue (instruction ambiguity, missing info, infeasible build, hidden tests not inferable) or is it agent capability?
    Always quote concrete tool calls / messages with citations when available.
    """
]

def main():
    client = Docent()
    client.plan_name = "GSO numpy add.at — task inspection"

    run_ids_sql = ", ".join(f"'{u}'" for u in RUN_IDS)
    runs_meta = client.query(
        COLLECTION_ID,
        f"""SELECT id AS run_id,
                  metadata_json->'run'->>'agent' AS agent,
                  metadata_json->'run'->>'model' AS model,
                  metadata_json->'run'->>'role' AS role
            FROM agent_runs
            WHERE id IN ({run_ids_sql})""",
        name="Fetch all 18 gso-numpy runs metadata",
    )

    analysis = client.read(
        prompt_template=[
            *prompt_template[:-2],
            runs_meta.run_id.as_type("agent_run"),
            prompt_template[-1],
        ],
        context_configs={
            "run_id": AgentRunContextConfig(
                agent_run_metadata=INCLUDE_ALL_GLOB_FILTER,
                transcript_group_names=INCLUDE_ALL_GLOB_FILTER,
                transcript_names=INCLUDE_ALL_GLOB_FILTER,
                transcript_metadata=INCLUDE_ALL_GLOB_FILTER,
                message_metadata=INCLUDE_ALL_GLOB_FILTER,
            )
        },
        model="openai/gpt-5.4-mini",
        output_schema={
            "type": "object",
            "properties": {
                "agent_label": {"type": "string"},
                "status": {"type": "string", "enum": ["success", "failure"]},
                "closeness": {
                    "type": "string",
                    "enum": ["perfect", "almost_there", "partial", "off_track"],
                },
                "approach_summary": {"type": "string", "citations": True},
                "rebuilt_and_measured": {"type": "string"},
                "optimization_strategy": {"type": "string", "citations": True},
                "surface_reason": {"type": "string", "citations": True},
                "root_cause": {"type": "string", "citations": True},
                "overfit_risk": {"type": "string", "citations": True},
                "agent_vs_task_bottleneck": {"type": "string", "citations": True},
            },
            "required": [
                "status",
                "closeness",
                "approach_summary",
                "rebuilt_and_measured",
                "optimization_strategy",
                "surface_reason",
                "root_cause",
                "overfit_risk",
                "agent_vs_task_bottleneck",
            ],
        },
        name="Per-run analysis (gso-numpy)",
    )

    client.flush(auto_approve=True)

    out = []
    for rr in analysis.results:
        out.append({"result_id": str(rr.id), "output": rr.output})
    with open("all_results.json", "w") as f:
        json.dump(out, f, indent=2)
    print(f"Wrote {len(out)} results to all_results.json")


if __name__ == "__main__":
    main()
