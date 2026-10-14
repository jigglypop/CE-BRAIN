#!/usr/bin/env python3
"""Temporal Pattern-Jet validation on real C. elegans calcium traces."""
from __future__ import annotations
import argparse, csv, hashlib, io, json, math, urllib.request
from pathlib import Path
import numpy as np

URL = "https://raw.githubusercontent.com/Mighty-Stahl/Extended-Essay-Complete-Processing-Pipeline/840b910bc5103badc9bfbceb76408a1456574500/dFF.csv"
BLOB = "c85efb78c8aa1b5e2d61445190261bafec19d418"
KINDS = ("current","lag","cascade","parallel","finite")

def git_blob_sha1(raw):
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()

def load_data(path=None):
    raw=Path(path).read_bytes() if path else urllib.request.urlopen(URL).read()
    if git_blob_sha1(raw)!=BLOB: raise ValueError("source blob mismatch")
    d={}
    for r in csv.DictReader(io.StringIO(raw.decode())):
        o=d.setdefault(r["filename"],{"sex":r["sex"],"AVA":[],"AVB":[]})
        o[r["neuron"]].append((float(r["timepoint"]),float(r["dFF"])))
    out=[]
    for name,o in sorted(d.items()):
        for n in ("AVA","AVB"): o[n].sort()
        if len(o["AVA"])!=40 or len(o["AVB"])!=40: continue
        if any(abs(o["AVA"][i][0]-o["AVB"][i][0])>1e-9 for i in range(40)): continue
        out.append({"file":name,"sex":o["sex"],
                    "time":np.array([z[0] for z in o["AVA"]]),
                    "x":np.array([[o["AVA"][i][1],o["AVB"][i][1]] for i in range(40)])})
    return out

def feature_fn(x,K,kind):
    T=len(x); casc=[]; parallel=[]; finite=[]; prev=x.copy()
    for k in range(K):
        a=np.exp(-1/(2**k)); h=prev[0].copy(); d=np.zeros_like(prev); low=np.zeros_like(prev)
        for t in range(T):
            if t: h=a*h+(1-a)*prev[t]
            d[t]=prev[t]-h; low[t]=h
        casc.append(d); prev=low
        h=x[0].copy(); d=np.zeros_like(x)
        for t in range(T):
            if t: h=a*h+(1-a)*x[t]
            d[t]=x[t]-h
        parallel.append(d)
    fd=x.copy()
    for _ in range(K):
        nd=np.zeros_like(fd); nd[1:]=fd[1:]-fd[:-1]; finite.append(nd); fd=nd
    def at(t):
        f=list(x[t])
        if kind=="current": return np.asarray(f)
        if kind=="lag":
            for k in range(1,K+1): f.extend(x[t-k])
        elif kind=="cascade":
            for k in range(K): f.extend(casc[k][t])
        elif kind=="parallel":
            for k in range(K): f.extend(parallel[k][t])
        elif kind=="finite":
            for k in range(K): f.extend(finite[k][t])
        return np.asarray(f,float)
    return at

def rows(s,K,kind,h,burn=10):
    F=feature_fn(s["x"],K,kind)
    return [(F(t),s["x"][t+h]) for t in range(max(burn,K),40-h)]

def fit(rr,eps=1e-9):
    X=np.vstack([z[0] for z in rr]); Y=np.vstack([z[1] for z in rr])
    mx=X.mean(0); sx=X.std(0); sx[sx==0]=1; my=Y.mean(0); Z=(X-mx)/sx
    W=np.linalg.solve(Z.T@Z+eps*len(Z)*np.eye(Z.shape[1]),Z.T@(Y-my))
    return lambda x: my+((x-mx)/sx)@W

def sign_p(k,n):
    m=min(k,n-k)
    return min(1.0,2*sum(math.comb(n,i) for i in range(m+1))/2**n)

def evaluate(S,K,h):
    per={k:[] for k in KINDS}
    for oi in range(len(S)):
        for kind in KINDS:
            tr=[]
            for i,s in enumerate(S):
                if i!=oi: tr.extend(rows(s,K,kind,h))
            te=rows(S[oi],K,kind,h); pred=fit(tr)
            E=np.vstack([pred(x)-y for x,y in te])
            per[kind].append(float(np.sqrt(np.mean(E*E))))
    out={"K":K,"horizon":h}
    for k in KINDS: out[k+"_rmse"]=float(np.mean(per[k]))
    for other in ("current","lag","parallel","finite"):
        wins=sum(a<b for a,b in zip(per["cascade"],per[other]))
        out["cascade_vs_"+other]={"wins":wins,"n":len(S),"sign_p":sign_p(wins,len(S)),
            "reduction":(out[other+"_rmse"]-out["cascade_rmse"])/out[other+"_rmse"]}
    return out

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--csv"); ap.add_argument("--out",default="temporal_results_full.json")
    a=ap.parse_args(); S=load_data(a.csv)
    res={"source_blob":BLOB,"n_sessions":len(S),
         "results":[evaluate(S,K,h) for h in (1,2,4) for K in (1,2,4,8)]}
    Path(a.out).write_text(json.dumps(res,indent=2),encoding="utf-8")
    print(json.dumps(res,indent=2))
if __name__=="__main__": main()
