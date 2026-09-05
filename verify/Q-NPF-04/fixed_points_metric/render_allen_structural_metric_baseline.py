"""Describe frozen out-of-fold predictions; no refitting or model selection."""
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent
STEM = "allen_structural_metric_baseline"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def aggregate(y, probability, selector, value):
    rows = []
    for left, right in zip(selector[:-1], selector[1:]):
        mask = (value >= left) & (value < right)
        if right == selector[-1]:
            mask |= value == right
        if not mask.any():
            continue
        rows.append(dict(left=float(left), right=float(right), n=int(mask.sum()),
                         positive=int(y[mask].sum()), observed=float(y[mask].mean()),
                         mean_x=float(value[mask].mean()), predicted=float(probability[mask].mean())))
    return rows


def main():
    outputs = [HERE / (STEM + suffix) for suffix in ["_summary.json", ".png", ".svg"]]
    if any(p.exists() for p in outputs):
        raise FileExistsError("Completed presentation artifacts are immutable")
    source = HERE / (STEM + "_result.json")
    arrays = HERE / (STEM + "_arrays.npz")
    result = json.loads(source.read_text(encoding="utf-8"))
    assert digest(arrays) == result["arrays_sha256"]
    assert digest(HERE / (STEM + ".py")) == result["code_sha256"]
    with np.load(arrays, allow_pickle=False) as data:
        y = data["label"]
        p = data["out_of_fold_probability"]
        distance = data["distance_um"]
        models = data["models"].tolist()
    calibration = {}
    distance_bins = {}
    for model in models:
        pred = p[:, models.index(model)]
        calibration[model] = aggregate(y, pred, [0, .025, .05, .075, .1, .15, .2, .3, .5, 1], pred)
        distance_bins[model] = aggregate(y, pred, [0, 50, 100, 150, 200, 300, 500, 1000], distance)
    geometry = result["geometry_audit"]
    ratio = np.array([r["distance_3D_over_2D"] for r in geometry])
    error = np.array([r["squared_2D_reconstruction_error_um2"] for r in geometry])
    squared = np.array([r["distance_2D_um"] ** 2 for r in geometry])
    relative = np.abs(error) / squared
    geometry_summary = dict(n=len(geometry), ratio_3D_over_2D_q05_q50_q95=np.quantile(ratio, [.05, .5, .95]).tolist(),
                            max_absolute_squared_error_um2=float(np.abs(error).max()),
                            max_relative_squared_error=float(relative.max()),
                            relative_error_above_1e_minus_6=int((relative > 1e-6).sum()),
                            worst_relative_pair_ids=[geometry[i]["pair_id"] for i in np.argsort(relative)[-10:][::-1]])
    quadratic = sorted([r for r in result["model_fits"] if r["model"] == "quadratic_metric"], key=lambda r: r["fold"])
    scores = {r["model"]: r for r in result["overall_scores"]}
    summary = dict(version="allen-structural-metric-baseline-presentation-v1", renderer_sha256=digest(Path(__file__)),
                   result_sha256=digest(source), arrays_sha256=digest(arrays),
                   calibration=calibration, distance_bins=distance_bins, geometry=geometry_summary,
                   quadratic_relative_log_loss_reduction=1-scores["quadratic_metric"]["log_loss"]/scores["no_distance"]["log_loss"],
                   quadratic_relative_brier_reduction=1-scores["quadratic_metric"]["brier"]/scores["no_distance"]["brier"],
                   scope="Descriptive bins of fixed internal OOF predictions; context mixtures retained; no new fit or uncertainty calculation")
    with outputs[0].open("x", encoding="utf-8") as stream:
        json.dump(summary, stream, indent=2, allow_nan=False)
        stream.write("\n")

    plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False,
                         "svg.fonttype": "none", "figure.dpi": 120})
    fig, axes = plt.subplots(2, 2, figsize=(12.8, 9.2))
    colors = {"no_distance": "#808080", "quadratic_metric": "#1265a8", "radial_link": "#c36013", "shape_control": "#35804d"}
    labels = {"no_distance": "Context only", "quadratic_metric": "Squared-distance link", "radial_link": "Distance link", "shape_control": "Piecewise distance link"}
    ax = axes[0, 0]
    fold_scores = {(r["model"], r["fold"]): r["log_loss"] for r in result["fold_scores"]}
    for model in ["quadratic_metric", "radial_link", "shape_control"]:
        differences = [fold_scores[model, f] - fold_scores["no_distance", f] for f in range(5)]
        ax.plot(range(5), differences, "o-", label=labels[model], color=colors[model])
    ax.axhline(0, color="black", linewidth=.8)
    ax.set(title="A  Distance improves held-out label prediction", xlabel="Held-out donor fold", ylabel="Log loss minus context-only baseline")
    ax.set_xticks(range(5))
    ax.legend(frameon=False, fontsize=8, loc="upper right")

    ax = axes[0, 1]
    for model in ["quadratic_metric", "radial_link"]:
        rows = calibration[model]
        ax.plot([r["predicted"] for r in rows], [r["observed"] for r in rows], "o-", color=colors[model], label=labels[model])
    ax.plot([0, .6], [0, .6], "--", color="gray", linewidth=1)
    ax.set(title="B  Internal OOF calibration (descriptive bins)", xlabel="Mean predicted probability", ylabel="Observed connection-label fraction", xlim=(0, .6), ylim=(0, .6))
    ax.legend(frameon=False, fontsize=8)

    ax = axes[1, 0]
    rows = distance_bins["quadratic_metric"]
    ax.plot([r["mean_x"] for r in rows], [r["observed"] for r in rows], "ko-", label="Observed labels", linewidth=1.5)
    for model in ["no_distance", "quadratic_metric", "radial_link"]:
        values = distance_bins[model]
        ax.plot([r["mean_x"] for r in values], [r["predicted"] for r in values], "s--", color=colors[model], label=labels[model], markersize=4)
    for row in rows:
        ax.annotate(f'n={row["n"]:,}', (row["mean_x"], row["observed"]), xytext=(0, 10), textcoords="offset points", ha="center", fontsize=7)
    ax.set(title="C  Distance bins retain their cell-context mixtures", xlabel="Mean nominal 3D soma distance (um)", ylabel="Connection-label fraction", ylim=(-.01, .26))
    ax.legend(frameon=False, fontsize=8)

    ax = axes[1, 1]
    scales = [r["metric"]["length_scale_um"] for r in quadratic]
    ax.plot(range(5), scales, "o-", color=colors["quadratic_metric"])
    for row, scale in zip(quadratic, scales):
        ax.annotate(f'beta={row["metric"]["beta"]:.4f}', (row["fold"], scale), xytext=(0, 12), textcoords="offset points", ha="center", fontsize=8)
    ax.set(title="D  Conditional isotropic scale, g = beta I / (100 um)^2", xlabel="Held-out donor fold (fit uses other four)", ylabel="Model scale 100 / sqrt(beta) (um)", ylim=(168, 183))
    ax.set_xticks(range(5))
    ax.text(.03, .10, "Flatness and isotropy are imposed.\nPositive beta does not identify 3D anisotropy.\nThis scale is not an axon length or a power cost.", transform=ax.transAxes, fontsize=9)

    fig.suptitle("Fixed 3D neurons and chemical connection labels\n28,616 directed pairs | 1,036 specimen-name donor IDs | 5-fold internal evaluation", fontsize=15, y=.985)
    fig.text(.5, .018, "Nominal local domain <= 1 mm. OOF = out of fold. No external validation, hormone measurement, or causal metric identification.\nBoth squared-distance and distance links can use a Riemannian metric; the comparison tests the probability link.", ha="center", fontsize=9)
    fig.tight_layout(rect=[0, .07, 1, .935], h_pad=2.6, w_pad=2.0)
    fig.savefig(outputs[1], dpi=180)
    fig.savefig(outputs[2])
    plt.close(fig)
    print(json.dumps(dict(geometry=geometry_summary, relative_log_loss_reduction=summary["quadratic_relative_log_loss_reduction"], output_paths=[str(p) for p in outputs])))


if __name__ == "__main__":
    main()
