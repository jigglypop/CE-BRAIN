"""Plot all fixed channels and report the command-clear development comparison."""
from io import BytesIO
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm
import numpy as np

from electrical_star_periodic_channel_association import center_windows,PRIMARY,DEVICES

HERE=Path(__file__).resolve().parent


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def summarize(data):
    counts=[];pooled=[]
    for sweep in range(10):
        events=[e for e in data["events"] if e["sweep"]==sweep]
        counts.append(dict(sweep=sweep,total=len(events),
            actual_clear=sum(e["actual_window_command_clear"] for e in events),
            control_clear=sum(e["control_window_command_clear"] for e in events),
            both_clear=sum(e["both_windows_command_clear"] for e in events),
            actual_recorded_command_changes=sum(max(e["actual_command_range_mV"])>1e-9 for e in events),
            control_recorded_command_changes=sum(max(e["control_command_range_mV"])>1e-9 for e in events)))
    for block in data["analysis"]:
        for subset in ["both_windows_clear","all_catalogue_background"]:
            for sweep in block["evaluate"]:
                rows=[r for r in block["evaluation"] if r["subset"]==subset and r["sweep"]==sweep]
                # Same event count and time-bin count in all six channel rows.
                mse0=sum(r["actual"]["zero_RMSE_pA"]**2 for r in rows)/6
                mse=sum(r["actual"]["RMSE_pA"]**2 for r in rows)/6
                gain=mse0-mse
                shifted_gain=np.mean([r["shifted_other_channel"]["gain_over_zero_pA2"] for r in rows])
                pooled.append(dict(holding_mV=block["holding_mV"],sweep=sweep,subset=subset,n_events=rows[0]["n_events"],
                    zero_RMSE_pA=float(np.sqrt(mse0)),RMSE_pA=float(np.sqrt(mse)),RMSE_over_zero=float(np.sqrt(mse/mse0)),
                    gain_over_zero_pA2=float(gain),actual_gain_minus_shifted_gain_pA2=float(gain-shifted_gain)))
    primary=[r for b in data["analysis"] for r in b["evaluation"] if r["subset"]=="both_windows_clear"]
    return dict(counts=counts,pooled=pooled,
        individual_RMSE_over_zero_range=[min(r["actual"]["RMSE_over_zero"] for r in primary),max(r["actual"]["RMSE_over_zero"] for r in primary)],
        aggregation="Six other channels pooled by squared error; target is not scored. No p-value or new mechanistic gate.")


def heatmap(ax,values,title,center):
    low=min(float(np.min(values)),center-1e-6);high=max(float(np.max(values)),center+1e-6)
    span=max(center-low,high-center)
    im=ax.imshow(values,aspect="auto",cmap="RdBu_r",norm=TwoSlopeNorm(center,vmin=center-span,vmax=center+span))
    ax.set(title=title,xticks=range(6),xticklabels=[2,3,4,7,8,9],yticks=range(6),yticklabels=DEVICES[:-1],xlabel="Evaluation record",ylabel="Other channel")
    for row in range(6):
        for column in range(6):
            ax.text(column,row,f"{values[row,column]:.3f}" if center==1 else f"{values[row,column]:.2f}",ha="center",va="center",fontsize=8,color="black")
    return im


def main():
    outputs=[HERE/("electrical_star_periodic_channel_association."+ext) for ext in ["png","svg"]]
    summary_path=HERE/"electrical_star_periodic_channel_summary.json"
    for path in outputs+[summary_path]:
        if path.exists():raise FileExistsError(path)
    source=HERE/"electrical_star_periodic_channel_association_result.json"
    data=json.loads(source.read_text());summary=summarize(data)
    summary.update(source_sha256=digest(source),renderer_sha256=digest(Path(__file__)))
    wave_path=HERE/"electrical_star_periodic_channel_windows.npz"
    assert digest(wave_path)==data["raw_windows_sha256"]
    with np.load(wave_path,allow_pickle=False) as waves:
        raw_values=waves["raw_current"];time=waves["time_ms"]
    by_sweep={r["sweep"]:r for r in data["metadata"]}
    conversion=np.array([[d["conversion"] for d in by_sweep[e["sweep"]]["acquisition"]] for e in data["events"]])[...,None]
    offset=np.array([[d["offset"] for d in by_sweep[e["sweep"]]["acquisition"]] for e in data["events"]])[...,None]
    actual,_=center_windows(raw_values,conversion,offset)
    plt.rcParams.update({"font.size":10,"axes.spines.top":False,"axes.spines.right":False,
                         "svg.hashsalt":"electrical-star-periodic-channel-association-v1"})
    fig,axes=plt.subplots(3,2,figsize=(12.5,10.5),layout="constrained")
    ax=axes[0,0]
    ax.bar(np.arange(10),[r["total"] for r in summary["counts"]],color="#CCCCCC",label="All 84 catalogue events")
    ax.bar(np.arange(10),[r["both_clear"] for r in summary["counts"]],color="#4477AA",label="Both windows command-clear (54)")
    ax.set(title="A. Window eligibility fixed from recorded commands",xlabel="Record",ylabel="Event count",xticks=range(10))
    ax.legend(frameon=False,fontsize=8)
    ax=axes[0,1]
    for index,(block,color) in enumerate(zip(data["analysis"],["#4477AA","#CC3377"])):
        ax.bar(np.arange(6)+(index-.5)*.35,[block["coefficients_by_device"][str(d)]*100 for d in DEVICES[:-1]],width=.33,color=color,label=f"{block['holding_mV']} mV, n={block['training_events']}")
    ax.axhline(0,color="black",lw=.7)
    ax.set(title="B. Coefficients fitted in two earlier records",xlabel="Other channel",ylabel="Other / target current coefficient (%)",xticks=range(6),xticklabels=DEVICES[:-1])
    ax.legend(frameon=False,fontsize=8)
    palette=["#4477AA","#EE7733","#228833","#CC3377","#66CCEE","#AA3377"]
    for column,block in enumerate(data["analysis"]):
        ax=axes[1,column]
        selected=np.array([e["sweep"] in block["evaluate"] and e["both_windows_command_clear"] for e in data["events"]])
        means=actual[selected].mean(axis=0)
        for c,(device,color) in enumerate(zip(DEVICES[:-1],palette)):
            ax.plot(time,means[c],color=color,lw=1,label=f"Channel {device}")
        target_axis=ax.twinx()
        target_axis.plot(time,means[-1]/1000,color="black",ls="--",lw=1.5,label="Target 7 (right scale)")
        target_axis.set_ylabel("Target mean current (nA)")
        ax.axvspan(-.5,4,color="gray",alpha=.1)
        ax.set(title=f"{'C' if column==0 else 'D'}. Evaluation means: {block['holding_mV']} mV, {sum(selected)} events",xlabel="Time from observed target peak (ms)",ylabel="Other-channel mean current (pA)",xlim=(-2,6))
        ax.legend(frameon=False,fontsize=7,ncol=3,loc="lower left")
        target_axis.legend(frameon=False,fontsize=7,loc="upper right")
    rows=[r for b in data["analysis"] for r in b["evaluation"] if r["subset"]=="both_windows_clear"]
    lookup={(r["sweep"],r["device"]):r for r in rows}
    ratios=np.array([[lookup[s,d]["actual"]["RMSE_over_zero"] for s in [2,3,4,7,8,9]] for d in DEVICES[:-1]])
    gains=np.array([[lookup[s,d]["actual_gain_minus_shifted_gain_pA2"] for s in [2,3,4,7,8,9]] for d in DEVICES[:-1]])
    heatmap(axes[2,0],ratios,"E. Concurrent prediction RMSE / zero RMSE",1)
    heatmap(axes[2,1],gains,"F. Actual gain minus shifted-channel gain (pA squared)",0)
    fig.suptitle("Periodic-current candidates: simultaneous channel association\nFixed target timing; no evaluation refit; coefficients do not identify causal transmission",fontsize=12)
    for path in outputs:
        ext=path.suffix[1:];buffer=BytesIO()
        fig.savefig(buffer,format=ext,dpi=160,metadata={"Date":None} if ext=="svg" else None)
        with path.open("xb") as stream:stream.write(buffer.getvalue())
    plt.close(fig)
    with summary_path.open("x",encoding="utf-8") as stream:
        json.dump(summary,stream,indent=2,allow_nan=False);stream.write("\n")


if __name__=="__main__":main()
