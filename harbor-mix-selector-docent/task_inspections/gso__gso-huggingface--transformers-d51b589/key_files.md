# Key Files: `gso/gso-huggingface--transformers-d51b589`

- `task_files/instruction.md`: task prompt and reproduced XLNet timing/equivalence script.
- `task_files/test.sh`: verifier wrapper; captures the submitted diff, runs `/tests/eval.sh`, then calls `gso_evaluate.py`.
- `task_files/solve.sh`: oracle patch. The core change is in `transformers/modeling_xlnet.py`, reordering XLNet attention tensors to `bnij` so softmax runs over the contiguous last dimension.
- `run_summaries.json`: exported metadata for all 18 runs. The pasted user links had 17 URLs; `d7d0c912-41d0-49ac-9484-c7073c9e4a53` was discovered from the collection and included.
- `trajectories/*.md`: exported full agent trajectories.
- `test_stdout/*.txt`: verifier stdout for each submitted patch.
- `discovered_runs.json`: collection query result used to confirm all 18 runs for this task.
