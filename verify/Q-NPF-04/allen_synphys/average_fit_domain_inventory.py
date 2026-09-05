"""저장 평균의 모든 행에서 공개 PSP 모델의 유효 범위를 확인한다."""
import argparse
import json
import math
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path
from population_reciprocity import ROOT, DB, sha
from superficial_ee_eligibility import save

HERE = Path(__file__).resolve().parent
NAME = 'average_fit_domain_inventory'
SQL = '''select a.id,a.synapse_id,a.poly_synapse_id,a.clamp_mode,a.holding,
 a.manual_qc_pass,a.n_averaged_responses,a.fit_rise_time,a.fit_decay_tau,a.fit_rise_power,
 a.fit_amp,a.nrmse,coalesce(s.pair_id,y.pair_id) pair_id,
 coalesce(s.synapse_type,y.synapse_type) synapse_type,p.experiment_id,
 e.slice_id,e.target_region,l.species
 from avg_response_fit a
 left join synapse s on s.id=a.synapse_id
 left join poly_synapse y on y.id=a.poly_synapse_id
 left join pair p on p.id=coalesce(s.pair_id,y.pair_id)
 left join experiment e on e.id=p.experiment_id
 left join slice l on l.id=e.slice_id order by a.id'''


def classify(row):
    r = dict(row)
    power = r['fit_rise_power'] if r['fit_rise_power'] is not None else 2
    r['power_source'] = 'database' if r['fit_rise_power'] is not None else 'public_source_fixed_2'
    r['effective_power'] = power
    values = (r['fit_rise_time'], r['fit_decay_tau'], power)
    r['ratio'] = None
    if any(v is None or not math.isfinite(v) or v <= 0 for v in values):
        r['domain'] = 'missing_or_nonpositive'
    else:
        r['ratio'] = r['fit_rise_time'] / (power * r['fit_decay_tau'])
        r['domain'] = 'outside' if r['ratio'] >= 1 else 'inside'
    r['source_clips'] = r['ratio'] is not None and r['ratio'] > .99999
    r['kind'] = ('mono' if r['synapse_id'] is not None else 'poly')
    assert (r['synapse_id'] is None) != (r['poly_synapse_id'] is None)
    return r


def summary(rows, keys):
    groups = defaultdict(list)
    for r in rows:
        groups[tuple(r[k] for k in keys)].append(r)
    output = []
    for key, rr in sorted(groups.items(), key=lambda x: str(x[0])):
        counts = Counter(r['domain'] for r in rr)
        output.append(dict(zip(keys, key), n=len(rr), counts=dict(counts),
            source_clips=sum(r['source_clips'] for r in rr),
            null_power=sum(r['fit_rise_power'] is None for r in rr),
            outside_percent=100 * counts['outside'] / len(rr),
            unique_pairs=len({r['pair_id'] for r in rr}),
            affected_pairs=len({r['pair_id'] for r in rr if r['domain'] == 'outside'}),
            affected_experiments=len({r['experiment_id'] for r in rr if r['domain'] == 'outside'})))
    return output


def analyze(raw):
    rows = [classify(r) for r in raw]
    assert len(rows) == len({r['id'] for r in rows})
    return dict(rows=rows, total=len(rows),
        by_mode_qc=summary(rows, ['clamp_mode', 'manual_qc_pass']),
        by_kind_mode_qc=summary(rows, ['kind', 'clamp_mode', 'manual_qc_pass']),
        by_species_mode_qc=summary(rows, ['species', 'clamp_mode', 'manual_qc_pass']),
        by_holding_mode_qc=summary(rows, ['holding', 'clamp_mode', 'manual_qc_pass']),
        qc_pass_outside_ids=[r['id'] for r in rows if r['manual_qc_pass'] == 1 and r['domain'] == 'outside'])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    sources = ['source_snapshots/allen971__neuroanalysis__fitting__psp.py',
        'source_snapshots/aisynphys__pipeline__multipatch__synapse.py', 'vc_amplitude_estimands_v2_result.json']
    if args.verify:
        c = json.loads((HERE / (NAME + '_contract.json')).read_text(encoding='utf-8'))
        assert c['code_sha256'] == sha(Path(__file__)) and c['db_sha256'] == sha(DB)
        for p, digest in c['sources'].items():
            assert sha(HERE / p) == digest
    else:
        save(NAME + '_contract.json', dict(
            question='공개 PSP 모델의 유효 범위 위반이 제작자 QC 통과 평균에도 있는가?',
            objective='연결 강도 해석에 사용하는 적합 매개변수의 적격성을 검사한다. 뇌 구조나 연결의 부재 판정이 아니다.',
            population='SynPhys r2.1 small DB avg_response_fit 전체 행. 종·모드·QC·단일/다중시냅스·유지전압을 분리하고 누락도 분모에 유지한다.',
            criterion='양수 유한 rise_time,decay_tau,power에서 rise_time/(power*decay_tau)>=1이면 공개 모델 유효 범위 밖. NULL power는 공개 코드의 고정값2 조건부. source clipping은 ratio>0.99999로 별도 표시.',
            interpretation='행 단위 전수 기술이며 독립 동물 표본이 아니다. null QC는 실패와 분리한다. 적합 수정·제외·유의성 검정·생물학적 인과 주장 없음. L0 측정모형 감사.',
            gate='전수 행수와 ID 보존·범주 분모 합·독립 SQL 교차검사. 위반이면 QC만으로 모델 영역 적합성을 보증할 수 없다고 판정한다.',
            sql=SQL, code_sha256=sha(Path(__file__)), db_sha256=sha(DB), sources={p: sha(HERE / p) for p in sources}))
    with sqlite3.connect(DB.as_uri() + '?mode=ro', uri=True) as db:
        db.row_factory = sqlite3.Row
        raw = [dict(r) for r in db.execute(SQL)]
        total = db.execute('select count(*) from avg_response_fit').fetchone()[0]
        # 파이썬 분류와 별도로 DB 조건식을 직접 평가한다.
        counts = [tuple(r) for r in db.execute('''select clamp_mode,manual_qc_pass,count(*),
            sum(case when fit_rise_time>0 and fit_decay_tau>0 and coalesce(fit_rise_power,2)>0
            and fit_rise_time>=coalesce(fit_rise_power,2)*fit_decay_tau then 1 else 0 end)
            from avg_response_fit group by clamp_mode,manual_qc_pass order by clamp_mode,manual_qc_pass''')]
    result = analyze(raw)
    assert total == result['total']
    for mode, qc, n, outside in counts:
        g = next(g for g in result['by_mode_qc'] if g['clamp_mode'] == mode and g['manual_qc_pass'] == qc)
        assert g['n'] == n and g['counts'].get('outside', 0) == outside
        assert sum(g['counts'].values()) == n
    payload = dict(contract_sha256=sha(HERE / (NAME + '_contract.json')), analysis=result)
    if args.verify:
        assert payload == json.loads((HERE / (NAME + '_result.json')).read_text(encoding='utf-8'))
        print('AVERAGE_FIT_DOMAIN_INVENTORY_VERIFIED')
    else:
        save(NAME + '_result.json', payload)
        print(json.dumps({k: v for k, v in result.items() if k not in ('rows', 'qc_pass_outside_ids')}, indent=2))


if __name__ == '__main__':
    main()
