"""탐색: 기록상 응답 없는 catch의 발화 변화. 인과적 보정이 아니다."""
import json
from pathlib import Path
import h5py
import numpy as np
from population_reciprocity import ROOT,sha
from superficial_ee_eligibility import save
HERE=Path(__file__).resolve().parent
BASE=ROOT/'data/external/xie_icms_plasticity_2025'

def main():
    source=HERE/'icms_catch_anchor_audit_result.json'
    parent=json.loads((HERE/'icms_catch_anchor_audit_contract.json').read_text(encoding='utf-8'))
    save('icms_catch_response_split_contract.json',dict(
        code_sha256=sha(Path(__file__)),source_sha256=sha(source),inputs=parent['inputs'],
        method='Reuse paired geometry-valid good catches and both anchor counts. Split by neither hit nor finite response time versus either. Report discordance.',
        status='EXPLORATORY_POST_OUTCOME_DESCRIPTION',
        limitation='No response flag does not establish no motion or no reward. No causal adjustment or independent confirmation.'))
    result=[]
    for r in json.loads(source.read_text(encoding='utf-8'))['subjects']:
        p=ROOT/parent['inputs'][r['subject']]['path']
        assert sha(p)==parent['inputs'][r['subject']]['sha256']
        with h5py.File(p,'r') as f:
            tr=f['intervals/trials'];lookup={int(v):i for i,v in enumerate(tr['trial_index'][:])}
            rows=[]
            for a in r['trials']:
                if not all(v['geometry_pass'] for v in a['variants']):continue
                i=lookup[a['trial_id']];hit=bool(tr['is_hit'][i]);finite=bool(np.isfinite(tr['response_time'][i]))
                rows.append(dict(trial_id=a['trial_id'],hit=hit,finite_response_time=finite,
                    changes=[((np.array(v['counts'])[:,1]-np.array(v['counts'])[:,0])*2).tolist() for v in a['variants']]))
        summaries=[]
        for label,responded in [('no_recorded_response',False),('either_response_indicator',True)]:
            selected=[a for a in rows if (a['hit'] or a['finite_response_time'])==responded]
            values=np.array([a['changes'] for a in selected])
            summaries.append(dict(group=label,trials=len(selected),
                mean_change_by_anchor=values.mean(axis=(0,2)).tolist() if len(selected) else None))
        result.append(dict(subject=r['subject'],discordant=sum(a['hit']!=a['finite_response_time'] for a in rows),summaries=summaries,trials=rows))
    save('icms_catch_response_split_result.json',dict(subjects=result))
    for r in result:print(r['subject'],r['discordant'],r['summaries'])

if __name__=='__main__':main()
