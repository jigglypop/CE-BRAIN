import numpy as np
import calib_power as C

def phi_terms(mu,s2):
    d=C.fisher_1d(mu,s2,C.DU)
    p=d["p"]; Phi = mu**2/s2 + p**2/2.0
    rho = (p**2/2.0)/Phi
    R = (2.0-p)*(1.0-rho)
    return Phi,p,rho,R,d

def truth_phi(sig_d=0.08, dw=0.18, vfac=1.25, gain=1.30, indicator=True):
    C.SIG_D=sig_d; C.LEARN_DW=dw; C.LEARN_VFAC=vfac; C.LEARN_GAIN=gain
    wp=C.prepare_world("true", C.SEED)
    K=int(round(C.T_END/C.BIN)); num=den=0.0; ps=[];rhos=[];Ls=[];nb=0;Rs=[]
    for e in wp:
        lam=e["lam"][("early","A")]
        resp = lam[:, 3:24].mean(1) - lam[:, :2].mean(1)
        if indicator:
            S=resp>0
            if S.sum()<3: continue
            a=S.astype(float)/S.sum()
        else:
            a=np.maximum(resp,0); a/=np.linalg.norm(a)
        for cue in ("A","B"):
            mu_e,s2_e=C.exact_moments(e["lam"][("early",cue)],e["dlam"][("early",cue)],a)
            mu_l,s2_l=C.exact_moments(e["lam"][("late",cue)], e["dlam"][("late",cue)], a)
            Pe,pe,re_,Re,de=phi_terms(mu_e,s2_e); Pl,_,_,_,dl=phi_terms(mu_l,s2_l)
            L=np.log(mu_l)-np.log(mu_e); Y=np.log(Pl)-np.log(Pe)
            keep=C.select_bins(mu_e,s2_e,mu_l,K)
            if keep.sum()<3: continue
            Xr=(Re-2.0)*L; Yp=Y-2.0*L
            num+=float(np.sum(Xr[keep]*Yp[keep])); den+=float(np.sum(Xr[keep]**2))
            ps.append(np.mean(pe[keep])); rhos.append(np.mean(re_[keep])); Rs.append(np.mean(Re[keep]))
            Ls.append(np.mean(L[keep])); nb+=int(keep.sum())
    return dict(lam=round(num/den,4), p=round(float(np.mean(ps)),3), rho=round(float(np.mean(rhos)),3),
                R=round(float(np.mean(Rs)),3), logalpha=round(float(np.mean(Ls)),3), bins=nb)

print("Phi indicator full  ", truth_phi())
print("Phi indicator nojit ", truth_phi(sig_d=0.0))
print("Phi indicator clean ", truth_phi(sig_d=0.0,dw=0.0,vfac=1.0))
print("Phi weighted  full  ", truth_phi(indicator=False))
print("Phi weighted  nojit ", truth_phi(sig_d=0.0, indicator=False))
