import numpy as np, time
import calib_power as C

def p_global(lmu, ls2, keep):
    x=lmu[keep]; y=ls2[keep]
    if x.size<4 or x.std()<1e-6: return np.nan
    return float(np.cov(x,y,ddof=1)[0,1]/np.var(x,ddof=1))

def p_local(lmu, ls2, half=3, sdmin=0.05):
    n=lmu.size; out=np.full(n,np.nan)
    for k in range(n):
        lo,hi=max(0,k-half),min(n,k+half+1)
        x=lmu[lo:hi]; y=ls2[lo:hi]
        if x.size<4 or x.std(ddof=1)<sdmin: continue
        out[k]=float(np.cov(x,y,ddof=1)[0,1]/np.var(x,ddof=1))
    return out

def terms(mu,s2,mode,keep=None):
    lmu,ls2=np.log(mu),np.log(s2)
    p = np.full(mu.size, p_global(lmu,ls2,keep)) if mode=="glob" else p_local(lmu,ls2)
    Phi = mu**2/s2 + p**2/2.0
    rho = (p**2/2.0)/Phi
    return Phi,p,rho,(2.0-p)*(1.0-rho)

def window(K):
    w=np.zeros(K,bool); w[C.EDGE_PAD:-C.EDGE_PAD]=True; return w

def sel(mu_e,s2_e,mu_l,K):
    k=window(K); k&=np.abs(np.log(mu_l)-np.log(mu_e))>=C.L_MIN
    k&=(np.sqrt(s2_e)/mu_e)<=C.CV_MAX; return k

def truth(wp, mode):
    K=int(round(C.T_END/C.BIN)); num=den=0.0; ps=[];rs=[];Rs=[];nb=0
    for e in wp:
        a=C.exact_chart(e["lam"][("early","A")])
        for cue in ("A","B"):
            mu_e,s2_e=C.exact_moments(e["lam"][("early",cue)],e["dlam"][("early",cue)],a)
            mu_l,s2_l=C.exact_moments(e["lam"][("late",cue)], e["dlam"][("late",cue)], a)
            keep=sel(mu_e,s2_e,mu_l,K)
            if keep.sum()<4: continue
            Pe,pe,re_,Re=terms(mu_e,s2_e,mode,keep); Pl,_,_,_=terms(mu_l,s2_l,mode,keep)
            L=np.log(mu_l)-np.log(mu_e); Y=np.log(Pl)-np.log(Pe)
            X=(Re-2.0)*L; Yp=Y-2.0*L
            ok=keep&np.isfinite(X)&np.isfinite(Yp)
            num+=float(np.sum(X[ok]*Yp[ok])); den+=float(np.sum(X[ok]**2))
            ps.append(np.nanmean(pe[ok])); rs.append(np.nanmean(re_[ok])); Rs.append(np.nanmean(Re[ok])); nb+=int(ok.sum())
    return dict(lam=round(num/den,4),p=round(float(np.nanmean(ps)),3),rho=round(float(np.nanmean(rs)),3),
                R=round(float(np.nanmean(Rs)),3),bins=nb)

wp=C.prepare_world("true",C.SEED)
for mode in ("glob","loc"):
    print(mode, truth(wp,mode))
