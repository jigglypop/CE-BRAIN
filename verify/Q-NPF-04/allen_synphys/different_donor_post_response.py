"""정렬 누락 시행의 후세포 전압을 명령 기준 고정 창과 자극 전 대조로 측정한다."""
import argparse
import json
from pathlib import Path
import h5py
import numpy as np
import medium_recording_lookup as m
import raw_metadata as raw
from reference_spike_audit import sha
from superficial_ee_eligibility import save

HERE = Path(__file__).resolve().parent
PRIOR = HERE/'different_donor_raw_spikes_result.json'
COVERAGE = HERE/'different_donor_fit_coverage_result.json'
PREFIX = 'different_donor_post_response'


def txt(v):
    return v.decode() if isinstance(v, bytes) else str(v)


def contrast(v, center, fs):
    def window(lo, hi):
        a, b = center+round(lo*fs), center+round(hi*fs)
        assert 0 <= a < b <= len(v)
        return float(np.mean(v[a:b]))
    before, after = window(-.008, -.003), window(.003, .009)
    return dict(before_V=before, after_V=after, delta_uV=(after-before)*1e6)


def analyze(assets, prior):
    fs = 200000
    zero = np.zeros(fs)
    assert contrast(zero, fs//2, fs)['delta_uV'] == 0
    step = zero.copy(); step[fs//2:] = .0001
    assert abs(contrast(step, fs//2, fs)['delta_uV']-100) < 1e-10
    assert abs(contrast(step+.03, fs//2, fs)['delta_uV']-100) < 1e-8
    records, controls = [], []
    for asset in assets:
        pre_asset = next(a for a in prior['assets'] if a['binding']['sweep'] == asset['binding']['sweep'])
        assert sha(raw.ROOT/asset['path']) == asset['sha256']
        assert sha(raw.ROOT/pre_asset['path']) == pre_asset['sha256']
        with np.load(raw.ROOT/asset['path'], allow_pickle=False) as z:
            v, command = z['voltage'], z['current']
        with np.load(raw.ROOT/pre_asset['path'], allow_pickle=False) as z:
            pre_command = z['current']
        assert len(v) == len(pre_command)
        fs = asset['rate_hz']; sweep = int(asset['binding']['sweep'])
        pulses = [r for r in prior['records'] if r['sweep'] == sweep]
        assert len(pulses) == 12
        centers = [.1+.025*i for i in range(17)]
        assert centers[-1]+.009 < min(r['actual_onset_s'] for r in pulses)
        quiet = slice(round(.08*fs), round(.53*fs))
        assert np.ptp(command[quiet]) == 0 and np.ptp(pre_command[quiet]) == 0
        cc = [dict(center_s=c, **contrast(v, round(c*fs), fs)) for c in centers]
        values = [c['delta_uV'] for c in cc]
        controls.append(dict(sweep=sweep, records=cc, minimum_uV=min(values), maximum_uV=max(values),
                             mean_uV=float(np.mean(values))))
        for row in pulses:
            center = round(row['actual_onset_s']*fs)
            command_window = command[center-round(.008*fs):center+round(.009*fs)]
            assert np.ptp(command_window) == 0, '후세포 자체 명령 변화: 반응 해석 중단'
            observed = contrast(v, center, fs)
            records.append(dict(sweep=sweep, pulse=row['stimulus']['pulse_number']+1,
                stim_pulse_id=row['stimulus']['id'], spike_alignment_missing=not row['aligned'],
                actual_onset_s=row['actual_onset_s'], **observed,
                minus_control_mean_uV=observed['delta_uV']-float(np.mean(values)),
                within_control_range=min(values)<=observed['delta_uV']<=max(values)))
    return dict(assets=assets, records=records, controls=controls,
                validation='24 pulse; post command constant per window; both commands constant during controls; DC and100uV step fixtures')


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--verify', action='store_true'); args=parser.parse_args()
    prior = json.loads(PRIOR.read_text(encoding='utf-8'))
    output = HERE/f'{PREFIX}_result.json'
    if args.verify:
        result=json.loads(output.read_text(encoding='utf-8'))
        contract=json.loads((HERE/f'{PREFIX}_contract.json').read_text(encoding='utf-8'))
        assert contract['code_sha256']==sha(Path(__file__)) and contract['prior_sha256']==sha(PRIOR)
        assert analyze(result['analysis']['assets'], prior)==result['analysis']
        print('OFFLINE_REPRODUCTION_PASS'); return
    save(f'{PREFIX}_contract.json', dict(
        question='다른 donor의 정렬 누락 시행에서도 명령 기준 후세포 전압 변화가 자극 전 변동과 구별되는가?',
        selection='앞선 원파형 검사의 두 시행32,33, pair116053, 모든24 pulse; 누락4개도 제외하지 않음.',
        preparation='mouse donor581866, Allen experiment4251, VisP layer5; 단일 연결, 2시행.',
        biological_model='시냅스전 자극 뒤 시냅스후 전압 변화. 막전위 자체이며 시냅스 효능과 흥분성·입력저항·자발변동을 분리하지 못함.',
        ce_delta='없음. CE 추가항 시험이 아니라 연결 반응의 측정 적격성 개발 분석.',
        measurement='실제 명령 시작 기준 평균V[3,9)ms - 평균V[-8,-3)ms. sample index 반올림. 무필터·무적합. 모든 창 기록 내 포함 필수.',
        window_reason='앞선 발화 상대[2,8)ms 반응 창에 약1ms 자극-발화 지연을 반영한 개발용 고정 창. 이 전압을 보기 전에 고정하며 제작자 진폭과 다른 추정량.',
        controls='각 시행17개 고정 중심 .100+.025*i 초(i=0..16)에 동일 창; .08..53초 전후세포 명령 각각 상수 확인. 후세포 event 창에도 명령 변화 없어야 함.',
        decision='24개 부호·대조 평균 차이·대조 min/max 안 여부 보고. 34개 대조를 독립 동물로 세지 않으며 유의성/인과 기준 아님.',
        split='전체 개발 자료. 사후 누락 진단 계보이며 독립 확인 자료 아님.',
        limits='첫 자극과 회복 첫 자극 구분. 뒤 자극의 기준선에 이전 반응 혼입 가능. 첫 반응으로 나누지 않음. 누락 시각/기존 적합 대체 안 함. L1 기술 관측 상한, 통합사슬L0.',
        next_gate='부호와 대조를 검토하고 이 두 시행의 판별 한계를 기록. 결과를 본 뒤 창 조정 금지.',
        prior_sha256=sha(PRIOR), coverage_sha256=sha(COVERAGE), code_sha256=sha(Path(__file__))))
    raw.URL='https://allen-synphys.s3-us-west-2.amazonaws.com/synphys_r2.1_medium.sqlite'
    raw.CACHE=raw.ROOT/'data/external/allen_synphys_r21/medium_ranges'; raw.LIMIT=128*1024*1024
    with raw.CachedRanges() as reader:
        assert reader.remote==json.loads((HERE/'medium_recording_lookup_result.json').read_text(encoding='utf-8'))['remote']
        vfs=m.ReadVFS(reader); db=m.apsw.Connection('remote.sqlite',flags=m.apsw.SQLITE_OPEN_READONLY,vfs='ce_medium_readonly')
        try:
            bindings=[dict(zip(('recording','sweep','experiment','external','electrode','device','clamp_mode','qc_pass'),r)) for r in db.execute(
                'select r.id,s.ext_id,e.id,e.ext_id,el.id,el.device_id,p.clamp_mode,p.qc_pass from recording r '
                'join sync_rec s on s.id=r.sync_rec_id join experiment e on e.id=s.experiment_id '
                'join electrode el on el.id=r.electrode_id join patch_clamp_recording p on p.recording_id=r.id '
                'where r.id in (716325,716327) order by r.id')]
        finally:
            db.close(); vfs.unregister()
    assert len(bindings)==2
    assert all(b['experiment']==4251 and b['external']=='1623269658.635' and b['electrode']==33926 and b['clamp_mode']=='ic' for b in bindings)
    coverage=json.loads(COVERAGE.read_text(encoding='utf-8'))['records']
    for b in bindings:
        previous=next(a for a in prior['assets'] if a['binding']['sweep']==b['sweep'])
        rr=[r for r in coverage if r['response']['recording_id']==b['recording']]
        assert len(rr)==12 and all(r['stimulus']['recording_id']==previous['binding']['recording'] for r in rr)
    raw.URL=prior['assets'][0]['remote']['url']
    raw.CACHE=raw.ROOT/'data/external/allen_synphys_r21/raw_ranges/1623269658.635'
    assets=[]
    with raw.CachedRanges() as reader:
        assert reader.remote==prior['assets'][0]['remote']
        with h5py.File(reader,'r') as f:
            for b in bindings:
                sw=int(b['sweep']); dest=raw.CACHE/f'post_{sw}.npz'; receipt=dest.with_suffix('.json')
                if dest.exists() and receipt.exists():
                    meta=json.loads(receipt.read_text(encoding='utf-8'))
                    assert meta['binding']==b and sha(dest)==meta['sha256']; assets.append(meta); continue
                assert not dest.exists() and not receipt.exists()
                nodes=[]
                for group,unit in [('acquisition/timeseries','V'),('stimulus/presentation','A')]:
                    matches=[f[group][k] for k in f[group] if k.startswith(f'data_{sw:05d}_')
                             and 'electrode_name' in f[group][k] and txt(f[group][k]['electrode_name'][()][0])==f"electrode_{b['device']}"
                             and txt(f[group][k]['data'].attrs['unit'])==unit]
                    assert len(matches)==1; nodes.append(matches[0])
                prev=next(a for a in prior['assets'] if a['binding']['sweep']==b['sweep'])
                assert all(float(n['starting_time'][()][0])==prev['start_s'] and float(n['starting_time'].attrs['rate'])==prev['rate_hz'] for n in nodes)
                arrays=[np.asarray(n['data'][:],float)*float(n['data'].attrs['conversion'])+float(n['data'].attrs.get('offset',0)) for n in nodes]
                assert arrays[0].shape==arrays[1].shape and all(np.isfinite(a).all() for a in arrays)
                with dest.open('xb') as stream: np.savez_compressed(stream,voltage=arrays[0],current=arrays[1])
                meta=dict(binding=b,path=dest.relative_to(raw.ROOT).as_posix(),sha256=sha(dest),rate_hz=prev['rate_hz'],start_s=prev['start_s'],nodes=[n.name for n in nodes])
                with receipt.open('x',encoding='utf-8') as stream: json.dump(meta,stream,ensure_ascii=False,indent=2)
                assets.append(meta); print('POST_RAW_CACHED',sw,meta['nodes'],flush=True)
        new_bytes=reader.downloaded_this_session
        save(f'{PREFIX}_cache_snapshot.json',reader.manifest)
    analysis=analyze(assets,prior)
    save(f'{PREFIX}_result.json',dict(contract_sha256=sha(HERE/f'{PREFIX}_contract.json'),remote=prior['assets'][0]['remote'],new_nwb_bytes=new_bytes,analysis=analysis))
    print(json.dumps(dict(new_bytes=new_bytes,records=analysis['records'],controls=[{k:v for k,v in c.items() if k!='records'} for c in analysis['controls']]),ensure_ascii=True,indent=2))


if __name__=='__main__': main()
