"""기존 반응창과 대조창을 유지한 채 동시기 기록 상태와 기술적으로 연결한다."""
import json
from datetime import datetime
from pathlib import Path
import numpy as np
from population_reciprocity import sha
from superficial_ee_eligibility import save

HERE=Path(__file__).resolve().parent

def main():
    names=['connection_recording_state_result.json','ic_extension_first_result.json',
           'ic_matched_baseline_result.json','ic_extended_inventory_result.json']
    save('connection_state_response_join_contract.json',dict(
        question='How do fixed20 event contrasts and baseline controls covary descriptively with contemporaneous recording state?',
        scope='Post-result exploratory join of20 sweeps from one experiment; no fitting, threshold changes or exclusions.',
        fields='Elapsed DB seconds; baseline current/potential, access/input resistance on all3 electrodes. Report all Pearson correlations.',
        outcomes='Unmodified event contrast and existing17-window control mean. No new adjusted outcome or causal correction.',
        limits='Correlated repeated sweeps, multiple exploratory associations, protocol and recording drift confounding; no p-values, independence or causal inference.',
        checks='Exact sweep37..56 keys and device mapping from raw inventory; matched-control event identity within1e-5 uV.',
        source_sha256={n:sha(HERE/n) for n in names},code_sha256=sha(Path(__file__))))
    state,response,control,inventory=[json.loads((HERE/n).read_text(encoding='utf-8')) for n in names]
    states={(r['sweep'],r['device']):r for r in state['records']}
    responses={r['sweep']:r for r in response['analysis']['records']}
    controls={r['sweep']:r for r in control['rows']}
    inv={r['sweep']:r for r in inventory['selected']}
    assert set(responses)==set(controls)==set(range(37,57))
    assert len(states)==60
    rows=[]
    for sw in range(37,57):
        for name,device in [('pre',5),('positive',4),('negative',2)]:
            assert inv[sw]['nodes'][name]['electrode']==f'electrode_{device}'
        rr=responses[sw];cc=controls[sw]
        assert abs(rr['difference_uV']-cc['actual_uV'])<1e-5
        row=dict(sweep=sw,event_uV=rr['difference_uV'],control_mean_uV=cc['control_mean_uV'],
                 within_control_range=cc['actual_inside_control_range'])
        times={states[sw,d]['recording']['start_time'] for d in (2,4,5)};assert len(times)==1
        row['elapsed_s']=(datetime.fromisoformat(next(iter(times)))-datetime.fromisoformat(states[37,2]['recording']['start_time'])).total_seconds()
        for d in (2,4,5):
            s=states[sw,d];assert s['same_recording']
            for origin,key,scale in [('qc','baseline_current',1e12),('qc','baseline_potential',1e3),('test_pulse','access_resistance',1e-6),('test_pulse','input_resistance',1e-6)]:
                row[f'device{d}_{key}']=s[origin][key]*scale
        rows.append(row)
    covariates=['elapsed_s']+[k for k in rows[0] if k.startswith('device')]
    correlations={}
    for k in covariates:
        x=np.array([r[k] for r in rows]);assert np.isfinite(x).all()
        correlations[k]={}
        for endpoint in ('event_uV','control_mean_uV'):
            y=np.array([r[endpoint] for r in rows]);assert np.isfinite(y).all()
            value=float(np.corrcoef(x,y)[0,1]) if x.std()>0 and y.std()>0 else None
            correlations[k][endpoint]=value
    out=dict(contract_sha256=sha(HERE/'connection_state_response_join_contract.json'),records=rows,correlations=correlations,
             event_inside_control_range=sum(r['within_control_range'] for r in rows),verification='PASS20 exact joins, electrode roles, event values and contemporaneous records')
    save('connection_state_response_join_result.json',out)
    print(json.dumps({k:v for k,v in out.items() if k!='records'},indent=2))

if __name__=='__main__':main()
