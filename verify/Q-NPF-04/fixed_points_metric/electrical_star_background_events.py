"""Continuous target-7 event catalogue and command-relative exposure rates.

Large inward-current peaks are observations, not identified APs, synapses or
clamp escape. Peak-aligned normalized morphology is descriptive, not prediction.
"""
import argparse
import json
from pathlib import Path

import h5py
import numpy as np
from scipy.signal import find_peaks,peak_widths

from allen_joint_inventory import BASE,OfflineRanges,raw,sha
from electrical_star_incoming_chemical import TrackedFetch

HERE=Path(__file__).resolve().parent
OUTPUT=HERE/"electrical_star_background_events_result.json"
WAVES=HERE/"electrical_star_background_current.npz"
RATE=50000
RADIUS=125  # 2.5 ms prominence half-window
SHAPE_INDEX=np.arange(-25,76)  # -0.5 to +1.5 ms, inclusive
LABELS={0:"background_context_clear",1:"other_near_command",2:"command_transition",
        **{10+s:"post_source_"+str(s) for s in [0,1,2,4,5,6]}}


def interval(mask,start,end,value):
    """Half-open times on the recorded sample grid; clip to available samples."""
    lo=max(0,int(np.ceil(start*RATE-1e-7)))
    hi=min(len(mask),int(np.ceil(end*RATE-1e-7)))
    if hi>lo: mask[lo:hi]=value


def exposure_categories(samples,pulses,analysis_start=.05):
    category=np.full(samples,-1,dtype=np.int16)
    lo=round(analysis_start*RATE)+RADIUS
    hi=samples-RADIUS
    category[lo:hi]=0
    for source,onset,offset in pulses:
        # The entire 2.5 ms context must be outside command onset..offset+30 ms.
        interval(category,onset-RADIUS/RATE,offset+.030+RADIUS/RATE,1)
    for source,onset,offset in pulses:
        interval(category,offset+.0005,offset+.015,10+source)
        interval(category,onset-.0005,offset+.0005,2)
    category[:lo]=-1;category[hi:]=-1
    return category


def detect(current,category,threshold=500.):
    current=np.asarray(current,float)
    peaks,props=find_peaks(-current,prominence=threshold,distance=100,wlen=2*RADIUS+1)
    widths=peak_widths(-current,peaks,rel_height=.5,
        prominence_data=(props["prominences"],props["left_bases"],props["right_bases"]))[0]/RATE*1000
    events=[]
    for number,peak in enumerate(peaks):
        if category[peak]<0: continue
        baseline=float(current[peak-100:peak-25].mean())
        amplitude=baseline-float(current[peak])
        if amplitude<threshold: continue
        events.append(dict(peak_sample=int(peak),time_s=float(peak/RATE),category=int(category[peak]),
            category_label=LABELS[int(category[peak])],baseline_pA=baseline,inward_amplitude_pA=amplitude,
            prominence_pA=float(props["prominences"][number]),half_prominence_width_ms=float(widths[number]),
            previous_peak_within_5ms=bool(events and peak-events[-1]["peak_sample"]<250),
            normalized_shape=((current[peak+SHAPE_INDEX]-baseline)/amplitude).tolist()))
    return events


def rate_table(category,events):
    counts=np.bincount([e["category"] for e in events],minlength=17)
    rows=[]
    for code,label in LABELS.items():
        duration=float(np.sum(category==code)/RATE)
        count=int(counts[code])
        rows.append(dict(category=code,label=label,exposure_s=duration,peak_count=count,
                         peaks_per_s=count/duration if duration else None))
    assert sum(r["peak_count"] for r in rows)==len(events)
    assert abs(sum(r["exposure_s"] for r in rows)-np.sum(category>=0)/RATE)<1e-10
    return rows


def morphology(records,threshold=500):
    out=[]
    shape_mask=np.abs(SHAPE_INDEX)>5  # ignore the forced aligned peak neighborhood
    for holding,train,evaluate in [(-70,[0,1],[2,3,4]),(-55,[5,6],[7,8,9])]:
        chosen=[e for r in records if r["sweep"] in train for e in r["thresholds"][str(threshold)]["events"]
                if e["category"]==0]
        if not chosen:
            out.append(dict(holding_mV=holding,status="no_training_background_events"));continue
        template=np.mean([e["normalized_shape"] for e in chosen],axis=0)
        evaluation=[]
        for sweep in evaluate:
            events=next(r for r in records if r["sweep"]==sweep)["thresholds"][str(threshold)]["events"]
            for label,predicate in [("background",lambda e:e["category"]==0),
                                    ("post_command",lambda e:e["category"]>=10)]:
                candidates=[e for e in events if predicate(e)]
                errors=[float(np.sqrt(np.mean((np.array(e["normalized_shape"])[shape_mask]-template[shape_mask])**2))) for e in candidates]
                evaluation.append(dict(sweep=sweep,category=label,n=len(candidates),
                    median_normalized_shape_RMSE=float(np.median(errors)) if errors else None))
        out.append(dict(holding_mV=holding,training_background_events=len(chosen),
            normalized_background_template=template.tolist(),evaluation=evaluation,
            interpretation="Peak detection/alignment/amplitude normalization shape this comparison; not independent mechanistic identification"))
    return out


def error_overlap(records):
    """Post-hoc association of the prior model's errors with train/eval events.

    No events are subtracted and no failed model is refitted or reclassified.
    """
    prior_path=HERE/"electrical_star_incoming_chemical_result.json"
    prior=json.loads(prior_path.read_text())
    wave_path=HERE/"electrical_star_incoming_chemical_waveforms.npz"
    assert sha(wave_path)==prior["waveform_sha256"]
    with np.load(wave_path,allow_pickle=False) as waves:
        currents=waves["current_pA"];offsets=waves["offset_samples"]
    primary=np.array(prior["primary_mask"])
    time=np.array(prior["time_ms"])[primary]/1000
    def event_mask(sweep,column):
        times=offsets[sweep,column,:,None]/RATE+time
        mask=np.zeros(times.shape,bool)
        for event in records[sweep]["thresholds"]["500"]["events"]:
            mask|=(times>=event["time_s"]-.0005)&(times<event["time_s"]+.004)
        return mask
    rows=[]
    for block in prior["analysis"]:
        for sweep in block["evaluate"]:
            for source in prior["settings"]["pooled_primary_sources"]:
                column=prior["sources"].index(source)
                predicted=currents[block["train"],column].mean(axis=0)[:,primary]
                observed=currents[sweep,column][:,primary]
                error=(observed-predicted)**2
                mask=event_mask(sweep,column)
                for train in block["train"]:mask|=event_mask(train,column)
                rows.append(dict(sweep=sweep,source=source,time_fraction=float(mask.mean()),
                    squared_error_fraction=float(error[mask].sum()/error.sum()) if error.sum()>0 else None,
                    total_squared_error_pA2=float(error.sum()),marked_squared_error_pA2=float(error[mask].sum())))
    return dict(prior_result_sha256=sha(prior_path),support_relative_to_peak_ms=[-.5,4.],rows=rows,
        interpretation="Post-hoc time support from events in evaluation or its two training records; no new predictive score")


def run(fetch=False):
    if OUTPUT.exists() or WAVES.exists():raise FileExistsError("Existing event results are immutable")
    inputs_path=HERE/"electrical_star_vc_inputs_result.json"
    protocol_path=HERE/"electrical_star_protocol_result.json"
    assert sha(inputs_path)=="52cebb1cfbd4ce2b7d4dacb2e589194034298314fdcad852bcb35e8989ae876b"
    assert sha(protocol_path)=="a889d98c7bbce920f78366a15c67e40464a3b4926ecec412bdd17e7f44dbb4d0"
    inputs=json.loads(inputs_path.read_text());protocol=json.loads(protocol_path.read_text())
    adc={(r["sweep"],r["device"]):r for r in protocol["records"] if r["kind"]=="acquisition"}
    cache=BASE/"raw_ranges/1552517188.758"
    manifest=json.loads((cache/"manifest.json").read_text())
    initial=sum(x["bytes"] for x in manifest["blocks"].values())
    raw.URL,raw.CACHE,raw.LIMIT=manifest["remote"]["url"],cache,initial+32*1024*1024
    saved={};records=[]
    with (TrackedFetch() if fetch else OfflineRanges(cache)) as reader:
        assert reader.remote==manifest["remote"]
        with h5py.File(reader,"r") as f:
            for sweep in range(10):
                devices={d["device"]:d for d in inputs["sweeps"][sweep]["devices"]}
                first_target=min(s["start_s"] for s in devices[7]["command_segments"] if s["command_mV"]>1)
                end=round((first_target-.030)*RATE)
                pulses=[(source,s["start_s"],s["end_s"]) for source,d in devices.items() if source!=7
                        for s in d["command_segments"] if s["command_mV"]>1]
                assert len(pulses)==72
                a=adc[sweep,7];assert a["unit"]=="A" and a["rate"]==RATE
                original=np.asarray(f[a["path"]+"/data"][:end],dtype=np.float32)
                current=(original.astype(float)*a["conversion"]+a["offset"])*1e12
                assert np.isfinite(current).all()
                categories=exposure_categories(end,pulses)
                thresholds={}
                for threshold in [500,1000]:
                    events=detect(current,categories,threshold)
                    thresholds[str(threshold)]=dict(events=events,rates=rate_table(categories,events))
                saved[f"raw_adc_{sweep:02d}"]=original
                records.append(dict(sweep=sweep,holding_mV=-70 if sweep<5 else -55,adc=a,
                    end_sample=end,first_target_command_s=first_target,pulses=pulses,thresholds=thresholds,
                    valid_peak_time_start_s=(round(.05*RATE)+RADIUS)/RATE,
                    valid_peak_time_end_exclusive_s=(end-RADIUS)/RATE))
                print("CONTINUOUS",sweep,"peaks500",len(thresholds["500"]["events"]),
                      "new_bytes",getattr(reader,"downloaded_this_session",0),flush=True)
        provenance=dict(remote=reader.remote,initial_cached_bytes=initial,
            new_download_bytes=getattr(reader,"downloaded_this_session",0),used_blocks=reader.used)
    overlap=error_overlap(records)
    with WAVES.open("xb") as stream:np.savez_compressed(stream,**saved)
    result=dict(version="electrical-star-background-events-v1",code_sha256=sha(Path(__file__)),
        inputs_sha256=sha(inputs_path),protocol_sha256=sha(protocol_path),raw_waveforms_sha256=sha(WAVES),
        raw_reader_sha256=sha(Path(raw.__file__)),fetch_wrapper_sha256=sha(HERE/"electrical_star_incoming_chemical.py"),
        provenance=provenance,records=records,morphology=morphology(records),error_overlap=overlap,
        settings=dict(primary_amplitude_and_prominence_pA=500,sensitivity_pA=1000,refractory_ms=2,
            prominence_window_samples=251,baseline_relative_to_peak_ms=[-2,-.5],
            primary_post_window_relative_to_offset_ms=[.5,15],background_after_offset_ms=30,
            full_context_half_width_ms=2.5,shape_time_ms=(SHAPE_INDEX/50).tolist()),
        claim_ceiling="L1 current-event observations; exposed-data development analysis, no AP/origin/hormone/metric identification")
    with OUTPUT.open("x",encoding="utf-8") as stream:
        json.dump(result,stream,indent=2,allow_nan=False);stream.write("\n")
    print(json.dumps({"result":str(OUTPUT),"new_bytes":provenance["new_download_bytes"],
        "peaks500":sum(len(r["thresholds"]["500"]["events"]) for r in records),
        "background500":sum(sum(e["category"]==0 for e in r["thresholds"]["500"]["events"]) for r in records)}))


if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument("--fetch-missing",action="store_true")
    args=parser.parse_args();run(args.fetch_missing)
