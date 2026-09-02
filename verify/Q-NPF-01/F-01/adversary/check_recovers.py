# -*- coding: utf-8 -*-
"""F-01 recovers 3 limits, independently recomputed (not reusing card verify block).
   L1: DTheta=0 ; L2: -qdd/qd vs eq (21.47)/(21.48) ; L3: chart re-expression (u-indep AND u-dep).
"""
import numpy as np, sympy as sp

SEED = 20260902
rng = np.random.default_rng(SEED)
out = []

def say(k, v):
    out.append((k, v)); print(f"{k:52s} {v}")

# ---------- L1: DTheta = 0  (Delta_tau -> 0, J_post = J_pre) ----------
u, D, c, s, a = sp.symbols('u Delta c sigma alpha', positive=True)
# generic d-dim: g_pre(u) arbitrary SPD family; shift hypothesis g_post(u)=g_pre(u-D)
# scalar surrogate for logdet: L(u) = log V_g(u)
L = sp.Function('L')
lhs_L1 = (L(u - D) - L(u)).subs(D, 0)
say("L1 lhs trE(DTheta=0)", sp.simplify(lhs_L1))
rhs_L1 = (-a*D*sp.diff(L(u), u)).subs(D, 0)        # alpha = ARBITRARY coefficient
say("L1 rhs with ARBITRARY coeff alpha", sp.simplify(rhs_L1))
say("L1 discriminates coeff?", "NO - 0=0 for every alpha")

# ---------- L2: -qdd/qd, 1-D Gaussian family, g=(dq/du)^2/sigma^2 ----------
q = sp.Rational(1,2)*u**2
g_pre = (sp.diff(q, u)/s)**2
logV = sp.log(sp.sqrt(g_pre))
trE_exact = sp.simplify(sp.log(sp.sqrt(g_pre.subs(u, u-D)))-sp.log(sp.sqrt(g_pre)))
say("L2 trE_exact", sp.simplify(trE_exact))
say("L2 lim trE/D (D->0)", sp.simplify(sp.limit(trE_exact/D, D, 0)))
say("L2 -d_u logV  (= -qdd/qd)", sp.simplify(-sp.diff(logV, u)))
say("L2 card claim -1/u matches", sp.simplify(sp.limit(trE_exact/D, D, 0) + 1/u) == 0)
# same for a general q: the identity is Jacobi/chain rule, holds for ANY q
qg = sp.Function('q')
gg = (sp.diff(qg(u), u)/s)**2
lv = sp.log(sp.sqrt(gg))
say("L2 general -d_u log V_g", sp.simplify(-sp.diff(lv, u)))
say("L2 is it independent of the shift hypothesis?", "NO - trE_exact is DEFINED via g(u-D)")

# ---------- L2b: does an internal delay change actually produce a pure time shift? ----------
# leaky recurrent unit with cue-locked (NOT shifted) external drive:
#   tau_m x' = -x + w*tanh(x(t-tau)) + I(t) ,  I cue-locked
def run(tau, T=3.0, dt=1e-4, tau_m=0.05, w=0.9, x0=0.0):
    n = int(T/dt); nd = int(round(tau/dt))
    x = np.zeros(n+1); buf = np.zeros(nd+1)  # history = 0
    t = np.arange(n+1)*dt
    I = 1.5*np.exp(-0.5*((t-0.30)/0.12)**2)   # cue-locked pulse at 0.30 s
    for k in range(n):
        xd = x[k-nd] if k-nd >= 0 else 0.0
        x[k+1] = x[k] + dt*(-x[k] + w*np.tanh(xd) + I[k])/tau_m
    return t, x

dtau = 0.004
t, xA = run(0.020)
_, xB = run(0.020 + dtau)
dt = t[1]-t[0]; k = int(round(dtau/dt))
shift = np.concatenate([np.zeros(k), xA[:-k]])          # xA(t - dtau) = pure-lag prediction
m = (t > 0.15) & (t < 1.5)
num = np.linalg.norm((xB - shift)[m]); den = np.linalg.norm((xB - xA)[m])
say("L2b ||x_{tau+d} - x_tau(.-d)|| / ||x_{tau+d}-x_tau||", f"{num/den:.4f}")
# scaling: if pure-lag were exact to O(dtau), ratio -> 0 as dtau -> 0
for dd in (0.008, 0.004, 0.002, 0.001):
    _, xb = run(0.020+dd); kk = int(round(dd/dt))
    sh = np.concatenate([np.zeros(kk), xA[:-kk]])
    r = np.linalg.norm((xb-sh)[m])/max(np.linalg.norm((xb-xA)[m]), 1e-300)
    say(f"L2b residual ratio at dtau={dd:.3f}", f"{r:.4f}")

# ---------- L3: chart re-expression ----------
def spd(dseed):
    r = np.random.default_rng(dseed); A = r.normal(size=(3,3))
    return A@A.T + 0.5*np.eye(3)
def gfield(uu, base):
    # smooth SPD family g(u) = M(u)^T base M(u)
    M = np.array([[1+0.6*np.sin(2*uu), 0.2*uu, 0.0],
                  [0.1, 1+0.4*uu, 0.3*np.cos(uu)],
                  [0.0, 0.15*uu, 1+0.5*np.exp(-uu)]])
    return M.T@base@M
base = spd(1)
Dtau = 0.05; ug = np.array([0.45, 0.75, 1.05]); h = 0.3
def logV(uu, phi=None):
    g = gfield(uu, base)
    if phi is not None:
        J = phi(uu); g = np.linalg.inv(J).T@g@np.linalg.inv(J)
    return 0.5*np.log(np.linalg.det(g))
def trE(uu, phi=None):
    gp = gfield(uu, base); gq = gfield(uu-Dtau, base)   # pure-lag post
    if phi is not None:
        J = phi(uu); Ji = np.linalg.inv(J)
        gp = Ji.T@gp@Ji; gq = Ji.T@gq@Ji                # SAME chart at the same u
    A = np.linalg.solve(gp, gq)
    return 0.5*np.sum(np.log(np.linalg.eigvals(A).real))
def beta1(phi=None):
    y = np.array([trE(x, phi) for x in ug])
    T = np.array([-Dtau*(logV(x+h, phi)-logV(x-h, phi))/(2*h) for x in ug])
    A = np.vstack([T, np.ones_like(T)]).T
    return np.linalg.lstsq(A, y, rcond=None)[0][0]
Jc = np.array([[1.3,0.2,0.0],[0.0,0.8,0.1],[0.4,0.0,1.1]])
say("L3 beta1 identity chart", f"{beta1(None):.6f}")
say("L3 beta1 u-INDEPENDENT chart", f"{beta1(lambda x: Jc):.6f}")
say("L3 trE invariant (u-indep)", f"{trE(0.75)-trE(0.75, lambda x: Jc):.3e}")
Ju = lambda x: Jc@np.diag([np.exp(0.9*x), np.exp(-0.4*x), 1.0])
say("L3 trE invariant (u-DEPENDENT)", f"{trE(0.75)-trE(0.75, Ju):.3e}")
say("L3 beta1 u-DEPENDENT chart", f"{beta1(Ju):.6f}")
Ju2 = lambda x: Jc@np.diag([np.exp(3.0*x), np.exp(-0.4*x), 1.0])
say("L3 beta1 u-DEP chart (stronger)", f"{beta1(Ju2):.6f}")

# ---------- gain-only orthogonality (ladder step 3, second half) ----------
aa = 1.7
def trE_gain(uu):
    gp = gfield(uu, base); gq = aa**2*gp
    return 0.5*np.sum(np.log(np.linalg.eigvals(np.linalg.solve(gp, gq)).real))
y = np.array([trE_gain(x) for x in ug])
T = np.array([-Dtau*(logV(x+h)-logV(x-h))/(2*h) for x in ug])
A = np.vstack([T, np.ones_like(T)]).T
say("gain-only beta1 (free intercept)", f"{np.linalg.lstsq(A,y,rcond=None)[0][0]:.3e}")
say("gain-only trE constant in u", f"{np.ptp(y):.3e}")
