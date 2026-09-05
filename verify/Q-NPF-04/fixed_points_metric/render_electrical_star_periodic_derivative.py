"""Show all derivative-model comparisons without treating development as confirmation."""
from io import BytesIO
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm
import numpy as np

HERE=Path(__file__).resolve().parent


def main():
    outputs=[HERE/("electrical_star_periodic_derivative."+ext) for ext in ["png","svg"]]
    for path in outputs:
        if path.exists():raise FileExistsError(path)
    data=json.loads((HERE/"electrical_star_periodic_derivative_result.json").read_text())
    plt.rcParams.update({"font.size":10,"axes.spines.top":False,"axes.spines.right":False,
                         "svg.hashsalt":"electrical-star-periodic-derivative-v1"})
    fig,axes=plt.subplots(2,2,figsize=(11.5,7.7),layout="constrained")
    models=[("current_only","Current only","#4477AA"),("derivative_only","Derivative only","#CC3377"),
            ("current_and_derivative","Current + derivative","#228833")]
    devices=[0,1,2,4,5,6]
    for column,block in enumerate(data["analysis"]):
        ax=axes[0,column]
        for model,label,color in models:
            rows=[r for r in data["pooled"] if r["holding_mV"]==block["holding_mV"] and r["model"]==model and r["subset"]=="both_windows_clear"]
            ax.plot([r["sweep"] for r in rows],[r["RMSE_over_zero"] for r in rows],"o-",color=color,label=label)
        ax.axhline(1,color="black",ls=":",lw=1)
        ax.set(title=f"{'A' if column==0 else 'B'}. Six other channels pooled, {block['holding_mV']} mV",xlabel="Evaluation record",ylabel="RMSE / zero RMSE",xticks=block["evaluate"])
        ax.legend(frameon=False,fontsize=8)
        ax=axes[1,column]
        rows={(r["device"],r["sweep"]):r for r in block["evaluation"] if r["model"]=="derivative_only" and r["subset"]=="both_windows_clear"}
        values=np.array([[rows[d,s]["actual"]["RMSE_over_zero"] for s in block["evaluate"]] for d in devices])
        ax.imshow(values,aspect="auto",cmap="RdBu_r",norm=TwoSlopeNorm(1,vmin=.90,vmax=1.10))
        for i in range(6):
            for j in range(3):ax.text(j,i,f"{values[i,j]:.4f}",ha="center",va="center",fontsize=9)
        ax.set(title=f"{'C' if column==0 else 'D'}. Derivative-only model: all six channels",xlabel="Evaluation record",ylabel="Other channel",xticks=range(3),xticklabels=block["evaluate"],yticks=range(6),yticklabels=devices)
    fig.suptitle("Current-change basis: post-plot development comparison\nSmall channel delays and filters can also create derivative terms; neither coefficient is conductance",fontsize=12)
    for path in outputs:
        ext=path.suffix[1:];buffer=BytesIO()
        fig.savefig(buffer,format=ext,dpi=160,metadata={"Date":None} if ext=="svg" else None)
        with path.open("xb") as stream:stream.write(buffer.getvalue())
    plt.close(fig)


if __name__=="__main__":main()
