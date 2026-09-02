# -*- coding: utf-8 -*-
"""Four limit tests demanded by the audit brief, closed explicitly. Seed 20260902."""
import numpy as np
rng=np.random.default_rng(20260902)
UG=np.array([0.45,0.75,1.05]); H=0.3
def ols(T,y):
    A=np.vstack([T,np.ones(len(T))]).T
    return np.linalg.lstsq(A,y,rcond=None)[0][0]

print("== LIMIT 1. Dtau -> 0 : is beta_1 a 0/0 ? ==")
def L(u,u0=0.75,s=0.30,A=1.0): return A*np.exp(-0.5*((u-u0)/s)**2)
print(f"{'Dtau':>10s} {'Var(T)':>12s} {'Cov(y,T)':>12s} {'beta1':>10s}   (exact pure-lag, noise-free)")
for Dt in (1e-1,1e-2,1e-3,1e-6,1e-9,0.0):
    y=np.array([L(u-Dt)-L(u) for u in UG])
    T=np.array([-Dt*(L(u+H)-L(u-H))/(2*H) for u in UG])
    print(f"{Dt:10.1e} {np.var(T):12.3e} {np.cov(y,T,bias=True)[0,1]:12.3e} {ols(T,y):10.4f}")
print("  noise-free: both -> 0 at the SAME rate, beta_1 has a finite limit (1.403 here, NOT 1.00).")
print("  with noise on the LHS the numerator does NOT vanish with Dtau -> genuine 0/0:")
for Dt in (0.10,0.02,0.005,0.001):
    b=[]
    for _ in range(20000):
        y=np.array([L(u-Dt)-L(u)+rng.normal(0,0.05) for u in UG])
        T=np.array([-Dt*(L(u+H)-L(u-H))/(2*H) for u in UG])
        b.append(ols(T,y))
    b=np.array(b)
    print(f"  Dtau={Dt:6.3f} sigma_L=0.05: median beta1={np.median(b):8.3f} IQR=[{np.percentile(b,25):7.2f},"
          f"{np.percentile(b,75):7.2f}] P(in[0.70,1.30])={np.mean((b>=.7)&(b<=1.3)):.3f}")

print("\n== LIMIT 2. d_u log V_g == 0 over the window : is the regression defined? ==")
for lab,Lf in [("flat log V (d_u logV = 0)", lambda u: 3.0),
               ("linear log V (exact CD)",   lambda u: 0.8*u+3.0),
               ("quadratic log V (exact CD)",lambda u: 0.8*u*u+3.0)]:
    Dt=0.10
    y=np.array([Lf(u-Dt)-Lf(u) for u in UG])
    T=np.array([-Dt*(Lf(u+H)-Lf(u-H))/(2*H) for u in UG])
    try:
        b=ols(T,y); msg=f"beta1={b:.4f}"
    except Exception as e: msg=f"{type(e).__name__}"
    print(f"  {lab:28s} Var(T)={np.var(T):.3e}  {msg}"
          + ("   <- 0/0, ANY beta1 fits; lstsq silently returns a value" if np.var(T)<1e-30 else ""))
print("  the card pre-registers no lower bound on Var(T); a mouse whose log V_g is flat or")
print("  extremal in [0.45,1.05] contributes an arbitrary beta_1 to the 8-mouse median and sign test.")

print("\n== LIMIT 3. rank-deficient g : log det divergence ==")
for e in (1e-1,1e-3,1e-6,1e-12,0.0):
    g=np.diag([1.0,0.5,e])
    ld=np.log(np.linalg.det(g)) if e>0 else -np.inf
    print(f"  lambda_min={e:8.1e}: log det g = {ld:12.4f}, log V_g = {ld/2:12.4f}"
          + ("   <- -inf, trE and d_u logV both undefined" if e==0 else ""))
g1=np.diag([1.0,0.5,1e-6]); g2=np.diag([1.0,0.5,2e-6])
print(f"  a 2x change in a 1e-6 eigenvalue moves tr E_fold by {0.5*np.log(np.linalg.det(g2)/np.linalg.det(g1)):.4f}"
      f" (= 0.5*log 2), i.e. the trace is dominated by the least identified direction.")

print("\n== LIMIT 4. sign convention: does flipping it flip beta_1 ? ==")
Dt=0.10
yA=np.array([L(u-Dt)-L(u) for u in UG])          # card: Dtau>0 = post later => g_post(u)=g_pre(u-Dtau)
yB=np.array([L(u+Dt)-L(u) for u in UG])          # slipped: g_post(u)=g_pre(u+Dtau)
T =np.array([-Dt*(L(u+H)-L(u-H))/(2*H) for u in UG])
print(f"  card convention   g_post(u)=g_pre(u-Dtau): beta1={ols(T,yA):+.4f}  (sign +, kill 1 sign test PASSES)")
print(f"  slipped in the xcorr direction (u+Dtau)  : beta1={ols(T,yB):+.4f}  (sign -, kill 1 sign test FAILS 0/8)")
print("  the card fixes the convention in words ('Dtau>0 = post is later') but not as an estimator")
print("  formula (which sequence is shifted in the normalized cross-correlation). A one-line slip")
print("  turns a perfect confirmation into a maximal one-sided refutation. Self-consistent as written.")
