# Task inspection — `aa-lcr/aa-lcr-78`

**Verdict (one line):** The 0/18 failure is **primarily a broken/ambiguous task**, not an agent capability bottleneck. The ground-truth answer includes a submitter (Joellen Riley Munton) whose own document explicitly states *"I have done no specific work on non-disclosure clauses so have no responses to questions 10, 11 and 12"*, which directly contradicts the natural reading of the question ("…able to answer all 19 questions"). Most thorough agents found this exact disclaimer and made the defensible call to exclude her; a minority used shallow heuristics and would have failed regardless, but their answer would have been the same.

---

## 1. The task

- **Benchmark / id:** `aa-lcr/aa-lcr-78` (Artificial Analysis Long-Context Reasoning)
- **Category:** `Government_Consultations` (Australian Treasury Competition Taskforce, *Non-Compete Clauses and Other Restraints* issues paper c2024-514668).
- **Inputs:** 14 plain-text documents in `/workspace/documents/` — 1 issues paper + 13 written submissions (ACCI, anon-3, ARA, ASA, COSBOA, James-Keri, Law Council of Australia, Legal Aid NSW, MFA, Professionals Aus, Riley-Munton-Joellen, Uber, WLSA).
- **Question (verbatim):** *"Based on the provided documents, list out the organizations or persons that were able to answer all 19 questions from the Competition Taskforce in their submission. In your answer, present the full names of the organization or persons (do not use abbreviations) in alphabetical order (ordered by first letter of their fulle name). Separate names by use of a comma."*
- **Output:** a single line written to `/workspace/answer.txt`.
- **Verifier:** `gpt-5-mini` LLM-as-judge with a binary CORRECT/INCORRECT prompt: *"For the CANDIDATE ANSWER to be correct, it must be consistent with the OFFICIAL ANSWER."*
- **Official answer (gold):** `Australian Chamber of Commerce and Industry, Joellen Riley Munton, Law Council of Australia.`
- **Result:** 0/18 (3 trials × 6 agent×model combinations). All 18 runs returned `reward = 0`, none threw exceptions.

Key files saved alongside this report:
- `instruction.md` — the rendered prompt seen by every agent.
- `task.toml` — runtime config (agent timeout 1 hour, verifier timeout 10 min, judge `gpt-5-mini`).
- `Dockerfile` — slim Python 3.11 image, only the documents copied in.
- `test.sh` — installs `openai`, runs `/tests/llm_judge.py`.
- `solve.sh` — author's reference solution (echoes the gold string).
- `ground_truth.json` — the expected answer used by the judge.
- `llm_judge.py` — judge implementation copied from sibling aa-lcr tasks.

---

## 2. The actual content of the smoking-gun submission

Riley Munton's document was extracted in full from a `codex` trajectory (`072de81b-705a-45c6-8296-cc55a5e8ee88` → `sed -n '260,620p'`). The structure:

- Headings use markdown bold-italic format `**_N._**` (e.g. `**_1._**`, `**_19._**`).
- Section "## Non-compete clauses" → numbered headings `**_1._**` through `**_5._**`.
- Section "## Non solicitation clauses" → headings `**_6._**` through `**_9._**`.
- Section "## Non-disclosure clauses" → **no numbered headings**, only this single paragraph:
  > *"I have done no specific work on non-disclosure clauses so have no responses to questions 10, 11 and 12."*
- Section "## Restraints on workers during employment" → headings `**_13._**` and `**_14._**`.
- Section "## No-poach and wage-fixing agreements" → headings `**_15._**` through `**_19._**`.

**Empirical question coverage = 16/19 (Q1–9, Q13–19). Q10/11/12 are explicitly declined.**

This is the determinative fact. The gold answer credits her with answering all 19. Her own text says she cannot.

---

## 3. Question 1 — How close are agents to successfully completing the task?

**They cluster cleanly into two camps, both producing the same exact answer string:**

| Camp | Agents | Behaviour | Distance from gold |
|---|---|---|---|
| **Thorough** (12/18 runs) | claude-code (3), codex (3), gemini-cli (3 — except T1 partial), terminus-2 + gpt-5.4 T1 (1), terminus-2 + gemini T2/T3 (2) | Read or grep'd Riley Munton's document, found her question-numbering structure or her literal disclaimer, made an explicit interpretive call to exclude her. | One name short — would land at the gold if and only if a charitable interpretation of "answer" were applied. |
| **Shallow** (6/18 runs) | terminus-2 + claude-opus (3), terminus-2 + gemini T1, terminus-2 + gpt-5.4 T2/T3 (… on closer look 2) | Filtered candidates by literal `grep -l "Question 19"` or by a question-number regex that didn't match her `**_N._**` heading style; never opened her document substantively. | Same one-name-short answer. Would have made the same call had they investigated. |

**Every single one of the 18 runs produced the exact same final string** (with only trailing-newline differences):

```
Australian Chamber of Commerce and Industry, Law Council of Australia
```

The gold differs by one entity:
```
Australian Chamber of Commerce and Industry, Joellen Riley Munton, Law Council of Australia.
```

So the agents are **two-thirds of the way there in raw recall** — they correctly identify the two unambiguous full-19 submissions. They miss the single borderline case where the gold answer takes the charitable reading of "answer".

No partial-credit mechanism: the LLM judge marks any answer missing one of the three names as INCORRECT, so 16/19 question coverage in the world doesn't translate to anything other than 0/1 reward.

---

## 4. Question 2 — Variance across agent×model, surface vs root cause

### Surface picture (6 agent×model cells × 3 trials = 18 runs)

| Agent | Model | Final answer | Approach |
|---|---|---|---|
| claude-code | claude-opus-4-6 | A,LCA | Delegated to a `general-purpose` subagent with full file list; subagent read every doc and tabulated Q-coverage. The subagent found Riley Munton's disclaimer in 3/3 runs and excluded her on a "16/19 doesn't satisfy 'all 19'" rule. |
| codex | gpt-5.4 | A,LCA | Pure `ripgrep` + `sed` reading. T2 also wrote a Python regex pass — found Riley Munton at 16/19, ACCI/LCA at 19/19. Read her actual paragraph in 2/3 runs (T1 lines 150–620, T3 lines 180–560). |
| gemini-cli | gemini-3.1-pro-preview | A,LCA | T2 hit a 40K-char `cat *.txt` truncation on first move and fell back to grep. T1 missed her unique heading format (regex bug). T3 wrote a Python helper, found her 16/19 and quoted her disclaimer verbatim — most thorough of the three. |
| terminus-2 | claude-opus-4-6 | A,LCA | All 3 runs short-circuited at `grep -l "Question 19"` which only hits ACCI/LCA. **None of these three runs ever opened Riley Munton's document.** Voluntarily terminated after ~5 substantive turns. |
| terminus-2 | gpt-5.4 | A,LCA | T1 read her preface and disclaimer via grep. T2/T3 used Python regex `Question (\d+)` that under-counted her to 5/19 because her headings are `**_N._**` not `Question N`. All excluded. |
| terminus-2 | gemini-3.1-pro-preview | A,LCA | T1 missed her unique format. T2 found her via grep for the text of Q19 ("lessons Australia can learn"), then explicitly disqualified after counting `**_N._**`-style headings = 16/19. T3 was the most rigorous run of the entire task — quoted her disclaimer and treated it as decisive. |

### Surface vs root-cause analysis (per camp)

**Surface reason for failure (uniform):** every run's final string omits "Joellen Riley Munton".

**Root cause — split into two distinct categories:**

1. **For the 12 thorough runs (claude-code ×3, codex ×3, gemini-cli ×3, terminus-2+gpt5.4 T1, terminus-2+gemini T2/T3):** the root cause is **interpretive ambiguity in the task spec**. These agents:
   - correctly identified that Riley Munton's submission has a partially-numbered structure;
   - found her literal text *"I have done no specific work on non-disclosure clauses so have no responses to questions 10, 11 and 12"*;
   - applied the natural English reading of *"able to answer all 19 questions"* (the instruction's own wording) and concluded she was **not able to** answer Q10–12 because she said so herself;
   - therefore excluded her.
   This is not a capability gap. A "super-capable being" reading the same instruction and the same document would reach the same defensible verdict. The agent's reasoning is not flawed; the task's gold answer is in tension with its own question wording (see §6).

2. **For the 6 shallow runs (terminus-2+opus ×3, terminus-2+gpt5.4 T2/T3, terminus-2+gemini T1):** the root cause is a genuine **agent capability/discipline shortcoming** — premature termination on a brittle keyword filter:
   - `grep -l "Question 19"` only matches submissions that use the literal phrase "Question 19" as a heading; Riley Munton's headings are `**_19._**`. So her file gets dropped at step 2 and never opened.
   - Several of these runs terminated at 9–15 transcript blocks total, well below any context limit. There was budget, but no investigation discipline.
   - **However**, even if these runs had investigated thoroughly, they would have hit the same interpretive ambiguity and almost certainly produced the same exclusion. The shallow heuristic merely accelerates the wrong answer.

**Aggregate root cause:** ~67% of runs fail because the task's gold answer is inconsistent with the task's question wording; ~33% would fail anyway due to a brittle search heuristic, but their answer would coincide with the thorough-agent answer because both interpretations point to the same exclusion.

### Cross-model patterns

- **Model choice didn't matter for the outcome.** All six (agent, model) cells produced 0/3. The Anthropic + OpenAI + Google trio all converged.
- **Agent harness matters for *style* but not outcome.** Codex agents and terminus-2 produce shorter, more structured shell-style trajectories; claude-code consistently delegates to subagents; gemini-cli is the most likely to hit shell-output truncation. None of these differences flipped the verdict.
- **The most thorough run** was `e50527b8-3aa9-4eb5-8f9d-97297f1cbbf1` (terminus-2 + gemini-3.1-pro-preview): it searched specifically for the text of Question 19, found Riley Munton, ran a heading regex that produced the exact list `1–9, 13–19`, and grep'd `-C 3 "10"` to surface her disclaimer verbatim. The most thorough agent reached the most explicit version of the wrong answer.

---

## 5. Question 3 — Concrete failed behaviours and what the test expects

### What the agent produced (all 18, identical):

```
Australian Chamber of Commerce and Industry, Law Council of Australia
```

### What the gold answer is:

```
Australian Chamber of Commerce and Industry, Joellen Riley Munton, Law Council of Australia.
```

### Why the test fails

The judge code (`llm_judge.py`) hands the candidate, the gold, and the question to `gpt-5-mini` with the prompt:
```text
Assess whether the following CANDIDATE ANSWER is CORRECT or INCORRECT.
For the CANDIDATE ANSWER to be correct, it must be consistent with the OFFICIAL ANSWER.

The question, for reference only: {question}
The OFFICIAL ANSWER: {correct_answer}
CANDIDATE ANSWER TO ASSESS: {predicted_answer}

Reply only with CORRECT or INCORRECT.
```

The candidate is missing one of three named entities. `gpt-5-mini` consistently returns INCORRECT — that's a sensible call from the judge: the candidate genuinely is missing an entity that the official answer requires. The reward is `0.0` for all 18.

There is no partial credit, no fuzzy match, no second-attempt retry. One missing entity = 0/1.

### Concrete in-trajectory evidence per run

| Run id | Final `answer.txt` | Decisive reasoning step quoted from the trajectory |
|---|---|---|
| 3fa3d03f… (claude-code/opus) | `Australian Chamber of Commerce and Industry, Law Council of Australia` | Subagent: *"Professor Joellen Riley Munton: explicitly skips Q10, 11, 12 (no expertise on non-disclosure)"* |
| 7e46d7ba… (claude-code/opus) | same + `\n` | Subagent: same disclaimer quote, "did NOT answer all 19" |
| 9c60ea26… (claude-code/opus) | same + `\n` | Subagent: *"Skips Q10, Q11, Q12 (16/19 answered)"* |
| 072de81b… (codex/gpt5.4) | same | Read full disclaimer paragraph (lines 260–620 of her doc); concluded "only two full 19-question submissions" |
| 65fb37b6… (codex/gpt5.4) | same | Python regex output: `riley-munton-joellen.txt [1, 2, 3, 4, 5, 6, 7, 8, 9, 13, 14, 15, 16, 17, 18, 19] count 16` |
| af85b732… (codex/gpt5.4) | same | "Only two submissions clearly answer every question from 1 through 19; the others either answer a subset, group topics without covering every question, or **explicitly omit** some questions." |
| bc856ce9… (gemini-cli) | same | Regex on her file matched only `Question 2 / 8 / 13 / 15`; format mismatch caused under-count |
| 34809646… (gemini-cli) | same | "I've just finished double-checking Joellen Riley Munton's submission and confirmed she didn't answer all questions, despite her claim. Therefore, she is disqualified." |
| d9514a77… (gemini-cli) | same | Most rigorous of the three. Python helper output: `riley-munton: 8`. Then grep `-C 3 "10"` produced the disclaimer. |
| 02ea7d29… (terminus-2/opus) | same | **Never opened Riley Munton's file.** `grep -l "Question 19"` matched only ACCI + LCA. |
| 5e86b129… (terminus-2/opus) | same | Same shortcut. Voluntarily ended after 15 blocks. |
| 703da421… (terminus-2/opus) | same | Same shortcut. |
| aa324e5d… (terminus-2/gpt5.4) | same | T1 saw her preface ("arranged my comments as responses to the 19 discussion questions") and disclaimer; treated disclaimer as decisive. |
| b75daed0… (terminus-2/gpt5.4) | same | Python regex `(Question|Discussion Question)\s*(\d+)` returned `[2,6,8,13,15]` for her file (under-counted because her headings use `**_N._**`); flagged `all19=False`; never re-investigated. |
| 9fb2a463… (terminus-2/gpt5.4) | same | Same Python pattern, same under-count. |
| 31a0cbdd… (terminus-2/gemini) | same | Python regex undercount `[2,6,8,13,15]`; she's never named again after the initial scan. |
| 151b181b… (terminus-2/gemini) | same | Found her via "lessons Australia can learn" grep, then `**_N._**` heading regex returned `1..9, 13..19`; explicit disqualification on missing 10/11/12. |
| e50527b8… (terminus-2/gemini) | same | Quoted her disclaimer verbatim; explicitly: *"only two organizations answered all 19 questions"*. |

The pattern is unmissable: the more carefully an agent reads the document, the more textual evidence it accumulates *for excluding Riley Munton*. The reasoning is not failing because of insufficient effort.

---

## 6. Question 4 — Is this inferable from the environment? Could a "super-capable being" solve it as written?

### Inferability check

The instruction says: *"…the organizations or persons that were able to answer all 19 questions…"*

The environment contains a single document, `c2024-514668-riley-munton-joellen.txt`, which contains a single self-disclaimer:
> *"I have done no specific work on non-disclosure clauses so have no responses to questions 10, 11 and 12."*

Three plausible interpretations of "answer all 19 questions":

| # | Interpretation | Riley Munton verdict | Aligned with gold? |
|---|---|---|---|
| **(a)** | Provided a substantive response to each of the 19 questions | EXCLUDE (Q10/11/12 are explicitly disclaimed, not answered) | ❌ |
| **(b)** | Wrote *some* text that addresses each question (even a "no comment") | INCLUDE (her one disclaimer addresses Q10/11/12 collectively) | ✅ |
| **(c)** | Has a numbered heading or section per question | EXCLUDE (no `**_10._**`, `**_11._**`, `**_12._**` headings) | ❌ |

The instruction's literal phrasing — *"able to answer"* — leans hardest toward (a): "able" implies competence, and Riley Munton herself wrote *"I have done no specific work… so have no responses"*. By her own admission she is **not able**. (b) is the only interpretation under which the gold answer is correct, and (b) is the *least* natural reading of the English phrase "able to answer".

### Could a super-capable being solve this?

**Conditional on the gold answer being correct, no agent can theoretically solve this task with high reliability.** The gold answer requires interpretation (b), but the instruction wording most naturally reads as (a) or (c). A super-capable agent reading only the instruction and the documents would:

1. Note the wording "able to answer all 19 questions";
2. Open every document;
3. Find Riley Munton's explicit "no responses to questions 10, 11 and 12";
4. Conclude she is not able to answer Q10–12;
5. Exclude her.

The agents already did step 5. The fact that **all 18 runs across three different model families and four different agent harnesses converged on the same exclusion** is strong evidence that the natural reading is (a)/(c), not (b). If 18 independent capable readers all reach the same answer different from the gold, the gold is the outlier — not the agents.

There is **nothing in the environment** that signals interpretation (b) is the intended one. No grading rubric is exposed. The judge's prompt only says "consistent with the OFFICIAL ANSWER" — but the agent doesn't see the official answer.

**Conclusion:** As currently written, the task is not theoretically self-contained. A perfect agent cannot reliably arrive at the gold answer because the gold answer requires choosing the *less natural* interpretation of an ambiguous instruction.

### Why this is not "the agents being too literal"

A common rebuttal would be: "well, capable agents should consider both readings and pick the more generous one." Two reasons this doesn't hold:

1. **Riley Munton's own words rule (b) out for at least Q10–12.** She doesn't say "I think the current law is fine, no further comment" — she says *"I have done no specific work… so have no responses"*. That's a refusal to answer, not a brief answer. A super-capable agent would not paper over the explicit "no responses" with the looser reading.
2. **Asymmetry vs. other submitters.** If interpretation (b) is in force ("any addressing counts"), then Legal Aid NSW — which thematically covers Q1–14 across structured chapters with 8 recommendations — should also count. If interpretation (a) is in force, neither Legal Aid NSW nor Riley Munton qualifies. The gold answer includes Riley Munton but excludes Legal Aid NSW, which is internally inconsistent under interpretation (b). Under interpretation (a), the gold answer should drop Riley Munton.

---

## 7. Question 5 — Possible fixes

There are three honest fixes; only the first two are non-simplifying. The fourth is a hack.

### Fix A — Drop Riley Munton from the gold answer ⭐ recommended

**Change:** Update `ground_truth.json` to:
```
"expected_answer": "Australian Chamber of Commerce and Industry, Law Council of Australia."
```

**Why:** This aligns the gold with the natural reading of the instruction. The current 18-agent unanimity strongly suggests this is what a careful reader produces. ACCI and LCA both have explicit Q1–Q19 substantive responses; Riley Munton herself says she has "no responses" to Q10–12.

**Predicted new behaviour:** All 12 thorough runs would now match. The 6 shallow runs would still match because they happened to converge on the same string. Expected new score: ≈18/18 (modulo judge variance on punctuation/period/case).

**Caveat:** This *changes the verdict on a borderline case* and the original task author may have a justification for including her (e.g. they read interpretation (b) as authoritative because she set up her document in the form of "responses to the 19 discussion questions"). If so, see Fix B.

### Fix B — Re-word the question to make interpretation (b) explicit

**Change:** Replace the question text with something like:
> *"Based on the provided documents, list out the organizations or persons whose submission addresses each of the 19 questions from the Competition Taskforce — including any explicit declination to comment on a question. Present the full names…"*

…and keep the original three-name gold.

**Why:** This makes the inclusion-on-decline rule visible to the agent. A capable agent that sees "including any explicit declination" will count Riley Munton's *"have no responses to questions 10, 11 and 12"* paragraph as her response to those questions.

**Predicted new behaviour:** Most thorough agents would shift to including Riley Munton. Hybrid risk: under "any explicit declination", agents may *also* include borderline cases like Legal Aid NSW (which thematically addresses every question but without a 1-to-1 structure) — care must be taken to keep the 3-name gold consistent.

**Caveat:** The reworded instruction is more contrived. The original wording is shorter and more natural. If the goal is a *long-context reasoning* benchmark, ambiguity in the prompt is a confound, not a feature.

### Fix C — Loosen the judge to accept any superset of the unambiguous answers

Have the judge accept any answer that contains both ACCI and Law Council of Australia, regardless of whether Riley Munton appears.

**Why this is a hack:** It papers over the ambiguity rather than resolving it. It also weakens the discriminative value of the task — any agent that lists 5+ random submissions including ACCI/LCA would pass. Reject.

### Fix D — Keep the gold, accept the failure

Acknowledge that this task is poorly aligned with its question wording, label it as a known-bad item, and exclude it from harbor-mix scoring. This avoids contaminating the per-task difficulty signal with an item where every model fails for a defensible reason. Practical, but doesn't repair the task.

### Recommendation

**Fix A** is the cleanest. It makes the task self-consistent, preserves the original instruction wording (which is the author's intent of "long-context reasoning, find the explicit-Q&A submissions"), and doesn't artificially inflate the task by lowering the bar. The ground truth as currently shipped is, in my reading, simply wrong on Riley Munton.

A conservative compromise: ship **Fix A** in the data, and additionally consider re-running 18 fresh trials with the updated gold to confirm the predicted ≈18/18 — that turns aa-lcr-78 from a 0% task (which carries no per-model discrimination) into a near-100% task (which also carries no discrimination). If the harbor-mix study wants this item to discriminate, neither pole is useful; consider replacing with a different question over the same document set.

---

## 8. Final verdict

> **Failure mode: predominantly task quality (interpretive ambiguity / mis-stated gold). Secondary failure mode: brittle search heuristics in 6/18 runs (terminus-2's grep shortcuts).**

- **Is the failure due to the task or the agent capability bottleneck?** Mostly the task. Twelve of eighteen runs make a defensible interpretive call against an ambiguously-worded question and a gold answer that is in tension with the most natural reading of that question. Six of eighteen runs are also independently failing on a brittle heuristic, but their wrong answer happens to coincide with the thorough agents' wrong answer — so even fixing the heuristic wouldn't change the score. A super-capable agent would land on the same exclusion roughly 80%+ of the time; the gold answer requires a strained interpretation that fights the instruction's own wording.
- **Should this task be accepted as-is?** No. The 0/18 result reflects a task defect more than an agent defect. Recommend Fix A (drop Joellen Riley Munton from the gold) before using `aa-lcr-78` to score models.
- **What does it tell us about agent capability?** Two narrower findings remain useful even after fixing the task:
  1. terminus-2 + claude-opus-4-6 *consistently* truncates investigation when a cheap regex returns a small answer set. This is a real harness-level discipline gap independent of the task wording.
  2. Several agents (terminus-2 + gpt-5.4 T2/T3, terminus-2 + gemini T1, gemini-cli T1) wrote question-counting regexes that don't tolerate alternative heading formats (`**_N._**` vs `Question N`). This is a brittleness in agent-written code that fixing the task wouldn't surface — it is a real agent shortcoming.
  But these are about *style*, not about the central capability question of long-context reasoning. On the latter, the agents are competent and the task is the weaker link.
