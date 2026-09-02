# -*- coding: utf-8 -*-
"""A4: recovers limits actually executed; (a,b) identifiability; dimension table. Seed 20260902."""
import sys, os, math, numpy as np
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import calib_synthetic as C
rng = np.random.default_rng(C.SEED)
U = C.U; gpre = C.g_true(U); zpre = C.zbar_true(U)

print("== A4a. recovers limit 1 (gain: k_x=0, gamma!=0). Card check index 5 only verifies that gamma")
print("   cancels in the trace-free part of a DIAGONAL 3x3 log; it never evaluates E0 or tr E. ==")
for gam in [0.0, 0.15, 0.40]:
    gq = math.exp(2*gam)*gpre
    r = C.estimate(gpre, gpre, gq, zpre, zpre.copy())
    tr = np.mean(r['trY']) if r.get('stop') is False else None
    Y = 0.5*(C.logm(np.einsum('kij,kjl,klm->kim', C.isqrtm(C.smooth(gpre)[0]), gq, C.isqrtm(C.smooth(gpre)[0])))
             - C.logm(np.einsum('kij,kjl,klm->kim', C.isqrtm(C.smooth(gpre)[0]), gpre, C.isqrtm(C.smooth(gpre)[0]))))
    print(f"   gamma={gam:.2f}: pipeline -> {r.get('stop')}   ||E0||_max={np.abs(C.tf(Y)).max():.2e}   "
          f"mean tr E={np.trace(Y,axis1=-2,axis2=-1).mean():+.4f}  d*gamma={3*gam:+.3f}")
print("   -> tr E = d*gamma holds, but the pipeline STOPs ('kx0'): b1 = <E0,B>/<B,B> = 0/0 because")
print("      the templates A,B are both proportional to k_x. The gain limit is unreachable BY the estimator.")

print("")
print("== A4b. recovers limit 2 (fixed delay -> the (a,0) point). Noise-free 2-template regression ==")
for dt in [0.05, 0.10, 0.20]:
    gq = C.g_true(U-dt); zq = C.zbar_true(U-dt)
    r = C.estimate(gpre, gpre, gq, zpre, zq)
    print(f"   Delta={dt:.2f}: k_x_hat={r['k_x']:+.4f} a={r['a']:+.3f} b={r['b']:+.3f} Psi={r['Psi']:+.3f}"
          f"  b1(KILL-1 statistic)={r['b1']:+.4f}   -> K1 sees {r['b1']:.2f}, prediction is 1.00")
print("   -> the (a,b) split does recover (a,0)-ish noise-free, but K1's b1 statistic is ~1 in BOTH")
print("      worlds, and (a,b)/Psi is NOT among the card's predicts or kills.")

print("")
print("== A4c. is the card's actual claim (a,b)=(0,1) measurable?  Psi = b*ubar/(a*u_pk+b*ubar) ==")
for N in [300, 1000]:
    rows = C.run('D', 0.10, N, 80, rng)
    gated = [r for r in rows if r.get('stop') is False and C.KX_LO <= abs(r['k_x']) <= C.KX_HI and r['R2'] >= C.R2_FLOOR]
    PS = []
    for _ in range(300):
        grp = [gated[i] for i in rng.integers(0, len(gated), 8)]
        PS.append(C.pool_rows(grp)['Psi'])
    PS = np.array(PS, float)
    lo, hi = np.nanpercentile(PS, [2.5, 97.5])
    print(f"   N={N:5d} TRUE world (Psi_true=1, rigid-shift world Psi=0): pooled Psi 95% = [{lo:+.2f},{hi:+.2f}]"
          f"  width {hi-lo:.2f}  P(Psi>0.5)={np.nanmean(PS>0.5):.3f}")
print("   -> the interval that would separate (0,1) from (a,0) is 2-3 orders of magnitude too wide;")
print("      that is presumably why Psi was dropped from predicts/kill after being computed.")

print("")
print("== A4d. dimension table ==")
tab = {'u':'T','u_pk':'T','delta':'T','k_x':'1','S0':'T^-1','delta*S0':'1','E0':'1','trE':'1',
       'Jbar':'O','Sigma_o':'O^2','g':'1','b1':'1','kappa':'1','Lambda_x':'1'}
print("   g = Jbar^T Sigma_o^-1 Jbar : [O]*[O^-2]*[O] = 1                    OK")
print("   S = g^-1/2 d_u g g^-1/2   : [1]*[T^-1]*[1] = T^-1                  OK")
print("   delta*S0                  : [T]*[T^-1] = 1                         OK")
print("   b1 = <E0,B>/<B,B>         : B ~ k_x*u*S0 ~ [1][T][T^-1] = 1        OK  (b1 dimensionless)")
print("   Lambda_x = log(r_s/r_d)   : ratio of residuals in the same z units OK")
print("   BUT the frozen code's admissibility gate ||S0||>=0.5 has units s^-1 and is NOT in the card;")
print("   and lambda_min(g)>=0.02 is a bare number on a chart-scale-dependent quantity (see A3d).")
print("")
print("== A4e. the card's own tolerance vs its own noise-free bias ==")
for e in [0.05, 0.10, 0.20]:
    gq = math.exp(0.3)*C.g_true(U/(1+e)); zq = 1.3*C.zbar_true(U/(1+e))
    r = C.estimate(gpre, gpre, gq, zpre, zq)
    d = r['b1']-1.0
    print(f"   eps={e:.2f}: noise-free b1={r['b1']:.4f}  bias={d:+.4f}  {'INSIDE' if abs(d)<=0.06 else 'OUTSIDE'} the declared 1.00+-0.06")
