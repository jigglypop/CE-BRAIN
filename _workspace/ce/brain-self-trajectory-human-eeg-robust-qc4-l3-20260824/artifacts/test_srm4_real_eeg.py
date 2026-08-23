import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
import numpy as np

HERE=Path(__file__).with_name("srm4_real_eeg.py")
spec=importlib.util.spec_from_file_location("srm4",HERE); s=importlib.util.module_from_spec(spec); spec.loader.exec_module(s)
ROOT=HERE.parents[4]
PRE=ROOT/"_workspace/ce/brain-self-trajectory-human-eeg-channel-qc3-l3-20260824/artifacts/b1-allocation.json"

def test_allocation_is_sealed_and_balanced():
    a=s.allocation(PRE); assert a["counts"]=={"R0-SMALL":10,"R1-MEDIUM":20,"R2-LARGE":70}; assert a["session_counts"]["ses-01"]["R2-LARGE"]==42
    assert a["signal_accessed"] is False and a["network_accessed"] is False and len(a["trials"])==100
    assert len(a["r2_all_word_coverage"])==8 and a["contract_sha256"]==s.CONTRACT_SHA256 and a["manifest_sha256"]==s.MANIFEST_SHA256
def test_transform_and_area_are_finite():
    rng=np.random.default_rng(2); x=rng.normal(size=(4,126,63)); t=s.fit_transform(x); z=s.project(x,t)
    assert z.shape==(4,126,2) and np.isfinite([s.area(v) for v in z]).all() and t["d_eff"]>0
def test_area_is_all_increment_pairs_not_adjacent_only():
    # increments (1,0), (0,1), (1,0): cross products are 1,0,-1 -> area 0.
    z=np.zeros((126,2)); z[1]=[1,0]; z[2]=[1,1]; z[3]=[2,1]
    z[4:]=z[3]
    assert s.area(z)==0.0
    z=np.zeros((126,2)); z[1]=[1,0]; z[2]=[1,1]; z[3]=[1,2]; z[4:]=z[3]
    assert s.area(z)==1.0
def test_nonfinite_and_flat_fail_closed():
    x=np.ones((2,126,63))
    try: s.fit_transform(x); assert False
    except s.Invalid: pass
def test_post_car_channelwise_affine_preserves_bounded_gram():
    # This is explicitly post-CAR algebra; arbitrary pre-CAR gains are not claimed.
    rng=np.random.default_rng(9); x=rng.normal(size=(3,126,63)); x-=x.mean(axis=2,keepdims=True)
    gain=rng.choice([-1.,1.],size=63)*rng.uniform(.2,3.,size=63); off=rng.normal(size=63)
    def bounded(a):
        m=np.median(a.reshape(-1,63),0); q=1.4826*np.median(np.abs(a.reshape(-1,63)-m),0)
        return 4*np.tanh(((a-m)/q)/4)
    u=bounded(x).reshape(-1,63); v=bounded(x*gain+off).reshape(-1,63)
    assert np.allclose(u@u.T,v@v.T,rtol=1e-10,atol=1e-10)
    x[0,0,0]=np.nan
    try: s.fit_transform(x); assert False
    except s.Invalid: pass
def test_synthetic_contract():
    r=s.synthetic(17); assert r["status"]=="P0_SYNTHETIC_PASS"; assert r["markov"]["gain"]<=.01; assert r["injected"]["gain"]>=.05
    assert len(r["injected"]["controls"])==20 and all(x["oriented_minus_shuffle"]<=-.01 for x in r["injected"]["controls"])
def test_future_target_is_not_in_features():
    z=np.arange(252,dtype=float).reshape(126,2); f=s.features(z); changed=z.copy(); changed[101:125]+=1e9
    assert np.array_equal(f,s.features(changed))
    changed[125]+=1e9
    assert np.array_equal(f,s.features(changed))
    assert not np.array_equal(z[125]-z[100],changed[125]-changed[100])

def _brainlike_windows():
    rng=np.random.default_rng(31); mix=rng.normal(size=(2,63)); t=np.arange(126,dtype=float); windows=[]
    for session in range(2):
        for pair in range(5):
            for condition in range(2):
                a=.004*(pair+1)+.001*condition; b=-.003*(6-pair)+.0005*session
                latent=np.c_[a*t+.03*np.sin(t/13+pair),b*t+.02*np.cos(t/11+condition)]
                windows.append(latent@mix+rng.normal(0,1e-4,(126,63)))
    return windows

class _FakeReader:
    def __init__(self, windows, fail_at=None): self.windows=windows; self.calls=0; self.fail_at=fail_at
    def recording_for(self, meta, subject, session): return {"eeg_url":"mock://"+session,"content_length":999,"etag":"mock"}
    def anchor_to_sample(self, anchor): return int(round(anchor*5000))
    def byte_geometry(self, anchor): return 0,0,anchor,anchor+1
    def fetch_exact_range(self, url, start, end, length, etag):
        self.calls+=1
        if self.fail_at is not None and self.calls==self.fail_at: raise OSError("synthetic fetch failure")
        i=self.calls-1
        return i,{"status":206,"url":url,"content_range":f"bytes {start}-{end}/{length}","etag":etag,"sha256":f"mock-{i}"}
    def parse_multiplexed_float32(self, raw): return raw
    def causal_filter_and_decimate(self, parsed): return self.windows[parsed]

def _manifest_and_allocation():
    alloc=s.allocation(PRE); return {"trials":[{k:v for k,v in r.items() if k not in ("old_split","new_split","allocation_key")} for r in alloc["trials"]]},alloc

def test_r0_loader_opens_exactly_twenty_r0_windows_and_truthfully_tracks_failure():
    manifest,alloc=_manifest_and_allocation(); reader=_FakeReader(_brainlike_windows()); access=s.new_access_state()
    pairs=s.r0_rows(reader,manifest,{},alloc,access)
    assert len(pairs)==10 and reader.calls==20 and len(access["completed_requests"])==20
    assert access["network_accessed"] and access["signal_accessed"]
    reader=_FakeReader(_brainlike_windows(),fail_at=2); access=s.new_access_state()
    try: s.r0_rows(reader,manifest,{},alloc,access); assert False
    except OSError: pass
    assert access["network_accessed"] and access["signal_accessed"] and len(access["completed_requests"])==1

def test_r0_fit_is_train_only_and_baseline_beats_persistence():
    manifest,alloc=_manifest_and_allocation(); reader=_FakeReader(_brainlike_windows()); pairs=s.r0_rows(reader,manifest,{},alloc)
    train=[p for p in pairs if p["session"]=="ses-01"]; test=[p for p in pairs if p["session"]=="ses-02"]
    tr,loss,diag=s.r0_fit(train,test)
    assert loss["task"]["B"]>0 and diag["training_rows"]==10 and diag["sample_guard_margin"]>=0
    changed=[]
    for p in test:
        q={**p,"windows":[]}
        for item in p["windows"]:
            w=item["window"].copy(); w[101:126]+=1e4
            q["windows"].append({**item,"window":w})
        changed.append(q)
    tr2,_,_=s.r0_fit(train,changed)
    for key in ("median","scale","mean","eig","basis"): assert np.array_equal(tr[key],tr2[key])

def _write_provenance(tmp_path):
    manifest,alloc=_manifest_and_allocation(); paths={}
    for name,obj in (("contract",{}),("manifest",manifest),("meta",{}),("self1",{}),("self3",{}),("alloc",alloc)):
        p=tmp_path/(name+".json"); p.write_text(json.dumps(obj),encoding="utf-8"); paths[name]=p
    return paths

def _patch_hashes(monkeypatch,paths):
    expected={paths["contract"]:s.CONTRACT_SHA256,paths["manifest"]:s.MANIFEST_SHA256,paths["meta"]:s.SOURCE_A0_SHA256,
              paths["self1"]:s.SELF1_SHA256,paths["self3"]:s.SELF3_ALLOCATION_SHA256,paths["alloc"]:s.SRM4_ALLOCATION_SHA256}
    original=s.sha
    monkeypatch.setattr(s,"sha",lambda path: expected.get(Path(path),original(path)))

def test_r0_safe_pass_failure_flags_and_seals(monkeypatch,tmp_path):
    paths=_write_provenance(tmp_path); _patch_hashes(monkeypatch,paths)
    reader=_FakeReader(_brainlike_windows()); monkeypatch.setattr(s,"load_reader",lambda path:reader)
    result=s.r0_safe(paths["contract"],paths["manifest"],paths["meta"],paths["self1"],paths["self3"],paths["alloc"])
    assert result["status"]=="R0_SMALL_PASS" and len(result["windows"])==20
    assert result["scientific_endpoint_opened"] and result["model_outcome_computed"]
    assert result["path_area_opened"] is False and result["ordered_history_gain_opened"] is False and result["word_effect_opened"] is False
    assert result["unopened_splits"]==["R1-MEDIUM","R2-LARGE","C1","C2","C3"]
    reader=_FakeReader(_brainlike_windows(),fail_at=2); monkeypatch.setattr(s,"load_reader",lambda path:reader)
    failed=s.r0_safe(paths["contract"],paths["manifest"],paths["meta"],paths["self1"],paths["self3"],paths["alloc"])
    assert failed["status"]=="APPARATUS_INVALID_OR_BASELINE_UNRESOLVED" and failed["network_accessed"] and failed["signal_accessed"]
    assert len(failed["windows"])==1 and failed["scientific_endpoint_opened"] is False

def test_r0_tampered_provenance_and_offline_preflight_never_fetch(monkeypatch,tmp_path):
    paths=_write_provenance(tmp_path); called={"reader":0}
    monkeypatch.setattr(s,"load_reader",lambda path:called.__setitem__("reader",called["reader"]+1))
    result=s.r0_safe(paths["contract"],paths["manifest"],paths["meta"],paths["self1"],paths["self3"],paths["alloc"])
    assert result["status"]=="APPARATUS_INVALID_PROVENANCE" and not result["network_accessed"] and called["reader"]==0
    original=s.sha; monkeypatch.setattr(s,"sha",lambda path:s.CONTRACT_SHA256 if Path(path)==paths["contract"] else original(path))
    pre=s.preflight("R0-SMALL",paths["contract"])
    assert pre["network_accessed"] is False and pre["unopened_splits"]==["R1-MEDIUM","R2-LARGE","C1","C2","C3"]
