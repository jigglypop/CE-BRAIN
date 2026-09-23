import importlib.util, numpy as np
s = importlib.util.spec_from_file_location("vs", r"C:/dev/ce/ce-agi-runtime/research/ce_brain_a1_loop_20260923/step30_visual_spectrum/visual_spectrum.py")
vs = importlib.util.module_from_spec(s); s.loader.exec_module(vs)
rng = np.random.default_rng(0)
# synthetic hex patch (elliptical), coupling = distance kernel (local, isotropic) + noise; and a disordered control
pts = []
for a in range(-20, 21):
    for b in range(-20, 21):
        p = a * np.array([1.0, 0.0]) + b * np.array([-0.5, np.sqrt(3) / 2])
        if (p[0] / 14) ** 2 + (p[1] / 20) ** 2 <= 1: pts.append(p)
xy = np.array(pts); d = np.linalg.norm(xy[:, None] - xy[None], axis=2)
C = np.exp(-d ** 2 / 2) * (d > 0) * np.exp(0.3 * rng.normal(size=d.shape))
print("local kernel:", {k: (round(v, 3) if isinstance(v, float) else v) for k, v in vs.analyse(C, xy, rng).items() if not isinstance(v, (list, dict))})
Cr = C[np.ix_(rng.permutation(len(xy)), rng.permutation(len(xy)))]
print("scrambled:", {k: (round(v, 3) if isinstance(v, float) else v) for k, v in vs.analyse(Cr, xy, rng).items() if not isinstance(v, (list, dict))})
