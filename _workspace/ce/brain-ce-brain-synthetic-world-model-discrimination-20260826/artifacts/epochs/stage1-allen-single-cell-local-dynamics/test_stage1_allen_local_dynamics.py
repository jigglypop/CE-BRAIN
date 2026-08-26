"""Mechanical fixture tests only; no real Allen NWB is opened or sealed."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import h5py
import numpy as np
import pytest


MODULE = Path(__file__).with_name("stage1_allen_local_dynamics.py")
SPEC = importlib.util.spec_from_file_location("stage1_allen_test", MODULE)
assert SPEC is not None and SPEC.loader is not None
stage = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(stage)


def _metadata_fixture(path: Path, sweep: int = 60) -> None:
    with h5py.File(path, "w") as file:
        raw_length = 150000 + stage.EXPECTED_COUNTS[sweep]
        response = file.create_dataset(stage._path(sweep, "response"), shape=(raw_length,), dtype="f8", chunks=True)
        stimulus = file.create_dataset(stage._path(sweep, "stimulus"), shape=(raw_length,), dtype="f8", chunks=True)
        response.attrs["unit"], stimulus.attrs["unit"] = "Volts", "Amps"
        response.attrs["conversion"], stimulus.attrs["conversion"] = 1.0, 1.0
        response.parent.create_dataset("starting_time", data=0.).attrs["rate"] = stage.RATE
        stimulus.parent.create_dataset("starting_time", data=0.).attrs["rate"] = stage.RATE
        for kind in ("response", "stimulus"):
            epoch = file.require_group(stage._epoch(sweep, kind)); epoch.create_dataset("idx_start", data=150000); epoch.create_dataset("count", data=stage.EXPECTED_COUNTS[sweep])


def _row(improvement: float, brier0: float = .2, brier1: float = .2, persistence: float = 4.) -> dict:
    m0 = 2.; m1 = m0*(1-improvement)
    return {"relative_voltage_improvement": improvement, "persistence_rmse_mv": persistence,
            "M0": {"rmse_mv":m0,"brier":brier0,"brier_sum":brier0*100,"count":100},
            "M1": {"rmse_mv":m1,"brier":brier1,"brier_sum":brier1*100,"count":100}}


def test_metadata_schema_is_value_guarded_and_unit_rate_fail_closed(tmp_path: Path) -> None:
    fixture = tmp_path / "compact.nwb"; _metadata_fixture(fixture)
    with h5py.File(fixture, "r") as file:
        receipt = stage._schema_sweep(file, 60)
        assert receipt["bins"] == 242700 and receipt["aligned_half_open"] == [150000, 5004000]
    with h5py.File(fixture, "r+") as file:
        file[stage._path(60,"response")].attrs["unit"]="mV"
    with h5py.File(fixture,"r") as file:
        with pytest.raises(RuntimeError,match="unit/rate"):
            stage._schema_sweep(file,60)


def test_block_indices_history_and_fit_fail_closed() -> None:
    response=np.arange(80.,dtype=float)*1e-3; stimulus=np.arange(80.,dtype=float)*1e-12
    voltage,current=stage._block(response,stimulus,0,80)
    assert np.allclose(voltage,[9.5,29.5,49.5,69.5]) and np.allclose(current,[9.5,29.5,49.5,69.5])
    values=np.linspace(-70,20,530); current=np.linspace(-10,10,530)
    m0,m1,target,event=stage._rows(values,current,thin=False)
    assert len(target)==20 and target[0]==values[510] and m0.shape[1]==2 and m1.shape[1]==11
    with pytest.raises(RuntimeError,match="history boundary"):
        stage._rows(values[:510],current[:510],thin=False)
    with pytest.raises(RuntimeError,match="degenerate spikes"):
        stage._logistic(np.ones((10,2)),np.zeros(10))


def test_decision_statuses_are_frozen() -> None:
    assert stage.decision([_row(.03,.2,.19),_row(.02,.2,.2)])=="STAGE1_HISTORY_SUPPORTED"
    assert stage.decision([_row(.01,.2,.199),_row(.0,.2,.2)])=="STAGE1_MARKOV_SUFFICIENT"
    assert stage.decision([_row(.03,.2,.3),_row(.01,.2,.2)])=="STAGE1_HISTORY_TENSION"
    assert stage.decision([])==stage.STOP


def test_raw_hash_and_manifest_mutation_fail_closed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    raw=tmp_path/"fixture.nwb"; raw.write_bytes(b"fixture")
    monkeypatch.setattr(stage,"FILENAME","fixture.nwb"); monkeypatch.setattr(stage,"RAW_BYTES",7); monkeypatch.setattr(stage,"RAW_SHA256",stage._sha(b"fixture"))
    identity=stage._raw_identity(raw); assert identity["sha256"]==stage._sha(b"fixture")
    raw.write_bytes(b"changed")
    with pytest.raises(RuntimeError,match="raw identity"): stage._raw_identity(raw)
    raw.write_bytes(b"fixture")
    for relative in stage.PREREG_FILES:
        target=tmp_path/relative; target.parent.mkdir(parents=True,exist_ok=True); target.write_text("fixture",encoding="utf-8")
    schema = {"schema":1,"raw":stage._raw_identity(raw),"confirmation_values_opened":False,
              "nwb_pipeline":{"nwb_version":"NWB-1.0.5","pipeline":"IVSCC 1.0","specimen":stage.SPECIMEN,"session":stage.SESSION},
              "sweeps":[stage._schema_receipt_shape(sweep) for sweep in stage.FIT+stage.DEV+stage.CONFIRM]}
    (tmp_path/stage.SCHEMA).write_text(json.dumps(schema),encoding="utf-8")
    stage.seal(raw,pivot=tmp_path)
    stage.verify_manifest(raw,pivot=tmp_path)
    schema["sweeps"][0]["rates"]=[1,1]
    (tmp_path/stage.SCHEMA).write_text(json.dumps(schema),encoding="utf-8")
    with pytest.raises(RuntimeError,match="schema sweep receipt"): stage.verify_manifest(raw,pivot=tmp_path)
    schema["sweeps"][0]["rates"]=[stage.RATE,stage.RATE]
    (tmp_path/stage.SCHEMA).write_text(json.dumps(schema),encoding="utf-8")
    (tmp_path/"20-hypotheses.md").write_text("mutation",encoding="utf-8")
    with pytest.raises(RuntimeError,match="manifest mutation"): stage.verify_manifest(raw,pivot=tmp_path)


def test_json_model_boundary_and_schema_receipt_fail_closed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    raw=tmp_path/"fixture.nwb"; raw.write_bytes(b"fixture")
    monkeypatch.setattr(stage,"FILENAME","fixture.nwb"); monkeypatch.setattr(stage,"RAW_BYTES",7); monkeypatch.setattr(stage,"RAW_SHA256",stage._sha(b"fixture"))
    numeric={"M0":{"mean":np.array([1.,2.]),"scale":np.array([2.,3.]),"voltage":np.array([.1,.2,.3]),"spike":np.array([.4,.5,.6]),"parameter_sha256":"p"}}
    safe=stage._json_models(numeric); digest=stage._atomic(tmp_path/"result.json",{"models":safe})
    assert digest and isinstance(json.loads((tmp_path/"result.json").read_text())["models"]["M0"]["mean"],list)
    bad={"schema":1,"raw":stage._raw_identity(raw),"confirmation_values_opened":False,"nwb_pipeline":{},"sweeps":[]}
    (tmp_path/stage.SCHEMA).write_text(json.dumps(bad),encoding="utf-8")
    with pytest.raises(RuntimeError,match="schema identity"):
        stage._verify_schema_receipt(raw,tmp_path)


def test_result_row_receipts_bind_metrics_and_sweep_identity() -> None:
    models={"M0":{"parameter_sha256":"m0"},"M1":{"parameter_sha256":"m1"}}
    rows=[]
    for sweep in stage.FIT+stage.DEV+stage.CONFIRM:
        receipt={**stage._schema_receipt_shape(sweep),"voltage_sha256":f"v{sweep}","current_sha256":f"i{sweep}"}
        m0={"rmse_mv":2.,"nrmse":1.,"brier":.2,"brier_sum":20.,"count":100,"prevalence":.1,"persistence_improvement":.1}
        m1={"rmse_mv":1.9,"nrmse":.95,"brier":.19,"brier_sum":19.,"count":100,"prevalence":.1,"persistence_improvement":.15}
        rows.append({"sweep":sweep,"origins":100000 if sweep in stage.NOISE else 10,"target_sha256":f"t{sweep}","M0":m0,"M1":m1,"persistence_rmse_mv":3.,"relative_voltage_improvement":.05,"relative_brier_improvement":.05,"data_receipt":receipt})
    stage._verify_rows(rows,models)
    rows[0]["data_receipt"]["units"]=["mV","pA"]
    with pytest.raises(RuntimeError,match="data receipt"):
        stage._verify_rows(rows,models)


def test_verify_result_reloads_and_rejects_model_decision_and_manifest_mutations(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    raw=tmp_path/"fixture.nwb"; raw.write_bytes(b"fixture")
    monkeypatch.setattr(stage,"FILENAME","fixture.nwb"); monkeypatch.setattr(stage,"RAW_BYTES",7); monkeypatch.setattr(stage,"RAW_SHA256",stage._sha(b"fixture"))
    for relative in stage.PREREG_FILES:
        target=tmp_path/relative; target.parent.mkdir(parents=True,exist_ok=True); target.write_text("fixture",encoding="utf-8")
    schema={"schema":1,"raw":stage._raw_identity(raw),"confirmation_values_opened":False,
            "nwb_pipeline":{"nwb_version":"NWB-1.0.5","pipeline":"IVSCC 1.0","specimen":stage.SPECIMEN,"session":stage.SESSION},
            "sweeps":[stage._schema_receipt_shape(sweep) for sweep in stage.FIT+stage.DEV+stage.CONFIRM]}
    (tmp_path/stage.SCHEMA).write_text(json.dumps(schema),encoding="utf-8"); stage.seal(raw,pivot=tmp_path)
    models={}
    for name,dimension in (("M0",2),("M1",11)):
        mean=np.zeros(dimension); scale=np.ones(dimension); voltage=np.zeros(dimension+1); spike=np.zeros(dimension+1)
        models[name]={"mean":mean.tolist(),"scale":scale.tolist(),"voltage":voltage.tolist(),"spike":spike.tolist(),"parameter_sha256":stage._array_hash(mean,scale,voltage,spike)}
    rows=[]
    for sweep in stage.FIT+stage.DEV+stage.CONFIRM:
        receipt={**stage._schema_receipt_shape(sweep),"voltage_sha256":f"v{sweep}","current_sha256":f"i{sweep}"}
        m0={"rmse_mv":2.,"nrmse":1.,"brier":.2,"brier_sum":20.,"count":100,"prevalence":.1,"persistence_improvement":.1}; m1={"rmse_mv":1.9,"nrmse":.95,"brier":.19,"brier_sum":19.,"count":100,"prevalence":.1,"persistence_improvement":.15}
        rows.append({"sweep":sweep,"origins":100000 if sweep in stage.NOISE else 10,"target_sha256":f"t{sweep}","M0":m0,"M1":m1,"persistence_rmse_mv":3.,"relative_voltage_improvement":.05,"relative_brier_improvement":.05,"data_receipt":receipt})
    manifest=json.loads((tmp_path/stage.MANIFEST).read_text(encoding="utf-8"))
    base={"schema":1,"manifest_sha256":stage._sha((tmp_path/stage.MANIFEST).read_bytes()),"schema_receipt_sha256":manifest["schema_receipt_sha256"],"raw_sha256":stage.RAW_SHA256,"models":models,"sweeps":rows,"decision":"STAGE1_HISTORY_SUPPORTED","stage2_authorized":False,"persistent_raw_bytes":0}
    stage._atomic(tmp_path/stage.RESULT,base); assert stage.verify_result(raw,pivot=tmp_path)["result_sha256"]
    broken=json.loads(json.dumps(base)); broken["models"]["M0"]["parameter_sha256"]="bad"; stage._atomic(tmp_path/stage.RESULT,broken)
    with pytest.raises(RuntimeError,match="model parameter hash"): stage.verify_result(raw,pivot=tmp_path)
    broken=json.loads(json.dumps(base)); broken["decision"]="STAGE1_HISTORY_TENSION"; stage._atomic(tmp_path/stage.RESULT,broken)
    with pytest.raises(RuntimeError,match="result decision"): stage.verify_result(raw,pivot=tmp_path)
    broken=json.loads(json.dumps(base)); broken["manifest_sha256"]="bad"; stage._atomic(tmp_path/stage.RESULT,broken)
    with pytest.raises(RuntimeError,match="result identity"): stage.verify_result(raw,pivot=tmp_path)


def test_schema_mode_confirmation_guard_and_index_corruption(tmp_path: Path) -> None:
    fixture=tmp_path/"compact.nwb"; _metadata_fixture(fixture)
    with h5py.File(fixture,"r+") as file:
        file[stage._epoch(60,"response")+"/count"][...]=1
    with h5py.File(fixture,"r") as file:
        with pytest.raises(RuntimeError,match="index_range"):
            stage._schema_sweep(file,60)
    # Schema inspection uses shape/attrs/epoch metadata only; this fixture never writes values.
