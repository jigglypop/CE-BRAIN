"""대조 분할의 시간 구조를 추세와 고정50/60Hz 성분으로 진단한다. 신호를 보정하지 않는다."""
import argparse
import json
from pathlib import Path
import numpy as np
from population_reciprocity import ROOT,sha
from superficial_ee_eligibility import save
from different_donor_vc_response import response

HERE=Path(__file__).resolve().parent
NAME='vc_control_time_structure'
SOURCES=['different_donor_vc_response_result.json','next_donor_vc_response_result.json','vc_empirical_sensitivity_result.json']


def design(t):
    return np.column_stack([np.ones(len(t)),t-.305,np.sin(2*np.pi*50*t),np.cos(2*np.pi*50*t),np.sin(2*np.pi*60*t),np.cos(2*np.pi*60*t)])


def split_gap(values):return float(np.mean(values[1::2])-np.mean(values[::2]))


def run():
    old=json.loads((HERE/SOURCES[0]).read_text(encoding='utf-8'))
    new=json.loads((HERE/SOURCES[1]).read_text(encoding='utf-8'))
    controls={('581866',c['sweep']):c for c in old['analysis']['controls']}
    for g in new['groups']:
        for c in g['analysis']['controls']:controls['593646',c['sweep']]=c
    t=np.arange(4000)/10000+.08;X=design(t);beta=np.array([20.,2.,0.,0.,3*np.cos(.37),3*np.sin(.37)])
    fit=np.linalg.lstsq(X,X@beta,rcond=None)[0]
    assert np.max(np.abs(fit-beta))<1e-9
    cc=.1+.025*np.arange(17)
    assert np.allclose(np.sin(2*np.pi*60*cc+.37),(-1.)**np.arange(17)*np.sin(.37),atol=1e-12)
    records=[]
    for donor,source in [('581866',old),('593646',new)]:
        for asset in source['assets']:
            path=ROOT/asset['path'];assert sha(path)==asset['sha256']
            with np.load(path,allow_pickle=False) as z:
                raw=z['post_current'];commands=[z['pre_command'],z['post_command']]
            fs=asset['rate_hz'];a,b=round(.08*fs),round(.53*fs)
            assert all(np.ptp(c[a:b])==0 for c in commands)
            time=np.arange(a,b)/fs;y=raw[a:b]*1e12;X=design(time)
            train=time<.305;test=~train
            models={};fits={}
            for name,columns in [('trend',[0,1]),('trend_50',[0,1,2,3]),('trend_60',[0,1,4,5]),('trend_50_60',list(range(6)))]:
                xx=X[:,columns]
                coef,_,rank,_=np.linalg.lstsq(xx,y,rcond=None);assert rank==len(columns)
                fits[name]=coef
                train_coef=np.linalg.lstsq(xx[train],y[train],rcond=None)[0]
                models[name]=dict(full_fit_mse_pA2=float(np.mean((y-xx@coef)**2)),
                    later_prediction_mse_pA2=float(np.mean((y[test]-xx[test]@train_coef)**2)))
            coef=fits['trend_50_60'];predicted={}
            # 원 표본 시각의 동일 창에 각 성분을 투영한다. 결과는 진단용으로만 저장한다.
            for label,columns in [('trend',[0,1]),('component_50',[2,3]),('component_60',[4,5])]:
                values=[]
                for center in cc:
                    means=[]
                    for lo,hi in [(-.008,-.003),(.001,.005)]:
                        ta=np.arange(round((center+lo)*fs),round((center+hi)*fs))/fs
                        means.append(float(np.mean(design(ta)[:,columns]@coef[columns])))
                    values.append(means[1]-means[0])
                predicted[label]=values
            original=[response(raw,c,fs)['delta_pA'] for c in cc]
            stored=[r['delta_pA'] for r in controls[donor,asset['sweep']]['records']]
            assert np.max(np.abs(np.array(original)-stored))<1e-8
            total=np.sum(list(predicted.values()),axis=0)
            residual=np.array(original)-total
            gaps={label:split_gap(values) for label,values in predicted.items()}
            assert abs(split_gap(original)-sum(gaps.values())-split_gap(residual))<1e-10
            records.append(dict(donor=donor,sweep=asset['sweep'],holding_nominal_mV=-70 if int(asset['sweep'])<5 else -55,
                array_sha256=asset['sha256'],rate_hz=fs,models=models,
                component_50_amplitude_pA=float(np.hypot(coef[2],coef[3])),component_60_amplitude_pA=float(np.hypot(coef[4],coef[5])),
                trend_pA_per_s=float(coef[1]),observed_split_gap_pA=split_gap(original),projected_split_gap_pA=gaps,
                residual_split_gap_pA=split_gap(residual),observed_controls_pA=original,projected_controls_pA=predicted))
    summary=[]
    for donor in ('581866','593646'):
        for voltage in (-70,-55):
            rr=[r for r in records if r['donor']==donor and r['holding_nominal_mV']==voltage];assert len(rr)==5
            summary.append(dict(donor=donor,holding_mV=voltage,
                mean_observed_split_gap_pA=float(np.mean([r['observed_split_gap_pA'] for r in rr])),
                mean_projected_60_gap_pA=float(np.mean([r['projected_split_gap_pA']['component_60'] for r in rr])),
                mean_residual_split_gap_pA=float(np.mean([r['residual_split_gap_pA'] for r in rr])),
                median_60_amplitude_pA=float(np.median([r['component_60_amplitude_pA'] for r in rr])),
                later_prediction_improved_count=sum(r['models']['trend_50_60']['later_prediction_mse_pA2']<r['models']['trend']['later_prediction_mse_pA2'] for r in rr)))
    return dict(records=records,summary=summary,checks='20 archive hashes;340 original control reproductions; harmonic coefficient fixture;60Hz alternating phase identity; split-gap decomposition')


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verify',action='store_true');args=parser.parse_args()
    contract=dict(
        question='25ms간격대조의짝수/홀수분할차이가선형추세나50/60Hz성분과일관되는가?',
        rationale='60Hz는25ms마다3pi위상이진행되어부호가뒤집힘. 이산분할의기하로정한후보이며전기장치원인으로단정안함.50Hz도고정대안으로함께검사.',
        scope='보유20VC시행의후세포원전류 .08..53초; 기존대조340개. 새다운로드없음. 모든시행보존.',
        fit='원표본pA에OLS:절편+시간선형추세;추세+50Hz;추세+60Hz;추세+50+60Hz.각주파수sin/cos두항.주파수검색안함.',
        temporal_check='동일구간앞부분 .08..305초로적합해뒤부분 .305..53초 MSE비교. 이미본자료의개발진단이며독립생물holdout아님.',
        decomposition='전체구간적합의추세·50·60Hz성분을기존[1,5)-[-8,-3)ms창에투영하고홀수평균-짝수평균차이를분해.잔차는진단용이며정정반응으로쓰지않음.',
        limits='동일자료적합의오차감소는자명하며증거승격안함.고정60Hz성분이있어도mains/생물/장치원인미확정.문턱·반응창·원판정변경안함.L0시간구조진단.',
        sources={s:sha(HERE/s) for s in SOURCES},code_sha256=sha(Path(__file__)))
    if args.verify:assert json.loads((HERE/f'{NAME}_contract.json').read_text(encoding='utf-8'))==contract
    else:save(f'{NAME}_contract.json',contract)
    result=dict(contract_sha256=sha(HERE/f'{NAME}_contract.json'),analysis=run())
    if args.verify:
        assert json.loads((HERE/f'{NAME}_result.json').read_text(encoding='utf-8'))==result
        print('CONTROL_TIME_STRUCTURE_REPRODUCTION_PASS');return
    save(f'{NAME}_result.json',result);print(json.dumps(result['analysis']['summary'],indent=2))


if __name__=='__main__':main()
