"""Allen 시각피질 상층 E-E 비교 모집단과 양방향 평가 누락을 확인한다."""
import csv
import json
import sqlite3
from collections import Counter
from pathlib import Path
from population_reciprocity import DB, TABLE, SQL, analyze, sha

HERE = Path(__file__).resolve().parent


def save(name, value):
    path = HERE / name
    if path.exists():
        assert json.loads(path.read_text(encoding='utf-8')) == value
    else:
        with path.open('x', encoding='utf-8') as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)


def main():
    assert sha(DB) == '7372499fdd874f057565080d5769baaf2659ef39d9f3bc3c7147dd1e1c280a53'
    assert sha(TABLE) == '92675aaf6fc7e032fc262cc7666998cb8009ce54e6422146d40d00ff6ae28700'
    save('superficial_ee_eligibility_contract.json', {
        'question': 'Allen 전기생리에서 EM 상층 E-E 분석과 비교할 평가 완료 모집단은 얼마나 되는가?',
        'selection': "mouse; VisP; both cell_class_nonsynaptic=ex; both target_layer in {2,2/3,3}",
        'denominator': '양방향 has_synapse 비결측인 쌍만 관측 연결률에 포함. 미평가를 음성으로 치환하지 않음.',
        'endpoint': '평가 누락, 0/1/2방향 연결 수, 실험·절편 수, 실험별 쌍 수',
        'split': '적격성 기술 조사이며 학습/확인 분할이나 가설검정 없음',
        'gate': '평가 완료 쌍과 누락 분모가 독립 SQL 및 기존 CSV와 일치해야 후속 설계 가능',
        'limits': '기능적 표지는 해부학적 정답이 아님. 절편은 독립 동물로 간주하지 않음. CE 항이나 인과사슬 검정 아님.',
        'code_sha256': sha(Path(__file__)), 'db_sha256': sha(DB), 'table_sha256': sha(TABLE)})
    with sqlite3.connect(DB.as_uri() + '?mode=ro', uri=True) as db:
        db.row_factory = sqlite3.Row
        rows = [dict(r) for r in db.execute(SQL)]
        selected = [r for r in rows if r['species'] == 'mouse' and r['target_region'] == 'VisP'
                    and r['pre_class'] == r['post_class'] == 'ex'
                    and r['pre_layer'] in ('2', '2/3', '3') and r['post_layer'] in ('2', '2/3', '3')]
        dyads, analysis = analyze(selected)
        # Independent self-join: no reliance on analyze's pairing or CSV counts.
        check = db.execute('''SELECT count(*),
          sum(p.has_synapse IS NOT NULL AND q.has_synapse IS NOT NULL),
          sum(p.has_synapse=1 AND q.has_synapse=1)
          FROM pair p JOIN pair q ON q.experiment_id=p.experiment_id
          AND q.pre_cell_id=p.post_cell_id AND q.post_cell_id=p.pre_cell_id
          JOIN experiment e ON e.id=p.experiment_id JOIN slice s ON s.id=e.slice_id
          JOIN cell a ON a.id=p.pre_cell_id JOIN cell b ON b.id=p.post_cell_id
          WHERE p.pre_cell_id<p.post_cell_id AND s.species='mouse' AND e.target_region='VisP'
          AND a.cell_class_nonsynaptic='ex' AND b.cell_class_nonsynaptic='ex'
          AND a.target_layer IN ('2','2/3','3') AND b.target_layer IN ('2','2/3','3')''').fetchone()
    with TABLE.open(encoding='utf-8', newline='') as stream:
        old = [r for r in csv.DictReader(stream) if r['species']=='mouse' and r['region']=='VisP'
               and r['class_pair']=='ex|ex' and all(x in ('2','2/3','3') for x in r['layer_pair'].split('|'))]
    assert {(int(r['pair_ab']),int(r['pair_ba']),int(r['label_ab']),int(r['label_ba'])) for r in old} == {
        (r['pair_ab'],r['pair_ba'],r['label_ab'],r['label_ba']) for r in dyads}
    counts = Counter(r['positive_directions'] for r in dyads)
    assert list(check) == [analysis['coverage']['unordered_total'], len(dyads), counts[2]]
    result = {
        'contract_sha256': sha(HERE/'superficial_ee_eligibility_contract.json'),
        'coverage': analysis['coverage'],
        'observed': {'neither': counts[0], 'one_way': counts[1], 'mutual': counts[2]},
        'experiments': len(analysis['per_experiment']),
        'slices': len({r['slice_id'] for r in dyads}),
        'assessed_dyads_per_experiment_histogram': dict(sorted(Counter(r['dyads'] for r in analysis['per_experiment']).items())),
        'missing_distance_dyads': sum(r['distance_m'] is None for r in dyads),
        'verification': 'PASS: independent SQL denominator and mutual count; exact CSV pair IDs and directional labels',
        'analysis_status': 'descriptive eligibility only; no generalization or causal result'}
    # JSON keys are strings; normalize for idempotent verification.
    result = json.loads(json.dumps(result))
    save('superficial_ee_eligibility_result.json', result)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
