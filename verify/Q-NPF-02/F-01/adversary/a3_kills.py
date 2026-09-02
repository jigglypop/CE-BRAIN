# -*- coding: utf-8 -*-
"""A3: K2 (kappa <-> Finsler?), K4 (placebo), power at the real N, gates/thresholds. Seed 20260902."""
import sys, os, math, numpy as np
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import calib_synthetic as C
import check_prereg as P

rng = np.random.default_rng(C.SEED)
U = C.U

# ---------------- K2 ----------------
print("== A3a. K2: is kappa != 0 equivalent to non-Riemannian (Randers b(z)^T y)? ==")
print("   world: g_post(u) = R(u)^T g_pre(u-delta(u)) R(u),  R = exp(theta(u) K)  -- STRICTLY Riemannian,")
print("   SPD and direction-EVEN at every u; only the eigenbasis rotates with u.")
gpre = C.g_true(U); zpre = C.zbar_true(U); eps = 0.10; gam = 0.15
K = np.array([[0., 1., 0.], [-1., 0., 0.4], [0., -0.4, 0.]])
zpost = 1.0*C.lagrange4(zpre, np.clip(U/(1+eps), C.T_LO, C.T_HI))
gw = math.exp(2*gam)*C.g_true(U/(1+eps))
print("   theta_amp   b1        kappa      K2 verdict (|kap|>0.15 kills)")
for th in [0.0, 0.02, 0.05, 0.10, 0.20, 0.35]:
    R = np.stack([C.expm(th*np.sin(2.2*u)*K[None])[0] for u in U])
    gp2 = np.einsum('kji,kjl,klm->kim', R, gw, R)
    r = C.estimate(gpre, gpre, gp2, zpre, zpost)
    if r.get('stop') is not False: print(f"   {th:8.2f}   STOP({r['stop']})"); continue
    print(f"   {th:8.2f}  {r['b1']:+8.4f}  {r['kap']:+9.4f}   {'K2_REFUTE' if abs(r['kap'])>0.15 else 'passes'}")

print("")
print("   Randers side: the frozen estimator forms ghat = Jbar^T Sigma^-1 Jbar, symmetric by CONSTRUCTION.")
Jb = rng.normal(size=(3, 3)); Sg = np.eye(3)
gh = Jb.T @ np.linalg.inv(Sg) @ Jb
print(f"   ||ghat - ghat^T|| = {np.linalg.norm(gh-gh.T):.3e}  ->  F(z,-y) = F(z,+y) identically for every")
print("   output of the pipeline. A Randers 1-form b(z)^T y cannot appear in ANY ghat the card computes.")

# ---------------- power at the real N ----------------
print("")
print("== A3b. power at the data's actual N (D7 contract: A1 early = first 60 trials, late = last 60; ==")
print("   pre split into two time-ordered halves -> n_pre-half = 30, n_post = 60; per-cue: 20 / 10 / 20) ==")
NMICE = 60
print("   N(trials/phase)  gate   verdict distribution (TRUE world D, eps=0.10), 200 cohorts")
for N in [20, 40, 60, 120, 300, 1000]:
    rows = C.run('D', 0.10, N, NMICE, rng)
    ok = [r for r in rows if r.get('stop') is False]
    gated = [r for r in ok if C.KX_LO <= abs(r['k_x']) <= C.KX_HI and r['R2'] >= C.R2_FLOOR]
    gf = len(gated)/len(rows)
    if len(gated) < 8:
        print(f"   {N:6d}          {gf:.2f}   GATE BLOCKS (n_gated={len(gated)})"); continue
    V = {}
    for _ in range(200):
        s = P.cohort_stats(gated); v = P.verdict(s); V[v] = V.get(v, 0) + 1
    tot = sum(V.values())
    print(f"   {N:6d}          {gf:.2f}   " + "  ".join(f"{k}={v/tot:.3f}" for k, v in sorted(V.items(), key=lambda kv: -kv[1])))

# ---------------- K4 placebo, trial reuse ----------------
print("")
print("== A3c. K4 placebo: the synthetic uses THREE independent trial sets (g1,g2,g_post) for the ==")
print("   placebo; the frozen design has only TWO pre halves, so the placebo must reuse them. ==")
def placebo_rows(N, nm, shared):
    out = []
    for _ in range(nm):
        gp, gq, zp, zq = C.world('P', 0.0)
        g1 = C.noisy_g(gp, N/2, rng); g2 = C.noisy_g(gp, N/2, rng)
        gpl = g2 if shared else C.noisy_g(gp, N, rng)     # shared: placebo 'post' = the other pre half
        z1 = zp + rng.normal(size=zp.shape)/math.sqrt(N); z2 = zq + rng.normal(size=zq.shape)/math.sqrt(N)
        r = C.estimate(g1, g2, gpl, z1, z2, k_prim=0.10/1.10)
        if r.get('stop') is False: out.append(r)
    return out
for shared in [False, True]:
    for N in [300, 1000]:
        rr = placebo_rows(N, 80, shared)
        pb = np.array([r.get('plac_b1', np.nan) for r in rr], float)
        exc = []
        for _ in range(300):
            grp = [rr[i] for i in rng.integers(0, len(rr), 8)]
            bb = []
            for _ in range(200):
                rs = [grp[i] for i in rng.integers(0, 8, 8)]
                G = sum(x['G'] for x in rs); Gn = sum(x['Gn'] for x in rs); y = sum(x['yv'] for x in rs)
                sc = np.mean([(0.10/1.10)/x['k_x'] for x in rs])
                e = C.endpoints(G*sc*sc, Gn*sc*sc, y*sc, np.mean([x['u_pk'] for x in rs]), np.mean([x['ub'] for x in rs]))
                bb.append(e['b1'])
            lo, hi = np.nanpercentile(bb, [2.5, 97.5])
            exc.append((lo > 0) or (hi < 0))
        tag = "SHARED halves (real design)" if shared else "3 independent sets (card's synthetic)"
        print(f"   {tag:38s} N={N:5d}: median plac_b1={np.nanmedian(pb):+.3f} "
              f"sd={np.nanstd(pb):.2f}  CI-excludes-0 rate={np.mean(exc):.3f}")

# ---------------- undeclared thresholds / chart scale ----------------
print("")
print("== A3d. thresholds: S_FLOOR=0.5 (||S0||, units s^-1) is in the FROZEN CODE but NOT in the card. ==")
print("   Also lambda_min>=0.02 is a bare number on g, whose scale depends on the chart normalisation.")
gpre = C.g_true(U); zpre = C.zbar_true(U)
gpost = math.exp(2*0.15)*C.g_true(U/(1+0.10)); zpost = 1.3*C.lagrange4(zpre, np.clip(U/1.10, C.T_LO, C.T_HI))
import importlib
print("   S_FLOOR    nadm   b1        kappa")
for sf in [0.0, 0.25, 0.5, 0.8, 1.2, 2.0]:
    C.S_FLOOR = sf
    r = C.estimate(gpre, gpre, gpost, zpre, zpost)
    if r.get('stop') is not False: print(f"   {sf:6.2f}   STOP({r['stop']}) nadm={r.get('nadm')}"); continue
    print(f"   {sf:6.2f}   {r['nadm']:3d}   {r['b1']:+8.4f}  {r['kap']:+8.4f}")
C.S_FLOOR = 0.5
print("")
print("   chart rescaling z -> c z  (allowed: chart is only frozen to be u-independent).  g -> g/c^2.")
print("   c      lambda_min(g)  nadm   b1        (b1 must be chart-invariant per ladder step 1)")
for c in [1.0, 1.5, 2.0, 3.0, 0.7]:
    gp2 = gpre/c**2; gq2 = gpost/c**2
    lm = np.linalg.eigvalsh(C.sym(C.smooth(gp2)[0])).min()
    r = C.estimate(gp2, gp2, gq2, zpre/c, zpost/c)
    if r.get('stop') is not False: print(f"   {c:4.2f}   {lm:11.4f}   STOP({r['stop']}) nadm={r.get('nadm')}"); continue
    print(f"   {c:4.2f}   {lm:11.4f}   {r['nadm']:3d}   {r['b1']:+8.4f}")

print("")
print("== A3e. delta -> 0 and gate boundaries ==")
print("   k_x        b1        note")
for e in [1e-6, 1e-3, 0.01, 0.05, 0.06, 0.30, 0.35]:
    gq = math.exp(0.3)*C.g_true(U/(1+e)); zq = 1.0*C.lagrange4(zpre, np.clip(U/(1+e), C.T_LO, C.T_HI))
    r = C.estimate(gpre, gpre, gq, zpre, zq)
    if r.get('stop') is not False: print(f"   eps={e:<9.6g} STOP({r['stop']})"); continue
    g = "GATE-PASS" if C.KX_LO <= abs(r['k_x']) <= C.KX_HI else "gate-blocked"
    print(f"   eps={e:<9.6g} k_x={r['k_x']:+.6f}  b1={r['b1']:+9.4f}   {g}")
