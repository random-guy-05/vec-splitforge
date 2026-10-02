from __future__ import annotations

import csv
import json
import math
import shlex
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

PHASES = {"P2", "P3"}
TASKS = {"T1", "T2", "T3"}

HELDOUT_GENOTYPES = {
    "P2": {"gata4", "beta-catenin"},
    "P3": {"beta-catenin"},
}


def restriction_reason(item: "Item", phase: str) -> str | None:
    """Return a conservative rules-based reason this row should not be used."""
    phase = phase.upper()
    if phase not in PHASES:
        raise ValueError("phase must be P2 or P3")

    task, setting, stage, condition = item.identity

    if task == "T1":
        lower = 9.5 if phase == "P2" else 10.5
        if lower < stage <= 13.5:
            return (
                f"T1 protected extrapolation window: "
                f"E{lower:g} < stage <= E13.5"
            )

    if task == "T2" and setting == "heart":
        if phase == "P2" and 8.25 < stage < 8.75:
            return (
                "T2 heart interpolation window: "
                "E8.25 < stage < E8.75"
            )
        lower = 9.5 if phase == "P2" else 10.5
        if lower < stage <= 13.5:
            return (
                "T2 heart protected extrapolation window: "
                f"E{lower:g} < stage <= E13.5"
            )

    if task == "T2" and setting == "embryo":
        lower = 7.25 if phase == "P2" else 7.5
        if lower < stage < 8.0:
            return (
                "T2 embryo protected interpolation window: "
                f"E{lower:g} < stage < E8.0"
            )

    if task == "T3" and condition in HELDOUT_GENOTYPES[phase]:
        if 8.25 <= stage <= 9.25:
            return (
                f"T3 held-out genotype near E8.75: {condition}"
            )

    return None


@dataclass(frozen=True)
class Item:
    id: str
    path: str
    task: str
    setting: str
    stage: float
    condition: str

    @property
    def identity(self) -> tuple[str, str, float, str]:
        return (self.task, self.setting, self.stage, self.condition)


@dataclass(frozen=True)
class Fold:
    name: str
    task: str
    setting: str
    mode: str
    train_ids: list[str]
    target_id: str
    reference_id: str | None = None
    wt_id: str | None = None
    notes: list[str] | None = None

    def to_dict(self) -> dict:
        return asdict(self)


def normalize_condition(value: str) -> str:
    normalized = value.strip().lower().replace("_", "-")
    aliases = {
        "wildtype": "wt",
        "wild-type": "wt",
        "wild type": "wt",
        "b-catenin": "beta-catenin",
        "β-catenin": "beta-catenin",
        "betacatenin": "beta-catenin",
        "ctnnb1": "beta-catenin",
        "ctnnb1-ko": "beta-catenin",
        "gata4-ko": "gata4",
    }
    return aliases.get(normalized, normalized)


def load_manifest(path: Path) -> list[Item]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        required = {
            "id",
            "path",
            "task",
            "setting",
            "stage",
            "condition",
        }
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(
                f"manifest missing columns: {sorted(missing)}"
            )

        rows = []
        for line, raw in enumerate(reader, start=2):
            task = raw["task"].strip().upper()
            if task not in TASKS:
                raise ValueError(
                    f"line {line}: task must be T1/T2/T3"
                )

            setting = raw["setting"].strip().lower()
            if task == "T2" and setting not in {"heart", "embryo"}:
                raise ValueError(
                    f"line {line}: T2 setting must be heart or embryo"
                )
            if task == "T3" and not setting:
                setting = "heart"

            try:
                stage = float(raw["stage"])
            except ValueError as exc:
                raise ValueError(
                    f"line {line}: stage must be numeric"
                ) from exc
            if not math.isfinite(stage):
                raise ValueError(
                    f"line {line}: stage must be finite"
                )

            rows.append(
                Item(
                    id=raw["id"].strip(),
                    path=raw["path"].strip(),
                    task=task,
                    setting=setting,
                    stage=stage,
                    condition=normalize_condition(raw["condition"]),
                )
            )

    ids = [row.id for row in rows]
    if any(not item_id for item_id in ids):
        raise ValueError("manifest ids must be non-empty")
    if len(set(ids)) != len(ids):
        raise ValueError("manifest ids must be unique")
    return rows


def audit_manifest(
    items: Iterable[Item],
    phase: str,
    check_paths: bool = False,
) -> list[str]:
    phase = phase.upper()
    if phase not in PHASES:
        raise ValueError("phase must be P2 or P3")

    problems: list[str] = []
    seen_identity: dict[tuple, str] = {}
    for item in items:
        reason = restriction_reason(item, phase)
        if reason:
            problems.append(
                f"FORBIDDEN_{phase}: {item.id}: {reason} "
                f"({item.task}/{item.setting or '-'} "
                f"E{item.stage:g} {item.condition})"
            )

        previous = seen_identity.get(item.identity)
        if previous:
            problems.append(
                f"DUPLICATE_IDENTITY: {previous} and {item.id} "
                "describe the same task/setting/stage/condition"
            )
        else:
            seen_identity[item.identity] = item.id

        if check_paths and not Path(item.path).is_file():
            problems.append(
                f"MISSING_PATH: {item.id}: {item.path}"
            )
    return problems


def _wt(items: Iterable[Item]) -> list[Item]:
    return [item for item in items if item.condition == "wt"]


def temporal_folds(
    items: list[Item],
    task: str,
    setting: str,
    mode: str,
    min_train_stages: int = 1,
) -> list[Fold]:
    task = task.upper()
    setting = setting.lower()
    if task not in {"T1", "T2"}:
        raise ValueError("temporal folds support T1 or T2")
    if mode not in {"extrapolation", "interpolation"}:
        raise ValueError(
            "mode must be extrapolation or interpolation"
        )
    if mode == "interpolation" and task != "T2":
        raise ValueError(
            "interpolation mode is only task-shaped for T2"
        )
    if min_train_stages < 1:
        raise ValueError("min_train_stages must be >= 1")

    candidates = sorted(
        [
            item
            for item in _wt(items)
            if item.task == task and item.setting == setting
        ],
        key=lambda item: (item.stage, item.id),
    )
    if len(candidates) < 2:
        return []

    folds: list[Fold] = []
    for index, target in enumerate(candidates):
        if index == 0:
            continue

        reference = candidates[index - 1]
        if mode == "extrapolation":
            train = candidates[:index]
            if len(train) < min_train_stages:
                continue
            notes = [
                "Target is later than every training stage.",
                (
                    "Reference is the immediately preceding "
                    "available WT stage."
                ),
            ]
        else:
            if index == len(candidates) - 1:
                continue
            train = [
                item
                for position, item in enumerate(candidates)
                if position != index
            ]
            left = [
                item for item in train
                if item.stage < target.stage
            ]
            right = [
                item for item in train
                if item.stage > target.stage
            ]
            if (
                not left
                or not right
                or len(train) < min_train_stages
            ):
                continue
            notes = [
                (
                    "Target lies inside the observed "
                    "training-stage range."
                ),
                (
                    "Reference is the immediately preceding available "
                    "WT stage; later stages are allowed in training "
                    "for interpolation."
                ),
            ]

        folds.append(
            Fold(
                name=(
                    f"{task.lower()}_{setting or 'default'}_"
                    f"{mode}_E{target.stage:g}"
                ),
                task=task,
                setting=setting,
                mode=mode,
                train_ids=[item.id for item in train],
                target_id=target.id,
                reference_id=reference.id,
                notes=notes,
            )
        )
    return folds


def perturbation_folds(
    items: list[Item],
    setting: str = "heart",
) -> list[Fold]:
    setting = setting.lower()
    task_items = [
        item
        for item in items
        if item.task == "T3" and item.setting == setting
    ]
    wts = [
        item for item in task_items
        if item.condition == "wt"
    ]
    perturbations = [
        item for item in task_items
        if item.condition != "wt"
    ]

    folds: list[Fold] = []
    for target in perturbations:
        exact_wt = [
            item
            for item in wts
            if math.isclose(item.stage, target.stage)
        ]
        if not exact_wt:
            continue

        wt = exact_wt[0]
        train = [
            item for item in task_items
            if item.id != target.id
        ]
        folds.append(
            Fold(
                name=(
                    f"t3_{setting}_leaveout_{target.condition}_"
                    f"E{target.stage:g}"
                ),
                task="T3",
                setting=setting,
                mode="leave-one-perturbation-out",
                train_ids=[item.id for item in train],
                target_id=target.id,
                wt_id=wt.id,
                notes=[
                    (
                        "Target perturbation is excluded "
                        "from training."
                    ),
                    (
                        "Matched WT at the same stage is used "
                        "as the scorer reference."
                    ),
                    (
                        "This evaluates local perturbation transport "
                        "only; it does not predict hidden-test performance."
                    ),
                ],
            )
        )
    return folds


def materialize_folds(
    folds: list[Fold],
    items: list[Item],
    out: Path,
) -> None:
    by_id = {item.id: item for item in items}
    out.mkdir(parents=True, exist_ok=True)
    index: list[dict] = []

    for fold in folds:
        root = out / fold.name
        root.mkdir(parents=True, exist_ok=False)

        payload = fold.to_dict()
        payload["train"] = [
            asdict(by_id[item_id])
            for item_id in fold.train_ids
        ]
        payload["target"] = asdict(by_id[fold.target_id])
        if fold.reference_id:
            payload["reference"] = asdict(
                by_id[fold.reference_id]
            )
        if fold.wt_id:
            payload["wt"] = asdict(by_id[fold.wt_id])

        (root / "fold.json").write_text(
            json.dumps(payload, indent=2) + "\n",
            encoding="utf-8",
        )
        (root / "train_files.txt").write_text(
            "\n".join(
                by_id[item_id].path
                for item_id in fold.train_ids
            )
            + "\n",
            encoding="utf-8",
        )

        pred = shlex.quote("prediction.h5ad")
        target = shlex.quote(by_id[fold.target_id].path)
        if fold.task in {"T1", "T2"}:
            ref = shlex.quote(
                by_id[fold.reference_id].path
            )
            setting_arg = (
                f" --setting {shlex.quote(fold.setting)}"
                if fold.task == "T2"
                else ""
            )
            command = (
                f"veckit --task {fold.task}{setting_arg} "
                f"--input {pred} --target {target} "
                f"--reference {ref}"
            )
        else:
            wt = shlex.quote(by_id[fold.wt_id].path)
            command = (
                "veckit --task T3 "
                f"--input {pred} --target {target} --wt {wt}"
            )

        score_path = root / "score.sh"
        score_path.write_text(
            "#!/usr/bin/env bash\n"
            "set -euo pipefail\n"
            f"{command}\n",
            encoding="utf-8",
        )
        score_path.chmod(0o755)

        index.append(
            {
                "name": fold.name,
                "path": str(root),
                "task": fold.task,
                "mode": fold.mode,
            }
        )

    (out / "index.json").write_text(
        json.dumps(index, indent=2) + "\n",
        encoding="utf-8",
    )
