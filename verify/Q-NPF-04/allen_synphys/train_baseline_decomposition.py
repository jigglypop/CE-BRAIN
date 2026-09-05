"""각 표적의 반복 자극 전후 전압을 첫 자극 전 기준선으로 분해한다."""
import json
from pathlib import Path
import numpy as np
from population_reciprocity import ROOT,sha
from superficial_ee_eligibility import save

HERE=Path(__file__).resolve().parent

def main():
    sources={n:HERE/f for n,f in dict(train='recovery_train_responses_result.json',targets='ic_full_recording_qc_result.json',inventory='ic_extended_inventory_result.json').items()}
    save('train_baseline_decomposition_contract.json',dict(
        question='How much of the local response contrast comes from the evolving pre-pulse baseline versus post-pulse voltage?',
        scope='All20 sweeps x12 pulses x2 targets; exploratory algebraic decomposition, no model fit or exclusion.',
        windows='Unchanged spike-relative pre[-8,-3)ms and post[2,8)ms; common reference is pre-window of pulse1 for each target and sweep.',
        identity='local_response = post_minus_first_pre - current_pre_minus_first_pre; same identity for positive-minus-negative contrast.',
        limits='Common-reference voltage is not isolated synaptic amplitude. Residual prior responses, spontaneous activity, drift and artifacts remain mixed.',
        checks='Target archive hashes; all480 local responses reproduce previous values within1e-5uV; algebraic identity; pulse1 baseline zero.',
        source_sha256={n:sha(p) for n,p in sources.items()},code_sha256=sha(Path(__file__))))
    data={n:json.loads(p.read_text(encoding='utf-8')) for n,p in sources.items()}
    receipts={(r['sweep'],r['target']):r for r in data['targets']['analysis']['records']}
    inventory={r['sweep']:r for r in data['inventory']['selected']}
    rows=[]
    for sw in range(37,57):
        events=sorted([r for r in data['train']['records'] if r['sweep']==sw],key=lambda r:r['pulse'])
        assert len(events)==12 and all(len(r['spikes'])==1 for r in events)
        fs=inventory[sw]['nodes']['pre']['rate'];target_rows={}
        for target in ('positive','negative'):
            receipt=receipts[sw,target];path=ROOT/receipt['array_path'];assert sha(path)==receipt['array_sha256']
            with np.load(path,allow_pickle=False) as z:v=z['voltage']
            values=[]
            for e in events:
                center=e['command_start_s']+e['spikes'][0]['max_slope_time']
                def mean(lo,hi):
                    indices=(center+np.arange(lo,hi,1/fs))*fs
                    assert indices.min()>=0 and indices.max()<len(v)-1
                    return float(np.interp(indices,np.arange(len(v)),v).mean()*1e6)
                pre,post=mean(-.008,-.003),mean(.002,.008)
                assert abs((post-pre)-e['responses'][target])<1e-5
                values.append((pre,post))
            reference=values[0][0]
            target_rows[target]=[dict(pre_shift_uV=pre-reference,post_shift_uV=post-reference,local_response_uV=post-pre) for pre,post in values]
            assert target_rows[target][0]['pre_shift_uV']==0
        for index,e in enumerate(events):
            row=dict(sweep=sw,pulse=index+1,positive=target_rows['positive'][index],negative=target_rows['negative'][index])
            row['contrast']={k:row['positive'][k]-row['negative'][k] for k in row['positive']}
            c=row['contrast'];assert abs(c['local_response_uV']-e['difference_uV'])<1e-5
            assert abs(c['post_shift_uV']-c['pre_shift_uV']-c['local_response_uV'])<1e-8
            rows.append(row)
    summary=[]
    for pulse in range(1,13):
        selected=[r for r in rows if r['pulse']==pulse]
        summary.append(dict(pulse=pulse,**{target:{key:float(np.mean([r[target][key] for r in selected])) for key in selected[0][target]} for target in ('positive','negative','contrast')}))
    save('train_baseline_decomposition_result.json',dict(contract_sha256=sha(HERE/'train_baseline_decomposition_contract.json'),records=rows,summary=summary,
        verification='PASS480 original-response reproductions and240 contrast identities; no new downloads'))
    print(json.dumps(summary,indent=2))

if __name__=='__main__':main()
