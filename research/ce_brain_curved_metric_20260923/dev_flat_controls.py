"""Development (primary panel only): flat equal-parameter controls for the calyx divisive effect."""
import numpy as np
import metric_models as M
from kc_data import load_table, panel_tasks

t = load_table()
tasks = panel_tasks(t, "leave1")
cfg = M.PUBLISHED
CALYX = np.array([1.0, 0, 0, 0, 0, 0])
ys = np.concatenate([task["test_y"] for task in tasks])


def exponent_map(pc):
    def fmap(x, train_x):
        f = x ** cfg["power"]
        f[:, 0] = x[:, 0] ** pc
        return f
    return fmap


def input_state_map(bc):
    def fmap(x, train_x):
        phi_tr = train_x ** cfg["power"]
        u = M.coupling_direction(phi_tr, cfg)
        s0 = (phi_tr @ u).mean()
        phi = x ** cfg["power"]
        return phi / (1 + bc * CALYX[None, :] * ((phi @ u) / s0 - 1)[:, None])
    return fmap


def run(fmap):
    preds = []
    for task in tasks:
        tr = task["train"]
        force = lambda data, phi, tr=tr: fmap(data["x"], data["x"])
        g = M.fit_constant_spd(tr, cfg, force)
        L = np.linalg.inv(g[:6, :6])
        b = -L @ g[:6, 6]
        preds.append(fmap(np.atleast_2d(task["test_x"]), tr["x"]) @ L.T + b)
    e = np.concatenate(preds) - ys
    return round(float(np.sqrt(np.mean(e ** 2))), 8), round(float(np.mean(np.abs(e))), 8), \
        np.round(np.sqrt(np.mean(e ** 2, axis=0)), 5)


for pc in (0.625, 0.75, 1.0, 1.25, 1.5, 2.0):
    print("calyx exponent", pc, run(exponent_map(pc)), flush=True)
for bc in (-0.2, -0.3, -0.4, -0.5):
    print("input-state calyx divisive", bc, run(input_state_map(bc)), flush=True)
