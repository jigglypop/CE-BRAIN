"""외부 5마리의 실제 입력·결과와 고정 전체범위 조건을 점검한다."""
import json
from pathlib import Path
import h5py
import numpy as np
from population_reciprocity import ROOT,sha
from superficial_ee_eligibility import save
HERE=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def main():
    cp=HERE/'icms_external_first_sessions_contract.json';contract=read(cp);rows=[]
    for asset in contract['selected']:
        subject=asset['path'].split('/')[0][4:];prefix=subject.lower()+'_external';resultpath=HERE/(prefix+'_result.json');r=read(resultpath);ex=read(HERE/(prefix+'_execution_contract.json'))
        assert ex['parent_sha256']==sha(cp) and ex['code_sha256']==sha(HERE/'icms_external_session.py')
        path=ROOT/'data/external/xie_icms_plasticity_2025'/Path(asset['path']).name
        meta=read(path.parent/('external_'+asset['asset_id']+'_metadata.json'));assert path.stat().st_size==asset['size'] and sha(path)==ex['input_sha256']==meta['digest']['dandi:sha2-256']
        with h5py.File(path,'r') as f:
            ntr=len(f['intervals/trials/id']);nu=len(f['units/id']);nc=int((f['intervals/trials/current_uA'][:]==0).sum())
            st=f['intervals/electrical_stimulation'];nominal=bool(np.all(st['frequency_hz'][:]==100) and np.all(st['pulse_count'][:]==70) and np.allclose(st['stop_time'][:]-st['start_time'][:],.7,atol=1e-8))
        base=dict(subject=subject,session=Path(asset['path']).name,trials=ntr,units=nu,catch_trials=nc,result_sha256=sha(resultpath),input_sha256=ex['input_sha256'])
        if r['status']=='STIMULATION_CONTRACT_MISMATCH':
            assert not nominal;rows.append(dict(**base,status=r['status']));continue
        assert r['status']=='ANALYZED' and nominal
        countpath=HERE/(prefix+'_counts.npz');assert sha(countpath)==r['counts_sha256']
        with np.load(countpath) as a:
            assert len(a['unit_ids'])==nu and a['counts'].shape==(ntr,nu,2)
            assert a['trial_ids'].tolist()==[v['trial_id'] for v in r['trials']]
            delta=(a['counts'][:,:,1]-a['counts'][:,:,0])/.5
        checks=[]
        for quality in ('good_only','all_quality'):
            for summary in [s for s in r['summaries'] if s['quality']==quality]:
                c=summary['current'];eligible=np.array([v['geometry_pass'] and (quality=='all_quality' or v['good']) for v in r['trials']]);curr=np.array([v['current'] for v in r['trials']]);block=np.array([v['block'] for v in r['trials']]);sel=eligible&(curr==c)
                unavailable=[b for b in range(4) if np.any(sel&(block==b)) and not np.any(eligible&(curr==0)&(block==b))]
                if summary['status']=='UNDEFINED':assert unavailable or not sel.any();continue
                assert not unavailable
                # Calculate a per-trial linear contrast and verify every unit separately.
                w=np.zeros(ntr);w[sel]=1/sel.sum()
                for b in range(4):
                    ctl=eligible&(curr==0)&(block==b);n=int((sel&(block==b)).sum())
                    if n:w[ctl]-=n/sel.sum()/ctl.sum()
                assert abs(w.sum())<1e-12
                actual=np.array([sum(w[i]*delta[i,j] for i in range(ntr)) for j in range(nu)])
                assert np.allclose(actual,summary['per_unit'],atol=1e-12) and abs(actual.mean()-summary['mean'])<1e-12
            primary=[s for s in r['summaries'] if s['quality']==quality]
            checks.append(dict(quality=quality,defined=sum(s['status']=='DEFINED' for s in primary),undefined=sum(s['status']=='UNDEFINED' for s in primary),nonnegative=[s['current'] for s in primary if s['status']=='DEFINED' and s['mean']>=0]))
        main=checks[0];status='UNDEFINED_COMPARISON' if main['undefined'] else 'DIRECTION_COUNTEREXAMPLE' if main['nonnegative'] else 'NEGATIVE_MEANS_OBSERVED'
        rows.append(dict(**base,status=status,quality_results=checks,geometry_failures=r['geometry_failures']))
    assert len(rows)==5
    complete=all(r['status']=='NEGATIVE_MEANS_OBSERVED' and r.get('geometry_failures',0)==0 for r in rows)
    save('icms_external_scope_audit_result.json',dict(animals=rows,all5_direction_condition_met=complete,code_sha256=sha(Path(__file__)),limits='Scope and arithmetic audit only; complete flag applies solely to frozen descriptive direction, never the whole brain objective.'))
    for r in rows:print(r['subject'],r['status'])
    print('ALL5_DIRECTION_CONDITION',complete)
if __name__=='__main__':main()
