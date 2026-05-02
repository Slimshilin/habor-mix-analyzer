#!/usr/bin/env python3
"""Analyze all 18 agent trajectories for crustbench-genetic-neural-network-for-simple-control."""

from docent.sdk.client import Docent
from docent import TranscriptRef

COLLECTION_ID = "640e920a-aef3-4b7c-9487-69899ef19e9d"

# All 18 runs for this task: (agent_run_id, transcript_id, agent_name, role)
RUNS = [
    # claude-code (all 3 failed with AgentTimeoutError)
    ("10693755-f1fe-47ff-9d9d-d464c9cfe745", "71b6e481-d669-45db-9963-727067cb0411", "claude-code", "failure-timeout"),
    ("c9458e1e-2328-4d4e-b753-526fc42cc874", "02b467af-ab20-4f96-8cd4-a60ddd43314a", "claude-code", "failure-timeout"),
    ("98fd3d05-b1f4-406f-add8-ab5aba676f12", "4f357c57-97d1-4c08-ac28-f9c2990c4af2", "claude-code", "failure-timeout"),

    # codex (all 3 succeeded)
    ("2b51236f-612f-4b46-8ce4-66faffc2b6ca", "5a58b646-1f9f-40fd-8d4c-93402700b2b7", "codex", "success"),
    ("7927c5c8-703d-4290-88db-90bc69016f8e", "644099b4-16eb-47fe-96dc-302b73930063", "codex", "success"),
    ("c0b02108-2c37-4188-8894-bdb54854de7c", "51d50067-561e-4928-bef1-8cc1d86d6a63", "codex", "success"),

    # gemini-cli (all 3 failed with AgentTimeoutError)
    ("e29b0564-3352-4661-a2c0-7c4d7048a27a", "8c233bde-b27d-4217-9130-698268a0c986", "gemini-cli", "failure-timeout"),
    ("5b9fc238-1c20-4bf5-b726-4c75ad76259f", "aa93387d-a241-49b3-99f7-16655ba5047d", "gemini-cli", "failure-timeout-0reward"),
    ("c04be36b-ce7f-433d-83dc-8d0a26756f6a", "841cc8c0-dadf-4b35-b229-45a7bf29ccfb", "gemini-cli", "failure-timeout"),

    # terminus-2 (2 success, 7 failure)
    ("fbcc1678-7207-4b22-9ebe-e9480725ce22", "1f389e0e-501c-44c9-988d-879be0aec1cf", "terminus-2", "failure-timeout"),
    ("09a6112d-ef37-4941-8556-e7167127b95c", "0a960169-ccae-492c-b95d-09ce152ef81a", "terminus-2", "failure-timeout"),
    ("2c0c7e34-d8c3-48a8-b4c7-571b499ea673", "2aaa491f-8913-40ab-b493-a3cf4b8b9bd6", "terminus-2", "failure-timeout"),
    ("5b15cbd5-97ec-4d79-98f4-bd349d992189", "b21bb967-a513-4bf9-a013-407c9a034eb2", "terminus-2", "success"),
    ("8743bf39-8b23-4e44-bae7-ffd41e3b73af", "f01091df-19a6-412c-af4c-6f9a2229f06e", "terminus-2", "failure-timeout"),
    ("c7f27a2f-c348-44ce-bef7-e8f848048b9c", "576f58d6-7662-4cbe-81c1-1967830b1279", "terminus-2", "failure-timeout"),
    ("d917e7e1-e395-4221-95d3-7f3e47b9e18a", None, "terminus-2", "success"),  # transcript ID needs lookup
    ("f41aa3e3-7f27-47ab-8794-fff4ddbf9f5c", "17ef9835-7696-4cdb-bc06-7b3c517e2af1", "terminus-2", "failure-no-timeout"),
    ("07f30e35-0435-4d0c-a0e6-66631d313a7a", "5a6b38c9-1af3-4453-8ec5-75f8eb1b3e9a", "terminus-2", "failure-timeout-most-complete"),
]

client = Docent.from_url(f"https://docent.transluce.org/dashboard/{COLLECTION_ID}")
client.plan_name = "crustbench-genetic-nn-trajectory-analysis-v1"

# Build prompts_list for all 18 trajectories
ANALYSIS_PROMPT = """You are analyzing an AI agent trajectory for a C-to-Rust transpilation task.

The task: Transpile ~14 C source files (genetic algorithm + neural network + math library) to safe Rust that passes cargo test.
- There are 13 Rust interface files to implement (replace unimplemented!() macros)
- Tests are in 11 test binaries
- Agent has 1800 seconds (30 min) total
- Key test: test_full_run runs 50,000 generations of a genetic algorithm

Agent info:
- Agent name: {agent_name}
- Outcome: {role}

Please analyze this trajectory and answer:

1. **APPROACH**: How did the agent approach the task? Did it read/explore files first or jump straight to implementing? Did it try to transpile all files at once or one by one?

2. **FILES WORKED ON**: Which Rust interface files did the agent actually implement or attempt to implement? List them.

3. **COMPLETION STATUS**: How far did the agent get?
   - Did it finish implementing all 13 interfaces?
   - Did it successfully compile the code?
   - Did it run tests? Which tests passed/failed?

4. **FAILURE MODE** (for failed runs):
   - Was it a timeout (ran out of time)?
   - Was there a specific bug it kept hitting?
   - What was the last thing it was doing when it failed/timed out?

5. **ROOT CAUSE**: What is the ACTUAL reason this agent failed or succeeded?
   - Surface reason: what specific error/behavior appeared at failure
   - Root cause: what underlying capability gap or approach flaw caused the surface problem
   - E.g., "Surface: index-out-of-bounds in neural_network.rs:139 / Root: incorrect translation of C array indexing logic for the deNormalizationProcess function"

6. **KEY MOMENTS**: Quote 2-3 specific moments from the trajectory that best illustrate the agent's approach and failure mode.

Be specific and concrete. Quote actual code, error messages, or agent reasoning when relevant."""

prompts_list = []
for run_id, transcript_id, agent_name, role in RUNS:
    if transcript_id is None:
        continue
    prompt_text = ANALYSIS_PROMPT.format(agent_name=agent_name, role=role)
    prompts_list.append([
        prompt_text,
        TranscriptRef(id=transcript_id, agent_run_id=run_id, collection_id=COLLECTION_ID)
    ])

reading = client.read(
    name="All 18 trajectory analysis",
    prompts_list=prompts_list,
    model="anthropic/claude-opus-4-6",
    output_schema={
        "type": "object",
        "properties": {
            "approach": {"type": "string", "description": "How the agent approached the task"},
            "files_worked_on": {"type": "array", "items": {"type": "string"}, "description": "Rust interface files implemented"},
            "completion_status": {"type": "string", "description": "How far the agent got"},
            "failure_mode": {"type": "string", "description": "For failures: what happened"},
            "surface_reason": {"type": "string", "description": "Surface-level failure symptom"},
            "root_cause": {"type": "string", "description": "Underlying capability gap or approach flaw"},
            "key_moments": {"type": "array", "items": {"type": "string"}, "description": "2-3 specific quotes from trajectory"},
        },
        "required": ["approach", "completion_status", "root_cause"]
    }
)

print(f"Analysis submitted for {len(prompts_list)} trajectories")
print("Waiting for results...")
results = reading.results
print(f"Got {len(results)} results")

for i, (result, run_info) in enumerate(zip(results, RUNS)):
    run_id, transcript_id, agent_name, role = run_info
    if transcript_id is None:
        continue
    output = result.output
    print(f"\n{'='*80}")
    print(f"Run {i+1}: {agent_name} | {role} | {run_id[:8]}")
    print(f"{'='*80}")
    if output:
        print(f"APPROACH: {output.get('approach', 'N/A')}")
        print(f"\nFILES: {output.get('files_worked_on', [])}")
        print(f"\nCOMPLETION: {output.get('completion_status', 'N/A')}")
        print(f"\nFAILURE_MODE: {output.get('failure_mode', 'N/A')}")
        print(f"\nSURFACE: {output.get('surface_reason', 'N/A')}")
        print(f"\nROOT CAUSE: {output.get('root_cause', 'N/A')}")
        print(f"\nKEY MOMENTS:")
        for km in output.get('key_moments', []):
            print(f"  - {km}")
    else:
        print(f"ERROR: {result.error}")
