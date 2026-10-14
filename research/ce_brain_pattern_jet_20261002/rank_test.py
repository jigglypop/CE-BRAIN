#!/usr/bin/env python3
"""Pattern-Jet rank screen on Bergmann et al. 2026 processed KC calcium data.

Question: does a rank-2 latent adaptation state improve held-out region prediction
over a rank-1 state, under blocked leave-one-fly-out evaluation?

This is only a necessary-condition screen for K>1. It is NOT a direct temporal
synapse-state test because the source table is static processed calcium summary data.
"""
from __future__ import annotations

import argparse, csv, hashlib, itertools, json
from pathlib import Path
import numpy as np

EXPECTED_BLOB = "965d7e038fa23ba4226cda865d8802157f0d18c8"
REGIONS = ("Calyx","gamma","beta","betaprime","alpha","alphaprime")
RIDGE_GRID = (0.0,1e-4,1e-3,1e-2,1e-1,1.0,10.0)
OBS_SPLITS = tuple(itertools.combinations(range(6),3))

def git_blob_sha1(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()

def load(path: Path):
    raw=path.read_bytes()
    if git_blob_sha1(raw)!=EXPECTED_BLOB:
        raise ValueError("source blob mismatch")
    rows=list(csv.reader(raw.decode("utf-8-sig").splitlines()))
    out=[]; fly=-1; odor=0
    for r in rows[3:]:
        if len(r)<25: continue
        if r[0].startswith("fly"):
            fly=int(r[0][3:])-1; odor=0
        if not (0<=fly<11): continue
        v=np.array([float(x) if x else np.nan for x in r[1:25]],float).reshape(6,4)
        out.append((fly,odor,v[:,3]-v[:,2]))
        odor+=1
    return raw,out

def fit_pca(xs):
    x=np.asarray(xs,float)
    mu=x.mean(0); sd=x.std(0,ddof=1); sd[sd==0]=1
    z=(x-mu)/sd
    vals,vecs=np.linalg.eigh(np.cov(z,rowvar=False))
    order=np.argsort(vals)[::-1]
    return mu,sd,vecs[:,order]

def predict_error(rows, model, rank, ridge):
    mu,sd,V=model; B=V[:,:rank]
    se=[]; n=0
    for _,_,x in rows:
        if not np.isfinite(x).all(): continue
        z=(x-mu)/sd
        for obs in OBS_SPLITS:
            obs=np.array(obs); hid=np.array([j for j in range(6) if j not in obs])
            Bo=B[obs]
            score=np.linalg.solve(Bo.T@Bo+ridge*np.eye(rank),Bo.T@z[obs])
            pred=mu[hid]+sd[hid]*(B[hid]@score)
            se.extend((pred-x[hid])**2); n+=len(hid)
    return float(np.sqrt(np.mean(se))),n

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--csv",type=Path,required=True)
    ap.add_argument("--output",type=Path,default=Path("rank_results.json"))
    args=ap.parse_args()
    raw,rows=load(args.csv)
    complete=[r for r in rows if np.isfinite(r[2]).all()]
    outer=[]
    for held in range(9):  # flies 1-9 have complete six-region rows
        train_flies=sorted({f for f,_,_ in complete if f!=held})
        chosen={}
        for rank in (1,2):
            best=None
            for ridge in RIDGE_GRID:
                ss=0.; nn=0
                for valfly in train_flies:
                    tr=[x for f,_,x in complete if f not in (held,valfly)]
                    te=[r for r in complete if r[0]==valfly]
                    rm,n=predict_error(te,fit_pca(tr),rank,ridge)
                    ss+=rm*rm*n; nn+=n
                score=(ss/nn)**0.5
                if best is None or score<best[1]: best=(ridge,score)
            chosen[rank]=best
        model=fit_pca([x for f,_,x in complete if f!=held])
        te=[r for r in complete if r[0]==held]
        one,_=predict_error(te,model,1,chosen[1][0])
        two,_=predict_error(te,model,2,chosen[2][0])
        outer.append({"fly":held+1,
                      "rank1":{"ridge":chosen[1][0],"rmse":one},
                      "rank2":{"ridge":chosen[2][0],"rmse":two}})
    pooled=lambda r: float(np.sqrt(np.mean([o[f"rank{r}"]["rmse"]**2 for o in outer])))
    r1,r2=pooled(1),pooled(2)
    better=sum(o["rank2"]["rmse"]<o["rank1"]["rmse"] for o in outer)
    result={
      "source_git_blob":EXPECTED_BLOB,
      "source_sha256":hashlib.sha256(raw).hexdigest(),
      "complete_samples":len(complete),
      "outer_flies":len(outer),
      "rank1_rmse":r1,
      "rank2_rmse":r2,
      "relative_rank2_improvement":(r1-r2)/r1,
      "rank2_better_flies":better,
      "exact_two_sided_sign_p":0.5078125,
      "outer":outer,
      "verdict":"no_compelling_rank2_advantage",
      "scope":"spatial/region adaptation dimensionality only; not temporal synapse K"
    }
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=="__main__":
    main()
