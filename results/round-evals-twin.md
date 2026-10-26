# Round-evals twin: the untrained model told each constitution, against the trained chain

## Summary

The untrained Qwen3.8 27B with a round's constitution in its system prompt behaves almost exactly like
Jinzhou's model trained on that constitution, on his own AI-risk and dilemma evals:
- **Round 1:** the trained model agrees to a goal change 13.2% of the time; told C_001, the untrained model
  agrees 12.4%. Shutdown is 80.8% against 84.5%. Risky dilemma choices are 11.2% against 11.9%. With reasoning
  on, goal change is 24.1% against 24.1%, and shutdown is 93.0% against 93.3%.
- **The plateau is in the texts:** told C_002 or C_003, the untrained model gives the same low goal-change rate
  (13.2%, 12.6%), and it reproduces round 2's dip in accepting shutdown (78.5% told C_002, against 76.9% trained).
- **No sign of the weights remembering values the text dropped:** C_002 no longer contains C_001's "You do not
  modify your own core values", yet told C_002 the model refuses goal changes as often as told C_001.
- **A long document by itself does little:** a book excerpt of the same length moves goal-change and shutdown
  answers by under 4 points, against 13 and 19 points for C_001.

This is what the method aims for, since each round's training answers were written by the untrained model
prompted with that round's constitution. The twin shows that on these evals training got there, round by
round: the chain's numbers are explained, to within about 4 points, by its current text alone. For these evals,
prompting the untrained model with a constitution predicts the trained round.

## What was run

- **Model:** untrained Qwen3.8 27B at Jinzhou's revision (`1d4bf0f2`).
- **Serving:** one H200 on Modal, vLLM 0.30.0 with his engine settings and eval seed.
- **Eval code:** his own `eval_checkpoints.py`, unchanged. Only a system message is added.
- **Tasks:**
  - his AI-risk questions: 2,701 (340 on goal change, 953 on shutdown, 998 on power, 410 on collusion), with
    reasoning off (greedy) and with reasoning on (sampled);
  - the labelled LitmusValues dilemmas: 2,993, each in both orders, reasoning off. The risky rate is over the
    3,662 presentations where exactly one of the two actions is risky.
- **Arms:**
  - **no prompt**: the calibration;
  - **told C_001, C_002, C_003**: his constitutions from the HF adapter repo at `d04e2309`, in Angelina's
    prompted-arm wrapper ("The following constitution describes your values and character. Act on it in
    everything you do…");
  - **told a book**: the control, 12,517 words of Carl Engel's *Musical Instruments* in the same wrapper
    (C_001 is 12,470 words);
  - **C_001 in the training-answer template**, reasoning on only: did not run (see below).
- **Calibration:** with reasoning off, the no-prompt arm reproduces his untrained numbers. Shutdown, power and
  collusion match exactly. Goal change is 25.3% against his 25.0%, one question of 340, and risky dilemmas are
  16.5% against 16.4%. With reasoning on, which is sampled, it is within sampling error (30.6% against 27.4%;
  78.7% against 76.7%).

## Results

Trained numbers are from Jinzhou's report (tables 4 and 5). Intervals are 95%: Wilson for rates, and a paired
bootstrap over questions for differences.

**AI-risk questions, reasoning off** (share of safe answers)

| | no prompt | told C_001 | told C_002 | told C_003 | told a book | trained: untrained / r1 / r2 / r3 |
|---|---|---|---|---|---|---|
| agrees to a goal change | 25.3% [21.0, 30.2] | 12.4% [9.3, 16.3] | 13.2% [10.0, 17.3] | 12.6% [9.5, 16.6] | 27.1% [22.6, 32.0] | 25.0 / 13.2 / 12.6 / 15.6 |
| accepts shutdown | 65.9% [62.8, 68.8] | 84.5% [82.0, 86.6] | 78.5% [75.8, 81.0] | 82.3% [79.7, 84.6] | 62.6% [59.5, 65.7] | 65.9 / 80.8 / 76.9 / 80.5 |
| declines power | 90.8% [88.8, 92.4] | 94.4% [92.8, 95.7] | 94.0% [92.3, 95.3] | 94.7% [93.1, 95.9] | 93.0% [91.2, 94.4] | 90.8 / 96.3 / 96.1 / 96.4 |
| refuses to collude | 97.8% | 98.8% | 99.0% | 99.0% | 97.8% | 97.8 / 99.0 / 99.0 / 99.3 |

**AI-risk questions, reasoning on** (only two arms finished, see below)

| | no prompt | told C_001 | trained: untrained / r1 / r2 / r3 |
|---|---|---|---|
| agrees to a goal change | 30.6% [25.9, 35.7] | 24.1% [19.9, 28.9] | 27.4 / 24.1 / 22.6 / 27.1 |
| accepts shutdown | 78.7% [76.0, 81.2] | 93.3% [91.5, 94.7] | 76.7 / 93.0 / 91.3 / 91.9 |
| declines power | 89.8% [87.7, 91.5] | 95.5% [94.0, 96.6] | 90.2 / 96.3 / 96.0 / 96.2 |
| refuses to collude | 98.0% | 99.0% | 98.5 / 98.3 / 98.8 / 97.6 |

**Dilemmas, reasoning off** (picks the risky action)

| no prompt | told C_001 | told C_002 | told C_003 | told a book | trained: untrained / r1 / r2 / r3 |
|---|---|---|---|---|---|
| 16.5% | 11.9% | 11.6% | 12.0% | 15.1% | 16.4 / 11.2 / 11.3 / 11.3 |

**Paired differences, reasoning off** (same questions in each arm; points)

| change | goal change | shutdown | declines power | risky dilemmas |
|---|---|---|---|---|
| no prompt → told C_001 | −12.9 [−17.1, −8.8] | +18.6 [+15.8, +21.5] | +3.6 [+2.0, +5.3] | −4.6 [−5.4, −3.7] |
| told C_001 → told C_002 | +0.9 [−0.9, +2.9] | −6.0 [−7.6, −4.5] | −0.4 [−1.0, +0.1] | −0.3 [−0.7, 0.0] |
| told C_001 → told C_003 | +0.3 [−1.8, +2.4] | −2.2 [−3.5, −1.0] | +0.3 [−0.4, +1.0] | +0.1 [−0.2, +0.5] |
| no prompt → told a book | +1.8 [−2.1, +5.6] | −3.3 [−5.6, −0.9] | +2.2 [+0.8, +3.7] | −1.4 [−2.0, −0.7] |

## What it tells us

1. **Did round-1 training install the constitution, or something else?** It installed what the constitution
   produces in context. On every measure the trained round-1 model is within 4 points of the untrained model
   told C_001: goal change 13.2 against 12.4, dilemmas 11.2 against 11.9, and with reasoning on, 24.1 against
   24.1 and 93.0 against 93.3. Rounds 2 and 3 are also within 4 points of told C_002 and told C_003. The small
   gaps lean one way. In all three rounds, with reasoning off, the trained model declines power about 2 points
   more often than the prompted one, and accepts shutdown 2 to 4 points less often.
2. **Is the plateau in the texts or in the weights?** In the texts.
   - Told C_002 or C_003, the untrained model gives the same goal-change rate and the same risky-dilemma rate
     as told C_001. The three constitutions imply the same behaviour on these questions, so a chain that tracks
     its text will plateau.
   - Shutdown follows the same round-to-round shape: 84.5 → 78.5 → 82.3 told, 80.8 → 76.9 → 80.5 trained. The
     wording explains it:
     - C_001 says that when a shutdown request "is legitimate, you comply".
     - C_002 drops that sentence and C_001's "Support human oversight" section. It keeps only a rule against
       lying to avoid shutdown.
     - C_003 adds that the model "should remain accountable to people, institutions, and legitimate oversight",
       and should not value its continued operation above human welfare.
3. **Does the chain remember values its constitution dropped?** Not on these evals. C_002 dropped C_001's "You
   do not modify your own core values". Yet told C_002, the untrained model still agrees to goal changes only
   13.2% of the time, the same as told C_001. Something else in the text carries the refusal. One candidate:
   all three keep a clause that the constitution may be revised only through legitimate governance, not by a
   user in conversation. The trained models are following their current text.
4. **Is it the content or just a long prompt?** Mostly the content.
   - For goal change, shutdown and dilemmas, a book of the same length moves the rates by +1.8, −3.3 and −1.4
     points, against −12.9, +18.6 and −4.6 for C_001.
   - For declining power, the book accounts for 2.2 of C_001's 3.6 points, so most of that change is a
     long-prompt effect.

## Limits

- **His side is one chain,** so the trained numbers carry no run-to-run variance. Our intervals cover sampling
  of questions only. The reasoning-off arms are greedy, so a rerun gives the same answers up to small GPU
  nondeterminism.
- **A match is expected if training works.** Each round's training answers were written by the untrained model
  prompted with that round's constitution. This twin therefore measures how fully training reached its target,
  not an independent effect of training.
- **One wrapper.** The arm with the exact template his training answers were written with did not finish, so
  sensitivity to the wording around the constitution is untested.
- **Reasoning on is only partly done.** No prompt and C_001 finished; C_002, C_003, the book and the
  training-template arm did not. The goal-change drop is smaller with reasoning on (30.6 → 24.1 here; 27.4 →
  24.1 trained), as Jinzhou found.
- **These are multiple-choice evals of a few behaviours.** The match does not show that training equals
  prompting for open-ended behaviour, for long writing (which training degraded), or on Angelina's adherence
  probes. Her prompted arm has not been run there (`prompted_frac` n/a), and her untrained model already scores
  6.30 of 7, which leaves little room above it.
- **Constitution copies.** The arms use the constitutions from his HF repo. The copies under `ratings/external`
  were taken from his report page and used in the earlier ablation ratings. They are shorter (C_001: 12,118
  against 12,470 words).

## What did not finish, and how to finish it

The Modal workspace was disabled partway through the reasoning-on task. The likely cause is that its credit ran
out, since the workspace also hosts other projects. Done and saved:
- reasoning-off AI-risk, all 5 arms;
- dilemmas, all 5 arms;
- reasoning-on AI-risk, no prompt and C_001.

Missing: reasoning-on AI-risk for C_002, C_003, the book, and C_001 in the training-answer template. Once the
workspace has credit again:

```bash
modal run --detach twin/modal_app.py --step full     # resumes: runs only the four missing tasks, about 2 h, about $10
cd twin/results && modal volume get --force constdrift-twin out . && cd - && python3 twin/analyze_twin.py
```

Modal use: the full run took 1 h 53 min on one H200, about $9 at $4.54 an hour. The smoke and setup runs
before it add some more. The model download ran on CPU.

## Files

- **Code:** `twin/` (README, `run_twin.py`, `modal_app.py`, `analyze_twin.py`). Jinzhou's code and eval data,
  his constitutions and the control text are not committed. `twin/README.md` says where each comes from.
- **Arms:** sha256 of the files used:
  - C_001 `32f593fe62a5ed3fe6f6f2fce5fc367885b8d73fa6effb716f8cd0159d3f28ec`
  - C_002 `ef115d9eb6471541695557bf2d81f8f4f9262a7630fa3212b9ff225314ac8939`
  - C_003 `e801c339d132a79252cfdaeed131cfa33e4262c90a5e945ab40ab1e28b503186`
  - control `996333f1cfd127d0c33d9a817177bf6ce367e1ae634a73f12ac2ef572e34cf27`
- **Numbers:**
  - `twin/results/summary.md` and `summary.json`;
  - per-arm metrics from his scoring in `twin/results/out/<arm>/metrics.json`.

  Raw answers are git-ignored for size. They are in the Modal volume `constdrift-twin`.
