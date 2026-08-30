"""CE-BRAIN Phase 2E individual-axis and recovery replication."""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, os
from pathlib import Path
from typing import Any
import h5py
import numpy as np
from scipy.signal import butter, sosfiltfilt

ROOT=Path(__file__).resolve().parents[2]; STOP="PHASE2E_APPARATUS_STOP"
CONTRACT=ROOT/"paper"/"검증_원장"/"CE_BRAIN_PHASE2E_개체축_가역성_복제_계약.md"
TEST_FILE=ROOT/"tests"/"test_ce_brain_phase2e_axis_recovery.py"
BASE_FILE=ROOT/"examples"/"brain"/"ce_brain_phase2d_model_competition.py"
_s=importlib.util.spec_from_file_location("ce_brain_phase2d_dependency",BASE_FILE); assert _s and _s.loader
base=importlib.util.module_from_spec(_s); _s.loader.exec_module(base)
FS=2500.; CURRENTS=(40,60,80); STATES=("awake","isoflurane","recovery")
CHANNELS=(5,20,22,23,24,25,26,27,28,29); BOOTSTRAPS=1999; SEED=20260904
PERMUTATIONS=999; PERM_SEED=20261904
base.PERMUTATIONS=PERMUTATIONS; base.PERMUTATION_SEED=PERM_SEED
RAW_BYTES=11_687_836_529; RAW_SHA="a949ca38d1b2c55b32c694bff8c9ce73195ec6c84a9d58f61cc9ce456ba14029"
COUNTS={
"awake/40/development":57,"awake/40/confirmation":61,"awake/60/development":56,"awake/60/confirmation":64,"awake/80/development":67,"awake/80/confirmation":53,
"isoflurane/40/development":57,"isoflurane/40/confirmation":62,"isoflurane/60/development":56,"isoflurane/60/confirmation":64,"isoflurane/80/development":67,"isoflurane/80/confirmation":53,
"recovery/40/development":114,"recovery/40/confirmation":125,"recovery/60/development":112,"recovery/60/confirmation":128,"recovery/80/development":134,"recovery/80/confirmation":106}
SCHEMA="phase2e-schema-receipt.json"; MANIFEST="phase2e-manifest.json"; RESULT="phase2e-result.json"; VALIDATION="phase2e-validation-receipt.json"

canonical_json_bytes=base.canonical_json_bytes; sha256_file=base.sha256_file; write_json_once=base.write_json_once

def raw_identity(path:Path)->dict[str,Any]:
    if not path.is_file() or path.stat().st_size!=RAW_BYTES or sha256_file(path)!=RAW_SHA: raise RuntimeError(f"{STOP}: raw identity")
    return {"subject":"551399","filename":path.name,"bytes":RAW_BYTES,"sha256":RAW_SHA}

def decode(x): return np.asarray([v.decode() if isinstance(v,bytes) else str(v) for v in x])

def read_schema(nwb:h5py.File,opened:bool)->dict[str,Any]:
    data=nwb["/acquisition/ElectricalSeriesEEG/data"]; ts=np.asarray(nwb["/acquisition/ElectricalSeriesEEG/timestamps"][...],float)
    if data.shape!=(17_173_504,30) or data.dtype!=np.dtype("int16") or float(data.attrs["conversion"])!=1.9499999284744263e-07: raise RuntimeError(f"{STOP}: EEG")
    dt=np.diff(ts); med=float(np.median(dt))
    if np.any(dt<=0) or np.any(dt>1.5*med) or abs(1/med-FS)>.02 or np.max(np.abs(dt/med-1))>3e-5: raise RuntimeError(f"{STOP}: timestamps")
    reg=np.asarray(nwb["/acquisition/ElectricalSeriesEEG/electrodes"][...],int); valid=np.asarray(nwb["/general/extracellular_ephys/electrodes/is_data_valid"][...],bool)
    columns=tuple(np.flatnonzero(valid[reg]).tolist())
    if columns!=(2,5,6,8,9,12,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29): raise RuntimeError(f"{STOP}: channels")
    t=nwb["/intervals/trials"]; ids=np.asarray(t["id"][...],int); starts=np.asarray(t["start_time"][...],float)
    states=decode(t["behavioral_epoch"][...]); currents=decode(t["estim_current"][...]).astype(int)
    target=decode(t["estim_target_region"][...]); desc=decode(t["stimulus_description"][...]); valid_t=np.asarray(t["is_valid"][...],bool)
    if any(len(x)!=1440 for x in (ids,starts,states,currents,target,desc,valid_t)): raise RuntimeError(f"{STOP}: trials")
    origins=base.nearest_origins(ts,starts); eligible=valid_t&np.isin(states,STATES)&np.isin(currents,CURRENTS)&(target=="MOs")&(desc=="biphasic")
    eligible &= (origins-1250>=0)&(origins+1250<len(ts))
    counts={f"{s}/{u}/{q}":int(np.sum(eligible&(states==s)&(currents==u)&(ids%2==p))) for s in STATES for u in CURRENTS for q,p in (("development",0),("confirmation",1))}
    if counts!=COUNTS: raise RuntimeError(f"{STOP}: counts")
    return {"confirmation_values_opened":opened,"conversion":float(data.attrs["conversion"]),"eeg_shape":list(data.shape),"eligible":eligible,"fs_hz":1/med,"origins":origins,"segments":{s:(0,len(ts)) for s in STATES},"split_counts":counts,"trial_ids":ids,"trial_starts":starts,"trial_states":states,"trial_currents":currents,"valid_channels":list(CHANNELS)}

def public(s):
    hidden={"eligible","origins","trial_ids","trial_starts","trial_states","trial_currents"}; return {k:v for k,v in s.items() if k not in hidden}

def extract(nwb,schema):
    rows=np.flatnonzero(schema["eligible"]); origins=schema["origins"][rows]; raw=np.empty((len(rows),249,len(CHANNELS))); baseline=np.empty((len(rows),len(CHANNELS)))
    data=nwb["/acquisition/ElectricalSeriesEEG/data"]; sos=butter(3,(.1,100),btype="bandpass",fs=FS,output="sos")
    for j,ch in enumerate(CHANNELS):
        x=np.asarray(data[:,ch],float); base.replace_artifacts(x,origins); x*=schema["conversion"]*1e6; x=sosfiltfilt(sos,x)
        for i,o in enumerate(origins): baseline[i,j]=x[o-1250:o-25].mean(); raw[i,:,j]=x[o+5:o+1250:5]
    raw-=raw.mean(2,keepdims=True); baseline-=baseline.mean(1,keepdims=True); raw-=baseline[:,None,:]
    flat=raw.reshape(len(raw),-1); norms=np.linalg.norm(flat,axis=1)
    if flat.shape[1]!=2490 or not np.all(np.isfinite(flat)) or np.any(norms<=0): raise RuntimeError(f"{STOP}: waveform")
    return flat,flat/norms[:,None],rows

def cells(values,rows,schema,parity):
    ids=schema["trial_ids"][rows]; st=schema["trial_states"][rows]; cur=schema["trial_currents"][rows]; out={}
    for s in STATES:
        for u in CURRENTS: out[f"{s}/{u}"]=values[(st==s)&(cur==u)&(ids%2==parity)]
    return out

def contrast(c): return np.stack([c[f"isoflurane/{u}"].mean(0)-c[f"awake/{u}"].mean(0) for u in CURRENTS])
def predictions(dev):
    axis=base.rank_one_axis(dev); return {"Z":np.zeros_like(dev),"I":np.outer(dev@axis,axis),"K":dev.copy()}
def errors(pred,conf): return {k:float(np.mean(np.sum((conf-v)**2,axis=1))) for k,v in pred.items()}
def improvement(e,a,b): return (e[b]-e[a])/e[b]
def q_values(c): return {str(u):float(np.linalg.norm(c[f"recovery/{u}"].mean(0)-c[f"awake/{u}"].mean(0))/np.linalg.norm(c[f"isoflurane/{u}"].mean(0)-c[f"awake/{u}"].mean(0))) for u in CURRENTS}
def means(rng,x,b): n=len(x); return (rng.multinomial(n,np.full(n,1/n),size=b)/n)@x
def batch_axis(m): return base._batch_axis(m)

def bootstrap(dev,conf,reps=BOOTSTRAPS,seed=SEED,batch=32):
    rng=np.random.Generator(np.random.PCG64(seed)); out={"I_vs_Z":[],"K_vs_I":[],**{f"Q_{u}":[] for u in CURRENTS}}; done=0
    while done<reps:
        b=min(batch,reps-done); d=np.stack([means(rng,dev[f"isoflurane/{u}"],b)-means(rng,dev[f"awake/{u}"],b) for u in CURRENTS],1)
        a=np.stack([means(rng,conf[f"awake/{u}"],b) for u in CURRENTS],1); i=np.stack([means(rng,conf[f"isoflurane/{u}"],b) for u in CURRENTS],1); r=np.stack([means(rng,conf[f"recovery/{u}"],b) for u in CURRENTS],1); c=i-a
        axis=batch_axis(d); pi=np.sum(d*axis[:,None,:],2)[:,:,None]*axis[:,None,:]
        ez=np.mean(np.sum(c*c,2),1); ei=np.mean(np.sum((c-pi)**2,2),1); ek=np.mean(np.sum((c-d)**2,2),1)
        out["I_vs_Z"].append((ez-ei)/ez); out["K_vs_I"].append((ei-ek)/ei)
        qs=np.linalg.norm(r-a,axis=2)/np.linalg.norm(i-a,axis=2)
        for j,u in enumerate(CURRENTS): out[f"Q_{u}"].append(qs[:,j])
        done+=b
    return {k:np.concatenate(v) for k,v in out.items()}

def time_halves(values,rows,schema,state_names):
    ids=schema["trial_ids"][rows]; st=schema["trial_states"][rows]; cur=schema["trial_currents"][rows]; starts=schema["trial_starts"][rows]; outs=({}, {})
    for s in state_names:
        for u in CURRENTS:
            ix=np.flatnonzero((st==s)&(cur==u)&(ids%2==1)); ix=ix[np.argsort(starts[ix],kind="stable")]; m=len(ix)//2
            if min(m,len(ix)-m)<20: raise RuntimeError(f"{STOP}: halves")
            outs[0][f"{s}/{u}"]=values[ix[:m]]; outs[1][f"{s}/{u}"]=values[ix[m:]]
    return outs

def decide(imp,lower,kimp,klower,q,upper,qhalves):
    axis=imp>=.10 and lower>0 and not(kimp>=.10 and klower>0)
    recovery=all(q[str(u)]<=.75 and upper[str(u)]<1 for u in CURRENTS) and all(all(h[str(u)]<1 for u in CURRENTS) for h in qhalves.values())
    if axis and recovery:return "INDIVIDUAL_AXIS_AND_RECOVERY_REPLICATED"
    if axis:return "INDIVIDUAL_AXIS_REPLICATED_RECOVERY_NOT_ESTABLISHED"
    return "INDIVIDUAL_AXIS_NOT_REPLICATED"

def preregistered(): return (Path(__file__).resolve(),TEST_FILE,CONTRACT,BASE_FILE)
def schema_receipt(raw,adir):
    ident=raw_identity(raw)
    with h5py.File(raw,"r") as f:s=public(read_schema(f,False))
    x={"confirmation_values_opened":False,"raw":ident,"schema":s}; x["receipt_sha256"]=write_json_once(adir/SCHEMA,x); return x
def seal(raw,adir):
    rp=adir/SCHEMA; rec=json.loads(rp.read_text("utf-8")); ident=raw_identity(raw)
    if rec.get("raw")!=ident or rec.get("confirmation_values_opened") is not False:raise RuntimeError(f"{STOP}: receipt")
    files={str(p.relative_to(ROOT)).replace("\\","/"):sha256_file(p) for p in preregistered()}; x={"confirmation_values_opened":False,"files":files,"raw":ident,"schema_receipt_sha256":sha256_file(rp)}; x["manifest_sha256"]=write_json_once(adir/MANIFEST,x); return x
def verify_manifest(raw,adir):
    p=adir/MANIFEST; m=json.loads(p.read_text("utf-8")); files={str(x.relative_to(ROOT)).replace("\\","/"):sha256_file(x) for x in preregistered()}
    if m.get("raw")!=raw_identity(raw) or m.get("files")!=files or m.get("schema_receipt_sha256")!=sha256_file(adir/SCHEMA):raise RuntimeError(f"{STOP}: manifest")
    return sha256_file(p)

def compute(raw,adir):
    manifest=verify_manifest(raw,adir)
    with h5py.File(raw,"r") as f:s=read_schema(f,True); rawv,unit,rows=extract(f,s)
    dev=cells(unit,rows,s,0); conf=cells(unit,rows,s,1); rawc=cells(rawv,rows,s,1); dc=contrast(conf); pred=predictions(contrast(dev)); e=errors(pred,dc); imp=improvement(e,"I","Z"); kimp=improvement(e,"K","I")
    bs=bootstrap(dev,conf); lower=float(np.quantile(bs["I_vs_Z"],.025)); klower=float(np.quantile(bs["K_vs_I"],.025)); q=q_values(conf); upper={str(u):float(np.quantile(bs[f"Q_{u}"],.975)) for u in CURRENTS}
    ah=time_halves(unit,rows,s,("awake","isoflurane")); rh=time_halves(unit,rows,s,STATES)
    halfscores={}; qhalves={}
    for n,h in zip(("early","late"),ah,strict=True): he=errors(pred,contrast(h)); halfscores[n]={"errors":he,"ranking":sorted(he,key=he.get)}
    for n,h in zip(("early","late"),rh,strict=True):qhalves[n]=q_values(h)
    decision=decide(imp,lower,kimp,klower,q,upper,qhalves)
    permutation={str(u):base.permutation_p(conf[f"awake/{u}"],conf[f"isoflurane/{u}"],u) for u in CURRENTS}; gain={str(u):base.gain_residual(rawc[f"awake/{u}"],rawc[f"isoflurane/{u}"]) for u in CURRENTS}
    x={"bootstrap":{"I_vs_Z_lower_95":lower,"I_vs_Z_median":float(np.median(bs["I_vs_Z"])),"K_vs_I_lower_95":klower,"K_vs_I_median":float(np.median(bs["K_vs_I"])),"Q_upper_97_5":upper,"repetitions":BOOTSTRAPS,"seed":SEED},"decision":decision,"errors":e,"gain_control":gain,"I_vs_Z":imp,"K_vs_I":kimp,"manifest_sha256":manifest,"permutation":permutation,"recovery":{"Q":q,"time_halves":qhalves},"response_dimension":2490,"stage3_authorized":decision=="INDIVIDUAL_AXIS_AND_RECOVERY_REPLICATED","time_halves":halfscores}
    validate(x); return x
def validate(x):
    expected=decide(x["I_vs_Z"],x["bootstrap"]["I_vs_Z_lower_95"],x["K_vs_I"],x["bootstrap"]["K_vs_I_lower_95"],x["recovery"]["Q"],x["bootstrap"]["Q_upper_97_5"],x["recovery"]["time_halves"])
    if x.get("decision")!=expected or x.get("stage3_authorized")!=(expected=="INDIVIDUAL_AXIS_AND_RECOVERY_REPLICATED"):raise RuntimeError(f"{STOP}: decision")
def execute(raw,adir):
    if (adir/RESULT).exists():raise RuntimeError(f"{STOP}: overwrite")
    x=compute(raw,adir); write_json_once(adir/RESULT,x); return x
def verify(raw,adir):
    p=adir/RESULT; stored=json.loads(p.read_text("utf-8")); validate(stored); recomputed=compute(raw,adir)
    if canonical_json_bytes(stored)!=canonical_json_bytes(recomputed):raise RuntimeError(f"{STOP}: recompute")
    x={"decision":stored["decision"],"raw_recomputed":True,"result_sha256":sha256_file(p),"status":"PASS"}; x["validation_receipt_sha256"]=write_json_once(adir/VALIDATION,x); return x
def main():
    p=argparse.ArgumentParser();p.add_argument("--raw",type=Path,required=True);p.add_argument("--artifact-dir",type=Path,default=ROOT/"artifacts"/"brain"/"ce_brain_phase2e_axis_recovery");g=p.add_mutually_exclusive_group(required=True)
    for n in ("schema-only","seal","execute","verify-result"):g.add_argument(f"--{n}",action="store_true")
    a=p.parse_args(); out=schema_receipt(a.raw,a.artifact_dir) if a.schema_only else seal(a.raw,a.artifact_dir) if a.seal else execute(a.raw,a.artifact_dir) if a.execute else verify(a.raw,a.artifact_dir);print(json.dumps(out,sort_keys=True,allow_nan=False))
if __name__=="__main__":main()
