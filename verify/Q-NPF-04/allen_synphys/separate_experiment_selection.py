"""개발 실험과 같은 조건의 별도 실험을 진폭과 무관한 ID 순서로 고른다."""
import json
import sqlite3
from pathlib import Path
from population_reciprocity import ROOT,DB,sha
from superficial_ee_eligibility import save

HERE=Path(__file__).resolve().parent
SQL='''select e.id experiment_id,e.ext_id,e.slice_id,s.lims_specimen_name,
 p.id pair_id,p.pre_cell_id,p.post_cell_id,a.electrode_id pre_electrode_id,b.electrode_id post_electrode_id,
 sy.id synapse_id,sy.latency,sy.psp_rise_time,sy.psp_decay_tau
 from experiment e join slice s on s.id=e.slice_id join pair p on p.experiment_id=e.id
 join cell a on a.id=p.pre_cell_id join cell b on b.id=p.post_cell_id join synapse sy on sy.pair_id=p.id
 where e.id>3337 and e.slice_id!=2869 and s.species='mouse' and e.target_region='VisP'
 and e.project_name='mouse V1 coarse matrix' and e.internal='Standard K-Gluc'
 and e.acsf='1.3mM Ca & 1mM Mg' and e.target_temperature=32
 and a.target_layer='5' and b.target_layer='5' and a.cell_class_nonsynaptic='ex'
 and p.has_synapse=1 and sy.synapse_type='ex' and sy.latency>0 and sy.psp_rise_time>0 and sy.psp_decay_tau>0
 order by e.id,p.id limit 1'''

def main():
    save('separate_experiment_selection_contract.json',dict(
        question='Which separate experiment can check the fixed measurement workflow under matched mouseL5 recording conditions?',
        rule=SQL,selection='No amplitude or QC-score ranking; next eligible experiment/pair ID after development3337; distinct slice.',
        limits='Known positive connection and pooled producer kinetics: not blind connectivity discovery or an independent calibration holdout. Distinct animal not inferred from distinct slice.',
        db_sha256=sha(DB),code_sha256=sha(Path(__file__))))
    with sqlite3.connect(DB.as_uri()+'?mode=ro',uri=True) as db:
        db.row_factory=sqlite3.Row;rows=[dict(r) for r in db.execute(SQL)]
    save('separate_experiment_selection_result.json',dict(contract_sha256=sha(HERE/'separate_experiment_selection_contract.json'),selected=rows))
    print(json.dumps(rows,indent=2))

if __name__=='__main__':main()
