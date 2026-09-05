"""사전에 고정한 추가 20개 시행의 첫 자극 비교. 같은 실험의 반복 관측."""
import argparse
import json
import platform
import sys
from pathlib import Path
import h5py
import numpy as np
from raw_metadata import CachedRanges, CACHE
from reference_spike_audit import reference, sha, clean
from ic_pair_comparison import fixtures

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
CONTRACT = HERE / 'ic_extension_first_contract.json'
OUTPUT = HERE / 'ic_extension_first_result.json'
INVENTORY = HERE / 'ic_extended_inventory_result.json'
ARCHIVE = CACHE / 'ic_extension_first_windows.npz'


def normalized(value):
    return json.loads(json.dumps(clean(value), allow_nan=False))


def evaluate(arrays, selected, TSeries, detector):
    rows = []
    for sweep in selected:
        sw = sweep['sweep']; fs = sweep['nodes']['pre']['rate']
        pre = arrays[f'{sw}_pre']; command = arrays[f'{sw}_command']
        t = np.arange(len(pre))/fs - .01
        height = command.max()-command[t < -.003].mean()
        active = np.flatnonzero(command-command[t < -.003].mean() > height/2)
        assert len(active)>1 and np.all(np.diff(active)==1)
        spikes = detector(TSeries(pre, dt=1/fs, t0=-.01, units='V'),
                          (float(t[active[0]]), float(t[active[-1]]+1/fs)))
        row = dict(sweep=sw, command_pA=float(height*1e12), spikes=spikes, responses={}, local_quality={})
        for target in ('positive','negative'):
            v = arrays[f'{sw}_{target}']; base = v[:round(.005*fs)]
            median = float(np.median(base)); sd = float(base.std())
            maximum = float(v.max()); excursion = float(np.max(np.abs(v-median)))
            row['local_quality'][target] = dict(baseline_mV=median*1000, baseline_sd_uV=sd*1e6,
                local_violation=bool(sd>.0015 or maximum>-.04 or excursion>.01 or not -.085<median<-.05))
        if len(spikes)==1 and spikes[0]['max_slope_time'] is not None:
            center = float(spikes[0]['max_slope_time'])
            assert np.isfinite(center) and center-.009>=t[0] and center+.008<t[-1]
            for target in ('positive','negative'):
                v = arrays[f'{sw}_{target}']
                def mean(lo,hi): return float(np.interp(center+np.arange(lo,hi,1/fs),t,v).mean())
                row['responses'][target] = dict(voltage_change_uV=(mean(.002,.008)-mean(-.008,-.003))*1e6,
                    pre_event_control_uV=(mean(-.007,-.002)-mean(-.009,-.007))*1e6)
            row['difference_uV'] = row['responses']['positive']['voltage_change_uV']-row['responses']['negative']['voltage_change_uV']
        rows.append(row)
    usable = [r for r in rows if r['responses']]
    summary = dict(total=len(rows), usable=len(usable), excluded_for_spike_count_or_time=len(rows)-len(usable),
        local_violation_windows=sum(q['local_violation'] for r in rows for q in r['local_quality'].values()))
    if usable:
        diff = np.array([r['difference_uV'] for r in usable])
        summary.update(difference_mean_uV=float(diff.mean()), difference_median_uV=float(np.median(diff)),
            difference_range_uV=[float(diff.min()),float(diff.max())], positive_differences=int((diff>0).sum()),
            negative_differences=int((diff<0).sum()),
            chronological_groups=[dict(sweeps=[r['sweep'] for r in usable if lo<=r['sweep']<=hi],
                mean_difference_uV=float(np.mean([r['difference_uV'] for r in usable if lo<=r['sweep']<=hi])))
                for lo,hi in ((37,41),(42,46),(47,51),(52,56)) if any(lo<=r['sweep']<=hi for r in usable)])
        for target in ('positive','negative'):
            summary[target] = {key:float(np.mean([r['responses'][target][key] for r in usable]))
                               for key in ('voltage_change_uV','pre_event_control_uV')}
    return normalized(dict(records=rows, summary=summary))


def main():
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument('--verify',action='store_true')
    args=parser.parse_args()
    inventory=json.loads(INVENTORY.read_text(encoding='utf-8'))
    selected=[s for s in inventory['selected'] if 37<=s['sweep']<=56]
    assert [s['sweep'] for s in selected]==list(range(37,57))
    TSeries,_,manifest=reference()
    from neuroanalysis.spike_detection import detect_ic_evoked_spikes as detector
    checks=fixtures(TSeries,detector)
    spec=dict(question='동일 실험 추가 시행에서 양성-음성 첫 자극 반응 차이가 반복되는가?',
        scope='BIO_EVIDENCE_L1; 같은 전세포/실험, 저자 연결 표지 기지; 독립 생물 표본이나 전체 뇌 구조 확정 아님',
        selection='메타데이터 후보37..56 전부, 첫pulse만. 이미 분석한32..36 제외. 반응값으로 제외하지 않음.',
        primary='spike+[2,8)ms minus[-8,-3)ms: 표적5-표적3. 기존 창 유지.',
        control='spike[-7,-2)ms minus[-9,-7)ms; 사후 차감 없음.',
        decision='평균/중앙값/부호 수/범위 및 시간순5개씩 네 묶음 기술. 일반화 검정이나 연결 확정 없음.',
        quality='국소 품질 항목 기록만, 사후 제외 없음. 전체 기록 품질 미검증 상태로 명시.',
        missing='full-recording QC, producer pulse IDs/windows, access resistance, independent spike truth, causal specificity',
        detector='upstream IC defaults; exactly1 candidate and finite max_slope_time for response; missing recorded',
        inventory_sha256=sha(INVENTORY), code_sha256=sha(Path(__file__)),
        upstream_commit=manifest['commit'], source_manifest_sha256=sha(ROOT/'data/external/analysis_tools/neuroanalysis_source/source_manifest.json'),
        fixtures=checks, runtime=dict(python=platform.python_version(),executable=sys.executable,numpy=np.__version__))
    if CONTRACT.exists():
        assert spec==json.loads(CONTRACT.read_text(encoding='utf-8'))
    elif args.verify: raise RuntimeError('계약 없음')
    else:
        with CONTRACT.open('x',encoding='utf-8') as stream: json.dump(spec,stream,ensure_ascii=False,indent=2)
    if args.verify:
        result=json.loads(OUTPUT.read_text(encoding='utf-8'))
        assert sha(CONTRACT)==result['contract_sha256'] and sha(ARCHIVE)==result['arrays_sha256']
        with np.load(ARCHIVE,allow_pickle=False) as arrays:
            assert len(arrays.files)==80
            assert evaluate(arrays,selected,TSeries,detector)==result['analysis']
        print('EXTENSION_REPRODUCED_FROM_80_LOCAL_ARRAYS');return
    if OUTPUT.exists(): raise RuntimeError('기존 결과 보존')
    arrays={}
    with CachedRanges() as reader:
        with h5py.File(reader,'r') as f:
            for sweep in selected:
                sw=sweep['sweep'];fs=sweep['nodes']['pre']['rate'];mid=round(sweep['onset_times_s'][0]*fs)
                for label,node in dict(sweep['nodes'],command=sweep['command']).items():
                    ds=f[node['path']+'/data']
                    v=np.array(ds[mid-round(.01*fs):mid+round(.012*fs)],dtype=float)*float(ds.attrs['conversion'])
                    assert len(v)==round(.022*fs) and np.isfinite(v).all()
                    arrays[f'{sw}_{label}']=v
                print('extracted first pulse',sw,flush=True)
        new_bytes=reader.downloaded_this_session
    if ARCHIVE.exists():
        with np.load(ARCHIVE,allow_pickle=False) as saved:
            assert set(saved.files)==set(arrays) and all(np.array_equal(saved[k],v) for k,v in arrays.items())
    else:
        with ARCHIVE.open('xb') as stream: np.savez_compressed(stream,**arrays)
    result=dict(contract_sha256=sha(CONTRACT),arrays_sha256=sha(ARCHIVE),new_bytes=new_bytes,
                analysis=evaluate(arrays,selected,TSeries,detector))
    with OUTPUT.open('x',encoding='utf-8') as stream: json.dump(result,stream,ensure_ascii=False,indent=2,allow_nan=False)
    print(json.dumps(result['analysis']['summary'],ensure_ascii=False,indent=2))


if __name__=='__main__': main()
