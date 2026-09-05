"""같은 전세포 spike에 대한 양성/음성 표적의 IC 반응: 한 실험 내 탐색 비교."""
import argparse
import json
import platform
import sys
from pathlib import Path
import h5py
import numpy as np
import scipy
from raw_metadata import CachedRanges,CACHE
from reference_spike_audit import reference,sha,clean

HERE=Path(__file__).resolve().parent
CONTRACT=HERE/'ic_pair_comparison_contract.json'
OUTPUT=HERE/'ic_pair_comparison_result.json'


def fixtures(TSeries,detector):
    fs=100000;t=np.arange(2000)/fs-.01
    v=np.full_like(t,-.07);on=(t>=0)&(t<.0015);off=t>=.0015
    v[on]+=.02*(1-np.exp(-t[on]/.02))
    v[off]+=.02*(1-np.exp(-.0015/.02))*np.exp(-(t[off]-.0015)/.02)
    counts={name:len(detector(TSeries(y,dt=1/fs,t0=-.01,units='V'),(0,.0015)))
        for name,y in [('passive',v),('spike',v+.08*np.exp(-.5*((t-.0008)/.00012)**2))]}
    assert counts=={'passive':0,'spike':1}
    return counts


def summarize(arrays,inventory,TSeries,detector):
    records=[]
    for sweep in inventory['selected']:
        sw=sweep['sweep'];fs=sweep['nodes']['pre']['rate']
        for pulse in range(1,13):
            prefix=f'sweep{sw}_pulse{pulse}'
            pre=arrays[prefix+'_pre'];command=arrays[prefix+'_command']
            t=np.arange(len(pre))/fs-.01
            base=command[t<-.003].mean();height=command.max()-base
            active=np.flatnonzero(command-base>height/2)
            assert len(active)>1 and np.all(np.diff(active)==1)
            edges=(float(t[active[0]]),float(t[active[-1]]+1/fs))
            candidates=detector(TSeries(pre,dt=1/fs,t0=-.01,units='V'),edges)
            row={'sweep':sw,'pulse':pulse,'command_pA':float(height*1e12),'edges_s':edges,
                 'spikes':clean(candidates),'pre_peak_mV':float(pre[(t>=0)&(t<.004)].max()*1e3),'responses':{}}
            if len(candidates)==1 and candidates[0]['max_slope_time'] is not None:
                center=float(candidates[0]['max_slope_time'])
                assert np.isfinite(center) and center-.009>=t[0] and center+.008<t[-1]
                for target in ('positive','negative'):
                    voltage=arrays[prefix+'_'+target]
                    def mean(lo,hi):return float(np.interp(center+np.arange(lo,hi,1/fs),t,voltage).mean())
                    row['responses'][target]={'voltage_change_uV':(mean(.002,.008)-mean(-.008,-.003))*1e6,
                        'pre_event_control_uV':(mean(-.007,-.002)-mean(-.009,-.007))*1e6}
                row['difference_uV']=row['responses']['positive']['voltage_change_uV']-row['responses']['negative']['voltage_change_uV']
            records.append(row)
    summaries=[]
    for sweep in inventory['selected']:
        sw=sweep['sweep'];rows=[r for r in records if r['sweep']==sw];usable=[r for r in rows if r['responses']]
        first=rows[0]
        summaries.append({'sweep':sw,'single_spike_count':len(usable),'pulse_count':len(rows),
            'first_pulse':first['responses'],'first_difference_uV':first.get('difference_uV'),
            'all_pulse_positive_uV':float(np.mean([r['responses']['positive']['voltage_change_uV'] for r in usable])) if usable else None,
            'all_pulse_negative_uV':float(np.mean([r['responses']['negative']['voltage_change_uV'] for r in usable])) if usable else None})
    return records,summaries


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify',action='store_true')
    args=parser.parse_args()
    TSeries,_,manifest=reference()
    from neuroanalysis.spike_detection import detect_ic_evoked_spikes as detector
    checks=fixtures(TSeries,detector)
    ipath=HERE/'ic_recovery_inventory_result.json'
    inventory=json.loads(ipath.read_text(encoding='utf-8'))
    assert inventory['status']=='READY'
    archive=CACHE/'ic_positive_negative_windows.npz'
    if args.verify:
        result=json.loads(OUTPUT.read_text(encoding='utf-8'))
        spec=json.loads(CONTRACT.read_text(encoding='utf-8'))
        assert sha(Path(__file__))==spec['code_sha256'] and sha(ipath)==spec['inventory_sha256']
        assert sha(archive)==result['arrays_sha256'] and sha(CONTRACT)==result['contract_sha256']
        with np.load(archive,allow_pickle=False) as arrays:records,summaries=summarize(arrays,inventory,TSeries,detector)
        assert clean(records)==result['records'] and summaries==result['summaries']
        print('IC_PAIR_REPRODUCED_FROM_LOCAL_ARRAYS');return
    if CONTRACT.exists() or OUTPUT.exists():raise RuntimeError('기존 비교 영수증을 보존합니다.')
    spec={'kind':'EXPLORATORY_WITHIN_EXPERIMENT_L1_COMPONENT','question':'같은 전세포6의 spike 후 양성표적5와 음성표적3의 전압 반응이 구분되는가?',
        'selection':'메타데이터로 선택한 첫5 IC SRecovery 시행32..36,12pulse씩; 모든 기록 유지, 후세포값으로 제외하지 않음.',
        'primary':'각 sweep 첫pulse의 spike 정렬 전압 변화: 표적5-표적3. 5개의 짝 비교이며60개의 독립 생물표본이 아님. 원 연결 판정을 알고 정한 검사로 blind 구조발견이 아님.',
        'secondary':'각 sweep의 모든1-spike pulse 전압 평균; 50Hz 잔류반응·단기 가소성을 분리하지 않음.',
        'detection':'고정 neuroanalysis detect_ic_evoked_spikes 기본값. 단일 후보 및 유한max_slope_time이 있는 pulse에만 반응 요약. 누락건수와 모든 후보 기록.',
        'window':'추출 command[-10,+12]ms; 반응 spike+[2,8)ms minus baseline[-8,-3)ms. 자극 전 대조[-7,-2)ms minus[-9,-7)ms. 100kHz interpolation. 공간누화/동일공통입력 인과분리는 아직 없음.',
        'decision':'방향과 크기를 기술한다. n=5 선택된 한 전세포/한slice이며 일반화 p값이나 인과 지지를 선언하지 않음. 참조양성표지 재현 가능성만 탐색.',
        'claim_ceiling':'L1 관측; 전체뇌구조·미시변수-계량-행동 미확립.',
        'inventory_sha256':sha(ipath),'code_sha256':sha(Path(__file__)),
        'upstream_commit':manifest['commit'],'source_manifest_sha256':sha(HERE.parents[2]/'data/external/analysis_tools/neuroanalysis_source/source_manifest.json'),
        'runtime':{'python':platform.python_version(),'numpy':np.__version__,'scipy':scipy.__version__,'executable':sys.executable},
        'fixtures':checks,'compatibility':'동일한 process-local trapz->trapezoid alias. upstream source 변경 없음.'}
    with CONTRACT.open('x',encoding='utf-8') as f:json.dump(spec,f,ensure_ascii=False,indent=2)
    arrays={}
    with CachedRanges() as remote:
        with h5py.File(remote,'r') as f:
            for sweep in inventory['selected']:
                sw=sweep['sweep'];fs=sweep['nodes']['pre']['rate']
                for n,onset in enumerate(sweep['onset_times_s'],1):
                    mid=round(onset*fs);before=round(.010*fs);after=round(.012*fs)
                    nodes=dict(sweep['nodes']);nodes['command']=sweep['command']
                    for label,node in nodes.items():
                        ds=f[node['path']+'/data']
                        values=np.array(ds[mid-before:mid+after],dtype=float)*float(ds.attrs['conversion'])
                        assert len(values)==before+after and np.isfinite(values).all()
                        arrays[f'sweep{sw}_pulse{n}_{label}']=values
                print('extracted IC sweep',sw,flush=True)
        new_bytes=remote.downloaded_this_session
        total_bytes=sum(b['bytes'] for b in remote.manifest['blocks'].values())
    with archive.open('xb') as f:np.savez_compressed(f,**arrays)
    records,summaries=summarize(arrays,inventory,TSeries,detector)
    result={'contract_sha256':sha(CONTRACT),'arrays_sha256':sha(archive),'arrays_path':archive.relative_to(ROOT).as_posix(),
        'new_bytes':new_bytes,'total_cached_bytes':total_bytes,'records':clean(records),'summaries':summaries}
    with OUTPUT.open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2,allow_nan=False)
    print(json.dumps({k:v for k,v in result.items() if k!='records'},ensure_ascii=False,indent=2))


if __name__=='__main__':main()
