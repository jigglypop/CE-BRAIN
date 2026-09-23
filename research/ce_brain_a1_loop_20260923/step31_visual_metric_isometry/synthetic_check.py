import importlib.util, numpy as np
s = importlib.util.spec_from_file_location("mi", r"C:/dev/ce/ce-agi-runtime/research/ce_brain_a1_loop_20260923/step31_visual_metric_isometry/metric_isometry.py")
mi = importlib.util.module_from_spec(s); s.loader.exec_module(mi)
# 1) regular hexagon: equal weights -> 60/60/60, M = HEX up to rotation
M, a, t = mi.metric_map(np.array([1.0, 1.0, 1.0])); print("equal w: angles", np.round(a, 2), "sum", round(t, 2))
# 2) the hypothesis check: a true metric (triangle angles 54.9,54.9,70.3) -> cot weights -> recover angles
true = np.radians([54.9, 54.9, 70.2]); w = 1 / np.tan(true); M, a, t = mi.metric_map(w * 7.3); print("recover:", np.round(a, 2), round(t, 2))
# 3) vectors antiparallel in a metric frame appear non-antiparallel in the hex frame; mapping back restores them
Mtrue = M
Minv = np.linalg.inv(Mtrue)
vis = {"a": np.array([1, 0.0]), "b": np.array([-1, 0.0]), "c": np.array([0, 1.0]), "d": np.array([0, -1.0])}
vecs = {f"T4{s}": (Minv @ v)[None, :].repeat(5, 0) for s, v in vis.items()}
vecs.update({f"T5{s}": (Minv @ v)[None, :].repeat(5, 0) for s, v in vis.items()})
print("hex frame:", {k: {x: round(y, 1) for x, y in v.items() if x != "directions_deg"} for k, v in mi.frame_tests(vecs, mi.HEX).items()})
print("metric frame:", {k: {x: round(y, 1) for x, y in v.items() if x != "directions_deg"} for k, v in mi.frame_tests(vecs, Mtrue).items()})
