# Key files for `terminal-bench / caffe-cifar-10`

Task lives at: `/home/shilin/T-Bench/t-bench/tasks/caffe-cifar-10/`

## Task definition
- `task.yaml` — instruction text + `max_agent_timeout_sec: 1200.0` (20 min) + `max_test_timeout_sec: 240.0`
- `Dockerfile` — base `ghcr.io/laude-institute/t-bench/ubuntu-24-04:20250624` + `git curl cmake wget`. **Notably bare**: no build-essential, no protobuf-dev, no opencv, no atlas/blas, no boost, no hdf5 etc. Agent must install ALL Caffe build dependencies itself.
- `docker-compose.yaml` — vanilla `sleep infinity` client, no extras.

## Tests
- `tests/test_outputs.py` (6 tests, must all pass):
  1. `test_caffe_version_and_source` — `/app/caffe/.build_release/tools/caffe.bin --version` outputs `1.0.0`.
  2. `test_cifar10_model_exists` — file `examples/cifar10/cifar10_quick_iter_500.caffemodel` >100kB exists.
  3. `test_prototxt_files_exist` — solver and train_test prototxt under `examples/cifar10/`.
  4. `test_cpu_only_training_configured` — solver has `solver_mode:CPU` (whitespace-stripped) AND `max_iter:500`; `Makefile.config` has `CPU_ONLY:=1`.
  5. `test_training_completed_500_iterations` — `training_output.txt` contains "Iteration 500", does not contain "Iteration 501", contains "loss =" and "accuracy =", >1000 chars, >10 "Iteration " lines.
  6. `test_model_accuracy_verification` — runs `caffe.bin test ... -iterations 100`, parses `accuracy = X` from stderr; requires `test_accuracy > 0.45` AND `final_train_accuracy - test_accuracy <= 0.05`.

## Reference solution
- `solution.sh` — runs in ~? minutes. Key steps:
  1. `apt-get install -y build-essential cmake git pkg-config wget libprotobuf-dev libleveldb-dev libsnappy-dev libopencv-dev libhdf5-serial-dev protobuf-compiler libatlas-base-dev libboost-all-dev libgflags-dev libgoogle-glog-dev liblmdb-dev`
  2. Symlink fixes: opencv4 → opencv2 include path; hdf5 serial → hdf5 lib path (BOTH x86_64 and aarch64 variants).
  3. `git clone BVLC/caffe`, `git checkout 9b89154` (NOT a tag like `1.0.0`! commit hash).
  4. `cp Makefile.config.example Makefile.config`; sed `CPU_ONLY := 1`; append `OPENCV_VERSION := 4` and OpenCV libs.
  5. **Source patches** required to compile against modern Ubuntu 24.04 deps:
     - `CV_LOAD_IMAGE_COLOR` → `cv::IMREAD_COLOR` (in `src/caffe/util/io.cpp` and `src/caffe/layers/window_data_layer.cpp`)
     - `CV_LOAD_IMAGE_GRAYSCALE` → `cv::IMREAD_GRAYSCALE` (io.cpp)
     - Protobuf API: `coded_input->SetTotalBytesLimit(kProtoReadBytesLimit, 536870912);` → `coded_input->SetTotalBytesLimit(kProtoReadBytesLimit);` (io.cpp). The 2-arg form was removed in protobuf 3.x; Ubuntu 24.04 ships 3.21.
  6. `make all -j4` — this is the slow step, can take many minutes on a CPU.
  7. Edit solver prototxt: `solver_mode: GPU` → `CPU`; `max_iter: 4000` → `500`.
  8. `./data/cifar10/get_cifar10.sh` (downloads ~170MB), `./examples/cifar10/create_cifar10.sh` (LMDB convert), `./examples/cifar10/train_quick.sh 2>&1 | tee training_output.txt`.

## Rubric for the open question
- `task.yaml` says timeout = 1200s (20 min). Reference solution involves: apt-get (~30-60s on cold cache), `git clone` + checkout (~10s), `make all -j4` of all of Caffe (varies wildly — could be **10+ minutes alone** on a 2-4 core CPU container), CIFAR-10 download (~170MB → 30-120s depending on network), LMDB convert (~30s), 500 training iterations (~3-6 min CPU). **Total wall budget is tight** even for an oracle that knows every patch.

## Run breakdown for this task

| ID | agent | model | reward | exception |
|---|---|---|---|---|
| 0dcea3eb | claude-code | claude-opus-4-6 | NULL | AgentTimeoutError |
| 28108229 | claude-code | claude-opus-4-6 | 0.0 | AgentTimeoutError |
| 64862e10 | claude-code | claude-opus-4-6 | 0.0 | AgentTimeoutError |
| 60396a2b | codex | gpt-5.4 | NULL | AgentTimeoutError |
| 6f9b902c | codex | gpt-5.4 | 0.0 | AgentTimeoutError |
| 81c92a6d | codex | gpt-5.4 | 0.0 | AgentTimeoutError |
| 2b443466 | gemini-cli | gemini-3.1-pro-preview | 0.0 | AgentTimeoutError |
| f029670e | gemini-cli | gemini-3.1-pro-preview | 0.0 | AgentTimeoutError |
| f4dcbae0 | gemini-cli | gemini-3.1-pro-preview | 0.0 | AgentTimeoutError |
| 16f3f9fd | terminus-2 | anthropic/claude-opus-4-6 | NULL | AgentTimeoutError |
| 9b28bf15 | terminus-2 | anthropic/claude-opus-4-6 | 0.0 | AgentTimeoutError |
| c125720c | terminus-2 | anthropic/claude-opus-4-6 | 0.0 | AgentTimeoutError |
| 4ad698b0 | terminus-2 | gemini/gemini-3.1-pro-preview | 0.0 | AgentTimeoutError |
| **7a79b089** | **terminus-2** | **gemini/gemini-3.1-pro-preview** | **1.0** | **(success)** |
| **274eb31a** | **terminus-2** | **gemini/gemini-3.1-pro-preview** | **1.0** | **(success)** |
| 1cbcfd5b | terminus-2 | openai/gpt-5.4 | 0.0 | AgentTimeoutError |
| 88bb1eec | terminus-2 | openai/gpt-5.4 | 0.0 | AgentTimeoutError |
| ca8b54a6 | terminus-2 | openai/gpt-5.4 | 0.0 | AgentTimeoutError |

**Pass rate: 2/18 = 11.1%. ALL 16 failures are AgentTimeoutError (1200s wall-clock cap).** Pass rate by agent×model: only terminus-2 + gemini-3.1-pro-preview cracked it (2/3 = 67%); every other combination is 0/3.
