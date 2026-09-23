import importlib.util, numpy as np
spec = importlib.util.spec_from_file_location("iso", r"C:/dev/ce/ce-agi-runtime/research/ce_brain_a1_loop_20260923/step23_isometry_generator/isometry.py")
iso = importlib.util.module_from_spec(spec); spec.loader.exec_module(iso)
rng = np.random.default_rng(1)
N = 16
ang = np.arange(N) * 2 * np.pi / N
K = lambda a, b, s=0.0, k=3.0: np.exp(k * np.cos(a[:, None] - b[None, :] - s))
for D in (20.0, 45.0, 55.0, 70.0):
    Dr = np.radians(D)
    kind = ["EPG"] * N + ["PEN_a(PEN1)"] * (2 * N) + ["PEG"] * N
    side = [""] * N + ["left"] * N + ["right"] * N + [""] * N
    n = 4 * N
    E, L, R, G = slice(0, N), slice(N, 2 * N), slice(2 * N, 3 * N), slice(3 * N, 4 * N)
    w = np.zeros((n, n))
    w[E, E] = 2 * K(ang, ang, 0, 3)     # strong EPG recurrence (via PEG-like local loop)
    w[G, E] = K(ang, ang, 0, 4); w[E, G] = K(ang, ang, 0, 4)
    w[L, E] = K(ang, ang, 0, 4); w[R, E] = K(ang, ang, 0, 4)
    w[E, L] = 0.4 * K(ang, ang, Dr, 4); w[E, R] = 0.4 * K(ang, ang, -Dr, 4)
    w *= 1 + 0.05 * rng.random((n, n))
    res = iso.analyse(w, kind, side, ang)
    r = res["routes"]
    print(D, "K1 K2 K3", res["K1_invariance"], res["K2_isometry"], res["K3_literature_shift"],
          "lam", {m: [round(x, 3) for x in res["pairs"][m]["lambda"]] for m in res["pairs"] if res["pairs"][m]},
          "psi", {m: {s: round(r[m][s]["angle_deg"], 1) for s in ("left", "right")} for m in r},
          "conf", {m: round(min(r[m][s]["conformal_fraction"] for s in r[m]), 3) for m in r})
