"""기존 자료의 시간·자극 전 상태 보정: 사후 탐색적 선형 대비."""
import json
import sys
from pathlib import Path

import numpy as np

from randi_target_response import HERE, save, sha
from rowland_first_session import BASE
from rowland_sessions import read_sessions
from rowland_symbolic_reader import array


def fit(y, treatment, covariates):
    z = np.asarray(covariates, dtype=float)
    if z.size:
        z = (z - z.mean(axis=0)) / z.std(axis=0)
    else:
        z = np.empty((len(y), 0))
    nuisance = np.column_stack([np.ones(len(y)), z])
    x = np.column_stack([nuisance, treatment])
    assert np.isfinite(x).all() and np.isfinite(y).all()
    beta, _, rank, _ = np.linalg.lstsq(x, y, rcond=None)
    assert rank == x.shape[1] and np.linalg.cond(x) < 1e8
    rt = treatment - nuisance @ np.linalg.lstsq(nuisance, treatment, rcond=None)[0]
    ry = y - nuisance @ np.linalg.lstsq(nuisance, y, rcond=None)[0]
    fwl = float(rt @ ry / (rt @ rt))
    assert abs(fwl - beta[-1]) < 1e-10
    return {'coefficient': float(beta[-1]), 'rank': int(rank),
            'condition_number': float(np.linalg.cond(x)),
            'treatment_residual_variance_fraction': float(rt @ rt / np.sum((treatment-treatment.mean())**2))}


def synthetic_check():
    rng = np.random.default_rng(20260905)
    t = rng.integers(0, 2, 100).astype(float)
    z = np.column_stack([rng.normal(size=100) + t, rng.normal(size=100)])
    y = .3 + .7*t + z @ np.array([2., -1.])
    assert abs(fit(y, t, z)['coefficient'] - .7) < 1e-12
    assert abs(fit(y, t, [])['coefficient'] - (y[t==1].mean()-y[t==0].mean())) < 1e-12
    assert abs(fit(y-z[:, 0], t, z)['coefficient'] - .7) < 1e-12


def reference(mouse, run):
    if (mouse, run) == ('J064', 10):
        p = HERE/'rowland_first_session_result.json'
        r = json.loads(p.read_text(encoding='utf-8'))
        return p, r['test_minus_catch']
    suffix = '' if (mouse, run) == ('J064', 11) else '_clock_filtered'
    p = HERE/f'rowland_{mouse}_run{run}{suffix}_result.json'
    r = json.loads(p.read_text(encoding='utf-8'))
    return p, next(o['test_minus_catch'] for o in r['offsets'] if o['shift_frames']==0)


def main():
    synthetic_check()
    path = BASE/'sessions_lite_flu_2022-08-11.pkl'
    verified_path = HERE/'rowland_complete_payload_validation.json'
    verified = json.loads(verified_path.read_text(encoding='utf-8'))
    assert path.stat().st_size == verified['bytes'] and verified['pickle_complete']
    sessions, status = read_sessions(path)
    assert status['pickle_complete'] and status['sessions'] == verified['sessions']
    refs = [reference(s['mouse'], s['run_number']) for s in sessions]
    contract = save('rowland_prestate_adjustment_contract.json', {
        'question': '시간 및 자극 전 S1/S2 평균을 선형 보정해도 S2 관측 대비 부호가 유지되는가',
        'objective_chain': 'S1 자극과 S2 관측 반응의 관계; 직접 전달 경로의 식별은 하지 않음',
        'bio_starting_mechanism': '자극 뒤 신경 활동과 칼슘 형광의 관계; 기전 매개변수 추정 아님',
        'ce_delta': '없음; CE 항 검증 또는 새 뇌 법칙 제안 아님',
        'measurement_model': '기존 export 형광, 명목 30Hz; 프레임 전처리·칼슘 동역학을 역산하지 않음',
        'split': '이미 본 전체 11세션의 사후 탐색; 독립 holdout 없음',
        'source_sha256': verified['sha256'], 'source_bytes': verified['bytes'],
        'validation_sha256': sha(verified_path), 'source_url': 'https://gin.g-node.org/doi/S1S2_all-optical_data',
        'code_sha256': sha(Path(__file__)),
        'dependencies': {n: sha(HERE/n) for n in ['rowland_sessions.py','rowland_symbolic_reader.py','randi_target_response.py']},
        'previous_results': {p.name: sha(p) for p, _ in refs},
        'windows_seconds': {'pre': [-2,-.5], 'post': [1.5,3]},
        'eligibility': '기존 export, 유한한 galvo 시각, catch 또는 test; easy 제외',
        'models': ['S2 delta ~ 1 + test', 'S2 delta ~ 1 + elapsed_galvo_time + test',
                   'S2 delta ~ 1 + elapsed_galvo_time + S1_pre + S2_pre + test'],
        'estimand': '세션별 선형 투영의 test 계수; 인과효과 아님',
        'nuisance_scaling': '세션별 분석 시행에서 평균 0·표준편차 1; 상수 열·rank 부족·condition>=1e8 중단',
        'selection': '모든 세션·세 모형 보고; 부호에 따른 모형/표본 선택 없음',
        'matched_controls': '동일 시행에서 무보정·시간만·시간과 두 영역 전 상태 보정 비교',
        'falsifier': '보정 후 부호 반전이면 해당 모형에서 무보정 부호 유지라는 기술적 진술 불성립',
        'residual_rule': 'OLS와 잔차화 계수 일치 및 기존 delta 대비 재현 확인; 통계적 유의성 판정 없음',
        'revision_trigger': '대응·수치 검증 실패시 결과 해석 중단; 보정에 따른 차이는 후속 탐색 질문',
        'limits': ['비무작위·미측정 교란', '전처리된 pre 신호가 완전한 인과적 사전 상태는 아님',
                   'baseline 측정오차·평균회귀', '비선형 시간·역사효과 미모형화',
                   '자극 뒤 핥기·보상으로 조건화하지 않음', '동물간 통합·세포 종단 동일성 없음'],
        'claim_ceiling': 'BIO_EVIDENCE_L1 exploratory conditional association',
        'interpreter': sys.executable, 'numpy': np.__version__})
    rows = []
    for s, (refpath, refdelta) in zip(sessions, refs):
        y = array(s['behaviour_trials'])
        s1, s2 = array(s['s1_bool']), array(s['s2_bool'])
        idx, stim = array(s['nonnan_trials']), array(s['photostim'])
        galvo = array(s['galvo_ms'])[idx]
        assert s['frequency']==30 and s['pre_frames']==240 and y.shape[2]==420
        assert np.array_equal(s1, ~s2) and s1.any() and s2.any()
        valid = np.isfinite(galvo) & np.isin(stim,[0,1])
        preframes, postframes = np.arange(180,225), np.arange(285,330)
        pre = y[:,:,preframes].mean(axis=2)
        post = y[:,:,postframes].mean(axis=2)
        assert np.isfinite(pre).all() and np.isfinite(post).all()
        a, b = pre[s1].mean(axis=0)[valid], pre[s2].mean(axis=0)[valid]
        after = post[s2].mean(axis=0)[valid]
        delta = (post[s2]-pre[s2]).mean(axis=0)[valid]
        t = (stim[valid]==1).astype(float)
        elapsed = (galvo[valid]-galvo[valid][0])/1000
        assert np.all(np.diff(elapsed)>0)
        raw = fit(delta,t,[])
        assert abs(raw['coefficient']-refdelta)<1e-12
        covs = np.column_stack([elapsed,a,b])
        adjusted = fit(delta,t,covs)
        assert abs(adjusted['coefficient']-fit(after,t,covs)['coefficient'])<1e-10
        row = {'mouse': s['mouse'], 'run': s['run_number'], 'n': int(valid.sum()),
               'catch_n': int((t==0).sum()), 'test_n': int((t==1).sum()),
               'reference': refpath.name, 'raw': raw,
               'time_only': fit(delta,t,elapsed[:,None]), 'time_prestate': adjusted,
               's1_pre_gap': float(a[t==1].mean()-a[t==0].mean()),
               's2_pre_gap': float(b[t==1].mean()-b[t==0].mean()),
               's2_post_gap': float(after[t==1].mean()-after[t==0].mean()),
               'original_indices': idx[valid].tolist(), 'test': t.tolist(),
               'elapsed_seconds': elapsed.tolist(), 's1_pre': a.tolist(), 's2_pre': b.tolist(),
               's2_post': after.tolist(), 's2_delta': delta.tolist()}
        rows.append(row)
        if isinstance(y,np.memmap): y._mmap.close()
    save('rowland_prestate_adjustment_result.json', {'contract_sha256':sha(contract),
         'synthetic_check_passed':True,'rows':rows,'claim_ceiling':'BIO_EVIDENCE_L1'})
    print(json.dumps([{k:r[k] for k in ['mouse','run','n','raw','time_only','time_prestate','s2_pre_gap','s2_post_gap']} for r in rows]))


if __name__ == '__main__':
    main()
