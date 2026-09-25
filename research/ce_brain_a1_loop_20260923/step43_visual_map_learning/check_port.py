"""Port checks against the authors' own self-checks (result_check.m) and velocity calibration (main_config.m)."""
import numpy as np

import kim2019_model as km

ra = km.ring_params()
print("discrete params: alpha %.4f D %.4f beta %.4f M %d A %.5f S %.5f A_peak %.5f" % (ra["alpha"], ra["D"], ra["beta"], ra["M"], ra["A"], ra["S"], ra["A_peak"]))
rng = np.random.default_rng(0)
T = 2000
cond = {"vel": np.zeros(T), "vis": np.zeros((km.NI, T)), "inj": np.zeros((km.NW, T))}
y0 = rng.random(km.NW) * ra["A"]
y, W, ys = km.simulate(cond, np.zeros((km.NW, km.NI)), y0, learn=False)
print("stationary bump (no input, 20 s): S/sum %.4f  A_peak/max %.4f  active %d" % (ra["S"] / y.sum(), ra["A_peak"] / y.max(), int(np.sum(y > 1e-6))))
for v in (km.VEL_1, 2 * km.VEL_1, 0.375, 0.765):
    cond = {"vel": np.full(T, v), "vis": np.zeros((km.NI, T)), "inj": np.zeros((km.NW, T))}
    y, W, ys = km.simulate(cond, np.zeros((km.NW, km.NI)), y, learn=False)
    ph, _ = km.pva(ys)
    un = np.unwrap(ph)
    t = np.arange(un.size) * km.DT
    m = t > 2
    sp = np.polyfit(t[m], un[m], 1)[0]
    print("vel %.4f -> bump speed %.3f pi rad/s" % (v, sp / np.pi))
