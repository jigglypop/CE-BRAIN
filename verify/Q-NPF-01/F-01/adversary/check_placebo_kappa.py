# -*- coding: utf-8 -*-
"""kill 2 (placebo) conditioning + kappa null geometry.  Seed 20260902.
   placebo: same phase, odd/even interleaved fold => NO learning-time difference => Dtau_plac ~ 0.
   Card: beta1_plac = Cov(trE_plac, T_plac)/Var(T_plac), T_plac = -Dtau_plac * d_u logV.
   Since T_plac is proportional to Dtau_plac ~ 0, beta1_plac is a ratio of two ~zero quantities."""
import numpy as np
rng = np.random.default_rng(20260902)
UG = np.array([0.45,0.75,1.05]); H = 0.3
def ols(T,y): return np.linalg.lstsq(np.vstack([T,np.ones(len(T))]).T, y, rcond=None)[0][0]

print("== A. beta1_plac is a ratio of two zero-mean normals => Cauchy (0/0) ==")
print(f"{'sigma_L':>8s} {'sigma_tau(s)':>12s} {'P(|median_8 b1p|>0.30)':>24s} {'median|b1p| (1 draw)':>21s}")
for sL in (0.05,0.10,0.20):
    for st in (0.005,0.010,0.030,0.050):
        trips=0; NS=4000; single=[]
        for _ in range(NS):
            bs=[]
            for m in range(8):
                s_u = rng.normal(0,1.0,3)*1.0 + np.array([2.0,0.0,-2.0])  # d_u logV shape
                dtp = rng.normal(0,st)                                     # placebo lag ~ 0
                Tp  = -dtp*s_u
                yp  = rng.normal(0,sL*np.sqrt(2),3)                        # pure estimator noise
                bs.append(ols(Tp,yp) if np.var(Tp)>0 else np.nan)
            bs=np.array(bs); single.append(np.median(np.abs(bs)))
            if abs(np.median(bs))>0.30: trips+=1
        print(f"{sL:8.2f} {st:12.3f} {trips/NS:24.3f} {np.median(single):21.2f}")
print("  -> kill 2 says: |median beta1_plac|>0.30 => REJECT the card even if primary is positive.")

print("\n== B. is beta1_plac heavy-tailed? (Cauchy signature: median of |b| grows as 1/sigma_tau) ==")
for st in (0.050,0.020,0.010,0.005,0.002):
    v=[]
    for _ in range(20000):
        s_u = rng.normal(0,1.0,3)+np.array([2.0,0.0,-2.0]); dtp=rng.normal(0,st)
        v.append(ols(-dtp*s_u, rng.normal(0,0.1*np.sqrt(2),3)))
    v=np.array(v)
    print(f"  sigma_tau={st:.3f}: median|b1p|={np.median(np.abs(v)):8.2f}  "
          f"P(|b1p|<=0.30)={np.mean(np.abs(v)<=0.30):.3f}  99pct={np.percentile(np.abs(v),99):.1f}")

print("\n== C. alternative reading: placebo REUSES the primary Dtau (nonzero) ==")
v=[]
for _ in range(20000):
    s_u = rng.normal(0,1.0,3)+np.array([2.0,0.0,-2.0]); dt=0.10
    v.append(ols(-dt*s_u, rng.normal(0,0.1*np.sqrt(2),3)))
v=np.array(v)
print(f"  Dtau reused=0.10 s: median|b1p|={np.median(np.abs(v)):.3f}  P(|median_8|>0.30)~"
      f"{np.mean([abs(np.median(rng.choice(v,8)))>0.30 for _ in range(4000)]):.3f}   (well conditioned)")
print("  -> the two readings of 'same estimator, no learning' give opposite verdicts. Card is ambiguous.")

print("\n== D. kappa null geometry: cosine between two symmetric 3x3 in whitened frame ==")
def sym(rr): A=rr.normal(size=(3,3)); return (A+A.T)/2
def cos(A,B): return np.sum(A*B)/np.sqrt(np.sum(A*A)*np.sum(B*B))
for cond in (1.0, 10.0, 50.0, 200.0):
    lam=np.geomspace(1.0,1.0/cond,3); Q=np.linalg.qr(rng.normal(size=(3,3)))[0]
    g=Q@np.diag(lam)@Q.T; gi=np.linalg.inv(g)
    ks=[]
    for _ in range(20000):
        E_fold = gi@sym(rng)          # null: post-pre difference is isotropic RAW noise
        E_del  = gi@sym(rng)          # template built from the SAME g^{-1}
        ks.append(cos(E_fold,E_del))
    ks=np.array(ks)
    med8=[np.median(rng.choice(ks,8)) for _ in range(5000)]
    print(f"  cond(g)={cond:6.0f}: P(kappa>0.50)={np.mean(ks>0.5):.3f}  "
          f"P(|kappa|>0.9)={np.mean(np.abs(ks)>0.9):.3f}  "
          f"P(median_8 kappa>0.30)={np.mean(np.array(med8)>0.30):.3f}")
print("  kill 2 also rejects if median kappa_plac > 0.30.")
