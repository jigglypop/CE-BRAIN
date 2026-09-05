"""Render frozen internal MICrONS prediction results; no refitting."""
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE=Path(__file__).resolve().parent


def main():
    result=json.loads((HERE/"microns_node_metric_schur_result.json").read_text(encoding="utf-8"))
    assert hashlib.sha256((HERE/"microns_node_metric_schur.py").read_bytes()).hexdigest()==result["code_sha256"]
    scores={r["model"]:r for r in result["summary"]["scores"]}
    fits={(r["block"],r["model"]):r for r in result["fits"]}
    fig,axes=plt.subplots(2,2,figsize=(12,8.5),layout="constrained")
    suffixes=["context","isotropic_quadratic","diagonal_quadratic","isotropic_radial"]
    names=["Context","Isotropic quadratic","Diagonal quadratic","Isotropic radial"]
    colors=["#75818a","#287aaf","#bc6246","#3b9272"]
    for ax,condition,title in zip(axes[0],["strategy","typed"],["A. Reconstruction metadata","B. Reconstruction + published cell type"]):
        selected=suffixes+(["signed_quadratic"] if condition=="typed" else [])
        labels=names+(["Signed quadratic"] if condition=="typed" else [])
        values=[scores[condition+"_"+s]["log_loss"] for s in selected]
        ax.barh(np.arange(len(values)),values,color=colors+(["#9562ab"] if condition=="typed" else []))
        ax.set_yticks(np.arange(len(values)),labels,fontsize=9)
        ax.invert_yaxis()
        ax.set_xlim(0,max(values)*1.23)
        ax.set_xlabel("Pooled held-out log loss (lower is better)")
        ax.set_title(title,loc="left",fontsize=11)
        for i,value in enumerate(values):ax.text(value+max(values)*.02,i,f"{value:.6f}",va="center",fontsize=9)
    ax=axes[1,0]
    for condition,style in [("strategy","-"),("typed","--")]:
        for candidate,color,short in [("diagonal_quadratic",colors[2],"Diagonal"),("isotropic_radial",colors[3],"Radial")]:
            match=next(r for r in result["comparisons"] if r["candidate"]==condition+"_"+candidate and r["reference"]==condition+"_isotropic_quadratic")
            ax.plot([r["block"] for r in match["block_differences"]],[r["log_loss_difference"] for r in match["block_differences"]],style,color=color,marker=".",label=short+" / "+condition)
    ax.axhline(0,color="black",linewidth=.8)
    ax.set(title="C. Shape and link differences within each block",xlabel="Held-out node-group block",ylabel="Log loss minus isotropic quadratic")
    ax.legend(fontsize=8)
    ax=axes[1,1]
    for condition,style in [("strategy","-"),("typed","--")]:
        beta=np.array([fits[b,condition+"_diagonal_quadratic"]["coefficients"] for b in range(15)])
        for i,(axis,color) in enumerate(zip("XYZ",["#287aaf","#bc6246","#3b9272"])):
            ax.plot(np.arange(15),beta[:,i],style,color=color,marker=".",label=axis+" / "+condition)
    ax.axhline(0,color="black",linewidth=.8)
    ax.set(title="D. Nonnegative diagonal cost coefficients",xlabel="Held-out node-group block",ylabel="Coefficient on (displacement / 100 um)^2")
    ax.legend(fontsize=8,ncol=2)
    for ax in axes[1]:ax.set_xticks([0,3,6,9,12,14])
    for ax in axes.flat:
        ax.spines[["top","right"]].set_visible(False)
        ax.grid(axis="x" if ax in axes[0] else "y",alpha=.15)
    fig.suptitle("1,348 fixed somata; 1,815,756 directed pairs; both test neurons excluded from training\nOne EM volume, observed annotations versus unlisted pairs; no independent-animal intervals",fontsize=12)
    for ext in ["png","svg"]:
        path=HERE/("microns_node_metric."+ext)
        if path.exists():raise FileExistsError(path)
        fig.savefig(path,dpi=180)
        print(path.name)
    plt.close(fig)


if __name__=="__main__":main()
