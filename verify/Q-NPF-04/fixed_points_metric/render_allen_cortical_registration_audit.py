"""Plot frozen coordinate audit and conditional 3D metric completions."""
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent
STEM = "allen_cortical_registration_audit"


def main():
    paths = [HERE/(STEM+suffix) for suffix in [".png", ".svg"]]
    if any(p.exists() for p in paths):
        raise FileExistsError("Completed figures are immutable")
    result = json.loads((HERE/(STEM+"_result.json")).read_text(encoding="utf-8"))
    assert hashlib.sha256((HERE/(STEM+".py")).read_bytes()).hexdigest() == result["code_sha256"]
    common = [r for r in result["experiments"] if all(v["all_loo_identifiable"] for v in r["models"].values())]
    example = next(r for r in common if r["experiment_id"] == 2771)
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False, "svg.fonttype": "none"})
    fig, axes = plt.subplots(2, 2, figsize=(12.6, 9.7))
    colors = {"centroid":"#888888", "xy_similarity":"#176ba0", "xy_affine":"#31976a", "xyz_affine":"#c36720"}
    labels = {"centroid":"Centroid", "xy_similarity":"XY similarity", "xy_affine":"XY affine", "xyz_affine":"3D affine"}
    ax = axes[0,0]
    for model in result["settings"]["model_names"]:
        errors = np.sort(np.concatenate([r["models"][model]["loo_error_um"] for r in common]))
        ax.plot(errors,np.arange(1,len(errors)+1)/len(errors),color=colors[model],label=labels[model])
    ax.set(xscale="log", xlabel="Held-out cell image-position error (um)", ylabel="Fraction of cells", title="A  A simpler XY map predicts the image coordinates")
    ax.legend(frameon=False,fontsize=9)
    ax.axvline(1,color="gray",linestyle=":",linewidth=.8)

    ax = axes[0,1]
    x = [r["models"]["xy_similarity"]["loo_rmse_um"] for r in common]
    y = [r["models"]["xyz_affine"]["loo_rmse_um"] for r in common]
    ax.scatter(x,y,s=10,alpha=.35,color="#176ba0")
    ax.plot([.008,300],[.008,300],"k--",linewidth=.8)
    ex = example["models"]["xy_similarity"]["loo_rmse_um"]
    ey = example["models"]["xyz_affine"]["loo_rmse_um"]
    ax.scatter([ex],[ey],color="#ba3040",s=50,zorder=4)
    ax.annotate("Experiment 2771",(ex,ey),xytext=(-95,30),textcoords="offset points",arrowprops={"arrowstyle":"-","color":"#ba3040"},fontsize=9)
    ax.set(xscale="log",yscale="log",xlabel="XY similarity: cell LOO RMSE (um)",ylabel="3D affine: cell LOO RMSE (um)",title="B  Comparison on the same 1,270 experiments")

    ax = axes[1,0]
    depth = [r for r in common if r["depth"].get("max_loo_angle_deg") is not None]
    angles = np.sort([r["depth"]["max_loo_angle_deg"] for r in depth])
    ax.plot(angles,np.arange(1,len(angles)+1)/len(angles),color="#7050a0")
    ax.set(xlim=(0,180),ylim=(0,1.03),xlabel="Maximum LOO-to-full gradient angle (degrees)",ylabel="Fraction of experiments",title="C  Stability of a fitted, stored-depth gradient")
    ax.text(.39,.40,"1,221 experiments\nMedian maximum angle: 3.01 deg\n95th percentile: 43.00 deg\n\nNot an independent 3D pia normal",transform=ax.transAxes,fontsize=9)

    ax = axes[1,1]
    # Section through the first visible singular vector and the image-map null direction.
    s = example["pullback"]["image_map_singular_values"][0]
    theta = np.linspace(0,2*np.pi,400)
    for weight,color in [(.25,"#176ba0"),(4.,"#c36720")]:
        ax.plot(100/s*np.cos(theta),100/np.sqrt(weight)*np.sin(theta),color=color,label=f"Completion weight = {weight}")
    ax.axhline(0,color="gray",linewidth=.7);ax.axvline(0,color="gray",linewidth=.7)
    ax.set_aspect("equal",adjustable="box")
    ax.set(xlabel="Displacement in one visible direction (um)",ylabel="Displacement in hidden direction (um)",title="D  Same image map, different candidate 3D costs")
    ax.legend(frameon=False,fontsize=8,loc="upper right",bbox_to_anchor=(1.45,1.02))
    ax.text(.02,.025,"q = 1 sections; conditional fit from experiment 2771\nNeither curve is a measured biological cost",transform=ax.transAxes,fontsize=8)

    fig.suptitle("3D soma coordinates and 2D cortical images\nCoordinate correspondence does not determine the missing 3D metric component",fontsize=15,y=.985)
    fig.text(.5,.022,"LOO = leave one cell out. Exploratory domain: 3D span <= 1 mm, 2D span <= 2 mm, >= 5 matched cells.\nNo connection labels were queried. Image-field accuracy and independence are not established by small LOO errors.",ha="center",fontsize=9)
    fig.tight_layout(rect=[0,.065,1,.935],h_pad=2.8,w_pad=2.3)
    for path in paths:
        fig.savefig(path,dpi=180)
    plt.close(fig)
    print(json.dumps({"figures":[str(p) for p in paths]}))


if __name__ == "__main__":
    main()
