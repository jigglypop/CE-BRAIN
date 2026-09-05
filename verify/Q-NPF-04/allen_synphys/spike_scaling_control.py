"""검출 결과를 본 뒤의 선형 배율 대조. 실제 자극 개입이나 독립 확인은 아니다."""
import json
from collections import Counter
from pathlib import Path
import numpy as np
from reference_spike_audit import reference,sha

HERE=Path(__file__).resolve().parent


def main():
    output=HERE/'spike_scaling_control_result.json'
    if output.exists():raise RuntimeError('기존 배율 대조 보존')
    TSeries,detector,manifest=reference()
    previous=json.loads((HERE/'reference_spike_audit_result.json').read_text(encoding='utf-8'))
    raw=json.loads((HERE/'raw_pulse_windows_result.json').read_text(encoding='utf-8'))
    archive=HERE.parents[2]/raw['array_archive']
    assert sha(archive)==raw['array_sha256']
    tests=[]
    with np.load(archive,allow_pickle=False) as arrays:
        for row in previous['records']:
            sw=row['sweep'];pulse=row['pulse'];dose=round(row['dose_mV'])
            y=arrays[f'sweep{sw}_pulse{pulse}_pre']
            fs=next(x['rate_hz'] for x in raw['records'] if x['sweep']==sw)
            baseline=y[:round(.007*fs)].mean()
            factor=2 if dose==60 else .5
            changed=baseline+factor*(y-baseline)
            calls=detector(TSeries(changed,dt=1/fs,t0=-.01,units='A'),tuple(row['edges_s']))
            tests.append({'sweep':sw,'pulse':pulse,'original_dose_mV':dose,'offline_scale':factor,'candidates':len(calls)})
    result={'kind':'POST_RESULT_LINEAR_SCALING_CONTROL','question':'단순 선형 진폭 배율만으로 검출의 dose 차이가 재현되는가?',
        'limits':'디지털 파형 변환이며 실제 전압 자극 변화의 결과가 아니다. 비선형 이온 전류·clamp 탈출과 실제 AP의 구별을 단독 증명하지 못한다.',
        'code_sha256':sha(Path(__file__)),'previous_result_sha256':sha(HERE/'reference_spike_audit_result.json'),
        'upstream_commit':manifest['commit'],'array_sha256':sha(archive),'tests':tests,
        'summary':{str(d):dict(Counter(r['candidates'] for r in tests if r['original_dose_mV']==d)) for d in (60,120)}}
    output.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result['summary'],indent=2))


if __name__=='__main__':main()
