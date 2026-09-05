"""Observed repeat errors and the two directions with existing VC fit QC."""
from io import BytesIO
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE=Path(__file__).resolve().parent


def main():
    d=json.loads((HERE/"electrical_star_incoming_chemical_result.json").read_text())
    with np.load(HERE/"electrical_star_incoming_chemical_waveforms.npz",allow_pickle=False) as waves:
        values=waves["current_pA"]
        time=waves["time_ms"]
    plt.rcParams.update({"font.size":10,"axes.spines.top":False,"axes.spines.right":False,
                         "svg.hashsalt":"electrical-star-incoming-chemical-v1"})
    fig,axes=plt.subplots(3,2,figsize=(12,10.4),layout="constrained")
    models=[("pulse_specific","Pulse identity", "#4477AA"),
            ("pulse_pooled","Pulse pooled", "#228833"),
            ("negative_source","Negative source", "#CC6677"),
            ("shifted_time","Time shifted", "#AA3377")]
    for column,group in enumerate(["all_annotated","VC_QC_pass"]):
        ax=axes[0,column]
        for model,label,color in models:
            for b_index,block in enumerate(d["analysis"]):
                xs=[r["sweep"] for r in block["evaluation"]]
                ys=[r["groups"][group][model]["rmse_over_zero"] for r in block["evaluation"]]
                ax.plot(xs,ys,"o-",color=color,label=label if b_index==0 else None,lw=1.5,ms=4)
        ax.axhline(.8,color="black",ls="--",lw=1)
        ax.axhline(1,color="gray",ls=":",lw=1)
        ax.set(title="All five annotated directions" if column==0 else "VC-fit QC subset: sources 2 and 5",
               xlabel="Evaluation recording (2-4: -70 mV; 7-9: -55 mV)",ylabel="RMSE / zero-prediction RMSE")
        ax.set_xticks([2,3,4,7,8,9])
        if column==1: ax.set_yscale("log")
        ax.legend(frameon=False,fontsize=8,ncol=2)
    palette=["#EE7733","#009988","#CC3311"]
    for row,source in enumerate([2,5],start=1):
        index=d["sources"].index(source)
        for column,block in enumerate(d["analysis"]):
            ax=axes[row,column]
            train=values[block["train"],index].mean(axis=(0,1))
            displayed=[train]
            ax.plot(time,train,color="#333333",lw=1.8,label="Train mean (2 recordings)")
            for color,sweep in zip(palette,block["evaluate"]):
                curve=values[sweep,index].mean(axis=0)
                displayed.append(curve)
                ax.plot(time,curve,color=color,lw=1.1,alpha=.85,label=f"Record {sweep}")
            ax.axvspan(.5,15,color="#CCCCCC",alpha=.2)
            ax.axhline(0,color="gray",ls=":",lw=.8)
            ax.set(title=f"Source {source} to target 7; holding {block['holding_mV']} mV",
                   xlabel="Time from command offset (ms)",ylabel="Mean current across 12 pulses (pA)",xlim=(-3,20))
            shown=np.asarray(displayed)[:,(time>=-3)&(time<=20)]
            low,high=float(shown.min()),float(shown.max())
            pad=max(1.,.08*(high-low))
            ax.set_ylim(low-pad,high+pad)
            if row==1: ax.legend(frameon=False,fontsize=8)
    fig.suptitle("Incoming chemical-pair candidates: current repeatability, not conductance\n"
                 "Waveforms below average pulses for display; primary scores preserve all 12 pulse identities",fontsize=12)
    for ext in ["png","svg"]:
        output=HERE/("electrical_star_incoming_chemical."+ext)
        if output.exists(): raise FileExistsError(output)
        buffer=BytesIO()
        fig.savefig(buffer,format=ext,dpi=160,metadata={"Date":None} if ext=="svg" else None)
        with output.open("xb") as stream: stream.write(buffer.getvalue())
    plt.close(fig)


if __name__=="__main__": main()
