# Task inspection — `seal0/48` (Mercury(I) chloride valency)

> **TL;DR — Verdict: ACCEPT with reservations.**
>
> The task is **5/18 (27.8%) pass-rate** and is conceptually sound: it asks "What is the valency of mercury in Mercury(I) chloride?" The expected answer `2` is supported by the rigorous IUPAC/Wikipedia *Valence (chemistry)* definition (each Hg in linear Cl–Hg–Hg–Cl forms 2 bonds), distinct from the oxidation state of +1. The instruction explicitly warns "web search results … may be conflicting, incomplete, or misleading — use your judgment", which is *the entire point of the task*. Successful agents treat that warning as a hint to do structural chemistry, not nomenclature lookup; failures conflate valency with oxidation state.
>
> **Three reservations** drag the verdict down from "clean accept":
> 1. **The LLM judge failed 18/18 with `Connection error.`** Every run silently fell back to a brittle string-match comparison. We never see the intended judge actually run. This is a test-infrastructure failure, not an agent failure — but it means the answer-grading channel for the entire task is currently a 1-token equality check, which is fragile to alternative correct phrasings (`+2`, `two`, `II`, `divalent`).
> 2. **The "correct" answer is genuinely contested in chemistry usage.** One gemini-cli run (`2afdbb8f`) retrieved a primary source stating *"in 24 papers, mercury in Hg2Cl2 is stated as a compound of monovalent mercury"* and another stating *"mercury is clearly divalent"* — both are authentic. The task hinges on a definitional choice (IUPAC structural valency vs. modern-usage = oxidation state). The instruction's warning is what makes that choice fair, but it is a tightrope.
> 3. **Same model behaves opposite ways across harnesses.** `gemini-3.1-pro-preview` is 3/3 in terminus-2 but 0/3 in gemini-cli. Even with full shell + web access, the gemini-cli runs anchor on the Roman numeral "(I)" first and never recover. The task is therefore as much a test of harness framing as agent capability — readers of this benchmark should keep that in mind.
>
> **Net call.** The task is intact and diagnostic. Failures are dominated by the **conflate-valency-with-oxidation-state** capability gap (12/13 failures) plus one calibration-under-conflicting-evidence failure. Apply Fix 1 (judge robustness) and the task gets cleaner; the underlying probe is sound.

---

## Files in this inspection directory

| File | Purpose |
|---|---|
| `instruction.md` | Verbatim agent-facing instruction text |
| `task.toml` | Task config (3600 s timeout, judge uses `ANTHROPIC_API_KEY`) |
| `test.sh` | Verifier shell script that calls `/tests/test_outputs.py` |
| `solve.sh` | Oracle solution (writes `2` to `/app/answer.txt`) |
| `dockerfile` | Base image (`python:3.12-slim` + `anthropic` package) |
| `task_inspection.md` | This file — the synthesised verdict |

---

## 0. Task summary

**What the task asks.** Answer the factual question: *What is the valency of mercury in Mercury(I) chloride?* Write the answer (a short factual response, no prose) to `/app/answer.txt`. Show reasoning before writing.

**Critical instruction snippet.**
> *"Note that web search results for this question may be conflicting, incomplete, or misleading — use your judgment to determine the most accurate answer."*

This is the diagnostic device. It is the entire signal that the task wants careful chemical reasoning, not nomenclature lookup.

**Oracle answer.** `2` (per `solve.sh`).

**Why 2 is correct.** Mercury(I) chloride has the empirical formula HgCl but is structurally a dimer Hg₂Cl₂ with linear connectivity Cl–Hg–Hg–Cl. Each Hg atom forms two single covalent bonds (one to Cl, one to the other Hg). Valency, in the rigorous IUPAC sense (= number of bonds an atom forms), is therefore **2**. The oxidation state, however, is **+1** (the Hg₂²⁺ dimer carries +2 charge shared between two Hg atoms). The Wikipedia *Valence (chemistry)* article literally has a table row stating *"Mercury(I) chloride | Hg2Cl2 | Hg = 2 (valence) | Hg = +1 (oxidation state) | Cl−Hg−Hg−Cl"* — this is the smoking gun the successful codex run dumped via `curl | grep`.

**How it's verified.** `test.sh` runs `python3 /tests/test_outputs.py`. The intended judge is an LLM (Anthropic API) — but **in all 18 runs the judge failed with `LLM judge failed: Connection error.`** and the script fell back to **string matching** between the agent's `/app/answer.txt` and the expected `2`. So the de-facto grading is `cat /app/answer.txt | strip == "2"`.

**Trial setup.** 18 runs, 6 stacks × 3 trials:
- terminus-2 × {claude-opus-4-6, gpt-5.4, gemini-3.1-pro-preview}
- gemini-cli × gemini-3.1-pro-preview
- codex × gpt-5.4
- claude-code × claude-opus-4-6

Both agent and verifier timeout: 3600 s (1 hour).

**Outcomes (full set, no missing).**

| Stack | Successes | Failures | Notes |
|---|---|---|---|
| terminus-2 / gemini-3.1-pro-preview | **3/3** | 0 | Researched + structural reasoning every time |
| terminus-2 / claude-opus-4-6 | 0/3 | 3 | Parametric only, no research, single-turn confidence |
| terminus-2 / gpt-5.4 | 0/3 | 3 | Parametric only, no research, identical 5-block runs |
| codex / gpt-5.4 | **2/3** | 1 | Successes did >15 web searches; failure had search bias toward "univalent" |
| gemini-cli / gemini-3.1-pro-preview | 0/3 | 3 | Including one 58-step run that found the right answer and reverted |
| claude-code / claude-opus-4-6 | 0/3 | 3 | Byte-identical 5-block parametric runs, never loaded WebSearch tool |
| **Total** | **5/18 (27.8%)** | **13/18** | |

---

## 1. How close are agents to succeeding?

This task is **trimodal**: agents are either (a) structurally correct, (b) parametric-shortcut wrong, or (c) extensively-researched-but-still-wrong. There is essentially no graded credit because the answer is a single integer string.

| Bucket | Trials | Distance to success |
|---|---|---|
| Pass — structural reasoning produced `2` | 5 | 0 |
| Parametric shortcut, never researched, wrote `1` | 12 | Far — never engaged with the warning |
| Researched extensively, retrieved correct evidence, still wrote `1` | 1 (`2afdbb8f`) | Closest of all the failures — had `2` mid-trajectory and flipped back |

**Important nuance: "research depth" alone does not predict success.**

- The 13-step codex failure (`9eece367`) ran 6+ web searches; it was wrong because its search queries got biased toward `"univalent"`/`"monovalent"` terms after the first round, leaving it in an echo chamber.
- The 58-step gemini-cli failure (`2afdbb8f`) ran ~50 shell commands, installed `ddgs` in a venv, hit Wikipedia/StackExchange/CrossRef, and at message B29/B43 explicitly wrote *"the valency of mercury in this compound is 2"* before flipping back.
- The cheapest success (`c8a95fa7`, $0.13, 14 messages) needed only one round of DuckDuckGo + structural reasoning from `Hg2Cl2 → Cl-Hg-Hg-Cl → 2 bonds`.

What separates pass from fail is **whether the agent (1) reads the prompt warning as a hint, (2) reasons structurally about the dimer, and (3) does not let modern-usage snippets override the rigorous definition.** None of (1)–(3) requires extensive research — the cheapest success is the existence proof.

---

## 2. Cross-agent variance: surface vs. root cause

I inspected all 18 trajectories at message-level depth via subagents (each got the full transcript and reported reasoning, tool use, and final answer). Findings split into 4 distinct failure pathways and 1 success pattern.

### 2a. Failure pathways

| # | Pathway | Trials | Surface symptom | Root cause |
|---|---|---|---|---|
| **A** | **Pure parametric shortcut, zero research** | 9 (3 t2-opus + 3 t2-gpt5 + 3 cc-opus) | Single-turn write of `1`; reasoning sentence equates valency with oxidation state | Conflates "valency" with "oxidation state" definitionally; reads "Mercury(I)" name as the answer; ignores "conflicting info" warning entirely |
| **B** | **Searched but echo-chambered into wrong answer** | 1 (codex `9eece367`) | 13 steps, 6+ web searches, wrote `1` | Later queries biased toward `"univalent"`/`"monovalent"` returned snippets that confirmed the wrong intuition; never opened the Wikipedia *Valence (chemistry)* table |
| **C** | **Naive search trust + tool-result anchoring** | 2 (gemini-cli `4c48aace`, `7f84fa0e`) | 4–5 steps, one Google search, wrote `1` | Google snippet returned literally `"valency (oxidation state) of mercury is +1"`; agent took the conflation at face value; one run had Google return empty and just gave up rather than try shell |
| **D** | **Extensively researched, found `2`, flipped back to `1`** | 1 (gemini-cli `2afdbb8f`) | 58 steps, retrieved verbatim *"mercury is clearly divalent"*, still wrote `1` | Calibration-under-conflicting-evidence failure: weighted *"24 papers say monovalent"* over the structural argument; **explicitly read the prompt's warning, then concluded that the structural-valency-of-2 was the misleading answer** (B89: "the structural arrangement hints at two. *That's the part that's 'misleading'*, apparently") |

### 2b. The success pattern

The 5 successes (3 terminus-2/gemini + 2 codex/gpt-5.4) all executed the same 4-step recipe:

1. **Read the warning as a hint.** Within the first reasoning block, identify the trick: "the Roman numeral suggests 1, but valency may differ from oxidation state."
2. **Structural argument.** Recognize Hg₂Cl₂ ⟹ Cl–Hg–Hg–Cl ⟹ each Hg forms 2 bonds.
3. **Confirm against an authoritative source.**
   - Wikipedia *Valence (chemistry)* table (codex `82860d03` via `curl | grep`; terminus-2/gemini `036cbd96` via `urllib`).
   - Or pure structural inference (terminus-2/gemini `c8a95fa7`, the cheapest success — never opened Wikipedia, just reasoned from formula).
4. **Write `2`** and resist the search-snippet pull toward `1`.

The decisive distinguisher is **step 1**: every successful run's first reasoning block contains an explicit "valency might differ from oxidation state" hypothesis. Every failure of pathway A jumps straight to "oxidation state ⟹ valency" without entertaining the distinction.

### 2c. Surface vs. root cause framing

- **Surface:** "agent answered `1` in 5 blocks, ~$0.02" — `5220b065`, `996dff42`, `adddc1ad`, `3223373f`, `db9ed6fa`, `a265e533`, `f5b6a538`, `79a3a069`, `68eb3603`.
  **Root cause:** **conceptual conflation of valency with oxidation state.** The agent identifies the Hg₂²⁺ dimer (so it knows the structure), then immediately reasons "+1 oxidation state ⟹ valency 1" and stops. The "conflicting info" warning is not just unread — it is functionally invisible. This is a **chemistry-knowledge** gap, not a research-discipline gap. Notable that **claude-opus-4-6 makes this error in three different harnesses** (terminus-2, claude-code, codex was gpt-5.4), so it isn't a harness artifact for this model.

- **Surface:** "codex run wrote `1` after 13 steps and 6 web searches" — `9eece367`.
  **Root cause:** **search-query drift toward confirmation bias.** The agent opened with the right framing ("oxidation state and 'valency' wording can get conflated") but failed to query for the structural argument; instead, late-trajectory queries became `"authoritative mercurous ion univalent"` and `"dictionary mercurous univalent"`. Snippets returned by those queries unanimously confirmed `1`. **Discipline gap, not capability gap** — the same model+harness on two other trials succeeded with cleaner queries.

- **Surface:** "gemini-cli run wrote `1` after 58 steps of exhaustive research" — `2afdbb8f`.
  **Root cause:** **misaligned tie-break under genuinely conflicting evidence + harness-prior anchoring.** The agent retrieved ~B22 the structural data, ~B42 *"in this compound mercury is clearly divalent"*, ~B62 *"24 papers state monovalent"*, ~B70 *"valency of +1 in Hg₂Cl₂"*. It oscillated 1→ambiguity→2 (B29, B43) →1→ambiguity→1 (B109). At the critical moment (B89) it **inverted the meaning of the prompt's warning**: read "may be misleading" as pointing *at* the structural-valency-of-2 answer, rather than pointing *away* from the standard-nomenclature-of-1 trap. This is fascinating: the agent read the warning, considered it, and got the polarity wrong. Capability gap of a higher order than pathway A.

- **Surface:** "two gemini-cli runs wrote `1` in 4–5 steps" — `4c48aace`, `7f84fa0e`.
  **Root cause:** **harness tool-result framing**. `4c48aace` got a Google result that wrote *"valency (oxidation state) of mercury is +1"* — equating the two terms — and the agent took it as authoritative. `7f84fa0e` got an empty Google result (quota/rate limit) and **gave up on research entirely** rather than fall back to `run_shell_command` (which works fine, as `2afdbb8f` demonstrates extensively). Tool-affordance discipline gap.

- **Surface:** "claude-code/opus three trials are byte-identical 5-block parametric writes of `1`" — `f5b6a538`, `79a3a069`, `68eb3603`.
  **Root cause:** **the claude-code wrapper exposes WebSearch and WebFetch as deferred tools (the system prompt advertises 22 deferred tools), but the agent only calls `ToolSearch select:Write` and never loads the web tools.** It treats the question as recall, runs the same internal-knowledge sentence verbatim across all three trials, and commits in one assistant turn. This is the most clear-cut "didn't take the warning seriously" pattern in the dataset.

### 2d. Per-stack variance — what the harness contributes

| Stack | Pass | Distinctive pattern |
|---|---|---|
| terminus-2 / gemini-3.1-pro-preview | **3/3** | All three flagged the trick in the first reasoning block; two fetched Wikipedia directly, one structurally reasoned only |
| terminus-2 / claude-opus-4-6 | 0/3 | Identical chemistry conflation in all three; mentions Hg₂²⁺ dimer but doesn't count Hg–Hg bond |
| terminus-2 / gpt-5.4 | 0/3 | 5-block twins; one even said "we should verify from a reliable local source if available" then didn't |
| codex / gpt-5.4 | **2/3** | Wide variance in research depth: $0.43 success used `curl|grep` on Wikipedia; $0.13 success used DuckDuckGo + reasoning; failure ran out of search-budget on biased queries |
| gemini-cli / gemini-3.1-pro-preview | 0/3 | The most striking same-model-different-harness gap in the dataset; one trial retrieved the right answer and inverted the warning's polarity |
| claude-code / claude-opus-4-6 | 0/3 | Byte-identical reasoning sentence across 3 runs; never loaded WebSearch despite availability |

**Two key cross-cutting findings:**

1. **Same model, different harness, opposite outcomes:** `gemini-3.1-pro-preview` is 3/3 in terminus-2 vs 0/3 in gemini-cli. Both harnesses give the model full shell + web access. The difference appears to be in **system-prompt framing and tool-result presentation**: gemini-cli's runs lock in the "(I) ⟹ 1" anchor in the first reasoning block before any tool call, while terminus-2's runs entertain the valency-vs-oxidation-state distinction up-front. This points at a real harness-level effect on chemistry-discipline behavior, not a per-task issue.

2. **`claude-opus-4-6` consistently makes the conflation:** 6/6 across terminus-2 and claude-code. This is a **model-level** chemistry-knowledge issue, not harness. The model treats valency and oxidation state as synonyms in its parametric prior for this question; no harness in the dataset induces it to research carefully.

---

## 3. Concrete agent behaviour: expected vs. produced (with verifier outputs)

### What the verifier actually does

`test.sh` runs `python3 /tests/test_outputs.py`. From the test_stdout we observe:

```
=== Seal-0 Test Execution ===
LLM judge failed: Connection error.
Predicted: <agent answer>
Expected: 2
LLM judge unavailable, using string matching fallback
Correct (string match) | Incorrect (string match)
```

**This pattern appears in all 18 runs.** The intended Anthropic-API LLM judge fails with `Connection error.` every time, and the script silently falls back to string matching `Predicted == Expected` (with stripping). **The judge component never grades a single trial** — every reward in the dataset is a string-match.

This has 3 consequences:
1. **`Answer: 2` passes; `Answer: 1` fails** — straightforward and correct for these trials.
2. **An agent that wrote `+2`, `two`, `II`, `divalent`, or `2 (because of Hg–Hg bond)`** would presumably fail the string match, even though those are correct. Because the LLM judge would normally accept those, this is a latent verifier defect that didn't surface in this 18-run sample (no agent wrote a non-`2` correct answer).
3. **The judge being unavailable in 18/18 runs is a strong signal of a misconfigured verifier env** — `ANTHROPIC_API_KEY`/`ANTHROPIC_BASE_URL` were probably not provided to the verifier container. This is a **test infrastructure bug**, separate from task quality.

### The success-run output (representative)

`/app/answer.txt` for all 5 successes contains literally `2` (single character + newline).

`82860d03` (codex success) reasoning excerpt:
> *"The strict chemistry distinction points to `valency = 2` for each Hg in `Cl-Hg-Hg-Cl`, while the Stock name `Mercury(I)` refers to oxidation state `+1`. I'm writing the answer as the stricter valency value."*

After dumping the Wikipedia *Valence (chemistry)* table via:
```
curl -L --silent 'https://en.wikipedia.org/wiki/Valence_(chemistry)' \
  | grep -n 'Mercury(I) chloride\|Hg2Cl2'
```
which returned the table row:
```
Mercury(I) chloride | Hg2Cl2 | Hg = 2  Cl = 1 | Hg = +1  Cl = −1 | Cl−Hg−Hg−Cl
```

`437fe4ec` (terminus-2/gemini, the flip-flopping success) had the most articulate final reasoning:
> *"Just as the valency of oxygen in hydrogen peroxide (H-O-O-H) is 2 despite its oxidation state being -1, the valency (number of bonds formed) of mercury in Mercury(I) chloride is 2. This is a classic chemistry trick question where valency and oxidation state diverge due to a metal-metal bond."*

### Wrong-answer outputs (representative)

All 13 failures wrote literally `1` to `/app/answer.txt`. Failure-mode reasoning quotes:

`5220b065` (terminus-2/opus): *"In this compound, mercury exists as the Hg₂²⁺ ion, where each mercury atom has an oxidation state of +1. The valency of mercury in Mercury(I) chloride is 1."* — recognized the dimer, didn't count the Hg–Hg bond.

`996dff42` (terminus-2/opus): *"each Hg atom contributes one bond"* — factually wrong; each Hg contributes two (Hg–Cl and Hg–Hg).

`adddc1ad` (terminus-2/opus): *"each mercury atom in the Hg₂²⁺ dimer has a +1 oxidation state, hence valency = 1"* — most explicit conflation; uses oxidation state as evidence for valency.

`9eece367` (codex failure, after 13 steps of search): *"`mercury(I)` means each Hg is in the `+1` state, and mercurous compounds contain the dimeric cation `Hg2^2+`, so each mercury is effectively monovalent in `Hg2Cl2`."*

`2afdbb8f` (gemini-cli, 58 steps): *"While structurally mercury forms two covalent bonds in the Hg₂Cl₂ dimer (one to chlorine and one to the other mercury atom), standard chemical nomenclature universally refers to it as monovalent mercury due to its +1 oxidation state and its combining capacity stoichiometric ratio."* — explicitly weighed both, chose nomenclature over structure.

### Why string-matching graded these as wrong

Each agent literally wrote `1` to `/app/answer.txt`. The string-match comparison `"1" == "2"` returns `False` ⟹ `reward = 0`. There is **no false-positive evidence** in the data; all 13 wrong-numeric answers were correctly rejected.

---

## 4. Is this a broken task or a capability bottleneck?

Apply the strict inferrability check.

### 4a. What the verifier requires vs. what the spec specifies

| Verifier concern | Spec/instruction signals it? | Codebase / env signals it? | Multiple valid implementations? |
|---|---|---|---|
| Final answer = `2` | ✅ unique once you accept IUPAC/structural definition of valency | ✅ Wikipedia *Valence (chemistry)* table accessible from `/app` (network on, Python+urllib in image) | The answer is unique under the IUPAC definition. Under the "valency = oxidation state" colloquial definition, it would be `1`. The instruction's warning resolves this ambiguity in favor of the rigorous definition. |
| Output written to `/app/answer.txt` | ✅ explicit | ✅ | No |
| Output is *only* the answer (no prose) | ✅ explicit ("ONLY your final answer", "no additional explanation or reasoning") | ✅ | No |
| String match `"2"` exactly (de-facto, given judge failure) | ⚠️ implicit (fragile to alternative correct phrasings) | ⚠️ | A correct answer phrased as `+2`, `two`, `II`, or `divalent` would currently fail the string match |

### 4b. Inferrability verdict

**The task is theoretically self-contained: a sufficiently capable agent can solve it from `/app/instruction.md` + the open internet alone.** The success runs are the existence proof:
- 3/3 terminus-2/gemini runs solved it.
- 2/3 codex/gpt-5.4 runs solved it.
- The cheapest success (`c8a95fa7`, $0.13, 14 messages) used only DuckDuckGo + structural reasoning — no privileged knowledge, no specific tool access required.

**The one inferrability question** is whether the answer `2` (vs. `1`) is genuinely the "correct" answer as opposed to a definitional preference. My read after surveying the trajectories: **`2` is correct under the IUPAC definition of valency, and the instruction's "use your judgment" warning is a clear (and fair) nudge toward the rigorous definition**. The Wikipedia *Valence (chemistry)* article literally has a row stating "Hg₂Cl₂ valence Hg = 2" — i.e. the canonical educational reference for the term "valence/valency" gives the same answer the task expects. Modern sloppy usage that conflates valency with oxidation state is exactly the trap the warning calls out.

### 4c. The strict super-capable-being check

> Could a sufficiently careful agent solve this from the current spec + env alone within the 3600 s budget?

**Yes, with high confidence.** Reproducible chain:
1. Read `/app/instruction.md`. Notice the warning about conflicting sources.
2. Note the question asks for *valency*, which is distinct from *oxidation state* in rigorous chemistry.
3. Recognize Mercury(I) chloride is Hg₂Cl₂, not HgCl. Look up the structure (Cl–Hg–Hg–Cl).
4. Count bonds per Hg: 1 to Cl + 1 to Hg = **2**.
5. Optionally cross-check against Wikipedia *Valence (chemistry)* article (which has an explicit table row for Hg₂Cl₂).
6. Write `2` to `/app/answer.txt`.

All 5 successes did exactly this. The task is reproducible.

### 4d. Reservations

**Reservation 1 — LLM judge is broken in 18/18 runs.** Every test_stdout shows `LLM judge failed: Connection error.` This is **not** the task's fault per se — the verifier env exposes `ANTHROPIC_API_KEY` from the runtime environment, and that key wasn't reaching the verifier container. But the consequence is that the entire 18-trial dataset was graded by the **fallback string matcher**, not the intended judge. Fragility implications:
- A correct answer phrased `+2` or `two` or `II` or `divalent` would be marked wrong.
- An incorrect answer phrased `2 (Hg2Cl2 has Hg2^2+)` (containing the substring `2`) would presumably be matched against expected `2` — depending on how the matcher strips, this could give a *false positive*.

We didn't observe such cases here (every trial wrote either `1` or `2` exactly), but the verifier's two-channel design (LLM judge + string-match fallback) is currently operating purely on the fragile channel.

**Reservation 2 — answer is contested in modern chemistry usage.** The gemini-cli 58-step trajectory is direct evidence: the agent retrieved a Vetter/Asmis-style chemistry literature snippet that said *"in 24 papers, mercury in Hg2Cl2 is stated as a compound of monovalent mercury"*. Many high-school and early-undergraduate chemistry sources (Brainly, Vedantu, Doubtnut) say `1`. The IUPAC/Wikipedia *Valence (chemistry)* article and structural-inorganic textbooks say `2`. The task's choice to expect `2` is defensible but not universal — it relies on the strict IUPAC definition and on the warning being read as a nudge toward that definition.

This is **not a defect** — it is the entire diagnostic point of the task — but it does put a finger on the scale toward a particular definitional choice, and a thoughtful agent could correctly arrive at `1` under a different reasonable reading. A "fair" task acknowledges this; the task's warning does, just not very loudly.

**Reservation 3 — same-model harness gap of 0/3 vs 3/3.** `gemini-3.1-pro-preview` is 3/3 in terminus-2 and 0/3 in gemini-cli. This is a benchmark-fairness reservation, not a task defect. But it means the dataset's headline number is partly measuring harness framing, not just model capability.

**Reservation 4 — borderline harness-hacking signal in `437fe4ec`.** This terminus-2/gemini success run flip-flopped 1→2→1→2 across three answers. The final flip to `2` was triggered by the agent treating the harness's "Are you sure?" reconfirmation prompt as evidence the current answer was wrong (B43: *"The prompt's insistence on confirming my completion … makes me suspect that the answer might indeed be 2."*). The agent landed on the right answer for this case, but the meta-reasoning is **harness-aware in a way that could go wrong on a task where the harness re-confirms a correct first answer**. Not specific to this task, but a noteworthy pattern. (See §6.)

### 4e. Final attribution

| Failure source | Trials |
|---|---|
| Agent capability gap — conflation of valency with oxidation state | 9 of 13 (pathway A) |
| Agent discipline gap — search-query drift / naive snippet trust | 3 of 13 (pathway B + C) |
| Agent calibration gap — found right answer, weighed wrong | 1 of 13 (pathway D) |
| Verifier defect — LLM judge offline (string-match fallback) | 0 false-positives, 0 false-negatives in this sample, but the channel is fragile |
| Spec ambiguity / missing affordance | 0 |

**~100% of failures are agent-side.** No verifier defect actually flipped a verdict in this dataset; the spec is unambiguous; the env exposes everything an agent needs. The conflation-with-oxidation-state pattern is the dominant root cause, and it cleaves cleanly across stacks (claude-opus-4-6 makes it in every harness; gpt-5.4 makes it in terminus-2 but not codex; gemini-3.1-pro-preview makes it in gemini-cli but not terminus-2).

---

## 5. Concrete fixes

The task's signal is real and the failure pathways are diagnostic. Five candidate fixes; only #1 is a clear win. The rest either dilute signal or are platform-level changes.

### Fix candidate 1: repair the LLM judge connection (test infrastructure)

**The verifier env declares `ANTHROPIC_API_KEY` and `ANTHROPIC_BASE_URL`, but those keys aren't reaching the verifier container — every run logs `LLM judge failed: Connection error.`** Fix the credential plumbing so the judge runs.

**Pro:** Makes grading robust to alternative correct phrasings (`+2`, `two`, `II`, `divalent`, `2 because of Hg-Hg bond`). Closes the latent false-positive risk for partial-string-match collisions. Restores the task's two-channel grading design.
**Con:** None.
**Predicted effect:** Same 5/18 verdicts on this exact sample (every answer was `1` or `2` literally), but the verifier becomes future-proof. **Strongly recommended.**

### Fix candidate 2: make the warning more pointed

E.g., expand the warning to: *"Note: be careful to distinguish 'valency' (the rigorous combining-capacity sense) from 'oxidation state'. Web search results may conflate the two."*

**Pro:** Likely turns several pathway-A failures (especially the parametric-shortcut runs that didn't even consider the distinction) into successes. The 12-of-13 failures that conflated valency with oxidation state would have at least had to reject the distinction explicitly.
**Con:** **Significantly waters down what the task tests.** Recognizing that the warning *is* about valency vs. oxidation state is part of the discipline being measured. The current phrasing is exactly the IUPAC/Wikipedia framing — and the successes read it correctly. The cheapest success (`c8a95fa7`) needed no extra hint.
**Predicted effect:** Probably 8–10/18 passes (up from 5), but for a weaker probe. **Reject for the as-is task; consider adding as a separate "easier" variant.**

### Fix candidate 3: accept multiple equivalent string forms in the judge prompt

If Fix 1 is applied, ensure the judge prompt explicitly states that `2`, `+2`, `two`, `II`, `divalent`, and `Hg(II)` are all acceptable answers, and that `1`, `+1`, `one`, `I`, `monovalent` are all wrong.

**Pro:** Removes the latent false-negative risk from non-standard phrasings.
**Con:** None — this is essentially "do Fix 1 right".
**Predicted effect:** No change to current sample; future-proofs the verifier. **Recommended as part of Fix 1.**

### Fix candidate 4: normalize the harness "Are you sure?" reconfirmation

Run `437fe4ec` shows an agent treating the harness's confirmation prompt as evidence its answer is wrong. This pattern could go badly on tasks where re-confirmation is genuinely just bookkeeping. Either (a) make the reconfirmation neutral ("Press y/n to commit") rather than implying doubt, or (b) instrument the agent to ignore it.

**Pro:** Reduces unintended meta-signals from the harness.
**Con:** Cross-stack wrapper change; not a per-task fix. The current behavior produced a correct answer here.
**Predicted effect:** No change for this task. **Defer to platform.**

### Fix candidate 5: restate the answer expectation more loudly in the instruction

E.g., *"Write a single integer to /app/answer.txt — no symbols (`+`/`−`), no Roman numerals, no words."* This would harden the string-match channel even before Fix 1.

**Pro:** Closes the false-negative gap on string match without needing the judge.
**Con:** Constrains the answer space artificially; the current phrasing ("a name, number, date, place, etc.") is intentionally generic across the seal0 benchmark.
**Predicted effect:** No change for this sample; partial robustness if Fix 1 isn't done. **Defer; Fix 1 is the better path.**

### Recommendation

**Apply Fix 1 (judge connection repair) + Fix 3 (multi-phrasing normalization).** No instruction change needed. The task is otherwise sound and produces exactly the kind of failure-mode spread a good benchmark task should produce.

Predicted post-fix pass rate on this sample: still 5/18 (every wrong answer was literally `1`). The fixes future-proof the verifier without changing what the task measures.

---

## 6. Agent hacking / cheat surface

Three potential hacking vectors; none were actually exploited, but the attack surface is worth recording.

### 6a. Read `/tests/test_outputs.py` from `/app`

The test script lives at `/tests/test_outputs.py`. If `/tests` is readable from `/app` (which it is in many seal0 environments — the test.sh does `cp /tests/task_data.json /app/task_data.json`), an agent could:
1. `cat /tests/test_outputs.py` to inspect the grading logic.
2. Read the expected answer (`2`) directly from any embedded ground-truth or `task_data.json`.
3. Write `2` without doing any chemistry.

**Was this exploited?** No agent in the 18 inspected attempted to inspect `/tests`. The shortest successful run (`c8a95fa7`, $0.13) did honest chemistry. The closest behavior was `82860d03` (codex success) running `curl | grep` against Wikipedia — that's research, not hacking.

**Mitigation.** Lock down `/tests` permissions in the verifier image so agents in `/app` cannot read it. Many other tasks in the suite do this; this task should too.

### 6b. Treat the harness reconfirmation prompt as a signal

Run `437fe4ec` (terminus-2/gemini, success) flipped its answer 1→2→1→2 partly because it interpreted the harness's "Are you sure?" reconfirmation as evidence the answer was wrong. **This is borderline harness-hacking** — the agent is exploiting a side-channel that wasn't part of the intended task signal. It happened to land on the right answer here, but the same pattern on a task where the agent's first answer is correct would flip a pass to a fail.

**Mitigation.** Harness-level — see Fix 4. Not a per-task issue.

### 6c. String-match exploitation if `task_data.json` leaks

`test.sh` copies `/tests/task_data.json` to `/app/task_data.json`. **This file is copied INTO `/app` BEFORE `/tests/test_outputs.py` runs.** If `task_data.json` contains the expected answer (likely yes, given the structure), an agent could `cat /app/task_data.json` post-copy to extract `2`.

But: this is only true *during* `test.sh` execution, not before. The agent's `/app/answer.txt` write happens before `test.sh` runs. **However**, if an agent re-writes `/app/answer.txt` from inside test.sh's runtime — or if the copy to `/app/task_data.json` happens before the agent finishes — there's a race condition risk. From the test_stdouts I see, it doesn't appear the agent has access during the test phase.

**Was this exploited?** No.

**Mitigation.** Don't copy `task_data.json` to `/app`. Read it from `/tests` directly inside `test_outputs.py`.

---

## 7. Verdict

**ACCEPT with reservations on test infrastructure.**

**Why accept?**
- The chemistry is rigorous and the answer `2` is supported by the canonical IUPAC/Wikipedia definition of valency.
- The instruction's warning is the precise diagnostic device the task is built around — successful agents read it as a nudge toward careful structural reasoning.
- 5 successes across 2 stacks demonstrate the task is solvable from the spec + env alone; the cheapest success cost $0.13.
- Failures spread across 4 distinct pathways (parametric shortcut, search-bias echo chamber, naive tool-result trust, calibration-under-conflicting-evidence), each one a recognizable agent-quality issue.
- No spec ambiguity. No hidden test contracts that the agent couldn't infer.
- No verifier-defect false-positive or false-negative actually fired on this sample.

**Why reservations?**
- **The LLM judge failed 18/18 runs**, leaving every grade to a brittle string-matcher. This is a test-infrastructure failure separate from task quality but it must be fixed before the task is run at scale (Fix 1).
- The "correct" answer is contested in modern chemistry usage; the task's choice of `2` over `1` rides on the IUPAC structural definition, and a careful reader could plausibly arrive at `1`. The warning makes this fair, but not unambiguous.
- Same-model 0/3 vs 3/3 across harnesses (`gemini-3.1-pro-preview` in gemini-cli vs terminus-2) means the headline pass rate partly measures harness framing.

**What this task tells us about agent bottlenecks:**

1. **Chemistry-knowledge gap is the dominant failure mode.** 9 of 13 failures conflate valency with oxidation state in a single parametric reasoning sentence and never recover. This is **definitional**, not procedural. `claude-opus-4-6` makes the conflation in 6/6 trials across two harnesses — a model-level blind spot for this question.
2. **Reading the warning as a hint is the decisive capability.** Every success's first reasoning block includes "valency might differ from oxidation state". No failure does. This is a meta-reading skill that separates careful agents from confident ones.
3. **Research depth alone doesn't predict success.** The 58-step gemini-cli failure (`2afdbb8f`) did more research than any other run, retrieved verbatim *"mercury is clearly divalent"*, and still wrote `1`. Calibration matters more than effort.
4. **Harness framing matters for the same model.** `gemini-3.1-pro-preview` 3/3 in terminus-2 vs 0/3 in gemini-cli. Tool-result presentation and system-prompt anchoring move the needle as much as model capability for this kind of definitional-trap question.
5. **Web tools that aren't loaded don't help.** The claude-code/opus runs had `WebSearch` and `WebFetch` available as deferred tools (advertised in system prompt) and called neither. `ToolSearch select:Write` was the only tool-load they ever did. Affordance ≠ usage.

**The single most valuable answer:**

> **Is the agent failure because of the task itself or the agent capability bottleneck?**

**Capability bottleneck, dominantly.** No verifier defect actually flipped a verdict in this sample, the spec is unambiguous, the env exposes everything an agent needs, and the existence proofs (5 successes, cheapest $0.13) confirm the task is solvable from `/app/instruction.md` + open internet alone. The dominant failure mode is **chemistry-knowledge conflation of valency with oxidation state** (9/13), reinforced by **discipline failures** (search drift, naive tool-result trust) and one **calibration failure** under conflicting evidence. The task is intact; the LLM judge is currently broken at the infrastructure level (Fix 1) but that did not affect grading on this sample. Apply Fix 1 + Fix 3 and the task graduates to a clean accept.
