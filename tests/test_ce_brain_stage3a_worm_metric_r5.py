from __future__ import annotations
import importlib.util,sys
from pathlib import Path
P=Path(__file__).parents[1]/"examples"/"brain"/"ce_brain_stage3a_worm_metric_r5.py"
S=importlib.util.spec_from_file_location("r5",P); assert S and S.loader
r5=importlib.util.module_from_spec(S);sys.modules[S.name]=r5;S.loader.exec_module(r5)

def test_triangle_is_explicitly_unidentifiable():
    rates={("A","B"):{"subjects":3},("B","C"):{"subjects":3},("A","C"):{"subjects":3}}
    row=r5.triangle_unidentifiable(rates)
    assert row["status"]=="NOT_IDENTIFIABLE" and row["eligible_ordered_triads"]==1

def test_r5_freezes_revision_chain():
    paths=r5.preregistered_files(); assert len(paths)==15 and all(p.is_file() for p in paths)
