import importlib.util,json,sys
from pathlib import Path
import pytest
s=importlib.util.spec_from_file_location('h7',Path('examples/brain/ba_obs_hpc7_endpoint_recovery.py'));h=importlib.util.module_from_spec(s);sys.modules['h7']=h;s.loader.exec_module(h)
def paths(t):return t/'rp.json',t/'vpre.json',t/'vcomp.json',t/'rc.json'
def test_real_frozen_happy_path_and_no_predecessor_writes(tmp_path):
 rp,vpre,vcomp,rc=paths(tmp_path);before={p:h.sha(p) for p in (h.PP,h.W,h.R,h.PA,h.PE)};x=h.recovery(rp,vpre,vcomp,rc);assert x['status']=='CONTENT_VALIDATED_NOT_STANDALONE_AUTHORITY' and h.verify_authority(rp,vpre,vcomp,rc) and h.read(vcomp)['status']=='COMPLETE';assert before=={p:h.sha(p) for p in before}
def test_prior_refusal_and_validator_failures(tmp_path):
 rp,vpre,vcomp,rc=paths(tmp_path);rp.write_text('{}')
 with pytest.raises(ValueError):h.recovery(rp,vpre,vcomp,rc)
 rp.unlink()
 with pytest.MonkeyPatch.context() as m:
  m.setattr(h,'validator',lambda:lambda *a,**k:False)
  with pytest.raises(ValueError):h.recovery(rp,vpre,vcomp,rc)
 assert h.read(rp)['status']=='RECOVERY_STOP' and not rc.exists()
def test_terminal_and_execution_drift_rejected(tmp_path,monkeypatch):
 rp,vpre,vcomp,rc=paths(tmp_path);orig=h.read
 def bad(p):
  x=orig(p)
  if Path(p)==h.PP:x['error']='forged'
  return x
 monkeypatch.setattr(h,'read',bad)
 with pytest.raises(ValueError):h.recovery(rp,vpre,vcomp,rc)
def test_no_producer_or_loader_or_http(tmp_path,monkeypatch):
 rp,vpre,vcomp,rc=paths(tmp_path)
 def forbidden(*a,**k):raise AssertionError('forbidden')
 monkeypatch.setattr(h,'validator',forbidden)
 with pytest.raises(AssertionError):h.recovery(rp,vpre,vcomp,rc)
 assert h.read(rp)['status']=='RECOVERY_STOP' and not rc.exists()

def test_orphan_receipt_never_authority(tmp_path):
 rp,vpre,vcomp,rc=paths(tmp_path);h.recovery(rp,vpre,vcomp,rc);rp.unlink()
 assert not h.verify_authority(rp,vpre,vcomp,rc)
