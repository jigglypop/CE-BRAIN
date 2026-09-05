"""Descriptive summaries and plots; no event removal or revised predictive gate."""
from io import BytesIO
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE=Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def summarize(data):
    rates=[];intervals=[];overlap=[]
    for holding in [-70,-55]:
        records=[r for r in data["records"] if r["holding_mV"]==holding]
        for threshold in ["500","1000"]:
            for name,codes in [("Background",[0]),("Post command",[10,11,12,14,15,16]),
                               ("Transition",[2]),("Other nearby",[1])]:
                rows=[t for r in records for t in r["thresholds"][threshold]["rates"] if t["category"] in codes]
                count=sum(t["peak_count"] for t in rows);duration=sum(t["exposure_s"] for t in rows)
                rates.append(dict(holding_mV=holding,threshold_pA=int(threshold),category=name,
                    peaks=count,exposure_s=duration,peaks_per_s=count/duration))
        delta=np.concatenate([np.diff([e["time_s"] for e in r["thresholds"]["500"]["events"]]) for r in records])
        events=[e for r in records for e in r["thresholds"]["500"]["events"]]
        intervals.append(dict(holding_mV=holding,total_within_record_intervals=len(delta),
            within_1ms_of_1p2s=int(np.sum(abs(delta-1.2)<=.001)),
            within_2ms_of_p6s=int(np.sum(abs(delta-.6)<=.002)),
            period_choices_are_post_hoc=True,
            amplitude_min_median_max_pA=np.quantile([e["inward_amplitude_pA"] for e in events],[0,.5,1]).tolist(),
            width_min_median_max_ms=np.quantile([e["half_prominence_width_ms"] for e in events],[0,.5,1]).tolist()))
        rows=[r for r in data["error_overlap"]["rows"] if r["sweep"] in ([2,3,4] if holding==-70 else [7,8,9])]
        for sweep in sorted({r["sweep"] for r in rows})+[None]:
            selected=[r for r in rows if sweep is None or r["sweep"]==sweep]
            overlap.append(dict(holding_mV=holding,sweep=sweep,
                marked_time_fraction=float(np.mean([r["time_fraction"] for r in selected])),
                squared_error_fraction=sum(r["marked_squared_error_pA2"] for r in selected)/sum(r["total_squared_error_pA2"] for r in selected)))
    return dict(rates=rates,intervals=intervals,error_overlap=overlap,
        aggregation="Counts and exposures pooled; error fractions pooled by squared error. All rows have equal time bins.",
        claim_ceiling="Descriptive current observations and post-hoc diagnostics, not origin or metric identification")


def main():
    paths=[HERE/("electrical_star_background_events."+ext) for ext in ["png","svg"]]
    summary_path=HERE/"electrical_star_background_summary.json"
    for path in paths+[summary_path]:
        if path.exists():raise FileExistsError(path)
    source=HERE/"electrical_star_background_events_result.json"
    data=json.loads(source.read_text())
    summary=summarize(data)
    summary.update(source_sha256=sha(source),renderer_sha256=sha(Path(__file__)))
    plt.rcParams.update({"font.size":10,"axes.spines.top":False,"axes.spines.right":False,
                         "svg.hashsalt":"electrical-star-background-events-v1"})
    fig,axes=plt.subplots(3,2,figsize=(12,10.2),layout="constrained")
    ax=axes[0,0]
    palette={0:"#4477AA",1:"#999999",2:"#EE7733"}
    for record in data["records"]:
        for source_id,onset,offset in record["pulses"]:
            ax.plot([offset+.0005,offset+.015],[record["sweep"]]*2,color="#BBBBBB",lw=4,alpha=.35)
        for event in record["thresholds"]["500"]["events"]:
            ax.plot(event["time_s"],record["sweep"],"|",color=palette.get(event["category"],"#CC3377"),ms=10,mew=1.5)
    for label,color in [("Background","#4477AA"),("Post command","#CC3377"),("Transition","#EE7733"),("Other nearby","#999999")]:
        ax.plot([],[],"|",color=color,label=label,ms=8)
    ax.axhline(4.5,color="black",ls=":",lw=.8)
    ax.set(title="A. All 124 inward-current peaks (500 pA rule)",xlabel="Recorded time (s)",ylabel="Record: 0-4 = -70 mV; 5-9 = -55 mV",xlim=(0,7.04),yticks=range(10))
    ax.legend(frameon=False,ncol=2,fontsize=8,loc="upper left")
    ax.set_ylim(10.2,-.5)
    ax=axes[0,1]
    for j,(holding,threshold,color) in enumerate([(-70,500,"#4477AA"),(-70,1000,"#88CCEE"),(-55,500,"#CC3377"),(-55,1000,"#EE99AA")]):
        rows=[r for r in summary["rates"] if r["holding_mV"]==holding and r["threshold_pA"]==threshold]
        ax.bar(np.arange(4)+(j-1.5)*.19,[r["peaks_per_s"] for r in rows],width=.18,color=color,label=f"{holding} mV, {threshold} pA")
    ax.set(title="B. Counts divided by eligible observation time",ylabel="Detected peaks / s",xticks=range(4),xticklabels=["Background","Post\ncommand","Transition","Other\nnearby"])
    ax.legend(frameon=False,fontsize=8,ncol=2)
    for column,model in enumerate(data["morphology"]):
        ax=axes[1,column];holding=model["holding_mV"]
        sweeps=[2,3,4] if holding==-70 else [7,8,9]
        time=np.array(data["settings"]["shape_time_ms"])
        for category,color in [("background","#4477AA"),("post","#CC3377")]:
            chosen=[e for r in data["records"] if r["sweep"] in sweeps for e in r["thresholds"]["500"]["events"] if (e["category"]==0 if category=="background" else e["category"]>=10)]
            for index,event in enumerate(chosen):
                ax.plot(time,event["normalized_shape"],color=color,alpha=.35,lw=.8,label=f"Later {category} peaks (n={len(chosen)})" if index==0 else None)
        ax.plot(time,model["normalized_background_template"],color="black",lw=1.8,label="Earlier background mean")
        ax.axvspan(-.1,.1,color="gray",alpha=.15)
        ax.set(title=f"{'C' if column==0 else 'D'}. Peak-aligned shapes at {holding} mV",xlabel="Time from observed peak (ms)",ylabel="Baseline-centered current / inward amplitude")
        ax.legend(frameon=False,fontsize=8)
    ax=axes[2,0]
    rows=[r for r in summary["error_overlap"] if r["sweep"] is not None]
    xx=np.arange(len(rows))
    ax.bar(xx-.18,[r["marked_time_fraction"]*100 for r in rows],width=.35,label="Marked time",color="#4477AA")
    ax.bar(xx+.18,[r["squared_error_fraction"]*100 for r in rows],width=.35,label="Squared prediction error",color="#CC3377")
    ax.set(title="E. Previous model errors near train/evaluation peaks",xlabel="Evaluation recording",ylabel="Fraction (%)",xticks=xx,xticklabels=[r["sweep"] for r in rows],ylim=(0,100))
    ax.legend(frameon=False,fontsize=8)
    ax=axes[2,1]
    for holding,color in [(-70,"#4477AA"),(-55,"#CC3377")]:
        delta=np.concatenate([np.diff([e["time_s"] for e in r["thresholds"]["500"]["events"]]) for r in data["records"] if r["holding_mV"]==holding])
        ax.hist(delta,bins=np.arange(0,1.301,.025),histtype="step",lw=1.5,color=color,label=f"{holding} mV (n={len(delta)})")
    ax.set(title="F. Within-record adjacent-peak intervals",xlabel="Interval (s)",ylabel="Count")
    ax.legend(frameon=False,fontsize=8)
    fig.suptitle("Target 7: continuous current events and measurement limits\nPeaks are not identified APs; alignment and error association are descriptive",fontsize=12)
    for path in paths:
        ext=path.suffix[1:];buffer=BytesIO()
        fig.savefig(buffer,format=ext,dpi=160,metadata={"Date":None} if ext=="svg" else None)
        with path.open("xb") as stream:stream.write(buffer.getvalue())
    plt.close(fig)
    with summary_path.open("x",encoding="utf-8") as stream:
        json.dump(summary,stream,indent=2,allow_nan=False);stream.write("\n")


if __name__=="__main__":main()
