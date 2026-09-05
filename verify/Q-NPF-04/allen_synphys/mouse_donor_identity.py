"""제작자 mouse 표본명 규약으로 동일 donor를 판별하고 별도 donor 후보를 고른다."""
import ast
import json
import re
import sqlite3
from pathlib import Path
from population_reciprocity import DB,sha
from superficial_ee_eligibility import save
from separate_experiment_selection import SQL

HERE=Path(__file__).resolve().parent

def main():
    source=HERE/'qc_sources/lims.py'
    tree=ast.parse(source.read_text(encoding='utf-8'))
    patterns=[x.value for x in ast.walk(tree) if isinstance(x,ast.Constant) and isinstance(x.value,str) and '(?P<donor_id>' in x.value]
    assert len(patterns)==1;pattern=patterns[0]
    save('mouse_donor_identity_contract.json',dict(
        question='Do development3337 and selected3338 share the donor named in the official mouse specimen convention?',
        parser='Extract unchanged named donor_id regex from inspected producer lims.py; use fullmatch; no demographic inference.',
        selection='Retain existing matching conditions and ID order; exclude development donor solely for independence, then take first valid different donor. Preserve3338 result.',
        limits='Naming-convention identity, not an independent public donor-table join; different animals do not resolve positive-label or pooled-kinetics conditioning.',
        pattern=pattern,source_sha256=sha(source),db_sha256=sha(DB),prior_selection_code_sha256=sha(HERE/'separate_experiment_selection.py'),code_sha256=sha(Path(__file__))))
    def parse(value):
        match=re.fullmatch(pattern,value)
        return match.groupdict() if match else None
    assert parse('Driver;Reporter-123456.01.06')['donor_id']=='123456'
    assert parse('Driver;Reporter-123456.09.06')['donor_id']=='123456'
    assert parse('Driver;Reporter-654321.01.06')['donor_id']=='654321'
    assert parse('unrecognized') is None
    with sqlite3.connect(DB.as_uri()+'?mode=ro',uri=True) as db:
        db.row_factory=sqlite3.Row
        old=[dict(r) for r in db.execute('select e.id,e.ext_id,s.id slice_id,s.lims_specimen_name from experiment e join slice s on s.id=e.slice_id where e.id in(3337,3338) order by e.id')]
        for r in old:r['parsed']=parse(r['lims_specimen_name']);assert r['parsed'] is not None
        candidates=[dict(r) for r in db.execute(SQL.replace(' limit 1',''))]
    donor=old[0]['parsed']['donor_id'];checked=[];selected=None
    for r in candidates:
        parsed=parse(r['lims_specimen_name'])
        checked.append(dict(experiment_id=r['experiment_id'],pair_id=r['pair_id'],parsed=parsed))
        if parsed is not None and parsed['donor_id']!=donor:
            selected={**r,'parsed':parsed};break
    result=dict(contract_sha256=sha(HERE/'mouse_donor_identity_contract.json'),prior=old,
        same_donor=old[0]['parsed']['donor_id']==old[1]['parsed']['donor_id'],checked=checked,selected=selected,
        identity_basis='Producer documented mouse specimen naming convention')
    save('mouse_donor_identity_result.json',result)
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
