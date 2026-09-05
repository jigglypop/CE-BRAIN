"""TSeries.t_end의 마지막 표본 시각을 반영한 기준선 경계 교정. 원 결과 보존."""
import copy
import json
from pathlib import Path
import numpy as np
from ic_full_recording_qc import HERE, META, INV, STORE, OUTPUT, measure
from reference_spike_audit import reference,sha

DEST=HERE/'ic_baseline_endpoint_result.json'


def audit():
    TSeries,_,_=reference()
    from neuroanalysis.baseline import float_mode
    prior=json.loads(OUTPUT.read_text(encoding='utf-8'))
    metadata=json.loads(META.read_text(encoding='utf-8'))
    inventory=json.loads(INV.read_text(encoding='utf-8'))
    rows=[]
    for row in metadata['rows']:
        sw=row['sweep'];target=row['target']
        node=next(s for s in inventory['selected'] if s['sweep']==sw)['nodes'][target]
        path=STORE/f'{sw}_{target}.npz'
        old=next(r for r in prior['analysis']['records'] if r['sweep']==sw and r['target']==target)
        assert sha(path)==old['array_sha256']
        with np.load(path,allow_pickle=False) as data:v=data['voltage']
        trace=TSeries(v,sample_rate=node['rate'],t0=0,units='V')
        corrected=copy.deepcopy(row);tail=row['fields']['Delay termination']/1000
        corrected['notebook_baseline_regions_s'][-1]=[float(trace.t_end-tail),float(trace.t_end)]
        for a,b in corrected['notebook_baseline_regions_s']:
            assert np.array_equal(trace.time_slice(a,b).data,v[round(a*node['rate']):round(b*node['rate'])])
        new=measure(v,corrected,node,float_mode)
        rows.append(dict(sweep=sw,target=target,corrected_regions_s=corrected['notebook_baseline_regions_s'],
            corrected_measurement=new,baseline_delta_uV=(new['baseline_mV']-old['baseline_mV'])*1000,
            noise_delta_uV=new['baseline_sd_uV']-old['baseline_sd_uV'],
            pass_changed=new['reconstructed_recording_pass']!=old['reconstructed_recording_pass']))
    return dict(reason='Previous metadata used n/fs end; pinned TSeries.t_end=(n-1)/fs. Tail window shifted earlier by one sample (10us).',
        timing='source boundary correction; original contract and output preserved',
        source_result_sha256=sha(OUTPUT),code_sha256=sha(Path(__file__)),
        corrected_passed=sum(r['corrected_measurement']['reconstructed_recording_pass'] for r in rows),total=len(rows),
        changed_passes=sum(r['pass_changed'] for r in rows),
        max_abs_baseline_delta_uV=max(abs(r['baseline_delta_uV']) for r in rows),
        max_abs_noise_delta_uV=max(abs(r['noise_delta_uV']) for r in rows),records=rows)


if __name__=='__main__':
    result=audit()
    if DEST.exists():
        assert result==json.loads(DEST.read_text(encoding='utf-8'));print('ENDPOINT_CORRECTION_REPRODUCED')
    else:
        with DEST.open('x',encoding='utf-8') as stream:json.dump(result,stream,ensure_ascii=False,indent=2,allow_nan=False)
    print(json.dumps({k:v for k,v in result.items() if k!='records'},indent=2))
