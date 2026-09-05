"""별도 자극 전 구간에서 대조 분포와 이미 고정된 문턱의 이동을 확인한다."""
import argparse
import json
from pathlib import Path
import numpy as np
from population_reciprocity import ROOT,sha
from superficial_ee_eligibility import save
from different_donor_vc_response import response
from vc_empirical_sensitivity import independent_means

HERE=Path(__file__).resolve().parent
NAME='vc_second_control_interval'
SOURCES=['different_donor_vc_response_result.json','next_donor_vc_response_result.json','vc_empirical_sensitivity_result.json']


def run():
    old=json.loads((HERE/SOURCES[0]).read_text(encoding='utf-8'))
    new=json.loads((HERE/SOURCES[1]).read_text(encoding='utf-8'))
    sensitivity=json.loads((HERE/SOURCES[2]).read_text(encoding='utf-8'))['analysis']
    early={(r['donor'],r['holding_V']):r for r in sensitivity['noise']}
    records=[]
    for donor,source in [('581866',old),('593646',new)]:
        for asset in source['assets']:
            path=ROOT/asset['path'];assert sha(path)==asset['sha256']
            with np.load(path,allow_pickle=False) as z:
                current=z['post_current'];commands=[z['pre_command'],z['post_command']]
            fs=asset['rate_hz'];centers=.6+.025*np.arange(17)
            a,b=round(.592*fs),round(1.005*fs)
            assert b<len(current) and all(np.ptp(c[a:b])==0 for c in commands),'별도 구간 명령이 변함; 구간 재선택 없이 중단'
            original=(old['analysis']['records'] if donor=='581866' else [r for g in new['groups'] for r in g['analysis']['records']])
            first=min(r['center_s'] for r in original if r['sweep']==asset['sweep'])
            assert 1.005<first-.008
            values=[response(current,float(c),fs)['delta_pA'] for c in centers]
            group=next(r for (d,_),r in early.items() if d==donor and asset['sweep'] in r['sweeps'])
            index=group['sweeps'].index(asset['sweep']);before=np.array(group['controls_pA'][index])
            # 같은 시간차로 이동한 창들을 원표본으로 다시 확인한다.
            reconstructed=np.array([response(current,float(c-.5),fs)['delta_pA'] for c in centers])
            assert np.max(np.abs(reconstructed-before))<1e-8
            records.append(dict(donor=donor,sweep=asset['sweep'],holding_V=group['holding_V'],array_sha256=asset['sha256'],
                centers_s=centers.tolist(),controls_pA=values,early_mean_pA=float(before.mean()),later_mean_pA=float(np.mean(values)),
                early_sd_pA=float(before.std(ddof=1)),later_sd_pA=float(np.std(values,ddof=1)),
                paired_mean_shift_pA=float(np.mean(np.array(values)-before)),
                absolute_baseline_shift_pA=float((current[round(.6*fs):round(1.*fs)].mean()-current[round(.1*fs):round(.5*fs)].mean())*1e12)))
    summaries=[]
    for (donor,holding),group in early.items():
        rr=sorted([r for r in records if r['donor']==donor and r['holding_V']==holding],key=lambda r:int(r['sweep']))
        assert len(rr)==5
        matrix=np.array([r['controls_pA'] for r in rr])
        assert [r['sweep'] for r in rr]==group['sweeps']
        center=np.array(group['controls_pA'])[:,::2].mean(axis=1,keepdims=True)
        evaluations=[]
        for dependence in ('independent_record_draws','shared_center_draws'):
            prior=next(r for r in sensitivity['records'] if r['donor']==donor and r['holding_V']==holding and r['n_records']==5 and r['dependence']==dependence)
            threshold=prior['threshold_pA']
            distribution=independent_means(matrix-center) if dependence=='independent_record_draws' else (matrix-center).mean(axis=0)
            evaluations.append(dict(dependence=dependence,frozen_threshold_pA=threshold,
                old_evaluation_flag_fraction=prior['evaluation_null_flag_fraction'],later_flag_fraction=float(np.mean(distribution<threshold)),
                combinations=len(distribution),interpretation='기존문턱을그대로적용한조건부표시율.새생물표본또는교정성공판정아님.'))
        summaries.append(dict(donor=donor,holding_V=holding,
            mean_early_control_pA=float(np.mean(group['controls_pA'])),mean_later_control_pA=float(matrix.mean()),
            mean_control_shift_pA=float(np.mean([r['paired_mean_shift_pA'] for r in rr])),
            absolute_baseline_shift_range_pA=[min(r['absolute_baseline_shift_pA'] for r in rr),max(r['absolute_baseline_shift_pA'] for r in rr)],
            evaluations=evaluations))
    return dict(records=records,summary=summaries,validation='20 raw hashes;20 later constant-command checks;340 early controls reproduced;all later windows before first stimulus')


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verify',action='store_true');args=parser.parse_args()
    contract=dict(
        question='별도 자극 전 시간대에서 대조 분포와 앞선 문턱의 표시율이 얼마나 이동하는가?',
        timing='기존시각메타데이터로첫자극최소1.04166초임을확인한뒤새구간고정.후세포값을보고구간선택안함.',
        windows='기존.1+.025*i초와별도.6+.025*i초,i0..16. [1,5)-[-8,-3)ms측정그대로;원표본반올림. .5초이동은50/60Hz모두정수주기지만잡음안정성을보증하지않음.',
        gate='새창전체.592..1.005초가같은기록안,자극전이고전후명령이각각상수여야함.실패시구간재선택안함.',
        measures='각시행대조평균/표준편차와동일인덱스이동차이; .1..5초대비.6..1초의절대전류수준차이.반응과기준전류이동은다른양.',
        threshold='앞선5시행민감도결과의각문턱과초기짝수대조중앙화값을그대로사용. 새17대조의독립조합17^5와동일인덱스17개에서표시율계산.재적합/신호추가/문턱수정없음.',
        limits='같은20시행의다른구간,독립개체holdout아님. 원파일은앞서확보했고새구간요약만이번에계산. 시간정상성/독립성/자발입력없는상태미확인.L0측정진단.기존생물판정변경없음.',
        sources={s:sha(HERE/s) for s in SOURCES},code_sha256=sha(Path(__file__)))
    if args.verify:assert json.loads((HERE/f'{NAME}_contract.json').read_text(encoding='utf-8'))==contract
    else:save(f'{NAME}_contract.json',contract)
    result=dict(contract_sha256=sha(HERE/f'{NAME}_contract.json'),analysis=run())
    if args.verify:
        assert json.loads((HERE/f'{NAME}_result.json').read_text(encoding='utf-8'))==result
        print('SECOND_CONTROL_INTERVAL_REPRODUCTION_PASS');return
    save(f'{NAME}_result.json',result);print(json.dumps(result['analysis']['summary'],indent=2))


if __name__=='__main__':main()
