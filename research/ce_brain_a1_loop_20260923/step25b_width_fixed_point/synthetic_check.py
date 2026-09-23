import numpy as np, importlib.util
spec = importlib.util.spec_from_file_location("wc", r"C:/dev/ce/ce-agi-runtime/research/ce_brain_a1_loop_20260923/step25_width_law/width_core.py")
wc = importlib.util.module_from_spec(spec); spec.loader.exec_module(wc)
N = 16
ang = np.arange(N) * 2 * np.pi / N
K = lambda s=0.0, k=3.0: np.exp(k * np.cos(ang[:, None] - ang[None, :] - s))
def fixed_point(W, x0, eta=0.2, iters=40000):
    x = x0 / np.linalg.norm(x0)
    for i in range(iters):
        new = x + eta * np.maximum(W @ x, 0); new /= np.linalg.norm(new)
        if np.max(np.abs(new - x)) < 1e-11: x = new; break
        x = new
    h = np.maximum(W @ x, 0); Lam = float(x @ h)
    return x, Lam, float(np.linalg.norm(h - Lam * x) / max(np.linalg.norm(Lam * x), 1e-12))
def harm(v, m): return abs(np.sum(v * np.exp(-1j*m*ang)))**2 / (len(v) * np.sum(np.abs(v)**2)) * (1 if m == 0 else 2)
for D in (np.radians(55),):
    for inhib in (1.0, 2.0, 3.0, 4.0, 6.0):
        n = 4 * N + 1
        E, L, R, Dl, G = slice(0, N), slice(N, 2*N), slice(2*N, 3*N), slice(3*N, 4*N), slice(4*N, 4*N + 1)
        w = np.zeros((n, n))
        w[E, E] = K(0, 3)
        w[L, E] = K(0, 4); w[R, E] = K(0, 4); w[E, L] = 0.5 * K(D, 4); w[E, R] = 0.5 * K(-D, 4)
        w[Dl, E] = K(0, 1); w[E, Dl] = -0.3 * K(np.pi, 1)
        w[G, E] = 1.0; w[E, G] = -inhib * K(0, 3).sum(1)[:, None] / 1.0 / 1
        W = w / np.abs(w).sum(1, keepdims=True).clip(1e-12)
        lam, V = np.linalg.eig(W); o = np.argsort(-lam.real)
        rows = [(round(lam[k].real, 3), round(harm(V[E, k], 0), 2), round(harm(V[E, k], 1), 2), round(harm(V[E, k], 2), 2)) for k in o[:6]]
        x0 = np.zeros(n); x0[E] = np.maximum(np.cos(ang), 0)
        x, Lam, res = fixed_point(W, x0)
        print("inhib", inhib, "top modes (re,P0,P1,P2)", rows)
        print("     fixed point Lam %.4f resid %.1e EPG fwhm %s" % (Lam, res, wc.fwhm_profile(x[E], ang)))
