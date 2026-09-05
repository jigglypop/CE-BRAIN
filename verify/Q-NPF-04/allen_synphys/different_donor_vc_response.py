"""동일 조건 VC10시행의 원전류 반응을 DB 발화 기준 고정 창으로 기술한다."""
import argparse
import json
from pathlib import Path
import h5py
import numpy as np
import raw_metadata as raw
from reference_spike_audit import sha
from superficial_ee_eligibility import save

HERE=Path(__file__).resolve().parent
SOURCE=HERE/'different_donor_protocol_repeats_result.json'
NAME='different_donor_vc_response'


def txt(v):return v.decode() if isinstance(v,bytes) else str(v)


def response(values,center,fs):
    def mean(a,b):
        a,b=round((center+a)*fs),round((center+b)*fs)
        assert 0<=a<b<=len(values)
        return float(values[a:b].mean())
    before,after=mean(-.008,-.003),mean(.001,.005)
    return dict(before_A=before,after_A=after,delta_pA=(after-before)*1e12)


def analyze(assets,selected):
    fs=100000;v=np.zeros(fs);v[fs//2:]=-1e-11
    assert abs(response(v,.5,fs)['delta_pA']+10)<1e-10
    assert abs(response(v+1e-9,.5,fs)['delta_pA']+10)<1e-8
    rows=[];controls=[]
    for asset in assets:
        path=raw.ROOT/asset['path'];assert sha(path)==asset['sha256']
        record=next(r for r in selected if r['post']['sweep']==asset['sweep'])
        with np.load(path,allow_pickle=False) as z:
            post=z['post_current'];post_command=z['post_command'];pre_command=z['pre_command']
        fs=asset['rate_hz'];quiet=slice(round(.08*fs),round(.53*fs))
        assert np.ptp(post_command[quiet])==np.ptp(pre_command[quiet])==0
        baseline=float(np.median(pre_command[quiet]));active=pre_command-baseline>(pre_command.max()-baseline)/2
        starts=np.flatnonzero(np.diff(active.astype(int),prepend=0)==1)
        stops=np.flatnonzero(np.diff(active.astype(int),append=0)==-1)+1
        assert len(starts)==len(stops)==12
        pulses=record['pulses']
        assert all(abs(a/fs-p['onset_time'])<=1/fs+1e-9 for a,p in zip(starts,pulses))
        assert all(abs((b-a)/fs-p['duration'])<=1/fs+1e-9 for a,b,p in zip(starts,stops,pulses))
        centers=[.1+.025*i for i in range(17)]
        assert centers[-1]+.005 < starts[0]/fs-.008
        cc=[dict(center_s=c,**response(post,c,fs)) for c in centers]
        cv=[r['delta_pA'] for r in cc];control_mean=float(np.mean(cv))
        controls.append(dict(sweep=asset['sweep'],records=cc,mean_pA=control_mean,min_pA=min(cv),max_pA=max(cv)))
        for pulse in pulses:
            center=pulse['first_spike_time'];assert center is not None and pulse['n_spikes']==1
            q=post_command[round((center-.008)*fs):round((center+.005)*fs)]
            assert np.ptp(q)==0,'후세포 자체 명령 변화'
            r=response(post,center,fs)
            rows.append(dict(sweep=asset['sweep'],pulse=pulse['pulse_number']+1,stimulus_id=pulse['id'],center_s=center,
                **r,minus_control_mean_pA=r['delta_pA']-control_mean,within_control_range=min(cv)<=r['delta_pA']<=max(cv)))
    summary=[]
    for pulse in range(1,13):
        rr=[r for r in rows if r['pulse']==pulse];d=[r['delta_pA'] for r in rr];c=[r['minus_control_mean_pA'] for r in rr]
        summary.append(dict(pulse=pulse,n=len(rr),mean_pA=float(np.mean(d)),median_pA=float(np.median(d)),
            inward_count=sum(x<0 for x in d),mean_minus_control_pA=float(np.mean(c)),
            corrected_inward_count=sum(x<0 for x in c),within_control_range=sum(r['within_control_range'] for r in rr)))
    return dict(records=rows,controls=controls,summary=summary,
                validation='120 pulse joins/durations;120 post constant commands;10 quiet pre/post command checks; negative step andDC fixtures')


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verify',action='store_true');args=parser.parse_args()
    source=json.loads(SOURCE.read_text(encoding='utf-8'))
    selected=[r for r in source['records'] if r['condition']['pre_mode']==r['condition']['post_mode']=='vc']
    assert len(selected)==10 and len({json.dumps(r['condition'],sort_keys=True) for r in selected})==1
    assert all(r['pre']['qc_pass']==r['post']['qc_pass']==1 and r['aligned_count']==r['single_spike_count']==12 for r in selected)
    if args.verify:
        result=json.loads((HERE/f'{NAME}_result.json').read_text(encoding='utf-8'))
        contract=json.loads((HERE/f'{NAME}_contract.json').read_text(encoding='utf-8'))
        assert contract['code_sha256']==sha(Path(__file__)) and contract['source_sha256']==sha(SOURCE)
        assert analyze(result['assets'],selected)==result['analysis']
        print('VC_OFFLINE_REPRODUCTION_PASS');return
    save(f'{NAME}_contract.json',dict(
        question='다른 donor의 동일 VC조건10시행에서 초기·반복 전류 변화가 같은 시행의 자극 전 변동과 어떠한 관계인가?',
        selection='조건 재고의 VC/VC 전부10시행0..9, 각12pulse. 결과·크기로 제외하지 않음. mouse donor581866, experiment4251, pair116053.',
        measurement='NWB current(A), spike center=기존DB first_spike_time; 평균[1,5)ms - 평균[-8,-3)ms, sample index 반올림. 무필터·무PSP적합. 음수는 inward 전류 변화.',
        rationale='앞선 VC 원전류 측정의 [1,5)ms와[-8,-3)ms 창을 재사용. IC의 전압 창과 다른 추정량.',
        controls='동일 시행 중심 .1+.025*i초 i0..16 같은 창17개; .08..53초 전후 명령 상수 확인, 실제 전후 창에서 후세포 명령 상수 확인.',
        identity='동일 remoteETag; NWB electrode_name=DB device.4채널 단위 A,V,A,V와 시간·rate·길이 일치; 실제 전세포 command12 pulse 시작·길이를DB1sample이내 대조.',
        output='120개 원값과 대조차이,12pulse별10반복 평균·중앙값·inward개수·대조범위안개수. 첫/회복 첫 반응도 별도 표시.',
        biological_model='막전류 관측. 통제전압·접근저항·자발입력·명령artifact와 시냅스전류를 완전히 분리하지 않음.',
        ce_delta='없음; 제작자PSC kinetics가 없어도 원전류 기술은 가능하나 기존 적합의 대체나 인과 증거 아님.',
        split='개발 재분석;10반복은 한 개체 한 연결이며 독립 개체 확인 아님.',
        falsifier='반응 방향 혼재 또는 대조변동과 겹치면 이 고정 창이 전달을 명확히 분리했다는 해석을 하지 않음. 범위는 유의성검정이 아님.',
        limits='DB spike시각의독립정답미확인; laterbaseline혼입가능; IC와합치지않음; 비율·STP적합·창튜닝안함; L1기술상한, 통합사슬L0.',
        source_sha256=sha(SOURCE),code_sha256=sha(Path(__file__)),reader_sha256=sha(Path(raw.__file__))))
    prior=json.loads((HERE/'different_donor_raw_spikes_result.json').read_text(encoding='utf-8'))
    remote=prior['assets'][0]['remote'];raw.URL=remote['url']
    raw.CACHE=raw.ROOT/'data/external/allen_synphys_r21/raw_ranges/1623269658.635';raw.LIMIT=128*1024*1024
    assets=[]
    with raw.CachedRanges() as reader:
        assert reader.remote==remote
        with h5py.File(reader,'r') as f:
            for r in selected:
                sweep=r['post']['sweep'];dest=raw.CACHE/f'vc_{sweep}.npz';receipt=dest.with_suffix('.json')
                if dest.exists() and receipt.exists():
                    meta=json.loads(receipt.read_text(encoding='utf-8'))
                    assert meta['post_recording']==r['post']['recording'] and sha(dest)==meta['sha256'];assets.append(meta);continue
                assert not dest.exists() and not receipt.exists()
                arrays={};metadata=[]
                for role in ('pre','post'):
                    for kind,group,unit in [('current','acquisition/timeseries','A'),('command','stimulus/presentation','V')]:
                        matches=[f[group][k] for k in f[group] if k.startswith(f'data_{int(sweep):05d}_')
                            and 'electrode_name' in f[group][k] and txt(f[group][k]['electrode_name'][()][0])==f"electrode_{r[role]['device_id']}"
                            and txt(f[group][k]['data'].attrs['unit'])==unit]
                        assert len(matches)==1;node=matches[0];ds=node['data']
                        arrays[f'{role}_{kind}']=np.asarray(ds[:],float)*float(ds.attrs['conversion'])+float(ds.attrs.get('offset',0))
                        metadata.append(dict(path=node.name,start_s=float(node['starting_time'][()][0]),rate_hz=float(node['starting_time'].attrs['rate'])))
                assert len({a.shape for a in arrays.values()})==1 and all(np.isfinite(a).all() for a in arrays.values())
                assert len({m['start_s'] for m in metadata})==len({m['rate_hz'] for m in metadata})==1
                with dest.open('xb') as stream:np.savez_compressed(stream,**arrays)
                meta=dict(sweep=sweep,post_recording=r['post']['recording'],pre_recording=r['pre']['recording'],
                    path=dest.relative_to(raw.ROOT).as_posix(),sha256=sha(dest),rate_hz=metadata[0]['rate_hz'],nodes=metadata)
                with receipt.open('x',encoding='utf-8') as stream:json.dump(meta,stream,indent=2)
                assets.append(meta);print('VC_CACHED',sweep,flush=True)
        new_bytes=reader.downloaded_this_session
        save(f'{NAME}_cache_snapshot.json',reader.manifest)
    analysis=analyze(assets,selected)
    save(f'{NAME}_result.json',dict(contract_sha256=sha(HERE/f'{NAME}_contract.json'),remote=remote,new_nwb_bytes=new_bytes,assets=assets,analysis=analysis))
    print(json.dumps(dict(summary=analysis['summary'],new_bytes=new_bytes),indent=2))


if __name__=='__main__':main()
