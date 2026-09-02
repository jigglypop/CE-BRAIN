# -*- coding: utf-8 -*-
"""A5. 추정기 편향 시험. late phase 공유변동 배수 k 를 훑어 참값 Lam_true(k) 를
정확 모멘트로 계산하고, 같은 세계의 유한표본 Lam_hat 과 비교한다.
(동결 코드 truth() 는 hist 세계에서도 nu=NU_G 를 써 lam_true=0.988 을 잘못 보고한다.)
k=1 은 카드가 참인 세계, k=3 은 W_hist."""
from __future__ import annotations
import json, sys, numpy as np
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import calib_power as C
HERE=Path(__file__).resolve().parent
K=int(round(C.T_END/C.BIN))

def moms(lam,dlam,a,nu):
    mu=a@lam; Cc=a@dlam; nup=np.exp(nu)-1.0
    return mu, (a**2)@lam + nup*mu**2 + (1.0+nup)*C.SIG_D**2*Cc**2

def truth_k(wp,k):
    num=den=0.0
    for e in wp:
        a=C.exact_chart(e["lam"][("early","A")])
        for cue in ("A","B"):
            mu_e,s2_e=moms(e["lam"][("early",cue)],e["dlam"][("early",cue)],a,C.NU_G)
            mu_l,s2_l=moms(e["lam"][("late",cue)],e["dlam"][("late",cue)],a,C.NU_G*k)
            keep=C.select_bins(mu_e,s2_e,mu_l,K)
            if keep.sum()<4: continue
            X,Y=C.xy(mu_e,s2_e,mu_l,s2_l,keep)
            if X is None: continue
            num+=float(np.sum(X[keep]*Y[keep])); den+=float(np.sum(X[keep]**2))
    return num/den

def rep_k(wp,k,rng,nrep):
    lams=[]
    for _ in range(nrep):
        pools={}
        for mi,e in enumerate(wp):
            cnt={}
            for phase in ("early","late"):
                for cue in ("A","B"):
                    nu=C.NU_G*(k if phase=="late" else 1.0)
                    cnt[(phase,cue)]=C.draw_counts(rng,e["lam"][(phase,cue)],e["dlam"][(phase,cue)],C.TRIALS[cue],nu=nu)
            a=C.fit_chart(np.concatenate([cnt[("early","A")][0::2],cnt[("early","B")][0::2]],0))
            got=[t for cue in ("A","B") if (t:=C.pair_terms(cnt[("early",cue)],cnt[("late",cue)],a,K)) is not None]
            if got: pools[mi]=got
        r=C.boot(pools,rng,nboot=400)
        if r: lams.append(r["lam"])
    C.RAW_RANK.clear()
    return lams

out={"note":"A5 추정기 편향(IV 가 참값을 되찾는가)","rows":[]}
wp=C.prepare_world("true", C.SEED+0)
rng=np.random.default_rng(C.SEED)
for k in (0.2,0.5,1.0,1.5,2.0,3.0):
    lt=truth_k(wp,k); ls=rep_k(wp,k,rng,40)
    out["rows"].append({"late_shared_var_x":k,"lam_true_exact":round(lt,4),
        "lam_hat_median":round(float(np.median(ls)),4),
        "bias":round(float(np.median(ls))-lt,4),
        "lam_hat_q05":round(float(np.percentile(ls,5)),4),
        "lam_hat_q95":round(float(np.percentile(ls,95)),4),"n":len(ls)})
(HERE/"a5_estimator.json").write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding="utf-8")
for r in out["rows"]: print(r)
