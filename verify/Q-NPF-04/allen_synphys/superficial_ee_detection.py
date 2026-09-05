"""고정한 상층 E-E 모집단의 연결 검출 조건을 재점검한다."""
import csv
import json
import sqlite3
from collections import Counter
from pathlib import Path
from population_reciprocity import DB, TABLE, sha
from superficial_ee_eligibility import save

HERE = Path(__file__).resolve().parent


def main():
    assert sha(DB) == '7372499fdd874f057565080d5769baaf2659ef39d9f3bc3c7147dd1e1c280a53'
    assert sha(TABLE) == '92675aaf6fc7e032fc262cc7666998cb8009ce54e6422146d40d00ff6ae28700'
    save('superficial_ee_detection_contract.json', {
        'question': '앞서 집계한 상층 E-E 231쌍의 저자 평가 표지와 검사 자극 수 조건이 일치하는가?',
        'selection': 'superficial_ee_eligibility와 동일; 기존 결과를 대체하지 않는 후속 검토',
        'rule': '각 방향 n_ex_test_spikes > 10; 양쪽 충족 쌍을 별도 기술; 임계값 탐색 없음',
        'source': 'https://raw.githubusercontent.com/AllenInstitute/aisynphys/current-release/aisynphys/connectivity.py',
        'source_scope': '열람한 current-release pair_was_probed 기준; DB 생성 당시 버전과 동일하다고 단정하지 않음',
        'identity': 'lims_specimen_name은 절편 표지로만 집계; 문자열 절단으로 동물 ID를 추정하지 않음',
        'limits': '선택/검출 감사이며 기전·전이 검정 아님; >10도 생물학적 부재를 보장하지 않음',
        'code_sha256': sha(Path(__file__)), 'db_sha256': sha(DB), 'table_sha256': sha(TABLE)})
    with TABLE.open(encoding='utf-8', newline='') as stream:
        rows = [r for r in csv.DictReader(stream) if r['species']=='mouse' and r['region']=='VisP'
                and r['class_pair']=='ex|ex' and all(x in ('2','2/3','3') for x in r['layer_pair'].split('|'))]
    with sqlite3.connect(DB.as_uri()+'?mode=ro', uri=True) as db:
        pair = {r[0]: r[1:] for r in db.execute('select id,n_ex_test_spikes,has_synapse from pair')}
        specimens = dict(db.execute('select id,lims_specimen_name from slice'))
        columns = [r[1] for r in db.execute('pragma table_info(slice)')]
    passing, failing, directions = [], [], []
    for row in rows:
        info = [pair[int(row[k])] for k in ('pair_ab','pair_ba')]
        assert [x[1] for x in info] == [int(row['label_ab']),int(row['label_ba'])]
        directions.extend(info)
        (passing if all(x[0] is not None and x[0]>10 for x in info) else failing).append(row)
    def summarize(group):
        counts = Counter(int(r['positive_directions']) for r in group)
        return {'dyads':len(group),'neither':counts[0],'one_way':counts[1],'mutual':counts[2]}
    assert len(rows)==231 and len(passing)+len(failing)==231
    result = {'contract_sha256': sha(HERE/'superficial_ee_detection_contract.json'),
        'both_above_10':summarize(passing), 'at_least_one_not_above_10':summarize(failing),
        'direction_spike_counts':{'missing':sum(x[0] is None for x in directions),
            'at_most_10':sum(x[0] is not None and x[0]<=10 for x in directions),
            'min':min(x[0] for x in directions if x[0] is not None),
            'max':max(x[0] for x in directions if x[0] is not None)},
        'slice_count':len({int(r['slice_id']) for r in rows}),
        'distinct_nonempty_specimen_names':len({specimens[int(r['slice_id'])] for r in rows if specimens[int(r['slice_id'])]}),
        'missing_specimen_name_slices':len({int(r['slice_id']) for r in rows if not specimens[int(r['slice_id'])]}),
        'explicit_donor_id_column': 'donor_id' in columns,
        'animal_independence': 'UNRESOLVED; specimen names not promoted to animal identities',
        'verification':'PASS: all pair labels match prior CSV; partition conserves 231 dyads'}
    save('superficial_ee_detection_result.json', result)
    print(json.dumps(result,ensure_ascii=False,indent=2))


if __name__=='__main__':
    main()
