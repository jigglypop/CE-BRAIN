"""Development: exercise confirmation-only code paths on synthetic copies of the primary panel (no confirmation data)."""
import copy
import json
from pathlib import Path
import run_curved_metric as R
from kc_data import FRESH_SEEDS, load_table

here = Path(__file__).resolve().parent
dev = json.loads((here / "results_development_v1.json").read_text(encoding="utf-8"))
summary = {p: copy.deepcopy(dev["panels"]["leave1"]) for p in ("leave1", "leave2", "slot0", "slot1")}
per_seed = {f"fresh:{s}": copy.deepcopy(dev["panels"]["leave1"]) for s in FRESH_SEEDS}
fresh = R.fresh_summary(per_seed)
crit = R.criteria(summary, fresh, dev["final_model"])
table = load_table()
repro = R.baseline_reproduction(table, summary, fresh, {"synthetic": True})
print("fresh keys", sorted(fresh), "criteria keys", sorted(crit), "verdict (synthetic, meaningless)", crit["verdict"])
print("repro keys", sorted(repro))
