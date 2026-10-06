# Release audit

Release: **v1.0.0**  
Audit date: **2026-10-05**

## Release gate

GitHub Actions installs the package on Python **3.10, 3.11, and 3.12** and requires:

- the complete pytest suite;
- Ruff static/lint checks;
- bytecode compilation of `src` and `tests`.

All fixtures are synthetic manifests; no Challenge data is bundled.

## Coverage

The suite covers:

- P2 protected stage-window boundaries;
- the conservative T3 held-out-genotype guard without inventing a numeric "comparable stage" cutoff;
- the explicit pre-P3 preview warning;
- T1/T2 temporal fold construction;
- T3 leave-one-perturbation-out folds;
- manifest schema validation;
- score-script generation and shell quoting.

## Current verification

The latest public GitHub Actions matrix is green. Challenge-specific rule claims are tied to `docs/SOURCES.md` and `docs/PHASE_RULES.md`; the official rules remain authoritative.
