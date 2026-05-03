"""Re-run analysis for the 4 runs whose first read returned None."""
import json
from docent.sdk.client import Docent
from docent.data_models.context_config import AgentRunContextConfig
from docent.data_models.metadata_util import INCLUDE_ALL_GLOB_FILTER

COLLECTION_ID = "640e920a-aef3-4b7c-9487-69899ef19e9d"

MISSING = [
    "191225fc-9e49-4f59-9100-216c6a5a6d23",
    "1abad4c5-9f78-4f0a-b197-40a1c81f119b",
    "25caae67-a01f-4554-92e4-2be7f1a3c0db",
    "b0aa979b-3fa3-41f5-bf68-dbe9a2df5598",
]

prompt_template = [
    "You are reviewing one agent trajectory for the GSO performance-optimization task `numpy__numpy-ba89ef9`.",
    "BACKGROUND:",
    "- Repo: numpy/numpy at commit 9f1b3efef4. The agent must speed up `np.add.at(res, indices, vals)` (1M random indices into length-1000 float64 destination) WITHOUT breaking equivalence and WITHOUT overfitting.",
    "- Reference fix: split `ufunc_at` in numpy/core/src/umath/ufunc_object.c into a fast strided-loop path that avoids the buffered NpyIter when stride preconditions hold; also a small SIMD cutoff in loops_arithm_fp.dispatch.c.src. Patch ~4KB, ~8x on Test 0.",
    "- Hidden grader: builds with agent patch, runs 20 timing tests; builds with oracle commit, runs 20 timing tests; sets reward=1 only when the agent's timings match the oracle's band (and equivalence holds in the gso_test_*.py phase).",
    "Here is the trajectory to review:",
    "{run_id}",
    """
    Provide the structured analysis. Be sure to fill every field; do not return null.
    """
]


def main():
    client = Docent()
    client.plan_name = "GSO numpy add.at — retry missing"

    sql_ids = ", ".join(f"'{u}'" for u in MISSING)
    runs_meta = client.query(
        COLLECTION_ID,
        f"""SELECT id AS run_id,
                  metadata_json->'run'->>'agent' AS agent,
                  metadata_json->'run'->>'model' AS model,
                  metadata_json->'run'->>'role' AS role
            FROM agent_runs
            WHERE id IN ({sql_ids})""",
        name="Fetch missing 4 gso-numpy runs metadata",
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
        model="openai/gpt-5.4",
        output_schema={
            "type": "object",
            "properties": {
                "agent_run_id_text": {"type": "string"},
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
                "agent_run_id_text",
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
        name="Per-run analysis (retry)",
    )

    client.flush(auto_approve=True)

    out = []
    for rr in analysis.results:
        out.append({"result_id": str(rr.id), "output": rr.output})
    with open("retry_results.json", "w") as f:
        json.dump(out, f, indent=2)
    print(f"Wrote {len(out)} retry results to retry_results.json")


if __name__ == "__main__":
    main()
