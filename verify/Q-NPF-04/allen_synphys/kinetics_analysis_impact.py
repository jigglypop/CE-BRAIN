"""기존 구조 집계와 고정 개체 분석의 kinetics 의존 범위를 검사한다."""
import argparse
import json
import sqlite3
from pathlib import Path
import population_reciprocity as topology
from population_reciprocity import ROOT, DB, sha
from separate_experiment_selection import SQL
from superficial_ee_eligibility import save

HERE = Path(__file__).resolve().parent
NAME = 'kinetics_analysis_impact'


def read(name):
    return json.loads((HERE / name).read_text(encoding='utf-8'))


def analyze():
    accesses = set()
    denied = {'synapse', 'poly_synapse', 'avg_response_fit', 'resting_state_fit'}
    def authorizer(action, table, column, database, trigger):
        if action == sqlite3.SQLITE_READ:
            accesses.add((table, column))
            if table in denied:
                return sqlite3.SQLITE_DENY
        return sqlite3.SQLITE_OK
    with sqlite3.connect(DB.as_uri() + '?mode=ro', uri=True) as db:
        db.row_factory = sqlite3.Row
        db.set_authorizer(authorizer)
        rows = [dict(r) for r in db.execute(topology.SQL)]
        _, result = topology.analyze(rows)
        assert result == read('population_reciprocity_result.json')['analysis']
        db.set_authorizer(None)
        candidates = [dict(r) for r in db.execute(SQL.replace(' limit 1', ''))]
    prior = read('next_donor_batch_result.json')
    assert [r['pair_id'] for r in candidates] == [r['pair'] for r in prior['screening']]
    propagation = read('kinetics_domain_propagation_result.json')['analysis']['rows']
    lookup = {(r['pair_id'], r['mode']): r for r in propagation if r['kind'] == 'mono'}
    ids = sorted({104272, 116053, 121538} | {r['pair_id'] for r in candidates})
    pairs = []
    for pair in ids:
        modes = {}
        for mode in ('ic', 'vc'):
            r = lookup[pair, mode]
            modes[mode] = {k: r[k] for k in ('id', 'source_average_ids', 'outside_average_ids', 'stored', 'matches', 'final_domain')}
        pairs.append(dict(pair_id=pair, modes=modes))
    deconv = read('producer_pulse_fits_result.json')['synapse']
    actual = lookup[deconv['pair_id'], 'ic']
    assert all(deconv['psp_' + p] == actual['stored'][p] for p in ('rise_time', 'decay_tau'))
    return dict(
        scope='population_reciprocity 집계, next_donor_batch 후보5개, 실제 원파형 비교3개, 개발 IC deconvolution. 저장소 전체 의존성 증명은 아님.',
        topology=dict(reproduced=True, denied_tables=sorted(denied), observed_reads=sorted([list(p) for p in accesses]),
            directed_rows=len(rows), coverage=result['coverage'], species=result['species']),
        candidates=[r['pair_id'] for r in candidates], pairs=pairs,
        deconvolution=dict(pair_id=deconv['pair_id'], input_matches_current_db=True,
            domain=actual['final_domain'], outside_average_ids=actual['outside_average_ids']),
        limits='연결 표지의 상류 생물학적 검증 독립성을 증명하지 않는다. 이 집계에서 kinetics를 직접 읽지 않음을 확인한다. 구조 결과의 기존 검출·표본 편향은 남는다.')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    inputs = ['population_reciprocity.py', 'population_reciprocity_result.json', 'separate_experiment_selection.py',
        'next_donor_batch.py', 'next_donor_batch_result.json', 'kinetics_domain_propagation_result.json',
        'producer_pulse_fits_result.json', 'producer_deconv_comparison.py',
        'different_donor_vc_response.py', 'next_donor_vc_response.py']
    if args.verify:
        c = read(NAME + '_contract.json')
        assert c['code_sha256'] == sha(Path(__file__)) and c['db_sha256'] == sha(DB)
        for name, digest in c['inputs'].items():
            assert sha(HERE / name) == digest
    else:
        save(NAME + '_contract.json', dict(
            question='발견한 kinetics 영역 문제가 기존 구조 집계 및 고정 개체 비교에 직접 영향을 주는가?',
            method='연결 구조 SQL 실행 시 SQLite authorizer로 kinetics와 적합 표 읽기를 금지한다. 동일 분석 재현 확인. 후보5개 ID 재현 후 IC/VC 영역 상태를 연결한다.',
            gate='표 접근 금지 상태에서 기존 구조 결과와 정확히 일치; 후보 ID 일치; 실제 deconv 입력과 현재 IC 매개변수 일치. 실패는 기록하며 재선정하지 않는다.',
            limits='전역 의존성 자동 증명이 아닌 명시된 분석 경로 검사. 원파형 고정 창 측정은 직접 kinetics를 쓰지 않지만 후보 선정은 IC kinetics 존재에 조건부. L0 영향 감사.',
            code_sha256=sha(Path(__file__)), db_sha256=sha(DB), inputs={n: sha(HERE / n) for n in inputs}))
    result = dict(contract_sha256=sha(HERE / (NAME + '_contract.json')), analysis=analyze())
    if args.verify:
        assert result == read(NAME + '_result.json')
        print('KINETICS_ANALYSIS_IMPACT_VERIFIED')
    else:
        save(NAME + '_result.json', result)
        a = result['analysis']
        print(json.dumps(dict(topology_reproduced=a['topology']['reproduced'], candidates=a['candidates'],
            pairs=[dict(pair_id=r['pair_id'], modes={m: dict(domain=v['final_domain'], flagged_inputs=v['outside_average_ids']) for m, v in r['modes'].items()}) for r in a['pairs']],
            deconvolution=a['deconvolution']), indent=2))


if __name__ == '__main__':
    main()
