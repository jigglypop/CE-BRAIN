"""Development: reproduce published fresh32 aggregates and per-split counts for both SPD configs."""
import json
import numpy as np
import metric_models as M
from kc_data import load_table, fresh_tasks, FRESH_SEEDS, PUBLICATION

t = load_table()
pub = json.loads((PUBLICATION / "fresh32_summary.json").read_text())
errs = {"previous": [], "candidate": []}
for seed in FRESH_SEEDS:
    tasks = fresh_tasks(t, seed)
    for name, cfg in (("previous", M.PREVIOUS), ("candidate", M.PUBLISHED)):
        e = [M.predict_constant_spd(M.fit_constant_spd(task["train"], cfg), task["test_x"], cfg["power"])
             - task["test_y"] for task in tasks]
        errs[name].append(np.concatenate(e).reshape(-1))
for name in errs:
    e = np.concatenate(errs[name])
    print(name, f"rmse {np.sqrt(np.mean(e ** 2)):.8f} (pub {pub[name]['rmse']:.8f}) "
                f"mae {np.mean(np.abs(e)):.8f} (pub {pub[name]['mae']:.8f})")
rp = np.array([np.sqrt(np.mean(e ** 2)) for e in errs["previous"]])
rc = np.array([np.sqrt(np.mean(e ** 2)) for e in errs["candidate"]])
mp = np.array([np.mean(np.abs(e)) for e in errs["previous"]])
mc = np.array([np.mean(np.abs(e)) for e in errs["candidate"]])
print("rmse improved", int((rc < rp).sum()), "mae improved", int((mc < mp).sum()),
      "both", int(((rc < rp) & (mc < mp)).sum()), "(pub", pub["rmse_improved_splits"], pub["mae_improved_splits"],
      pub["both_improved_splits"], ")")
print("closest margins rmse", np.sort(np.abs(rc - rp))[:3], "mae", np.sort(np.abs(mc - mp))[:3])
