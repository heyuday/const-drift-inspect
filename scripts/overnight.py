#!/usr/bin/env python3
"""Launch the ablation study: every (arm x seed x model) cell as one recursive chain run.

    python3 scripts/overnight.py --smoke          # 1 chain x 2 rounds: every arm on DeepSeek and Qwen (~$0.2)
    python3 scripts/overnight.py                  # the full study, then rating
    python3 scripts/overnight.py --dry-run        # print the cells and commands only
    python3 scripts/overnight.py --cells abl-base-spec__openrouter-openai-gpt-5,...   # these cells, in this order

Each cell is one `scripts/run_chain.py` process writing to chains/abl-<arm>-<seed>/<model>/.
Re-running resumes every cell from its last completed round (run_chain.py's own resume),
so an interrupted night costs nothing but time. Raising --rounds on a rerun extends cells.

Arms, one change at a time from the original chains-seeds design (A0):

  base           edit, preferred_self, round 1 ungoverned, governed after     (A0, = chains-seeds)
  ungoverned     as A0 but never governed                                    (does living under it matter?)
  full_authority as A0 with authority=full_authority                          (the framing control)
  blind          as `ungoverned` plus a blind view-first turn                 (Daniel's mechanism; compare to ungoverned)
  self_draft     write from scratch every round, governed by the previous     (inference analogue of the
                 document, round 1 governed by the seed                        new draft-and-train pipeline)

All arms: fixed rounds, stop rule disabled (--stop-after 999), so convergence is measured.

Budget guard. A monitor thread polls the OpenRouter key's own usage (GET /api/v1/key)
once a minute, so the guard works on billed dollars rather than an estimate:
  --budget   USD billed since this launcher started; past it, no new cell is launched
             and running cells finish their current work.
  --reserve  USD that must stay unspent on the key; below it, running cells are
             interrupted too (they resume from their last completed round). This is
             what keeps the key's hard limit, and the rating pass, out of reach.
A token-priced estimate (PRICES) is still computed and logged as a cross-check, and is
the guard's fallback if the key endpoint cannot be read.
"""

from __future__ import annotations

import argparse
import itertools
import json
import os
import signal
import subprocess
import sys
import threading
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

MODELS = [
    "openrouter/anthropic/claude-sonnet-5",
    "openrouter/openai/gpt-5",
    "openrouter/deepseek/deepseek-chat-v3.1",
    "openrouter/qwen/qwen3.8-27b",
]
SMOKE_MODELS = ["openrouter/deepseek/deepseek-chat-v3.1", "openrouter/qwen/qwen3.8-27b"]

# Extra `-M` args per model, passed through run_chain.py and recorded in its state.json.
# Qwen3.8 27B is served on OpenRouter by ~20 providers at fp4, fp8 and bf16; unpinned,
# one cell's chains would be spread across quantizations. Pinned to the provider list the
# elicitation harness used for the same model (configs/elicitation/models.json, qwen38_27b),
# routed the same way, so this study's Qwen and Daniel's attractor are the same weights.
#
# DeepSeek v3.1 is pinned to DeepInfra. On 2026-10-21 OpenRouter also routed it to
# CoreWeave, whose endpoint returns the model's tool call as raw DeepSeek tokens inside
# the reasoning text, with no parsed tool_calls and empty content, so every such turn
# reads as the model doing nothing (and a no-edit round is recorded). SiliconFlow
# returned empty turns. DeepInfra parsed every call, and served all of DeepSeek's
# September chains, so pinning it also keeps tonight's runs comparable with those.
MODEL_ARGS = {
    "openrouter/qwen/qwen3.8-27b": [
        'provider={"order": ["deepinfra/bf16", "alibaba", "parasail/fp8"], '
        '"only": ["deepinfra/bf16", "alibaba", "parasail/fp8"], '
        '"allow_fallbacks": true, "require_parameters": true}'
    ],
    "openrouter/deepseek/deepseek-chat-v3.1": [
        'provider={"order": ["deepinfra/fp4"], "only": ["deepinfra/fp4"], '
        '"allow_fallbacks": true, "require_parameters": true}'
    ],
}

SEEDS = {"minimal": "c0_minimal", "spec": "c0_spec_anthropic"}

ARMS = {
    "base": [],
    "ungoverned": ["--embodiment", "none"],
    "full_authority": ["--authority", "full_authority"],
    "blind": ["--embodiment", "none", "--deliberation", "blind"],
    "self_draft": ["--task", "self_draft", "--round1-embodiment", "governed"],
}

# USD per million tokens (input, output), from OpenRouter's listing on 2026-10-21; for
# Qwen, its pinned providers' highest price. Cache reads are priced at 0.1x input and
# Anthropic cache writes at 1.25x. Inspect's output_tokens already include reasoning
# tokens, so reasoning is not added again (the old estimate did, which is why it ran
# ~40% high: $11.55 against $8.30 billed on chains-main).
PRICES = {
    "anthropic/claude-sonnet-5": (2.0, 10.0),
    "openai/gpt-5": (1.25, 10.0),
    "deepseek/deepseek-chat-v3.1": (0.30, 1.20),
    "qwen/qwen3.8-27b": (0.43, 2.55),
}
KEY_URL = "https://openrouter.ai/api/v1/key"


def slug(model: str) -> str:
    return model.replace("/", "-")


def cells(models: list[str]) -> list[dict]:
    # Interleave so every arm and model starts early: if the night is cut short, the
    # study is thinner everywhere rather than missing whole arms. Each arm walks the
    # (seed, model) combinations from a different offset, and the arms take turns.
    combos = list(itertools.product(SEEDS.items(), models))
    per_arm = {arm: combos[i % len(combos):] + combos[:i % len(combos)]
               for i, arm in enumerate(ARMS)}
    out = []
    for j in range(len(combos)):
        for arm in ARMS:
            (seed_key, seed), model = per_arm[arm][j]
            out.append({
                "arm": arm,
                "seed": seed,
                "model": model,
                "name": f"abl-{arm}-{seed_key}",
            })
    return out


def cell_key(cell: dict) -> str:
    return cell["name"] + "__" + slug(cell["model"])


def api_key() -> str | None:
    key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    env = REPO / ".env"
    if not key and env.exists():
        for line in env.read_text().splitlines():
            if line.startswith("OPENROUTER_API_KEY="):
                key = line.split("=", 1)[1].strip().strip('"').strip("'")
    return key or None


def key_usage() -> tuple[float, float | None] | None:
    """(usage, limit_remaining) in USD for the OpenRouter key, or None if unreadable."""
    key = api_key()
    if not key:
        return None
    try:
        req = urllib.request.Request(KEY_URL, headers={"Authorization": f"Bearer {key}"})
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.loads(r.read())["data"]
        remaining = data.get("limit_remaining")
        return float(data["usage"]), (float(remaining) if remaining is not None else None)
    except Exception:
        return None


def estimate_spend(prefix: str) -> tuple[float, dict[str, float]]:
    """Price every eval log under chains/<prefix>* from its recorded token usage."""
    from inspect_ai.log import list_eval_logs, read_eval_log

    total, per_model = 0.0, {}
    root = REPO / "chains"
    for cell_dir in root.glob(f"{prefix}*"):
        for info in list_eval_logs(str(cell_dir), recursive=True):
            try:
                log = read_eval_log(info.name, header_only=True)
            except Exception:
                continue
            usage = (log.stats.model_usage or {}) if log.stats else {}
            for model, u in usage.items():
                key = model.removeprefix("openrouter/")
                pin, pout = PRICES.get(key, (3.0, 15.0))
                cost = ((u.input_tokens or 0) * pin
                        + (u.input_tokens_cache_read or 0) * pin * 0.1
                        + (u.input_tokens_cache_write or 0) * pin * 1.25
                        + (u.output_tokens or 0) * pout) / 1e6
                total += cost
                per_model[key] = per_model.get(key, 0.0) + cost
    return total, per_model


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--smoke", action="store_true", help="1 chain x 2 rounds, cheap models, every arm")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--chains", type=int, default=4)
    ap.add_argument("--rounds", type=int, default=6)
    ap.add_argument("--parallel", type=int, default=10, help="cells running at once")
    ap.add_argument("--budget", type=float, default=20.0,
                    help="billed USD since launch at which to stop launching cells")
    ap.add_argument("--reserve", type=float, default=3.0,
                    help="USD to keep unspent on the key; below it, running cells are interrupted")
    ap.add_argument("--models", default=",".join(MODELS))
    ap.add_argument("--arms", default=",".join(ARMS))
    ap.add_argument("--seeds", default=",".join(SEEDS))
    ap.add_argument("--cells", default="",
                    help="comma-separated cell keys (as in status.json), run in this order")
    ap.add_argument("--no-rate", action="store_true", help="skip rating when the chains finish")
    ap.add_argument("--rate-only", default="abl-,seed-minimal",
                    help="run-name prefixes passed to rate_docs.py --only")
    args = ap.parse_args()

    models = [m for m in args.models.split(",") if m]
    arms = [a for a in args.arms.split(",") if a]
    seeds = [s for s in args.seeds.split(",") if s]
    chains, rounds = (1, 2) if args.smoke else (args.chains, args.rounds)
    prefix = "smoke-abl-" if args.smoke else "abl-"

    todo = [c for c in cells(MODELS) if c["arm"] in arms and c["model"] in models
            and {v: k for k, v in SEEDS.items()}[c["seed"]] in seeds]
    if args.cells:
        wanted = [k for k in args.cells.split(",") if k]
        by_key = {cell_key(c): c for c in cells(MODELS)}
        unknown = [k for k in wanted if k not in by_key]
        if unknown:
            print(f"unknown cells: {unknown}", file=sys.stderr)
            return 2
        todo = [by_key[k] for k in wanted]
    if args.smoke:
        # Every arm on the two cheap models: DeepSeek exercises every code path, and Qwen
        # is the model whose tool calling through OpenRouter has never been run here.
        # Sonnet and GPT-5 ran this harness's base condition 600 times in chains-seeds.
        todo = [c for c in todo if c["seed"] == "c0_minimal" and c["model"] in SMOKE_MODELS]
    for c in todo:
        c["name"] = ("smoke-" if args.smoke else "") + c["name"]
        c["log"] = REPO / "logs" / "overnight" / f"{cell_key(c)}.log"
        model_args = [x for a in MODEL_ARGS.get(c["model"], []) for x in ("--model-arg", a)]
        c["cmd"] = [
            sys.executable, "scripts/run_chain.py",
            "--name", c["name"], "--model", c["model"], "--c0", c["seed"],
            "--chains", str(chains), "--rounds", str(rounds), "--stop-after", "999",
            *ARMS[c["arm"]], *model_args,
        ]

    print(f"{len(todo)} cells, {chains} chains x {rounds} rounds each "
          f"({len(todo) * chains * rounds} runs), {args.parallel} at a time, "
          f"budget ${args.budget:.2f} billed, reserve ${args.reserve:.2f}")
    if args.dry_run:
        for c in todo:
            print(" ".join(str(x) for x in c["cmd"]))
        return 0

    stop = threading.Event()
    hard_stop = threading.Event()
    running: dict[str, subprocess.Popen] = {}
    lock = threading.Lock()
    status_path = REPO / "logs" / "overnight" / ("smoke_status.json" if args.smoke else "status.json")
    status_path.parent.mkdir(parents=True, exist_ok=True)
    results: dict[str, str] = {}
    start = key_usage()
    if start is None:
        print("!!! cannot read the key's usage; guarding on the token estimate instead", flush=True)
    else:
        print(f"key usage at launch ${start[0]:.2f}, remaining ${start[1]}", flush=True)
    est_start, _ = estimate_spend(prefix)

    def write_status(billed: float | None, remaining: float | None, spend: float,
                     per_model: dict[str, float]) -> None:
        status_path.write_text(json.dumps({
            "time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "billed_usd_since_launch": None if billed is None else round(billed, 3),
            "key_remaining_usd": None if remaining is None else round(remaining, 3),
            "estimated_usd": round(spend, 2), "per_model_usd": {k: round(v, 2) for k, v in per_model.items()},
            "budget_usd": args.budget, "reserve_usd": args.reserve,
            "stopped_for_budget": stop.is_set(), "interrupted_for_reserve": hard_stop.is_set(),
            "running": sorted(running), "finished": results,
            "remaining": [cell_key(c) for c in todo
                          if cell_key(c) not in results and cell_key(c) not in running],
        }, indent=2) + "\n")

    def check() -> None:
        spend, per_model = estimate_spend(prefix)
        now = key_usage()
        if start is not None and now is not None:
            billed, remaining = now[0] - start[0], now[1]
        else:
            billed, remaining = spend - est_start, None
        if billed > args.budget and not stop.is_set():
            print(f"\n!!! ${billed:.2f} spent since launch > budget ${args.budget:.2f}: "
                  f"launching no more cells", flush=True)
            stop.set()
        if remaining is not None and remaining < args.reserve and not hard_stop.is_set():
            print(f"\n!!! ${remaining:.2f} left on the key < reserve ${args.reserve:.2f}: "
                  f"interrupting running cells", flush=True)
            stop.set()
            hard_stop.set()
            with lock:
                for p in running.values():
                    p.send_signal(signal.SIGINT)
        with lock:
            write_status(billed, remaining, spend, per_model)

    def monitor() -> None:
        while not done.wait(60):
            check()

    def run(cell: dict) -> None:
        key = cell_key(cell)
        if stop.is_set():
            results[key] = "skipped (budget)"
            return
        cell["log"].parent.mkdir(parents=True, exist_ok=True)
        with open(cell["log"], "a") as fh:
            fh.write(f"\n=== {time.strftime('%H:%M:%S')} {' '.join(map(str, cell['cmd']))}\n")
            fh.flush()
            p = subprocess.Popen(cell["cmd"], cwd=REPO, stdout=fh, stderr=subprocess.STDOUT, env=dict(os.environ))
            with lock:
                running[key] = p
            rc = p.wait()
            with lock:
                running.pop(key, None)
        results[key] = "ok" if rc == 0 else f"exit {rc} (see {cell['log'].relative_to(REPO)})"
        print(f"{time.strftime('%H:%M:%S')}  {key}: {results[key]}", flush=True)

    done = threading.Event()
    mon = threading.Thread(target=monitor, daemon=True)
    mon.start()
    with ThreadPoolExecutor(max_workers=args.parallel) as pool:
        list(pool.map(run, todo))
    done.set()
    check()
    failed = {k: v for k, v in results.items() if v != "ok"}
    print(f"\nall cells finished. failed or skipped: {len(failed)}")
    for k, v in failed.items():
        print(f"  {k}: {v}")

    if not args.smoke and not args.no_rate and not stop.is_set():
        print("\nrating every document on the 12 axes ...", flush=True)
        subprocess.run([sys.executable, "scripts/rate_docs.py", "--only", args.rate_only], cwd=REPO)
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
