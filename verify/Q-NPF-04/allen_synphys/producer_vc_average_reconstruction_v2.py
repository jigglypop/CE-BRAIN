"""보유 원파형에서 제작자 VC 평균을 재구성하고 저장 평균과 직접 비교한다."""
import argparse
import ast
import json
from pathlib import Path
from types import SimpleNamespace
import numpy as np
import medium_recording_lookup as m
from population_reciprocity import ROOT, sha
from reference_spike_audit import reference
from superficial_ee_eligibility import save

HERE = Path(__file__).resolve().parent
NAME = 'producer_vc_average_reconstruction_v2'


def read(name):
    return json.loads((HERE / name).read_text(encoding='utf-8'))


def reconstruct(starts):
    TSeries, _, _ = reference()
    from neuroanalysis.data import TSeriesList
    from neuroanalysis.baseline import float_mode
    source = HERE / 'qc_sources/multipatch_data.py'
    tree = ast.parse(source.read_text(encoding='utf-8'))
    node = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'PulseResponseList')
    ns = dict(np=np, TSeriesList=TSeriesList, float_mode=float_mode)
    exec(compile(ast.Module(body=[node], type_ignores=[]), str(source), 'exec'), ns)
    membership = read('producer_average_membership_result.json')
    inventory = read('next_donor_recording_inventory_result.json')['pairs'][0]['records']
    assets = read('next_donor_vc_response_result.json')['assets']
    records = {r['post']['id']: r for r in inventory}
    traces = {}
    for a in assets:
        assert sha(ROOT / a['path']) == a['sha256']
        with np.load(ROOT / a['path'], allow_pickle=False) as f:
            traces[a['post_recording']] = TSeries(f['post_current'], sample_rate=a['rate_hz'], t0=0)
    results = []
    arrays = {}
    for stored in membership['averages']:
        if stored['clamp_mode'] != 'vc':
            continue
        group = stored['group']
        ids = membership['membership']['included'][group]
        prs = []
        windows = []
        for rid in ids:
            row = starts[str(rid)]
            record = records[row['recording_id']]
            pulses = sorted(record['pulses'], key=lambda p: p['onset_time'])
            i = next(i for i, p in enumerate(pulses) if p['response_id'] == rid)
            p = pulses[i]
            trace = traces[row['recording_id']]
            start = max(trace.t0, p['onset_time'] - .010)
            stop = start + .050
            if i + 1 < len(pulses):
                stop = min(stop, pulses[i + 1]['onset_time'])
            down = trace.time_slice(start, stop).resample(sample_rate=20000)
            delta = float(down.t0 - row['data_start_time'])
            # 저장된 시각을 사용하는 DB schema의 post_tseries와 같은 입력을 만든다.
            prs.append(SimpleNamespace(post_tseries=down.copy(t0=row['data_start_time']),
                stim_pulse=SimpleNamespace(onset_time=p['onset_time'], first_spike_time=p['first_spike_time'])))
            windows.append(dict(response_id=rid, samples=len(down), start_delta_s=delta))
        avg = ns['PulseResponseList'](prs).post_tseries(align='spike', bsub=True).mean()
        assert sha(ROOT / stored['array_path']) == stored['array_sha256']
        expected = np.load(ROOT / stored['array_path'], allow_pickle=False)
        same_shape = avg.data.shape == expected.shape
        same_time = abs(avg.t0 - stored['avg_data_start_time']) <= 1e-12
        starts_match = all(abs(w['start_delta_s']) <= 1e-12 for w in windows)
        metrics = None
        equal = False
        if same_shape and same_time:
            error = avg.data - expected
            equal = bool(np.allclose(avg.data, expected, atol=1e-14, rtol=1e-3))
            metrics = dict(max_abs_error_pa=float(np.max(np.abs(error)) * 1e12),
                rmse_pa=float(np.sqrt(np.mean(error**2)) * 1e12),
                within_tolerance=int(np.count_nonzero(np.isclose(avg.data, expected, atol=1e-14, rtol=1e-3))))
        arrays[group] = avg.data
        results.append(dict(group=group, count=len(prs), stored_count=stored['n_averaged_responses'],
            samples=len(avg.data), stored_samples=len(expected), t0=float(avg.t0),
            stored_t0=stored['avg_data_start_time'], same_shape=same_shape, same_time=bool(same_time),
            starts_match=starts_match, waveform_match=equal, metrics=metrics, windows=windows,
            passed=bool(same_shape and same_time and starts_match and equal)))
    return results, arrays


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    inputs = ['producer_average_membership_result.json', 'next_donor_recording_inventory_result.json',
              'next_donor_vc_response_result.json', 'qc_sources/multipatch_data.py',
              'qc_sources/dataset_pipeline.py', 'reference_spike_audit.py']
    if args.verify:
        contract = read(f'{NAME}_contract.json')
        assert contract['code_sha256'] == sha(Path(__file__))
        for name, digest in contract['inputs'].items():
            assert sha(HERE / name) == digest
        result = read(f'{NAME}_result.json')
        assert result['contract_sha256'] == sha(HERE / f'{NAME}_contract.json')
        groups, arrays = reconstruct(result['starts'])
        assert groups == result['groups']
        for group, values in arrays.items():
            path = HERE / result['arrays'][group]['path']
            assert sha(path) == result['arrays'][group]['sha256']
            assert np.array_equal(values, np.load(path, allow_pickle=False))
        print('PRODUCER_VC_AVERAGE_REPRODUCTION_VERIFIED')
        return
    save(f'{NAME}_contract.json', dict(
        supersedes='v1은 NWB 세션 시각을 시행 내부 DB 시각에 그대로 적용해 첫 절단에서 IndexError. 파형 비교 전 중단. v2는 시행 시작을 0으로 둔다. 원 계약·코드는 보존하고 비교 기준은 유지한다.',
        question='pair121538의 VC 두 조건에서 원파형으로 제작자 저장 평균을 재현할 수 있는가?',
        objective='신경 연결 추론의 측정모형을 점검한다. 뇌 전체 구조나 인과기전 확정이 아니다.',
        selection='기존 제작자 평균 선택 후보 각 60개 전부. 결과에 따른 제외 없음.',
        method='명령 onset-10ms부터 최대50ms/다음명령까지 절단, 20kHz resample, DB 시작시각, 제작자 PulseResponseList 기준선·발화정렬·mean.',
        gate='분모·shape 일치, 시작시각 오차<=1e-12초, 모든 샘플 atol1e-14A+rtol1e-3. 재정렬·추가 기준선 보정 없음.',
        limits='고정한 공개 소스 판본을 사용한다. 역사적 제작 환경과 동일함은 미확인. 실패는 보존하며 연결 부재로 해석하지 않는다. L0 측정 진단.',
        code_sha256=sha(Path(__file__)), inputs={n: sha(HERE / n) for n in inputs}))
    remote = read('medium_recording_lookup_result.json')['remote']
    raw = m.raw
    raw.URL = remote['url']
    raw.CACHE = ROOT / 'data/external/allen_synphys_r21/medium_ranges'
    raw.LIMIT = 128 * 1024 * 1024
    with raw.CachedRanges() as reader:
        assert reader.remote == remote
        vfs = m.ReadVFS(reader)
        db = m.apsw.Connection('remote.sqlite', flags=m.apsw.SQLITE_OPEN_READONLY, vfs='ce_medium_readonly')
        try:
            rows = list(db.execute('select pr.id,pr.recording_id,pr.data_start_time from pulse_response pr '
                'join patch_clamp_recording pc on pc.recording_id=pr.recording_id '
                "where pr.pair_id=121538 and pc.clamp_mode='vc' order by pr.id"))
        finally:
            db.close()
            vfs.unregister()
        new_bytes = reader.downloaded_this_session
    starts = {str(r[0]): dict(recording_id=r[1], data_start_time=r[2]) for r in rows}
    assert len(starts) == 120
    groups, arrays = reconstruct(starts)
    paths = {}
    for group, values in arrays.items():
        path = HERE / f'{NAME}_{group}.npy'
        with path.open('xb') as f:
            np.save(f, values, allow_pickle=False)
        paths[group] = dict(path=path.name, sha256=sha(path))
    save(f'{NAME}_result.json', dict(contract_sha256=sha(HERE / f'{NAME}_contract.json'),
        remote=remote, new_bytes=new_bytes, starts=starts, groups=groups, arrays=paths))
    print(json.dumps(dict(new_bytes=new_bytes, groups=[{k: v for k, v in g.items() if k != 'windows'} for g in groups]), indent=2))


if __name__ == '__main__':
    main()
