"""공개 MICrONS 생년월일과 사용한 synphys slice 메타데이터의 비중복 후보 점검."""
import json
import sqlite3
from pathlib import Path
from reference_spike_audit import sha

HERE=Path(__file__).resolve().parent
DB=HERE.parents[2]/'data/external/allen_synphys_r21/synphys_r2.1_small.sqlite'
POPULATION=HERE/'population_reciprocity_result.json'
OUTPUT=HERE/'microns_specimen_screen_result.json'


def main():
    population=json.loads(POPULATION.read_text(encoding='utf-8'))
    ids={r['slice_id'] for r in population['analysis']['per_experiment'] if r['species']=='mouse'}
    sql='SELECT id,date_of_birth,sex,genotype,lims_specimen_name FROM slice WHERE species=? ORDER BY id'
    with sqlite3.connect(DB.as_uri()+'?mode=ro',uri=True) as db:
        db.row_factory=sqlite3.Row;rows=[dict(r) for r in db.execute(sql,('mouse',)) if r['id'] in ids]
    assert len(rows)==len(ids)
    matches=[r for r in rows if r['date_of_birth'] is not None and r['date_of_birth'][:10]=='2017-12-19']
    unknown=[r for r in rows if not r['date_of_birth']]
    result=dict(microns_reference=dict(source='https://www.nature.com/articles/s41586-025-08790-w',section='Methods / Mouse lines and Timeline',
        date_of_birth='2017-12-19',sex='male',genotype='Slc17a7-Cre;Ai162',source_access_date='2026-09-05'),
        db_sha256=sha(DB),population_sha256=sha(POPULATION),code_sha256=sha(Path(__file__)),sql=sql,
        tested_mouse_slices=len(rows),different_known_birth_date_slices=len(rows)-len(matches)-len(unknown),
        matching_birth_date_candidates=matches,missing_birth_date_candidates=unknown,
        conclusion='metadata screen only; date mismatch supports distinct specimens if metadata correct; shared universal specimen ID and exact export-specimen binding are not established; matching DOB would not prove identity')
    if OUTPUT.exists():
        assert result==json.loads(OUTPUT.read_text(encoding='utf-8'));print('SPECIMEN_SCREEN_REPRODUCED')
    else:
        with OUTPUT.open('x',encoding='utf-8') as stream:json.dump(result,stream,indent=2)
    print(json.dumps(dict(tested=len(rows),different_known_birth_date=result['different_known_birth_date_slices'],matching_birth_date=len(matches),missing_birth_date=len(unknown)),indent=2))


if __name__=='__main__':main()
