from __future__ import annotations

import argparse
import json
from pathlib import Path

from .core import (
    audit_manifest,
    load_manifest,
    materialize_folds,
    perturbation_folds,
    temporal_folds,
)


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Leakage-audited VEC pseudo-holdout construction."
    )
    sub = p.add_subparsers(dest="command", required=True)

    audit = sub.add_parser(
        "audit",
        help="audit a manifest against current phase restrictions",
    )
    audit.add_argument("manifest", type=Path)
    audit.add_argument(
        "--phase",
        choices=["P2", "P3"],
        default="P2",
    )
    audit.add_argument("--check-paths", action="store_true")
    audit.add_argument("--json", type=Path, dest="json_path")

    forge = sub.add_parser(
        "forge",
        help="construct pseudo-holdout fold manifests",
    )
    forge.add_argument("manifest", type=Path)
    forge.add_argument(
        "--task",
        required=True,
        choices=["T1", "T2", "T3"],
    )
    forge.add_argument("--setting", default="")
    forge.add_argument(
        "--mode",
        required=True,
        choices=[
            "extrapolation",
            "interpolation",
            "perturbation",
        ],
    )
    forge.add_argument(
        "--phase",
        choices=["P2", "P3"],
        default="P2",
    )
    forge.add_argument(
        "--min-train-stages",
        type=int,
        default=1,
    )
    forge.add_argument(
        "--out",
        type=Path,
        default=Path("splitforge_out"),
    )
    forge.add_argument(
        "--allow-restricted-manifest",
        action="store_true",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    if args.phase == "P3":
        print(
            "WARNING: P3 has not started yet. The P3 guardrail is a "
            "conservative preview based on the published split schedule; "
            "recheck the official rules when P3 opens on 2026-10-20."
        )

    items = load_manifest(args.manifest)
    problems = audit_manifest(
        items,
        args.phase,
        getattr(args, "check_paths", False),
    )

    if args.command == "audit":
        for problem in problems:
            print(problem)
        if not problems:
            print(
                "PASS: no restricted identities or manifest "
                "conflicts detected"
            )
        if args.json_path:
            args.json_path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )
            args.json_path.write_text(
                json.dumps(
                    {"problems": problems},
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
        return 3 if problems else 0

    if problems and not args.allow_restricted_manifest:
        for problem in problems:
            print(problem)
        print(
            "ERROR: refusing to forge folds from a manifest "
            "that claims currently restricted measured data"
        )
        return 3

    if args.task == "T3":
        if args.mode != "perturbation":
            raise SystemExit(
                "T3 requires --mode perturbation"
            )
        folds = perturbation_folds(
            items,
            setting=args.setting or "heart",
        )
    else:
        if args.mode == "perturbation":
            raise SystemExit(
                "--mode perturbation is only valid for T3"
            )
        folds = temporal_folds(
            items,
            args.task,
            args.setting,
            args.mode,
            min_train_stages=args.min_train_stages,
        )

    if not folds:
        print(
            "ERROR: no valid pseudo-holdout folds can be "
            "constructed from this manifest"
        )
        return 4

    materialize_folds(folds, items, args.out)
    print(f"wrote {len(folds)} fold(s) to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
