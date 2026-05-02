# omnimath_20 — key task files

The task is generated dynamically from the HuggingFace `KbsdJames/Omni-MATH` dataset (split `test`, index 20) by the adapter at `/home/shilin/T-Bench/TB3/harbor/adapters/omnimath/`. There is no static per-task directory checked into the repo; everything below is what gets materialized at run time.

## Task-generation entrypoint
- `/home/shilin/T-Bench/TB3/harbor/adapters/omnimath/adapter.py` — `OmniMathAdapter._prepare_task` materializes `instruction.md`, `tests/{test.sh, llm_judge.py, ground_truths.json}`, `solution/solve.sh`, `task.toml`, `environment/Dockerfile`.
- `OmniMathTask.eval_mode = "llm_verifier"` — LLM-judge grading, no string match.
- Output dir name: `omnimath_{index}` → `omnimath_20`.

## Materialized files for this trial (logical content)
- `instruction.md` — built from `template/instruction.md` by replacing `{problem}` with the dataset row. The exact prompt the agent sees (verified verbatim from agent run `00c2f940`):
  ```
  # Mathematical Problem
  Consider pairs (f,g) of functions from the set of nonnegative integers to itself such that
   - f(0) ≥ f(1) ≥ ... ≥ f(300) ≥ 0
   - f(0)+f(1)+...+f(300) ≤ 300
   - for any 20 nonneg integers n_1,...,n_20: g(n_1+...+n_20) ≤ f(n_1)+...+f(n_20)
  Determine the maximum possible value of g(0)+g(1)+...+g(6000).
  [Sean Li]
  ## Instructions
  Solve ... write your final answer to /workspace/answer.txt. Plain text. Example: "What is 2+2?" → "4".
  ```
- `task.toml` (from `template/task.toml`):
  - `difficulty = "hard"`, `category = "math"`, `tags = ["omni-math"]`
  - `[agent] timeout_sec = 600.0`
  - `[verifier] timeout_sec = 60.0`
  - Verifier env: `OPENAI_API_KEY`, `MODEL_NAME = "gpt-5-mini-2025-08-07"`
- `tests/test.sh` (from `template/tests/test.sh`):
  - Runs `python3 /tests/llm_judge.py`, then writes `reward.txt` (falls back to 0.0 if `reward.json` missing).
- `tests/llm_judge.py` (from `template/tests/llm_judge.py`):
  - Loads `/workspace/answer.txt` (returns reward 0.0 on `FileNotFoundError` or empty).
  - Loads `/tests/ground_truths.json` (single problem with `eval_mode=llm_verifier`).
  - Calls `gpt-5-mini-2025-08-07` with `JudgeResponse {binary_score: bool}` structured output.
  - Grading prompt verbatim:
    ```
    You are given a question, target answer and a predicted answer. Your task is to compare the
    target answer with the predicted and assess if the predicted answer is correct or incorrect.
    Question: {question}
    Target Answer: {answer}
    Predicted Answer: {output}
    Respond only with valid JSON with the key binary_score
    ```
- `tests/ground_truths.json` (rendered for index 20):
  - `question`: the problem statement above
  - `ideal_answer`: `"115440"` (the dataset's `answer` field)
  - `eval_mode`: `"llm_verifier"`
- `solution/solve.sh` (from `template/solution/solve.sh`):
  ```bash
  cat > /workspace/answer.txt << '__SOLUTION__'
  115440
  __SOLUTION__
  ```
- `environment/Dockerfile` (from `template/environment/Dockerfile`):
  - Base: `ghcr.io/laude-institute/t-bench/python-3-13:20250620`
  - Installs pytest, pydantic, openai, anthropic; bootstraps `uv 0.7.13`.
  - **Notable**: numpy is NOT pre-installed (the agent must `pip install numpy` if needed). One terminus-2/opus run (`bfbebe46`) was crippled by this and fell back to pure-Python loops.

## Source dataset row (index 20)
- HuggingFace: `KbsdJames/Omni-MATH`, split `test`, row 20.
- `problem`: as quoted in instruction.md above.
- `answer`: `"115440"`.
- Origin: HMMT February 2024 Team Round Problem #10 (Sean Li). Not stated in the dataset row.

## Correct-solution sketch
- Define h = 20-fold infimal convolution of f. Then `g ≤ h` on every value, so `Σ g ≤ Σ h`.
- Optimal f is convex (a 2nd-difference unbounded-knapsack argument): items `B_j(x) = max(0, j-x)` have weight `j(j+1)/2` (sum f) and value `400·j(j+1)/2 - 190·j` (sum h for N=20). Value/weight is strictly increasing in `j` up to `j=24`.
- With sum budget 300 and `B_24` weighing exactly `24·25/2 = 300`, the unique knapsack optimum is `f(x) = max(0, 24-x)`.
- Then `h(k) = 20·f(k/20)` smoothed → `h(k) = max(0, 480-k)`, and `Σ_{k=0}^{6000} h(k) = 480·481/2 = 115440`. ✓
