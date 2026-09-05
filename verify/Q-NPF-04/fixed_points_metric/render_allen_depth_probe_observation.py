"""Render frozen retrospective observation-model comparisons."""
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE=Path(__file__).resolve().parent


def main():
    x=json.loads((HERE/"allen_depth_probe_observation_result.json").read_text())
    scores={r["model"]:r for r in x["summary"]["scores"]}
    plt.rcParams.update({"font.family":"DejaVu Sans","font.size":10,"axes.spines.top":False,"axes.spines.right":False,"svg.fonttype":"none"})
    fig,axes=plt.subplots(1,2,figsize=(12,5.4),gridspec_kw={"width_ratios":[1.25,1]})
    groups=[("context","radial"),("depth_context","depth_radial"),("depth_count_context","depth_count_radial")]
    labels=["Context only","+ Cut-surface depth","+ Depth and final count"]
    color0="#77818a";color1="#157f86"
    for i,(plain,radial) in enumerate(groups):
        a=scores[plain]["log_loss"];b=scores[radial]["log_loss"]
        axes[0].plot([b,a],[i,i],color="#bcc5cc",lw=3,zorder=1)
        axes[0].scatter([a],[i],s=55,color=color0,label="Without distance" if i==0 else None,zorder=3)
        axes[0].scatter([b],[i],s=65,color=color1,label="With radial distance" if i==0 else None,zorder=3)
        axes[0].text(a+.0003,i+.14,f"{a:.6f}",ha="right",fontsize=9,color=color0)
        axes[0].text(b-.0003,i-.13,f"{b:.6f}",ha="left",fontsize=9,color=color1)
        comparison=next(r for r in x["comparisons"] if r["candidate"]==radial and r["reference"]==plain)
        v=comparison["log_loss_difference"];mean=-v["pair_weighted_mean"]
        lo,hi=-np.array(v["pair_weighted_cluster_percentile95"])[::-1]
        axes[1].errorbar(mean,i,xerr=[[mean-lo],[hi-mean]],fmt="o",color=color1,capsize=4,ms=7)
        axes[1].text(mean,i-.17,f"{mean:.6f}",ha="center",fontsize=9)
    axes[0].set(yticks=range(3),yticklabels=labels,xlabel="Out-of-fold log loss (lower is better)",xlim=(.274,.297),ylim=(2.5,-.65))
    axes[0].set_title("Same 28,616 pairs / 1,036 donors",loc="left",fontweight="bold")
    axes[0].legend(loc="upper right",fontsize=8,frameon=False)
    axes[1].set(yticks=range(3),yticklabels=["No summaries","Depth","Depth + count"],xlabel="Log-loss reduction from adding distance",xlim=(0,.012),ylim=(2.5,-.65))
    axes[1].set_title("Distance retains predictive value",loc="left",fontweight="bold")
    axes[1].axvline(0,color="#a8aeb4",ls=":")
    for ax in axes:ax.grid(axis="x",alpha=.15)
    fig.suptitle("Fixed neuron positions: acquisition summaries and connection labels",x=.055,ha="left",fontsize=14,fontweight="bold")
    fig.text(.055,.07,"Intervals: 2,000 donor resamples of fixed out-of-fold predictions; models were not refit.\nFinal counts are retrospective. This does not identify detection sensitivity or a biological metric.",fontsize=9,color="#45515b")
    fig.tight_layout(rect=(0,.14,1,.93),w_pad=2.8)
    for suffix in ["png","svg"]:
        path=HERE/("allen_depth_probe_observation."+suffix)
        if path.exists():raise FileExistsError(path)
        fig.savefig(path,dpi=180,facecolor="white")
        print(path.name,path.stat().st_size,hashlib.sha256(path.read_bytes()).hexdigest())
    plt.close(fig)


if __name__=="__main__":main()
