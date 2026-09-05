"""고정된 다음 개체에 이전 VC 측정을 그대로 적용하고 유지 조건별로 보고한다."""
import argparse
import json
from pathlib import Path
import h5py
import numpy as np
import different_donor_vc_response as previous
import raw_metadata as raw
from reference_spike_audit import sha
from superficial_ee_eligibility import save

HERE=Path(__file__).resolve().parent
SOURCE=HERE/'next_donor_recording_inventory_result.json'
NAME='next_donor_vc_response'


def analyze(assets,records,groups):
    output=[]
    for group in groups:
        subset=[a for a in assets if a['sweep'] in group['sweeps']]
        assert len(subset)==5
        analysis=previous.analyze(subset,records)
        assert len(analysis['records'])==60 and sum(len(c['records']) for c in analysis['controls'])==85
        # 기존 함수의 검증 설명 문자열은10시행으로 고정돼 있어 실제 분모로 교체한다.
        analysis['validation']='60 pulse joins/durations;60 constant post commands;5 quiet pre/post command checks; unchanged negative step andDC fixtures'
        state=[]
        for r in records:
            if r['post']['sweep'] not in group['sweeps']:continue
            state.append(dict(sweep=r['post']['sweep'],pre=r['pre'],post=r['post']))
        output.append(dict(condition=group['condition'],sweeps=group['sweeps'],state=state,analysis=analysis))
    return output


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verify',action='store_true');args=parser.parse_args()
    source=json.loads(SOURCE.read_text(encoding='utf-8'))
    assert len(source['pairs'])==1
    pair=source['pairs'][0];candidate=pair['selection']
    assert candidate['donor_id']=='593646' and candidate['pair_id']==121538
    groups=[g for g in pair['groups'] if g['condition']['pre_mode']==g['condition']['post_mode']=='vc']
    assert len(groups)==2 and all(g['repeats']==g['both_qc']==g['all_aligned']==g['all_single_spike']==g['all_ex_qc']==5 for g in groups)
    wanted={s for g in groups for s in g['sweeps']}
    records=[]
    for r in pair['records']:
        if r['post']['sweep'] not in wanted:continue
        r=dict(r);r['pulses']=[dict(p,id=p['stimulus_id']) for p in r['pulses']];records.append(r)
    old_contract=json.loads((HERE/'different_donor_vc_response_contract.json').read_text(encoding='utf-8'))
    assert sha(Path(previous.__file__))==old_contract['code_sha256']
    if args.verify:
        result=json.loads((HERE/f'{NAME}_result.json').read_text(encoding='utf-8'))
        contract=json.loads((HERE/f'{NAME}_contract.json').read_text(encoding='utf-8'))
        assert contract['source_sha256']==sha(SOURCE) and contract['code_sha256']==sha(Path(__file__))
        assert analyze(result['assets'],records,groups)==result['groups']
        print('NEXT_DONOR_VC_OFFLINE_PASS');return
    save(f'{NAME}_contract.json',dict(
        question='反応크기로선정하지않은다음개체593646의 VC에서 이전고정측정의 첫/반복전류 방향은 어떠한가?',
        selection='고정 후보121538 VC전체10시행. 유지전압별5시행 두그룹. 원전류 보기 전 선정;결과로제외/교체안함.',
        method='이전고정코드 analyze/response 재사용. DB발화시각 기준 평균[1,5)ms - 평균[-8,-3)ms; 음수=inward. 각시행 .1+.025*i초 i0..16 대조.4채널 원배열, 명령·시간·단위 결박.',
        adaptation='새 재고의stimulus_id를기존함수입력id로연결. 수치규칙변경없음. 이전함수의고정10시행 검증설명만실제5시행 분모로수정.',
        groups=groups,
        state='각시행동일recording의testpulse access/input resistance와기준전압/전류를같이보존. 상태일치가정및상태보정인과효과주장안함.',
        decision='모든12pulse의 평균/중앙값/inward개수/대조범위안개수를두조건별보고. 범위는신뢰구간아님. 반응이혼재하거나대조와겹치면전달반응분리를확정하지않음.',
        limits='선정은known-positive와kinetics존재조건부. 이전실험과동일한생물조건전부를보장하지않음. 독립발화정답·무작위개입없음. CE항검정없음; L1기술상한,통합사슬L0.',
        source_sha256=sha(SOURCE),previous_method_sha256=sha(Path(previous.__file__)),code_sha256=sha(Path(__file__))))
    raw.URL=f"https://allen-synphys.s3-us-west-2.amazonaws.com/synphys-{candidate['ext_id']}.nwb"
    raw.CACHE=raw.ROOT/f"data/external/allen_synphys_r21/raw_ranges/{candidate['ext_id']}"
    raw.LIMIT=128*1024*1024
    assets=[]
    with raw.CachedRanges() as reader:
        remote=reader.remote
        with h5py.File(reader,'r') as f:
            for r in records:
                sweep=r['post']['sweep'];dest=raw.CACHE/f'vc_{sweep}.npz';receipt=dest.with_suffix('.json')
                if dest.exists() and receipt.exists():
                    meta=json.loads(receipt.read_text(encoding='utf-8'))
                    assert meta['post_recording']==r['post']['id'] and meta['remote']==remote and sha(dest)==meta['sha256']
                    assets.append(meta);continue
                assert not dest.exists() and not receipt.exists()
                arrays={};metadata=[]
                for role in ('pre','post'):
                    for kind,group,unit in [('current','acquisition/timeseries','A'),('command','stimulus/presentation','V')]:
                        matches=[f[group][k] for k in f[group] if k.startswith(f'data_{int(sweep):05d}_')
                            and 'electrode_name' in f[group][k] and previous.txt(f[group][k]['electrode_name'][()][0])==f"electrode_{r[role]['device_id']}"
                            and previous.txt(f[group][k]['data'].attrs['unit'])==unit]
                        assert len(matches)==1;node=matches[0];ds=node['data']
                        arrays[f'{role}_{kind}']=np.asarray(ds[:],float)*float(ds.attrs['conversion'])+float(ds.attrs.get('offset',0))
                        metadata.append(dict(path=node.name,start_s=float(node['starting_time'][()][0]),rate_hz=float(node['starting_time'].attrs['rate'])))
                assert len({a.shape for a in arrays.values()})==1 and all(np.isfinite(a).all() for a in arrays.values())
                assert len({n['start_s'] for n in metadata})==len({n['rate_hz'] for n in metadata})==1
                with dest.open('xb') as stream:np.savez_compressed(stream,**arrays)
                meta=dict(sweep=sweep,post_recording=r['post']['id'],pre_recording=r['pre']['id'],path=dest.relative_to(raw.ROOT).as_posix(),
                    sha256=sha(dest),rate_hz=metadata[0]['rate_hz'],nodes=metadata,remote=remote)
                with receipt.open('x',encoding='utf-8') as stream:json.dump(meta,stream,indent=2)
                assets.append(meta);print('NEXT_DONOR_VC_CACHED',sweep,flush=True)
        new_bytes=reader.downloaded_this_session
        save(f'{NAME}_cache_snapshot.json',reader.manifest)
    output=analyze(assets,records,groups)
    save(f'{NAME}_result.json',dict(contract_sha256=sha(HERE/f'{NAME}_contract.json'),remote=remote,assets=assets,groups=output,new_nwb_bytes=new_bytes))
    print(json.dumps(dict(new_bytes=new_bytes,groups=[dict(sweeps=g['sweeps'],summary=g['analysis']['summary']) for g in output]),indent=2))


if __name__=='__main__':main()
