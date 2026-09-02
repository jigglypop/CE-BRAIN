import numpy as np
import calib_power as C

def truth_ind(sig_d=0.08, dw=0.18, vfac=1.25, gain=1.30, indicator=True):
    C.SIG_D=sig_d; C.LEARN_DW=dw; C.LEARN_VFAC=vfac; C.LEARN_GAIN=gain
    wp=C.prepare_world("true", C.SEED)
    K=int(round(C.T_END/C.BIN)); num=den=0.0; ps=[];rhos=[];Ls=[];nb=0
    for e in wp:
        lam=e["lam"][("early","A")]
        resp = lam[:, 3:24].mean(1) - lam[:, :2].mean(1)
        if indicator:
            S = resp > 0
            if S.sum()<3: continue
            a = S.astype(float)/S.sum()
        else:
            a = np.maximum(resp,0); a/=np.linalg.norm(a)
        for cue in ("A","B"):
            mu_e,s2_e = C.exact_moments(e["lam"][("early",cue)], e["dlam"][("early",cue)], a)
            mu_l,s2_l = C.exact_moments(e["lam"][("late",cue)],  e["dlam"][("late",cue)],  a)
            Xr,Yp,de,dl,L = C.contrast_terms(mu_e,s2_e,mu_l,s2_l)
            keep=C.select_bins(mu_e,s2_e,mu_l,K)
            if keep.sum()<3: continue
            num+=float(np.sum(Xr[keep]*Yp[keep])); den+=float(np.sum(Xr[keep]**2))
            ps.append(np.mean(de["p"][keep])); rhos.append(np.mean(de["rho"][keep]))
            Ls.append(np.mean(L[keep])); nb+=int(keep.sum())
    R=(2-np.mean(ps))*(1-np.mean(rhos))
    return dict(lam=round(num/den,4), p=round(float(np.mean(ps)),3), rho=round(float(np.mean(rhos)),3),
                R=round(float(R),3), logalpha=round(float(np.mean(Ls)),3), bins=nb)

print("indicator, full learn ", truth_ind())
print("indicator, no jitter  ", truth_ind(sig_d=0.0))
print("indicator, gain only  ", truth_ind(dw=0.0, vfac=1.0))
print("indicator, clean      ", truth_ind(sig_d=0.0, dw=0.0, vfac=1.0))
print("weighted , full learn ", truth_ind(indicator=False))
