"""Pure mechanical fixtures for the read-only recovery validator."""
from __future__ import annotations
import hashlib, importlib.util
from pathlib import Path
import numpy as np
import pytest

PATH=Path(__file__).with_name("validate_stage1_armijo_result.py");spec=importlib.util.spec_from_file_location("recovery_test",PATH);assert spec and spec.loader;recovery=importlib.util.module_from_spec(spec);spec.loader.exec_module(recovery)
class Retry:
 @staticmethod
 def _array_hash(*items):return hashlib.sha256(b"".join(np.ascontiguousarray(x).tobytes() for x in items)).hexdigest()
def _item(name:str)->dict:
 arrays={"mean":np.array([-1.25,2.5],dtype=np.float32 if name=="M0" else np.float64),"scale":np.array([.5,3.],dtype=np.float32 if name=="M0" else np.float64),"voltage":np.array([1.,2.,3.],dtype=np.float64),"spike":np.array([4.,5.,6.],dtype=np.float64)}
 return {**{k:v.tolist() for k,v in arrays.items()},"parameter_sha256":Retry._array_hash(*(arrays[k] for k in ("mean","scale","voltage","spike")))}
def test_historical_m0_dtype_envelope_recovers_legacy_hash() -> None:
 item=_item("M0");restored=recovery._legacy_model(Retry,"M0",item)
 assert restored["mean"].dtype==np.float32 and restored["scale"].dtype==np.float32 and restored["voltage"].dtype==np.float64
 # Generic JSON float64 reload is intentionally a different byte hash.
 generic=Retry._array_hash(*(np.asarray(item[k],dtype=np.float64) for k in ("mean","scale","voltage","spike")))
 assert generic!=item["parameter_sha256"]
def test_dtype_recovery_rejects_parameter_mutation() -> None:
 item=_item("M0");item["mean"][0]+=1e-3
 with pytest.raises(RuntimeError,match="legacy parameter hash"):recovery._legacy_model(Retry,"M0",item)
def test_row_comparison_rejects_metric_and_receipt_mutation() -> None:
 row={"sweep":1,"origins":2,"target_sha256":"t","persistence_rmse_mv":1.,"relative_voltage_improvement":.1,"relative_brier_improvement":.1,"M0":{"rmse_mv":1.,"nrmse":1.,"brier":.2,"brier_sum":.4,"count":2,"prevalence":.1,"persistence_improvement":.1},"M1":{"rmse_mv":.9,"nrmse":.9,"brier":.18,"brier_sum":.36,"count":2,"prevalence":.1,"persistence_improvement":.2},"data_receipt":{k:v for k,v in {"sweep":1,"response_path":"r","stimulus_path":"i","units":["Volts"],"conversions":[1.],"rates":[1.],"index_inclusive":[0,1],"aligned_half_open":[0,2],"bins":1,"voltage_sha256":"v","current_sha256":"c"}.items()}}
 recovery._compare_row(row,row.copy());bad={**row,"M1":{**row["M1"],"brier":.19}}
 with pytest.raises(RuntimeError,match="metric"):recovery._compare_row(row,bad)
