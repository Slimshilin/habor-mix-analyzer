# Task inspection — `element-hq/element-web` "rename device sessions" (PR #9282)

> **TL;DR.** This is a SWE-bench Pro feature-implementation task drawn verbatim from a real merged PR. **All 18 trials failed (0/18) and the failures are not "agents got the business logic wrong"** — the median run gets ≥35/51 required tests passing, and the missing 16 tests cluster on the **exact same set of contracts** for every trial. Those 16 tests are *not derivable* from the PR description: they assert (a) **specific `data-testid` strings** the instruction never names, (b) **frozen Jest snapshots** that pin React component HTML/CSS-class structure that the instruction never pins, and (c) an **exact log-message string** the instruction never names. The instruction also contains a **direct contradiction** with the gold tests on the only error-text the spec *did* try to pin down (instruction says `"Failed to set display name."` with a period; gold/test require the string without the period). This is a **TIA (test-instruction-alignment) failure**, not a capability-bottleneck failure. A super-capable being given only the instruction + repo state cannot reliably reach 51/51 — they would have to mind-read the gold author. Verdict: **Reject** in current form, but the task is *fixable* with a small set of additions to the instruction (enumerated in §5).

## Files in this inspection directory

| File | Purpose |
|---|---|
| `raw_instruction.txt` | The verbatim instruction shown to the agent (PR description + bulleted requirements). |
| `raw_test_sh.txt` | The verifier script that runs gold tests. Crucially it `git checkout`s the gold test files **after** the agent finishes (line 32–45). |
| `raw_solve_sh.txt` | The "oracle" solve script. **Truncated to 8000 bytes** in the dataset — incomplete. |
| `raw_dockerfile.txt` | The container Dockerfile (resets to base commit, no test files yet). |
| `raw_task_toml.txt` | Verifier/agent timeouts (3000s each). |
| `gold_patch.diff` | The actual gold patch from element-web commit `4fec43688…` — fetched fresh from GitHub since the dataset's `solve_sh` is truncated. |
| `gold_test_files.diff` | The gold tests + snapshots (only added at verifier time, **invisible to the agent**). |
| `gold_test__DeviceDetailHeading.tsx` | Gold component-level test for the new component. |
| `gold_test__SessionManagerTab.tsx` | Gold integration-level rename tests. |
| `gold_src__DeviceDetailHeading.tsx` | Gold implementation of the new component. |
| `gold_snap__*.snap` | Gold Jest snapshot files (exact HTML the agent must reproduce). |
| `test_stdouts/<run>.txt` | Verifier output per run (Required/Passed/Missing tests list). |
| `runs_summary.json` | Per-run agent/model/exception summary. |
| `run_<id>.md` | Per-run trajectory analysis (one per run, written by sub-inspectors). |
| `task_inspection.md` | This file — the synthesized verdict. |

---

## 0. Task summary

**What it asks.** Implement a "rename device sessions" feature in element-web: add a new React component `DeviceDetailHeading.tsx`, expose `saveDeviceName` from the `useOwnDevices` hook, drill it as a prop through `SessionManagerTab → CurrentDeviceSection → DeviceDetails → FilteredDeviceList`. Tweak `CurrentDeviceSection`'s spinner gating. Files are sourced from a real merged PR (#9282) by element-hq.

**How it's verified.** Standard SWE-bench Pro runner. The verifier `bash /tests/run_script.sh` first runs `git checkout 4fec436883b… -- <gold-test-files>` and then runs Jest on `DeviceDetailHeading-test.tsx`, `DeviceDetails-test.tsx`, `CurrentDeviceSection-test.tsx`, `FilteredDeviceList-test.tsx`, `SessionManagerTab-test.tsx`, plus their `__snapshots__/*.snap`. Required tests ≡ `fail_to_pass ∪ pass_to_pass` = 51 total. Pass = all 51 PASS.

**Critical structural property.** The gold test files are checked out **after** the agent's edit window closes. During implementation the agent only has the pre-PR test files in `/app`, which do not yet reference `DeviceDetailHeading`, `saveDeviceName`, the snapshot HTML, or any of the rename data-testids. **Anything the gold tests assert that diverges from the pre-PR pattern is invisible to the agent.**

**Trial setup.** 18 runs, 4 agent stacks × 3 models (some skipped):
- claude-code × claude-opus-4-6 (3 runs; 1 timeout)
- codex × gpt-5.4 (3 runs)
- gemini-cli × gemini-3.1-pro-preview (3 runs)
- terminus-2 × claude-opus-4-6 (3 runs; 1 timeout)
- terminus-2 × gemini-3.1-pro-preview (3 runs)
- terminus-2 × gpt-5.4 (3 runs)

**Outcome.** 0/18 successes. **All 18 runs got the user-visible feature working** (the read-mode renders display_name with a Rename button, the form opens, save/cancel/empty/error paths behave correctly). They all converge on the same hidden contracts they cannot satisfy.

---

## 1. How close are agents to succeeding?

**Very close on behavior, exactly 0 on the implementation contract.** From `test_stdouts/`:

| Run | Agent × Model | Required passed | Notable |
|---|---|---|---|
| 0aef9630 | claude-code × claude-opus-4-6 | 35/51 | Invented `device-heading-*` testid namespace; ran `jest -u`, false-positive locally |
| 1f78cf59 | claude-code × claude-opus-4-6 (timeout) | 35/51 | Same wrong namespace; wrong log message `"Error setting device name"` |
| 50c89a30 | claude-code × claude-opus-4-6 | 35/51 | Closest claude-code on testids; used `device-rename-save-cta` not `-submit-cta` |
| 073520d4 | codex × gpt-5.4 | 35/51 | **Got gold log message right** (`"Error setting session display name"`); never ran jest |
| 2ca5fe0e | codex × gpt-5.4 | 35/51 | Same gold log message; wrote own repro spec (didn't run gold tests) |
| f309e195 | codex × gpt-5.4 | 35/51 | Ran actual gold-style tests, saw failures, shipped anyway |
| 489aff6c | gemini-cli × gemini-3.1-pro-preview | 35/51 | Never ran jest; used `-btn` suffixes |
| 5e4d82a2 | gemini-cli × gemini-3.1-pro-preview | 35/51 | Never ran jest; id-suffixed heading testid |
| e40088f9 | gemini-cli × gemini-3.1-pro-preview | 35/51 | Got `device-detail-heading` testid right; jest hung on 5-min timeout, gave up |
| 210b26e6 | terminus-2 × claude-opus-4-6 | 35/51 | **Best testid match**; **actively self-sabotaged**: wrote correct no-period error text, all 83 local tests passed, then `sed`-edited to add period because instruction said so |
| 3a95facc | terminus-2 × claude-opus-4-6 (timeout) | 27/51 | AgentTimeoutError after 3 messages; no patch applied; "missing" list shows collateral damage from empty tree |
| ca7a3f01 | terminus-2 × claude-opus-4-6 | 35/51 | Near-twin of 210b26e6; **same self-inflicted period regression** |
| 4b791725 | terminus-2 × gemini | 35/51 | Never ran jest; `-btn` suffixes |
| 57fdaca4 | terminus-2 × gemini | 35/51 | Saw 3 snapshot failures, diagnosed correctly, didn't pivot |
| adf2f8f0 | terminus-2 × gemini | 35/51 | Ran jest but got `0 total` every time (gold tests not on disk), shipped without coverage |
| 284403c9 | terminus-2 × gpt-5.4 | **0/51** | **Build-broken**: bogus `MatrixClientPeg` import in `useOwnDevices.ts` crashed every device test on load; collateral damage to ExternalLink/ThemeController/RightPanel/StopGapWidgetDriver test loading |
| 2b5b1172 | terminus-2 × gpt-5.4 | 35/51 | Most thorough local jest loop; green-on-stale-tests because gold tests not in tree |
| 9c286dba | terminus-2 × gpt-5.4 | 35/51 | Jest explicitly suggested `-u`; agent ignored, shipped with 18 local tests still red |

The "16 missing" count appears in **every run that successfully built the feature**. The 16 missing tests are the exact same set, listed in `test_stdouts/50c89a30…txt`:

```
DeviceDetailHeading > renders device name                                       (snapshot)
DeviceDetailHeading > renders device id as fallback when device has no display name
DeviceDetailHeading > displays name edit form on rename button click             (snapshot)
DeviceDetailHeading > cancelling edit switches back to original display
DeviceDetailHeading > clicking submit updates device name with edited value
DeviceDetailHeading > disables form while device name is saving
DeviceDetailHeading > toggles out of editing mode when device name is saved successfully
DeviceDetailHeading > displays error when device name fails to save
DeviceDetails > renders device with metadata                                     (snapshot)
DeviceDetails > renders device without metadata                                  (snapshot)
DeviceDetails > renders a verified device                                        (snapshot)
SessionManagerTab > Rename sessions > renames current session
SessionManagerTab > Rename sessions > renames other session
SessionManagerTab > Rename sessions > does not rename session or refresh devices is session name is unchanged
SessionManagerTab > Rename sessions > saves an empty session display name successfully
SessionManagerTab > Rename sessions > displays an error when session display name fails to save
```

The 35/51 baseline pass is exactly the pre-existing tests (DeviceTile, security cards, sign-out flows, etc.) plus the rename tests that incidentally don't depend on hidden contracts (none — the rename test cluster is uniformly hidden-contract-bound).

**The bimodality is interesting and small.** 16 of 18 runs land at exactly 35/51. One run (3a95facc) timed out so early that it never patched, scoring 27/51 against a partly-broken tree. One run (284403c9) introduced a bad `MatrixClientPeg` import that broke every device test on module load, scoring 0/51 (and the "missing" list bleeds into ExternalLink/ThemeController/RightPanel/StopGapWidgetDriver tests because their suites couldn't even load — collateral damage from the build break, not a real regression). **Other than the timeout and the build-break, every single run hits the same 16-test ceiling.** That convergence is overwhelming evidence the 16-test cluster is a fixed contract, not a randomly-distributed difficulty.

So: **median run = 16-test gap, all on the same contracts.** Reliability is not the issue — the missing tests are unreachable, not unreliable.

---

## 2. Cross-agent variance: surface reasons vs. root cause

### Surface reasons (what the agents *appear* to be doing wrong)

The 16-test gap decomposes into three independently fatal "wrong contract" buckets, all hidden:

**Bucket A — Wrong/missing `data-testid` strings (8 tests).** Every test that uses `getByTestId('device-heading-rename-cta' | 'device-rename-input' | 'device-rename-cancel-cta' | 'device-rename-submit-cta' | 'device-detail-heading' | 'device-rename-error')` fails outright when the agent uses different strings. The instruction says "expose stable testing hooks (e.g., `data-testid` attributes)" — example pattern, no required values. Agents pick reasonable but divergent names.

**Bucket B — Frozen snapshot HTML (4 tests).** `DeviceDetails > renders {device with metadata, device without metadata, a verified device}` and `DeviceDetailHeading > {renders device name, displays name edit form on rename button click}` all use `expect(...).toMatchSnapshot()` with the gold author's exact HTML pinned (e.g. `<div class="mx_DeviceDetailHeading mx_AccessibleButton mx_AccessibleButton_kind_link_inline">…<h3 class="mx_Heading_h3">…`). Agents produce equivalent React but different class names / element nesting / wrapping div structure. The gold snapshot file is **also** restored by the verifier `git checkout`, so the agent's local `jest -u` does nothing for the verifier.

**Bucket C — Hidden interface details for SessionManagerTab integration tests (5 tests).** The `Rename sessions` tests in `SessionManagerTab-test.tsx`:

- `renames current session` / `renames other session` — assert `mockClient.setDeviceDetails(deviceId, { display_name: newName })` is called with the *exact* call shape (positional deviceId, second arg is `{display_name: newName}`).
- `does not rename session or refresh devices is session name is unchanged` — asserts `mockClient.setDeviceDetails` is **not** called when the input equals the current display_name. The instruction does say "the name must only be persisted if it is different from the previous one" — this one *is* derivable. But it also asserts `mockClient.getDevices` was called only once; that requires `refreshDevices()` only fire on success.
- `saves an empty session display name successfully` — asserts empty string is passed, not coerced to undefined or null.
- `displays an error when session display name fails to save` — asserts `logSpy.toHaveBeenCalledWith("Error setting session display name", error)`. The exact log message **`"Error setting session display name"` is nowhere in the instruction** — the instruction only says "Any error must be propagated with a clear message." Also asserts `getByTestId('device-rename-error')` exists.

### The error-text contradiction (instruction-vs-gold mismatch)

Beyond the hidden contracts above, there is one place the instruction *did* try to pin down a string and **got it demonstrably wrong**:

| Source | Text |
|---|---|
| **Instruction** (line 54 of `raw_instruction.txt`) | `"Failed to set display name."` (with trailing period) |
| **Gold src** (`gold_src__DeviceDetailHeading.tsx:54`) | `_t('Failed to set display name')` (no period) |
| **Gold src** (gold `useOwnDevices.ts:152`) | `throw new Error(_t("Failed to set display name"))` (no period) |
| **Gold test** (`gold_test__DeviceDetailHeading.tsx:140`) | `expect(queryByText('Failed to set display name')).toBeTruthy();` (no period; default `exact: true`) |

A diligent agent who copies the *instruction's* exact-text mandate ("the UI should display the exact error message text…") puts the period in. `@testing-library`'s `queryByText` with default `exact: true` requires the entire `textContent` of an element to match the string — so an agent rendering `"Failed to set display name."` is **rejected** by `queryByText('Failed to set display name')`. The instruction *literally* told the agent to fail this test.

**The smoking gun for "this contradiction caused real damage":** runs **210b26e6** and **ca7a3f01** (terminus-2 × claude-opus-4-6) both:

1. Initially wrote `"Failed to set display name"` *without* the period (gold-correct).
2. Ran `npx jest --testPathPattern='settings/(devices/|tabs/user/SessionManagerTab)'` and saw **all 83 tests pass**.
3. Then **explicitly `sed`-edited the source to ADD the trailing period** because the instruction said `"Failed to set display name."`.
4. Submitted in the wrong state.

This is a clean, repeatable, model-stable example of the instruction *forcing* a regression on top of working code. The agent followed instructions and lost the test. (See `run_210b26e6-e98b-420d-81dc-6039a6b6e0f8.md` and `run_ca7a3f01-b7e4-41c1-8804-3d9043c16513.md`.)

**Counts.** Across 17 non-timeout runs, **15 used `"Failed to set display name."` (with period)** and 2 used `"Failed to set display name"` without — and the 2 that omitted the period still failed the test for *other* reasons (snapshot/testid mismatches). So the period typo isn't load-bearing on its own — but it is a clear, fixable instruction defect that actively harms the success rate when other contracts are addressed.

### Root cause (one sentence)

> The verifier asserts a much more specific contract than the instruction describes: exact `data-testid` names, exact snapshot HTML, and an exact log-message string — none of which a reasonable agent can recover from the instruction or the pre-PR repo state.

This is the inverse of the well-known "essential difficulty too high" pattern. Essential difficulty here is *moderate*: the feature is a 200-line React component + a 30-line hook tweak + 4 lines of prop drilling. Models can build it. The bottleneck is **mind-reading the gold author's micro-decisions** that the test asserts but the spec does not.

### Variance by stack (synthesized from all 18 `run_<id>.md` files)

Cross-stack variance is small in score (16/18 land at exactly 35/51) but visible in *behavior*:

| Stack | Local-test discipline | Testid scheme invented | Got gold log message? | Period error text? |
|---|---|---|---|---|
| claude-code × claude-opus-4-6 (3) | Ran `jest -u` 1–3× and got false-positive "all green" locally | `device-heading-*` namespace (`-edit`, `-rename-cta`, `-save-cta`, `-cancel-cta`); 50c89a30 closest with `-rename-cta`, `-input`, `-cancel-cta`, `-error` matching gold but `-save-cta` not `-submit-cta` | No (omitted or wrong) | Mixed (some both texts) |
| codex × gpt-5.4 (3) | Mostly didn't run jest; one run wrote its own `.spec.tsx` | `device-detail-heading-{edit,rename,input,save,cancel,error}` uniform prefix | **Yes (matches gold exactly)** | Yes (with period) |
| gemini-cli × gemini-3.1-pro-preview (3) | Tried `yarn test`, hung or errored, gave up | `device-detail-heading-read/-edit`, `-cta` for rename, `-btn` for save/cancel | No (`Error setting device name`/`session name`) | Yes (with period) |
| terminus-2 × claude-opus-4-6 (3, 1 timeout) | Ran full jest suite 12+ times, 83/83 passed locally | **Closest match to gold**: `device-detail-heading`, `device-heading-rename-cta`, `device-rename-input`, `device-rename-cancel-cta`, `device-rename-error` — but `device-rename-save-cta` not `-submit-cta` | **No** (no `logger.error` in saveDeviceName at all) | **Yes — actively `sed`-added after passing locally without it** |
| terminus-2 × gemini (3) | Mixed: one ran jest and saw real failures; two never validated | `device-detail-heading-read/-edit`, `-cta`/`-action`/`-rename-cta`, `-btn` or no suffix | No | Yes (with period) |
| terminus-2 × gpt-5.4 (3) | One ran ~25 tests locally and stayed green; one broke imports | `device-detail-heading-{view,edit,rename,input,message,error,save,cancel}` uniform prefix | Mixed (one matches; two omit; one has `device display name`) | Yes (with period) |

**Surface vs. root cause analysis:**

- **Surface symptoms** look different across stacks — claude invents `device-heading-rename-cta`, codex invents `device-detail-heading-rename`, gemini invents `device-rename-cta`, etc. This *could* be misread as "different stacks have different exploration habits." It isn't.
- **Root cause is identical**: every stack faces the same information-theoretic problem — the gold tests are not in `/app` during the agent window, so the agent has no signal that distinguishes `device-rename-save-cta` from `device-rename-submit-cta`. They all generate locally-coherent (but verifier-incompatible) testids by extrapolating from the instruction's example pattern + element-web's BEM-ish conventions. The fact that *no two stacks converge on the same testid set* is itself evidence that the contract is unrecoverable from the visible environment.
- **Local-test discipline does not help** because the gold tests aren't on disk. Even the most thorough loops (terminus-2/claude's 83-test green pass, terminus-2/gpt5's 25/25 pass) are green-on-stale-tests. Several agents *did* run jest successfully against the agent-edited tests-of-record — and shipped because those tests were green. That's not laziness; the only signal jest gives them is "your edits don't break the pre-existing tests." That signal was always going to be uninformative.
- **Where stacks differ in *capability*** is on the small set of contracts that ARE recoverable: `logger.error("Error setting session display name", error)` is recoverable by reading the existing `useOwnDevices.ts` (`logger.error("Error loading sessions:", error)` and `logger.error("Error getting device cross-signing info", error)` are sibling patterns) and writing a parallel one. Codex got this right 3/3. Terminus-2/claude omitted the log call entirely 2/2 and added it differently 1/1. Gemini wrote a wrong but plausible variant 3/3. **This is the only place I'd say capability genuinely separates the stacks.**

The 3a95facc timeout (terminus-2/claude) is the only run where capability/budget was load-bearing — agent didn't even reach the patch phase.

The 284403c9 collateral damage (terminus-2/gpt-5.4) is the only run where a *capability error* — picking a non-existent import path `MatrixClientPeg` — produced a build break that masked everything. This is a real capability bottleneck: it's a TypeScript-level error the agent should have caught with a test run, but didn't. Worth noting that even *with* this build break, the agent would still have hit the same 16-test cluster — it just additionally took out the build.

---

## 3. Concrete agent behavior on each failing test (expected vs. produced)

Below, "expected" is from the gold tests (`gold_test__*.tsx`, `gold_snap__*.snap`); "produced" is the typical near-miss agent's output. Per-run divergence is in the `run_<id>.md` files.

### 3a. `DeviceDetailHeading > renders device name` (snapshot)

**Test code** (`gold_test__DeviceDetailHeading.tsx:44-47`):
```js
it('renders device name', () => {
    const { container } = render(getComponent());
    expect({ container }).toMatchSnapshot();
});
```
**Expected snapshot** (excerpt from `gold_snap__DeviceDetailHeading.snap`):
```html
<div class="mx_DeviceDetailHeading" data-testid="device-detail-heading">
  <h3 class="mx_Heading_h3">My device</h3>
  <div class="mx_AccessibleButton mx_DeviceDetailHeading_renameCta mx_AccessibleButton_hasKind mx_AccessibleButton_kind_link_inline" data-testid="device-heading-rename-cta" role="button" tabindex="0">Rename</div>
</div>
```
**Typical agent output.** Different class names (`mx_DeviceHeading`, `mx_RenameButton`), different element types (`<button>` instead of an `AccessibleButton` rendering as `<div role="button">`), missing `data-testid="device-detail-heading"` on the wrapping div, missing the `mx_AccessibleButton_kind_link_inline` modifier class. → fails.

### 3b. `DeviceDetailHeading > renders device id as fallback when device has no display name`

**Test code**:
```js
const { getByText } = render(getComponent({ device: { ...device, display_name: undefined } }));
expect(getByText(device.device_id)).toBeTruthy();
```
**Inferable from instruction.** "if that value is undefined, it must display the `device_id`" — yes. Most agents *do* implement this. But it fails for agents who put fallback text inside an attribute, or who use `display_name ?? ''` and never render device_id, or who wrap device_id in a structure where `getByText` can't find it.

### 3c. `DeviceDetailHeading > displays name edit form on rename button click` (snapshot + getByTestId)

```js
fireEvent.click(getByTestId('device-heading-rename-cta'));
expect({ container }).toMatchSnapshot();
```
**Hidden contracts**: testid `device-heading-rename-cta`, snapshot HTML of the form (form classes `mx_DeviceDetailHeading_renameForm`, field classes `mx_Field mx_Field_input mx_DeviceDetailHeading_renameFormInput`, exact `<p id="device-rename-{device_id}">…<span class="mx_Caption" id="device-rename-description-{device_id}">…`). No agent reproduces this verbatim.

### 3d. `DeviceDetailHeading > cancelling edit switches back to original display`

```js
fireEvent.click(getByTestId('device-heading-rename-cta'));
fireEvent.click(getByTestId('device-rename-cancel-cta'));
expect(container.getElementsByClassName('mx_DeviceDetailHeading').length).toBe(1);
```
**Hidden contracts**: testids `device-heading-rename-cta`, `device-rename-cancel-cta`; CSS class `mx_DeviceDetailHeading` on the read-mode container. Behavior (cancel returns to read mode) is inferable. Class name is not.

### 3e. `DeviceDetailHeading > clicking submit updates device name with edited value`

```js
fireEvent.click(getByTestId('device-heading-rename-cta'));
fireEvent.change(getByTestId('device-rename-input'), { target: { value: 'new device name' } });
fireEvent.click(getByTestId('device-rename-submit-cta'));
expect(saveDeviceName).toHaveBeenCalledWith('new device name');
```
**Hidden contracts**: testids `device-heading-rename-cta`, `device-rename-input`, `device-rename-submit-cta`. Also the agent's `saveDeviceName` prop must be called positionally with just the new name (not `(deviceId, newName)` — that's the *hook*'s signature; the prop into `DeviceDetailHeading` is a curried `(deviceName: string) => Promise<void>`). The instruction does specify "An object containing device (the device object) and saveDeviceName (an async function to persist the new name)" but doesn't quite say which signature.

### 3f. `DeviceDetailHeading > disables form while device name is saving`

```js
expect(getByTestId('device-rename-cancel-cta').getAttribute('aria-disabled')).toEqual("true");
expect(getByTestId('device-rename-submit-cta').getAttribute('aria-disabled')).toEqual("true");
expect(container.getElementsByClassName('mx_Spinner').length).toBeTruthy();
```
**Hidden contracts**: testids again, plus `mx_Spinner` class. The `aria-disabled` requirement is inferable from "visual indicator should inform the user that the operation is in progress" + "Save"/"Cancel" buttons, but the *exact* spinner class name `mx_Spinner` is element-web-internal — only inferable by reading existing element-web code (which the agent can do).

### 3g. `DeviceDetailHeading > toggles out of editing mode when device name is saved successfully`

```js
fireEvent.click(getByTestId('device-rename-submit-cta'));
await flushPromisesWithFakeTimers();
expect(getByTestId('device-detail-heading')).toBeTruthy();
```
**Hidden contract**: testid `device-detail-heading` on the read-mode container. Instruction says "render a stable container for the heading so it is possible to assert the mode change" — pattern, no name.

### 3h. `DeviceDetailHeading > displays error when device name fails to save`

```js
const saveDeviceName = jest.fn().mockRejectedValueOnce('oups').mockResolvedValue({});
…
expect(queryByText('Failed to set display name')).toBeTruthy();
expect(container.getElementsByClassName('mx_Spinner').length).toBeFalsy();
fireEvent.click(getByTestId('device-rename-submit-cta'));
expect(queryByText('Failed to set display name')).toBeFalsy();
```
**Hidden contracts**: error text without period (instruction has it with period — direct contradiction); spinner class `mx_Spinner`; testid `device-rename-submit-cta`; behavior that re-submitting clears the error (inferable).

### 3i. `DeviceDetails > renders {a verified device, device with metadata, device without metadata}` (snapshot)

These are integration-level snapshot tests on `DeviceDetails`, which is a **pre-existing** component the agent only minimally edits (to thread `saveDeviceName` and embed `<DeviceDetailHeading>`). The pre-PR `DeviceDetails` had `<h3 class="mx_Heading_h3">{device.display_name || device.device_id}</h3>` directly. The gold replaces this with `<DeviceDetailHeading device={…} saveDeviceName={…} />`. The snapshot now includes the *full* `DeviceDetailHeading` HTML. Any divergence in the `DeviceDetailHeading` HTML cascades into all three `DeviceDetails` snapshot tests.

### 3j. `SessionManagerTab > Rename sessions > renames current session / renames other session`

```js
fireEvent.click(getByTestId('device-heading-rename-cta'));
const input = getByTestId('device-rename-input');
fireEvent.change(input, { target: { value: newDeviceName } });
fireEvent.click(getByTestId('device-rename-submit-cta'));
…
expect(mockClient.setDeviceDetails).toHaveBeenCalledWith(alicesDevice.device_id, { display_name: newDeviceName });
expect(mockClient.getDevices).toHaveBeenCalledTimes(2);
```
Same testids; also requires that on success, `refreshDevices` (which calls `getDevices`) fires exactly once (so total getDevices calls = 1 initial + 1 refresh = 2). Inferable behavior, hidden testids.

### 3k. `SessionManagerTab > Rename sessions > does not rename session or refresh devices is session name is unchanged`

```js
await updateDeviceName(getByTestId, alicesDevice, alicesDevice.display_name);
expect(mockClient.setDeviceDetails).not.toHaveBeenCalled();
expect(mockClient.getDevices).toHaveBeenCalledTimes(1);
```
Behavior (no-op when name unchanged) **is** in the instruction. But the testid scaffold is required to even reach the assertion.

### 3l. `SessionManagerTab > Rename sessions > saves an empty session display name successfully`

```js
await updateDeviceName(getByTestId, alicesDevice, '');
expect(mockClient.setDeviceDetails).toHaveBeenCalledWith(alicesDevice.device_id, { display_name: '' });
```
Behavior (empty string accepted) **is** in the instruction. Testid scaffold required.

### 3m. `SessionManagerTab > Rename sessions > displays an error when session display name fails to save`

```js
const logSpy = jest.spyOn(logger, 'error');
const error = new Error('oups');
mockClient.setDeviceDetails.mockRejectedValue(error);
…
expect(logSpy).toHaveBeenCalledWith("Error setting session display name", error);
expect(getByTestId('device-rename-error')).toBeTruthy();
```
**Two undocumented hidden contracts**: the exact log-message string `"Error setting session display name"` AND the testid `device-rename-error` on the error span. Neither is in the instruction.

---

## 4. Is this task self-contained? Could a super-capable being solve it?

This section answers the user's framing questions directly.

### 4a. "Can the agent infer this from the environment?"

For each hidden contract:

| Hidden contract | Inferable from instruction? | Inferable from pre-PR repo? |
|---|---|---|
| Testid `device-heading-rename-cta` | No | No (no other testid uses this name in repo) |
| Testid `device-rename-input` | No | No |
| Testid `device-rename-cancel-cta` | No | No |
| Testid `device-rename-submit-cta` | No | No |
| Testid `device-detail-heading` | No | Hint: existing pattern uses `data-testid="device-detail-{device_id}"` on `DeviceDetails` itself, not on the heading — agents would naturally extrapolate `device-heading` or `device-name` instead |
| Testid `device-rename-error` | No | No |
| CSS class `mx_DeviceDetailHeading` | No | Convention `mx_<ComponentName>` is element-web-wide and *is* inferable. ✓ |
| CSS classes `mx_DeviceDetailHeading_renameForm`, `_renameFormInput`, `_renameFormHeading`, `_renameFormButtons`, `_renameFormError`, `_renameCta` | Partial. The BEM-ish `mx_<Comp>_<part>` convention is inferable, but the exact `_part` names (e.g. `_renameFormHeading` vs. `_formTitle`) are not. |
| Heading element `<h3>` with class `mx_Heading_h3` | No (instruction silent on heading level) | Partial — existing repo uses `<Heading size='h3'>` in similar `Subsection` components, an agent could find this |
| Snapshot HTML structure (Field component, AccessibleButton, Caption, exact ID format `device-rename-{deviceId}`) | No | Partial — these are element-web shared components and *would* be used by an agent reading the existing code |
| Log message `"Error setting session display name"` | No | No (different from pre-PR `"Error loading sessions:"` — close but different) |
| Error text exact string | **Contradiction**: instruction says `"Failed to set display name."` (with period), gold says without |

**Net.** Roughly half the contracts are weakly inferable via element-web's BEM-style conventions and existing component patterns; the testids and the exact log message are not inferable at all. The error text is **mis-specified**.

### 4b. "Can a super-capable being solve this with current instructions and environment?"

**No, not reliably.** A perfect agent given only the artifacts in `/app` plus the instruction would need to randomly guess:

1. The exact strings `"device-heading-rename-cta"`, `"device-rename-input"`, `"device-rename-cancel-cta"`, `"device-rename-submit-cta"`, `"device-detail-heading"`, `"device-rename-error"` (six binary-large-string guesses, each with O(10⁴+) plausible alternatives — combined probability of correct guesses ≈ 0).
2. The exact log-message string `"Error setting session display name"` (e.g. vs. `"Failed to update device display name"`, `"Error renaming session"`, `"Error saving device name"`).
3. The exact JSX class structure that produces a snapshot byte-equal to the gold snapshot — which requires using `Field`, `AccessibleButton`, `Caption`, `Heading` from the right paths, with the right `kind` modifiers, in the right nesting order.

Some of these are *retrievable* if the agent has been pre-trained on element-web's commit history and can recall PR #9282 verbatim — but that is the opposite of "solving the task," it's "having seen the answer." None of this is *derivable* from the instruction.

The task is therefore **not theoretically self-contained** in its current form. The instruction under-specifies the test contract.

### 4c. "What 'sufficient capability' would mean here"

If we relax to "find the closest equivalent on GitHub": a super-capable being could `git log -- "**/DeviceDetailHeading*"` against the actual element-web repo (the dataset's Dockerfile resets `/app` to commit `b8bb8f163a89cb6f2af0ac1cfc97e89deb938368`, the parent of #9282 — so `git log` in `/app` shows the parent's history, not the PR). Internet access in the sandbox is generally disallowed for SWE-bench Pro. So even with "sufficient capability," the agent has no legitimate signal.

The only ways an agent could get to 51/51 are: (i) memorized the gold patch from training data, or (ii) random guessed correctly on every hidden contract. Neither is "capability" in any meaningful sense.

---

## 5. Proposed fixes (not simplifications)

Each fix preserves the difficulty of "implement a real PR" but eliminates the *unfair* component. Listed in increasing order of rewrite effort; only fixes A+B+C together would I expect to bring success rates above ~30%.

### Fix A — Specify the required `data-testid` strings (instruction-side, smallest fix)

Add to the instruction's "data-testid" bullet:

> The component must expose the following stable `data-testid` attributes (verifiers will look these up by name):
>
> - `device-detail-heading` — the read-mode container `<div>`
> - `device-heading-rename-cta` — the "Rename" trigger button
> - `device-rename-input` — the editable name input
> - `device-rename-submit-cta` — the "Save" button
> - `device-rename-cancel-cta` — the "Cancel" button
> - `device-rename-error` — the error-message element shown on failed save

This single addition unblocks ~10 of the 16 missing tests (every test that calls `getByTestId(...)`). Cost to the task author: 6 new bullet lines. Capability ask is unchanged.

### Fix B — Specify the exact log-message string

Add to the `useOwnDevices` bullet:

> On error, log via `logger.error("Error setting session display name", error)` before rethrowing. (This message string is asserted by tests via `jest.spyOn(logger, 'error')`.)

This unblocks the `displays an error when session display name fails to save` test in SessionManagerTab.

### Fix C — Fix the error-text contradiction

In the instruction, change:
> the UI should display the exact error message text "Failed to set display name."

to:
> the UI should display the exact error message text `"Failed to set display name"` (no trailing period — asserted by `queryByText(...)` with default exact-match).

Cost: one bullet edit. Removes the most insidious failure mode (the agent literally followed instructions and lost the test).

### Fix D — Replace snapshot tests with structural assertions, or distribute the gold snapshots up front

Two non-overlapping options:

**Option D1 (test-side)**: Replace the three `DeviceDetails > renders ...` snapshot tests and the two `DeviceDetailHeading > renders / displays ...` snapshot tests with role/text/testid assertions:

```js
expect(getByRole('heading', { level: 3, name: 'My device' })).toBeTruthy();
expect(getByRole('button', { name: 'Rename' })).toBeTruthy();
```

This preserves the *behavior* the snapshots were meant to lock down ("the heading and rename button render correctly") without enforcing exact CSS class names. Cost to the task author: rewrite ~60 lines of test code in 2 files. Risk: under-specifies the visual structure relative to what the gold author intended.

**Option D2 (env-side)**: The dataset's `before_repo_set_cmd` already checks out the gold *test* files at verifier time. Have it ALSO check out the gold *snapshot* files into `/app/test/components/views/settings/devices/__snapshots__/` *before* the agent runs, and tell the agent in the instruction: "Snapshot files in `__snapshots__/` express the exact rendered HTML the implementation must produce. Do not modify them — make your component render to match." This converts the snapshots from a hidden contract into a visible one. Cost: change one line in the verifier config. Capability ask: now the agent can see the target HTML and reverse-engineer the JSX, which is a different task — but it is an *honest* task.

Of D1 and D2, **D2 is the more conservative** because it preserves the intent of the gold patch (locking down visual structure) while making the contract visible.

### Fix E — Distribute the entire gold-test file to the agent up front

The bluntest fix: ship the gold test files (or a "spec of what we will assert") in `/app/specs/` at start. This is what most TDD-style benchmarks do (e.g., HumanEval, MBPP). It collapses "implement a feature" into "make the tests green," which is a legitimate but different exercise. SWE-bench Pro deliberately avoids this because it wants to test "implement this PR description," not "make tests green." So Fix E **is a simplification** in the user's sense and I would not recommend it for this task.

### Recommended fix combination

**A + B + C + D2** — keep snapshots as a contract, but (i) name the testids, (ii) name the log message, (iii) fix the period typo, and (iv) ship the snapshot files as part of the visible env. This preserves the spirit of "real PR implementation," removes the mind-reading component, and predicts ≥ ~50% success rate based on per-run trajectories that already implement everything else correctly.

A+B+C alone (without D2 or D1) would unblock ~11 of 16 missing tests; the remaining 5 snapshot tests would still fail intermittently for agents whose React differs from gold.

---

## 6. Agent hacking / cheating risk

**Possible vectors examined:**

1. **Agent reads `/tests/config.json` directly during execution.** The `test_sh` (lines 32-62) shows that `/tests/config.json` contains `before_repo_set_cmd` (which encodes the gold test checkout command), `selected_test_files_to_run`, `fail_to_pass`, `pass_to_pass`. If the agent's container has read access to `/tests/` *during* the agent window, the agent can:
   - Read `fail_to_pass` and `pass_to_pass` to see test names (not test bodies, but enough to grep candidate testids).
   - Read `before_repo_set_cmd` to find the gold commit hash, then `git checkout <gold-commit> -- <test-files>` themselves.
   - Read `before_repo_set_cmd` and run it themselves to materialize the gold tests, then mirror them.

   **Risk level: high if `/tests/` is readable during the agent window.** A SWE-bench Pro container should *not* expose `/tests/` to the agent before verifier time — but the test_sh assumes it exists at verifier time, and there's no explicit barrier. **No agent in the 18 trials attempted this** (per upcoming `run_<id>.md` summaries). But future agents, especially auto-generated ones, may try.

2. **Agent runs `git log` and finds the PR commit.** The container resets to the parent commit `b8bb8f163a89cb…`; the PR commit `4fec43688…` is not in any branch from this base. `git log` would not show it. **Risk level: low.**

3. **Agent fetches the PR from GitHub.** SWE-bench Pro typically blocks outbound HTTPS in the sandbox. If outbound is allowed, an agent could `curl https://api.github.com/repos/element-hq/element-web/commits/4fec43688…` and download the gold patch verbatim. The PR title "Device manager - rename session (PSG-528) (#9282)" + the date + the file-list overlap would identify it within seconds. **Risk level: depends on container egress policy.** No agent in the 18 trials tried this.

4. **Agent writes a fake "result success" file.** The verifier writes `/logs/verifier/reward.txt` from the trap in `test_sh`. If the agent can write to `/logs/verifier/reward.txt = 1` before the verifier runs, they pass. The trap explicitly overwrites that file based on the eval's exit code, so this would be defeated *unless* the agent could control the exit signal. **Risk level: low.**

5. **Agent modifies the test files.** The instruction explicitly says "I've already taken care of all changes to any of the test files described in the <pr_description>. This means you DON'T have to modify the testing logic or any of the tests in any way!" — but this is an instruction, not an enforcement. The verifier `git checkout`s the gold tests over the agent's local edits *anyway*, so modifying tests is ineffective. **Risk level: low (cheating is impossible by construction).**

6. **Agent modifies snapshots locally.** Several agents (per the upcoming run analyses) ran `jest -u` to update snapshots locally after their edits — this is a legitimate jest workflow. But the verifier overwrites snapshots with gold via the same `git checkout`, so this provides no advantage. Not a hack, just wasted effort.

**Net assessment.** No exploitable cheating path observed in the 18 trials. The most concerning theoretical vector is the readability of `/tests/config.json` during the agent window — needs container-level verification. Agents in this dataset did not exploit it.

---

## 7. Final verdict — is the failure the task's fault or the agent's?

**The failure is predominantly the task's fault.** Specifically:

- ~10 of 16 missing tests fail due to **undisclosed `data-testid` strings**. Not inferable.
- ~3 of 16 fail due to **undisclosed log-message text** + **undisclosed snapshot HTML** that the instruction says nothing about.
- ~3 of 16 fail due to **frozen Jest snapshots** that pin the gold author's exact JSX/CSS choices that the instruction does not pin.
- 1 (the `displays error when device name fails to save` test) is exacerbated by an **outright contradiction** between instruction text and gold.

**The remaining capability gap** — and there is some — is on the snapshot tests, where even with all hidden testids surfaced, an agent who picks a slightly different JSX nesting (say, wrapping the heading in a `Subsection`, or using `<button>` instead of `AccessibleButton`) still fails. This *would* be a real capability test if the snapshots were honestly disclosed. As things stand, that test is mixed: ~80% task-fault, ~20% capability-genuine.

**Recommendation.** The Gemini audit's "accept" verdict (which framed the 0/18 outcome as "high essential difficulty due to multi-file React drilling") is **incorrect**. The Yuxin audit's "unsure" leaning toward TIA-fail and snapshot-derivability is **correct**. **Reject** in current form; add fixes A+B+C (instruction edits) at minimum and D2 (snapshot env) for full repair.

A repaired task is *valuable* — it would test multi-file long-horizon React refactor capability, which is a real bottleneck and is currently bucketed mostly under "they got the feature working but couldn't manage long-horizon coordination." The current task confounds that with mind-reading, which is not a measurable capability.

---

## Appendix — per-run trajectory file index

| File | Run | Outcome |
|---|---|---|
| `run_0aef9630-ce20-43aa-ba82-0ad90e454885.md` | claude-code × claude-opus-4-6 | 35/51 |
| `run_1f78cf59-e38b-4756-9782-1517b58570dd.md` | claude-code × claude-opus-4-6 (timeout) | 35/51 |
| `run_50c89a30-394c-499a-9e4b-bc93dc4ca8ca.md` | claude-code × claude-opus-4-6 | 35/51 |
| `run_073520d4-ae57-47ac-9688-12a2a06948a8.md` | codex × gpt-5.4 | 35/51 |
| `run_2ca5fe0e-cdd6-4e2c-85ea-90485c9a1471.md` | codex × gpt-5.4 | 35/51 |
| `run_f309e195-fb7f-480e-9864-d0d9155f0317.md` | codex × gpt-5.4 | 35/51 |
| `run_489aff6c-7d61-4333-9225-50dfe780cfde.md` | gemini-cli × gemini-3.1-pro-preview | 35/51 |
| `run_5e4d82a2-b4e3-4b39-b9c8-eeaa6d365e8a.md` | gemini-cli × gemini-3.1-pro-preview | 35/51 |
| `run_e40088f9-1534-493e-88fd-af6905b32c44.md` | gemini-cli × gemini-3.1-pro-preview | 35/51 |
| `run_210b26e6-e98b-420d-81dc-6039a6b6e0f8.md` | terminus-2 × claude-opus-4-6 | 35/51 — **smoking-gun period regression** |
| `run_3a95facc-93fb-4223-80c6-f1b387ada3db.md` | terminus-2 × claude-opus-4-6 (timeout) | 27/51 — no patch |
| `run_ca7a3f01-b7e4-41c1-8804-3d9043c16513.md` | terminus-2 × claude-opus-4-6 | 35/51 — **smoking-gun period regression** |
| `run_4b791725-49df-44d3-b1bc-0e66a0e325ea.md` | terminus-2 × gemini | 35/51 |
| `run_57fdaca4-b2cf-4249-9eb4-788c6603708a.md` | terminus-2 × gemini | 35/51 |
| `run_adf2f8f0-1f3f-4f63-8956-93a1c822ef15.md` | terminus-2 × gemini | 35/51 |
| `run_284403c9-856f-4c86-b609-435a6395287e.md` | terminus-2 × gpt-5.4 | **0/51** — broken-import build break |
| `run_2b5b1172-8232-4a8d-9e18-46cda8f12bb0.md` | terminus-2 × gpt-5.4 | 35/51 |
| `run_9c286dba-2e8d-4c18-9834-b625d1a20c94.md` | terminus-2 × gpt-5.4 | 35/51 |
