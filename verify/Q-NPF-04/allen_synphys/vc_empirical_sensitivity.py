"""대조값의 유한 재조합으로 평균 전류 변화에 대한 조건부 민감도를 계산한다."""
import argparse
import itertools
import json
from pathlib import Path
import numpy as np
from population_reciprocity import sha
from superficial_ee_eligibility import save

HERE=Path(__file__).resolve().parent
NAME='vc_empirical_sensitivity'
SOURCES=['different_donor_vc_response_result.json','different_donor_holding_groups_result.json','next_donor_vc_response_result.json']
AMPLITUDES=[0,1,2,3,5,10,20]


def independent_means(matrix):
    sums=np.array([0.])
    for row in matrix:sums=(sums[:,None]+row[None,:]).ravel()
    return sums/len(matrix)


def run():
    old=json.loads((HERE/SOURCES[0]).read_text(encoding='utf-8'))
    old_groups=json.loads((HERE/SOURCES[1]).read_text(encoding='utf-8'))['vc_analysis']
    new=json.loads((HERE/SOURCES[2]).read_text(encoding='utf-8'))
    inputs=[]
    for group in old_groups:
        cc=[c for c in old['analysis']['controls'] if c['sweep'] in group['sweeps']]
        inputs.append(('581866',group['condition']['post_holding_value'],cc))
    for group in new['groups']:
        inputs.append(('593646',group['condition']['post_holding_value'],group['analysis']['controls']))
    fixture=np.array([[1.,2.],[4.,8.],[0.,3.]])
    expected=np.array([sum(x)/3 for x in itertools.product(*fixture)])
    assert np.array_equal(independent_means(fixture),expected)
    assert np.allclose(independent_means(fixture-2),expected-2)
    rows=[];noise=[]
    for donor,holding,controls in inputs:
        controls=sorted(controls,key=lambda c:int(c['sweep']))
        assert len(controls)==5 and all(len(c['records'])==17 for c in controls)
        centers=np.array([[r['center_s'] for r in c['records']] for c in controls])
        assert np.allclose(centers,.1+.025*np.arange(17),atol=1e-12,rtol=0)
        matrix=np.array([[r['delta_pA'] for r in c['records']] for c in controls])
        means=np.array([c['mean_pA'] for c in controls])
        assert np.allclose(matrix.mean(axis=1),means,atol=1e-12,rtol=0)
        noise.append(dict(donor=donor,holding_V=holding,sweeps=[c['sweep'] for c in controls],controls_pA=matrix.tolist()))
        for n in range(1,6):
            # 偶数/奇数インデックスで分け、閾値作成側の平均だけで中心化する。
            train=matrix[:n,::2];evaluation=matrix[:n,1::2]
            center=train.mean(axis=1,keepdims=True)
            train=train-center;evaluation=evaluation-center
            for dependence in ('independent_record_draws','shared_center_draws'):
                if dependence=='independent_record_draws':
                    null=independent_means(train);test=independent_means(evaluation)
                    assert len(null)==9**n and len(test)==8**n
                else:
                    null=train.mean(axis=0);test=evaluation.mean(axis=0)
                    assert len(null)==9 and len(test)==8
                threshold=float(np.quantile(null,.05,method='lower'))
                rates=[dict(added_inward_mean_pA=a,flag_fraction=float(np.mean(test-a<threshold))) for a in AMPLITUDES]
                assert all(a['flag_fraction']<=b['flag_fraction'] for a,b in zip(rates,rates[1:]))
                fpr=rates[0]['flag_fraction']
                minimum=next((r['added_inward_mean_pA'] for r in rates if r['added_inward_mean_pA']>0 and r['flag_fraction']>=.8),None)
                rows.append(dict(donor=donor,holding_V=holding,n_records=n,sweeps=[c['sweep'] for c in controls[:n]],
                    dependence=dependence,train_combinations=len(null),evaluation_combinations=len(test),threshold_pA=threshold,
                    train_null_flag_fraction=float(np.mean(null<threshold)),evaluation_null_flag_fraction=fpr,
                    evaluation_null_gate_le_10pct=fpr<=.1,minimum_grid_for_80pct_pA=minimum,
                    qualified_grid_for_80pct_pA=minimum if fpr<=.1 else None,rates=rates))
    return dict(noise=noise,records=rows,checks='Cartesian enumeration agrees with itertools; additive shift; stored control means; nondecreasing response rates')


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verify',action='store_true');args=parser.parse_args()
    hashes={name:sha(HERE/name) for name in SOURCES}
    contract=dict(
        question='현재5기록의대조변동에서 몇pA의고정평균변화를 표시할 수 있는가? 가정과N에따라어떻게달라지는가?',
        scope='두개체×두유지전압. 각5시행의17대조값재사용; 생물반응값은판정에쓰지않음. 기존에이미본대조이므로전향적holdout아님.',
        split='각기록대조인덱스0,2,..16(9개)로문턱설정;1,3,..15(8개)로평가. 중앙화는문턱설정9개평균만사용.',
        signal='평가대조의평균전류차이에고정량A를뺌. A는0,1,2,3,5,10,20pA. 원파형의PSC peak가아니며kinetics·latency·검출누락은모사안함.',
        n='시행ID오름차순첫N개,N=1..5. 실제보유5개이상으로가상동물/가상기록을만들지않음. N에따라포함시행도달라짐.',
        noise_models='각기록에서대조하나를독립선택한모든조합(9^N,8^N); 대안은동일시간인덱스를모든기록에서함께선택(9,8). 두모두자료에조건부인인위적재조합.',
        rule='문턱=문턱설정평균분포의하위5% quantile method lower. 평가평균-A가문턱보다엄격히작으면표시. 영신호표시율<=10%일때만80%표시도달최소양의grid를조건부적격값으로보고.',
        uncertainty='유한조합은새독립생물표본아님. 실제noise의정상성·시행독립·시간교환가능성은미확인. 중간점끼리의인접상관이있을수있음. p값·신뢰구간·임상검출한계아님.',
        limits='L0장치민감도. 대조범위안의반응을0으로판정하지않음. 실제과학적검정력80%또는새실험에필요한N을확정하지않음. 기존생물판정변경없음.',
        sources=hashes,code_sha256=sha(Path(__file__)))
    if args.verify:
        assert json.loads((HERE/f'{NAME}_contract.json').read_text(encoding='utf-8'))==contract
    else:save(f'{NAME}_contract.json',contract)
    result=dict(contract_sha256=sha(HERE/f'{NAME}_contract.json'),analysis=run())
    if args.verify:
        assert json.loads((HERE/f'{NAME}_result.json').read_text(encoding='utf-8'))==result
        print('SENSITIVITY_EXACT_REPRODUCTION_PASS');return
    save(f'{NAME}_result.json',result)
    for r in result['analysis']['records']:
        if r['n_records']==5:
            print(json.dumps(r,ensure_ascii=True))


if __name__=='__main__':main()
