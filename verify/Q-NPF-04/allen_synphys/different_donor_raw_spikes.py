"""다른 donor의 정렬 누락 4건과 같은 기록의 나머지 20건을 원파형으로 대조한다."""
import json
from pathlib import Path
import h5py
import numpy as np
import medium_recording_lookup as m
import raw_metadata as raw
from reference_spike_audit import reference, sha, clean
from superficial_ee_eligibility import save

HERE = Path(__file__).resolve().parent
EXT = '1623269658.635'
COVERAGE = HERE / 'different_donor_fit_coverage_result.json'


def txt(value):
    return value.decode() if isinstance(value, bytes) else str(value)


def main():
    TSeries, _, manifest = reference()
    import neuroanalysis.spike_detection as sd
    save('different_donor_raw_spikes_contract.json', {
        'question': '누락된 max-slope 정렬 4건이 고정 검출기의 파형 경계 판정과 일치하는가?',
        'selection': '기존 coverage의 전세포 기록 716326,716328 전체 24 pulse. 누락 4건과 나머지 20건; 제외 없음.',
        'method': 'DB recording→sync→experiment 및 electrode→device 결박. NWB electrode_name으로 전압과 명령을 선택. 양의 명령 peak 절반 경계, 12 pulse와 DB onset 1 sample 이내 확인.',
        'detector': '고정 neuroanalysis IC 기본값; actual onset [-10,+12)ms. max_time 호출 결과를 감싸 기록하되 입력·출력·threshold는 변경하지 않음.',
        'decision': '후보 수, max-slope 존재, DB 시각 차이, max_time 경계 반환을 전부 보고. 불일치는 보존.',
        'limits': '사후 원인 진단. 원 생산 환경 동일성 및 독립 spike ground truth 없음. 인과·뇌 구조·CE 증거 승격 아님.',
        'coverage_sha256': sha(COVERAGE), 'source_manifest': manifest,
        'code_sha256': sha(Path(__file__)), 'reader_sha256': sha(Path(raw.__file__))})
    selected = [r for r in json.loads(COVERAGE.read_text(encoding='utf-8'))['records']
                if r['stimulus']['recording_id'] in (716326, 716328)]
    assert len(selected) == 24
    raw.URL = 'https://allen-synphys.s3-us-west-2.amazonaws.com/synphys_r2.1_medium.sqlite'
    raw.CACHE = raw.ROOT / 'data/external/allen_synphys_r21/medium_ranges'
    raw.LIMIT = 128 * 1024 * 1024
    with raw.CachedRanges() as reader:
        prior = json.loads((HERE / 'medium_recording_lookup_result.json').read_text(encoding='utf-8'))
        assert reader.remote == prior['remote']
        vfs = m.ReadVFS(reader)
        db = m.apsw.Connection('remote.sqlite', flags=m.apsw.SQLITE_OPEN_READONLY, vfs='ce_medium_readonly')
        try:
            bindings = [dict(zip(('recording', 'sweep', 'experiment', 'external', 'electrode', 'device'), r)) for r in db.execute(
                'select r.id,s.ext_id,e.id,e.ext_id,el.id,el.device_id from recording r '
                'join sync_rec s on s.id=r.sync_rec_id join experiment e on e.id=s.experiment_id '
                'join electrode el on el.id=r.electrode_id where r.id in (716326,716328) order by r.id')]
        finally:
            db.close()
            vfs.unregister()
    assert len(bindings) == 2
    assert all(b['experiment'] == 4251 and b['external'] == EXT and b['device'] == 5 for b in bindings)
    raw.URL = f'https://allen-synphys.s3-us-west-2.amazonaws.com/synphys-{EXT}.nwb'
    raw.CACHE = raw.ROOT / f'data/external/allen_synphys_r21/raw_ranges/{EXT}'
    assets = []
    with raw.CachedRanges() as reader:
        with h5py.File(reader, 'r') as f:
            for binding in bindings:
                sweep = int(binding['sweep'])
                dest = raw.CACHE / f'pre_{sweep}.npz'
                receipt = dest.with_suffix('.json')
                if dest.exists() and receipt.exists():
                    meta = json.loads(receipt.read_text(encoding='utf-8'))
                    assert sha(dest) == meta['sha256'] and meta['binding'] == binding
                    assets.append(meta)
                    continue
                assert not dest.exists() and not receipt.exists(), '불완전 파일은 덮어쓰지 않음'
                groups = [f['acquisition/timeseries'], f['stimulus/presentation']]
                nodes = []
                for group, unit in zip(groups, ('V', 'A')):
                    matches = [group[k] for k in group if k.startswith(f'data_{sweep:05d}_')
                               and 'electrode_name' in group[k]
                               and txt(group[k]['electrode_name'][()][0]) == 'electrode_5'
                               and txt(group[k]['data'].attrs['unit']) == unit]
                    assert len(matches) == 1, [n.name for n in matches]
                    nodes.append(matches[0])
                rates = [float(n['starting_time'].attrs['rate']) for n in nodes]
                starts = [float(n['starting_time'][()][0]) for n in nodes]
                assert rates[0] == rates[1] and starts[0] == starts[1]
                arrays = [np.asarray(n['data'][:], dtype=float) * float(n['data'].attrs['conversion'])
                          + float(n['data'].attrs.get('offset', 0)) for n in nodes]
                assert arrays[0].shape == arrays[1].shape and all(np.isfinite(a).all() for a in arrays)
                with dest.open('xb') as stream:
                    np.savez_compressed(stream, voltage=arrays[0], current=arrays[1])
                meta = dict(binding=binding, path=dest.relative_to(raw.ROOT).as_posix(), sha256=sha(dest),
                            nodes=[n.name for n in nodes], rate_hz=rates[0], start_s=starts[0], remote=reader.remote)
                with receipt.open('x', encoding='utf-8') as stream:
                    json.dump(meta, stream, ensure_ascii=False, indent=2)
                assets.append(meta)
                print('원파형 확보', sweep, meta['nodes'], flush=True)
        new_bytes = reader.downloaded_this_session
    rows = []
    original = sd.max_time
    for asset in assets:
        assert sha(raw.ROOT / asset['path']) == asset['sha256']
        with np.load(raw.ROOT / asset['path'], allow_pickle=False) as z:
            voltage, command = z['voltage'], z['current']
        fs = asset['rate_hz']
        active = command > command.max() / 2
        starts = np.flatnonzero(np.diff(active.astype(int), prepend=0) == 1)
        stops = np.flatnonzero(np.diff(active.astype(int), append=0) == -1) + 1
        assert len(starts) == len(stops) == 12
        rr = sorted([r for r in selected if r['stimulus']['recording_id'] == asset['binding']['recording']],
                    key=lambda r: r['stimulus']['pulse_number'])
        assert [r['stimulus']['pulse_number'] for r in rr] == list(range(12))
        for r, a, b in zip(rr, starts, stops):
            assert abs(a / fs - r['stimulus']['onset_time']) <= 1 / fs + 1e-9
            left, right = a - round(.01 * fs), a + round(.012 * fs)
            assert 0 <= left < right <= len(voltage)
            trace = TSeries(voltage[left:right], dt=1 / fs, t0=-.01, units='V')
            calls = []
            def traced(chunk):
                time, edge = original(chunk)
                calls.append(dict(start=float(chunk.t0), samples=len(chunk), time=float(time), edge=int(edge)))
                return time, edge
            sd.max_time = traced
            try:
                spikes = sd.detect_ic_evoked_spikes(trace, (0, (b-a)/fs))
            finally:
                sd.max_time = original
            # 包装が結果を変えないことを同じ入力で照合する。
            plain = sd.detect_ic_evoked_spikes(trace, (0, (b-a)/fs))
            assert clean(spikes) == clean(plain)
            aligned = len(spikes) == 1 and spikes[0]['max_slope_time'] is not None
            expected = r['stimulus']['first_spike_time']
            rows.append(dict(sweep=int(asset['binding']['sweep']), stimulus=r['stimulus'],
                actual_onset_s=float(a/fs), duration_s=float((b-a)/fs), spikes=clean(spikes), max_time_calls=calls,
                aligned=aligned, missing_matches=(expected is None) == (not aligned),
                delta_us=float((a/fs+spikes[0]['max_slope_time']-expected)*1e6) if aligned and expected is not None else None))
    result = dict(contract_sha256=sha(HERE/'different_donor_raw_spikes_contract.json'), assets=assets, records=rows,
        summary=dict(total=len(rows), db_missing=sum(r['stimulus']['first_spike_time'] is None for r in rows),
                     detected_missing=sum(not r['aligned'] for r in rows), missing_pattern_matches=sum(r['missing_matches'] for r in rows)),
        new_nwb_bytes=new_bytes, ceiling='L0 측정 누락 진단; 통합 생물학 인과사슬은 미확립')
    save('different_donor_raw_spikes_result.json', result)
    print(json.dumps(result['summary'], ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
