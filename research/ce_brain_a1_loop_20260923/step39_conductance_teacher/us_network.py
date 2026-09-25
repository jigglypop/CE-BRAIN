"""Vafidis et al. 2022 network with the teacher of Urbanczik & Senn 2014 (Neuron 81:521) as an option.

network_us() is the authors' fly_rec.network line by line (noise-free), with one extra somatic term g0 (U* - u): a
conductance teacher that nudges the soma toward a target potential U*(theta) = E_I + (E_E - E_I) g(theta - c).
With g0 = 0 it is the authors' current-based model (checked to machine precision against fly_rec.network).
At the learning fixed point f(u) = f(p V) of the conductance teacher, p V = U* (no saturation needed); for the
current teacher, the fixed point requires saturation wherever the teacher current is non-zero (step 38 note).
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
LOOP = HERE.parent
ROOT = HERE.parents[2]
VAF = ROOT / "data/external/vafidis_2022_learnpi"
sys.path.insert(0, str(VAF))
import fly_rec as rec  # noqa: E402
import utilities as util  # noqa: E402

P = {"dt": 5e-4, "n_neu": 60, "v0": 2, "v_max": 720, "M": 4, "sigma": .15, "inh": -1, "inh_rot": -1.5, "n_sigma": 0,
     "exc": 4, "tau_s": 65, "filt": True, "tau_d": 100, "x0": 1, "beta": 2.5, "gD": 2, "gL": 1, "fmax": .15, "eta": 5e-2}
N, NDIR, DPHI = 60, 30, 12.0
DIR = np.repeat(np.arange(NDIR) * DPHI, 2)
W_ROT = np.diag(np.full(N, 2 / P["fmax"]))
SIGN = np.r_[np.ones(N // 2), -np.ones(N // 2)]
K_VEST = P["v0"] / P["v_max"]


def logistic(x):
    return util.logistic(x, P["x0"], P["beta"], P["fmax"])


SOMA = {"mode": "euler"}   # "euler": authors' explicit step; "exp": exact step of the linear somatic equation


def network_us(f, f_rot, u, w, w_rot, v, r, Iden, V, Delta, PSP, I_PSP, x, train, exc, g0=0.0, Ustar=0.0, tau_l=10):
    """Authors' network() (n_sigma = 0) plus the conductance teacher g0 (U* - u) on the soma."""
    dt, tau_s, tau_d, gD, gL = P["dt"] * 1e3, P["tau_s"], P["tau_d"], P["gD"], P["gL"]
    f_all = np.concatenate((f_rot, f))
    Iden += (- Iden + np.dot(w, f_all) + P["inh"]) * dt / tau_s
    V += (-V + Iden) * dt / tau_l
    I_PSP += (- I_PSP + f_all) * dt / tau_s
    PSP += (-PSP + I_PSP) * dt / tau_l
    x += (f - x) / tau_s
    x_rot = np.concatenate((x[::2], x[1::2]))
    f_new_rot = logistic(np.dot(w_rot, x_rot) + v + P["inh_rot"])
    if SOMA["mode"] == "euler":
        u += (-gL * u + gD * (V - u) + r + exc + g0 * (Ustar - u)) * dt
    else:
        a = gL + gD + g0
        u_inf = (gD * V + r + exc + g0 * Ustar) / a
        u[:] = u_inf + (u - u_inf) * np.exp(-a * dt)
    f_new = logistic(u)
    V_ss = V * gD / (gD + gL)
    error = f_new - logistic(V_ss)
    if train:
        PI = np.outer(error, PSP)
        if P["filt"]:
            Delta += (PI - Delta) * dt / tau_d
        else:
            Delta = PI
        w += P["eta"] * Delta * dt
    return f_new, f_new_rot, u, Iden, V, Delta, w, PSP, I_PSP, x, error


def gauss_ring(c_deg, sigma, ang=DIR):
    return np.exp(-np.sin((np.radians(ang) - np.radians(c_deg)) / 2) ** 2 / (2 * sigma ** 2))


class Teacher:
    """kind 'current': authors' vis_in (M, sigma) + exc; kind 'conductance': g0 (U* - u), U* = EI + (EE - EI) g."""

    def __init__(self, kind, M=4.0, sigma=0.15, g0=0.0, EE=1.16, EI=-1.0):
        self.kind, self.M, self.sigma, self.g0, self.EE, self.EI = kind, M, sigma, g0, EE, EI

    def light(self, c, m=1.0, c2=None, m2=0.0, ang=DIR):
        g = m * gauss_ring(c, self.sigma, ang) + (0.0 if c2 is None else m2 * gauss_ring(c2, self.sigma, ang))
        if self.kind == "current":
            return {"r": self.M * g - P["exc"] - 1, "exc": P["exc"], "g0": 0.0, "Ustar": 0.0}
        return {"r": 0.0, "exc": 0.0, "g0": self.g0, "Ustar": self.EI + (self.EE - self.EI) * np.clip(g, 0.0, 1.0)}


DARK = {"r": 0.0, "exc": 0.0, "g0": 0.0, "Ustar": 0.0}


def zero_state(n=N, m=N):
    return {"f": np.zeros(n), "f_rot": np.zeros(m), "u": np.zeros(n), "Iden": np.zeros(n), "V": np.zeros(n),
            "Delta": np.zeros((n, n + m)), "PSP": np.zeros(n + m), "I_PSP": np.zeros(n + m), "x": np.zeros(n)}


def step(st, w, v, inp, train, w_rot=W_ROT):
    f, f_rot, u, Iden, V, Delta, w, PSP, I_PSP, x, err = network_us(
        st["f"], st["f_rot"], st["u"], w, w_rot, v, inp["r"], st["Iden"], st["V"], st["Delta"], st["PSP"], st["I_PSP"], st["x"],
        train, inp["exc"], inp["g0"], inp["Ustar"])
    st.update(f=f, f_rot=f_rot, u=u, Iden=Iden, V=V, Delta=Delta, PSP=PSP, I_PSP=I_PSP, x=x)
    return w, err


def run(w, phases, every=0, add_r=None):
    """phases: list of (seconds, input dict, omega deg/s). Returns final HD rates and the bump-centre trace."""
    w, st, trace = w.copy(), zero_state(), []
    for sec, inp, omega in phases:
        v = SIGN * K_VEST * omega
        for s in range(int(round(sec / P["dt"]))):
            w, _ = step(st, w, v, inp, False)
            if every and s % every == 0:
                trace.append(com(st["f"]))
    return st["f"], np.array(trace)


def train(w, theta0, teacher, n_snap=100, st=None):
    """Authors' training loop in light along the landmark trajectory theta0 (deg per step)."""
    w, st = w.copy(), (zero_state() if st is None else st)
    v_ang = -np.diff(theta0) / P["dt"]
    steps = theta0.size - 1
    block = max(steps // n_snap, 1)
    snaps, err_hist, acc, cnt = [], [], 0.0, 0
    for i in range(steps):
        inp = teacher.light(-theta0[i])          # authors' landmark theta0 puts the bump at -theta0
        w, err = step(st, w, SIGN * K_VEST * v_ang[i], inp, True)
        acc += float(np.mean(np.abs(err)))
        cnt += 1
        if (i + 1) % block == 0 and len(snaps) < n_snap:
            snaps.append(w.copy())
            err_hist.append(1e3 * acc / cnt)
            acc, cnt = 0.0, 0
    return w, np.array(snaps), np.array(err_hist)


def com(f, ang=DIR):
    return float(np.degrees(np.angle(np.sum(f * np.exp(1j * np.radians(ang))))) % 360)


def shape(f):
    p = f.reshape(NDIR, 2).mean(1)
    q = p - p.min()
    if q.max() <= 1e-9:
        return None, 0, 0.0, 0.0
    peaks = int(np.sum((q > np.roll(q, 1)) & (q >= np.roll(q, -1)) & (q > 0.5 * q.max())))
    a = np.arange(NDIR) * DPHI
    grid = np.arange(0, 360, 0.25)
    fine = np.interp(grid, np.r_[a - 360, a, a + 360], np.r_[q, q, q])
    return float(np.sum(fine >= fine.max() / 2) * 0.25), peaks, float(q.max() / max(p.max(), 1e-12)), float(q.max())


def learned():
    d = np.load(VAF / "fly_rec2Enoughv02inh1rot15NoClipOUsigma225tau05NoBoundx1k1b25s015exc4N60InitNoAnneal05.npz", allow_pickle=True)
    return d["w"][:, :, -1] if d["w"].ndim == 3 else d["w"]


def equivalence_check():
    """g0 = 0 current teacher must reproduce fly_rec.network (training on) to machine precision."""
    rng = np.random.default_rng(0)
    w0 = learned()
    a, b = zero_state(), zero_state()
    wa, wb = w0.copy(), w0.copy()
    th = np.radians(DIR)
    worst = 0.0
    for i in range(4000):
        c = 37.0 + 0.2 * i
        v = SIGN * K_VEST * 90.0
        r = P["M"] * np.exp(-np.sin((th - np.radians(c)) / 2) ** 2 / (2 * P["sigma"] ** 2)) - P["exc"] - 1
        fa = rec.network(a["f"], a["f_rot"], a["u"], wa, W_ROT, v, r, a["Iden"], a["V"], a["Delta"], a["PSP"], a["I_PSP"], a["x"], True,
                         P["eta"], P["x0"], P["beta"], P["fmax"], P["dt"] * 1e3, P["inh"], P["inh_rot"], P["exc"], 0, True, 65, 100, 2, 1)
        a.update(f=fa[0], f_rot=fa[1], u=fa[2], Iden=fa[3], V=fa[4], Delta=fa[5], PSP=fa[7], I_PSP=fa[8], x=fa[9]); wa = fa[6]
        wb, _ = step(b, wb, v, {"r": r, "exc": P["exc"], "g0": 0.0, "Ustar": 0.0}, True)
        worst = max(worst, float(np.max(np.abs(a["f"] - b["f"]))), float(np.max(np.abs(wa - wb))))
    return worst


if __name__ == "__main__":
    print("max |authors - port| over 4000 training steps:", equivalence_check())
