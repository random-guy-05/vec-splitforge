# Phase and leakage rules implemented by SplitForge

Snapshot date: **2026-10-01**. This file explains the guardrails in code; it is not a substitute for the official rules.

## P2

SplitForge blocks measured manifest rows in the published protected windows:

- **T1:** `E9.5 < stage <= E13.5`.
- **T2 heart interpolation:** `E8.25 < stage < E8.75`.
- **T2 heart extrapolation:** `E9.5 < stage <= E13.5`.
- **T2 embryo:** `E7.25 < stage < E8.0`.
- **T3:** known Gata4 / beta-catenin identities are blocked conservatively in P2. The official rules use biological comparability rather than publishing a numeric stage window, so SplitForge does not invent one.

The released boundary stages themselves remain usable where the rules say they are released training data.

## P3 preview

P3 has not started yet. The rules and task pages say that validation ground truth will be released for retraining on 20 October while test targets remain hidden. The guardrail below is therefore a conservative preview of the published split structure, not a claim that every external-data boundary for P3 has already been finalized. SplitForge therefore allows the newly released validation stages and conservatively shifts protection to the remaining test side:

- **T1:** E10.5 is usable; stages `E10.5 < stage <= E13.5` remain protected by the guardrail around hidden E12.5.
- **T2 heart:** E10.5 is usable; stages `E10.5 < stage <= E13.5` remain protected around hidden E12.5.
- **T2 embryo:** E7.5 is usable; `E7.5 < stage < E8.0` remains protected around hidden E7.75.
- **T3:** Gata4 is scheduled to become usable with the validation release; beta-catenin remains conservatively blocked in the P3 preview.

The P3 window behavior above is deliberately conservative. If the organisers publish a more specific phase-transition interpretation, update this file and the code together.

## What software cannot infer

The official rules also cover fractional staging systems, alternative alleles of the same held-out gene, and perturbations that phenocopy a held-out condition. SplitForge normalizes a few obvious aliases (`ctnnb1`, `beta-catenin`, `gata4-ko`), but it cannot determine biological equivalence from a CSV label. Ambiguous external sources should be cleared with the organisers before use.
