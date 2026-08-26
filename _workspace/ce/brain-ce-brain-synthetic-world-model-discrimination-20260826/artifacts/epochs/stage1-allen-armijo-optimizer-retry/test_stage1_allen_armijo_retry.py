"""Mechanical optimizer fixtures only; no Allen raw data is opened."""
from __future__ import annotations
import importlib.util
import json
from pathlib import Path
import numpy as np
import pytest

PATH=Path(__file__).with_name("stage1_allen_armijo_retry.py");spec=importlib.util.spec_from_file_location("armijo_test",PATH);assert spec and spec.loader;retry=importlib.util.module_from_spec(spec);spec.loader.exec_module(retry)

def _full_newton_worsens(x:np.ndarray,y:np.ndarray)->bool:
 d=np.c_[np.ones(len(x)),x];b=np.zeros(d.shape[1]);pen=np.diag(np.r_[0.,np.full(x.shape[1],retry.LAMBDA)])
 for _ in range(20):
  p=1/(1+np.exp(-np.clip(d@b,-50,50)));w=np.maximum(p*(1-p),1e-12);g=d.T@(y-p)-pen@b;step=np.linalg.solve(d.T@(w[:,None]*d)+pen,g);before=retry.objective(d,y,b);after=retry.objective(d,y,b+step)
  if after<before:return True
  b+=step
 return False

def test_armijo_monotone_converges_on_quasi_separable_fixture() -> None:
 rng=np.random.default_rng(4);x=np.c_[np.r_[rng.normal(-1,0.1,450),rng.normal(1,0.1,6)],np.r_[rng.normal(0,1,450),rng.normal(0,1,6)]];y=np.r_[np.zeros(450),np.ones(6)]
 assert _full_newton_worsens(x,y)
 # The fixture is deliberately strongly imbalanced; Armijo must retain a finite monotone optimum.
 beta,receipt=retry.armijo_logistic(x,y);assert np.all(np.isfinite(beta));assert receipt["final_gradient_inf"]<=1e-8;assert retry.MIN_ALPHA<=receipt["minimum_accepted_alpha"]<=1

def test_objective_and_kill_guards() -> None:
 x=np.ones((10,2));y=np.zeros(10)
 with pytest.raises(RuntimeError,match="degenerate spikes"):retry.armijo_logistic(x,y)
 with pytest.raises(RuntimeError,match="armijo input"):
  # A nonfinite feature stops before it can reach objective evaluation.
  retry.armijo_logistic(np.array([[0.,np.nan],[1.,0.]]),np.array([0.,1.]))
 assert retry.objective(np.eye(2),np.array([0.,1.]),np.zeros(2))<0

def test_stationary_start_converges_at_zero_iterations() -> None:
 x=np.zeros((20,3));y=np.r_[np.zeros(10),np.ones(10)]
 beta,receipt=retry.armijo_logistic(x,y)
 assert np.array_equal(beta,np.zeros(4));assert receipt["iterations"]==0;assert receipt["final_gradient_inf"]==0.;assert receipt["final_step_inf"]==0.

def test_optimizer_receipt_requires_gradient_and_local_prereg_population() -> None:
 assert set(retry.PREREG_FILES)=={"00-retry-contract.md","10-optimizer-routes.md","20-audit.md","21-preexecution-validation.md","stage1_allen_armijo_retry.py","test_stage1_allen_armijo_retry.py"}
 bad={"M0":{"iterations":1,"final_objective":0.,"final_step_inf":0.,"minimum_accepted_alpha":1.},"M1":{"iterations":1,"final_objective":0.,"final_step_inf":0.,"minimum_accepted_alpha":1.}}
 assert "final_gradient_inf" not in bad["M0"]
 good={"iterations":0,"final_objective":0.,"final_gradient_inf":0.,"final_step_inf":0.,"minimum_accepted_alpha":1.}
 retry._verify_optimizer_receipts({"M0":good,"M1":dict(good)})
 for broken in ({k:v for k,v in good.items() if k!="final_gradient_inf"},{**good,"final_gradient_inf":1e-6},{**good,"minimum_accepted_alpha":retry.MIN_ALPHA/2}):
  with pytest.raises(RuntimeError,match="optimizer receipt"):retry._verify_optimizer_receipts({"M0":broken,"M1":dict(good)})

def test_temp_verify_result_rejects_local_link_decision_model_and_receipt(tmp_path:Path,monkeypatch:pytest.MonkeyPatch)->None:
 class Parent:
  SCHEMA="stage1-schema-receipt.json";RAW_SHA256="raw"
  def _restore_models(self,x):
   if x!={"ok":True}:raise RuntimeError("model hash")
   return x
  def _verify_rows(self,rows,models):
   if rows!=[]:raise RuntimeError("rows")
  def decision(self,rows):return "DECISION"
 fake=Parent();monkeypatch.setattr(retry,"_parent",lambda raw:fake)
 # The parent schema file must exist because the local manifest binds its exact hash.
 root=retry._parent_pivot();schema=root/fake.SCHEMA;schema_digest=retry._sha(schema.read_bytes())
 for rel in retry.PREREG_FILES:
  p=tmp_path/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_text("fixture",encoding="utf-8")
 files={rel:retry._sha((tmp_path/rel).read_bytes()) for rel in retry.PREREG_FILES}
 manifest={"predecessor_manifest_sha256":retry.PREDECESSOR_MANIFEST,"predecessor_source_sha256":retry.PREDECESSOR_SOURCE,"schema_receipt_sha256":schema_digest,"raw_sha256":"raw","confirmation_opened":False,"files":files}
 retry._atomic(tmp_path/retry.MANIFEST,manifest)
 base={"manifest_sha256":retry._sha((tmp_path/retry.MANIFEST).read_bytes()),"predecessor_manifest_sha256":retry.PREDECESSOR_MANIFEST,"raw_sha256":"raw","persistent_raw_bytes":0,"stage2_authorized":False,"models":{"ok":True},"sweeps":[],"decision":"DECISION","optimizer_receipts":{"M0":{"iterations":0,"final_objective":0.,"final_gradient_inf":0.,"final_step_inf":0.,"minimum_accepted_alpha":1.},"M1":{"iterations":0,"final_objective":0.,"final_gradient_inf":0.,"final_step_inf":0.,"minimum_accepted_alpha":1.}}}
 retry._atomic(tmp_path/retry.RESULT,base);assert retry.verify_result(Path("fake"),pivot=tmp_path)["result_sha256"]
 for key,value,expected in (("manifest_sha256","bad","result identity"),("decision","bad","decision"),("models",{},"model hash")):
  x=json.loads(json.dumps(base));x[key]=value;retry._atomic(tmp_path/retry.RESULT,x)
  with pytest.raises(RuntimeError,match=expected):retry.verify_result(Path("fake"),pivot=tmp_path)
 x=json.loads(json.dumps(base));del x["optimizer_receipts"]["M0"]["final_gradient_inf"];retry._atomic(tmp_path/retry.RESULT,x)
 with pytest.raises(RuntimeError,match="optimizer receipt"):retry.verify_result(Path("fake"),pivot=tmp_path)
