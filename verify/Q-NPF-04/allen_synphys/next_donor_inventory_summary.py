"""고정 후보 재고의 모드별 누락과 실제 반복 조건을 간결한 영수증으로 남긴다."""
import json
from pathlib import Path
from population_reciprocity import sha
from superficial_ee_eligibility import save

HERE=Path(__file__).resolve().parent


def main():
    path=HERE/'next_donor_recording_inventory_result.json'
    source=json.loads(path.read_text(encoding='utf-8'));summaries=[]
    for pair in source['pairs']:
        records=pair['records'];modes=[]
        for mode in ('ic','vc'):
            rr=[r for r in records if r['post']['clamp_mode']==mode]
            pulses=[p for r in rr for p in r['pulses']]
            state={}
            for role in ('pre','post'):
                ranges={}
                for field in ('access_resistance','input_resistance'):
                    values=[r[role]['test_pulse'][0][field] for r in rr if r[role]['test_pulse_same_recording_electrode'] and r[role]['test_pulse'][0][field] is not None]
                    ranges[field]=dict(n=len(values),min_ohm=min(values) if values else None,max_ohm=max(values) if values else None)
                state[role]=ranges
            modes.append(dict(mode=mode,records=len(rr),pulses=len(pulses),
                both_recording_qc=sum(r['pre']['qc_pass']==r['post']['qc_pass']==1 for r in rr),
                both_test_pulse_same_recording=sum(r['pre']['test_pulse_same_recording_electrode'] and r['post']['test_pulse_same_recording_electrode'] for r in rr),
                single_spike=sum(p['n_spikes']==1 for p in pulses),aligned=sum(p['first_spike_time'] is not None for p in pulses),
                ex_qc=sum(p['ex_qc_pass']==1 for p in pulses),state=state))
        repeated=[dict(sweeps=g['sweeps'],n=g['repeats'],mode=g['condition']['post_mode'],
            all_aligned=g['all_aligned'],all_ex_qc=g['all_ex_qc']) for g in pair['groups'] if g['repeats']>1]
        target=[r for r in records if 77<=int(r['post']['sweep'])<=81]
        target_summary=dict(sweeps=[r['post']['sweep'] for r in target],pulses=sum(len(r['pulses']) for r in target),
            aligned=sum(p['first_spike_time'] is not None for r in target for p in r['pulses']))
        summaries.append(dict(selection=pair['selection'],exact_condition_groups=len(pair['groups']),modes=modes,
            repeated_groups=repeated,ic_20hz_alignment=target_summary))
    result=dict(source_sha256=sha(path),code_sha256=sha(Path(__file__)),summaries=summaries)
    save('next_donor_inventory_summary.json',result)
    print('INVENTORY_SUMMARY_SAVED',len(summaries))


if __name__=='__main__':main()
