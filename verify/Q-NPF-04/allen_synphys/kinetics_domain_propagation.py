"""QC 통과 평균의 가중 kinetics를 재현하고 최종 표의 유효 범위를 확인한다."""
import argparse
import json
import math
import sqlite3
from collections import defaultdict
from pathlib import Path
from population_reciprocity import ROOT, DB, sha
from superficial_ee_eligibility import save

HERE = Path(__file__).resolve().parent
NAME = 'kinetics_domain_propagation'
INPUT = 'average_fit_domain_inventory_result.json'
SOURCE = 'source_snapshots/aisynphys__pipeline__multipatch__synapse.py'


def read(name):
    return json.loads((HERE / name).read_text(encoding='utf-8'))


def close(a, b):
    return a is None and b is None or a is not None and b is not None and math.isclose(a, b, abs_tol=1e-12, rel_tol=1e-9)


def analyze(stored):
    grouped = defaultdict(list)
    for r in read(INPUT)['analysis']['rows']:
        key = (r['kind'], r['synapse_id'] if r['kind'] == 'mono' else r['poly_synapse_id'], r['clamp_mode'])
        if r['manual_qc_pass'] == 1:
            grouped[key].append(r)
    result = []
    for s in stored:
        for mode, prefix in [('ic', 'psp'), ('vc', 'psc')]:
            rr = grouped.get((s['kind'], s['id'], mode), [])
            weights = [r['n_averaged_responses'] for r in rr]
            assert all(isinstance(w, int) and w > 0 for w in weights)
            weight = sum(weights)
            estimated = {p: sum(r['fit_' + p] * w for r, w in zip(rr, weights)) / weight if weight else None
                         for p in ('rise_time', 'decay_tau')}
            actual = {p: s[prefix + '_' + p] for p in estimated}
            finite_positive = all(v is not None and math.isfinite(v) and v > 0 for v in actual.values())
            domain = 'outside' if finite_positive and actual['rise_time'] >= 2 * actual['decay_tau'] else 'inside' if finite_positive else 'missing_or_nonpositive'
            outside = [r for r in rr if r['domain'] == 'outside']
            result.append(dict(kind=s['kind'], id=s['id'], pair_id=s['pair_id'], mode=mode,
                source_average_ids=[r['id'] for r in rr], outside_average_ids=[r['id'] for r in outside],
                responses=weight, outside_weight_fraction=sum(r['n_averaged_responses'] for r in outside) / weight if weight else None,
                reconstructed=estimated, stored=actual, matches=all(close(estimated[p], actual[p]) for p in actual),
                final_domain=domain))
    summary = []
    for kind in ('mono', 'poly'):
        for mode in ('ic', 'vc'):
            rows = [r for r in result if r['kind'] == kind and r['mode'] == mode]
            affected = [r for r in rows if r['outside_average_ids']]
            summary.append(dict(kind=kind, mode=mode, total=len(rows),
                with_qc_average=sum(bool(r['source_average_ids']) for r in rows),
                stored_positive=sum(r['final_domain'] != 'missing_or_nonpositive' for r in rows),
                mismatches=sum(not r['matches'] for r in rows),
                affected_by_outside=len(affected),
                affected_final_outside=sum(r['final_domain'] == 'outside' for r in affected),
                affected_final_inside=sum(r['final_domain'] == 'inside' for r in affected),
                all_final_outside=sum(r['final_domain'] == 'outside' for r in rows),
                outside_without_flagged_input=sum(r['final_domain'] == 'outside' and not r['outside_average_ids'] for r in rows)))
    return dict(rows=result, summary=summary)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    if args.verify:
        c = read(NAME + '_contract.json')
        assert c['code_sha256'] == sha(Path(__file__)) and c['db_sha256'] == sha(DB)
        assert c['input_sha256'] == sha(HERE / INPUT) and c['source_sha256'] == sha(HERE / SOURCE)
    else:
        save(NAME + '_contract.json', dict(
            question='영역 밖 QC 통과 평균이 최종 시냅스 kinetics에 기여하고 저장값을 재현하는가?',
            population='small DB synapse 및 poly_synapse 전체 행의 IC/VC 각각. NULL도 유지.',
            method='공개 파이프라인처럼 QC 통과 평균의 rise_time/decay_tau를 n_averaged_responses로 가중. 입력 없으면 None. 원 적합과 표를 수정하지 않는다.',
            gate='저장값과 abs_tol1e-12초+rel_tol1e-9 비교. 불일치를 삭제하지 않는다. 최종 rise_time>=2*decay_tau를 별도 판정한다.',
            limits='고정 공개 소스와 상승지수2에 조건부. 평균 매개변수의 유효성 검사이며 연결 표지나 개입 인과성 검사 아님. IC/VC와 mono/poly 구분. L0.',
            code_sha256=sha(Path(__file__)), db_sha256=sha(DB), input_sha256=sha(HERE / INPUT), source_sha256=sha(HERE / SOURCE)))
    stored = []
    with sqlite3.connect(DB.as_uri() + '?mode=ro', uri=True) as db:
        db.row_factory = sqlite3.Row
        for kind, table in [('mono', 'synapse'), ('poly', 'poly_synapse')]:
            stored.extend(dict(r, kind=kind) for r in db.execute('select id,pair_id,psp_rise_time,psp_decay_tau,psc_rise_time,psc_decay_tau from ' + table + ' order by id'))
    result = dict(contract_sha256=sha(HERE / (NAME + '_contract.json')), analysis=analyze(stored))
    if args.verify:
        assert result == read(NAME + '_result.json')
        print('KINETICS_DOMAIN_PROPAGATION_VERIFIED')
    else:
        save(NAME + '_result.json', result)
        print(json.dumps(result['analysis']['summary'], indent=2))


if __name__ == '__main__':
    main()
