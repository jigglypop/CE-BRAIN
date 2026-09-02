# -*- coding: utf-8 -*-
"""(1) Dtau estimator resolution vs the 0.02 s input gate on 0.1 s bins (parabolic interp),
   and the 1/Dtau amplification into beta_1.
   (2) input_gate (>=6/8 mice) vs kill 1 sign test (>=7/8 positive): mutually consistent?"""
import numpy as np
from math import comb
rng = np.random.default_rng(20260902)
BIN = 0.1; NB = 15                      # frozen: 0.1 s bins, 15 bins

def lag_hat(dtau_true, snr, width=0.30, ntr=60):
    t = (np.arange(NB)+0.5)*BIN
    f = lambda s: np.exp(-0.5*((t-0.5-s)/width)**2)
    a = f(0.0) + rng.normal(0, 1.0/(snr*np.sqrt(ntr)), NB)
    b = f(dtau_true) + rng.normal(0, 1.0/(snr*np.sqrt(ntr)), NB)
    a = (a-a.mean())/ (a.std()+1e-12); b = (b-b.mean())/(b.std()+1e-12)
    lags = np.arange(-5, 6)             # +-0.5 s
    cc = np.array([np.corrcoef(a[max(0,-L):NB-max(0,L)], b[max(0,L):NB-max(0,-L)])[0,1]
                   if NB-abs(L) > 2 else -1 for L in lags])
    k = int(np.argmax(cc))
    if 0 < k < len(cc)-1:
        y0,y1,y2 = cc[k-1],cc[k],cc[k+1]; den = (y0-2*y1+y2)
        d = 0.5*(y0-y2)/den if abs(den) > 1e-12 else 0.0
        d = np.clip(d,-1,1)
    else: d = 0.0
    return (lags[k]+d)*BIN

print("== A. Dtau estimator on the frozen 0.1 s grid (parabolic interp), 2000 sims/cell ==")
print(f"{'true Dtau':>10s} {'SNR':>5s} {'mean Dtau_hat':>14s} {'sd':>7s} {'rel.err of beta1':>18s} {'P(gate pass)':>13s}")
for dt in (0.02, 0.05, 0.10, 0.20):
    for snr in (2.0, 5.0, 20.0):
        est = np.array([lag_hat(dt, snr) for _ in range(2000)])
        rel = np.median(np.abs(est-dt)/dt)
        print(f"{dt:10.2f} {snr:5.1f} {est.mean():14.4f} {est.std():7.4f} "
              f"{rel:18.2f} {np.mean(np.abs(est)>=0.02):13.3f}")
print("  beta_1 = Cov(trE,s)/(-Dtau_hat Var(s))  =>  rel.err(beta1) = rel.err(Dtau_hat).")
print("  tolerance on beta1 is +-0.30 (30%): any Dtau_hat with >30% relative error exhausts it alone.")

print("\n== B. systematic bias of parabolic interpolation on a 0.1 s grid (noise-free) ==")
for dt in (0.02,0.04,0.05,0.08,0.10,0.15,0.20,0.25):
    e = lag_hat(dt, 1e9)
    print(f"  true {dt:.2f} s -> Dtau_hat {e:.4f} s   bias {e-dt:+.4f} s ({100*(e-dt)/dt:+6.1f}%)"
          f"  => beta1 biased to {dt/e:.3f}" if e!=0 else "")

print("\n== C. input_gate (>=6/8 mice with |Dtau|>=0.02 and CI excluding 0) vs kill 1 (>=7/8 with beta1>0)")
def p_at_least(k, n, p): return sum(comb(n,i)*p**i*(1-p)**(n-i) for i in range(k, n+1))
for k_gated in (6,7,8):
    for p_pos in (1.00, 0.95, 0.90):
        # gated mice: sign correct w.p. p_pos ; non-gated mice: Dtau_hat ~ noise => sign is a coin flip
        n_ng = 8-k_gated
        tot = 0.0
        for i in range(k_gated+1):
            for j in range(n_ng+1):
                if i+j >= 7:
                    tot += comb(k_gated,i)*p_pos**i*(1-p_pos)**(k_gated-i) * comb(n_ng,j)*0.5**n_ng
        print(f"  gate passes with {k_gated}/8 solid, per-mouse sign correct {p_pos:.2f}: "
              f"P(kill 1 sign test PASSES | card TRUE) = {tot:.3f}   -> false-kill {1-tot:.3f}")
print("  gate only requires 6/8; kill 1 requires 7/8 positive => up to 2 sign-random mice decide it.")
