"""Development (primary panel only): symmetric compartment metric S(y) G0 S(y), fixed-beta grid."""
import numpy as np
import metric_models as M
from kc_data import load_table, panel_tasks

t = load_table()
tasks = panel_tasks(t, "leave1")
ys = np.concatenate([task["test_y"] for task in tasks])
for bc in (-0.6, -0.5, -0.4, -0.3, -0.2, 0.0):
    for bl in (-0.1, 0.0, 0.1):
        model = M.CurvedAPL(bc, bl)
        p = np.concatenate([model.predict(model.fit(task["train"]), task["test_x"]) for task in tasks])
        e = p - ys
        print(f"bc {bc:+.2f} bl {bl:+.2f} rmse {np.sqrt(np.mean(e ** 2)):.8f} mae {np.mean(np.abs(e)):.8f}",
              np.round(np.sqrt(np.mean(e ** 2, axis=0)), 5), flush=True)
