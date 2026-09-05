"""고정 upstream 검출기로 원본 VC spike 후보를 확인한다. 별도 전압 ground truth는 없다."""
import argparse
import hashlib
import json
import platform
import sys
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
import numpy as np
import scipy

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
SOURCE=ROOT/'data/external/analysis_tools/neuroanalysis_source'


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def reference():
    manifest=json.loads((SOURCE/'source_manifest.json').read_text(encoding='utf-8'))
    for path,digest in manifest['files'].items():assert sha(SOURCE/path)==digest
    # NumPy2 removed this name; the composite trapezoid operation is unchanged.
    if not hasattr(np,'trapz'):np.trapz=np.trapezoid
    sys.path.insert(0,str(SOURCE))
    from neuroanalysis.data import TSeries
    from neuroanalysis.spike_detection import detect_vc_evoked_spikes
    assert Path(sys.modules['neuroanalysis.spike_detection'].__file__).resolve().is_relative_to(SOURCE.resolve())
    return TSeries,detect_vc_evoked_spikes,manifest


def fixture_tests(TSeries,detector):
    fs=100000;t=np.arange(2000)/fs-.01
    cap=np.zeros_like(t);mask=(t>=0)&(t<.0015)
    cap[mask]=2e-9*np.exp(-t[mask]/.00005)
    tests={}
    for name,y in [('flat',np.zeros_like(t)),('capacitive_only',cap),
                   ('spike_fixture',cap-1e-9*np.exp(-.5*((t-.00065)/.00008)**2))]:
        calls=detector(TSeries(y,dt=1/fs,t0=-.01,units='A'),(0,.0015))
        tests[name]=len(calls)
    assert tests=={'flat':0,'capacitive_only':0,'spike_fixture':1}
    x=np.array([0.,.3,1.]);y=np.array([2.,-1.,4.])
    assert np.isclose(np.trapz(y,x),np.sum(np.diff(x)*(y[1:]+y[:-1])/2))
    return tests


def clean(value):
    if isinstance(value,dict):return {k:clean(v) for k,v in value.items()}
    if isinstance(value,list):return [clean(v) for v in value]
    if isinstance(value,np.generic):return value.item()
    return value


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--self-test',action='store_true')
    args=parser.parse_args()
    TSeries,detector,manifest=reference()
    fixtures=fixture_tests(TSeries,detector)
    if args.self_test:
        print('REFERENCE_FIXTURES_PASS',fixtures);return
    output=HERE/'reference_spike_audit_result.json'
    contract=HERE/'reference_spike_audit_contract.json'
    if output.exists() or contract.exists():raise RuntimeError('기존 검출 검사 기록을 보존합니다.')
    old=json.loads((HERE/'raw_pulse_windows_result.json').read_text(encoding='utf-8'))
    archive=ROOT/old['array_archive']
    assert sha(archive)==old['array_sha256']
    spec={'frozen_at':datetime.now(timezone.utc).isoformat(),'question':'원 명령에서 전세포 spike 후보가 검출되는지, 그 시각 기준으로 후세포 전류가 어떠한지',
          'kind':'POST_RESULT_REFERENCE_DETECTOR_AUDIT','upstream_commit':manifest['commit'],
          'source_manifest_sha256':sha(SOURCE/'source_manifest.json'),'code_sha256':sha(Path(__file__)),
          'array_sha256':sha(archive),'previous_result_sha256':sha(HERE/'raw_pulse_windows_result.json'),
          'runtime':{'python':platform.python_version(),'executable':sys.executable,'numpy':np.__version__,'scipy':scipy.__version__},
          'compatibility':'Only in-process np.trapz=np.trapezoid when absent; no upstream source edits. Trapezoid formula fixture verified.',
          'scope':'모든 보유 60 pulse, 임의 제외 없음. 고정 source의 detect_vc_evoked_spikes 기본값. 검출기는 VC pulse 안의 unclamped spike를 가정한다. 과거 DB producer commit과 동일성 미확인.',
          'edges':'실제 command의 baseline 대비 양의 peak 절반을 넘는 연속 pulse 첫/끝 sample. 물리적 spike detector threshold는 수정하지 않음.',
          'negative_control':'각 보유 pre trace의[-6,-4.5]ms 기준선 구간에 같은 검출기를 적용. 생물학적 거짓양성률의 보편 추정 아님.',
          'alignment':'정확히1개이고 max_slope_time 유한한 후보만 진단창 요약; 제외건수 기록. 후세포 baseline[-8,-3)ms, response[1,5)ms는 max_slope 상대시간; interpolation100kHz; 후세포값으로 선택하지 않음.',
          'summary':'60/120mV dose를 구분. 표준 source의 peak_value는 사용하지 않음. 추정 onset/max_slope/peak_time만 기록.',
          'ceiling':'Spike 후보와 원본 전류의 L1 기술적 관측. 단일시냅스 인과, 연결 부재, 원 spike QC 또는 원 평균 재현을 확정하지 않음.'}
    contract.write_text(json.dumps(spec,ensure_ascii=False,indent=2),encoding='utf-8')
    records=[]
    with np.load(archive,allow_pickle=False) as arrays:
        for sweep in old['records']:
            fs=sweep['rate_hz']
            for event in sweep['events']:
                prefix=f'sweep{sweep["sweep"]}_pulse{event["pulse"]}'
                pre=arrays[prefix+'_pre'];post=arrays[prefix+'_post'];command=arrays[prefix+'_command']
                t=np.arange(len(pre))/fs-.01
                baseline=command[t<-.003].mean();height=command.max()-baseline
                on=np.flatnonzero(command-baseline>height/2)
                assert len(on)>1 and np.all(np.diff(on)==1)
                edges=(float(t[on[0]]),float(t[on[-1]]+1/fs))
                trace=TSeries(pre,dt=1/fs,t0=-.01,units='A')
                candidates=detector(trace,edges)
                control=detector(trace,(-.006,-.0045))
                row={'sweep':sweep['sweep'],'pulse':event['pulse'],'dose_mV':float(height*1e3),
                     'edges_s':edges,'candidates':[{k:v for k,v in c.items() if k!='peak_value'} for c in candidates],
                     'control_candidates':len(control),'aligned_response_pA':None}
                if len(candidates)==1 and candidates[0]['max_slope_time'] is not None:
                    center=float(candidates[0]['max_slope_time'])
                    assert np.isfinite(center) and center-.008>=t[0] and center+.005<=t[-1]
                    baseline=np.interp(center+np.arange(-.008,-.003,1/fs),t,post).mean()
                    response=np.interp(center+np.arange(.001,.005,1/fs),t,post).mean()
                    row['aligned_response_pA']=float((response-baseline)*1e12)
                    row['max_slope_after_command_ms']=(center-edges[0])*1e3
                records.append(clean(row))
    summary={}
    for dose in [60,120]:
        rows=[r for r in records if round(r['dose_mV'])==dose]
        responses=[r['aligned_response_pA'] for r in rows if r['aligned_response_pA'] is not None]
        lags=[r['max_slope_after_command_ms'] for r in rows if 'max_slope_after_command_ms' in r]
        first=[r['aligned_response_pA'] for r in rows if r['pulse']==1 and r['aligned_response_pA'] is not None]
        later=[r['aligned_response_pA'] for r in rows if 2<=r['pulse']<=8 and r['aligned_response_pA'] is not None]
        summary[str(dose)]={'pulses':len(rows),'candidate_count_histogram':dict(Counter(len(r['candidates']) for r in rows)),
            'control_candidate_count':sum(r['control_candidates'] for r in rows),'aligned_pulses':len(responses),
            'lag_ms_quantiles':np.quantile(lags,[0,.5,1]).tolist() if lags else None,
            'mean_current_pA':float(np.mean(responses)) if responses else None,
            'first_mean_current_pA':float(np.mean(first)) if first else None,
            'later2to8_mean_current_pA':float(np.mean(later)) if later else None}
    result={'contract_sha256':sha(contract),'fixtures':fixtures,'records':records,'summary':summary}
    output.write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
    print(json.dumps(summary,indent=2))


if __name__=='__main__':main()
