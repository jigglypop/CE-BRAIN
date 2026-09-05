"""같은 VC 평균의 고정 구간 대비와 제작자 적합 진폭을 분해한다. 재적합은 없다."""
import argparse
import ast
import json
import sqlite3
import warnings
from pathlib import Path
import numpy as np
from scipy.special import lambertw
from population_reciprocity import ROOT, DB, sha
from superficial_ee_eligibility import save
from different_donor_vc_response import response

HERE = Path(__file__).resolve().parent
NAME = 'vc_amplitude_estimands'
PSP = 'source_snapshots/allen971__neuroanalysis__fitting__psp.py'


def read(name):
    return json.loads((HERE / name).read_text(encoding='utf-8'))


def functions():
    tree = ast.parse((HERE / PSP).read_text(encoding='utf-8'))
    nodes = []
    names = {'_psp_inner', 'psp_func', '_compute_rise_tau', 'stacked_psp_func'}
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name in ('Psp', 'StackedPsp'):
            node.bases = []
            node.body = [n for n in node.body if isinstance(n, ast.FunctionDef) and n.name in names]
            nodes.append(node)
    ns = dict(np=np, warnings=warnings, lambertw=lambertw)
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(HERE / PSP), 'exec'), ns)
    return ns['Psp'].psp_func, ns['StackedPsp'].stacked_psp_func


def analyze(fits):
    psp, stacked = functions()
    memberships = read('producer_average_membership_result.json')
    measured = read('next_donor_vc_response_result.json')
    summaries = []
    for fit in fits:
        group = 'vc_' + str(int(fit['holding']))
        a = next(a for a in memberships['averages'] if a['group'] == group)
        assert sha(ROOT / a['array_path']) == a['array_sha256']
        average = np.load(ROOT / a['array_path'], allow_pickle=False)
        t0 = a['avg_data_start_time']
        times = t0 + np.arange(len(average)) / 20000
        params = {k: fit['fit_' + k] for k in ('xoffset', 'yoffset', 'rise_time', 'decay_tau', 'amp', 'rise_power', 'exp_amp', 'exp_tau')}
        assert all(v is not None and np.isfinite(v) for v in params.values())
        assert params['rise_time'] < params['rise_power'] * params['decay_tau']
        total = stacked(times, **params)
        signal_args = {k: v for k, v in params.items() if k not in ('exp_amp', 'exp_tau')}
        signal_args['yoffset'] = 0
        signal = psp(times, **signal_args)
        baseline = total - signal
        residual = average - total
        contrast = lambda v: response(v, -t0, 20000)['delta_pA']
        values = dict(average=contrast(average), fit_total=contrast(total),
            psp_component=contrast(signal), exponential_baseline=contrast(baseline), residual=contrast(residual))
        assert abs(values['average'] - values['fit_total'] - values['residual']) < 1e-10
        assert abs(values['fit_total'] - values['psp_component'] - values['exponential_baseline']) < 1e-10
        assert abs(contrast(average + 1e-9) - values['average']) < 1e-10
        peak = psp(np.array([params['xoffset'] + params['rise_time']]), **signal_args)[0]
        assert np.isclose(peak, params['amp'], atol=1e-24, rtol=1e-10)
        membership = set(memberships['membership']['included'][group])
        inventory = read('next_donor_recording_inventory_result.json')['pairs'][0]['records']
        stimulus_ids = {p['stimulus_id'] for r in inventory for p in r['pulses'] if p['response_id'] in membership}
        raw = [r for g in measured['groups'] for r in g['analysis']['records'] if r['stimulus_id'] in stimulus_ids]
        assert len(raw) == len(stimulus_ids) == len(membership) == 60
        summaries.append(dict(group=group, fit=fit, n=60,
            raw_all_pulses_mean_pa=float(np.mean([r['delta_pA'] for r in raw])),
            raw_first_pulses_mean_pa=float(np.mean([r['delta_pA'] for r in raw if r['pulse'] == 1])),
            contrast_pa=values, fitted_peak_pa=params['amp'] * 1e12,
            peak_time_ms=(params['xoffset'] + params['rise_time']) * 1000,
            initial_latency_ms=fit['initial_xoffset'] * 1000,
            latency_shift_us=(params['xoffset'] - fit['initial_xoffset']) * 1e6,
            full_average_residual_rmse_pa=float(np.sqrt(np.mean(residual**2)) * 1e12),
            waveform_window=dict(before_ms=[-8, -3], after_ms=[1, 5], rate_hz=20000, t0=t0)))
    return summaries


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    inputs = [PSP, 'qc_sources/avg_response_fit.py', 'producer_average_membership_result.json',
        'next_donor_vc_response_result.json', 'next_donor_recording_inventory_result.json',
        'different_donor_vc_response.py', 'producer_vc_average_reconstruction_v2_result.json']
    if args.verify:
        c = read(NAME + '_contract.json')
        assert c['code_sha256'] == sha(Path(__file__))
        for name, digest in c['inputs'].items():
            assert sha(HERE / name) == digest
        result = read(NAME + '_result.json')
        assert result['contract_sha256'] == sha(HERE / (NAME + '_contract.json'))
        assert analyze(result['fits']) == result['groups']
        print('VC_AMPLITUDE_ESTIMANDS_VERIFIED')
        return
    save(NAME + '_contract.json', dict(
        question='같은 VC 자료의 고정 구간 대비와 제작자 적합 진폭은 같은 양인가?',
        objective='연결 강도 추론에서 측정 정의 혼동을 제거한다. CE 항의 생물학적 검정은 아니다.',
        selection='pair121538의 기존 두 VC 그룹, 각60반응 전부. 첫 자극은 별도 기술.',
        method='저장 평균과 저장 fit 매개변수를 고정한다. 공개 Psp/StackedPsp 수치 함수로 곡선만 평가하며 재적합하지 않는다.',
        contrast='기존 함수 그대로 평균[1,5)ms - 평균[-8,-3)ms. 평균 파형에서는 t0를 뺀 좌표를 사용한다.',
        decomposition='관측 대비=전체 적합 대비+잔차 대비; 전체 적합 대비=PSP 성분 대비+지수 기준선 대비. amp는 PSP 성분의 연속시간 정점이다.',
        gates='분모60·ID 일치·유한값·성분 선형합 오차<1e-10pA·정점과 amp 일치·상수 이동 불변 검사. 임의 임계값으로 생물 양성/음성 판정하지 않는다.',
        limits='수동 초기 지연 ±100us, 알려진 흥분성 VC의 음수 부호, 상승·감쇠 모델에 조건부. 시행 순서 혼합은 첫 자극 연결강도와 다르다. 기존 QC를 변경하지 않는다. L0 정의·계산 감사.',
        code_sha256=sha(Path(__file__)), db_sha256=sha(DB), inputs={n: sha(HERE / n) for n in inputs}))
    with sqlite3.connect(DB.as_uri() + '?mode=ro', uri=True) as db:
        db.row_factory = sqlite3.Row
        fits = [dict(r) for r in db.execute("select id,holding,n_averaged_responses,manual_qc_pass,initial_xoffset,fit_xoffset,fit_yoffset,fit_amp,fit_rise_time,fit_rise_power,fit_decay_tau,fit_exp_amp,fit_exp_tau,nrmse,meta from avg_response_fit where synapse_id=2985 and clamp_mode='vc' order by holding")]
    assert len(fits) == 2
    groups = analyze(fits)
    save(NAME + '_result.json', dict(contract_sha256=sha(HERE / (NAME + '_contract.json')), fits=fits, groups=groups))
    print(json.dumps(groups, indent=2))


if __name__ == '__main__':
    main()
