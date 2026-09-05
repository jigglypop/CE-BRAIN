"""원 코호트의 평균 파형·잡음 진단. 결과 뒤 탐색이며 기존 회귀를 변경하지 않는다."""
import hashlib
import io
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
DB = HERE.parents[2] / "data/external/allen_synphys_r21/synphys_r2.1_small.sqlite"
RATE = 20000


def digest(path):
    with path.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def decode(raw, start):
    if not raw or start is None:
        return None
    values = np.load(io.BytesIO(raw), allow_pickle=False)
    if values.ndim != 1 or not np.isfinite(values).all():
        return None
    # 공식 평균반응 처리의 첫 7ms 기준선을 사용하되 자극 이전인지 별도 확인한다.
    n = round(.007 * RATE)
    if len(values) < n or start + .007 > 0:
        return None
    return {"samples": len(values), "start_s": start,
            "baseline_mean": float(values[:n].mean()),
            "baseline_sd": float(values[:n].std()), "duration_s": len(values) / RATE}


def summary(values):
    values = [v for v in values if v is not None and np.isfinite(v)]
    return {"n": len(values), "quantiles_0_25_50_75_100": np.quantile(values, [0, .25, .5, .75, 1]).tolist() if values else None}


def main():
    output = HERE / "waveform_audit_result.json"
    if output.exists():
        raise RuntimeError("기존 파형 진단 영수증을 보존합니다.")
    contract = json.loads((HERE / "component_contract.json").read_text(encoding="utf-8"))
    assert digest(DB) == contract["db_sha256"]
    original = json.loads((HERE / "component_result.json").read_text(encoding="utf-8"))
    result = {"completed_at": datetime.now(timezone.utc).isoformat(),
              "kind": "POST_RESULT_MEASUREMENT_AUDIT", "db_sha256": digest(DB),
              "code_sha256": digest(Path(__file__)), "sample_rate_hz": RATE,
              "source_manifest_sha256": digest(HERE / "qc_sources/manifest.json"),
              "rules": "원 분석의 synapse ID 전부, 새 제외 없이 진단. 첫7ms baseline SD; 시작+7ms<=0 확인. |fit_amp|/SD<1 및<3 건수는 기술적 요약이며 검출검정·제외 기준 아님. 평균 waveform의 SD는 단일 시행 잡음이나 진폭 추정 표준오차가 아님.",
              "cohorts": []}
    with sqlite3.connect(DB.as_uri() + "?mode=ro", uri=True) as db:
        db.row_factory = sqlite3.Row
        result["raw_table_counts"] = {t: db.execute("SELECT count(*) FROM " + t).fetchone()[0] for t in ["pulse_response", "recording", "test_pulse", "patch_clamp_recording", "stim_pulse"]}
        for cohort in original["cohorts"]:
            records = []
            for sid in cohort["synapse_ids"]:
                syn = db.execute("SELECT * FROM synapse WHERE id=?", (sid,)).fetchone()
                rest = db.execute("SELECT * FROM resting_state_fit WHERE synapse_id=?", (sid,)).fetchall()
                assert len(rest) <= 1
                for mode, amp_col in [("ic", "psp_amplitude"), ("vc", "psc_amplitude")]:
                    entry = {"synapse_id": sid, "mode": mode, "summary_amp": syn[amp_col], "resting_record": bool(rest)}
                    if rest:
                        row = rest[0]
                        entry["resting_fit_amp"] = row[mode + "_amp"]
                        entry["same_amplitude"] = bool(np.isclose(syn[amp_col], row[mode + "_amp"], rtol=1e-12, atol=0)) if row[mode + "_amp"] is not None else False
                        entry["resting_nrmse"] = row[mode + "_nrmse"]
                        wave = decode(row[mode + "_avg_data"], row[mode + "_avg_data_start_time"])
                        entry["waveform"] = wave
                        entry["amp_over_baseline_sd"] = abs(syn[amp_col]) / wave["baseline_sd"] if wave and wave["baseline_sd"] > 0 else None
                    fits = db.execute("SELECT * FROM avg_response_fit WHERE synapse_id=? AND clamp_mode=? ORDER BY holding", (sid, mode)).fetchall()
                    entry["all_pulse_fits"] = []
                    for fit in fits:
                        wave = decode(fit["avg_data"], fit["avg_data_start_time"])
                        stored = fit["avg_baseline_noise"]
                        entry["all_pulse_fits"].append({"id": fit["id"], "holding": fit["holding"],
                            "qc": fit["manual_qc_pass"], "fit_amp": fit["fit_amp"], "n_averaged": fit["n_averaged_responses"],
                            "stored_baseline_sd": stored, "waveform": wave,
                            "baseline_relative_discrepancy": abs(wave["baseline_sd"] - stored) / stored if wave and stored and stored > 0 else None})
                    records.append(entry)
            item = {"cohort": cohort["cohort"], "records": records, "by_mode": {}}
            for mode in ["ic", "vc"]:
                selected = [r for r in records if r["mode"] == mode]
                ratios = [r.get("amp_over_baseline_sd") for r in selected]
                item["by_mode"][mode] = {
                    "n": len(selected), "decoded": sum(bool(r.get("waveform")) for r in selected),
                    "amplitude_mismatch": sum(not r.get("same_amplitude", False) for r in selected),
                    "amp_over_sd": summary(ratios),
                    "amp_below_sd": sum(v is not None and v < 1 for v in ratios),
                    "amp_below_3sd": sum(v is not None and v < 3 for v in ratios),
                    "no_all_pulse_qc_pass": sum(not any(f["qc"] == 1 for f in r["all_pulse_fits"]) for r in selected),
                    "baseline_relative_discrepancy": summary([f["baseline_relative_discrepancy"] for r in selected for f in r["all_pulse_fits"]])}
                item["by_mode"][mode]["smallest_three"] = [{k:v for k,v in r.items() if k != "all_pulse_fits"} for r in sorted(selected, key=lambda r: abs(r["summary_amp"]))[:3]]
            result["cohorts"].append(item)
    with output.open("x", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2, allow_nan=False)
    print(json.dumps({"raw_table_counts": result["raw_table_counts"], "cohorts": [{"cohort": c["cohort"], "by_mode": {m: {k:v for k,v in s.items() if k != "smallest_three"} for m,s in c["by_mode"].items()}} for c in result["cohorts"]]}, indent=2))


if __name__ == "__main__":
    main()
