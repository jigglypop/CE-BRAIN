# -*- coding: utf-8 -*-
"""A5: Var(u_adm)=0.04 knife-edge, u_pk anchor drift, lambda_min=0.02 edge. Seed 20260902."""
import sys, os, math, numpy as np
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import calib_synthetic as C
U = C.U
print("== A5a. MIN_BINS=7 and Var(u_adm)>=0.04 s^2 are the SAME constraint for contiguous bins ==")
for n in [6, 7, 8, 9]:
    v = np.var(U[1:1+n])
    print(f"   {n} contiguous 0.1 s bins: Var = {v:.10f}  {'PASS' if v >= 0.04 else 'STOP'} (floor 0.04)")
print("   -> 7 contiguous bins gives Var = 0.0400000000 exactly: the floor sits ON the boundary and the")
print("      comparison '< 0.04' is decided by floating point, not by design.")

print("")
print("== A5b. u_pk anchor drift ==")
gpre = C.g_true(U); zpre = C.zbar_true(U)
gq = math.exp(0.3)*C.g_true(U/1.10); zq = 1.0*C.zbar_true(U/1.10)
base = C.estimate(gpre, gpre, gq, zpre, zq)
print(f"   frozen u_pk = argmax||z_pre|| = {base['u_pk']:.3f} s;  b1={base['b1']:+.4f} a={base['a']:+.3f} kap={base['kap']:+.4f}")
print("   b1 = <Y0,B>/<B,B>* and B_k = -k_x u_k S0_k/2 contains NO u_pk  -> b1 is exactly u_pk-invariant.")
print("   a, lag, Psi and the kappa template n_pk = normalise(P(u_pk) z_pre(u_pk)) DO depend on u_pk.")
zsk = zpre*np.exp(-0.5*((U-0.35)/0.55)**2)[:, None]     # a mouse whose peak sits elsewhere
r2 = C.estimate(gpre, gpre, gq, zsk, zq)
print(f"   a mouse with a shifted response peak: u_pk={r2['u_pk']:.3f} -> b1={r2['b1']:+.4f} (same) "
      f"a={r2['a']:+.3f} kap={r2['kap']:+.4f}  (a and kappa move; pooling averages u_pk across mice)")

print("")
print("== A5c. lambda_min = 0.02 edge ==")
for s in [1.0, 0.6, 0.5, 0.45, 0.4]:
    gp2 = gpre*s; gq2 = gq*s
    lm = np.linalg.eigvalsh(C.sym(C.smooth(gp2)[0])).min()
    r = C.estimate(gp2, gp2, gq2, zpre, zq)
    st = r.get('stop')
    print(f"   scale={s:4.2f}: lambda_min={lm:.4f}  nadm={r.get('nadm')}  "
          + (f"b1={r['b1']:+.4f}" if st is False else f"STOP({st})"))
print("   -> the verdict's existence flips on an absolute number attached to a chart-scale-dependent")
print("      quantity; b1 itself never changes.")
