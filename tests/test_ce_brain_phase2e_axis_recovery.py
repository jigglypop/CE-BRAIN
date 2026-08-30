from __future__ import annotations
import importlib.util, sys
from pathlib import Path
import numpy as np

P=Path(__file__).parents[1]/"examples"/"brain"/"ce_brain_phase2e_axis_recovery.py"
S=importlib.util.spec_from_file_location("phase2e",P); assert S and S.loader
m=importlib.util.module_from_spec(S);sys.modules[S.name]=m;S.loader.exec_module(m)

def test_predictions_recover_rank_one_axis():
    d=np.array([[1.,0.],[2.,0.],[3.,0.]])
    p=m.predictions(d)
    assert np.allclose(p["I"],d) and np.allclose(p["K"],d)

def test_q_values_awake_recovery():
    c={}
    for u in m.CURRENTS:
        c[f"awake/{u}"]=np.zeros((4,2));c[f"isoflurane/{u}"]=np.tile([1.,0.],(4,1));c[f"recovery/{u}"]=np.tile([.2,0.],(4,1))
    assert all(v==.2 for v in m.q_values(c).values())

def test_decision_requires_axis_and_all_recovery():
    q={str(u):.5 for u in m.CURRENTS}; upper={str(u):.8 for u in m.CURRENTS}; halves={"early":q,"late":q}
    assert m.decide(.4,.1,.05,-.1,q,upper,halves)=="INDIVIDUAL_AXIS_AND_RECOVERY_REPLICATED"
    bad=dict(q);bad["40"]=1.1
    assert m.decide(.4,.1,.05,-.1,bad,upper,halves)=="INDIVIDUAL_AXIS_REPLICATED_RECOVERY_NOT_ESTABLISHED"
    assert m.decide(.05,-.1,.05,-.1,q,upper,halves)=="INDIVIDUAL_AXIS_NOT_REPLICATED"

def test_bootstrap_is_deterministic():
    rng=np.random.default_rng(1);dev={};conf={};direction=np.array([1.,-.5,.2])
    for u,scale in zip(m.CURRENTS,(1.,2.,3.),strict=True):
        for target,n in ((dev,20),(conf,22)):
            a=rng.normal(0,.01,(n,3));target[f"awake/{u}"]=a;target[f"isoflurane/{u}"]=a+scale*direction;target[f"recovery/{u}"]=a+.2*scale*direction
    a=m.bootstrap(dev,conf,reps=17,seed=9,batch=5);b=m.bootstrap(dev,conf,reps=17,seed=9,batch=5)
    assert all(np.array_equal(a[k],b[k]) for k in a)

def test_contract_constants_and_write_once(tmp_path):
    assert len(m.CHANNELS)==10 and m.RAW_BYTES==11_687_836_529 and m.BOOTSTRAPS==1999
    p=tmp_path/"x.json";m.write_json_once(p,{"x":1})
    try:m.write_json_once(p,{"x":2});assert False
    except RuntimeError:pass
