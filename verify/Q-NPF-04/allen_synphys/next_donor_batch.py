"""반응 크기를 조회하지 않고 다음 개체 후보 묶음을 고정한다."""
import json
import re
import sqlite3
from pathlib import Path
from population_reciprocity import DB,sha
from superficial_ee_eligibility import save
from separate_experiment_selection import SQL

HERE=Path(__file__).resolve().parent


def main():
    prior=HERE/'mouse_donor_identity_contract.json'
    identity=json.loads(prior.read_text(encoding='utf-8'))
    assert sha(DB)==identity['db_sha256']
    query=SQL.replace(' limit 1','')
    save('next_donor_batch_contract.json',dict(
        objective='연결 반응 측정의 개체별 한계를 비교할 고정 후보 묶음. 전체 뇌 구조의 인과 확인은 아님.',
        selection='기존 mouse VisP L5 조건과 ID순서를 유지. donor499168,581866 제외. 각 donor 최초 적격 pair만 선택, 처음3donor까지. 후보 부족은 그대로 보고.',
        query=query,donor_pattern=identity['pattern'],excluded_donors=['499168','581866'],maximum_donors=3,
        outcomes='후보 선정에 반응 진폭·효과·QC점수·반응 부호를 사용하지 않음. 기존 has_synapse와kinetics 존재조건은 유지하므로 양성 표지 조건부 표본.',
        next_gate='선정된 모든 후보의 조건별 반복과 전후 상태를 조사. 반응이 작거나 불분명하다는 이유로 후보를 추가·교체하지 않음.',
        ceiling='L0 표본계획. 알려진 양성 연결 재분석이며 연결 발견·독립 예측·일반화 아님.',
        db_sha256=sha(DB),identity_contract_sha256=sha(prior),code_sha256=sha(Path(__file__))))
    with sqlite3.connect(DB.as_uri()+'?mode=ro',uri=True) as db:
        db.row_factory=sqlite3.Row;rows=[dict(r) for r in db.execute(query)]
    selected=[];screening=[];seen={'499168','581866'}
    for row in rows:
        match=re.fullmatch(identity['pattern'],row['lims_specimen_name'])
        donor=match.group('donor_id') if match else None
        reason='unparsed' if donor is None else 'excluded_or_duplicate_donor' if donor in seen else 'selected' if len(selected)<3 else 'outside_fixed_batch'
        screening.append(dict(experiment=row['experiment_id'],pair=row['pair_id'],donor=donor,decision=reason))
        if reason=='selected':
            selected.append(dict(**row,donor_id=donor));seen.add(donor)
    result=dict(contract_sha256=sha(HERE/'next_donor_batch_contract.json'),candidate_pairs=len(rows),screening=screening,selected=selected)
    save('next_donor_batch_result.json',result)
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
