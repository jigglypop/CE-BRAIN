"""유지전압을 빠뜨린 VC 조건 묶음을 정정하고 조건별 반응만 해석한다."""
import argparse
import json
from collections import defaultdict
from pathlib import Path
import numpy as np
from population_reciprocity import sha
from superficial_ee_eligibility import save

HERE=Path(__file__).resolve().parent
SOURCE=HERE/'different_donor_protocol_repeats_result.json'
VC=HERE/'different_donor_vc_response_result.json'
NAME='different_donor_holding_groups'


def inventory(source):
    groups=defaultdict(list)
    for row in source['records']:
        condition=dict(row['condition'])
        for role in ('pre','post'):
            mode=row[role]['clamp_mode']
            field='baseline_potential' if mode=='vc' else 'baseline_current'
            condition[f'{role}_holding_unit']='V' if mode=='vc' else 'A'
            condition[f'{role}_holding_value']=row[role][field]
        groups[json.dumps(condition,sort_keys=True)].append(row)
    return [dict(condition=json.loads(key),sweeps=[r['post']['sweep'] for r in rows],
                 recordings=[r['post']['recording'] for r in rows],repeats=len(rows)) for key,rows in groups.items()]


def analyze(groups,vc):
    result=[]
    for group in groups:
        if group['condition']['post_mode']!='vc':continue
        rr=[r for r in vc['analysis']['records'] if r['sweep'] in group['sweeps']]
        assert len(rr)==12*group['repeats']
        summaries=[]
        for pulse in range(1,13):
            pp=[r for r in rr if r['pulse']==pulse]
            values=[r['delta_pA'] for r in pp];corrected=[r['minus_control_mean_pA'] for r in pp]
            summaries.append(dict(pulse=pulse,n=len(pp),mean_pA=float(np.mean(values)),median_pA=float(np.median(values)),
                inward_count=sum(x<0 for x in values),mean_minus_control_pA=float(np.mean(corrected)),
                corrected_inward_count=sum(x<0 for x in corrected),within_control_range=sum(r['within_control_range'] for r in pp)))
        result.append(dict(condition=group['condition'],sweeps=group['sweeps'],summary=summaries))
    assert len(result)==2 and all(len(g['sweeps'])==5 for g in result)
    for old in vc['analysis']['summary']:
        means=[g['summary'][old['pulse']-1]['mean_pA'] for g in result]
        assert abs(np.mean(means)-old['mean_pA'])<1e-10
    return result


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--inventory-only',action='store_true');parser.add_argument('--verify',action='store_true');args=parser.parse_args()
    source=json.loads(SOURCE.read_text(encoding='utf-8'))
    if not args.verify:
        save(f'{NAME}_contract.json',dict(
            correction='앞선 grouping에서 전압고정 유지전압을 누락했다. 펄스 모양만 같은10시행은 동일 전기생리 조건이 아님.',
            timing='원파형 수집 중 DB baseline_potential을 확인하여 -70/-55mV 차이를 발견. 원전류 결과를 보고 분할하지 않음.',
            method='이전 조건 키에 전후 유지조건 추가: VC baseline_potential(V), IC baseline_current(A). DB 실수값 그대로 그룹. 원값과 원분석 보존.',
            scope='기존15기록180pulse. 수정된VC2조건 각5시행에만 반응 요약. 기존10시행 pooled summary는 해석에서 폐기.',
            limits='baseline_potential은 DB 기준. 자극명령 조건 일치가 접근저항·세포상태 동일성을 보증하지 않음. 서로 다른 시각의5시행으로 유지전압 인과효과 추정 안 함.',
            source_sha256=sha(SOURCE),code_sha256=sha(Path(__file__))))
    groups=inventory(source)
    if args.inventory_only:
        save(f'{NAME}_inventory.json',dict(contract_sha256=sha(HERE/f'{NAME}_contract.json'),groups=groups))
        print('HOLDING_INVENTORY_SAVED');return
    vc=json.loads(VC.read_text(encoding='utf-8'))
    result=dict(contract_sha256=sha(HERE/f'{NAME}_contract.json'),vc_result_sha256=sha(VC),
                groups=groups,vc_analysis=analyze(groups,vc),status='SUPERSEDES_POOLED_VC_CONDITION_INTERPRETATION')
    if args.verify:
        contract=json.loads((HERE/f'{NAME}_contract.json').read_text(encoding='utf-8'))
        assert contract['code_sha256']==sha(Path(__file__)) and contract['source_sha256']==sha(SOURCE)
        assert json.loads((HERE/f'{NAME}_result.json').read_text(encoding='utf-8'))==result
        print('HOLDING_GROUP_REPRODUCTION_PASS');return
    save(f'{NAME}_result.json',result)
    print(json.dumps(result['vc_analysis'],indent=2))


if __name__=='__main__':main()
