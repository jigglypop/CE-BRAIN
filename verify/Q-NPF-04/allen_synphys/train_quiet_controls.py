"""고정된 네 기준선 위치에 동일12자극 시간표를 옮겨 기술 대조한다."""
import json
from pathlib import Path
import numpy as np
from population_reciprocity import ROOT,sha
from superficial_ee_eligibility import save

HERE=Path(__file__).resolve().parent
STARTS=[.100,.125,.150,.175]

def main():
    sources={k:HERE/v for k,v in dict(train='recovery_train_responses_result.json',
        qc='ic_full_recording_qc_result.json',inventory='ic_extended_inventory_result.json',
        command='ic_command_context_result.json').items()}
    save('train_quiet_controls_contract.json',dict(
        question='How do all12 fixed event contrasts compare with identically timed patterns in previously command-constant baseline?',
        scope='All20 sweeps, all12 pulses, four fixed starts; post-result exploratory control, no randomization or independent replicates.',
        starts_s=STARTS,allowed_interval_s=[.08,.53],
        timing='Preserve each actual relative command onset and its detected max-slope delay; no detection on pseudo events.',
        windows='Unchanged post[2,8)ms minus pre[-8,-3)ms for each target; positive-minus-negative contrast.',
        summaries='Mean by pulse at each control start and event; same-sweep range inclusion and event-minus-four-control-mean signs. Not p-values.',
        limits='Overlapping controls, nonexchangeable early baseline and event time; no evidence that all biological input is absent; no causal correction.',
        checks='All control windows contained in command-constant interval; archived DA constancy recomputed; target hashes and actual contrasts reproduced.',
        source_sha256={k:sha(v) for k,v in sources.items()},code_sha256=sha(Path(__file__))))
    data={k:json.loads(v.read_text(encoding='utf-8')) for k,v in sources.items()}
    command=data['command'];archive=ROOT/'data/external/allen_synphys_r21/raw_ranges/1574292898.139/ic_all_command_context.npz'
    assert sha(archive)==command['archive_sha256']
    assert len(command['metadata'])==60
    with np.load(archive,allow_pickle=False) as z:
        for r in command['metadata']:
            v=z[r['key']+'_baseline'];assert np.isfinite(v).all() and np.ptp(v)==0
    receipts={(r['sweep'],r['target']):r for r in data['qc']['analysis']['records']}
    inventory={r['sweep']:r for r in data['inventory']['selected']}
    rows=[]
    for sw in range(37,57):
        events=sorted([r for r in data['train']['records'] if r['sweep']==sw],key=lambda r:r['pulse']);assert len(events)==12
        fs=inventory[sw]['nodes']['pre']['rate'];vmap={}
        for target in ('positive','negative'):
            entry=receipts[sw,target];path=ROOT/entry['array_path'];assert sha(path)==entry['array_sha256']
            with np.load(path,allow_pickle=False) as z:vmap[target]=z['voltage']
        for e in events:
            actual=e['command_start_s']+e['spikes'][0]['max_slope_time']
            centers=[actual]+[start+(e['command_start_s']-events[0]['command_start_s'])+e['spikes'][0]['max_slope_time'] for start in STARTS]
            assert all(.08<=c-.008 and c+.008<=.53 for c in centers[1:])
            contrasts=[]
            for center in centers:
                responses={}
                for target,v in vmap.items():
                    def mean(lo,hi):return float(np.interp((center+np.arange(lo,hi,1/fs))*fs,np.arange(len(v)),v).mean())
                    responses[target]=(mean(.002,.008)-mean(-.008,-.003))*1e6
                contrasts.append(responses['positive']-responses['negative'])
            assert abs(contrasts[0]-e['difference_uV'])<1e-5
            controls=contrasts[1:]
            rows.append(dict(sweep=sw,pulse=e['pulse'],actual_uV=contrasts[0],controls_uV=controls,
                event_minus_control_mean_uV=contrasts[0]-float(np.mean(controls)),inside_control_range=min(controls)<=contrasts[0]<=max(controls)))
    summary=[]
    for pulse in range(1,13):
        rr=[r for r in rows if r['pulse']==pulse]
        summary.append(dict(pulse=pulse,n=len(rr),actual_mean_uV=float(np.mean([r['actual_uV'] for r in rr])),
            control_means_uV=np.mean([r['controls_uV'] for r in rr],axis=0).tolist(),
            mean_difference_uV=float(np.mean([r['event_minus_control_mean_uV'] for r in rr])),
            positive_differences=sum(r['event_minus_control_mean_uV']>0 for r in rr),inside_control_range=sum(r['inside_control_range'] for r in rr)))
    save('train_quiet_controls_result.json',dict(contract_sha256=sha(HERE/'train_quiet_controls_contract.json'),records=rows,summary=summary,
        verification='PASS60 archived baseline commands, 960 control window bounds and240 original contrast reproductions'))
    print(json.dumps(summary,indent=2))

if __name__=='__main__':main()
