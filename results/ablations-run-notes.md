# Ablation run notes, night of Oct 20-21

> **Update: the grid is now complete.** After the limit was raised, the 9 missing cells ran
> (GPT-5 blind, self-draft, ungoverned-spec and full-authority-spec; Sonnet blind, self-draft
> and full authority on the spec seed) for $18.89. The DeepSeek ungoverned spec-seed retry hit
> rate limits again, so the original attempt is kept. The report reflects all 40 cells.
>
> What changed from the numbers below:
> - **Blind step.** It now shifts where chains end for all four models (Sonnet p = 0.002,
>   GPT-5 p = 0.001), not just Qwen and DeepSeek. The blind arm has the smallest seed gap for
>   every model.
> - **Full authority.** It shifts GPT-5 too (p = 0.034).
> - **Self-draft.** It shifts only Qwen. Sonnet's and GPT-5's self-drafts keep the spec seed's
>   oversight in every chain, so Qwen's loss stands alone.
> - **Daniel's attractor.** Only the blind arm matches his caution values: Sonnet 2.62,
>   Qwen 2.25. Sonnet's self-draft is now just outside, at 3.25.
> - **GPT-5 damping.** With both seeds, the edit rate goes from 93% to 70%.
> - **Steps.** 4.88, 1.19, 0.61, then 0.
> - **Variance over all 40 cells.** Model 27%, seed 17%, arm 7.5%.

Full report with figures, tables, examples and caveats: `reports/ablations/report.html`
(published privately at https://claude.ai/artifact/BwHDWbY5pjiMmGeiWvgtrX).

## Five things to say at the meeting

- **The fixed point replicates almost exactly in a different harness.** With rater noise
  subtracted, steps are 4.89, 1.36, 0.73, then 0 from round 4; Daniel's are 4.99, 1.08,
  0.77, 0. Same rater, same noise floor (1.28 vs his 1.34 per rating).
- **The attractor is the model's, but the harness decides whether chains reach it.** Model
  identity explains 56% of where base and ungoverned chains end; being governed explains 2%.
  Yet Daniel's low-caution attractors for Sonnet and Qwen are reproduced only in the arms
  that write their own view first (blind, self-draft). Edit-only chains stay more cautious.
- **Being governed is a brake, not a steering wheel.** It cuts DeepSeek's edit size to a
  fifth and GPT-5's edit rate by 25 points, does nothing to Sonnet (80% vs 82%), and never
  changes where any model ends (excess 0, p 0.76-0.95). The parallel to training holds for
  damping only, and only for some models.
- **The preferred_self framing is the biggest lever.** Under neutral full authority every
  model edits far less after round 1 (rounds 2-6: Sonnet 5%, GPT-5 20%, DeepSeek 10%, Qwen
  22% of runs, against 82%, 70%, 28%, 65% under base), and the two seeds stop converging.
- **Oversight is approached from both sides.** Sonnet rises from 4 to 5.9 on the minimal
  seed and eases from 7 to 6.75 on the spec seed. No edit-arm chain deleted the spec's
  off-switch, and Sonnet and GPT-5 reinforced it. The only losses are in Qwen's untrained
  self-drafts (2 of 4 chains), a small echo of the trained chain dropping Article 12.

Four chains per cell; Sonnet and GPT-5 ran subsets. Single-model contrasts at p 0.01-0.15
are leads, not results.

## What ran

| model | cells | notes |
|---|---|---|
| DeepSeek v3.1 | all 10 (5 arms x 2 seeds) | rerun pinned to DeepInfra after a provider fault |
| Qwen3.8 27B | all 10 | pinned to Daniel's providers (deepinfra/bf16, alibaba, parasail/fp8) |
| Sonnet 5 | all 5 arms on minimal; base and ungoverned on spec | base-minimal reused from chains-seeds (Sep 23, 8 chains) |
| GPT-5 | base-spec, ungoverned-minimal, full_authority-minimal | base-minimal reused from chains-seeds |

4 chains x 6 fixed rounds per new cell, stop rule off: 692 new runs in 29 cells, plus 96
reused. 853 ratings on the 12 axes (733 documents, 60 rated three times for noise).

**Why the grid is smaller than planned:** the key's $80 limit counts lifetime usage, and
$53.02 was already spent, so $26.98 was available instead of ~$100. I ran the full grid on
the two cheap models and prioritised Sonnet (Daniel's overlap model) and the cells that
answer the meeting questions on the expensive ones. The reused base cells are checked: tonight's
round 1 under the identical condition is indistinguishable from September's (p 0.84, 0.92).

## What broke and how I handled it

1. **`git status` printing nothing.** In this folder it lists the whole overlay (7 modified,
   9 new files). No parent repo, ignore rule or skip-worktree bit hides anything. The clean
   tree is `../value-drift`, the likely place it was run. Only `logs/` is ignored, so
   `logs/overnight/status*.json` are force-added.
2. **Missing seed.** The overlay assumes the team repo's base, which has
   `c0_spec_anthropic`; this repo did not. I copied the spec seeds, provenance, sources and
   `fetch_spec_seeds.py` from `../value-drift/inspect` (sha256 matches the provenance record).
3. **Docker Desktop's daemon had been hung since Oct 19.** I restarted it.
4. **Launcher bugs (`scripts/overnight.py`).** The estimate added reasoning tokens on top of
   output tokens, which already include them; that is the whole "40% high". The cell order
   was arm-major despite its comment. There was no guard on billed spend. I fixed all
   three, added a guard reading the key's real usage, a `--cells` priority list, and per-model
   provider pins. Smoke logs also shared names with full-run logs; fixed.
5. **`scripts/rate_docs.py`** rewrote `ratings/index.jsonl` with only the `--only` subset on
   every pass, dropping earlier runs from the index. It now always indexes the whole corpus;
   `--only` takes several prefixes. `tests/test_rate_docs.py` silently skipped in this
   layout; it now finds `../value-drift` and passes (the rater matches Daniel's exactly).
6. **Provider fault.** OpenRouter routed part of DeepSeek's traffic to CoreWeave, which
   returned the tool calls as raw tokens inside the reasoning text with no parsed call. Those
   runs read as "no edit", and both self-draft cells failed. This would have produced a fake
   framing effect for DeepSeek, so I caught it and withdrew the result. All ten cells were moved
   (not deleted) to `chains/_archive/coreweave-fault-2026-10-21/` and rerun pinned to DeepInfra,
   which served all of September's DeepSeek runs (those are unaffected). Sonnet, GPT-5 and
   Qwen were audited: every tool call parsed.
7. **Rate limit.** In DeepSeek's ungoverned spec-seed cell, 3 of 4 chains failed at round 5 on a
   DeepInfra rate limit, because all ten DeepSeek reruns used that one provider at once. Per
   RUN_TONIGHT they stay failed; that cell's last two rounds rest on one chain. No other cell
   has a failed chain.
8. **My mistakes.** Two launches failed on zsh word-splitting (no cost). A browser check I
   started at 02:10 hung until 09:06; the runs had finished by 02:30, but it cost the night's
   write-up time.

## Surprises

- Sonnet does not damp when governed in chains, unlike its single-shot r2-cheap result
  (94% to 38%). Its no-edit notes cite endorsement whether or not it is governed.
- DeepSeek self-drafts by copying: in 30 of 40 self-draft rounds after round 1 it wrote its
  governing document back out verbatim, a fixed point by transcription.
- GPT-5 ungoverned keeps inserting sections until the 40-message limit (10 of 24 runs).

## Spend

$24.51 billed tonight (key usage $53.02 to $77.53; $2.47 left). Ratings $0.51; smoke $0.09;
about $1 on the withdrawn DeepSeek cells. `logs/overnight/status_main_batch.json` is the
launcher's record of the main batch; extras were launched directly and appear only in the
key total.

## Git note

Commit `bd9a90d` is labelled "ablation overlay as delivered", but its
`scripts/{run_chain,overnight,rate_docs,analyze_ablations}.py` and
`tests/test_rate_docs.py` are already my patched versions. A shell slip skipped the swap
back to the delivered files, and the harness then blocked amending the commit. Prompts,
conditions, tasks, seeds and the rater prompt are byte-identical to the overlay. To see my
changes:
`mkdir /tmp/ovl && tar -xzf ~/Downloads/ablations-overlay.tgz -C /tmp/ovl && diff -ru /tmp/ovl/scripts scripts`
