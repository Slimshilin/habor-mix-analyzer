# Key Files

- `task_files/instruction.md` — exported task prompt and reproduction script.
- `task_files/test.sh` — exported verifier wrapper; captures patch, runs `/tests/eval.sh`, then `/tests/gso_evaluate.py`.
- `task_files/solve.sh` — exported Docent solve script. Note: the stored metadata appears truncated and begins with unrelated upstream hunks; the true oracle used by the verifier is the upstream Pillow commit `d8af3fc23a730dd5e9a6e556263e7be7d8de1c7e`.
- `/tmp/pillow_d8af3fc.patch` — public upstream commit patch fetched from GitHub during this inspection; relevant split hunks are around `PIL/Image.py`, `_imaging.c`, `libImaging/Bands.c`, `libImaging/Imaging.h`, and `libImaging/Storage.c`.
- `run_summaries.json` — metadata for all 18 provided Docent links.
- `timing_summary.json` — parsed base/patch/oracle medians and aggregate ratios from verifier stdout.
- `test_stdout/*.txt` — full verifier logs for each run, including hidden timing outputs and final `opt_commit` result.
- `trajectories/*.md` — full exported Docent trajectories, one per run.
- `scripts/export_docent_runs.py` — reproducible exporter for task metadata, trajectories, and stdout.
- `scripts/summarize_stdout.py` — reproducible parser for verifier timing summaries.

