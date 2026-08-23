"""BA-SRM4: frozen, fail-closed state-versus-ordered-history EEG pilot.

Real stages are deliberately offline unless ``--execute`` is supplied.  The
small functions below are also used by P0: that keeps the synthetic checks on
the exact transform, area and ridge implementation used for human data.
"""
from __future__ import annotations

import argparse, hashlib, importlib.util, json, math, os, tempfile
from pathlib import Path
import numpy as np

CONTRACT_SHA256 = "04ea2bb2166916120bebf25c546646dd59f4bd20b4c97c4e9ba5de28f70a174d"
MANIFEST_SHA256 = "4ebc8efdca4e277a989c8e7aceb0f00911d84fd20e6b6980dc94cbce7062a061"
SELF1_SHA256 = "b075b9deb34c6a5e93ab58eabeb378a38c2e69045b4155d219252154baa3d559"
SELF3_ALLOCATION_SHA256 = "91fff95baa5ff309d2dda23e4206da8f7f04fd6341c6b1012b2dbb82bb95f1c2"
SOURCE_A0_SHA256 = "5bc7fb8acebe366db84ba6f4aa9b95eae2051e3bf0f5760792c7ac9e6520a3f7"
SRM4_ALLOCATION_SHA256 = "6bcedcf784caa9570f4a46066e9badb9e6fc2a0605de8c4491b4fbf1f84df255"
PREFIX = "BA-SRM4-REAL-v1:"
STAGES = ("A0-ALLOCATION", "P0-SYNTHETIC", "R0-SMALL", "R1-MEDIUM", "R2-LARGE")

class Invalid(RuntimeError): pass
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def h(text): return hashlib.sha256(text.encode("utf-8")).hexdigest()
def dump(path, obj):
    path=Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    fd,tmp=tempfile.mkstemp(dir=path.parent,prefix=path.name+".",suffix=".partial")
    try:
        with os.fdopen(fd,"w",encoding="utf-8",newline="\n") as f:
            json.dump(obj,f,ensure_ascii=False,sort_keys=True,indent=2); f.write("\n"); f.flush(); os.fsync(f.fileno())
        os.replace(tmp,path)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)

def unopened(stage):
    order=list(STAGES); return order[order.index(stage)+1:]+["C1","C2","C3"]

def allocation(previous):
    """Signal-blind deterministic 10/20/70 allocation from SELF3's D2-M."""
    if sha(previous)!=SELF3_ALLOCATION_SHA256: raise Invalid("SELF3 allocation hash mismatch")
    old=json.loads(Path(previous).read_text(encoding="utf-8"))
    rows=[dict(r) for r in old["trials"] if r["new_split"]=="D2-M"]
    if len(rows)!=100: raise Invalid("expected exactly 100 sealed D2-M pairs")
    by={"ses-01":[],"ses-02":[]}
    for r in rows:
        if r.get("subject")!="sub-02" or r.get("session") not in by: raise Invalid("unexpected sealed row")
        r["allocation_key"]=h(PREFIX+r["trial_hash"]); by[r["session"]].append(r)
    targets={"ses-01":(5,10,42),"ses-02":(5,10,28)}; out=[]
    for ses,g in by.items():
        g.sort(key=lambda r:(r["allocation_key"],r["trial_hash"])); a,b,c=targets[ses]
        if len(g)!=a+b+c: raise Invalid("session allocation count mismatch")
        for i,r in enumerate(g):
            r["old_split"]="D2-M"; r["new_split"]="R0-SMALL" if i<a else "R1-MEDIUM" if i<a+b else "R2-LARGE"; out.append(r)
    counts={k:sum(r["new_split"]==k for r in out) for k in STAGES[2:]}
    sescounts={s:{k:sum(r["session"]==s and r["new_split"]==k for r in out) for k in counts} for s in by}
    if counts!={"R0-SMALL":10,"R1-MEDIUM":20,"R2-LARGE":70}: raise Invalid("allocation counts")
    coverage={s:sorted({r["word"] for r in out if r["session"]==s and r["new_split"]=="R2-LARGE"}) for s in by}
    all_words=sorted({r["word"] for r in out if r["new_split"]=="R2-LARGE"})
    if len(all_words)!=8: raise Invalid("R2 lacks one of eight word levels")
    return {"schema":"BA-SRM4-allocation-v1","status":"A0_ALLOCATION_PASS","signal_accessed":False,
      "scientific_endpoint_opened":False,"model_outcome_opened":False,"model_outcome_computed":False,
      "contract_sha256":CONTRACT_SHA256,"manifest_sha256":MANIFEST_SHA256,"self1_brainvision_sha256":SELF1_SHA256,"self3_allocation_sha256":SELF3_ALLOCATION_SHA256,"network_accessed":False,"stage":"A0-ALLOCATION","allocation_prefix":PREFIX,"trials":sorted(out,key=lambda r:(r["session"],r["allocation_key"],r["trial_hash"])),"counts":counts,"session_counts":sescounts,"r2_word_coverage":coverage,"r2_all_word_coverage":all_words,"unopened_splits":unopened("A0-ALLOCATION")}

def fit_transform(train):
    """Fold-local median/MAD, bounded map, PCA and whitening."""
    a=np.asarray(train,float)
    if a.ndim!=3 or a.shape[1:]!=(126,63) or not np.isfinite(a).all(): raise Invalid("APPARATUS_INVALID_NONFINITE_WINDOW")
    flat=a.reshape(-1,63); med=np.median(flat,0); scale=1.4826*np.median(np.abs(flat-med),0)
    if not np.isfinite(scale).all() or np.any(scale<=0): raise Invalid("APPARATUS_INVALID_CHANNEL_SCALE")
    u=4*np.tanh(((a-med)/scale)/4); F=u.reshape(-1,63); mean=F.mean(0); cov=(F-mean).T@(F-mean)/len(F)
    val,vec=np.linalg.eigh(cov); idx=np.argsort(val)[::-1]; val,vec=val[idx],vec[:,idx]
    if len(val)<2 or val[1]<=0 or val[1]/val[0]<1e-6: raise Invalid("APPARATUS_INVALID_PCA_RANK")
    p=val/val.sum(); deff=float(np.exp(-np.sum(np.where(p>0,p*np.log(p),0))))
    return {"median":med,"scale":scale,"mean":mean,"basis":vec[:,:2],"eig":val,"d_eff":deff}
def project(w,t):
    a=np.asarray(w,float); u=4*np.tanh(((a-t["median"])/t["scale"])/4)
    return (u-t["mean"])@t["basis"]/np.sqrt(t["eig"][:2])
def area(z):
    """Exact contract area: one half of every ordered increment pair."""
    d=np.diff(np.asarray(z)[:101],axis=0)
    prior=np.vstack((np.zeros(2),np.cumsum(d[:-1],axis=0)))
    return .5*float(np.sum(prior[:,0]*d[:,1]-prior[:,1]*d[:,0]))
def features(z,word=None,condition=0,small=False):
    endpoint=z[100]; vel=z[100]-z[99]
    if small: return np.r_[endpoint,vel]
    start=z[1]; disp=endpoint-start; energy=np.sum(np.diff(z[:101],axis=0)**2); words=np.zeros(7)
    if word is not None and word!="child": words[sorted(["daughter","father","four","six","ten","three","wife"]).index(word)]=1
    return np.r_[endpoint,vel,start,disp,energy,condition,words]
def ridge(x,y,lmbda=1.):
    x=np.asarray(x,float); y=np.asarray(y,float); mu=x.mean(0); sd=x.std(0); active=sd>0; xs=(x[:,active]-mu[active])/sd[active]
    if len(x)<active.sum()+6: raise Invalid("APPARATUS_INVALID_SAMPLE_GUARD")
    design=np.c_[np.ones(len(x)),xs]; aug=np.r_[design,np.c_[np.zeros((active.sum(),1)),np.sqrt(lmbda)*np.eye(active.sum())]]; yy=np.r_[y,np.zeros((active.sum(),y.shape[1]))]
    beta=np.linalg.lstsq(aug,yy,rcond=None)[0]
    return {"mu":mu,"sd":sd,"active":active,"beta":beta}
def predict(model,x):
    active=model["active"]; return np.c_[np.ones(len(x)),(x[:,active]-model["mu"][active])/model["sd"][active]]@model["beta"]
def shuffle_area(z,trial_hash,j):
    inc=np.diff(z[:101],axis=0); fixed=inc[-1:]; earlier=inc[:-1].copy(); seed=int(h("BA-SRM4-SHUFFLE-v1:"+trial_hash+":"+str(j))[:16],16); rng=np.random.default_rng(seed); rng.shuffle(earlier); zz=np.r_[z[:1],z[:1]+np.cumsum(np.r_[earlier,fixed],0)]; return area(zz)

def synthetic(seed=7):
    rng=np.random.default_rng(seed); n=100; T=126; C=63
    def make(area_gain):
        # two latent coordinates, observed by a full-rank mixing matrix
        base=rng.normal(0,.15,(n,T,2)); base[:,1:]+=np.cumsum(base[:,1:],axis=1)*.10
        for i in range(n): base[i,125]+=area_gain*area(base[i])*np.array([1.,-.5])
        mix=rng.normal(size=(2,C)); return base@mix+rng.normal(0,.01,(n,T,C))
    null,pos=make(0),make(3.0)
    def gain(a, label):
        tr=fit_transform(a[:70]); z=project(a,tr); x=np.array([features(q) for q in z]); aa=np.array([area(q) for q in z])[:,None]; y=z[:,125]-z[:,100]
        m0=ridge(x[:70],y[:70]); m1=ridge(np.c_[x[:70],aa[:70]],y[:70]); l0=np.mean((y[70:]-predict(m0,x[70:]))**2); l1=np.mean((y[70:]-predict(m1,np.c_[x[70:],aa[70:]]))**2)
        controls=[]
        for j in range(20):
            sa=np.array([shuffle_area(q,label+str(i),j) for i,q in enumerate(z)])[:,None]
            sm=ridge(np.c_[x[:70],sa[:70]],y[:70]); sl=float(np.mean((y[70:]-predict(sm,np.c_[x[70:],sa[70:]]))**2))
            controls.append({"j":j,"seed_prefix":"BA-SRM4-SHUFFLE-v1:","loss":sl,"oriented_minus_shuffle":float(l1-sl)})
        return {"gain":float((l0-l1)/l0),"l0":float(l0),"l1":float(l1),"controls":controls}
    gn=gain(null,"null-"); gp=gain(pos,"positive-")
    if gn["gain"]>.01 or gp["gain"]<.05 or any(x["oriented_minus_shuffle"]>-.01 for x in gp["controls"]): raise Invalid("STOP_SYNTHETIC_IDENTIFIABILITY_FAILURE")
    # common pre-CAR gain/offset must be loss invariant
    g=2.7; off=rng.normal(size=(1,1,C)); transformed=pos*g+off; a=gain(transformed,"positive-")
    if not np.allclose([gp["l0"],gp["l1"]],[a["l0"],a["l1"]],rtol=1e-10,atol=1e-10): raise Invalid("common affine loss invariance")
    # fail-closed cases
    def rejects(value):
        try: fit_transform(value)
        except Invalid: return True
        return False
    if not rejects(np.zeros((2,126,63))): raise Invalid("zero scale accepted")
    bad=pos.copy(); bad[0,0,0]=np.nan
    if not rejects(bad): raise Invalid("nonfinite accepted")
    return {"status":"P0_SYNTHETIC_PASS","markov":gn,"injected":gp,"common_affine":{"base_losses":[gp["l0"],gp["l1"]],"transformed_losses":[a["l0"],a["l1"]],"max_delta":float(max(abs(gp["l0"]-a["l0"]),abs(gp["l1"]-a["l1"])))},"nonfinite_rejected":True,"zero_scale_rejected":True,"unopened_splits":unopened("P0-SYNTHETIC"),"signal_accessed":False,"scientific_endpoint_opened":False,"model_outcome_opened":False,"model_outcome_computed":False}

def preflight(stage, contract):
    if sha(contract)!=CONTRACT_SHA256: raise Invalid("contract hash mismatch")
    return {"schema":"BA-SRM4-real-eeg-v1","stage":stage,"status":stage+"_PREFLIGHT_NOT_EXECUTED","network_accessed":False,"signal_accessed":False,"scientific_endpoint_opened":False,"model_outcome_opened":False,"model_outcome_computed":False,"contract_sha256":CONTRACT_SHA256,"unopened_splits":unopened(stage)}
def load_reader(path):
    if sha(path)!=SELF1_SHA256: raise Invalid("SELF1 reader hash mismatch")
    sp=importlib.util.spec_from_file_location("srm4_self1",path); m=importlib.util.module_from_spec(sp); sp.loader.exec_module(m); return m
def new_access_state():
    return {"network_accessed":False,"signal_accessed":False,
            "scientific_endpoint_opened":False,"model_outcome_opened":False,
            "model_outcome_computed":False,"completed_requests":[]}

def r0_rows(reader, manifest, meta, alloc, access=None):
    access = access if access is not None else new_access_state()
    rows=[r for r in alloc["trials"] if r["new_split"]=="R0-SMALL"]
    if len(rows)!=10 or any(sum(r["session"]==s for r in rows)!=5 for s in ("ses-01","ses-02")): raise Invalid("R0 allocation mismatch")
    out=[]
    for r in rows:
        rec=reader.recording_for(meta,r["subject"],r["session"]); pair={"trial_hash":r["trial_hash"],"session":r["session"],"windows":[]}
        for cond in ("task","rest"):
            anchor=reader.anchor_to_sample(float(r[cond+"_anchor_s"])); _,_,start,end=reader.byte_geometry(anchor)
            access["network_accessed"]=True
            raw,request=reader.fetch_exact_range(rec["eeg_url"],start,end,rec["content_length"],rec["etag"])
            access["signal_accessed"]=True
            access["completed_requests"].append({"trial_hash":r["trial_hash"],"session":r["session"],"condition":cond,"anchor_sample":anchor,"request":request})
            w=reader.causal_filter_and_decimate(reader.parse_multiplexed_float32(raw))
            if w.shape!=(126,63) or not np.isfinite(w).all(): raise Invalid("APPARATUS_INVALID_DOMAIN")
            pair["windows"].append({"condition":cond,"window":w,"request":request,"anchor_sample":anchor})
        out.append(pair)
    return out
def r0_fit(train,test):
    raw=np.array([x["window"] for p in train for x in p["windows"]]); tr=fit_transform(raw)
    def rows(pairs):
        xx=[]; yy=[]; tags=[]
        for p in pairs:
            for x in p["windows"]:
                z=project(x["window"],tr); xx.append(features(z,small=True)); yy.append(z[125]-z[100]); tags.append((p["trial_hash"],x["condition"]))
        return np.array(xx),np.array(yy),tags
    x,y,_=rows(train); tx,ty,tags=rows(test); m=ridge(x,y); pred=predict(m,tx); err=np.sum((ty-pred)**2,1); pe=np.sum(ty**2,1)
    pair_losses=[]
    for trial_hash in sorted({t[0] for t in tags}):
        ix=[i for i,t in enumerate(tags) if t[0]==trial_hash]
        pair_losses.append({"trial_hash":trial_hash,"m0_mean_squared_error":float(np.mean(err[ix])),"persistence_mean_squared_error":float(np.mean(pe[ix]))})
    data={}
    for cond in ("task","rest"):
        ix=[i for i,t in enumerate(tags) if t[1]==cond]; s0=float(err[ix].sum()); sp=float(pe[ix].sum()); n=len(ix)
        if sp<=1e-12 or s0<=1e-12: raise Invalid("APPARATUS_INVALID_OR_BASELINE_UNRESOLVED")
        data[cond]={"sse_persistence":sp,"sse_m0":s0,"count":n,"L_p":sp/n,"L_0":s0/n,"B":(sp-s0)/sp,
                    "row_losses":[{"trial_hash":tags[i][0],"squared_error":float(err[i]),"persistence_squared_error":float(pe[i])} for i in ix]}
    standardized=(raw-tr["median"])/tr["scale"]
    diagnostics={"training_rows":int(len(x)),"active_parameter_count_including_intercept":int(m["active"].sum()+1),
                 "sample_guard_margin":int(len(x)-(m["active"].sum()+1)-5),
                 "training_saturation_fraction_abs_u_gt_4":float(np.mean(np.abs(standardized)>4)),
                 "pair_clustered_losses":pair_losses}
    return tr,data,diagnostics
def r0_execute(contract,manifest_path,meta_path,self1_path,self3_path,alloc_path,access=None):
    access = access if access is not None else new_access_state()
    if sha(contract)!=CONTRACT_SHA256 or sha(manifest_path)!=MANIFEST_SHA256 or sha(self3_path)!=SELF3_ALLOCATION_SHA256 or sha(meta_path)!=SOURCE_A0_SHA256 or sha(alloc_path)!=SRM4_ALLOCATION_SHA256: raise Invalid("R0 provenance mismatch")
    manifest=json.loads(Path(manifest_path).read_text()); meta=json.loads(Path(meta_path).read_text()); alloc=json.loads(Path(alloc_path).read_text())
    if alloc.get("contract_sha256")!=CONTRACT_SHA256 or alloc.get("manifest_sha256")!=MANIFEST_SHA256 or alloc.get("self1_brainvision_sha256")!=SELF1_SHA256 or alloc.get("self3_allocation_sha256")!=SELF3_ALLOCATION_SHA256: raise Invalid("R0 allocation linkage mismatch")
    index={r["trial_hash"]:r for r in manifest["trials"]}
    for r in alloc["trials"]:
        src=index.get(r["trial_hash"])
        if src is None or any(src.get(k)!=r.get(k) for k in ("session","word","task_anchor_s","rest_anchor_s")): raise Invalid("R0 allocation/manifest row mismatch")
    reader=load_reader(self1_path); pairs=r0_rows(reader,manifest,meta,alloc,access); results={}
    access["scientific_endpoint_opened"]=True; access["model_outcome_opened"]=True
    for held in ("ses-01","ses-02"):
        train=[p for p in pairs if p["session"]!=held]; test=[p for p in pairs if p["session"]==held]
        tr,d,diagnostics=r0_fit(train,test); results[held]={"d_eff":tr["d_eff"],"lambda2_over_lambda1":float(tr["eig"][1]/tr["eig"][0]),"losses":d,"diagnostics":diagnostics}
    pooled={}
    for c in ("task","rest"):
        sp=sum(results[s]["losses"][c]["sse_persistence"] for s in results); s0=sum(results[s]["losses"][c]["sse_m0"] for s in results); n=sum(results[s]["losses"][c]["count"] for s in results)
        pooled[c]={"sse_persistence":sp,"sse_m0":s0,"count":n,"L_p":sp/n,"L_0":s0/n,"B":(sp-s0)/sp}
    access["model_outcome_computed"]=True
    ok=pooled["task"]["B"]>0
    return {"schema":"BA-SRM4-real-eeg-v1","stage":"R0-SMALL","status":"R0_SMALL_PASS" if ok else "APPARATUS_INVALID_OR_BASELINE_UNRESOLVED",
            "network_accessed":access["network_accessed"],"signal_accessed":access["signal_accessed"],
            "scientific_endpoint_opened":access["scientific_endpoint_opened"],"model_outcome_opened":access["model_outcome_opened"],"model_outcome_computed":access["model_outcome_computed"],
            "contract_sha256":CONTRACT_SHA256,"manifest_sha256":MANIFEST_SHA256,"a0_receipt_sha256":SOURCE_A0_SHA256,"self1_brainvision_sha256":SELF1_SHA256,
            "self3_allocation_sha256":SELF3_ALLOCATION_SHA256,"srm4_allocation_sha256":SRM4_ALLOCATION_SHA256,
            "accepted_pairs":{"ses-01":5,"ses-02":5,"total":10},"directions":results,"pooled":pooled,
            "windows":access["completed_requests"],"path_area_opened":False,"ordered_history_gain_opened":False,"word_effect_opened":False,
            "unopened_splits":["R1-MEDIUM","R2-LARGE","C1","C2","C3"]}

def r0_safe(contract,manifest_path,meta_path,self1_path,self3_path,alloc_path):
    access=new_access_state()
    try:
        return r0_execute(contract,manifest_path,meta_path,self1_path,self3_path,alloc_path,access)
    except Exception as e:
        status="APPARATUS_INVALID_OR_BASELINE_UNRESOLVED" if access["network_accessed"] else "APPARATUS_INVALID_PROVENANCE"
        return {"schema":"BA-SRM4-real-eeg-v1","stage":"R0-SMALL","status":status,"error":f"{type(e).__name__}: {e}",
                "network_accessed":access["network_accessed"],"signal_accessed":access["signal_accessed"],
                "scientific_endpoint_opened":access["scientific_endpoint_opened"],"model_outcome_opened":access["model_outcome_opened"],
                "model_outcome_computed":access["model_outcome_computed"],"windows":access["completed_requests"],
                "path_area_opened":False,"ordered_history_gain_opened":False,"word_effect_opened":False,
                "unopened_splits":["R1-MEDIUM","R2-LARGE","C1","C2","C3"]}
def main():
    p=argparse.ArgumentParser(); p.add_argument("--stage",choices=STAGES,required=True); p.add_argument("--output",required=True); p.add_argument("--contract"); p.add_argument("--self3-allocation"); p.add_argument("--manifest"); p.add_argument("--a0-receipt"); p.add_argument("--self1-reader"); p.add_argument("--srm4-allocation"); p.add_argument("--execute",action="store_true"); a=p.parse_args()
    try:
        if a.stage=="A0-ALLOCATION": result=allocation(Path(a.self3_allocation))
        elif a.stage=="P0-SYNTHETIC": result=synthetic()
        else:
            if a.stage=="R0-SMALL" and a.execute:
                need=(a.contract,a.manifest,a.a0_receipt,a.self1_reader,a.self3_allocation,a.srm4_allocation)
                if not all(need): raise Invalid("R0 explicit provenance inputs required")
                result=r0_safe(Path(a.contract),Path(a.manifest),Path(a.a0_receipt),Path(a.self1_reader),Path(a.self3_allocation),Path(a.srm4_allocation))
            elif a.execute: raise Invalid("R1/R2 not implemented")
            else:
                result=preflight(a.stage,Path(a.contract))
    except Exception as e:
        result={"stage":a.stage,"status":"FAILED","error":f"{type(e).__name__}: {e}","signal_accessed":False,"scientific_endpoint_opened":False,"model_outcome_opened":False,"model_outcome_computed":False}
        dump(a.output,result); raise
    dump(a.output,result)
if __name__=="__main__": main()
