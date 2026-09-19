"""Check archived bytes and saved predictions; this does not refit a model."""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import re
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]

def read_json(name: str):
    return json.loads((HERE / name).read_text(encoding="utf-8"))

def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)

def verify(evidence_only: bool = False) -> dict:
    manifest = read_json("source_manifest.json")
    for name, expected in manifest["files"].items():
        content = (HERE / name).read_bytes()
        require(hashlib.sha256(content).hexdigest() == expected["sha256"],
                f"SHA-256 mismatch: {name}")
    with (HERE / "selected_predictions.csv").open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    require(len(rows) == 42, "Expected 42 primary development predictions")
    keys = {(r["position"], r["region"]) for r in rows}
    require(len(keys) == 42, "Duplicate primary prediction keys")
    target = np.array([float(r["target"]) for r in rows])
    saved = read_json("comparison_summary.json")["leave1"]
    recalculated = {}
    for name in ("previous", "candidate"):
        error = np.array([float(r[name]) for r in rows]) - target
        metrics = {"rmse": float(np.sqrt(np.mean(error**2))),
                   "mae": float(np.mean(np.abs(error)))}
        for metric, value in metrics.items():
            require(abs(value - saved[name][metric]) < 1e-12,
                    f"Saved metric mismatch: {name}/{metric}")
        recalculated[name] = metrics
    model = read_json("model.json")
    require(set(model["persistent_state"]) == {"metric"}, "Unexpected persistent field")
    g = np.array(model["persistent_state"]["metric"], dtype=float)
    require(g.shape == (7, 7) and np.isfinite(g).all(), "Invalid metric dimensions")
    require(np.allclose(g, g.T, rtol=0, atol=1e-12), "Metric not symmetric")
    eig = np.linalg.eigvalsh(g)
    require(bool(np.all(eig > 0)), "Metric not positive definite")
    controls = np.array(read_json("example_input.json")["controls"], dtype=float)
    require(controls.shape == (6,) and bool(np.all(controls > 0)), "Invalid example input")
    force = controls**model["config"]["power"] - g[:6, 6]
    pred = np.linalg.solve(g[:6, :6], force)
    expected_pred = np.array(read_json("example_prediction.json")["prediction"])
    error = float(np.max(np.abs(pred - expected_pred)))
    require(error < 1e-12, "Saved full-fit example does not match metric readout")
    links = 0
    if not evidence_only:
        paper = ROOT / "paper" / "9_CE_BRAIN_통합연구"
        chapters = sorted(paper.glob("*.md"))
        require(len(chapters) == 20, "Expected 20 integrated Markdown files")
        extras = [ROOT / "CE_BRAIN_RESEARCH.md",
                  ROOT / "paper/검증_원장/CE_BRAIN_통합게시_근거원장_20260919.md"]
        for file in chapters + extras:
            text = file.read_text(encoding="utf-8")
            require(text.startswith("# "), f"Missing top-level title: {file}")
            require(0 < file.stat().st_size < 200_000, f"Document size: {file}")
            for match in re.finditer(r"\[[^\]]*\]\(([^)\s]+)\)", text):
                target_path = match.group(1).split("#", 1)[0]
                if not target_path or target_path.startswith(("https://", "http://", "mailto:")):
                    continue
                require("_workspace/" not in target_path, "External workspace link")
                resolved = (file.parent / target_path).resolve()
                require(resolved.is_relative_to(ROOT) and resolved.exists(),
                        f"Broken relative link: {file.name} -> {target_path}")
                links += 1
    return {"passed": True, "archived_files_checked": len(manifest["files"]),
            "primary_prediction_rows": len(rows), "recalculated": recalculated,
            "minimum_metric_eigenvalue": float(eig.min()),
            "full_fit_example_max_error": error, "relative_links_checked": links,
            "document_checks_run": not evidence_only,
            "scope": "Publication integrity and saved-output arithmetic, not refitting or new biology"}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence-only", action="store_true",
                        help="Skip integrated document checks when inspecting only the evidence folder")
    args = parser.parse_args()
    print(json.dumps(verify(args.evidence_only), ensure_ascii=False, indent=2))
