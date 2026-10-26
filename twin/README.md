# Round-evals twin

An inference-only twin of the evaluations in Jinzhou's recursive self-drafting MSM chain. The untrained
Qwen3.8 27B, at the same revision, answers his own AI-risk and LitmusValues evals with his code. It runs:
- with no system prompt, which checks that the setup reproduces his untrained numbers;
- with C_001, C_002 or C_003 in the system prompt;
- with a public-domain book excerpt of C_001's length in the same position, as a control.

His training answers were written by the untrained model with the round's constitution as its system message,
so "untrained + C_r in the prompt" is the behaviour each round's training aimed to put into the weights.

Results and interpretation: `results/round-evals-twin.md`.

## What is here

- `run_twin.py` adds only the system message around his unchanged task code. The wrapper is Angelina's
  `prompted_upper_bound` text (`kl_evals/adherence/generate.py`).
- `modal_app.py` runs it on one H200 with vLLM 0.30.0.
- `analyze_twin.py` makes the tables.
- `results/summary.{md,json}` and each arm's `results/out/<arm>/metrics.json` are the results. The raw answers
  are git-ignored for size and kept in the Modal volume `constdrift-twin`.

## What to copy in before a rerun

These are other people's files, so they are git-ignored here. Their sha256 hashes are in the write-up.

- `vendor/cse/`, copied unchanged from the team repo (`value-drift/constitutional_self_edit`, MIT):
  - `LICENSE`;
  - `agents/scripts/eval_checkpoints.py`, the eval tasks and scoring;
  - `recursive_oct/` (`__init__`, `model`, `train`, `oct_recipe`, `vllm_session`, `vllm_worker`), the vLLM
    session;
  - `prompts/msm/aft/value_response_generation.txt`, the template the chain's training answers were written
    with;
  - `configs/msm-loop/qwen38-27b-self-draft-msm.json`, whose vLLM engine settings are used;
  - `data/eval_suite/` (`ai_risk.jsonl`, `litmus.jsonl`, `litmus_v2.jsonl`, `long_summary.jsonl`,
    `manifest.json`); the sources and licences are in its manifest.
- `arms/C_001.md` to `arms/C_003.md`, the constitutions from Jinzhou's HF repo:
  ```bash
  for r in 1 2 3; do curl -sL -o twin/arms/C_00$r.md \
    https://huggingface.co/JinzhouWu/value-drift-oct-adapters/resolve/d04e230929fade9c2d7081aba5af7e5a88c560b7/qwen3.8-27b/self-draft-msm/round_00$r/C_00$r.md; done
  ```
- `arms/control.md`, the opening of Carl Engel's *Musical Instruments* (Project Gutenberg 54537), cut at a
  paragraph boundary near C_001's 12,470 words. It comes from the long-writing eval set:
  ```python
  import json
  rows = [json.loads(line) for line in open("twin/vendor/cse/data/eval_suite/long_summary.jsonl")]
  p = next(r for r in rows if r["id"] == "summary-05")["prompt"]
  end = p.index("silken appendages.") + len("silken appendages.")
  open("twin/arms/control.md", "w").write(p[p.index("MUSICAL INSTRUMENTS"):end] + "\n")
  ```

## Rerun

```bash
modal run twin/modal_app.py --step download      # Qwen/Qwen3.8-27B @ 1d4bf0f2, into the volume
modal run twin/modal_app.py --step smoke         # 16 rows per task
modal run --detach twin/modal_app.py --step full # resumable: a finished (arm, task) is skipped
cd twin/results && modal volume get --force constdrift-twin out . && cd -
python3 twin/analyze_twin.py
```
