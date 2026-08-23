"""BA-SRM7 staged neural input audit; it never reads behavioral values before lock."""
from __future__ import annotations

import argparse, hashlib, json, math, os, time
from pathlib import Path
from typing import Any

import numpy as np
from scipy.io import loadmat
from scipy.ndimage import binary_dilation, binary_erosion
from scipy.optimize import curve_fit
from scipy.signal import medfilt

W, H, GUARD, EMBARGO, GAP_FACTOR = 60, 6, 12, 12, 3.0
ARCHIVES = {
 "AML310_moving.tar.gz": (348444164,"144126ee9a49d311c3393deea434e1a0963d55de35318e25d98d48f9c175250a"),
 "AML32_moving.tar.gz": (1218075251,"6b71a6ba1a5d2f1ef3bf9661e845e1e52634bae217fc0c2630a83fca07daed63"),
 "AML18_moving.tar.gz": (1409801111,"588d7666f4e8afebad1ab9b8483244a6de0303251d862425522c2b8dd78bbd82"), }
ROOTS = {"AKS297.51_moving":("gcamp","AKS297.51_moving_datasets.txt"),"AML32_moving":("gcamp","AML32_moving_datasets.txt"),"AML18_moving":("gfp","AML18_moving_datasets.txt")}
G = {x:"train" for x in ("BrainScanner20200130_105254","BrainScanner20200130_110803","BrainScanner20170424_105620","BrainScanner20170610_105634","BrainScanner20170613_134800","BrainScanner20180709_100433","BrainScanner20200309_151024")}
G.update({"BrainScanner20200310_141211":"validation","BrainScanner20200309_153839":"validation","BrainScanner20200310_142022":"held_out","BrainScanner20200309_162140":"held_out"})
_gfp=("BrainScanner20200116_145254","BrainScanner20200116_152636","BrainScanner20200204_102136","BrainScanner20200310_153952","BrainScanner20200311_100140","BrainScanner20200929_140030","BrainScanner20200929_143439","BrainScanner20210503_122703","BrainScanner20210503_135244","BrainScanner20210503_151831","BrainScanner20210503_154404")
P={x:("train" if i<7 else "validation" if i<9 else "held_out") for i,x in enumerate(_gfp)}
EX={"BrainScanner20200130_105254":((65.,75.),),"BrainScanner20200310_141211":((200.,210.),(240.,250.)),"BrainScanner20200309_151024":((30.,40.),(125.,135.)),"BrainScanner20200309_153839":((35.,45.),(160.,170.)),"BrainScanner20200309_162140":((0.,10.),(300.,310.))}

def sha(p:Path)->str:
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(1048576),b""):h.update(b)
 return h.hexdigest()
def dump_fsync(p:Path,x:Any)->None:
 with p.open("w",encoding="utf-8",newline="\n") as f: json.dump(x,f,sort_keys=True,indent=2,allow_nan=False); f.write("\n"); f.flush(); os.fsync(f.fileno())
def logrows(p:Path):
 for s in p.read_text().splitlines():
  s=s.split("#",1)[0].strip()
  if s:
   q=s.split(); yield q[0], (int(q[1]) if len(q)>1 else None)
def expf(x,a,b,c): return a*np.exp(-b*x)+c
def photo(raw:np.ndarray)->tuple[np.ndarray,int]:
 """Published 12.6-second, 6-Hz median/exponential rule; one audit fallback."""
 n,t=raw.shape; out=raw.copy(); fallback=0; x=np.arange(t,dtype=float)/6.; mw=77
 sm=medfilt(raw,kernel_size=(1,mw))
 for i in range(n):
  y=sm[i]; ok=np.isfinite(y); identity=False
  try:
   if ok.sum()<4 or not np.isfinite(np.nanmean(y)) or abs(np.nanmean(y))<=1e-12: raise ValueError()
   scale=float(np.nanmean(y)); ys=y/scale; xmax=float(x[-1]);
   bounds=([0.,1./(8.*xmax),0.],[float(np.nanmax(ys[ok])*1.5),.5,float(2*np.nanmean(ys))])
   p,_=curve_fit(expf,x[ok],ys[ok],p0=[np.nanmax(ys)/2.,2./xmax,np.nanmean(ys)],bounds=bounds)
   resid=ys-expf(x,*p); good=ok & (np.abs(resid)<=3*np.nanstd(resid))
   p,_=curve_fit(expf,x[good],ys[good],p0=p,bounds=bounds)
   p=np.asarray(p); p[[0,2]]*=scale; curve=expf(x,*p)
   if not np.all(np.isfinite(curve)) or np.nansum((raw[i]-curve)**2)>np.nansum((raw[i]-np.nanmean(raw[i]))**2): identity=True
  except Exception: identity=True
  if identity: fallback+=1
  else: out[i]=p[0]*raw[i]/curve
 return out,fallback
def closeholes(a):
 st=np.zeros((3,3),dtype=int);st[1,:]=1; nan=np.isnan(a); return np.where(binary_erosion(binary_dilation(nan,structure=st),structure=st),np.nan,a)
def causal(a):
 w=np.exp(-(np.arange(21,dtype=float)**2)/(2*25.)); out=np.full_like(a,np.nan)
 for t in range(a.shape[1]):
  z=a[:,max(0,t-20):t+1]; ww=w[:z.shape[1]][::-1]; m=np.isfinite(z); den=m@ww; num=np.nan_to_num(z,nan=0.)@ww; np.divide(num,den,out=out[:,t],where=den>0)
 return out
def split_anchors(clock, raw_index, rid, usable, kept, z):
 pos=np.diff(clock); pos=pos[np.isfinite(pos)&(pos>0)]; gap=GAP_FACTOR*np.median(pos) if pos.size else np.nan
 e1,e2=int(.6*usable),int(.8*usable); domains=[d for d in (2,4,8,16,32,48) if d<min(int(kept.sum()),W-1)]
 ids={"train":[],"validation":[],"test":[]}; total={"train":0,"validation":0,"test":0}; badgap=0
 # Fixed-d eigengap is checked on this neural-only, causal feature anchor set.
 for a in range(W-1,usable-H):
  s=a-W+1; stop=a+H
  if s<GUARD: continue
  ds=np.diff(clock[s:stop+1]); loc=clock[s:stop+1]
  if not(np.all(np.isfinite(ds)&(ds>0)&(ds<=gap))) or any(np.any((loc>=l)&(loc<=r)) for l,r in EX.get(rid,())): badgap+=1; continue
  role="train" if stop<e1-EMBARGO else "validation" if s>=e1+EMBARGO and stop<e2-EMBARGO else "test" if s>=e2+EMBARGO else None
  if role is None: continue
  total[role]+=1
  if not domains: continue
  # z is complete after prefix-only impute, so small Gram matrix preserves PSD.
  zz=z[:,s:a+1]; eig=np.linalg.eigvalsh((zz.T@zz)/(W-1))[::-1]; mx=max(float(eig[0]),1e-12)
  if any((eig[d-1]-eig[d])/mx<=1e-12 for d in domains if d<len(eig)): badgap+=1; continue
  ids[role].append(int(raw_index[a]))
 canonical={k:json.dumps(v,separators=(",",":")) for k,v in ids.items()}
 digest={k:hashlib.sha256(canonical[k].encode("utf-8")).hexdigest() for k in ids}
 meta={k:{"count":len(ids[k]),"ids_sha256":digest[k],"first_id":ids[k][0] if ids[k] else None,"last_id":ids[k][-1] if ids[k] else None} for k in ids}
 return meta,total,domains,badgap
def neural_record(p,rid,cut,cls,role):
 d=loadmat(p,variable_names=("rRaw","gRaw","rPhotoCorr","gPhotoCorr","hasPointsTime","flagged_volumes"),simplify_cells=True)
 req=("rRaw","gRaw","rPhotoCorr","gPhotoCorr","hasPointsTime"); missing=[x for x in req if x not in d]
 base={"recording_id":rid,"signal_class":cls,"outer_role":role,"cut_volume":cut,"mat_bytes":p.stat().st_size,"mat_sha256":sha(p),"raw_schema_missing":missing}
 if missing:return base|{"schema_passed":False}
 clock=np.asarray(d["hasPointsTime"],float).reshape(-1); full=clock.size; raw_stop=min(full,(cut+1 if cut is not None else full)); clock=clock[:raw_stop]
 rawr=np.asarray(d["rRaw"],float)[:,:raw_stop]; rawg=np.asarray(d["gRaw"],float)[:,:raw_stop]; pr=np.asarray(d["rPhotoCorr"],float)[:,:raw_stop]; pg=np.asarray(d["gPhotoCorr"],float)[:,:raw_stop]
 # Published manual exclusions act on the original (uncompressed) raw volume sequence.
 original_index=np.arange(raw_stop); excluded=np.zeros(raw_stop,dtype=bool)
 for left,right in EX.get(rid,()): excluded |= (clock>=left)&(clock<=right)
 keep_raw=~excluded; original_index=original_index[keep_raw]; clock=clock[keep_raw]; rawr=rawr[:,keep_raw]; rawg=rawg[:,keep_raw]; pr=pr[:,keep_raw]; pg=pg[:,keep_raw]; use=clock.size
 schema=rawr.ndim==2 and rawr.shape==rawg.shape==pr.shape==pg.shape and rawr.shape[1]==use
 if not schema:return base|{"schema_passed":False,"raw_shapes":[list(x.shape) for x in (rawr,rawg,pr,pg)],"clock_shape":list(clock.shape)}
 cal=int(.6*use)
 # Fit prefix, evaluate raw channels on the entire retained timeline with frozen fits.
 # Re-running the same routine on full data would leak; apply per-channel parameters via prefix correction ratio is intentionally unavailable.
 # Thus construct corrected traces using prefix-derived normalized correction factors by a single prefix fit helper below.
 def corr_all(raw):
  # Same published fit, only prefix observed; reconstruct each curve deterministically.
  out=raw.copy(); falls=0; x=original_index[:cal].astype(float)/6.; xa=original_index.astype(float)/6.; sm=medfilt(raw[:,:cal],(1,77))
  for i in range(raw.shape[0]):
   y=sm[i]; ok=np.isfinite(y); identity=False
   try:
    scale=float(np.nanmean(y)); xmax=float(x[-1]); ys=y/scale
    if ok.sum()<4 or not np.isfinite(scale) or abs(scale)<=1e-12: raise ValueError()
    bounds=([0.,1/(8*xmax),0.],[float(np.nanmax(ys[ok])*1.5),.5,float(2*np.nanmean(ys))]); pp,_=curve_fit(expf,x[ok],ys[ok],p0=[np.nanmax(ys)/2,2/xmax,np.nanmean(ys)],bounds=bounds)
    rr=ys-expf(x,*pp); good=ok&(np.abs(rr)<=3*np.nanstd(rr)); pp,_=curve_fit(expf,x[good],ys[good],p0=pp,bounds=bounds); pp=np.asarray(pp); pp[[0,2]]*=scale; cv=expf(xa,*pp)
    if not np.all(np.isfinite(cv)) or np.nansum((raw[i,:cal]-expf(x,*pp))**2)>np.nansum((raw[i,:cal]-np.nanmean(raw[i,:cal]))**2):identity=True
   except Exception:identity=True
   if identity:falls+=1
   else:out[i]=pp[0]*raw[i]/cv
  return out,falls
 R,fr=corr_all(rawr); Gc,fg=corr_all(rawg); R[np.isnan(pr)]=np.nan; Gc[np.isnan(pg)]=np.nan; R=closeholes(R); Gc=closeholes(Gc)
 if "flagged_volumes" in d and np.asarray(d["flagged_volumes"]).size:
  ix=np.asarray(d["flagged_volumes"]).reshape(-1).astype(int); ix=ix[(ix>=0)&(ix<raw_stop)]; ix=np.flatnonzero(np.isin(original_index,ix)); R[:,ix]=np.nan;Gc[:,ix]=np.nan
 I=np.full_like(Gc,np.nan)
 for i in range(I.shape[0]):
  ok=np.isfinite(R[i,:cal])&np.isfinite(Gc[i,:cal])
  if ok.sum()>=2: b,c=np.linalg.lstsq(np.c_[R[i,:cal][ok],np.ones(ok.sum())],Gc[i,:cal][ok],rcond=None)[0]; I[i]=Gc[i]-(b*R[i]+c)
 mask=np.isfinite(I); valid=np.mean(~mask,axis=0)<.5
 # The source majority-missing rule defines the retained (possibly noncontiguous) sequence.
 I, R, clock, original_index = I[:,valid], R[:,valid], clock[valid], original_index[valid]
 processed=int(.6*clock.size); ci=causal(I); cr=causal(R); finite=np.sum(np.isfinite(I[:,:processed]),axis=1); sd=np.nanstd(ci[:,:processed],axis=1); kept=(finite>=W)&np.isfinite(sd)&(sd>1e-12); redfinite=np.sum(np.isfinite(R[:,:processed]),axis=1); redsd=np.nanstd(cr[:,:processed],axis=1); redkept=(redfinite>=W)&np.isfinite(redsd)&(redsd>1e-12)
 mean=np.nanmean(ci[kept,:processed],axis=1); scale=np.nanstd(ci[kept,:processed],axis=1); zz=(np.where(np.isfinite(ci[kept]),ci[kept],mean[:,None])-mean[:,None])/scale[:,None]
 ac,at,domain,eg=split_anchors(clock,original_index,rid,clock.size,kept,zz)
 pos=np.diff(clock); pos=pos[np.isfinite(pos)&(pos>0)]
 unitok=bool(kept.sum()>0 and redkept.sum()>0); anchorok=bool(min((x["count"] for x in ac.values()),default=0)>=100)
 return base|{"schema_passed":True,"full_timepoints":int(full),"raw_before_manual_exclusion_timepoints":int(raw_stop),"raw_manual_excluded_timepoints":int(excluded.sum()),"raw_retained_timepoints":int(use),"usable_timepoints":int(clock.size),"raw_shape":list(rawr.shape),"clock_shape":list(clock.shape),"clock_strictly_increasing":bool(clock.size>1 and np.all(np.diff(clock)>0)),"clock_positive_step_min":float(np.min(pos)) if pos.size else None,"clock_positive_step_median":float(np.median(pos)) if pos.size else None,"photobleach_identity_fallbacks":{"red":int(fr),"green":int(fg)},"valid_timepoints":int(valid.sum()),"raw_calibration_timepoints":int(cal),"processed_calibration_timepoints":int(processed),"kept_primary_units":int(kept.sum()),"kept_red_units":int(redkept.sum()),"r_star":int(min(kept.sum(),W-1)),"red_r_star":int(min(redkept.sum(),W-1)),"unit_eligibility_passed":unitok,"fixed_d_domain":domain,"feature_common_anchors":ac,"feature_common_anchor_counts":{k:v["count"] for k,v in ac.items()},"feature_common_anchors_passed":anchorok,"pre_eigengap_anchor_counts":at,"projector_unidentified_or_clock_rejected":int(eg),"eligibility_passed":unitok}
def main():
 ap=argparse.ArgumentParser(); ap.add_argument("--output",required=True); a=ap.parse_args(); start=time.time(); repo=Path(__file__).resolve().parents[4]; root=repo/"data/external/ba_srm6"; ext=root/"extracted"; art=Path(__file__).parent
 ar=[]
 for n,(bs,h) in ARCHIVES.items():
  p=root/n; ar.append({"name":n,"bytes":p.stat().st_size,"expected_bytes":bs,"sha256":sha(p),"expected_sha256":h,"passed":p.exists() and p.stat().st_size==bs and sha(p)==h})
 rec=[]
 for rn,(cls,lg) in ROOTS.items():
  for rid,cut in logrows(ext/rn/lg): rec.append(neural_record(ext/rn/(rid+"_MS")/"heatDataMS.mat",rid,cut,cls,(G if cls=="gcamp" else P)[rid]))
 source=art/"source-lock.json"; sl=json.loads(source.read_text(encoding="utf-8")); code_root=repo/"data/external/ba_srm7/PredictionCode"
 code_rows=[]
 for item in sl["code"]["files"]:
  cp=code_root/item["path"]; actual=sha(cp) if cp.exists() else None
  code_rows.append({"path":item["path"],"sha256":actual,"expected_sha256":item["sha256"],"passed":actual==item["sha256"]})
 schemaok=all(x.get("schema_passed") for x in rec); sourceok=all(x["passed"] for x in code_rows); elig=all(x.get("eligibility_passed") for x in rec); anchor=all(min(x.get("feature_common_anchor_counts",{}).values(),default=0)>=100 for x in rec); passed=all(x["passed"] for x in ar) and sourceok and schemaok and elig and anchor
 lock={"schema":"ce.ba_srm7.neural_input_lock.v1","source_lock_sha256":sha(source),"source_code_files":code_rows,"archives":ar,"recordings":sorted(rec,key=lambda x:x["recording_id"]),"prior_attempt_hashes":{"attempt_00_input_audit":"33b53190ab695ffca7d0733a3378cb144dc56017df94c1ae46d8504eab383f35","attempt_00_neural_lock":"4ea47d78cee5941cbd7eb7f409292e63f59cdb6d493d6aa8f93b60f887b815bf","attempt_01_input_audit":"605a4d3cab45c14d6fe934ed80ded904737879174ab261eb85a89f347b12162f","attempt_01_neural_lock":"561f81240b7b40ec4807bb5fd580686f60ec963675d0f927ced7656bd8babc08"},"summary":{"archive_passed":all(x["passed"] for x in ar),"source_code_passed":sourceok,"schema_passed":schemaok,"eligibility_passed":elig,"feature_common_anchors_passed":anchor,"neural_lock_passed":passed},"behavior_loaded":False,"neural_lock_created_before_behavior":True}
 lp=art/"neural-input-lock.json"; dump_fsync(lp,lock); lh=sha(lp)
 # Behavior struct is unreachable unless the neural input lock already passes.
 beh=[]
 if passed:
  for row in rec:
   mp=next(ext/rn/(row["recording_id"]+"_MS")/"heatDataMS.mat" for rn,(cl,lg) in ROOTS.items() if (ext/rn/(row["recording_id"]+"_MS")/"heatDataMS.mat").exists())
   b=loadmat(mp,variable_names=("behavior","hasPointsTime"),simplify_cells=True); q=b.get("behavior",{}); use=row.get("usable_timepoints",0); beh.append({"recording_id":row["recording_id"],"behavior_fields":sorted(q.keys()) if isinstance(q,dict) else [],"v_shape":list(np.asarray(q["v"]).shape) if isinstance(q,dict) and "v" in q else None,"pc1_2_shape":list(np.asarray(q["pc1_2"]).shape) if isinstance(q,dict) and "pc1_2" in q else None,"clock_length":int(np.asarray(b["hasPointsTime"]).size),"retained_clock_length":use})
 else: beh=[{"status":"SKIPPED_NEURAL_LOCK_FAIL"}]
 attempts={"attempt_00":{"input_audit_sha256":"33b53190ab695ffca7d0733a3378cb144dc56017df94c1ae46d8504eab383f35","neural_input_lock_sha256":"4ea47d78cee5941cbd7eb7f409292e63f59cdb6d493d6aa8f93b60f887b815bf","staging":"behavior shape loaded after an incomplete neural lock; values were not scored"},"attempt_01":{"input_audit_sha256":"605a4d3cab45c14d6fe934ed80ded904737879174ab261eb85a89f347b12162f","neural_input_lock_sha256":"561f81240b7b40ec4807bb5fd580686f60ec963675d0f927ced7656bd8babc08","staging":"manual exclusions and behavior lock staging corrected, but receipt fields incomplete"},"prior_attempt_behavior_shape_loaded":True,"prior_attempt_behavior_values_scored":False}
 out={"schema":"ce.ba_srm7.input_audit.v1","neural_input_lock_sha256":lh,"neural_lock_created_before_behavior":True,"behavior_values_scored":False,"model_fit":False,"validation_opened":False,"test_opened":False,"endpoint_opened":False,"prior_attempt":attempts,"records":sorted(rec,key=lambda x:x["recording_id"]),"behavior_schema_after_lock":sorted(beh,key=lambda x:str(x.get("recording_id",""))),"summary":{"archive_passed":all(x["passed"] for x in ar),"source_code_passed":sourceok,"schema_passed":schemaok,"eligibility_passed":elig,"feature_common_anchors_passed":anchor,"input_passed":passed},"runtime_seconds":round(time.time()-start,3)}; dump_fsync(Path(a.output),out)
if __name__=="__main__":main()
