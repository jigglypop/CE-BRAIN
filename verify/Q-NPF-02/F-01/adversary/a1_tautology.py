# -*- coding: utf-8 -*-
"""A1 content/dof: b1=1 is forced by (readout mu(z),Sigma fixed) + (mean response anchored-dilates).
No metric assumption is used: G(z) is an ARBITRARY random smooth field. Seed 20260902."""
import sys, os, math, numpy as np
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import calib_synthetic as C

rng = np.random.default_rng(C.SEED)
U = C.U; D = 3

def make_readout(rng, scale=1.0):
    A = rng.normal(size=(3, 3)) * 0.7
    Cm = rng.normal(size=(3, 3)) * 0.9
    c = rng.normal(size=3) * 0.3
    M = np.eye(3) + 0.35 * rng.normal(size=(3, 3))   # well-conditioned linear part
    L = rng.normal(size=(3, 3)) * 0.3 + np.eye(3)
    Sig = L @ L.T + 0.5 * np.eye(3)          # z-independent, as the card declares
    Si = np.linalg.inv(Sig)
    def Jmu(z):
        s = np.tanh(A @ z + c)
        return scale * (M + 0.8 * (Cm * (1 - s**2)[None, :]) @ A)
    def G(z):
        J = Jmu(z); return J.T @ Si @ J
    return G

def field_on(G, zs):
    return np.stack([G(z) for z in zs])

def run(alpha, eps, G, gamma=0.0, extra=None):
    zp = C.zbar_true(U)
    zq = alpha * C.lagrange4(zp, np.clip(U/(1+eps), C.T_LO, C.T_HI))
    if extra is not None: zq = zq + extra
    gp = field_on(G, zp); gq = math.exp(2*gamma) * field_on(G, zq)
    r = C.estimate(gp, gp, gq, zp, zq)
    return r

print("== A1a. fixed readout + anchored dilation of the mean response; metric field G is ARBITRARY ==")
print("   (g_pre(u)=G(zbar_pre(u)), g_post(u)=G(alpha*zbar_pre(u/(1+eps))).  NO metric law imposed.)")
print("  field  alpha   eps    k_x     lam_min  nadm   b1       a        b       Psi      kap      Lam_x")
allb = []
for f in range(5):
    G = make_readout(rng)
    for alpha in [1.0, 1.3, 2.0, 0.6]:
        for eps in [0.05, 0.10, 0.20]:
            r = run(alpha, eps, G)
            if r.get('stop') is not False:
                print(f"   f{f}  {alpha:5.2f} {eps:5.2f}   STOP({r.get('stop')})  nadm={r.get('nadm')}"); continue
            lm = np.linalg.eigvalsh(C.sym(field_on(G, C.zbar_true(U)))).min()
            print(f"   f{f}  {alpha:5.2f} {eps:5.2f}  {r['k_x']:+.4f}  {lm:7.3f}  {r['nadm']:3d} "
                  f"{r['b1']:+8.4f} {r['a']:+8.4f} {r['b']:+7.4f} {r['Psi']:+8.4f} {r['kap']:+8.4f} {r['Lam_x']:+7.2f}")
            allb.append(r['b1'])
allb = np.array(allb)
print(f"   -> b1 over {len(allb)} arbitrary (field,alpha,eps): median {np.median(allb):.4f}  "
      f"min {allb.min():.4f}  max {allb.max():.4f}  frac in 1.00+-0.06: {np.mean(np.abs(allb-1)<=0.06):.3f}"
      f"  frac in 1.00+-0.15: {np.mean(np.abs(allb-1)<=0.15):.3f}")

print("")
print("== A1b. same, with gain gamma=0.15 (E0 must be gamma-blind) ==")
G = make_readout(np.random.default_rng(C.SEED+1))
for gam in [0.0, 0.15, 0.5]:
    r = run(1.3, 0.10, G, gamma=gam)
    print(f"   gamma={gam:.2f}: b1={r['b1']:+.4f} kap={r['kap']:+.4f} trE_mean={np.mean(r['trY']):+.4f} d*gamma={3*gam:+.3f}")

print("")
print("== A1c. how much non-dilation contamination of zbar_post does the R2>=0.50 gate still admit? ==")
print("   zbar_post = alpha*zbar_pre(u/(1+eps)) + c*v(u);  v = smooth random direction field")
G = make_readout(np.random.default_rng(C.SEED+2))
zp = C.zbar_true(U)
V1 = rng.normal(size=(3,)); V1 /= np.linalg.norm(V1)
vfun = (np.sin(3*U)[:, None]*V1 + np.cos(2*U)[:, None]*np.roll(V1, 1))
print("   c      R2_dil   k_x      b1       Psi      Lam_x   verdict-relevant")
for c in [0.0, 0.1, 0.2, 0.4, 0.7, 1.0, 1.5]:
    r = run(1.0, 0.10, G, extra=c*vfun)
    if r.get('stop') is not False:
        print(f"  {c:5.2f}   STOP({r.get('stop')})"); continue
    gate = "GATE-PASS" if (C.KX_LO <= abs(r['k_x']) <= C.KX_HI and r['R2'] >= C.R2_FLOOR) else "gate-blocked"
    print(f"  {c:5.2f}  {r['R2']:6.3f}  {r['k_x']:+.4f} {r['b1']:+8.4f} {r['Psi']:+8.4f} {r['Lam_x']:+7.2f}   {gate}")

print("")
print("== A1d. can the card's own null (world R, b1=0) be realised with an UNCHANGED readout? ==")
print("   R needs G_post(zbar_post(u)) = e^{2g} G_pre(zbar_pre(u)) while zbar_post(u) != zbar_pre(u).")
G = make_readout(np.random.default_rng(C.SEED+3))
zp = C.zbar_true(U); eps = 0.10
zq = C.lagrange4(zp, np.clip(U/(1+eps), C.T_LO, C.T_HI))
gp = field_on(G, zp); gq_fixed_readout = field_on(G, zq); gq_R = gp.copy()
d1 = np.linalg.norm(gq_fixed_readout - gp)/np.linalg.norm(gp)
print(f"   ||G(z_post)-G(z_pre)||/||G(z_pre)|| = {d1:.4f}  (fixed readout: metric MUST move)")
print(f"   world R sets g_post = g_pre exactly -> requires a readout change of relative size {d1:.4f}")
print("   i.e. b1=0 is not 'metric does not fold'; it is 'the readout map changed so as to cancel the warp'.")
