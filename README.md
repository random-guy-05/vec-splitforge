# VEC SplitForge

**Build task-shaped pseudo-validation splits without accidentally leaking official held-out data.**

`veckit` can score any prediction against a local target you provide, but that makes local evaluation only as good as the holdout you design. SplitForge turns a small manifest of released/local stages into reproducible pseudo-holdout recipes and audits the manifest against the current P2/P3 held-out restrictions.

It **does not copy data** and **does not know hidden answers**. It writes fold metadata, training-file lists, and the exact local `veckit` command to use after your model generates `prediction.h5ad`.

## What it can forge

- **T1 extrapolation:** target is later than every training stage; the immediately preceding stage is the DE/change reference.
- **T2 extrapolation:** same past→future structure within heart or embryo.
- **T2 interpolation:** an interior stage is held out while stages on both sides remain available; the preceding stage is still the scorer reference.
- **T3 perturbation:** leave one locally available perturbation out and use a matched WT stage as the scorer reference.

## Phase-aware leakage guard

As of the 2026-10-05 source snapshot, P2 still withholds the official validation/test targets. SplitForge implements the **published protected stage windows**, not only exact labels: T1/heart extrapolation windows, T2 heart/embryo interpolation windows, and known T3 held-out genotypes. With `--phase P3`, SplitForge can preview the published final-phase split: released validation stages become usable while conservative windows remain around the still-hidden test targets. Until P3 actually opens on 20 October, that mode is explicitly labeled a preview and users should re-check the official rules at the phase transition.

This is a **guardrail, not a legal determination**. The rules also cover alternative staging systems, other alleles and phenocopies that a CSV label cannot reliably infer. For ambiguous external data, ask the organisers as the official rules recommend.

## Manifest

```csv
id,path,task,setting,stage,condition
t1_e8_5,/data/T1/E8.5.h5ad,T1,,8.5,wt
t1_e9_5,/data/T1/E9.5.h5ad,T1,,9.5,wt
heart_e8_25,/data/T2/heart/E8.25.h5ad,T2,heart,8.25,wt
heart_e8_75,/data/T2/heart/E8.75.h5ad,T2,heart,8.75,wt
```

The path is recorded, not opened unless `audit --check-paths` is requested.

## Usage

```bash
pip install -e .

# Safety audit first
vec-splitforge audit stages.csv --phase P2

# T1 task-shaped historical extrapolation
vec-splitforge forge stages.csv \
  --task T1 --mode extrapolation --phase P2 --out splits/t1

# T2 heart interpolation
vec-splitforge forge stages.csv \
  --task T2 --setting heart --mode interpolation --phase P2 --out splits/t2_heart_interp

# T3 perturbation pseudo-holdouts
vec-splitforge forge stages.csv \
  --task T3 --setting heart --mode perturbation --phase P2 --out splits/t3
```

Each fold contains:

- `fold.json` — exact train/target/reference identities;
- `train_files.txt` — files your training script is allowed to see for that fold;
- `score.sh` — exact `veckit` command using `prediction.h5ad`;
- a top-level `index.json` summarizes all folds.

## Important interpretation

A pseudo-target is released/local data and is **not a preview of the hidden leaderboard**. SplitForge is designed to make local model selection less ad hoc and less leakage-prone, not to infer hidden answers.

See `docs/SOURCES.md` for the official split/rules snapshot.
