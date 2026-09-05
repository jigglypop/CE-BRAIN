"""처리본 간 동일 세포·학습·평가 시행의 예측 민감도."""
import json
from pathlib import Path

import numpy as np

from randi_target_response import BASE, HERE, save, sha


def features(y, t, event_times, targets):
    xx, yy, vv = [], [], []
    for a, target in zip(event_times, targets):
        pre = y[(t >= a - 10) & (t < a - 2)]
        post = y[(t >= a + 2) & (t < a + 10)]
        mu = pre.mean(axis=0)
        trend = pre[len(pre)//2:].mean(axis=0) - pre[:len(pre)//2].mean(axis=0)
        gp = np.median(mu[np.isfinite(mu)])
        valid = np.isfinite(pre).all(axis=0) & np.isfinite(post).all(axis=0) & (mu > 0)
        dff = np.full(y.shape[1], np.nan)
        dff[valid] = (post.mean(axis=0)[valid] - mu[valid]) / mu[valid]
        valid[target] = False
        xx.append(np.column_stack([mu, trend, np.full(len(mu), gp), np.full(len(mu), a)]))
        yy.append(dff)
        vv.append(valid)
    return np.array(xx), np.array(yy), np.array(vv)


def fit(x, y, tr, te, targets):
    center, xs = x[tr].mean(axis=0), x[tr].std(axis=0)
    xs[xs < 1e-12] = 1
    design = np.column_stack([np.ones(len(x)), (x - center) / xs])
    coef = np.linalg.solve(design[tr].T @ design[tr] + np.diag([0, 10, 10, 10, 10]), design[tr].T @ y[tr])
    base = design @ coef
    residual = y[tr] - base[tr]
    adjusted = base[te].copy()
    for n, i in enumerate(te):
        matched = targets[tr] == targets[i]
        adjusted[n] += residual[matched].sum() / (matched.sum() + 5)
    scale = y[tr].std()
    return {'baseline_mse': float(np.mean(((y[te] - base[te]) / scale)**2)),
            'target_mse': float(np.mean(((y[te] - adjusted) / scale)**2)),
            'train_scale': float(scale), 'observed': y[te].tolist(),
            'baseline_prediction': base[te].tolist(), 'target_prediction': adjusted.tolist()}


def main():
    support = json.loads((HERE / 'randi_temporal_support_result.json').read_text(encoding='utf-8'))
    parent_names = ['randi_raw_alignment_result.json', 'randi_temporal_support_result.json']
    for sid in ('6', '9'):
        parent_names += [f'randi_raw_prediction_session{sid}_result.json', f'randi_raw_prediction_session{sid}_contract.json']
    inputs = {str(p.relative_to(BASE)): sha(p) for sid in ('6', '9')
              for folder in ('raw_extracted', 'exported_data')
              for p in (BASE / folder).glob(f'{sid}_*.txt')}
    contract = {'question': '표본을 맞춰도 표적 보정의 이득이 처리본에 따라 달라지는가',
                'parents': {name: sha(HERE / name) for name in parent_names},
                'inputs': inputs, 'code_sha256': sha(Path(__file__)),
                'selection': '기존 세션 6,9와 시간 분할; 두 처리본의 유한·양수 baseline 마스크 교집합',
                'minimums': '학습20, 평가3, 같은 표적 학습2; 두 처리본 학습 반응 std >1e-12',
                'models': '기존 ridge10 및 표적 잔차 합/(n+5); 각 처리본 같은 시행에서 별도 적합',
                'population_feature': '각 처리본 전체 세포의 유한한 자극 전 평균 중앙값; 모집단 구성이 다를 수 있음',
                'scale': '각 처리본의 대응 학습 반응 std; 절대 오차를 물리적으로 같은 단위로 보지 않음',
                'status': '이미 본 결과의 처리 민감도, 새 독립 확인시험 아님',
                'claim_ceiling': 'BIO_EVIDENCE_L1; 처리 단계별 인과효과·직접 신경 연결 아님'}
    save('randi_matched_processing_contract.json', contract)
    results = []
    for sid in ('6', '9'):
        row = next(r for r in support['sessions'] if r['cohort'] == 'exported_data' and r['session'] == sid)
        split = row['policies']['event_local']
        events = split['train_events'] + split['supported_test_events']
        nt = len(split['train_events'])
        t = np.loadtxt(BASE / 'raw_extracted' / f'{sid}_t.txt')
        ev = np.loadtxt(BASE / 'raw_extracted' / f'{sid}_stim_volume_i.txt', dtype=int)
        target = np.loadtxt(BASE / 'raw_extracted' / f'{sid}_stim_neurons.txt', dtype=int)[events]
        arrays = {folder: features(np.loadtxt(BASE / folder / f'{sid}_gcamp.txt'), t, t[ev[events]], target)
                  for folder in ('raw_extracted', 'exported_data')}
        valid = arrays['raw_extracted'][2] & arrays['exported_data'][2]
        cells = []
        for cell in range(valid.shape[1]):
            tr = np.flatnonzero(valid[:nt, cell])
            te = np.flatnonzero(valid[nt:, cell]) + nt
            te = np.array([i for i in te if np.sum(target[tr] == target[i]) >= 2], dtype=int)
            if len(tr) < 20 or len(te) < 3 or any(a[1][tr, cell].std() <= 1e-12 for a in arrays.values()):
                continue
            c = {'cell': cell, 'train_events': [events[i] for i in tr], 'test_events': [events[i] for i in te]}
            for folder, (x, y, _) in arrays.items():
                c[folder] = fit(x[:, cell], y[:, cell], tr, te, target)
            cells.append(c)
        assert cells
        summary = {}
        for folder in arrays:
            b = float(np.mean([c[folder]['baseline_mse'] for c in cells]))
            a = float(np.mean([c[folder]['target_mse'] for c in cells]))
            summary[folder] = {'baseline_mse': b, 'target_mse': a, 'relative_mse_reduction': 1-a/b}
        # 交差マスクで選択が変わらない場合は既存 raw 結果との一致も確認する。
        prior = json.loads((HERE / f'randi_raw_prediction_session{sid}_result.json').read_text(encoding='utf-8'))
        matched_prior = []
        for c in cells:
            previous = next(p for p in prior['cells'] if p['cell'] == c['cell'])
            same = c['test_events'] == [p['event'] for p in previous['evaluation']] and len(c['train_events']) == previous['train_n']
            if same:
                for key in ('baseline_mse', 'target_mse'):
                    assert abs(c['raw_extracted'][key] - previous[key]) < 1e-10
                matched_prior.append(c['cell'])
        results.append({'session': sid, 'cells': cells, 'cells_count': len(cells),
                        'paired_observations': sum(len(c['test_events']) for c in cells),
                        'raw_parent_reproduced_cells': matched_prior, 'summary': summary})
    save('randi_matched_processing_result.json', {'contract_sha256': sha(HERE / 'randi_matched_processing_contract.json'), 'sessions': results})
    print(json.dumps([{k:v for k,v in r.items() if k!='cells'} for r in results]))


if __name__ == '__main__':
    main()
