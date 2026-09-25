"""Predictive (visual-teacher) learning on a fixed-contact network (step 35 core).

Rule (Vafidis et al. 2022 eLife, simplified to one compartment): for every existing synapse onto an EPG neuron,
dW_ij = eta * (x_i - p_i) * x_j, where x_i is the EPG rate with visual input and p_i = sigma(w0 (W x)_i + b_i) the
rate the recurrent/rotation input alone predicts. Signs are kept (Dale), contacts are fixed (no new synapses).
Dynamics: tau x' = -x + sigma(w0 W x + b + I_vis + u), u = +k v on left PEN, -k v on right PEN.
"""
from __future__ import annotations

import numpy as np

DT = 0.1


def sig(z):
    return 1.0 / (1.0 + np.exp(-z))


class Net:
    def __init__(self, W, epg, ang, gamma, w0, bias, k_vel=10.0, vis_amp=4.0, vis_kappa=3.0, vis_base=-1.0):
        self.W = W.copy()
        self.mask = W != 0
        self.sign = np.sign(W)
        self.epg, self.ang, self.gamma = epg, ang, gamma
        self.w0, self.bias = w0, bias
        self.k, self.amp, self.kap, self.vbase = k_vel, vis_amp, vis_kappa, vis_base
        self.x = np.full(W.shape[0], sig(bias.mean() if np.ndim(bias) else bias))

    def vis(self, theta):
        v = np.zeros(self.W.shape[0])
        v[self.epg] = self.amp * np.exp(self.kap * (np.cos(self.ang - theta) - 1)) + self.vbase
        return v

    def step(self, theta=None, v=0.0, eta=0.0):
        rec = self.w0 * (self.W @ self.x) + self.bias + v * self.k * self.gamma
        drive = rec + (self.vis(theta) if theta is not None else 0.0)
        new = self.x + DT * (-self.x + sig(drive))
        if eta > 0 and theta is not None:
            e = sig(drive[self.epg]) - sig(rec[self.epg])
            dW = eta * np.outer(e, self.x)
            rows = self.W[self.epg]
            rows += dW * self.mask[self.epg]
            rows = self.sign[self.epg] * np.maximum(self.sign[self.epg] * rows, 0)
            self.W[self.epg] = rows
        self.x = new

    def centre(self):
        e = self.x[self.epg] - self.x[self.epg].min()
        return float(np.angle(np.sum(e * np.exp(1j * self.ang))))


def train(net, steps, eta, rng, v_sd=0.05, tau_v=20.0):
    theta, v = 0.0, 0.0
    for _ in range(steps):
        v += DT * (-v / tau_v) + np.sqrt(2 * DT / tau_v) * v_sd * rng.standard_normal()
        theta += v * DT
        net.step(theta, v, eta)
    return net


def retention(net, headings_deg=np.arange(16) * 22.5, t_cue=20.0, t_dark=100.0):
    finals = []
    for h in headings_deg:
        net.x[:] = sig(net.bias)
        for _ in range(int(t_cue / DT)):
            net.step(np.radians(h), 0.0)
        for _ in range(int(t_dark / DT)):
            net.step(None, 0.0)
        finals.append(np.degrees(net.centre()))
    err = np.abs((np.array(finals) - headings_deg + 180) % 360 - 180)
    return float(np.mean(err <= 22.5)), float(np.median(err))


def integration(net, vels=(-0.1, -0.05, -0.02, 0.02, 0.05, 0.1), t_cue=20.0, t_run=60.0):
    out = []
    for v in vels:
        net.x[:] = sig(net.bias)
        for _ in range(int(t_cue / DT)):
            net.step(0.0, 0.0)
        ph = []
        for s in range(int(t_run / DT)):
            net.step(None, v)
            if s % 10 == 0:
                ph.append(net.centre())
        ph = np.unwrap(ph)
        t = np.arange(len(ph)) * 10 * DT
        half = t >= t_run / 3
        out.append(float(np.polyfit(t[half], ph[half], 1)[0]))
    vs, bv = np.array(vels), np.array(out)
    gain = float(vs @ bv / (vs @ vs))
    r2 = float(1 - np.sum((bv - gain * vs) ** 2) / np.sum((bv - bv.mean()) ** 2)) if np.ptp(bv) > 0 else 0.0
    return {"velocities": list(vels), "bump_velocity": out, "gain": gain, "R2": r2}
