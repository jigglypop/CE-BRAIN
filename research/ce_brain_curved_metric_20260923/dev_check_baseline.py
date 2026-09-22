"""Development: clean baseline reimplementation vs published panel numbers and saved predictions."""
import json
import numpy as np
import metric_models as M
from kc_data import load_table, cohort, panel_tasks, read_selected_predictions, REGIONS, N_POS, PUBLICATION

t = load_table()
full = cohort(t)
Gs = np.array(json.loads((PUBLICATION / "model.json").read_text())["persistent_state"]["metric"])
G = M.fit_constant_spd(full, M.PUBLISHED)
print("full metric max err", np.abs(G - Gs).max())
saved = {k: np.zeros((N_POS, 6)) for k in ("previous", "candidate")}
for row in read_selected_predictions():
    for k in saved:
        saved[k][int(row["position"]) - 1, REGIONS.index(row["region"])] = float(row[k])
summary = json.loads((PUBLICATION / "comparison_summary.json").read_text())
for name, cfg in (("candidate", M.PUBLISHED), ("previous", M.PREVIOUS)):
    for panel in ("leave1", "leave2", "slot0", "slot1"):
        preds, targets = [], []
        for task in panel_tasks(t, panel):
            g = M.fit_constant_spd(task["train"], cfg)
            preds.append(M.predict_constant_spd(g, task["test_x"], cfg["power"]))
            targets.append(task["test_y"])
        p, y = np.concatenate(preds), np.concatenate(targets)
        rmse, mae = np.sqrt(np.mean((p - y) ** 2)), np.mean(np.abs(p - y))
        ref = summary[panel][name]
        extra = ""
        if panel == "leave1":
            extra = f" max pred err {np.abs(p - saved[name]).max():.2e}"
        print(f"{name:9s} {panel:6s} rmse {rmse:.8f} (pub {ref['rmse']:.8f}, d {rmse - ref['rmse']:+.1e}) "
              f"mae {mae:.8f} (pub {ref['mae']:.8f}, d {mae - ref['mae']:+.1e}){extra}", flush=True)
