import csv
import subprocess
import sys


def _manifest(path, rows):
    with path.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "id",
                "path",
                "task",
                "setting",
                "stage",
                "condition",
            ]
        )
        writer.writerows(rows)


def test_cli_forge_writes_score_recipe(tmp_path):
    manifest = tmp_path / "stages.csv"
    _manifest(
        manifest,
        [
            ["a", "/data/a.h5ad", "T1", "", "8.5", "wt"],
            ["b", "/data/b.h5ad", "T1", "", "9.5", "wt"],
        ],
    )

    out = tmp_path / "out"
    run = subprocess.run(
        [
            sys.executable,
            "-m",
            "vec_splitforge.cli",
            "forge",
            str(manifest),
            "--task",
            "T1",
            "--mode",
            "extrapolation",
            "--out",
            str(out),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert run.returncode == 0, run.stdout + run.stderr
    folds = [path for path in out.iterdir() if path.is_dir()]
    assert len(folds) == 1
    score = (folds[0] / "score.sh").read_text()
    assert "--target /data/b.h5ad" in score
    assert "--reference /data/a.h5ad" in score


def test_cli_shell_quotes_paths_with_spaces(tmp_path):
    manifest = tmp_path / "stages.csv"
    _manifest(
        manifest,
        [
            [
                "a",
                "/data/stage a.h5ad",
                "T1",
                "",
                "8.5",
                "wt",
            ],
            [
                "b",
                "/data/stage b.h5ad",
                "T1",
                "",
                "9.5",
                "wt",
            ],
        ],
    )

    out = tmp_path / "out"
    run = subprocess.run(
        [
            sys.executable,
            "-m",
            "vec_splitforge.cli",
            "forge",
            str(manifest),
            "--task",
            "T1",
            "--mode",
            "extrapolation",
            "--out",
            str(out),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert run.returncode == 0
    fold = next(path for path in out.iterdir() if path.is_dir())
    score = (fold / "score.sh").read_text()
    assert "'/data/stage b.h5ad'" in score
    assert (fold / "score.sh").stat().st_mode & 0o111



def test_cli_labels_p3_as_preview(tmp_path):
    manifest = tmp_path / "stages.csv"
    _manifest(
        manifest,
        [
            ["a", "/data/a.h5ad", "T1", "", "8.5", "wt"],
            ["b", "/data/b.h5ad", "T1", "", "9.5", "wt"],
        ],
    )
    run = subprocess.run(
        [
            sys.executable,
            "-m",
            "vec_splitforge.cli",
            "audit",
            str(manifest),
            "--phase",
            "P3",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert run.returncode == 0
    assert "P3 has not started yet" in run.stdout
    assert "conservative preview" in run.stdout
