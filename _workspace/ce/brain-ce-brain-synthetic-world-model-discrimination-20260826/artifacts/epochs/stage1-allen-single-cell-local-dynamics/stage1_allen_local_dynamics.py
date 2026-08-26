"""Frozen Stage 1 Allen single-cell local-dynamics evaluation (h5py/numpy only)."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import h5py
import numpy as np


SPECIMEN, SESSION, WELL_KNOWN = "320654829", "320654827", "491201608"
FILENAME, RAW_BYTES = "320654827_ephys.nwb", 53057893
RAW_SHA256 = "fd164a3091fbbb3be358238088afa2e2f08981d49edffa87d55309931a9853ab"
RATE, FACTOR, HISTORY, HORIZON = 200000, 20, 500, 10
STOP = "STAGE1_APPARATUS_STOP"
FIT = tuple(list(range(33, 55)) + list(range(56, 60)) + [5, 6])
DEV, CONFIRM = (60, 62, 64), (61, 63)
NOISE = set(DEV + CONFIRM)
EXPECTED_COUNTS = {**{s: 1054001 for s in list(range(33, 55)) + list(range(56, 60))}, 5: 997844, 6: 1321863,
                   **{s: 4854001 for s in DEV + CONFIRM}}
EXPECTED_BINS = {**{s: 52700 for s in list(range(33, 55)) + list(range(56, 60))}, 5: 49892, 6: 66093,
                 **{s: 242700 for s in DEV + CONFIRM}}
MANIFEST, SCHEMA, RESULT = "stage1-preregistration-manifest.json", "stage1-schema-receipt.json", "stage1-result.json"
PREREG_FILES = ("00-contract.md", "10-data-lock.md", "10-sources.md", "20-hypotheses.md", "30-models.md", "40-metrics.md", "50-gates.md", "20-audit.md", "21-preexecution-validation.md", "stage1_allen_local_dynamics.py", "test_stage1_allen_local_dynamics.py")


def _sha(data: bytes) -> str: return hashlib.sha256(data).hexdigest()
def _array_hash(*items: np.ndarray) -> str: return _sha(b"".join(np.ascontiguousarray(x).tobytes() for x in items))
def _pivot() -> Path: return Path(__file__).resolve().parent
def _atomic(path: Path, payload: dict[str, Any]) -> str:
    body = (json.dumps(payload, sort_keys=True, indent=2) + "\n").encode(); tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_bytes(body); tmp.replace(path); return _sha(body)


def _raw_identity(path: Path) -> dict[str, Any]:
    if path.name != FILENAME or not path.is_file() or path.stat().st_size != RAW_BYTES or _sha(path.read_bytes()) != RAW_SHA256:
        raise RuntimeError(f"{STOP}:raw identity")
    return {"filename": path.name, "bytes": path.stat().st_size, "sha256": RAW_SHA256, "specimen": SPECIMEN, "session": SESSION, "well_known_file": WELL_KNOWN}


def _path(sweep: int, kind: str) -> str:
    return f"/acquisition/timeseries/Sweep_{sweep}/data" if kind == "response" else f"/stimulus/presentation/Sweep_{sweep}/data"
def _epoch(sweep: int, kind: str) -> str: return f"/epochs/Experiment_{sweep}/{kind}"
def _text(value: Any) -> str: return value.decode() if isinstance(value, bytes) else str(value)
def _attr(obj: Any, name: str) -> Any:
    if name not in obj.attrs: raise RuntimeError(f"{STOP}:missing metadata:{name}")
    return obj.attrs[name]


def _rate(group: h5py.Group) -> float:
    if "starting_time" in group and "rate" in group["starting_time"].attrs: return float(group["starting_time"].attrs["rate"])
    if "rate" in group.attrs: return float(group.attrs["rate"])
    raise RuntimeError(f"{STOP}:sampling metadata")


def _schema_sweep(file: h5py.File, sweep: int) -> dict[str, Any]:
    response, stimulus = file[_path(sweep, "response")], file[_path(sweep, "stimulus")]
    response_group, stimulus_group = response.parent, stimulus.parent
    if response.shape != stimulus.shape or len(response.shape) != 1: raise RuntimeError(f"{STOP}:shape:{sweep}")
    units = (_text(_attr(response, "unit")), _text(_attr(stimulus, "unit")))
    conversions = (float(_attr(response, "conversion")), float(_attr(stimulus, "conversion")))
    rates = (_rate(response_group), _rate(stimulus_group))
    if units != ("Volts", "Amps") or rates != (RATE, RATE) or conversions != (1.0, 1.0): raise RuntimeError(f"{STOP}:unit/rate:{sweep}")
    er, es = file[_epoch(sweep, "response")], file[_epoch(sweep, "stimulus")]
    # idx/count are SDK boundary metadata; response/stimulus data values are never indexed here.
    values = [int(er["idx_start"][()]), int(er["count"][()]), int(es["idx_start"][()]), int(es["count"][()])]
    if values[0] != values[2] or values[1] != values[3] or values[0] != 150000 or values[1] != EXPECTED_COUNTS[sweep]:
        raise RuntimeError(f"{STOP}:index_range:{sweep}")
    a, b = 20 * math.ceil(values[0] / 20), 20 * math.floor((values[0] + values[1]) / 20)
    if b <= a or (b - a) // 20 != EXPECTED_BINS[sweep] or b > response.shape[0]: raise RuntimeError(f"{STOP}:aligned range:{sweep}")
    return {"sweep": sweep, "response_path": _path(sweep, "response"), "stimulus_path": _path(sweep, "stimulus"),
            "shape": list(response.shape), "units": list(units), "conversions": list(conversions), "rates": list(rates), "index_inclusive": [values[0], values[0] + values[1] - 1], "aligned_half_open": [a, b], "bins": (b-a)//20}


def _scalar_text(file: h5py.File, path: str) -> str:
    if path not in file: raise RuntimeError(f"{STOP}:schema metadata:{path}")
    value = file[path][()]
    if isinstance(value, np.ndarray): return " ".join(_text(item) for item in value.reshape(-1))
    return _text(value)


def _schema_identity(file: h5py.File) -> dict[str, str]:
    nwb, generated, specimen, session = (_scalar_text(file, path) for path in ("/nwb_version", "/general/generated_by", "/general/aibs_specimen_id", "/general/session_id"))
    if nwb != "NWB-1.0.5" or "IVSCC" not in generated or "1.0" not in generated or specimen != SPECIMEN or session != SESSION:
        raise RuntimeError(f"{STOP}:nwb/pipeline identity")
    return {"nwb_version": nwb, "pipeline": generated, "specimen": specimen, "session": session}


def schema_smoke(raw: Path, *, pivot: Path | None = None) -> dict[str, Any]:
    identity = _raw_identity(raw); pivot = _pivot() if pivot is None else pivot
    with h5py.File(raw, "r") as file:
        # Metadata-only: this path never invokes __getitem__ on any response/stimulus data dataset.
        nwb_pipeline, sweeps = _schema_identity(file), [_schema_sweep(file, sweep) for sweep in FIT + DEV + CONFIRM]
    payload = {"schema": 1, "raw": identity, "nwb_pipeline": nwb_pipeline, "sweeps": sweeps, "confirmation_values_opened": False}
    digest = _atomic(pivot / SCHEMA, payload); return {"receipt_sha256": digest, **payload}


def _block(response: np.ndarray, stimulus: np.ndarray, a: int, b: int) -> tuple[np.ndarray, np.ndarray]:
    if response.ndim != 1 or stimulus.ndim != 1 or len(response) != len(stimulus): raise RuntimeError(f"{STOP}:raw arrays")
    if a % FACTOR or b % FACTOR or b <= a: raise RuntimeError(f"{STOP}:block alignment")
    voltage, current = response[a:b].reshape(-1, FACTOR).mean(1) * 1000.0, stimulus[a:b].reshape(-1, FACTOR).mean(1) * 1e12
    if not np.all(np.isfinite(voltage)) or not np.all(np.isfinite(current)): raise RuntimeError(f"{STOP}:nonfinite data")
    return voltage, current


def _load(file: h5py.File, sweep: int) -> tuple[np.ndarray, np.ndarray, dict[str, Any]]:
    receipt = _schema_sweep(file, sweep); a, b = receipt["aligned_half_open"]
    voltage, current = _block(np.asarray(file[_path(sweep, "response")]), np.asarray(file[_path(sweep, "stimulus")]), a, b)
    if len(voltage) != EXPECTED_BINS[sweep]: raise RuntimeError(f"{STOP}:bin receipt")
    receipt.update({"voltage_sha256": _array_hash(voltage), "current_sha256": _array_hash(current)})
    return voltage, current, receipt


def _rows(voltage: np.ndarray, current: np.ndarray, *, thin: bool) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    k = len(voltage)
    if len(current) != k or k <= HISTORY + HORIZON: raise RuntimeError(f"{STOP}:history boundary")
    t = np.arange(HISTORY, k-HORIZON)
    if thin: t = t[(t-HISTORY) % 10 == 0]
    crossings = np.zeros(k, dtype=np.int8); crossings[:-1] = (voltage[:-1] < 0) & (voltage[1:] >= 0)
    prefix = np.r_[0, np.cumsum(crossings)]
    counts = lambda lag: prefix[t] - prefix[t-lag]
    m0 = np.column_stack((voltage[t], current[t]))
    m1 = np.column_stack((m0, voltage[t-10], voltage[t-50], voltage[t-200], current[t-10], current[t-50], current[t-200], counts(20), counts(100), counts(500)))
    event = np.array([bool(np.any(crossings[index:index+HORIZON])) for index in t], dtype=np.float64)
    return m0, m1, voltage[t+HORIZON], event


def _fit_standardize(features: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    mean, scale = features.mean(0), features.std(0)
    if not np.all(np.isfinite(features)) or not np.all(np.isfinite(mean)) or np.any(~np.isfinite(scale)) or np.any(scale <= 0): raise RuntimeError(f"{STOP}:standardization")
    return (features-mean)/scale, mean, scale
def _apply_standardize(features: np.ndarray, mean: np.ndarray, scale: np.ndarray) -> np.ndarray:
    result = (features-mean)/scale
    if not np.all(np.isfinite(result)): raise RuntimeError(f"{STOP}:standardized evaluation")
    return result
def _ridge(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    design = np.c_[np.ones(len(x)), x]; penalty = np.diag(np.r_[0., np.full(x.shape[1], 1e-4)])
    return np.linalg.solve(design.T@design + penalty, design.T@y)
def _sigmoid(value: np.ndarray) -> np.ndarray: return 1/(1+np.exp(-np.clip(value, -50, 50)))
def _logistic(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    if np.min(y) == np.max(y): raise RuntimeError(f"{STOP}:degenerate spikes")
    design, beta = np.c_[np.ones(len(x)), x], np.zeros(x.shape[1]+1)
    penalty = np.diag(np.r_[0., np.full(x.shape[1], 1e-4)])
    for _ in range(50):
        p = _sigmoid(design@beta); weight = np.maximum(p*(1-p), 1e-12); gradient = design.T@(y-p)-penalty@beta
        try: step = np.linalg.solve(design.T@(weight[:,None]*design)+penalty, gradient)
        except np.linalg.LinAlgError as error: raise RuntimeError(f"{STOP}:irls solve") from error
        beta += step
        if float(np.max(np.abs(step))) <= 1e-8: return beta
    raise RuntimeError(f"{STOP}:irls convergence")


def _fit_models(data: list[tuple[np.ndarray, np.ndarray]]) -> dict[str, Any]:
    m0, m1 = np.vstack([item[0] for item in data]), np.vstack([item[1] for item in data]); target = np.concatenate([item[2] for item in data]); event = np.concatenate([item[3] for item in data])
    models = {}
    for name, features in (("M0", m0), ("M1", m1)):
        standardized, mean, scale = _fit_standardize(features); voltage, spike = _ridge(standardized, target), _logistic(standardized, event)
        models[name] = {"mean": mean, "scale": scale, "voltage": voltage, "spike": spike, "parameter_sha256": _array_hash(mean, scale, voltage, spike)}
    return models


def _json_models(models: dict[str, Any]) -> dict[str, Any]:
    return {name: {key: (value.tolist() if isinstance(value, np.ndarray) else value) for key, value in model.items()} for name, model in models.items()}


def _evaluate(models: dict[str, Any], voltage: np.ndarray, current: np.ndarray, sweep: int) -> dict[str, Any]:
    m0, m1, target, event = _rows(voltage, current, thin=False); output: dict[str, Any] = {"sweep": sweep, "origins": len(target), "target_sha256": _array_hash(target, event)}
    if sweep in NOISE and len(target) < 100000: raise RuntimeError(f"{STOP}:noise sample count:{sweep}")
    persistence = voltage[np.arange(HISTORY, len(voltage)-HORIZON)]; persistence_rmse = float(np.sqrt(np.mean((persistence-target)**2)))
    if not math.isfinite(persistence_rmse) or persistence_rmse <= 0: raise RuntimeError(f"{STOP}:persistence denominator")
    for name, features in (("M0", m0), ("M1", m1)):
        model, x = models[name], _apply_standardize(features, models[name]["mean"], models[name]["scale"]); design = np.c_[np.ones(len(x)), x]
        prediction, probability = design@model["voltage"], _sigmoid(design@model["spike"])
        rmse, brier, scale = float(np.sqrt(np.mean((prediction-target)**2))), float(np.mean((probability-event)**2)), float(np.std(target))
        if not all(math.isfinite(v) for v in (rmse,brier,scale)) or rmse <= 0 or brier <= 0 or scale <= 0 or np.any((probability < 0)|(probability > 1)): raise RuntimeError(f"{STOP}:metric finite")
        output[name] = {"rmse_mv": rmse, "nrmse": rmse/scale, "brier": brier, "brier_sum": float(np.sum((probability-event)**2)), "count": len(event), "prevalence": float(event.mean()), "persistence_improvement": 1-rmse/persistence_rmse}
    output["persistence_rmse_mv"] = persistence_rmse; output["relative_voltage_improvement"] = (output["M0"]["rmse_mv"]-output["M1"]["rmse_mv"])/output["M0"]["rmse_mv"]; output["relative_brier_improvement"] = (output["M0"]["brier"]-output["M1"]["brier"])/output["M0"]["brier"]
    return output


def decision(confirmation: list[dict[str, Any]]) -> str:
    if len(confirmation) != 2: return STOP
    try:
        improvement = [row["relative_voltage_improvement"] for row in confirmation]; pooled0 = sum(r["M0"]["brier_sum"] for r in confirmation)/sum(r["M0"]["count"] for r in confirmation); pooled1 = sum(r["M1"]["brier_sum"] for r in confirmation)/sum(r["M1"]["count"] for r in confirmation)
        degradation = [(r["M1"]["brier"]-r["M0"]["brier"])/r["M0"]["brier"] for r in confirmation]
        if all(x >= .02 for x in improvement) and pooled1 <= pooled0 and all(x <= .05 for x in degradation) and all(r["M1"]["rmse_mv"] < r["persistence_rmse_mv"] for r in confirmation): return "STAGE1_HISTORY_SUPPORTED"
        if all(abs(x) < .02 for x in improvement) and abs((pooled0-pooled1)/pooled0) <= .02: return "STAGE1_MARKOV_SUFFICIENT"
        return "STAGE1_HISTORY_TENSION"
    except (KeyError, ZeroDivisionError, TypeError): return STOP


def _verify_schema_receipt(raw: Path, pivot: Path) -> str:
    path = pivot / SCHEMA
    if not path.is_file(): raise RuntimeError(f"{STOP}:missing schema receipt")
    body, payload = path.read_bytes(), json.loads(path.read_bytes())
    if payload.get("raw") != _raw_identity(raw) or payload.get("confirmation_values_opened") is not False:
        raise RuntimeError(f"{STOP}:schema receipt")
    identity = payload.get("nwb_pipeline", {})
    if identity.get("nwb_version") != "NWB-1.0.5" or "IVSCC" not in identity.get("pipeline", "") or "1.0" not in identity.get("pipeline", "") or identity.get("specimen") != SPECIMEN or identity.get("session") != SESSION:
        raise RuntimeError(f"{STOP}:schema identity")
    sweeps = payload.get("sweeps")
    if not isinstance(sweeps, list) or [row.get("sweep") for row in sweeps] != list(FIT + DEV + CONFIRM): raise RuntimeError(f"{STOP}:schema population")
    for row in sweeps:
        sweep = row["sweep"]; expected = _schema_receipt_shape(sweep)
        if any(row.get(key) != value for key, value in expected.items()): raise RuntimeError(f"{STOP}:schema sweep receipt")
    return _sha(body)


def _schema_receipt_shape(sweep: int) -> dict[str, Any]:
    a, b = 150000, 20 * math.floor((150000 + EXPECTED_COUNTS[sweep]) / 20)
    return {"sweep": sweep, "response_path": _path(sweep,"response"), "stimulus_path": _path(sweep,"stimulus"), "units": ["Volts","Amps"], "conversions": [1.0,1.0], "rates": [RATE,RATE], "index_inclusive": [150000,150000+EXPECTED_COUNTS[sweep]-1], "aligned_half_open": [a,b], "bins": EXPECTED_BINS[sweep]}


def _verify_rows(rows: list[dict[str, Any]], models: dict[str, Any]) -> None:
    names = [row["sweep"] for row in rows]
    if len(names) != len(set(names)) or set(names) != set(FIT+DEV+CONFIRM) or set(FIT)&set(DEV+CONFIRM) or set(DEV)&set(CONFIRM): raise RuntimeError(f"{STOP}:split receipt")
    for name in ("M0", "M1"):
        if not models.get(name, {}).get("parameter_sha256"): raise RuntimeError(f"{STOP}:parameter receipt")
    for row in rows:
        if row["sweep"] in NOISE and row["origins"] < 100000: raise RuntimeError(f"{STOP}:noise receipt")
        if not row.get("target_sha256") or not all(math.isfinite(float(row[name][key])) for name in ("M0","M1") for key in ("rmse_mv","nrmse","brier","brier_sum","prevalence","persistence_improvement")): raise RuntimeError(f"{STOP}:row finite")
        receipt = row.get("data_receipt", {})
        expected = _schema_receipt_shape(row["sweep"])
        if any(receipt.get(key) != value for key, value in expected.items()) or not receipt.get("voltage_sha256") or not receipt.get("current_sha256"):
            raise RuntimeError(f"{STOP}:data receipt")
        m0,m1=row["M0"],row["M1"]
        if (m0["rmse_mv"] <= 0 or m0["brier"] <= 0 or row["persistence_rmse_mv"] <= 0
                or not np.isclose(row["relative_voltage_improvement"],(m0["rmse_mv"]-m1["rmse_mv"])/m0["rmse_mv"])
                or not np.isclose(row["relative_brier_improvement"],(m0["brier"]-m1["brier"])/m0["brier"])
                or not np.isclose(m0["brier_sum"],m0["brier"]*m0["count"]) or not np.isclose(m1["brier_sum"],m1["brier"]*m1["count"])):
            raise RuntimeError(f"{STOP}:metric receipt")


def seal(raw: Path, *, pivot: Path | None = None) -> dict[str, Any]:
    pivot = _pivot() if pivot is None else pivot; identity = _raw_identity(raw); schema_path = pivot/SCHEMA
    schema_digest = _verify_schema_receipt(raw, pivot)
    files = {}
    for relative in PREREG_FILES:
        path = pivot/relative
        if not path.is_file(): raise RuntimeError(f"{STOP}:missing prereg:{relative}")
        files[relative] = _sha(path.read_bytes())
    payload = {"schema":1,"raw":identity,"schema_receipt_sha256":schema_digest,"files":files,"confirmation_opened":False}
    return {"manifest_sha256":_atomic(pivot/MANIFEST,payload),**payload}


def verify_manifest(raw: Path, *, pivot: Path | None = None) -> dict[str, Any]:
    pivot = _pivot() if pivot is None else pivot; identity = _raw_identity(raw); path = pivot/MANIFEST
    if not path.is_file(): raise RuntimeError(f"{STOP}:missing manifest")
    payload=json.loads(path.read_bytes())
    schema_digest = _verify_schema_receipt(raw,pivot)
    if payload.get("confirmation_opened") is not False or payload.get("raw") != identity or payload.get("schema_receipt_sha256") != schema_digest or set(payload.get("files",{})) != set(PREREG_FILES): raise RuntimeError(f"{STOP}:manifest identity")
    for relative,digest in payload["files"].items():
        if _sha((pivot/relative).read_bytes()) != digest: raise RuntimeError(f"{STOP}:manifest mutation:{relative}")
    return payload


def _restore_models(serialized: Any) -> dict[str, Any]:
    if not isinstance(serialized, dict) or set(serialized) != {"M0", "M1"}: raise RuntimeError(f"{STOP}:result models")
    restored: dict[str, Any] = {}
    for name, dimension in (("M0", 2), ("M1", 11)):
        item = serialized[name]
        if not isinstance(item, dict) or set(item) != {"mean", "scale", "voltage", "spike", "parameter_sha256"}: raise RuntimeError(f"{STOP}:model fields")
        try: mean, scale, voltage, spike = (np.asarray(item[key], dtype=np.float64) for key in ("mean", "scale", "voltage", "spike"))
        except (TypeError, ValueError) as error: raise RuntimeError(f"{STOP}:model arrays") from error
        if (mean.shape != (dimension,) or scale.shape != (dimension,) or voltage.shape != (dimension+1,) or spike.shape != (dimension+1,)
                or not all(np.all(np.isfinite(value)) for value in (mean,scale,voltage,spike)) or np.any(scale <= 0)):
            raise RuntimeError(f"{STOP}:model dimensions")
        if _array_hash(mean,scale,voltage,spike) != item["parameter_sha256"]: raise RuntimeError(f"{STOP}:model parameter hash")
        restored[name] = {"mean":mean,"scale":scale,"voltage":voltage,"spike":spike,"parameter_sha256":item["parameter_sha256"]}
    return restored


def verify_result(raw: Path, *, pivot: Path | None = None) -> dict[str, Any]:
    pivot = _pivot() if pivot is None else pivot; manifest = verify_manifest(raw,pivot=pivot); path = pivot/RESULT
    if not path.is_file(): raise RuntimeError(f"{STOP}:missing result")
    body, payload = path.read_bytes(), json.loads(path.read_bytes())
    if (payload.get("schema") != 1 or payload.get("manifest_sha256") != _sha((pivot/MANIFEST).read_bytes())
            or payload.get("schema_receipt_sha256") != manifest.get("schema_receipt_sha256")
            or payload.get("raw_sha256") != RAW_SHA256 or payload.get("persistent_raw_bytes") != 0
            or payload.get("stage2_authorized") is not False or payload.get("manifest_sha256") != _sha((pivot/MANIFEST).read_bytes())):
        raise RuntimeError(f"{STOP}:result identity")
    if manifest.get("raw",{}).get("sha256") != payload["raw_sha256"]: raise RuntimeError(f"{STOP}:result manifest link")
    models = _restore_models(payload.get("models")); rows = payload.get("sweeps")
    if not isinstance(rows,list): raise RuntimeError(f"{STOP}:result sweeps")
    _verify_rows(rows,models)
    confirmation = [row for row in rows if row["sweep"] in CONFIRM]
    if payload.get("decision") != decision(confirmation): raise RuntimeError(f"{STOP}:result decision")
    return {"result_sha256": _sha(body), "result": payload}


def execute(raw: Path, *, pivot: Path | None = None) -> dict[str, Any]:
    pivot=_pivot() if pivot is None else pivot
    if (pivot/RESULT).exists(): raise RuntimeError(f"{STOP}:existing result")
    manifest=verify_manifest(raw,pivot=pivot); models: dict[str,Any]; rows=[]
    with h5py.File(raw,"r") as file:
        fit=[]
        for sweep in FIT:
            voltage,current,_=_load(file,sweep); fit.append(_rows(voltage,current,thin=True))
        models=_fit_models(fit)
        for sweep in DEV+CONFIRM:
            voltage,current,receipt=_load(file,sweep); row=_evaluate(models,voltage,current,sweep); row["data_receipt"]=receipt; rows.append(row)
        # Fit receipts are loaded after fitting only to preserve per-sweep audit without retaining raw arrays.
        for sweep in FIT:
            voltage,current,receipt=_load(file,sweep); row=_evaluate(models,voltage,current,sweep); row["data_receipt"]=receipt; rows.append(row)
    _verify_rows(rows,models); confirmation=[row for row in rows if row["sweep"] in CONFIRM]; status=decision(confirmation)
    payload={"schema":1,"manifest_sha256":_sha((pivot/MANIFEST).read_bytes()),"schema_receipt_sha256":manifest["schema_receipt_sha256"],"raw_sha256":RAW_SHA256,"models":_json_models(models),"sweeps":rows,"decision":status,"stage2_authorized":False,"persistent_raw_bytes":0}
    _atomic(pivot/RESULT,payload)
    verified = verify_result(raw,pivot=pivot)
    return {**payload,"result_sha256":verified["result_sha256"]}


def main() -> None:
    parser=argparse.ArgumentParser(); parser.add_argument("--nwb",required=True); parser.add_argument("--schema-smoke",action="store_true"); parser.add_argument("--seal",action="store_true"); parser.add_argument("--verify-result",action="store_true"); args=parser.parse_args(); raw=Path(args.nwb)
    if sum((args.schema_smoke,args.seal,args.verify_result)) > 1: raise RuntimeError(f"{STOP}:mode")
    if args.schema_smoke: print(json.dumps(schema_smoke(raw),sort_keys=True))
    elif args.seal: print(json.dumps(seal(raw),sort_keys=True))
    elif args.verify_result: print(json.dumps(verify_result(raw),sort_keys=True))
    else: print(json.dumps(execute(raw),sort_keys=True))
if __name__=="__main__": main()
