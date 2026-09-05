"""고정된 첫 5개 적격 sweep의 명령 정렬 파형을 조사한다. 원 회귀 재시험 아님."""
import hashlib
import json
import re
from pathlib import Path

import h5py
import numpy as np
from raw_metadata import CachedRanges, CACHE

HERE=Path(__file__).resolve().parent


def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def onset_times(note):
    times=[]
    for part in note.split(':'):
        if re.search(r'\bPulse=\d+;',part):
            times.append(float(part.split(',')[0]))
    return times


def main():
    path=HERE/'raw_pulse_windows_result.json'
    if path.exists(): raise RuntimeError('원 파형 추출 결과 보존')
    mapping_path=HERE/'raw_sweep_map_result.json'
    mapping=json.loads(mapping_path.read_text(encoding='utf-8'))
    sweeps={}
    for row in mapping['rows']: sweeps.setdefault(row['sweep'],{})[row['headstage']]=row
    eligible=[]
    for sw,pair in sorted(sweeps.items()):
        if set(pair)!={4,5}: continue
        post,pre=pair[4],pair[5]
        holding=float(post['metadata']['V-Clamp Holding Level'].split()[0])
        if post['unit']!='A' or pre['unit']!='A' or not -80<=holding<=-60: continue
        if 'SPulsTrn_20Hz' not in pre['stimulus']: continue
        if len(onset_times(pre['metadata'].get('Epochs','')))!=12: continue
        eligible.append(sw)
    selected=eligible[:5]
    if len(selected)!=5: raise RuntimeError(f'적격 sweep 부족: {eligible}')
    spec={'kind':'POST_RESULT_COMMAND_LOCKED_DIAGNOSTIC','mapping_sha256':digest(mapping_path),
          'code_sha256':digest(Path(__file__)),'selected_sweeps':selected,'eligible_sweeps':eligible,
          'selection':'첫5개: 양쪽 current unit A, 후세포 holding[-80,-60]mV, 20Hz train, 메타데이터12pulse. holding 메모 이월값은 notebook 미검증.',
          'windows':'각 명령 onset[-10,+10]ms; baseline[-10,-3)ms, response[2,5)ms 평균. 선행 current peak가 아니라 명령 정렬. 단일시냅스 분리·원 spike QC 재현 아님.',
          'comparison':'각 sweep에서 첫pulse 반응 대 pulse2..8 평균; n=5 기술적 비교, 조건별 귀무검정 없음.',
          'claim_ceiling':'측정진단. 뇌 구조나 단기 가소성 확정 아님.'}
    contract=HERE/'raw_pulse_windows_contract.json'
    with contract.open('x',encoding='utf-8') as f:json.dump(spec,f,ensure_ascii=False,indent=2)
    records=[]
    arrays={}
    with CachedRanges() as r:
        for sw in selected:
            with h5py.File(r,'r') as f:
                post,pre=sweeps[sw][4],sweeps[sw][5]
                assert post['start_s']==pre['start_s'] and post['rate']==pre['rate']
                fs=post['rate'];before=round(.010*fs);after=round(.010*fs)
                times=onset_times(pre['metadata']['Epochs'])
                events=[]
                for n,onset in enumerate(times):
                    center=round(onset*fs)
                    entry={'pulse':n+1,'onset_s':onset}
                    for label,row,node_name in [('post',post,'acquisition'),('pre',pre,'acquisition'),('command',pre,'command')]:
                        ds=f[row[node_name]+'/data']
                        values=np.asarray(ds[center-before:center+after],dtype=float)*float(ds.attrs['conversion'])
                        assert len(values)==before+after and np.isfinite(values).all()
                        arrays[f'sweep{sw}_pulse{n+1}_{label}']=values
                        baseline=values[:round(.007*fs)]
                        response=values[before+round(.002*fs):before+round(.005*fs)]
                        scale=1e12 if label!='command' else 1e3
                        entry[label]={'baseline_mean':float(baseline.mean()*scale),
                            'baseline_sd':float(baseline.std()*scale),
                            'response_minus_baseline':float((response.mean()-baseline.mean())*scale),
                            'units':'pA' if label!='command' else 'mV'}
                        if label=='command':
                            peak=float((values[before:before+round(.002*fs)].max()-baseline.mean())*scale)
                            assert peak>0, '메타데이터 onset에서 양의 자극 명령이 확인되지 않음'
                            entry[label]['pulse_peak_delta_mV']=peak
                    events.append(entry)
                first=-events[0]['post']['response_minus_baseline']
                later=-np.mean([e['post']['response_minus_baseline'] for e in events[1:8]])
                records.append({'sweep':sw,'rate_hz':fs,'events':events,'first_inward_pA':first,
                                'later_mean_inward_pA':float(later),'later_minus_first_pA':float(later-first)})
                print('extracted sweep',sw,flush=True)
        new_bytes=r.downloaded_this_session
        cached=sum(b['bytes'] for b in r.manifest['blocks'].values())
    archive=CACHE/'selected_pulse_windows.npz'
    with archive.open('xb') as f:np.savez_compressed(f,**arrays)
    result={'contract_sha256':digest(contract),'records':records,'new_bytes':new_bytes,'cached_bytes':cached,
            'array_archive':archive.relative_to(HERE.parents[2]).as_posix(),'array_sha256':digest(archive),
            'mean_first_inward_pA':float(np.mean([row['first_inward_pA'] for row in records])),
            'mean_later_inward_pA':float(np.mean([row['later_mean_inward_pA'] for row in records]))}
    path.write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k!='records'},indent=2))


if __name__=='__main__':main()
