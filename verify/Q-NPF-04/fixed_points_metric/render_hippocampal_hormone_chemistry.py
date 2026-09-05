"""Export formal hormone-model examples, not observed brain effects."""
import json
from io import BytesIO
from pathlib import Path
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE = Path(__file__).resolve().parent


def main():
    data = json.loads((BASE / "hippocampal_hormone_chemistry_result.json").read_text(encoding="utf-8"))
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False,
                         "svg.hashsalt": "hippocampal-hormone-chemistry-v1"})
    fig, axes = plt.subplots(1, 3, figsize=(12.4, 3.9), layout="constrained")
    kinetics = data["kinetics_synthetic"]
    for key, label, color in [("slow_fraction", "Slow binding", "#4477AA"),
                               ("fast_fraction", "Fast binding", "#CC6677")]:
        axes[0].plot(kinetics["time_min"], kinetics[key], label=label, color=color, lw=2)
    axes[0].axhline(.5, color="gray", ls="--", lw=1)
    axes[0].set(title="Same equilibrium, different timing", xlabel="Time (min)",
                ylabel="Receptor occupancy", ylim=(0, .56))
    axes[0].legend(frameon=False, loc="lower right")
    receptor = data["opposing_receptor_synthetic"]
    axes[1].semilogx(receptor["dose_nM"], receptor["effect_arbitrary_units"], color="#228833", lw=2)
    axes[1].axvline(10, color="gray", ls="--", lw=1)
    axes[1].set(title="Two receptor pools, opposing gains", xlabel="Free ligand (nM)",
                ylabel="Illustrative net effect (a.u.)", ylim=(0, .9))
    ratios = data["fixed_points_synthetic"]["axis_cost_ratios_after_before"]
    axes[2].bar(["x", "y", "z"], ratios, color=["#4477AA", "#CC6677", "#228833"], width=.55)
    axes[2].axhline(1, color="gray", ls="--", lw=1)
    axes[2].set(title="Fixed points, changed conductances", xlabel="Current-moment direction",
                ylabel="Cost after / before", ylim=(0, 2.4))
    for x, value in enumerate(ratios):
        axes[2].text(x, value+.05, f"{value:g}", ha="center")
    fig.suptitle("FORMAL EXAMPLES (L0) — parameters and conductance changes are synthetic", fontsize=12)
    output_folder = Path(sys.argv[1]) if len(sys.argv) > 1 else BASE
    for suffix in ["png", "svg"]:
        buffer = BytesIO()
        fig.savefig(buffer, format=suffix, dpi=180,
                    metadata={"Date": None} if suffix == "svg" else None)
        output = output_folder / ("hippocampal_hormone_chemistry."+suffix)
        payload = buffer.getvalue()
        if output.exists():
            if output.read_bytes() != payload:
                raise FileExistsError("Existing figure differs; specify a new output folder")
        else:
            with output.open("xb") as stream:
                stream.write(payload)
    plt.close(fig)


if __name__ == "__main__":
    main()
