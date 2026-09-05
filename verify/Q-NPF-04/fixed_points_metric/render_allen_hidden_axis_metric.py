"""Visualize frozen hidden-axis fits, OOF comparisons and training profiles."""
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE=Path(__file__).resolve().parent
STEM="allen_hidden_axis_metric"


def main():
    paths=[HERE/(STEM+s) for s in [".png",".svg"]]
    if any(p.exists() for p in paths):
        raise FileExistsError("Completed figures are immutable")
    r=json.loads((HERE/(STEM+"_result.json")).read_text(encoding="utf-8"))
    assert hashlib.sha256((HERE/(STEM+".py")).read_bytes()).hexdigest()==r["code_sha256"]
    plt.rcParams.update({"font.size":10,"axes.spines.top":False,"axes.spines.right":False,"svg.fonttype":"none"})
    fig,axes=plt.subplots(2,2,figsize=(12.8,9.5))
    colors={0:"#146aa2",1:"#ce6c20",2:"#348965",3:"#8b52a0",4:"#bc414d"}

    ax=axes[0,0]
    choices=[("z_radial","radial_link","Z split: radial"),("x_radial","radial_link","X split: radial"),
             ("y_radial","radial_link","Y split: radial"),("z_quadratic","quadratic_metric","Z split: squared"),
             ("x_quadratic","quadratic_metric","X split: squared"),("y_quadratic","quadratic_metric","Y split: squared"),
             ("z_radial","z_plane_radial","Z split vs XY only")]
    for i,(candidate,reference,label) in enumerate(choices):
        c=next(v for v in r["comparisons"] if v["candidate"]==candidate and v["reference"]==reference)["log_loss_difference"]
        mean=c["pair_weighted_mean"]*1e4;left,right=np.array(c["pair_weighted_cluster_percentile95"])*1e4
        ax.errorbar(mean,i,xerr=[[mean-left],[right-mean]],fmt="o",color="#176ba0" if i<3 or i==6 else "#c56b20",capsize=3)
    ax.axvline(0,color="black",linewidth=.8)
    ax.set_yticks(range(len(choices)),[v[2] for v in choices]);ax.invert_yaxis()
    ax.set(title="A  Axis-specific costs show no clear OOF gain",xlabel="Log-loss difference x 10,000 (negative is better)")

    ax=axes[0,1]
    scores={(v["model"],v["fold"]):v["log_loss"] for v in r["fold_scores"]}
    for reference,label,color in [("radial_link","Versus isotropic 3D distance","#176ba0"),("z_plane_radial","Versus XY-only boundary","#c56b20")]:
        difference=[(scores["z_radial",f]-scores[reference,f])*1e4 for f in range(5)]
        ax.plot(range(5),difference,"o-",label=label,color=color)
    ax.axhline(0,color="black",linewidth=.8)
    ax.set_xticks(range(5));ax.set(title="B  Z-split radial model: fold-specific differences",xlabel="Held-out donor fold",ylabel="Log-loss difference x 10,000")
    ax.legend(frameon=False,fontsize=8)

    ax=axes[1,0]
    for p in r["radial_profiles"]:
        if p["axis"]!=2:continue
        ax.plot([v["w"] for v in p["profile"]],[v["delta_penalized_sum"] for v in p["profile"]],color=colors[p["fold"]],label=f'Fit excluding fold {p["fold"]}')
        ax.plot(p["w"],0,"o",color=colors[p["fold"]],markersize=4)
    ax.set_yscale("symlog",linthresh=1.)
    ax.axvline(.5,color="gray",linestyle=":",linewidth=.8)
    ax.set(title="C  Training profiles include both exact boundaries",xlabel="Shape weight w: 0 = XY only, 0.5 = isotropic, 1 = Z only",ylabel="Penalized training loss sum above fitted minimum",xlim=(-.02,1.02))
    ax.legend(frameon=False,fontsize=8,loc="upper left")

    ax=axes[1,1]
    radial=sorted([v for v in r["fits"] if v["model"]=="z_radial"],key=lambda v:v["fold"])
    quadratic=sorted([v for v in r["fits"] if v["model"]=="z_quadratic"],key=lambda v:v["fold"])
    ax.plot(range(5),[v["metric"]["axis_to_plane_ratio"] for v in radial],"o-",color="#176ba0",label="Radial probability link")
    ax.plot(range(5),[v["coefficients"][1]/v["coefficients"][0] for v in quadratic],"s--",color="#c56b20",label="Squared-distance probability link")
    ax.axhline(1,color="gray",linestyle=":",linewidth=.8,label="Isotropic ratio")
    ax.set_xticks(range(5));ax.set(ylim=(0,1.12),title="D  Positive fitted ratios vary across training sets",xlabel="Excluded donor fold",ylabel="Metric coefficient ratio: raw Z / raw XY")
    ax.legend(frameon=False,fontsize=8,loc="upper right")

    fig.suptitle("Can connection labels identify the hidden 3D cost component?\n28,616 fixed neuron pairs | 1,036 donor IDs | reused internal folds",fontsize=15,y=.985)
    fig.text(.5,.021,"A: 95% percentile ranges from resampling donors with fixed OOF predictions; no model refitting or external confirmation.\nC: training profiles are not confidence intervals. Raw coordinate axes are not measured cortical normals.",ha="center",fontsize=9)
    fig.tight_layout(rect=[0,.07,1,.935],w_pad=2.8,h_pad=2.8)
    for path in paths:fig.savefig(path,dpi=180)
    plt.close(fig)
    print(json.dumps({"figures":[str(p) for p in paths]}))


if __name__=="__main__":main()
