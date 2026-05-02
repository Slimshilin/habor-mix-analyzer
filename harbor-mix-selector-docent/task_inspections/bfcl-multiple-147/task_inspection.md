# bfcl-multiple-147 — Task Inspection

> **Headline verdict:** REJECT (as currently shipped). The task is rendered such
> that the agent **cannot see the enum constraint** the verifier checks against,
> while the verifier strictly requires the enum value. The single success
> (1/18) is best explained as a lucky training-prior canonicalization, not
> enum-aware reasoning. This is a task-construction defect (prompt rendering
> drops schema constraints), not an agent capability bottleneck. A small
> targeted fix to the adapter would make the task solvable on its merits.

---

## 1. Task identity

- **Task ID**: `bfcl/bfcl-multiple-147` (source: BFCL v4 `multiple_147`)
- **Source**: Berkeley Function Call Leaderboard, "multiple" category
  (single-turn, pick the right function out of several and call it)
- **Difficulty**: medium
- **Category**: function_calling
- **Verifier**: auto-generated `tests/evaluate.py` from
  `BfclAdapter._generate_evaluate_script` — exit-code-driven; reward 1.0 iff
  exit 0
- **Agent timeout**: 300 s; verifier timeout 300 s
- **Adapter source**: `harbor/adapters/bfcl/adapter.py` (also in `TB3/`,
  `harbor-agent-compat/`)
- **Auditor (Gemini) verdict**: `accept` ("high-quality function-calling task...
  the success of GPT-5.4 proves the task is solvable... the verifier is
  well-implemented"). I disagree with this audit — see §6.

## 2. The user prompt

> "Get me the directions from New York to Los Angeles avoiding highways and
> toll roads."

## 3. Ground truth (BFCL upstream, recovered from verifier `Expected one of:` line)

```python
ground_truth = [
  {
    "map_service.get_directions": {
      "start": ["New York", "New York, NY", "NYC"],
      "end":   ["Los Angeles", "LA"],
      "avoid": [["highways", "tolls"], ["tolls", "highways"]]
    }
  }
]
```

The oracle solve.sh writes only the first acceptable value of each parameter:

```json
[{"map_service.get_directions": {"start": "New York", "end": "Los Angeles",
                                  "avoid": ["highways", "tolls"]}}]
```

## 4. Verifier behaviour (auto-generated `evaluate.py`)

- Compares predicted-list and ground-truth-list **positionally**, lengths must
  match.
- Function name normalised by replacing `.` with `_`.
- Per parameter, predicted value must `values_equal` to *any one* of the
  acceptable values listed in the BFCL ground truth.
- `values_equal` does direct equality, numeric coercion, case-insensitive
  string equality, and recursive **positional** list comparison.
- Crucially, the verifier does **not** itself sort or set-compare lists — both
  orderings of `avoid` are accepted only because BFCL upstream redundantly
  lists both `["highways","tolls"]` and `["tolls","highways"]` as acceptable
  values. (For 3+-element list parameters this redundancy would not save the
  task; it would become brittle.)
- Synonyms for `start`/`end` are accepted because BFCL ground truth lists
  multiple acceptable strings ("NYC", "LA", etc.).
- Empty string `""` in `acceptable_values` is treated as "parameter is optional
  and may be omitted".

The verifier is *itself* reasonable. The defect is upstream of it (§6).

## 5. Run inventory (all 18 runs)

Pulled by DQL from collection `640e920a-aef3-4b7c-9487-69899ef19e9d`, filtered
to `task_name = 'bfcl/bfcl-multiple-147'`. Reward 1.0 = pass, 0.0 = fail.

| run_id (short) | agent       | model                  | reward | predicted `avoid`        | function key written      | notes                   |
|----------------|-------------|------------------------|--------|--------------------------|---------------------------|-------------------------|
| d2193d50       | claude-code | claude-opus-4-6        | 0.0    | `["highways","toll roads"]` | `map_service.get_directions` |                         |
| 17dedc73       | claude-code | claude-opus-4-6        | 0.0    | `["highways","toll roads"]` | `map_service.get_directions` |                         |
| 29dff9f1       | claude-code | claude-opus-4-6        | 0.0    | `["highways","toll roads"]` | `map_service.get_directions` |                         |
| **06674887**   | **codex**   | **gpt-5.4**            | **1.0**| **`["highways","tolls"]`** | `map_service.get_directions` | **only success**         |
| 305f4864       | codex       | gpt-5.4                | 0.0    | `["highways","toll roads"]` | `map_service.get_directions` |                         |
| cd5f142a       | codex       | gpt-5.4                | 0.0    | `["highways","toll roads"]` | **literal `"function_name"`** | second, orthogonal bug |
| ecce88d2       | gemini-cli  | gemini-3.1-pro-preview | 0.0    | `["highways","toll roads"]` | `map_service.get_directions` |                         |
| 1382d078       | gemini-cli  | gemini-3.1-pro-preview | 0.0    | `["highways","toll roads"]` | `map_service.get_directions` |                         |
| 534c7b1e       | gemini-cli  | gemini-3.1-pro-preview | 0.0    | `["highways","toll roads"]` | `map_service.get_directions` |                         |
| 06221ea7       | terminus-2  | claude-opus-4-6        | 0.0    | `["highways","toll roads"]` | `map_service.get_directions` |                         |
| 30aad61e       | terminus-2  | claude-opus-4-6        | 0.0    | `["highways","toll roads"]` | `map_service.get_directions` |                         |
| df9f8232       | terminus-2  | claude-opus-4-6        | 0.0    | `["highways","toll roads"]` | `map_service.get_directions` |                         |
| 62ff5cea       | terminus-2  | gemini-3.1-pro-preview | 0.0    | `["highways","toll roads"]` | `map_service.get_directions` |                         |
| ea1e7753       | terminus-2  | gemini-3.1-pro-preview | 0.0    | `["highways","toll roads"]` | `map_service.get_directions` |                         |
| 4466fcca       | terminus-2  | gemini-3.1-pro-preview | 0.0    | `["highways","toll roads"]` | `map_service.get_directions` |                         |
| 81c2b53f       | terminus-2  | gpt-5.4                | 0.0    | `["highways","toll roads"]` | `map_service.get_directions` | wrote "tolls" in plan, "toll roads" in shell |
| 74af1b2d       | terminus-2  | gpt-5.4                | 0.0    | `["highways","toll roads"]` | `map_service.get_directions` |                         |
| be59edf2       | terminus-2  | gpt-5.4                | 0.0    | `["highways","toll roads"]` | `map_service.get_directions` |                         |

Counts: 1 pass, 17 fail. Per model: claude-opus-4-6 0/6, gemini-3.1-pro 0/6,
gpt-5.4 1/6 (only the codex harness, only one of three replicates).

## 6. The critical finding (root cause)

**The `avoid` enum `["tolls","highways","ferries"]` is NOT in the rendered
prompt.** I retrieved B0 of two runs verbatim
(`d2193d50` claude-code, `06674887` codex) and the function spec the agent
sees is:

```
- `avoid` (array, Optional): Route features to avoid. Default is an empty array.
```

That is the entire enum-related signal. No `enum: [...]`, no
"items must be one of ...", no JSON Schema, nothing. The verifier is checking
against a constraint that was withheld from the model.

The defect is in `BfclAdapter._format_functions_for_instruction`
(`harbor/adapters/bfcl/adapter.py:260-292`). It iterates a function's
`properties` and emits only `(param_name, param_type, required, description)`
— it never recurses into `items.enum`, `enum`, `oneOf`, `anyOf`, nested
`properties`, `format`, `pattern`, `default`, etc. So *every* BFCL schema
constraint beyond bare type+description is silently dropped before being
shown to the agent.

For comparison: the run's `metadata_json -> 'task' -> 'instruction'` field
contains a *different* version of the instruction in which the BFCL JSON
schema (with enum) appears verbatim. The agent did not see that version. So
the metadata can mislead reviewers (probably what happened to the Gemini
audit) — the agent's actual context omits the enum.

## 7. Per-run behavioural analysis (surface vs. root cause)

### 7a. Surface failure mode (17/18 runs)

All 17 failing runs produce the identical JSON
`{"start": "New York", "end": "Los Angeles", "avoid": ["highways", "toll roads"]}`.
At the surface level, they "lifted the user phrase 'toll roads' verbatim
into the array".

### 7b. Root cause: the enum is missing, not the reasoning

Across all six harness/model combinations the trajectories are short
(4–9 blocks) and uniform:

- **claude-code / claude-opus-4-6 (3 runs)**: 6-block trajectories. One-line
  reasoning ("Write the appropriate function call to result.json"), then a
  single `Write` tool call. No reflection, no schema introspection. The three
  runs are byte-identical except for tool-call UUIDs.
- **codex / gpt-5.4 (3 runs)**: 6-block trajectories. One-shot
  `printf > /app/result.json`. The success run says only "I'm mapping the
  request to the provided function schema" — no enum mentioned. The failed
  runs do the same thing and produce "toll roads". Run `cd5f142a` additionally
  emitted the **literal placeholder `"function_name"`** as the function key
  — see §7c.
- **gemini-cli / gemini-3.1-pro (3 runs)**: 4-block trajectories. Slightly
  more verbose chain-of-thought than the other agents but on the `avoid`
  value still parrots "highways and toll roads" verbatim. One run uses
  `echo`, two use `write_file`; content identical.
- **terminus-2 / claude-opus-4-6 (3 runs)**: ~5 blocks. Plan + single
  `echo > result.json` + `mark_task_complete`. Identical to claude-code's
  output despite different harness — confirming the harness is irrelevant.
- **terminus-2 / gemini-3.1-pro (3 runs)**: ~5 blocks. Identical output to
  gemini-cli — again, harness-invariant.
- **terminus-2 / gpt-5.4 (3 runs)**: 5–9 blocks. Most interesting:
  `81c2b53f` actually wrote `["highways", "tolls"]` in its prose plan in
  block B1, then *regressed* to `"toll roads"` in the actual `echo` command.
  Strong evidence that gpt-5.4 has the right token in its prior but doesn't
  reliably commit to it without an enum cue. The remaining two terminus-2
  gpt-5.4 runs never mention "tolls" at all.

So at the **root-cause** level the failure is uniform across all 17 runs:
the agent had no enum signal in its context, so canonicalising "toll roads"
to "tolls" required guessing from training-data prior on map APIs. Most
models / most samples did not guess the right token.

### 7c. The single success — was it skill?

The success (`06674887`, codex/gpt-5.4) sees the same enum-less prompt as the
17 failures. Its visible reasoning is just one terse sentence ("I'm mapping
the request to the provided function schema and writing the required JSON
payload to `/app/result.json`."). It then writes `["highways","tolls"]`
without any reasoning visible about why "tolls" rather than "toll roads".
Best explanation: gpt-5.4 has strong prior knowledge of common map-API
enum vocabularies (Google Maps' `avoid=tolls|highways|ferries` is the
canonical example). The other 5 of 6 gpt-5.4 runs (across both harnesses)
did *not* hit that prior. So it is sampling variance over a one-shot
generation, not a capability the other models lack. Treating 1/18 as a
demonstration of solvability is a Type I error.

### 7d. The orthogonal bug in `cd5f142a`

`cd5f142a` (codex/gpt-5.4) wrote the literal string `"function_name"` as the
top-level key. It copy-pasted the placeholder from the instruction's Format
line:

> `Format: - If a function applies: [{"function_name": {"param1": "value1"}}]`

The example *immediately below* uses `get_weather` (`echo '[{"get_weather":
{"city": "NYC"}}]' > /app/result.json`) and would have disambiguated, but
the agent never read it. This is a separate, second prompt-construction
weakness: the Format line uses unmarked literal placeholders (`function_name`,
`param1`, `value1`) where templating convention would use `<function_name>`,
`<param>`, `<value>` or an English gloss "Replace `function_name` with the
actual function name". This bug would presumably surface on other BFCL tasks
too.

## 8. Answers to the diagnostic questions

### Q1. How close did the agents get?

Very close *operationally* — every run produced syntactically valid JSON at
`/app/result.json` with the right function name (except `cd5f142a`'s
placeholder-literal bug), the right `start`, the right `end`, and a
two-element `avoid` array containing the right concept. The only thing
wrong was the lexeme `"toll roads"` instead of `"tolls"`. So the gap to
success is exactly one string substitution. From a behavioural standpoint
the models *understand* the request perfectly — they cannot guess the
correct vocabulary token because it is hidden from them.

### Q2. Variation across agent×model

Performance is uniform: 0/3 for every (agent, model) pair except codex/gpt-5.4
which got 1/3. There is no meaningful harness signal (claude-code and
terminus-2 with the same model produce the same answer, terminus-2 and
gemini-cli with gemini-3.1 produce the same answer). The only inter-model
difference visible is that gpt-5.4 occasionally writes "tolls" in its
prose reasoning (e.g. `81c2b53f`'s B1 plan) but doesn't always carry that
to the final command — suggesting it has a partial training-data prior
on the canonical token that the other two models lack. That is a real
between-model capability difference, but it is so small (1/6 of gpt-5.4
runs land the right token) that it is barely visible above noise.

**Surface vs root**:
- **Surface**: every model wrote `"toll roads"` instead of `"tolls"`.
- **Root**: the prompt renderer drops the `enum` constraint, so the
  agent has no signal to canonicalise. The "string mismatch" is downstream
  of an information-loss bug in task construction.

### Q3. Concrete behaviour vs. test code

- Predicted (17/18): `[{"map_service.get_directions": {"start": "New York",
  "end": "Los Angeles", "avoid": ["highways", "toll roads"]}}]`
- Expected (any of): `avoid` ∈ `[["highways","tolls"], ["tolls","highways"]]`
- The auto-generated `evaluate.py::compare_parameters` calls
  `values_equal(["highways","toll roads"], ["highways","tolls"])` which
  recurses element-by-element: `values_equal("highways","highways")` → True,
  `values_equal("toll roads","tolls")` → tries `==` (no), float coercion
  (no), case-insensitive string equality `"toll roads".lower() ==
  "tolls".lower()` (no) → returns False. Match fails. Loop tries the second
  acceptable value `["tolls","highways"]`, also fails. `compare_parameters`
  returns False, exit 1, reward 0.

  ```python
  # tests/evaluate.py (auto-generated)
  def values_equal(v1, v2):
      if v2 == "" or v2 is None: return True
      if v1 == v2: return True
      try:
          if float(v1) == float(v2): return True
      except (ValueError, TypeError): pass
      if str(v1).lower() == str(v2).lower(): return True
      if isinstance(v1, list) and isinstance(v2, list):
          if len(v1) != len(v2): return False
          return all(values_equal(a, b) for a, b in zip(v1, v2))
      return False
  ```

  The test as written cannot accept "toll roads" no matter how the verifier
  is invoked.

- For the success: `values_equal("tolls","tolls")` → True; both list elements
  match; `compare_parameters` returns True; exit 0; reward 1.

- For `cd5f142a`'s "function_name" bug: `compare_function_calls` checks
  `pred_func_name_norm == gt_func_name_norm`, i.e.
  `"function_name" == "map_service_get_directions"` → False; fail at the
  function-name check before parameter comparison even runs.

### Q4. Inferrable from environment? Solvable by a "super capable being"?

- The token `"tolls"` is **not** inferrable from the rendered prompt. The
  prompt's `avoid` description is a free-form English sentence ("Route
  features to avoid") with no enumeration of valid values. There is no
  natural-language clue ("must be one of...", "valid values are..."), no
  JSON Schema, no system-prompt constraint. The user's surface phrase
  "highways and toll roads" actively suggests `["highways","toll roads"]`
  as the most faithful translation.
- Could a super capable being still solve it? Only by injecting external
  knowledge — e.g., recognising that this is BFCL, that BFCL maps to
  Google-Maps-style enums, and that the canonical token is `tolls` not
  `toll roads`. That is not "inferring from the environment"; it is
  guessing from training prior. **The task is therefore not theoretically
  self-contained as currently rendered.**
- Conclusion: this is a **broken task** in its current form. The verifier's
  ground truth requires information the agent never receives. The single
  passing run is consistent with random sampling over training-prior
  guesses, not with capability that the other models lack.

### Q5. Proposed fixes

Three fix candidates, ranked by quality:

1. **Best fix (one-line behavioural change in the adapter): emit enum and
   item-type information when formatting parameters.** Modify
   `harbor/adapters/bfcl/adapter.py::_format_functions_for_instruction` so
   that for each parameter it also surfaces:

   - `items.type` for arrays (so the agent knows "array of strings" vs
     "array of objects")
   - `items.enum` for arrays (the case that breaks this task)
   - `enum`, `oneOf`, `anyOf` at the property level
   - `default` if present

   For this task the bullet would become:

   ```
   - `avoid` (array of [tolls|highways|ferries], Optional): Route features
     to avoid. Default is an empty array.
   ```

   Predicted effect: every model would produce the correct enum tokens. The
   1/18 → high-pass-rate jump would prove that the failure was an
   information-availability bug, not a capability bottleneck. This is the
   *correct* fix because it is faithful to BFCL's spec and does not weaken
   the test.

2. **Better fix (more invasive): drop the markdown reformatter and embed
   the raw BFCL function JSON directly.** This is what BFCL's official
   evaluator does, and matches what the `metadata_json -> 'task' ->
   'instruction'` field already contains. It preserves *all* schema
   constraints (enums, nested objects, format, pattern, defaults). It also
   eliminates the placeholder-vs-example confusion that bit `cd5f142a`,
   because the BFCL schema gives the model the function names directly.

3. **Inferior compensatory fix (verifier-side): accept "toll roads" as a
   synonym for "tolls".** This *would* make the task pass, but it defeats
   the BFCL contract — testing an agent's ability to map natural language
   to a strict schema vocabulary. It would also have to be applied
   per-task per-synonym, which is unmaintainable. Not recommended.

A small additional fix worth bundling with #1 or #2:

4. **Tighten the Output Format example.** Replace
   `[{"function_name": {"param1": "value1"}}]` with
   `[{"<function_name>": {"<param>": <value>}}]` or an English gloss like
   "Replace `function_name` with the actual function name from the list
   above." This would have prevented `cd5f142a`'s literal-placeholder bug
   and would protect all other BFCL tasks from the same failure mode.

## 9. Verdict on the question that matters

> Is the agent failure because of the task itself or the agent capability bottleneck?

**Task itself.** Specifically, the prompt-rendering pipeline strips the
`enum` constraint that the verifier's ground truth depends on, so 17 of 18
agents (across three frontier models and four harnesses) write a token they
have no way to know is wrong. The single 1/18 success is best explained as
training-prior sampling luck (canonical Google-Maps-style enum vocabulary),
not as a capability the other models lack — strongly supported by the
observation that the *same* gpt-5.4 model fails 5 of 6 times, and that
even the success run shows no enum-aware reasoning in its trace.

A small, surgical fix (emit enum + item-type information when rendering
function specs in `_format_functions_for_instruction`) would (a) make this
task solvable on its merits, (b) likely fix every other BFCL task that
relies on enum constraints, and (c) leave the strict-enum test contract
intact. Until that fix lands, this task should not be in the evaluation
mix; it is not measuring what it appears to measure.

## 10. Generalisation warning

This is almost certainly not specific to `multiple_147`. The same
prompt-rendering bug affects every BFCL task whose ground truth depends on
*any* JSON-Schema constraint beyond bare type+description: `enum`, `oneOf`,
`anyOf`, nested `items` constraints, `format`, `pattern`, numeric `minimum`/
`maximum`, default values, and nested `properties` for object-typed
parameters. A task-quality sweep should re-audit the BFCL accept-bucket with
this lens — many tasks tagged "agents fail because they don't follow the
schema" may actually be tasks where the schema was never shown to the agent.

---

## 11. Files in this folder

- `task_inspection.md` — this document
- `instruction.md` — the task instruction template **as stored in metadata**
  (full BFCL JSON, with enum)
- `rendered_prompt_to_agent.md` — what the agent **actually receives** at
  B0 (markdown reformatted, enum stripped) — this is the version that drives
  the failure
- `instruction_template.md` — the harbor `template/instruction.md` with
  `__TASK_DESCRIPTION__` / `__FUNCTION_DEFINITIONS__` placeholders
- `oracle_solution.json` — the ground-truth JSON the oracle solve.sh writes
- `verifier_ground_truth.txt` — the full per-parameter acceptable values
  reconstructed from the verifier's "Expected one of" output, plus a
  walkthrough of `evaluate.py`'s comparison logic
- `adapter.py` — the BFCL adapter source, including the buggy
  `_format_functions_for_instruction`
- `task.toml` — task metadata template
- `solve.sh`, `test.sh` — task templates
