# Community Contribution submission text

## Title
VEC SplitForge — leakage-audited task-shaped pseudo-validation split builder

## Description
VEC SplitForge turns a small manifest of locally available VEC stages into reproducible pseudo-validation folds instead of leaving every team to invent its own holdout logic. It generates task-shaped T1/T2 extrapolation folds, T2 interpolation folds, and T3 leave-one-perturbation-out folds; writes exact train/target/reference identities plus ready-to-run veckit scoring commands; and audits the manifest against the current P2/P3 held-out **stage windows** and known held-out genotypes, including fractional-stage rows inside the published protected intervals. P2 validation/test windows are refused by default. A separate P3 preview follows the published final-phase split by allowing validation stages scheduled for release while conservatively protecting the still-hidden test side; the CLI warns users to re-check the official rules when P3 opens. The tool never copies Challenge data or claims pseudo-target performance predicts the hidden leaderboard. It helps teams perform cleaner local model selection and avoid accidental leakage.
