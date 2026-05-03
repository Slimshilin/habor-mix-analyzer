# Task Context: `gso/gso-python-pillow--pillow-d8af3fc`

## Links Reviewed

- <https://docent.transluce.org/dashboard/640e920a-aef3-4b7c-9487-69899ef19e9d/agent_run/19b9442d-ae8a-4e77-992c-29d50736bc54>
- <https://docent.transluce.org/dashboard/640e920a-aef3-4b7c-9487-69899ef19e9d/agent_run/980b7fda-8273-42fc-8dc0-271f3046b965>
- <https://docent.transluce.org/dashboard/640e920a-aef3-4b7c-9487-69899ef19e9d/agent_run/f713d415-a3f8-4377-87a7-15a4584df8d1>
- <https://docent.transluce.org/dashboard/640e920a-aef3-4b7c-9487-69899ef19e9d/agent_run/832fb29d-1b98-417a-85b1-9346ebe93981>
- <https://docent.transluce.org/dashboard/640e920a-aef3-4b7c-9487-69899ef19e9d/agent_run/6f9577a6-64b2-4946-9920-f24d7c976e58>
- <https://docent.transluce.org/dashboard/640e920a-aef3-4b7c-9487-69899ef19e9d/agent_run/b2a38d2d-e444-43c2-bed8-73650a2a0e79>
- <https://docent.transluce.org/dashboard/640e920a-aef3-4b7c-9487-69899ef19e9d/agent_run/d8872b3a-a8ac-49c3-97fb-17101a59a24f>
- <https://docent.transluce.org/dashboard/640e920a-aef3-4b7c-9487-69899ef19e9d/agent_run/2e70536e-a5ac-42b8-9913-566e35132f6b>
- <https://docent.transluce.org/dashboard/640e920a-aef3-4b7c-9487-69899ef19e9d/agent_run/86156a24-2210-4405-8490-ddc11664cabc>
- <https://docent.transluce.org/dashboard/640e920a-aef3-4b7c-9487-69899ef19e9d/agent_run/35fbb005-8e97-4e31-b687-2a9705f57875>
- <https://docent.transluce.org/dashboard/640e920a-aef3-4b7c-9487-69899ef19e9d/agent_run/cf90d6d7-21bf-4e04-8a05-24d640329ff5>
- <https://docent.transluce.org/dashboard/640e920a-aef3-4b7c-9487-69899ef19e9d/agent_run/1f7ea0fc-62db-4fd7-8c6d-002fec298bd9>
- <https://docent.transluce.org/dashboard/640e920a-aef3-4b7c-9487-69899ef19e9d/agent_run/ef123134-3265-40cf-bb31-fc70ba11d480>
- <https://docent.transluce.org/dashboard/640e920a-aef3-4b7c-9487-69899ef19e9d/agent_run/27264558-50cf-4cb7-93ce-850b8f9a6295>
- <https://docent.transluce.org/dashboard/640e920a-aef3-4b7c-9487-69899ef19e9d/agent_run/e4a59aff-4ad8-4d19-a6e6-f842c96b3766>
- <https://docent.transluce.org/dashboard/640e920a-aef3-4b7c-9487-69899ef19e9d/agent_run/1ace91ca-0bf5-4a6c-a298-6614f8a81cf3>
- <https://docent.transluce.org/dashboard/640e920a-aef3-4b7c-9487-69899ef19e9d/agent_run/4fc922a1-8180-4651-a352-66bbbdb5a428>
- <https://docent.transluce.org/dashboard/640e920a-aef3-4b7c-9487-69899ef19e9d/agent_run/6f69a5bb-f1ab-457d-b4cd-66567cb87f5a>

## Local Evidence

- Exported task files: `task_files/`
- Exported trajectories: `trajectories/`
- Exported verifier output: `test_stdout/`
- Run metadata: `run_summaries.json`
- Parsed timing summary: `timing_summary.json`
- Public upstream oracle patch fetched during inspection: `/tmp/pillow_d8af3fc.patch`

## Task Summary

The prompt asks agents to optimize Pillow `Image.split()` for a benchmark that splits a mixture of `RGB`, `RGBA`, `LA`, `P`, `1`, skinny/tall/tiny images and records channel count, channel modes, and channel sizes. The baseline `PIL/Image.py::Image.split()` calls `self.im.getband(i)` once per band, which incurs repeated Python/C calls and repeated scans.

The verifier runs 11 hidden GSO tests, first on the base parent, then on the agent patch, then on the upstream target commit `d8af3fc23a730dd5e9a6e556263e7be7d8de1c7e`. Final reward follows `opt_commit`, meaning the patch must be close to the upstream commit's speed, not merely faster than baseline.

