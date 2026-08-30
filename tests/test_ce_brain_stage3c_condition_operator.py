from __future__ import annotations
import importlib.util,sys
from pathlib import Path
P=Path(__file__).parents[1]/"examples"/"brain"/"ce_brain_stage3c_condition_operator.py"
S=importlib.util.spec_from_file_location("s3c",P);assert S and S.loader
m=importlib.util.module_from_spec(S);sys.modules[S.name]=m;S.loader.exec_module(m)

def test_subject_split_is_stable():
 assert m.development_subject(9) and not m.development_subject(1)
 assert sum(m.development_subject(s) for s in range(18))==11

def test_decision_requires_structure_and_null_gates():
 good={"improvement":.1,"lower_95":.01};bad={"improvement":.01,"lower_95":.001}
 r={"condition_specific_ranking":["U_F","U_R"],"comparisons":{"U_F_vs_C_F":good,"U_F_vs_U_N":good,
    "winner_vs_runner":good,"U_N_vs_W_N":bad}}
 assert m.decide(r)=="EXPLORATORY_CONDITION_DEPENDENT_F_SUPPORTED"
 r["comparisons"]["U_F_vs_C_F"]=bad
 assert m.decide(r)=="CONDITION_DEPENDENT_OPERATOR_NOT_ESTABLISHED"

def test_revision_files_exist():
 assert len(m.preregistered_files())==6 and all(p.is_file() for p in m.preregistered_files())
