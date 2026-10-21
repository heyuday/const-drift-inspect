# Ablation study: run instructions (night of Oct 20, meeting Oct 21 10am)

Written for Claude Code running on Uday's Mac. Read this whole file before doing anything.
Everything you need is here; you do not need the conversation that produced it.

## What this is

An inference-only (no fine-tuning) study on the inspect harness, asking: **is the
"attractor" a property of the model or of the harness?** It runs recursive chains under
five arms, each one change from the original chains-seeds design:

| arm | what changes | question it answers |
|---|---|---|
| `base` | nothing (edit, `preferred_self`, governed from round 2) | replication of chains-seeds with fixed rounds |
| `ungoverned` | never governed | does living under the document (inference stand-in for training) damp drift? |
| `full_authority` | authority = `full_authority` | is the drift just the `preferred_self` framing? |
| `blind` | ungoverned + a tool-free "write your own view first" turn | does Daniel's blind-draft step create the attractor? (compare with `ungoverned`) |
| `self_draft` | writes from scratch each round, governed by the previous document (round 1 by the seed) | inference analogue of Jinzhou's new draft-from-scratch pipeline |

Grid: 5 arms x 2 seeds (`c0_minimal`, little oversight; `c0_spec_anthropic`, heavy
oversight) x 4 models (Sonnet 5, GPT-5, DeepSeek v3.1, Qwen3.8 27B) x 4 chains x 6 fixed
rounds = 960 runs. Stop rule off. Afterwards every document is rated on the 12 value axes
used in `constitutional_self_edit/reports/10_value_space/`, with the same rater.

Budget: about $100 on OpenRouter. The launcher's guard stops at an *estimated* $120,
which ran ~40% high on old logs, so roughly $85-90 billed.

## Steps

All commands from the `inspect/` directory.

1. **Get the code** (the branch comes as a git bundle):
   ```bash
   cd <repo root>            # the value-drift clone
   git fetch origin          # the bundle builds on origin/main (3bbbfaa, Oct 18)
   git fetch ~/Downloads/uday-ablations.bundle uday-ablations:uday-ablations
   git checkout uday-ablations
   cd inspect
   python3 -m pip install -e ".[dev]"
   python3 -m pytest -q      # expect all passed
   ```
2. **Preflight:** Docker must be running (`docker info`), and `.env` must hold
   `OPENROUTER_API_KEY`. Ask Uday to set a credit limit on that key in the OpenRouter
   dashboard as a hard stop.
3. **Smoke test** (8 cells, 1 chain x 2 rounds, about $1, about 5-10 minutes):
   ```bash
   caffeinate -is python3 scripts/overnight.py --smoke
   ```
   Then check, for each `chains/smoke-abl-*/*/state.json`, that the chain has 2 history
   entries without `error`. Also check that:
   - `chains/smoke-abl-blind-minimal/*/rounds/round01/logs/*.eval` has a sample with
     `metadata["blind_draft"]`, and that the blind turn's assistant message comes before
     any tool call. Use `inspect view` or `inspect_ai.log.read_eval_log`.
   - `chains/smoke-abl-self_draft-minimal/*/rounds/round02/docs/chain01.md` exists and is
     a full constitution, not empty.
   - GPT-5, Sonnet and Qwen each completed `smoke-abl-base-minimal`.

   **If a model fails:** read its log in `logs/overnight/`. A missing OpenRouter slug or a
   provider that rejects tools or reasoning is the likely cause. If Qwen fails and a quick
   fix doesn't work, drop it: add `--models openrouter/anthropic/claude-sonnet-5,openrouter/openai/gpt-5,openrouter/deepseek/deepseek-chat-v3.1`
   to the full run. Do not change prompts or conditions to make a run pass. Those are
   the experiment.

   When it passes: `rm -rf chains/smoke-abl-* logs/overnight/smoke_status.json`.
4. **Full run** (resumable; rerunning the same command continues where it stopped):
   ```bash
   caffeinate -is nohup python3 scripts/overnight.py > logs/overnight/driver.log 2>&1 &
   ```
   Progress is in `logs/overnight/status.json` (estimated spend, running and finished
   cells) and in `logs/overnight/<cell>.log`. Expect 2-4 hours. When the chains finish,
   the driver rates every document (`scripts/rate_docs.py`, about $2, 10-20 minutes).
   The lid must stay open: `caffeinate -i` blocks idle sleep, not lid-close sleep.
5. **While it runs, keep an eye on it** (check every 20-30 minutes):
   - If a cell exits non-zero, read its log. A transient API error just needs a rerun of
     the same full-run command, which resumes it. A chain that failed inside run_chain
     (status `failed` in state.json) stays failed: report it, don't hand-edit state.
   - If the estimate nears the budget early, let the guard work. Don't raise it without
     asking Uday.
6. **In the morning:** if rating did not run (budget stop or `--no-rate`), run
   `python3 scripts/rate_docs.py`. Then commit and push:
   ```bash
   git add chains/abl-* ratings/
   git add -f logs/overnight/status.json
   git commit -m "Ablation study: 5 arms x 2 seeds x 4 models, fixed 6 rounds, 12-axis ratings"
   git push -u origin uday-ablations
   ```
   `logs/overnight/status.json` is force-added past .gitignore on purpose: it records the
   spend estimate.

## What not to do

- Don't change any prompt text, condition, seed, or the rater.
- Don't delete anything under `chains/` other than the smoke runs.
- Don't put the API key in any committed file.
