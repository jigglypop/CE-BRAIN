from __future__ import annotations
import importlib.util,sys
from pathlib import Path
import numpy as np
P=Path(__file__).parents[1]/"examples"/"brain"/"ce_brain_stage3b_unc31_replication_r2.py"
S=importlib.util.spec_from_file_location("s3br2",P);assert S and S.loader
m=importlib.util.module_from_spec(S);sys.modules[S.name]=m;S.loader.exec_module(m)

def test_two_hz_windows_have_required_frames():
    t=np.arange(0,40,.5);volume=40
    baseline=np.flatnonzero((t>=t[volume]-10)&(t<=t[volume]-2))
    response=np.arange(volume+3,volume+21)
    assert len(baseline)==17 and len(response)==18

def test_revision_chain_is_frozen():
    paths=m.preregistered_files();assert len(paths)==7 and all(p.is_file() for p in paths)

def test_stage3b_seed_controls_model_and_bootstrap_rng():
    assert m.base.s3a.SEED == 20260906
