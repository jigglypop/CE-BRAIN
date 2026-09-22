"""Collect every attempted formula family and the frozen confirmation outcome into results_attempt_log_v1.json."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load(name: str) -> dict:
    return json.loads((HERE / name).read_text(encoding="utf-8"))


contract = load("contract_v1.json")
final = load("results_v1.json")
d8 = load("results_development_attempt_D8.json")
d9 = load("results_development_v1.json")
families = ("published_constant_spd", "affine_x", "affine_phi", "curved_apl_metric", "flat_input_metric",
            "flat_exponent_force")
confirmation = {p: {f: {"rmse": final["panels"][p][f]["rmse"], "mae": final["panels"][p][f]["mae"]} for f in families}
                for p in final["panels"]}
confirmation["fresh32"] = {f: {k: final["fresh32"][f][k] for k in
                               ("rmse", "mae", "rmse_improved_vs_reimplemented_baseline", "sign_test_p_one_sided")}
                           for f in families}
log = {
    "schema": "ce-curved-metric-attempt-log-v1",
    "contract_versions": ["contract_v1.json"],
    "contract_sha256": hashlib.sha256((HERE / "contract_v1.json").read_bytes()).hexdigest(),
    "formula_families_attempted": len(contract["development_attempts"]),
    "valid_curved_riemannian_families": sum(a["curved"] is True for a in contract["development_attempts"]),
    "families_evaluated_on_confirmation": ["curved_apl_metric (D9)"],
    "development_attempts": contract["development_attempts"],
    "development_nested_primary": {
        "D8_two_parameter": {f: d8["panels"]["leave1"][f]["rmse"] for f in d8["panels"]["leave1"]},
        "D9_calyx": {f: d9["panels"]["leave1"][f]["rmse"] for f in d9["panels"]["leave1"]}},
    "confirmation_v1": confirmation,
    "criteria_v1": final["criteria"],
    "verdict": final["criteria"]["verdict"],
    "post_confirmation_revisions": "none; any revision would be tuned on opened panels",
}
(HERE / "results_attempt_log_v1.json").write_text(json.dumps(log, ensure_ascii=False, indent=1), encoding="utf-8")
print(log["verdict"], log["formula_families_attempted"], log["valid_curved_riemannian_families"])
