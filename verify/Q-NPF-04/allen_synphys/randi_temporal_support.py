"""자극 음수 표지와 시간 분할의 입력 지지 범위. 신호 결과는 읽지 않는다."""
import json
from pathlib import Path

import numpy as np

from randi_target_response import BASE, HERE, ROOT, save, sha


def main():
    inventory = json.loads((HERE / 'randi_intervention_inventory_result.json').read_text(encoding='utf-8'))
    rows = []
    for s in inventory['sessions']:
        folder, sid = BASE / s['cohort'], s['session']
        paths = {k: folder / f'{sid}_{k}.txt' for k in ('t', 'stim_volume_i', 'stim_neurons')}
        t = np.atleast_1d(np.loadtxt(paths['t']))
        e = np.atleast_1d(np.loadtxt(paths['stim_volume_i'], dtype=int))
        z = np.atleast_1d(np.loadtxt(paths['stim_neurons'], dtype=int))
        ts = t[e]
        minus2 = np.flatnonzero(z == -2)
        cut = int(minus2[0]) if len(minus2) else len(z)
        later = int(np.sum(z[cut + 1:] >= 0))
        row = {'cohort': s['cohort'], 'session': sid,
               'metadata_sha256': {k: sha(p) for k, p in paths.items()},
               'nonnegative_after_first_minus2': later,
               'label_count_match': s['label_count_matches_signal_columns'],
               'event_order_ok': s['event_order_nonincreasing_count'] == 0}
        row['policies'] = {}
        if row['label_count_match'] and row['event_order_ok']:
            for policy, end in [('first_minus2_tail', cut), ('event_local', len(z))]:
                kept = [k for k in range(end)
                        if 0 <= z[k] < s['signal_columns_first_row']
                        and ts[k] - 10 >= t[0] and ts[k] + 10 <= t[-1]
                        and not np.any((np.arange(len(ts)) != k)
                                       & (ts >= ts[k] - 10) & (ts < ts[k] + 10))]
                split = 2 * len(kept) // 3
                train, test = kept[:split], kept[split:]
                supported = [k for k in test if np.sum(z[train] == z[k]) >= 2]
                row['policies'][policy] = {'retained': len(kept), 'train_events': train,
                                          'test_events': test, 'supported_test_events': supported,
                                          'supported_test_targets': sorted(set(int(z[k]) for k in supported)),
                                          'pass_min5_supported': len(supported) >= 5}
        rows.append(row)
    summary = {}
    for cohort in ('exported_data', 'exported_data_unc31'):
        rr = [r for r in rows if r['cohort'] == cohort]
        summary[cohort] = {'sessions': len(rr),
                          'nonterminal_minus2_sessions': sum(r['nonnegative_after_first_minus2'] > 0 for r in rr),
                          'nonnegative_after_first_minus2': sum(r['nonnegative_after_first_minus2'] for r in rr),
                          'policies': {}}
        for policy in ('first_minus2_tail', 'event_local'):
            eligible = [r for r in rr if policy in r['policies']]
            passes = [r['session'] for r in eligible if r['policies'][policy]['pass_min5_supported']]
            summary[cohort]['policies'][policy] = {
                'eligible_sessions': len(eligible), 'passing_sessions': passes,
                'selected_first_numeric_session': min(passes, key=int) if passes else None,
                'supported_test_events_total': sum(len(r['policies'][policy]['supported_test_events']) for r in eligible)}
    result = {'question': '두 회 이상 학습한 표적의 미래 평가 시행이 세션당 다섯 개 이상 있는가',
              'design_status': 'metadata_inspected_before_prediction; not blind preregistration',
              'source_semantics': 'Fconn manual loader accepts any value except -1; bubble loader writes a -2 suffix; a -2 value alone does not prove all following events are invalid',
              'scope': '첫 -2 이후 제외는 보수적 분석 규칙; 저자 export의 필수 규칙으로 해석한 설명을 정정',
              'gate': '신호·표지 수 일치, 자극 순서, 기존 시간 창; 앞 2/3 학습, 뒤 1/3 평가; 학습 동일 표적 2회 이상, 평가 지원 시행 최소 5개',
              'claim_ceiling': 'BIO_EVIDENCE_L0',
              'source_hashes': {p.name: sha(p) for p in BASE.glob('source_*')},
              'parent_inventory_sha256': sha(HERE / 'randi_intervention_inventory_result.json'),
              'code_sha256': sha(Path(__file__)), 'summary': summary, 'sessions': rows}
    save('randi_temporal_support_result.json', result)
    print(json.dumps(summary))


if __name__ == '__main__':
    main()
