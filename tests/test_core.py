from pathlib import Path

import pytest

from vec_splitforge.core import (
    Item,
    audit_manifest,
    load_manifest,
    perturbation_folds,
    temporal_folds,
)


def item(id, task, setting, stage, condition="wt"):
    return Item(
        id=id,
        path=f"/{id}.h5ad",
        task=task,
        setting=setting,
        stage=stage,
        condition=condition,
    )


def test_p2_restricted_data_is_flagged_across_protected_window():
    for stage in [10.2, 10.5, 12.5, 13.5]:
        problems = audit_manifest(
            [item("x", "T1", "", stage)],
            "P2",
        )
        assert problems
        assert "FORBIDDEN_P2" in problems[0]

    assert audit_manifest(
        [item("ok", "T1", "", 9.5)],
        "P2",
    ) == []
    assert audit_manifest(
        [item("late", "T1", "", 13.6)],
        "P2",
    ) == []


def test_t2_interpolation_windows_are_guarded():
    assert audit_manifest(
        [item("h", "T2", "heart", 8.5)],
        "P2",
    )
    assert audit_manifest(
        [item("e", "T2", "embryo", 7.6)],
        "P2",
    )
    assert audit_manifest(
        [item("h0", "T2", "heart", 8.25)],
        "P2",
    ) == []
    assert audit_manifest(
        [item("e0", "T2", "embryo", 8.0)],
        "P2",
    ) == []


def test_p3_validation_is_legal_but_test_window_stays_forbidden():
    validation = [item("v", "T1", "", 10.5)]
    test = [item("t", "T1", "", 12.5)]
    assert audit_manifest(validation, "P3") == []
    assert audit_manifest(test, "P3")
    assert audit_manifest(
        [item("embryo_val", "T2", "embryo", 7.5)],
        "P3",
    ) == []
    assert audit_manifest(
        [item("embryo_test", "T2", "embryo", 7.75)],
        "P3",
    )


def test_t1_extrapolation_fold_is_strictly_past_to_future():
    rows = [
        item("a", "T1", "", 8.5),
        item("b", "T1", "", 9.5),
    ]
    folds = temporal_folds(
        rows,
        "T1",
        "",
        "extrapolation",
    )
    assert len(folds) == 1
    fold = folds[0]
    assert fold.train_ids == ["a"]
    assert fold.reference_id == "a"
    assert fold.target_id == "b"


def test_t2_interpolation_requires_both_sides():
    rows = [
        item("a", "T2", "heart", 8.25),
        item("b", "T2", "heart", 8.75),
        item("c", "T2", "heart", 9.5),
    ]
    folds = temporal_folds(
        rows,
        "T2",
        "heart",
        "interpolation",
    )
    assert len(folds) == 1
    assert folds[0].target_id == "b"
    assert folds[0].train_ids == ["a", "c"]
    assert folds[0].reference_id == "a"


def test_t3_leave_one_perturbation_out_uses_matched_wt():
    rows = [
        item("wt", "T3", "heart", 9.5, "wt"),
        item(
            "ko",
            "T3",
            "heart",
            9.5,
            "mab21l2",
        ),
    ]
    folds = perturbation_folds(rows)
    assert len(folds) == 1
    assert folds[0].target_id == "ko"
    assert folds[0].wt_id == "wt"
    assert "ko" not in folds[0].train_ids


def test_manifest_schema_validation(tmp_path: Path):
    path = tmp_path / "bad.csv"
    path.write_text(
        "id,path,task\na,b,T1\n",
        encoding="utf-8",
    )
    with pytest.raises(
        ValueError,
        match="missing columns",
    ):
        load_manifest(path)



def test_t3_known_heldout_genotype_is_blocked_without_invented_stage_window():
    problems = audit_manifest(
        [item("gata4_late", "T3", "heart", 12.0, "gata4")],
        "P2",
    )
    assert problems
    assert "known held-out genotype" in problems[0]
