"""Render the frozen radial direction/observation comparison without refitting."""
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE=Path(__file__).resolve().parent
RESULT=HERE/"microns_radial_direction_observation_result.json"


def main():
    result=json.loads(RESULT.read_text(encoding="utf-8"))
    source=HERE/"microns_radial_direction_observation.py"
    assert hashlib.sha256(source.read_bytes()).hexdigest()==result["code_sha256"]
    scores={row["model"]:row for row in result["summary"]["scores"]}
    comparisons={(row["candidate"],row["reference"]):row for row in result["comparisons"]}
    fig,axes=plt.subplots(2,2,figsize=(12,8.2),layout="constrained")
    suffixes=["common_isotropic","common_directional","stratum_isotropic","stratum_directional"]
    labels=["Common / isotropic","Common / directional","Stratum gain / isotropic","Stratum gain / directional"]
    colors=["#75818a","#bc6246","#3b9272","#7655a5"]
    for ax,prefix,title in zip(axes[0],["strategy","typed"],["A. Reconstruction metadata","B. Reconstruction + published cell type"]):
        values=[scores[prefix+"_"+suffix]["log_loss"] for suffix in suffixes]
        ax.barh(np.arange(4),values,color=colors)
        ax.set_yticks(np.arange(4),labels,fontsize=9);ax.invert_yaxis()
        ax.set_xlim(0,max(values)*1.25);ax.set_xlabel("Pooled held-out log loss")
        ax.set_title(title,loc="left",fontsize=11)
        for i,value in enumerate(values):ax.text(value+max(values)*.018,i,f"{value:.6f}",va="center",fontsize=9)
    ax=axes[1,0]
    specs=[("common_directional","common_isotropic","Directional shape | common gain","#bc6246"),
           ("stratum_isotropic","common_isotropic","Stratum gain | isotropic","#3b9272"),
           ("stratum_directional","stratum_isotropic","Directional shape | stratum gain","#7655a5")]
    for prefix,style in [("strategy","-"),("typed","--")]:
        for candidate,reference,label,color in specs:
            row=comparisons[(prefix+"_"+candidate,prefix+"_"+reference)]
            ax.plot(range(15),[x["log_loss_difference"] for x in row["block_differences"]],style,marker=".",color=color,label=label+" / "+prefix)
    ax.axhline(0,color="black",linewidth=.8)
    ax.set(title="C. Held-out differences by node block",xlabel="Held-out node-group block",ylabel="Candidate minus reference log loss")
    ax.legend(fontsize=7,ncol=2)
    ax=axes[1,1]
    for prefix,style in [("strategy","-"),("typed","--")]:
        rows=[row for row in result["fits"] if row["model"]==prefix+"_common_directional"]
        weights=np.array([row["cost"]["shape_diagonal"] for row in rows])
        ax.plot(range(15),weights[:,0],style,marker=".",color="#287aaf",label="X/Y / "+prefix)
        ax.plot(range(15),weights[:,2],style,marker=".",color="#bc6246",label="Z/Y / "+prefix)
    ax.axhline(1,color="black",linewidth=.8)
    ax.set(title="D. Training-selected positive direction ratios",xlabel="Held-out node-group block",ylabel="Shape weight ratio (Y fixed to 1)")
    ax.legend(fontsize=8,ncol=2)
    for ax in axes[1]:ax.set_xticks([0,3,6,9,12,14])
    for ax in axes.flat:
        ax.spines[["top","right"]].set_visible(False);ax.grid(alpha=.15)
    fig.suptitle("Same 1,348 fixed somata and 15 endpoint-held-out blocks\nDirection shape versus reconstruction-stratum observation attenuation",fontsize=12)
    for extension in ["png","svg"]:
        target=HERE/("microns_radial_direction_observation."+extension)
        if target.exists():raise FileExistsError(target)
        fig.savefig(target,dpi=180);print(target.name)
    plt.close(fig)


if __name__=="__main__":main()
