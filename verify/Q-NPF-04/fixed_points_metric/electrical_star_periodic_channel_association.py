"""Background-event association across simultaneous channels, not causality.

The observed target waveform is a concurrent covariate, never an independent
input or a pre-event forecast. Fixed events, fixed timing, no channel alignment.
"""
import argparse
import json
from pathlib import Path

import h5py
import numpy as np

from allen_joint_inventory import BASE,OfflineRanges,raw,sha
from electrical_star_incoming_chemical import TrackedFetch

HERE=Path(__file__).resolve().parent
OUTPUT=HERE/"electrical_star_periodic_channel_association_result.json"
WAVES=HERE/"electrical_star_periodic_channel_windows.npz"
DEVICES=[0,1,2,4,5,6,7]
RATE=50000
TIME_MS=np.arange(-500,500)/50
PRIMARY=(TIME_MS>=-.5)&(TIME_MS<4)


def clear_of_commands(start,end,segments,tail=.030):
    """Recorded nonzero commands and a fixed post-command guard only."""
    return not any(start<offset+tail and end>onset for onset,offset in segments)


def center_windows(raw_values,conversion,offset):
    """Extract actual and -25 ms control windows from peak[-35,+10) ms."""
    values=(np.asarray(raw_values,float)*conversion+offset)*1e12
    control=values[...,0:1000]
    actual=values[...,1250:2250]
    return (actual-actual[...,100:350].mean(axis=-1,keepdims=True),
            control-control[...,100:350].mean(axis=-1,keepdims=True))


def coefficients(actual,train_mask):
    x=actual[train_mask,-1][:,PRIMARY]
    denom=float(np.sum(x*x))
    if len(x)==0 or denom<=0:raise ValueError("No eligible target energy in training")
    return np.array([np.sum(x*actual[train_mask,c][:,PRIMARY])/denom for c in range(6)])


def score(observed,predicted):
    mse0=float(np.mean(observed**2));mse=float(np.mean((observed-predicted)**2))
    return dict(zero_RMSE_pA=float(np.sqrt(mse0)),RMSE_pA=float(np.sqrt(mse)),
                RMSE_over_zero=float(np.sqrt(mse/mse0)) if mse0>0 else None,
                gain_over_zero_pA2=mse0-mse)


def analyze(actual,control,events):
    sweep=np.array([e["sweep"] for e in events])
    quiet=np.array([e["both_windows_command_clear"] for e in events])
    out=[]
    for holding,train,evaluate in [(-70,[0,1],[2,3,4]),(-55,[5,6],[7,8,9])]:
        training=np.isin(sweep,train)&quiet
        beta=coefficients(actual,training)
        rows=[]
        for record in evaluate:
            for subset in ["both_windows_clear","all_catalogue_background"]:
                chosen=(sweep==record)&(quiet if subset=="both_windows_clear" else True)
                if not chosen.any():continue
                target=actual[chosen,-1][:,PRIMARY]
                for c,device in enumerate(DEVICES[:-1]):
                    pred=beta[c]*target
                    real_score=score(actual[chosen,c][:,PRIMARY],pred)
                    control_score=score(control[chosen,c][:,PRIMARY],pred)
                    rows.append(dict(sweep=record,subset=subset,device=device,n_events=int(sum(chosen)),
                        actual=real_score,shifted_other_channel=control_score,
                        actual_gain_minus_shifted_gain_pA2=real_score["gain_over_zero_pA2"]-control_score["gain_over_zero_pA2"]))
        out.append(dict(holding_mV=holding,train=train,evaluate=evaluate,
            training_events=int(sum(training)),coefficients_by_device=dict(zip(map(str,DEVICES[:-1]),beta.tolist())),
            evaluation=rows))
    return out


def run(fetch=False):
    if OUTPUT.exists() or WAVES.exists():raise FileExistsError("Completed association artifacts are immutable")
    files={"events":HERE/"electrical_star_background_events_result.json",
           "protocol":HERE/"electrical_star_protocol_result.json",
           "inputs":HERE/"electrical_star_vc_inputs_result.json",
           "target_raw":HERE/"electrical_star_background_current.npz"}
    expected={"events":"b1eff0fc8f9fcfd3ddc436d05c9b591a2278f09ccdb0b7807af8e7ba0c5fe64c",
              "protocol":"a889d98c7bbce920f78366a15c67e40464a3b4926ecec412bdd17e7f44dbb4d0",
              "inputs":"52cebb1cfbd4ce2b7d4dacb2e589194034298314fdcad852bcb35e8989ae876b",
              "target_raw":"af648961f011a981acd697f49e3a0e96159e90cccb30a67e4626dc385e668d9c"}
    for name,path in files.items():assert sha(path)==expected[name]
    catalogue=json.loads(files["events"].read_text())
    protocol=json.loads(files["protocol"].read_text())
    inputs=json.loads(files["inputs"].read_text())
    descriptions={(r["kind"],r["sweep"],r["device"]):r for r in protocol["records"]}
    events=[];raw_current=[];raw_command=[];metadata=[]
    cache=BASE/"raw_ranges/1552517188.758"
    manifest=json.loads((cache/"manifest.json").read_text())
    initial=sum(b["bytes"] for b in manifest["blocks"].values())
    raw.URL,raw.CACHE,raw.LIMIT=manifest["remote"]["url"],cache,initial+64*1024*1024
    with np.load(files["target_raw"],allow_pickle=False) as target_saved:
      with (TrackedFetch() if fetch else OfflineRanges(cache)) as reader:
        assert reader.remote==manifest["remote"]
        with h5py.File(reader,"r") as f:
            for record in catalogue["records"]:
                sweep=record["sweep"]
                selected=[e for e in record["thresholds"]["500"]["events"] if e["category"]==0]
                segments=[(s["start_s"],s["end_s"]) for d in inputs["sweeps"][sweep]["devices"]
                          for s in d["command_segments"] if abs(s["command_mV"])>.005]
                time0=descriptions["acquisition",sweep,7]["start"]
                current_desc=[descriptions["acquisition",sweep,d] for d in DEVICES]
                command_desc=[descriptions["command",sweep,d] for d in DEVICES]
                for a,c in zip(current_desc,command_desc):
                    assert a["unit"]=="A" and c["unit"]=="V"
                    assert a["rate"]==c["rate"]==RATE and a["start"]==c["start"]==time0
                metadata.append(dict(sweep=sweep,acquisition=current_desc,command=command_desc))
                for event in selected:
                    peak=event["peak_sample"];left=peak-1750;right=peak+500
                    assert 0<=left<right<=record["end_sample"]
                    acq=[];commands=[]
                    for a,c in zip(current_desc,command_desc):
                        values=(target_saved[f"raw_adc_{sweep:02d}"][left:right] if a["device"]==7 else
                                np.asarray(f[a["path"]+"/data"][left:right],dtype=np.float32))
                        acq.append(values)
                        commands.append(np.asarray(f[c["path"]+"/data"][left:right],dtype=np.float32))
                    acq=np.array(acq);commands=np.array(commands)
                    assert acq.shape==commands.shape==(7,2250)
                    assert np.isfinite(acq).all() and np.isfinite(commands).all()
                    command_mV=np.array([(v.astype(float)*c["conversion"]+c["offset"])*1000 for v,c in zip(commands,command_desc)])
                    t=peak/RATE
                    real_clear=clear_of_commands(t-.010,t+.010,segments)
                    control_clear=clear_of_commands(t-.035,t-.015,segments)
                    actual_range=np.ptp(command_mV[:,1250:2250],axis=1)
                    control_range=np.ptp(command_mV[:,:1000],axis=1)
                    if real_clear:assert np.max(actual_range)<1e-9
                    if control_clear:assert np.max(control_range)<1e-9
                    events.append(dict(sweep=sweep,holding_mV=record["holding_mV"],peak_sample=peak,
                        time_s=t,NWB_clock_peak_s=time0+t,
                        catalogue_amplitude_pA=event["inward_amplitude_pA"],
                        actual_window_command_clear=real_clear,control_window_command_clear=control_clear,
                        both_windows_command_clear=real_clear and control_clear,
                        actual_command_range_mV=actual_range.tolist(),control_command_range_mV=control_range.tolist()))
                    raw_current.append(acq);raw_command.append(commands)
                print("CHANNEL_WINDOWS",sweep,len(selected),"new_bytes",getattr(reader,"downloaded_this_session",0),flush=True)
        provenance=dict(remote=reader.remote,initial_cached_bytes=initial,
            new_download_bytes=getattr(reader,"downloaded_this_session",0),used_blocks=reader.used)
    raw_current=np.array(raw_current,dtype=np.float32);raw_command=np.array(raw_command,dtype=np.float32)
    conversions=np.array([[descriptions["acquisition",e["sweep"],d]["conversion"] for d in DEVICES] for e in events])[...,None]
    offsets=np.array([[descriptions["acquisition",e["sweep"],d]["offset"] for d in DEVICES] for e in events])[...,None]
    actual,control=center_windows(raw_current,conversions,offsets)
    analysis=analyze(actual,control,events)
    with WAVES.open("xb") as stream:
        np.savez_compressed(stream,raw_current=raw_current,raw_command=raw_command,time_ms=TIME_MS,
            sweep=np.array([e["sweep"] for e in events]),peak_sample=np.array([e["peak_sample"] for e in events]))
    result=dict(version="electrical-star-periodic-channel-association-v1",code_sha256=sha(Path(__file__)),
        inputs_sha256=expected,raw_windows_sha256=sha(WAVES),
        raw_reader_sha256=sha(Path(raw.__file__)),fetch_wrapper_sha256=sha(HERE/"electrical_star_incoming_chemical.py"),
        provenance=provenance,devices=DEVICES,metadata=metadata,events=events,analysis=analysis,
        settings=dict(catalogue_threshold_pA=500,catalogue_category=0,
            actual_window_ms=[-10,10],control_center_shift_ms=-25,baseline_ms=[-8,-3],
            primary_window_ms=[-.5,4],command_guard_after_offset_ms=30,
            train_subset="both actual and control full windows command clear",
            prediction="one coefficient per holding and other channel times concurrently observed target waveform",
            time_control="actual target predicts shifted other channel; coefficients unchanged",
            evaluation_alignment_and_amplitude_refit=False),
        claim_ceiling="L1 simultaneous observations; development conditional association, no causal direction, AP origin, hormone or spatial metric identification")
    with OUTPUT.open("x",encoding="utf-8") as stream:
        json.dump(result,stream,indent=2,allow_nan=False);stream.write("\n")
    print(json.dumps({"events":len(events),"both_windows_clear":sum(e["both_windows_command_clear"] for e in events),
                     "new_bytes":provenance["new_download_bytes"]}))


if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument("--fetch-missing",action="store_true")
    args=parser.parse_args();run(args.fetch_missing)
