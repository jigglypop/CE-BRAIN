# -*- coding: utf-8 -*-
"""A2 recovers-3 / K3: does a TRUE conduction-velocity change (the card's own CE mechanism,
(21.47) line 3 + (21.48)) produce an anchored dilation of the mean response?  Seed 20260902."""
import sys, os, math, numpy as np
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import calib_synthetic as C

rng = np.random.default_rng(C.SEED)
NU = 8; DT = 0.0005; TMAX = 2.2; TAU_M = 0.020

def simulate(vfac, W, ell, v0, tau_m=TAU_M, drive_shift=0.0):
    """tau_m xdot = -x + W tanh(x(t - tau_ij)) + I(t);  tau_ij = ell_ij/(v0*vfac).
    Cue-locked drive I is NOT rescaled (it is the experimenter's cue)."""
    tau = ell/(v0*vfac)
    nt = int(TMAX/DT); lag = np.maximum(np.round(tau/DT).astype(int), 1)
    X = np.zeros((nt, NU))
    b = np.zeros(NU); b[0] = 1.0
    ts = np.arange(nt)*DT
    I = np.outer(np.exp(-0.5*((ts - 0.08 - drive_shift)/0.05)**2), b)*1.6
    for k in range(1, nt):
        s = np.zeros(NU)
        for i in range(NU):
            for j in range(NU):
                kk = k-1-lag[i, j]
                if kk >= 0: s[i] += W[i, j]*math.tanh(X[kk, j])
        X[k] = X[k-1] + DT/tau_m*(-X[k-1] + s + I[k-1])
    return ts, X

def bin15(ts, X, u0=0.0):
    out = np.zeros((15, NU))
    for k in range(15):
        m = (ts-u0 >= 0.05+0.1*k-0.05) & (ts-u0 < 0.05+0.1*k+0.05)
        out[k] = X[m].mean(0)
    return out

W = rng.normal(size=(NU, NU))*0.55; np.fill_diagonal(W, 0.0)
ell = rng.uniform(0.5, 3.0, size=(NU, NU)); v0 = 100.0     # tau in [5,30] ms
print("== A2a. true conduction-velocity change: is the mean response an anchored dilation? ==")
print("   circuit: tau_m=20 ms fixed, cue drive fixed, only tau_ij scaled by 1/(1+eps_v)")
print("   eps_v   R2_dil  k_x_hat   Lam_x     verdict(K3: Lam<=-0.10 kills)  best_shift(s)")
ts, X0 = simulate(1.0, W, ell, v0)
Q0 = bin15(ts, X0)
Uc, Sc, Vt = np.linalg.svd(Q0 - Q0.mean(0), full_matrices=False)
proj = Vt[:3].T
zpre = (Q0 - Q0.mean(0)) @ proj
zpre = zpre/np.std(zpre)
rows = []
for epsv in [0.05, 0.10, 0.20, 0.35, 0.50]:
    _, X1 = simulate(1.0+epsv, W, ell, v0)
    Q1 = bin15(ts, X1)
    zpost = ((Q1 - Q0.mean(0)) @ proj)/np.std((Q0-Q0.mean(0)) @ proj)
    r_d, e_h = C.warp_fit(zpre, zpost, C.EGRID, 'dil')
    r_s, d_h = C.warp_fit(zpre, zpost, C.DGRID, 'shift')
    lam = math.log(r_s/r_d) if r_d > 0 else float('nan')
    R2 = 1 - r_d/max(np.mean(np.sum((zpost-zpost.mean(0))**2, 1)), 1e-12)
    kx = e_h/(1+e_h)
    v = "K3_REFUTE" if lam <= -0.10 else ("support-side" if lam >= 0.10 else "neither")
    print(f"   {epsv:5.2f}  {R2:6.3f}  {kx:+.4f}  {lam:+8.3f}   {v:14s}  {d_h:+.3f}")
    rows.append((epsv, kx, lam, R2))

print("")
print("== A2b. positive control: EVERYTHING (drive + tau_m + delays) rescaled = a true time dilation ==")
for epsv in [0.10, 0.20]:
    _, X1 = simulate(1.0+epsv, W, ell, v0, tau_m=TAU_M/(1+epsv), drive_shift=0.0)
    ts2 = ts
    Q1 = bin15(ts2, X1)
    zpost = ((Q1 - Q0.mean(0)) @ proj)/np.std((Q0-Q0.mean(0)) @ proj)
    r_d, e_h = C.warp_fit(zpre, zpost, C.EGRID, 'dil'); r_s, d_h = C.warp_fit(zpre, zpost, C.DGRID, 'shift')
    lam = math.log(r_s/r_d) if r_d > 0 else float('nan')
    print(f"   eps_v={epsv:.2f} (drive kernel NOT rescaled): k_x={e_h/(1+e_h):+.4f} Lam_x={lam:+.3f}")
    _, X2 = simulate(1.0+epsv, W, ell, v0, tau_m=TAU_M/(1+epsv))
    Q2 = bin15(ts, X2)
    zpost2 = ((Q2 - Q0.mean(0)) @ proj)/np.std((Q0-Q0.mean(0)) @ proj)
    r_d2, e2 = C.warp_fit(zpre, zpost2, C.EGRID, 'dil'); r_s2, d2 = C.warp_fit(zpre, zpost2, C.DGRID, 'shift')
    print(f"      idem, tau_m also rescaled: k_x={e2/(1+e2):+.4f} Lam_x={math.log(r_s2/r_d2):+.3f} R2={1-r_d2/max(np.mean(np.sum((zpost2-zpost2.mean(0))**2,1)),1e-12):.3f}")

print("")
print("== A2c. fixed transmission-delay change (F-01's mechanism) through the same circuit ==")
def sim_extra_delay(dtau):
    tau = ell/v0 + dtau
    nt = int(TMAX/DT); lag = np.maximum(np.round(tau/DT).astype(int), 1)
    X = np.zeros((nt, NU)); b = np.zeros(NU); b[0] = 1.0
    tss = np.arange(nt)*DT
    I = np.outer(np.exp(-0.5*((tss-0.08)/0.05)**2), b)*1.6
    for k in range(1, nt):
        s = np.zeros(NU)
        for i in range(NU):
            for j in range(NU):
                kk = k-1-lag[i, j]
                if kk >= 0: s[i] += W[i, j]*math.tanh(X[kk, j])
        X[k] = X[k-1] + DT/TAU_M*(-X[k-1] + s + I[k-1])
    return tss, X
for dt in [0.004, 0.010]:
    tss, Xd = sim_extra_delay(dt)
    Qd = bin15(tss, Xd)
    zpost = ((Qd - Q0.mean(0)) @ proj)/np.std((Q0-Q0.mean(0)) @ proj)
    r_d, e_h = C.warp_fit(zpre, zpost, C.EGRID, 'dil'); r_s, d_h = C.warp_fit(zpre, zpost, C.DGRID, 'shift')
    lam = math.log(r_s/r_d) if r_d > 0 else float('nan')
    print(f"   d_tau=+{dt*1000:.0f} ms/edge: k_x={e_h/(1+e_h):+.4f} shift_hat={d_h:+.3f}s Lam_x={lam:+.3f}"
          f"  -> {'K3_REFUTE' if lam<=-0.10 else 'not killed'}")
