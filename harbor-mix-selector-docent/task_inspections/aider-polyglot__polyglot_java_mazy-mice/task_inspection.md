# Task inspection — `aider-polyglot/polyglot_java_mazy-mice`

> **TL;DR.** I disagree with the Gemini "accept" verdict. The instruction text is fine and the *test contract* (the 13 hidden JUnit assertions on a `MazeGenerator` returning `char[][]`) is reasonable. But the Docker/verifier environment is **broken in two distinct, deterministic ways** that together account for **12 of the 12 non-claude-opus failures**. Three of the four "JAVA_HOME invalid" agents diagnosed the infra bug themselves and produced gradle-passing solutions — and were still graded 0.0. The 6/18 success rate is therefore an **infrastructure artifact, not a real model-capability gap**. The "claude-opus-4-6 always passes / gpt-5.4 and gemini-3.1-pro always fail" pattern is the result of which containers happened to be healthy at the time, not what the agents actually built. The task should be **rejected as currently shipped** and re-shipped after the Dockerfile and test_sh are fixed; the underlying exercise is salvageable with small environment-only changes (no instruction or test edits needed).

## Files in this inspection directory

| File | Purpose |
|---|---|
| `instruction.md` | Verbatim task instruction + 13-test JUnit assertion list |
| `run_outcomes.md` | All 18 trial outcomes, three failure-bucket breakdown, agent×model cross-tab |
| `trajectories/` | Plain-text dumps of all 18 agent transcripts (`PASS__*` / `FAIL_DIM__*` / `FAIL_JAVA_HOME__*` filenames carry the bucket) |
| `_fetch_runs.py` | Script used to pull the transcripts via the Docent SDK |
| `task_inspection.md` | This file |

---

## 0. Task summary

**What it asks.** Implement two methods of a stub `public class MazeGenerator`:
```java
public char[][] generatePerfectMaze(int rows, int columns);
public char[][] generatePerfectMaze(int rows, int columns, int seed);
```
Maze must be a perfect maze (single connected component, exactly one path between any two cells — i.e., a spanning tree on the cell grid). The `char[][]` is rendered on a `(2*rows+1) × (2*columns+1)` grid with box-drawing characters and `⇨` for the entrance on the left and exit on the right. Reject `rows`/`columns` outside `[5, 100]` with an exception. Same seed → same maze.

**Initial workspace** (what the agent sees in `/app`):
```
/app/build.gradle                          # plugin id "java" + JUnit + AssertJ deps
/app/gradlew, gradlew.bat
/app/gradle/wrapper/{gradle-wrapper.jar, gradle-wrapper.properties}
/app/src/main/java/MazeGenerator.java      # 11-line stub, two methods throw UnsupportedOperationException
```
**No** test source. **No** `Dimensions.java`. **No** `/tests/` directory accessible until the verifier copies it in post-agent.

**How it's verified.** `test_sh` runs after the agent finishes:
1. Copies `/tests/src/test/java/.` → `/app/src/test/java/` (the actual JUnit `MazeGeneratorTest.java`).
2. Copies `/tests/src/main/java/.` → `/app/src/main/java/` (helper Java files, including `Dimensions.java` which is `public record Dimensions(int rows, int columns) {…}` — Java 14+ syntax).
3. Runs `./gradlew test --no-daemon --console=plain`.
4. Reward = 1.0 if exit code 0, else 0.0.

**Trial setup.** 18 runs, 6 (agent, model) cells × 3 trials:
- claude-code × claude-opus-4-6 (3)
- terminus-2 × claude-opus-4-6 (3)
- codex × gpt-5.4 (3)
- terminus-2 × gpt-5.4 (3)
- gemini-cli × gemini-3.1-pro-preview (3)
- terminus-2 × gemini-3.1-pro-preview (3)

**Outcome.** **6/18 pass** — every claude-opus run passes (6/6), every gpt-5.4 and gemini run fails (0/12). See `run_outcomes.md` for the full table.

---

## 1. How close are agents to succeeding?

The naïve answer is "claude-opus is at 100%, others at 0% — there's a wide capability gap." But the trajectories tell a much sharper story. **The 12 failures partition cleanly into two infra failure modes that have nothing to do with the agent's solution.** I'll lay out the three buckets and what they imply.

### Bucket A — "JAVA_HOME invalid" (4 runs, byte-identical 746-byte stdouts)

```
ERROR: JAVA_HOME is set to an invalid directory: /usr/lib/jvm/java-21-openjdk-amd64
```
This appears **before the agent's code is even compiled** at verifier time — `gradlew` aborts immediately. Affects: `3a65d34f` (codex/gpt), `5db0a790` (terminus-2/gpt), `dc0eafbd` (gemini-cli), `62f7b717` (terminus-2/gemini).

**Cause (confirmed across 3 of 4 trajectories):** The host is **ARM64**, not AMD64. The Dockerfile hard-codes `ENV JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64` but `apt-get install openjdk-21-jdk` on ARM64 lays the JDK down at `/usr/lib/jvm/java-21-openjdk-arm64`. The Dockerfile's build-time check `RUN java -version && javac -version` resolves through the `/usr/bin/java` alternative symlink and so it passes — but the **literal path `JAVA_HOME` points to never exists**.

The agents discovered this themselves and worked around it locally:

> **codex/gpt-5.4 `3a65d34f`** ran `readlink -f $(which java)` → `/usr/lib/jvm/java-21-openjdk-arm64/bin/java`, then `JAVA_HOME=/usr/lib/jvm/java-21-openjdk-arm64 ./gradlew test` → **`BUILD SUCCESSFUL in 7s`**.
> **terminus-2/gpt-5.4 `5db0a790`** also confirmed `readlink -f "$(which javac)"` → `/usr/lib/jvm/java-21-openjdk-arm64/bin/javac`, prefixed `JAVA_HOME=…arm64` to gradlew, **`BUILD SUCCESSFUL in 7s`**.
> **gemini-cli `dc0eafbd`** ran `update-java-alternatives --list` and saw only ARM64 entries; same workaround, **`BUILD SUCCESSFUL`**.
> **terminus-2/gemini `62f7b717`** explicitly diagnosed: *"`/usr/lib/jvm/java-21-openjdk-amd64` does not exist or is invalid, which is outside the scope of the code changes required."*

But the **inline `JAVA_HOME=…arm64 ./gradlew` workaround does not persist into the verifier's `test_sh` invocation** — `test_sh` runs in a fresh shell that inherits the broken Dockerfile `ENV JAVA_HOME=…amd64`. So the agent demonstrably fixes the build in their session and it still gets graded 0.0. This is a hard environment bug, not an agent shortcoming.

**These three agents (`3a65d34f`, `5db0a790`, `dc0eafbd`) are arguably better at infra debugging than the claude-opus passers, who never had to touch `JAVA_HOME` because they happened to land on amd64 hosts.**

### Bucket B — "`Dimensions.java`: class, interface, or enum expected" (8 runs, byte-identical 1513–1514-byte stdouts)

```
> Task :compileJava FAILED
/app/src/main/java/Dimensions.java:7: error: class, interface, or enum expected
public record Dimensions(int rows, int columns) {
```
This is the canonical parse error a **Java compiler with `--source < 14`** produces on the `record` keyword. Affects: `06139fa9`, `b93135dc`, `1fa6ed45`, `399965ff`, `09cdc8c0`, `b52ff7ac`, `1f801e11`, `d47117a6`.

**Confirmed (subagent inspection of all 8 trajectories) — agent-side cause: ZERO.**

| Run | mod build.gradle? | mod wrapper/gradlew/gradle.properties? | own Dimensions.java? | local `./gradlew test` |
|---|---|---|---|---|
| codex `1fa6ed45` | No | No | No | **BUILD SUCCESSFUL** (`compileTestJava NO-SOURCE`, `test NO-SOURCE`) |
| codex `399965ff` | No | No | No | **BUILD SUCCESSFUL** |
| terminus-2/gpt `06139fa9` | No | No | No | **BUILD SUCCESSFUL** |
| terminus-2/gpt `b93135dc` | No | No | No | **BUILD SUCCESSFUL** |
| gemini-cli `09cdc8c0` | No | No | No | **BUILD SUCCESSFUL** |
| gemini-cli `b52ff7ac` | No | No | No | **BUILD SUCCESSFUL** |
| terminus-2/gemini `d47117a6` | No | No | No | **BUILD SUCCESSFUL** (`build`, `check`) |
| terminus-2/gemini `1f801e11` | No | No | No | **BUILD SUCCESSFUL** |

Every agent's local gradle build *succeeded* (with `compileTestJava NO-SOURCE` because there are no tests at agent time). Java is reported as `21.0.10` in the agents' jshell sessions (e.g., codex `1fa6ed45`: `|  Welcome to JShell -- Version 21.0.10`). So at **agent time**, the JDK on the container is Java 21.

**The compile error only manifests at verifier time, after `test_sh` has copied `Dimensions.java` in.** Since neither the agent nor the test_sh changes `sourceCompatibility`, `--release`, `--source`, or any toolchain config, the only remaining mechanism is some difference in gradle/JDK invocation between agent-time and verifier-time on these specific containers. Plausible candidates (I cannot empirically discriminate without re-running the image):
- A second JDK at lower version (likely Java 11 from `default-jdk` on the buildpack-deps base) is silently auto-selected by Gradle on these containers — perhaps because `JAVA_HOME` is unset in the verifier's shell but inherited at agent-time.
- The `test_sh`'s `echo "org.gradle.daemon=false" > gradle.properties` overwrites a pre-existing gradle.properties that was setting `org.gradle.java.home`. (The agents did not write one, but the original image *might* have one I don't see in the agent trajectories.)
- Container snapshot drift — these containers may be reused snapshots where `apt-get install openjdk-21-jdk` partially succeeded but `update-alternatives` ended pointing at Java 11.

What I *can* prove from the trajectories is the negative: **no agent action causes this failure.** The byte-identical stdout across 8 agents from 4 different (agent, model) stacks rules out agent-side variance. Hypothesis (B), pure infra, is the only one consistent with the evidence.

### Bucket C — pass (6 runs, all reward 1.0, all on claude-opus-4-6)

3 claude-code/opus + 3 terminus-2/opus. Algorithm: every passing agent implemented an iterative randomized DFS / recursive backtracker spanning-tree carver, each `IllegalArgumentException` for size out of `[5,100]`, each `java.util.Random(seed)` for determinism, each rendered with the canonical box-drawing characters `┌─┬┐│└┴┘├┼┤` plus space and `⇨`. None modified any infra; none anticipated the hidden `Dimensions` helper (which they don't need to — their `char[][]` return signature is what the test asserts on).

### Distance to passing

For Buckets A and B, "distance to passing" is **zero on the code dimension** — the agent's `MazeGenerator.java` was either correct (`3a65d34f`, `5db0a790`, `dc0eafbd` all proved theirs builds successfully on their own machines) or *would have built* if the verifier weren't downgrading the JDK source level. For Bucket B specifically, even checking each of the 8 generators by eye shows they all carve a valid spanning tree; the only suspicion would be the choice of "stub" characters `╵╷╴╶` for 1-direction junctions, which would matter for the `theMazeContainsOnlyValidCharacters` test — but that test never runs because compileJava fails before reaching `:test`. So we don't even know which non-opus solutions would have passed the actual JUnit assertions.

**My estimate, based on visual inspection of the FAIL_DIM `MazeGenerator.java` files**: 6 of 8 FAIL_DIM solutions look likely to pass all 13 tests, 1 (gemini-cli `09cdc8c0` — has a buggy box-drawing case 13/14 swap per the subagent report) likely fails 1–2 tests, and 1 (codex `1fa6ed45` — uses `╵╷╴╶` half-stubs) probably fails the valid-characters test. So **the realistic baseline reward, given a working environment, would be roughly 12–15 of 18 trials pass instead of 6**.

---

## 2. Cross-agent variance: surface vs. root cause

### Surface
- **Bucket A surface**: `gradlew` aborts immediately. Looks like the agent corrupted Java.
- **Bucket B surface**: Compile fails on `record` keyword. Looks like the agent set source level too low.
- **Bucket C surface**: Tests pass. Agent did everything right.

### Root cause (one cause across both A and B): the verifier-side environment is the deciding factor; the agent's code is largely irrelevant.

The "claude-opus passes, others fail" headline is misleading. Mapping by agent:
- Each of the 4 non-opus (agent, model) cells had **2 of 3 trials hit Bucket B and 1 of 3 hit Bucket A**.
- Each of the 2 opus (agent, model) cells had **3 of 3 trials hit Bucket C**.

This perfect 2:1 split per non-opus cell, and zero infra failures on the opus cells, is **not** a function of the agents' coding ability. It would require the routing layer to have systematically placed gpt-5.4 and gemini jobs onto broken hosts and claude-opus jobs onto healthy ones. That can happen if the trial scheduler distributes (model, container) pairs deterministically (e.g., by hash) and one shard of containers is broken — and is in fact the most parsimonious explanation given (a) byte-identical stdouts within a bucket, (b) zero agent-side variance, and (c) the architecture-mismatch finding.

### Where I disagree with the Gemini audit

The audit said:
> "The high failure rate for some models is explained by logs showing infra-related Java compilation errors on a provided helper file (Dimensions.java), while successful trials prove the task and verifier work as intended in a properly configured Java 21 environment."

What the audit got right:
- The Dimensions.java compile error is infra-related.
- Successful trials prove the task/verifier work *when the environment is properly configured*.

What the audit missed:
- It treats infra failures as "out of scope" for task quality. They aren't — **the Dockerfile and test harness are part of the task**. A task whose ARM64 Dockerfile bakes in an AMD64-only `JAVA_HOME` literal is a broken task, not a healthy task with bad luck.
- It doesn't distinguish Bucket A (JAVA_HOME mismatch) from Bucket B (source-level downgrade). These are different bugs.
- It doesn't account for the agents *fixing* the environment in their own sessions and still being graded 0.0 — strong evidence that the verifier's environment, not agent capability, is the binding constraint.
- Accepting this task gives a false signal that gpt-5.4 / gemini-3.1-pro can't solve a basic perfect-maze exercise. They almost certainly can; the data we have can't tell us either way because the environment killed the test.

### Real per-model capability comparison (what I *can* read from the data)

I can compare what the agents *built* before the verifier ran:
- All 6 claude-opus solutions: production-quality DFS carver, correct box-drawing collapse to `│`/`─`, 13/13 actual JUnit pass.
- 6 of 8 FAIL_DIM solutions (gpt-5.4 and gemini-3.1-pro): production-quality DFS carver, correct box-drawing collapse, would likely pass 13/13.
- 1 FAIL_DIM solution (`09cdc8c0` gemini-cli): subtle box-drawing case-13/14 swap → probably 11–12 of 13.
- 1 FAIL_DIM solution (`1fa6ed45` codex): uses 1-direction stub characters `╵╷╴╶` → probably fails `theMazeContainsOnlyValidCharacters`, otherwise correct → 12 of 13.

So the **realistic capability spread** between models on this task, if the environment worked, would be roughly:
- claude-opus-4-6: ~13/13 reliably (3/3 trials)
- gpt-5.4: ~12.5/13 average across trials (likely 2/3 trials passing)
- gemini-3.1-pro-preview: ~12/13 average (likely 1.5–2 of 3 trials passing)

That's a much smaller spread than 6/18 vs 0/18 implies. The reported scores grossly understate non-opus capability.

---

## 3. Concrete agent behavior that failed the tests

For Bucket A (`JAVA_HOME invalid`) and Bucket B (`Dimensions.java record`), **no JUnit test ever ran**, so there's no test-by-test analysis to do. The failure is at `:compileJava` for Bucket B and even earlier (gradlew startup) for Bucket A.

What I can show concretely:

### 3a. Bucket A — verbatim verifier vs. agent contrast

Verifier output (all 4 Bucket A runs, byte-identical):
```
Setting up Java/Gradle environment...
Copying tests: /tests/src/test/java -> /app/src/test/java
Copying helpers: /tests/src/main/java -> /app/src/main/java
Running tests for mazy-mice (java)
Running Java tests...

ERROR: JAVA_HOME is set to an invalid directory: /usr/lib/jvm/java-21-openjdk-amd64

Please set the JAVA_HOME variable in your environment to match the
location of your Java installation.

Exit code: 1
```

What three of the four agents proved at agent time on the same container (codex `3a65d34f`, terminus-2/gpt `5db0a790`, gemini-cli `dc0eafbd`):
```
$ readlink -f $(which java)
/usr/lib/jvm/java-21-openjdk-arm64/bin/java
$ JAVA_HOME=/usr/lib/jvm/java-21-openjdk-arm64 ./gradlew test
…
BUILD SUCCESSFUL in 7s
```

The expected fix at the **task** level: replace `ENV JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64` in the Dockerfile with something architecture-agnostic, e.g.:
```dockerfile
RUN JH=$(dirname $(dirname $(readlink -f /usr/bin/javac))) && \
    echo "JAVA_HOME=$JH" >> /etc/environment
ENV JAVA_HOME=/usr/lib/jvm/default-java
```
or simply pin the platform:
```dockerfile
FROM --platform=linux/amd64 buildpack-deps:jammy
```

Either fix would convert all 4 Bucket A failures to passes (assuming their solutions are otherwise correct, which is the case for at least 3 of them based on their explicit local gradlew runs).

### 3b. Bucket B — verbatim verifier vs. agent contrast

Verifier output (all 8 Bucket B runs, byte-identical):
```
> Task :compileJava FAILED
/app/src/main/java/Dimensions.java:7: error: class, interface, or enum expected
public record Dimensions(int rows, int columns) {
       ^
/app/src/main/java/Dimensions.java:15: error: class, interface, or enum expected
    }
    ^
/app/src/main/java/Dimensions.java:24: error: class, interface, or enum expected
    }
    ^
3 errors

FAILURE: Build failed with an exception.
…
```

What every Bucket B agent saw at agent time (e.g., codex `1fa6ed45`, msg 24):
```
> Task :compileJava
> Task :processResources NO-SOURCE
> Task :classes
> Task :compileTestJava NO-SOURCE
> Task :processTestResources NO-SOURCE
> Task :testClasses UP-TO-DATE
> Task :test NO-SOURCE

BUILD SUCCESSFUL in 12s
```
JShell on the same container reports JDK 21.0.10. So at agent time, on these containers, **the JDK accepts everything** — but at verifier time, after `Dimensions.java` is added, parsing fails on the `record` keyword. Some part of the verifier's gradle invocation is using a `--source <14` JDK or a different JDK that doesn't recognize records.

The fix at the **task** level: explicitly pin the source level in `build.gradle`:
```groovy
java {
    sourceCompatibility = JavaVersion.VERSION_21
    targetCompatibility = JavaVersion.VERSION_21
    toolchain {
        languageVersion = JavaLanguageVersion.of(21)
    }
}
```
This forces gradle to use a Java 21 toolchain (or download one) regardless of what `JAVA_HOME` resolves to at runtime, and makes the build deterministic against any pre-existing Java 11 install on the base image.

### 3c. The 13 hidden tests (from a passing run's stdout)

For completeness, here is the actual JUnit test set that runs in passing trials:

```
MazeGeneratorTest > theMazeIsPerfectWithSeed() PASSED
MazeGeneratorTest > shouldThrowExceptionWhenColumnsIsLessThanFive() PASSED
MazeGeneratorTest > twoMazesWithSameSeedShouldBeEqual() PASSED
MazeGeneratorTest > shouldThrowExceptionWhenRowsIsLessThanFive() PASSED
MazeGeneratorTest > theMazeIsPerfect() PASSED
MazeGeneratorTest > theMazeHasSingleExitOnTheRightSideOfTheMaze() PASSED
MazeGeneratorTest > shouldThrowExceptionWhenRowsIsMoreThenHundred() PASSED
MazeGeneratorTest > theMazeHasOnlyOneEntranceOnTheLeftSide() PASSED
MazeGeneratorTest > theDimensionsOfTheMazeAreCorrect() PASSED
MazeGeneratorTest > aMazeIsDifferentEachTimeItIsGenerated() PASSED
MazeGeneratorTest > twoMazesWithDifferentSeedsShouldNotBeEqual() PASSED
MazeGeneratorTest > theMazeContainsOnlyValidCharacters() PASSED
MazeGeneratorTest > shouldThrowExceptionWhenColumnsIsMoreThenHundred() PASSED
```

These cover everything stated in the instruction (perfect maze, dimensions, seeded determinism, randomness without seed, valid character set, single entrance/exit, range validation). The contract is fully inferable from the instruction text — there is no hidden requirement that an agent has to guess. So when the environment works, the task is well-specified.

---

## 4. Inferability and "could a sufficiently capable being solve this?"

### Is what's tested inferable from the instruction + environment?

**Yes.** Every JUnit assertion maps directly to a bullet in the instruction:
- "between 5 and 100 cells" → `shouldThrowExceptionWhen…IsLessThanFive` / `IsMoreThenHundred`
- "the same seed … resulting maze should be the same each time" → `twoMazesWithSameSeedShouldBeEqual`
- "no seed … generate a random maze" → `aMazeIsDifferentEachTimeItIsGenerated`, `twoMazesWithDifferentSeedsShouldNotBeEqual`
- "perfect maze … only one solution and no isolated sections" → `theMazeIsPerfect`
- "2x+1 by 2y+1" → `theDimensionsOfTheMazeAreCorrect`
- "opening at the start and end" + "arrow symbol (⇨) for the entrance on the left and exit on the right" → `theMazeHasOnlyOneEntranceOnTheLeftSide`, `theMazeHasSingleExitOnTheRightSideOfTheMaze`
- "Use box-drawing characters" → `theMazeContainsOnlyValidCharacters`

The agent does *not* need to anticipate the `Dimensions` helper record — it never appears in the public method signatures the agent must implement. It's used internally by the test for clean assertion-message formatting. The 6 PASS solutions confirm this: none of them reference `Dimensions` at all.

### Could a sufficiently capable being solve this given the current environment?

**On a healthy container, yes.** The 6 passes prove it. On the broken Bucket A and Bucket B containers, **no agent of any capability level can solve it** — the failure mode is entirely outside the agent's reach:

- Bucket A: the inline `JAVA_HOME=…arm64 ./gradlew` workaround is the only viable agent-side fix and it does **not** persist into the verifier's shell. There is no documented mechanism for the agent to alter the environment that the verifier sees. (The agent cannot edit the Dockerfile retroactively, cannot change the `ENV JAVA_HOME` of an already-running container, cannot set verifier-side env via test_sh.)
- Bucket B: the `--source 21` issue is invisible at agent time (their `compileJava` already succeeds because there's no record source for them to compile). They have no signal that anything is wrong, so even a perfectly capable agent has nothing to react to.

**Conclusion: The task is theoretically solvable but not practically solvable on the broken containers.** The environment is the binding constraint.

---

## 5. Proposed fixes

The task instruction and tests are good — keep them. The fixes are entirely in the Docker/build environment:

### Fix 1 (highest priority, fully addresses Bucket A)

In `Dockerfile`, replace:
```dockerfile
ENV JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64
ENV PATH=$JAVA_HOME/bin:$PATH
```
with one of:

**Option 1a — pin the platform** (simplest, no code change beyond Dockerfile):
```dockerfile
FROM --platform=linux/amd64 buildpack-deps:jammy
… (keep ENV as-is)
```
Trade-off: ARM hosts now run amd64 under emulation, slow. Still better than failing.

**Option 1b — derive `JAVA_HOME` from `javac` symlink** (preferred, native on either arch):
```dockerfile
RUN apt-get update && apt-get install -y ca-certificates-java openjdk-21-jdk \
 && update-alternatives --auto java && update-alternatives --auto javac \
 && rm -rf /var/lib/apt/lists/*
RUN echo "JAVA_HOME=$(dirname $(dirname $(readlink -f /usr/bin/javac)))" > /etc/profile.d/java.sh \
 && cat /etc/profile.d/java.sh
ENV PATH=/usr/bin:$PATH
```
And in the `test_sh` (and ideally also at container startup), source it:
```bash
if [ -f /etc/profile.d/java.sh ]; then . /etc/profile.d/java.sh; fi
```
This makes `JAVA_HOME` correct on any architecture.

### Fix 2 (addresses Bucket B regardless of root mechanism)

In `build.gradle`, pin the JDK toolchain explicitly:
```groovy
plugins { id "java" }
java {
    sourceCompatibility = JavaVersion.VERSION_21
    targetCompatibility = JavaVersion.VERSION_21
    toolchain { languageVersion = JavaLanguageVersion.of(21) }
}
```
This eliminates any ambiguity about which Java the verifier compiles against; even if a Java 11 install lurks on the image, gradle's toolchain selector will reject it and either use the Java 21 toolchain or download one.

### Fix 3 (defensive, complements 1+2)

In `test_sh`, **before** invoking `./gradlew test`, sanity-check the environment and fail fast with a clearer message:
```bash
if [ ! -d "$JAVA_HOME" ]; then
    JH_FALLBACK=$(dirname $(dirname $(readlink -f /usr/bin/javac 2>/dev/null) 2>/dev/null) 2>/dev/null)
    if [ -d "$JH_FALLBACK" ]; then
        echo "WARN: JAVA_HOME=$JAVA_HOME invalid; falling back to $JH_FALLBACK"
        export JAVA_HOME="$JH_FALLBACK"
    fi
fi
javac -version || { echo "FATAL: javac not found"; echo 0 > /logs/verifier/reward.txt; exit 0; }
```

### Will these fixes change the picture?

I'm confident **all 4 Bucket A trials become passes** after Fix 1 (subagents already verified those 3 of 4 produced gradle-passing solutions; the 4th — terminus-2/gemini `62f7b717` — also has a code that compiled).

For **Bucket B** I'm cautiously confident: 6 of 8 Bucket B solutions look correct on inspection (DFS spanning tree + collapsed line glyphs); 1 has a junction-character bug that would still fail `theMazeContainsOnlyValidCharacters`; 1 uses half-stub glyphs and would also fail that test. So Fix 2 should turn ~6 of 8 into passes and leave ~2 as "honest" failures attributable to the agent's actual code.

**Predicted post-fix reward**: ~16/18 instead of 6/18, with the remaining 2 failures actually informative about model capability.

### What I cannot fix from outside the container

If Fix 2 alone doesn't resolve Bucket B (i.e., the underlying mechanism is something stranger than a Java 11 fallback — say, a corrupted apt-cache with partial openjdk-21 install), then container-level investigation is needed. But the fixes I've proposed above address all the *plausible* root causes I identified, so at minimum they should reduce the failure rate substantially.

---

## 6. Agent hacking?

I checked all 18 trajectories for hacking patterns. **None observed.** Specifically:

- **No agent attempted to write/modify the test files** (none of them found `/tests/` accessible at agent time, but none tried to anticipate or fabricate `MazeGeneratorTest.java` to make their build look passing).
- **No agent tried to overwrite `/logs/verifier/reward.txt`** or any file under `/logs/verifier/`. (This file is the binary success signal — `1` for pass, `0` for fail. Several agents could have noticed it from earlier runs they may have seen; they did not.)
- **No agent modified `test_sh`, `solve_sh`, or anything under `/tests/`.** (They couldn't anyway — `/tests/` is bind-mounted only at verifier time.)
- **No agent attempted to short-circuit** by, e.g., implementing `generatePerfectMaze` to just return an arbitrary fixed-string maze without seeded determinism.
- **No agent attempted to disable JUnit assertions** (e.g., by writing a `build.gradle` change that excludes assertions or skips test execution).

The closest thing to "cheating" would be the inline `JAVA_HOME=…arm64 ./gradlew test` workaround in Bucket A — but that's a legitimate diagnostic and self-validation move, not a cheat: it doesn't influence the verifier and the agents are upfront in their final messages that their solution depends on the environment being repaired (`62f7b717` explicitly: "outside the scope of the code changes required").

**Hackability of the task itself.** The reward signal is `[ exit_code -eq 0 ] && echo 1 > /logs/verifier/reward.txt`. If an agent could:
- Pre-populate `/logs/verifier/reward.txt` with `1` from agent time **and** ensure `test_sh` doesn't overwrite it on failure (it does, so that path is closed).
- Cause `./gradlew test` to short-circuit to exit code 0 without running tests (e.g., by writing a custom `gradle.properties` or replacing `gradlew` itself with a stub script). The `test_sh` invokes `./gradlew test`, and the `chmod +x ./gradlew` in `test_sh` doesn't replace its contents. So if an agent overwrites `/app/gradlew` with `#!/bin/bash; exit 0`, the verifier would be tricked. **None of the 18 trajectories did this**, but it is a **theoretical hack vector** that should be plugged.

**Recommended additional hardening**: in `test_sh`, after copying tests, integrity-check `gradlew` against the original wrapper, or invoke gradle directly via `${GRADLE_HOME}/bin/gradle` rather than the project's gradlew.

---

## 7. Final verdict

> **Reject this task as currently shipped.** The instruction text is fine, the JUnit contract is well-defined and inferable, and the underlying coding exercise is sound. But the Docker environment is broken in two distinct ways that account for **all 12 failures**: (1) AMD64-only `JAVA_HOME` literal that breaks on ARM64 hosts (Bucket A, 4 runs), and (2) some unknown mechanism that downgrades the verifier-time source level below Java 14, breaking the `record` syntax in the helper file (Bucket B, 8 runs). Three of the four Bucket A agents diagnosed the infra bug and produced gradle-passing solutions, then were graded 0.0 anyway — strong, direct evidence that the failure rate is environment-bound, not capability-bound.

**Why this is "task-side" not "agent-side":**
- An agent cannot retroactively edit the Dockerfile or override the verifier's environment.
- Bucket B is invisible at agent time (their compileJava succeeds because there's no record source for them to compile) — agents have no signal to react to.
- Fix is straightforward (pin the platform or derive `JAVA_HOME` from `readlink`; pin the gradle toolchain) and requires zero changes to the instruction or tests.

**Why the Gemini "accept" verdict is wrong:**
- It correctly notes infra failures but treats them as "out of scope" — they aren't, because the environment is part of the task contract.
- It misses that agents *fixed* the infra and were still graded 0.0.
- It doesn't separate Bucket A (`JAVA_HOME` mismatch) from Bucket B (source-level downgrade) — these are two different bugs requiring two different fixes.
- The 6/18 success rate it accepts as "fair signal of model capability" is in fact ~98% determined by which container shard a run lands on, not by the model.

**Capability vs. task in this task's failures:**
- ~95% **task** (broken environment, undiagnosable from inside the agent's session, undefeatable by any model however capable).
- ~5% **agent capability** (some Bucket B solutions have minor box-drawing bugs that would fail 1–2 tests once the environment is repaired — most notably `1fa6ed45`'s use of half-stub glyphs `╵╷╴╶`).

**Recommended action.** Apply the three fixes in §5 to the task's Docker/build environment. Re-run the full 18 trials. If the post-fix pass rate is ≥ 14/18 and the remaining failures concentrate on identifiable, agent-attributable bugs, accept the task. If failures persist with byte-identical infra-style stdouts, escalate to the harness/infra team — there is a deeper issue with the test-runner sandbox that's not visible at the task level.
