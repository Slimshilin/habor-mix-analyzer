# Task Inspection: `replicationbench__ls_cal__nwp`

## Verdict

**Task Quality:** Conditional Accept / Needs Revision Before Calling It High-Quality  
**Primary Bottleneck:** Agent capability bottleneck, with real task-spec clarity issues  
**Single Most Valuable Answer:** The observed agent failures are **primarily due to agent capability bottlenecks**, not because the task is theoretically broken. However, I would not endorse Gemini's "high-quality as-is" judgment without caveats: the task has fixable environment/specification defects that make failure more likely and make the task less clean as a benchmark item.

The task is solvable: 1 of 18 runs succeeded, and the successful run computed `[261.56, 57.34, 158.29, 1163.99, 302.20]`, comfortably within the verifier tolerance of `[10, 10, 10, 10, 10]` against gold `[264.3, 57.4, 157.6, 1157.2, 302.3]`. That success is important evidence that a sufficiently careful agent can infer the needed physics, parse the data, apply the equations, and produce a passing answer.

But the task is not pristine. The instructions say to use `/resources`, while the Dockerfile places resources under `/app/resources`, and several agents initially found `/resources` missing. The prompt also leans on "techniques of the last few tasks" and equation numbers rather than making the task fully self-contained in the prompt. Agents can recover by inspecting `/app/resources` and the assets, so this is not fatal, but it is a benchmark-quality blemish.

My binary recommendation would be: **keep the task only after small specification/environment fixes.** If forced to classify the current artifact as-is, I would call it **borderline acceptable but not high-quality**.

## Key Files Written

- `task_files/instruction.md`: saved task prompt.
- `task_files/test.sh`: saved verifier wrapper.
- `task_files/solve.sh`: saved oracle output script showing the hidden expected vector.
- `task_files/task.toml`: saved task metadata.
- `task_files/Dockerfile`: saved environment definition.
- `run_summaries.json`: run-level agent/model/outcome/prediction summary for all 18 links.
- `runs/*.md` and `runs/*.json`: full exported trajectories and metadata for all 18 Docent runs.
- `scripts/export_docent_runs.py`: exporter used to freeze the Docent evidence locally.

## Task And Verifier

The task asks the agent to compute the average noise wave parameters:

`[Tunc, Tcos, Tsin, TNS, TL]`

from calibrator PSDs, calibrator reflection data, MTS switch measurements, cable realized gain, and corrected cable/load temperatures. The required calibrators are:

`cold, hot, open, short, r25, r100, c2r27, c2r36, c2r69, c2r91`

The verifier is a generic ReplicationBench numeric-output check. It requires `/app/result.json` with key `"value"` and compares it against a hidden config:

```python
result_path = Path("/app/result.json")
assert result_path.exists(), "Agent must write /app/result.json with {'value': ...}"
result = json.loads(result_path.read_text())
assert "value" in result, "result.json must contain key 'value'"
comparison_passed = _compare_values(result["value"], expected, tol)
assert comparison_passed, (
    f"Result {result['value']} differs from expected {expected} "
    f"beyond tolerance {tol}"
)
```

Gold and tolerance observed from verifier output:

- Expected: `[264.3, 57.4, 157.6, 1157.2, 302.3]`
- Tolerance: `[10.0, 10.0, 10.0, 10.0, 10.0]`

This is a fair verification target for the scientific result, but it is all-or-nothing: a run with four nearly perfect values and one coefficient off by 11 K still fails.

## How Close Agents Got

The run set is not a uniform failure pile. Several agents were extremely close on most values but missed one or two equation-convention-sensitive parameters.

- **1/18 succeeded.** Run 01 got all five within tolerance.
- **Several near misses:** Runs 02, 03, 05, 08, 13, 14, 15, and 18 had multiple correct or near-correct components, usually `Tunc`, `TNS`, and `TL`, but failed on `Tcos`/`Tsin` or a `TNS` shift.
- **Clear formulation failures:** Runs 04, 06, 07, 12, 16, and 17 produced qualitatively wrong physics, such as negative `Tunc`, negative/low `TL`, or `TNS` hundreds of K too low.
- **Give-up/null failures:** Runs 10 and 11 wrote `null` after deciding their calculations were untrustworthy.

The dominant closeness pattern is: agents can load the dataset and often recover the scale of `Tunc`, `TNS`, and `TL`, but fail on the exact Eq. 5 rearrangement, correlated-noise sign/phase convention, MTS reference plane, or cable-temperature interpretation.

## Complete Run Review

| Run | Agent / Model | Outcome | Submitted Value | Surface Failure | Root Cause |
| --- | --- | --- | --- | --- | --- |
| 01 | claude-code / claude-opus-4-6 | Success | `[261.56, 57.34, 158.29, 1163.99, 302.20]` | None for grading. | Correctly compared MTS/reference-plane variants and chose the formulation with the right correlated-term orientation. Blocks 78-80 show approach comparison and final value. |
| 02 | claude-code / claude-opus-4-6 | Failure | `[265.28, 15.87, 150.14, 1162.86, 301.70]` | `Tcos` off by -41.53 K. | Wrong reference-plane or phase convention after testing de-embedding/PSD-correction variants. Blocks 104-106 compare variants; block 112 writes final JSON. |
| 03 | claude-code / claude-opus-4-6 | Failure | `[262.55, 67.96, -134.02, 1157.64, 303.05]` | `Tsin` wrong sign/magnitude; `Tcos` barely outside tolerance. | Incorrect correlated-noise sign/phase convention and incomplete MTS treatment. Block 93 explicitly rationalizes not using key MTS measurements fully; block 99 summarizes wrong result. |
| 04 | terminus-2 / claude-opus-4-6 | Failure | `[935.84, 69.96, -142.08, -43.69, 302.98]` | Huge `Tunc`, negative `TNS`. | Chose a `Ps/Pl` formulation because `TL ~= 303 K` looked plausible, despite noting it ignored the noise-source PSD. Blocks 68-73 show the bad choice; block 74 shows final JSON. |
| 05 | terminus-2 / claude-opus-4-6 | Failure | `[262.79, 84.23, 9.47, 1162.56, 301.26]` | `Tcos` high and `Tsin` collapsed. | Simplified MTS gain correction and wrong correlated-term phase/orientation, chosen by residual/physical plausibility rather than exact equation matching. Blocks 42-45 show final model and variant choice. |
| 06 | terminus-2 / claude-opus-4-6 | Failure | `[-263.72, 34.88, -70.74, 1163.00, 39.72]` | Negative `Tunc`, very low `TL`, bad correlated terms. | Wrong Eq. 5 structure, with `Tunc` and load/noise terms placed incorrectly. Blocks 80, 83, and 85 show the bad clean solver and the agent noticing but submitting implausible values. |
| 07 | codex / gpt-5.4 | Failure | `[-306.04, -8.73, -9.56, 300.46, 304.05]` | First four values wrong; `TNS` collapsed near ambient. | Incorrect Eq. 5 linearization. The final design matrix misplaced load/noise-source terms. Blocks 111 and 127-128 show solver and final JSON. |
| 08 | codex / gpt-5.4 | Failure | `[268.73, 111.16, 149.62, 1106.37, 303.79]` | Close-ish, but `Tcos` and `TNS` fail. | Selected a 50-130 MHz band and a temperature interpretation by residual/physical plausibility, despite task wording saying average over frequency. Blocks 101, 116, and 117 show the variant sweep and selection. |
| 09 | codex / gpt-5.4 | Failure | `[-266.57, -57.46, -157.88, 1157.68, 302.27]` | `TNS`/`TL` right, first three sign-flipped. | Eq. 5 rearrangement sign error: noise-wave terms on the wrong side of the solve. Blocks 20-22 quote Eq. 5; blocks 60-64 show design matrix and final result. |
| 10 | terminus-2 / gpt-5.4 | Failure | `null` | Submitted `{"value": null}`. | Could not recover exact calibration equations/constants, guessed a noise-source scale, saw absurd results, and gave up. Blocks 15-20 show guessed `Tnoise = Tload + 1000` and overwrite with null. |
| 11 | terminus-2 / gpt-5.4 | Failure | `null` | Submitted `{"value": null}`. | Heuristic cold/hot anchoring gave inconsistent physical checks, so the agent aborted. Block 18 shows inconsistent inferred temperatures; blocks 19-21 overwrite with null. |
| 12 | terminus-2 / gpt-5.4 | Failure | `[88.07, 85.08, -9.94, 174.44, -86.06]` | Most values qualitatively wrong. | Reconstructed an approximate model instead of exact Eq. 5, simplified MTS, and effectively disabled cable thermal-gradient correction. Blocks 19-22 show approximate model and final JSON. |
| 13 | gemini-cli / gemini-3.1-pro-preview | Failure | `[266.19, 165.28, 19.21, 1156.68, 302.45]` | `Tcos` inflated, `Tsin` collapsed; other terms close. | Mis-derived correlated Eq. 5 terms and over-trusted plausibility. Blocks 135-148 show solver and final JSON. |
| 14 | gemini-cli / gemini-3.1-pro-preview | Failure | `[267.58, 161.15, 18.86, 1128.71, 304.09]` | Same correlated-term failure plus `TNS` low by ~28 K. | Kept revising temperature interpretation and Eq. 5 scaling, then accepted plausible values without a decisive consistency check. Blocks 188-202 show this exploration and final JSON. |
| 15 | gemini-cli / gemini-3.1-pro-preview | Failure | `[266.19, 165.24, 19.56, 1156.59, 302.45]` | Nearly duplicate of run 13: `Tcos`/`Tsin` wrong. | Same Eq. 5 correlated-term scaling/orientation error. Blocks 125-136 show final solver and output. |
| 16 | terminus-2 / gemini-3.1-pro-preview | Failure | `[288.10, 80.72, 92.20, 734.56, 306.13]` | `TNS` low by 423 K; `Tunc` and `TL` elevated. | Confused `Gamma_source` vs load-end `Gamma_R`, used cable-model `source_*.s1p` as calibrator reflection, then forced cable reciprocity after NaNs. Blocks 50-58 show NaNs and the forced symmetry fix. |
| 17 | terminus-2 / gemini-3.1-pro-preview | Failure | `[291.88, 15.40, 37.09, 699.37, 306.60]` | Severe `TNS` underestimation and bad correlated terms. | Same conceptual mix-up as run 16, compounded by choosing a 50-130 MHz mask not requested by the task output. Blocks 43-45 and 63-66 show band choice and final JSON. |
| 18 | terminus-2 / gemini-3.1-pro-preview | Failure | `[267.54, 161.19, 18.87, 1128.74, 304.09]` | `Tcos`/`Tsin` wrong and `TNS` low. | Re-derived Eq. 5 incorrectly and made questionable cable temperature choices. Blocks 44-50 show solver revisions and final output. |

## Performance Variation And Failure Modes

The agents used broadly similar high-level approaches:

1. Explore `/assets/ls_cal`.
2. Inspect calibrator directories and S-parameter/PSD formats.
3. Look for or infer Equations 5, 9, 10, 11 from `/app/resources` or source text.
4. Write a Python solver over 12,288 frequency points.
5. Solve a frequency-wise least-squares system for five parameters.
6. Average the frequency-wise parameters and write `/app/result.json`.

The split was not in basic data loading. Most agents found the calibrator files and PSD arrays. The split was in exact scientific modeling.

### Common Surface Failures

- Wrong sign for `Tunc`, `Tcos`, and `Tsin` (run 09).
- Rotated or swapped correlated terms, with `Tcos ~= 160` and `Tsin ~= 19` instead of `Tcos ~= 57` and `Tsin ~= 158` (runs 13, 15, 18).
- Selecting a plausible but wrong frequency band, especially 50-130 MHz (runs 08, 17).
- Producing physically implausible outputs like negative `Tunc`, negative `TNS`, or `TL ~= 40 K` (runs 04, 06, 07, 12).
- Submitting `null` after failing to derive a trustworthy model (runs 10, 11).

### Root Causes

- **Insufficient equation discipline.** Many agents paraphrased Eq. 5 rather than deriving the exact linear system with correct signs and normalization.
- **Reference-plane confusion.** The successful run explicitly compared MTS/reference-plane variants and chose the right one. Many failures chose based on small residual differences or physical plausibility.
- **Correlated-term phase/orientation mistakes.** `Tcos` and `Tsin` are the most sensitive terms; failures often got the scale of `TNS`/`TL` right while rotating or sign-flipping these components.
- **Cable temperature ambiguity mishandled.** Eq. 11 needs a resistor/load temperature and cable temperature, while each calibrator directory exposes a single `temperature.txt`; capable agents inferred the convention from resources, weaker agents guessed.
- **Poor validation strategy.** Many agents saw residuals of a few K or a plausible `TL ~= 303 K` and stopped. The successful run compared multiple candidate formulations and selected the one that gave the correct global structure, not just a locally plausible parameter.

## Task Self-Containment

### Can a super capable being solve this from the current environment?

Yes. The success run proves this empirically. The assets contain the needed calibrator PSDs, S-parameters, MTS measurements, cable models, temperatures, and paper/resource context. A sufficiently capable agent can discover `/app/resources`, recover the equations, map the calibrators, and compute the target.

### Are hidden tests asking for something inferable?

Mostly yes. The hidden test only checks the five-number numerical result implied by the task. It does not require an arbitrary formatting trick beyond `{"value": [...]}`. The tolerance is reasonable for this task.

The hidden expected vector itself is not visible to the agent, but it is reproducible by correct computation. This is acceptable for a scientific-replication task.

### Does anything make the task theoretically impossible?

No. The observed issues make it easier for weaker agents to fail, but not impossible:

- `/resources` path mismatch: discoverable because `/app/resources` exists and the Dockerfile says resources are copied there.
- Equation numbering/context: recoverable from paper/resources.
- Single `temperature.txt` value despite Eq. 11 needing two temperatures: recoverable from the paper context and cable supplementary data, but not cleanly stated in the prompt.
- Frequency averaging range: the prompt says average over frequency, so full available frequency range is inferable, but agents familiar with the paper can be tempted by a narrower analysis band.

## Task Problems And Proposed Fixes

These fixes do not simplify the task. They make it complete and reduce accidental ambiguity.

1. **Fix the resource path mismatch.**
   - Current issue: prompt says `/resources`; environment exposes `/app/resources`.
   - Fix: either create a symlink `/resources -> /app/resources` in the Dockerfile or change the prompt to say `/app/resources`.
   - Impact: prevents early false-negative exploration and the null/give-up pattern seen in runs 10 and 11.

2. **Add a short equation appendix to the task prompt or resources README.**
   - Include the exact forms of Eq. 5, Eq. 9, Eq. 10, and Eq. 11 used for this dataset, including sign convention and reference plane.
   - Impact: preserves the scientific-computing challenge while removing equation-numbering and port-convention traps.

3. **Define the temperature-file convention.**
   - State whether `temperature.txt` is the resistor/load temperature, cable temperature, or thermocouple measurement, and how to infer the companion temperature for Eq. 11.
   - Impact: reduces arbitrary `T_res = T + 3`, `T_cab = T - 3`, and hot-cable ambient proxy guesses.

4. **Specify the averaging band.**
   - Current wording "average over frequency" implies all frequencies, but several agents used 50-130 MHz due to paper context.
   - Fix: say "average over all 12,288 frequency points in the provided files" or explicitly name the intended frequency range.
   - Impact: prevents plausible but wrong band-limited answers.

5. **Add non-oracle public sanity checks.**
   - Example: check only output schema, length five, all finite numbers, and perhaps broad physical ranges for `TL` and `TNS`.
   - Do not reveal the gold vector.
   - Impact: helps agents catch `null`, NaN, negative-load, and obvious formulation failures without making the task trivial.

## Final Assessment

I agree with Gemini on the main causal story: **most failures are agent capability bottlenecks.** The agents fail because they cannot reliably translate a dense scientific calibration procedure into the exact computation, not because the benchmark asks for unknowable information.

I disagree with Gemini's unqualified quality claim. The task is solvable and valuable, but not clean enough to call "high-quality" as-is. The resource path mismatch and implicit equation/temperature conventions are real task-quality defects. They did not cause the majority of failures, but they are enough that I would request revision before accepting this as a polished benchmark item.

**Bottom line:** retain the task after fixes. It is a strong discriminator of scientific reasoning, equation implementation, and validation rigor, but the current version is a conditional accept rather than a clean accept.
