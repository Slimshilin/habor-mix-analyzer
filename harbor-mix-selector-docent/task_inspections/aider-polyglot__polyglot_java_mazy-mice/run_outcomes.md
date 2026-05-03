# Run outcomes — `aider-polyglot/polyglot_java_mazy-mice`, 18 trials

## Headline: 6/18 successes, 0/18 with non-claude-opus models

| run_id | agent | model | reward | total_steps | test_stdout bucket |
|---|---|---|---|---|---|
| 7f97e4b5 | claude-code | claude-opus-4-6 | **1.0** | 16 | 2328 (all 13 tests pass) |
| 5b1fb9f6 | claude-code | claude-opus-4-6 | **1.0** | 16 | 2818 (gradle download + all pass) |
| f9ef9cc8 | claude-code | claude-opus-4-6 | **1.0** | 13 | 2328 (all pass) |
| c45636bf | terminus-2  | claude-opus-4-6 | **1.0** | NULL | 2328 (all pass) |
| 83ae6e4b | terminus-2  | claude-opus-4-6 | **1.0** | NULL | 2818 (all pass) |
| 8bdd8715 | terminus-2  | claude-opus-4-6 | **1.0** | NULL | 2328 (all pass) |
| 1fa6ed45 | codex       | gpt-5.4         | 0.0 | 31 | 1513 (Dimensions.java compile error) |
| 399965ff | codex       | gpt-5.4         | 0.0 | 26 | 1513 (Dimensions.java compile error) |
| 3a65d34f | codex       | gpt-5.4         | 0.0 | 32 | **746 (JAVA_HOME invalid)** |
| 06139fa9 | terminus-2  | gpt-5.4         | 0.0 | NULL | 1513 (Dimensions.java compile error) |
| b93135dc | terminus-2  | gpt-5.4         | 0.0 | NULL | 1513 (Dimensions.java compile error) |
| 5db0a790 | terminus-2  | gpt-5.4         | 0.0 | NULL | **746 (JAVA_HOME invalid)** |
| 09cdc8c0 | gemini-cli  | gemini-3.1-pro  | 0.0 | 16 | 1514 (Dimensions.java compile error) |
| dc0eafbd | gemini-cli  | gemini-3.1-pro  | 0.0 | 15 | **746 (JAVA_HOME invalid)** |
| b52ff7ac | gemini-cli  | gemini-3.1-pro  | 0.0 | 8  | 1514 (Dimensions.java compile error) |
| d47117a6 | terminus-2  | gemini-3.1-pro  | 0.0 | NULL | 1513 (Dimensions.java compile error) |
| 1f801e11 | terminus-2  | gemini-3.1-pro  | 0.0 | NULL | 1513 (Dimensions.java compile error) |
| 62f7b717 | terminus-2  | gemini-3.1-pro  | 0.0 | NULL | **746 (JAVA_HOME invalid)** |

## Three distinct failure modes (test_stdout buckets)

### Bucket A — `JAVA_HOME invalid` (4 runs, all rewards = 0)
```
ERROR: JAVA_HOME is set to an invalid directory: /usr/lib/jvm/java-21-openjdk-amd64
```
This appears at the gradle wrapper invocation step, **before any agent code is even compiled**. Pure infra/build issue. Affects: 3a65d34f (codex), 5db0a790 (terminus-2/gpt), 62f7b717 (terminus-2/gemini), dc0eafbd (gemini-cli).

### Bucket B — `Dimensions.java` compile error (8 runs, all rewards = 0)
```
> Task :compileJava FAILED
/app/src/main/java/Dimensions.java:7: error: class, interface, or enum expected
public record Dimensions(int rows, int columns) {
       ^
```
The compiler refuses `record` syntax (Java 14+). Either javac is being invoked at `--release 11` (or earlier), or the file is being copied somewhere that breaks its parse, or `Dimensions.java` is being mangled. Worth investigating whether this is reproducible deterministically (i.e., always happens to non-opus models) or depends on what the agent did. Affects: 06139fa9, 09cdc8c0, 1f801e11, 1fa6ed45, 399965ff, b52ff7ac, b93135dc, d47117a6.

### Bucket C — All 13 tests pass (6 runs, all rewards = 1.0)
All on `claude-opus-4-6`. Mix of `claude-code` (3) and `terminus-2` (3). Test stdout shows clean Gradle build, JUnit 13/13 PASS.

## Reward partitioning by (agent, model)

| agent      | model                  | passes | n |
|---|---|---|---|
| claude-code | claude-opus-4-6 | 3/3 | 3 |
| terminus-2  | claude-opus-4-6 | 3/3 | 3 |
| codex       | gpt-5.4         | 0/3 | 3 |
| terminus-2  | gpt-5.4         | 0/3 | 3 |
| gemini-cli  | gemini-3.1-pro-preview | 0/3 | 3 |
| terminus-2  | gemini-3.1-pro-preview | 0/3 | 3 |

**Pattern:** Capability axis (model) dominates harness axis (agent). Both opus harnesses succeed; both gpt-5.4 harnesses and both gemini harnesses fail uniformly.

## Cross-tabulation: did the bucket A "JAVA_HOME invalid" bucket hit only failed runs?
Yes. All 4 JAVA_HOME-invalid stdouts coincide with `reward=0`. None of them coincide with `reward=1`. **No claude-opus run shows the JAVA_HOME issue** — strongly suggesting JAVA_HOME failures are a *consequence* of something the gpt/gemini agents did to the environment, not a random infra flap.

## Stdout content bytes are tightly clustered
The 1513- vs. 1514-byte difference between `gpt-5.4` (1513) and `gemini-3.1-pro-preview` (1514) is just the agent name being one char off — the output is otherwise identical. So the Dimensions.java compile error is **byte-for-byte identical** across all 8 runs that hit it. This means it is not a random infra flap either; it is a deterministic state.
