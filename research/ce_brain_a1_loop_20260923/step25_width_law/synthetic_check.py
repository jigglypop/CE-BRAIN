import importlib.util, numpy as np
spec = importlib.util.spec_from_file_location("wc", r"C:/dev/ce/ce-agi-runtime/research/ce_brain_a1_loop_20260923/step25_width_law/width_core.py")
wc = importlib.util.module_from_spec(spec); spec.loader.exec_module(wc)
# analytic check (J0, J1 only): theta_c from -cos(tc)(tc - s c) = rho (s - tc c)
from scipy.optimize import brentq
def analytic(rho):
    f = lambda t: -np.cos(t) * (t - np.sin(t) * np.cos(t)) - rho * (np.sin(t) - t * np.cos(t))
    tc = brentq(f, 0.05, np.pi - 1e-6)
    th = np.arccos((1 + np.cos(tc)) / 2)
    return np.degrees(2 * th)
for rho in (-0.49, 0.0, 0.11, 0.69, 0.84):
    print("rho", rho, "law", round(wc.law_width({0: rho, 1: 1.0}), 1), "analytic", round(analytic(rho), 1),
          "with J2=0.71:", round(wc.law_width({0: rho, 1: 1.0, 2: 0.71}), 1))
# discrete ring network check: 16 glomeruli x 3 neurons, kernel from spectrum, nonlinear power iteration
N = 48; ang = np.repeat(np.arange(16) * 2 * np.pi / 16, 3) + np.random.default_rng(0).normal(0, 0.03, N)
for J in ({0: 0.69, 1: 1.0}, {0: -0.49, 1: 1.0}, {0: 0.2, 1: 1.0, 2: 0.7}):
    d = ang[:, None] - ang[None, :]
    W = (J[0] + sum(2 * J[m] * np.cos(m * d) for m in J if m) ) / N
    x = np.maximum(np.cos(ang), 0)
    for _ in range(3000):
        x = np.maximum(W @ x, 0); x /= np.linalg.norm(x)
    lam = np.linalg.eigvalsh(W)[::-1][:4]
    prof = [x[ang.round(2) == a].mean() for a in np.unique(ang.round(2))]
    print(J, "sim fwhm", wc.fwhm_profile(x, ang), "law", round(wc.law_width(J), 1), "eig", np.round(lam, 3))
