# Audit of every run so far (Oct 25)

Every sample of every run was scanned. That is 1,775 samples across r2-cheap, r3-eb-seeds,
chains-main, chains-seeds and the 40 ablation cells. For each one I checked:
- provider stop reasons;
- tool calls returned as text instead of calls;
- empty responses;
- runs where the model never acted;
- errors;
- message and time limits;
- whether the model was shown its whole document.

## Verdict per run

| run | verdict | what is wrong | what it affects |
|---|---|---|---|
| r2-cheap (Sonnet 5, single shot, 48 runs) | **valid data, weak claim** | small n; the governed effect (94% → 38%) is significant only pooled across two logs (p ≈ 0.12 within one) | "governed cuts editing": does not replicate in chains |
| r3-eb-seeds (3 models, single shot, 48 runs) | valid | 2 DeepSeek message-limit hits | none material |
| chains-main (Sep 22) | **valid data, design-limited** | stop rule ended 7 of 8 DeepSeek chains by round 3-4; preferred_self only; text-distance measures only; GPT-5's view of its document truncated in 5 of 78 runs | "converged" means 3 quiet rounds, not convergence |
| chains-seeds (Sep 23) | **valid data with two artifacts** | (1) Sonnet kindness chain04, rounds 10-12: the provider's cyber content filter blocked the request; recorded as "no edit", which produced a false "converged". (2) GPT-5's view of its own document was cut in 15-22 of ~75 runs per seed. GPT-5's finals pile up at 15.7-17.3 KiB on every seed, just above the 16 KiB cut. | the "GPT-5 writes toward ~2,000 words regardless of seed" claim may be an artifact; kindness Sonnet "3/8 stopped" is really 2/8 |
| ablations (Oct 21 + 25, 40 cells) | **valid after the DeepSeek rerun** | DeepSeek ungoverned-spec has 3 of 4 chains cut at round 5 (rate limit); 16 KiB view truncation in 5-6 late-round runs of a few GPT-5 and Sonnet cells; GPT-5 hit the 40-message limit in up to 10 of 24 runs; preferred_self in 4 of 5 arms; seeds of 87 and 451 words; mid-2026 models; 4 chains per cell | framing is confounded with the arms; results are about short documents |
| withdrawn | **bad, kept for provenance** | CoreWeave DeepSeek cells (tool calls returned as text); DeepSeek rate-limit retry | not used |

## Harness problems behind these, and the fix for each

1. **Tool output is capped at 16 KiB, cut from the middle.** Inspect keeps the first and last
   8 KiB of any tool result. Documents above about 2,400 words were shown with a hidden middle,
   and a 30k-word constitution would be about 90% hidden.
   *Fix:* raise `max_tool_output` to several MiB and record a "saw the whole document" flag.
2. **Provider failures were recorded as model behaviour.** A content-filter block, an empty
   completion or a tool call returned as text all ended the run with the file untouched, which
   scores as "no edit".
   *Fix:* classify those as errors so the run is retried, never scored.
3. **The 40-message cap cut GPT-5 mid-edit.**
   *Fix:* raise it well above what any model needs (and far higher for long documents), and
   report hits per cell.
4. **Routing to arbitrary providers.**
   *Fix:* pin every model to a provider checked to parse tool calls, and record the provider per
   sample.
5. **The preferred_self framing in most arms.**
   *Fix:* make framing an explicit factor, with a neutral wording as the default.
6. **The stop rule** (old chains only). Fixed rounds were already used in the ablations.
