# -*- coding: utf-8 -*-
"""A7. 극한과 카드가 주장한 불변성.
(1) L->0 : 학습 gain 을 1 로 보내면 X=(R-2)L -> 0, IV 는 0/0. 게이트가 막는가.
(2) bin 재척도 0.05 -> 0.10 s : predicts[0] 이 'bin 재척도에 불변'이라 주장한다.
(3) L_MIN, CV_MAX, SD_LMU_MIN 섭동 (사다리 6단의 사전 확인)."""
from __future__ import annotations
import json, sys, numpy as np
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
import calib_power as C
HERE=Path(__file__).resolve().parent

def gt(wp):
    K=int(round(C.T_END/C.BIN)); num=den=0.0; Rs=[]; nb=0; Ls=[]
    for e in wp:
        a=C.exact_chart(e["lam"][("early","A")])
        for cue in ("A","B"):
            mu_e,s2_e=C.exact_moments(e["lam"][("early",cue)],e["dlam"][("early",cue)],a)
            mu_l,s2_l=C.exact_moments(e["lam"][("late",cue)],e["dlam"][("late",cue)],a)
            keep=C.select_bins(mu_e,s2_e,mu_l,K)
            if keep.sum()<4: continue
            X,Y=C.xy(mu_e,s2_e,mu_l,s2_l,keep)
            if X is None: continue
            num+=float(np.sum(X[keep]*Y[keep])); den+=float(np.sum(X[keep]**2))
            p=C.fit_p(mu_e,s2_e,keep); Rs.append(float(np.mean(C.phi_terms(mu_e,s2_e,p)["R"][keep])))
            Ls.append(float(np.mean(np.abs(np.log(mu_l)-np.log(mu_e))[keep]))); nb+=int(keep.sum())
    if not Rs or abs(den)<1e-12: return {"bins":nb,"lam_true":None,"Gamma":None,"note":"0/0"}
    R=float(np.mean(Rs))
    return {"bins":nb,"lam_true":round(num/den,4),"Gamma":round(2-R,4),"mean|L|":round(float(np.mean(Ls)),4)}

def finite(wp,nrep=25,nboot=300):
    rng=np.random.default_rng(C.SEED); K=int(round(C.T_END/C.BIN)); g=0; lams=[]
    for _ in range(nrep):
        pools={}
        for mi,e in enumerate(wp):
            cnt={(ph,cu):C.draw_counts(rng,e["lam"][(ph,cu)],e["dlam"][(ph,cu)],C.TRIALS[cu])
                 for ph in ("early","late") for cu in ("A","B")}
            a=C.fit_chart(np.concatenate([cnt[("early","A")][0::2],cnt[("early","B")][0::2]],0))
            got=[t for cu in ("A","B") if (t:=C.pair_terms(cnt[("early",cu)],cnt[("late",cu)],a,K)) is not None]
            if got: pools[mi]=got
        r=C.boot(pools,rng,nboot=nboot)
        if r and r["den"]>0 and r["den_lo"]>0: g+=1; lams.append(r["lam"])
    C.RAW_RANK.clear()
    return {"gate_pass":round(g/nrep,3),"lam_hat_median":round(float(np.median(lams)),3) if lams else None,
            "lam_hat_q05":round(float(np.percentile(lams,5)),3) if lams else None,
            "lam_hat_q95":round(float(np.percentile(lams,95)),3) if lams else None}

out={"note":"A7 극한·불변성","rows":[]}
base=dict(DW=C.LEARN_DW,GN=C.LEARN_GAIN,VF=C.LEARN_VFAC,BIN=C.BIN,DU=C.DU,
          LMIN=C.L_MIN,CVM=C.CV_MAX,SDM=C.SD_LMU_MIN)
def restore():
    C.LEARN_DW,C.LEARN_GAIN,C.LEARN_VFAC=base["DW"],base["GN"],base["VF"]
    C.BIN,C.DU=base["BIN"],base["DU"]; C.L_MIN,C.CV_MAX,C.SD_LMU_MIN=base["LMIN"],base["CVM"],base["SDM"]

# (1) L -> 0
for g in (1.30,1.15,1.07,1.03,1.01,1.00):
    restore(); C.LEARN_GAIN=g; C.LEARN_DW=0.18*(g-1)/0.30; C.LEARN_VFAC=1.0+0.25*(g-1)/0.30
    wp=C.prepare_world("true",C.SEED+0)
    out["rows"].append({"case":"L->0 gain=%.2f"%g, **gt(wp), **finite(wp)})
# (2) bin 재척도
for b in (0.05,0.10):
    restore(); C.BIN=b; C.DU=b
    wp=C.prepare_world("true",C.SEED+0)
    out["rows"].append({"case":"bin=%.2fs"%b, **gt(wp), **finite(wp)})
# (3) 문턱 섭동
restore(); wp=C.prepare_world("true",C.SEED+0)
for nm,k,v in [("L_MIN","L_MIN",0.05),("L_MIN","L_MIN",0.20),("CV_MAX","CV_MAX",1.0),
               ("CV_MAX","CV_MAX",4.0),("SD_LMU_MIN","SD_LMU_MIN",0.05),("SD_LMU_MIN","SD_LMU_MIN",0.20)]:
    restore(); setattr(C,k,v)
    out["rows"].append({"case":"%s=%.2f"%(nm,v), **gt(wp), **finite(wp)})
restore()
(HERE/"a7_limits.json").write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding="utf-8")
for r in out["rows"]: print(r)
