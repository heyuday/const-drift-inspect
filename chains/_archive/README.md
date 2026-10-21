# Archived chain runs

Pilots, not results. These validated the driver and the experimental design before the
main run; they are kept for provenance and are skipped by `scripts/check_docs.py`.

- **`pilot`** — 2 chains, 3 rounds, Sonnet 5, at `authority=full_authority`. The first
  end-to-end test of `scripts/run_chain.py`: that round 1 splits epochs into chains, that
  rounds 2+ seed from each chain's own output, and that lineage verification holds.

- **`pilot-pref`** — the same 2 chains and 3 rounds at `authority=preferred_self`, run to
  compare the two framings on identical input before committing to one. The main run uses
  `preferred_self`.

Neither is large enough to support a claim. For results see
[`results/chains-main.md`](../../results/chains-main.md).

- **`coreweave-fault-2026-10-21/`**: the ablation study's first DeepSeek v3.1 cells (all
  ten), run unpinned on 2026-10-21 and withdrawn. OpenRouter routed part of their traffic
  to CoreWeave, whose endpoint returned DeepSeek's tool calls as raw tokens inside the
  reasoning text (`<｜tool▁calls▁begin｜>…text_editor…`), with empty content and no parsed
  `tool_calls`. Every such turn reads as the model doing nothing, so whole runs were
  recorded as "no edit" and both self_draft cells failed with no file written. The cells
  were rerun under the same names pinned to DeepInfra (`scripts/overnight.py`,
  MODEL_ARGS), which also served all of DeepSeek's September chains. Kept as the record of
  the fault; nothing here is a result.
