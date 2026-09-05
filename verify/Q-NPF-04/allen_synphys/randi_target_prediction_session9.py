"""WT session 9: 과거 상태 모형과 표적별 잔차 보정의 시간 분할 비교."""
import json
from pathlib import Path

import numpy as np

from randi_target_response import BASE, HERE, save, sha


def main():
    support_path = HERE / 'randi_temporal_support_result.json'
    support = json.loads(support_path.read_text(encoding='utf-8'))
    sid = '9'
    assert sid in support['summary']['exported_data']['policies']['event_local']['passing_sessions']
    row = next(r for r in support['sessions'] if r['cohort'] == 'exported_data' and r['session'] == sid)
    split = row['policies']['event_local']
    folder = BASE / 'exported_data'
    paths = {k: folder / f'{sid}_{k}.txt' for k in ('gcamp', 't', 'stim_volume_i', 'stim_neurons', 'labels')}
    contract = {'question': '비표적 세포의 미래 반응 예측에 자극 대상 정보가 이득을 주는가',
                'selection': 'Second metadata-eligible WT session 9; same model and thresholds; no outcome-based replacement',
                'support_sha256': sha(support_path), 'split': split,
                'inputs': {k: sha(p) for k, p in paths.items()}, 'code_sha256': sha(Path(__file__)),
                'windows_seconds_half_open': {'pre': [-10, -2], 'post': [2, 10]},
                'features': ['세포 전 평균', '전 구간 후반 평균 - 전반 평균', '전체 세포 전 평균의 중앙값', '자극 시각'],
                'response': 'export 형광 dF/F; 모든 창 유한 및 전 평균 양수',
                'baseline': '학습 자료만으로 feature 표준화; intercept 비벌점 ridge alpha=10',
                'target_model': 'baseline + 표적별 학습잔차 합/(표적별 학습수+5)',
                'eligibility': '직접 표적 시행 제외; 세포당 유효 학습 >=20, 지원되는 유효 평가 >=3; 학습 반응 표준편차 >1e-12',
                'metric': '학습 반응 표준편차로 나눈 제곱오차; 세포 내 평가평균 후 세포 간 평균',
                'decision': '표적 모형 평균오차 < baseline이면 탐색적 예측 이득; 인과 판정 아님',
                'limits': ['독립 동물 holdout 아님', '원 export 전처리의 전체 시계열 사용 가능성 미해결',
                           '시간·상태는 제한된 공변량이며 모든 공통 입력을 제거하지 않음',
                           'event_local은 결과를 본 기존 규칙의 수정; 새 독립 사전등록 아님'],
                'claim_ceiling': 'BIO_EVIDENCE_L1; prospective deployment and causal edge unestablished'}
    save('randi_target_prediction_session9_contract.json', contract)
    y, t = np.loadtxt(paths['gcamp']), np.loadtxt(paths['t'])
    ev, target = np.loadtxt(paths['stim_volume_i'], dtype=int), np.loadtxt(paths['stim_neurons'], dtype=int)
    labels = paths['labels'].read_text(encoding='utf-8').splitlines()
    assert y.shape == (len(t), len(labels))
    train_events = split['train_events']
    test_events = split['supported_test_events']
    assert max(train_events) < min(test_events)
    assert set(train_events).isdisjoint(test_events)
    events = train_events + test_events
    x, response, validity = [], [], []
    for k in events:
        a = t[ev[k]]
        pre = y[(t >= a - 10) & (t < a - 2)]
        post = y[(t >= a + 2) & (t < a + 10)]
        mu = pre.mean(axis=0)
        trend = pre[len(pre)//2:].mean(axis=0) - pre[:len(pre)//2].mean(axis=0)
        global_pre = np.median(mu[np.isfinite(mu)])
        valid = np.isfinite(pre).all(axis=0) & np.isfinite(post).all(axis=0) & (mu > 0)
        dff = np.full(y.shape[1], np.nan)
        dff[valid] = (post.mean(axis=0)[valid] - mu[valid]) / mu[valid]
        x.append(np.column_stack([mu, trend, np.full(len(mu), global_pre), np.full(len(mu), a)]))
        response.append(dff)
        valid[target[k]] = False
        validity.append(valid)
    x, response, validity = np.array(x), np.array(response), np.array(validity)
    event_targets = target[events]
    ntrain = len(train_events)
    cells = []
    for cell in range(y.shape[1]):
        tr = np.flatnonzero(validity[:ntrain, cell])
        te = np.flatnonzero(validity[ntrain:, cell]) + ntrain
        te = np.array([i for i in te if np.sum(event_targets[tr] == event_targets[i]) >= 2], dtype=int)
        if len(tr) < 20 or len(te) < 3:
            continue
        scale = response[tr, cell].std()
        if scale <= 1e-12:
            continue
        center = x[tr, cell].mean(axis=0)
        xs = x[tr, cell].std(axis=0)
        xs[xs < 1e-12] = 1
        design = np.column_stack([np.ones(len(events)), (x[:, cell] - center) / xs])
        penalty = np.diag([0, 10, 10, 10, 10])
        coef = np.linalg.solve(design[tr].T @ design[tr] + penalty, design[tr].T @ response[tr, cell])
        base = design @ coef
        residual = response[tr, cell] - base[tr]
        adjusted = base[te].copy()
        for n, i in enumerate(te):
            matched = event_targets[tr] == event_targets[i]
            adjusted[n] += residual[matched].sum() / (matched.sum() + 5)
        b_loss = ((response[te, cell] - base[te]) / scale) ** 2
        a_loss = ((response[te, cell] - adjusted) / scale) ** 2
        cells.append({'cell': cell, 'train_n': len(tr), 'test_n': len(te),
                      'baseline_mse': float(b_loss.mean()), 'target_mse': float(a_loss.mean()),
                      'evaluation': [{'event': events[i], 'observed': float(response[i, cell]),
                                      'baseline_prediction': float(base[i]), 'target_prediction': float(adjusted[n]),
                                      'train_scale': float(scale)} for n, i in enumerate(te)]})
    assert cells
    baseline = float(np.mean([c['baseline_mse'] for c in cells]))
    target_mse = float(np.mean([c['target_mse'] for c in cells]))
    result = {'contract_sha256': sha(HERE / 'randi_target_prediction_session9_contract.json'),
              'session': sid, 'cells': cells, 'cells_evaluated': len(cells),
              'supported_test_event_count': len(test_events), 'baseline_mse': baseline, 'target_mse': target_mse,
              'relative_mse_reduction': 1 - target_mse / baseline,
              'cells_improved': sum(c['target_mse'] < c['baseline_mse'] for c in cells),
              'status': 'EXPLORATORY_GAIN' if target_mse < baseline else 'NO_EXPLORATORY_GAIN'}
    save('randi_target_prediction_session9_result.json', result)
    print(json.dumps({k: v for k, v in result.items() if k != 'cells'}))


if __name__ == '__main__':
    main()
