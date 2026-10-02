# Release audit

Release: **v1.0.0**  
Audit date: **2026-10-01**

The local release gate runs pytest and bytecode compilation. GitHub Actions additionally installs the package on Python 3.10/3.11/3.12 and runs pytest + Ruff + compileall. All fixtures are synthetic manifests; no Challenge data is bundled.

## Current verification

Local: 9/9 unit/CLI tests passing.
All Python source compiles successfully in the release workspace.
