# -*- coding: utf-8 -*-
"""EXACT pure-lag world (card's own model, no noise): what beta_1 does the card's FROZEN
   estimator return?  L(u)=log V_g(u); trE(u)=L(u-Dt)-L(u) exactly, any d.
   Frozen: u in {0.45,0.75,1.05}, central difference h=0.3 s, free intercept.
   kill 1 window [0.70,1.30]; predicts 1.00+-0.30; kill 4 (synthetic) 1.00+-0.05."""
import numpy as np
UG = np.array([0.45,0.75,1.05]); H = 0.3
def beta1(L, Dt, h=H, exact_deriv=False, eps=1e-6):
    y = np.array([L(u-Dt)-L(u) for u in UG])
    if exact_deriv:
        T = np.array([-Dt*(L(u+eps)-L(u-eps))/(2*eps) for u in UG])
    else:
        T = np.array([-Dt*(L(u+h)-L(u-h))/(2*h) for u in UG])
    return np.linalg.lstsq(np.vstack([T,np.ones(len(UG))]).T, y, rcond=None)[0][0]
def bump(A,u0,s): return lambda u: A*np.exp(-0.5*((u-u0)/s)**2)

print("== A. central-difference (h=0.30 s) bias alone, Dtau -> 0 (no truncation) ==")
print(f"{'metric timescale s':>18s} {'beta1(h=0.3)':>13s} {'beta1(exact d/du)':>18s}  verdict")
for s in (0.15,0.20,0.25,0.30,0.40,0.50,0.80):
    L = bump(1.0,0.75,s)
    b_h = beta1(L,1e-4); b_e = beta1(L,1e-4,exact_deriv=True)
    v = "KILL1 FALSE-REJECT" if not (0.70<=b_h<=1.30) else ("outside +-0.05" if abs(b_h-1)>0.05 else "ok")
    print(f"{s:18.2f} {b_h:13.3f} {b_e:18.3f}  {v}")

print("\n== B. O(Dtau^2) truncation + h=0.3, exact pure-lag, bump s=0.30 at u0=0.75 ==")
print(f"{'Dtau (s)':>9s} {'beta1':>8s} {'beta1 exact-deriv':>18s}  verdict(kill1 / kill4)")
for Dt in (0.02,0.05,0.08,0.10,0.15,0.20,0.30):
    L = bump(1.0,0.75,0.30)
    b = beta1(L,Dt); be = beta1(L,Dt,exact_deriv=True)
    v1 = "FALSE-REJECT" if not (0.70<=b<=1.30) else "pass"
    v4 = "FALSE-REJECT" if abs(be-1)>0.05 else "pass"
    print(f"{Dt:9.2f} {b:8.3f} {be:18.3f}  {v1} / {v4}")

print("\n== C. how much of a plausible (u0,s,Dtau) space does the card FALSE-KILL? ==")
rng = np.random.default_rng(20260902); n=20000; bad=0; bad4=0; vals=[]
for _ in range(n):
    u0 = rng.uniform(0.2,1.3); s = rng.uniform(0.15,0.6); A = rng.uniform(0.3,2.0)
    Dt = rng.uniform(0.02,0.25)
    L = bump(A,u0,s); b = beta1(L,Dt); vals.append(b)
    if not (0.70<=b<=1.30): bad+=1
    if abs(beta1(L,Dt,exact_deriv=True)-1)>0.05: bad4+=1
vals=np.array(vals)
print(f"  n={n} exact pure-lag draws (u0~U[0.2,1.3], s~U[0.15,0.6], Dtau~U[0.02,0.25])")
print(f"  median beta1 = {np.median(vals):.3f}   IQR = [{np.percentile(vals,25):.3f},{np.percentile(vals,75):.3f}]")
print(f"  P(beta1 outside kill-1 window [0.70,1.30]) = {bad/n:.3f}")
print(f"  P(|beta1-1|>0.05 with EXACT derivative, i.e. kill 4 trips) = {bad4/n:.3f}")

print("\n== D. two-sided: is there an UPPER gate on Dtau? (card gates only |Dtau|>=0.02 s) ==")
L = bump(1.0,0.75,0.30)
for Dt in (0.35,0.45,0.50):
    try:
        print(f"  Dtau={Dt:.2f}: beta1={beta1(L,Dt):.3f}   (u-Dtau reaches {UG.min()-Dt:+.2f} s, pre-cue)")
    except Exception as e:
        print(f"  Dtau={Dt:.2f}: {type(e).__name__} {e}")
print("  card lag search range delta in [-0.5,0.5] s -> Dtau up to 0.5 s admissible; no upper gate.")
