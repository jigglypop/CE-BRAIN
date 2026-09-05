"""고정 외부 첫 세션 계약을 한 동물에 적용한다."""
import argparse,json
from pathlib import Path
import h5py
import numpy as np
from population_reciprocity import ROOT,sha
from superficial_ee_eligibility import save
HERE=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def main(subject):
    cp=HERE/'icms_external_first_sessions_contract.json';contract=read(cp)
    asset=next(a for a in contract['selected'] if a['path'].startswith('sub-'+subject+'/'))
    base=ROOT/'data/external/xie_icms_plasticity_2025';path=base/Path(asset['path']).name
    metadata=read(base/('external_'+asset['asset_id']+'_metadata.json'))
    assert path.stat().st_size==asset['size'] and sha(path)==metadata['digest']['dandi:sha2-256']
    prefix=subject.lower()+'_external'
    save(prefix+'_execution_contract.json',dict(parent_sha256=sha(cp),code_sha256=sha(Path(__file__)),input_sha256=sha(path),subject=subject))
    with h5py.File(path,'r') as f:
        required=['intervals/trials','intervals/electrical_stimulation','units/spike_times','units/spike_times_index','processing/behavior/wheel/wheel_position_processed/data','processing/behavior/wheel/wheel_position_processed/starting_time']
        missing=[p for p in required if p not in f]
        if missing:
            save(prefix+'_result.json',dict(status='SCHEMA_UNSUPPORTED',missing=missing));print(missing);return
        tr=f['intervals/trials'];st=f['intervals/electrical_stimulation'];unitids=f['units/id'][:]
        starts=st['start_time'][:];stops=st['stop_time'][:]
        nominal=bool(np.all(st['frequency_hz'][:]==100) and np.all(st['pulse_count'][:]==70) and np.allclose(stops-starts,.7,atol=1e-8))
        if not nominal:
            save(prefix+'_result.json',dict(status='STIMULATION_CONTRACT_MISMATCH',frequency=np.unique(st['frequency_hz'][:]).tolist(),pulses=np.unique(st['pulse_count'][:]).tolist(),duration_range=[float((stops-starts).min()),float((stops-starts).max())]));return
        ids=tr['trial_index'][:];sids=st['trial_index'][:];assert len(set(ids.tolist()))==len(ids) and len(set(sids.tolist()))==len(sids)
        lookup={int(i):j for j,i in enumerate(sids)};assert set(lookup)<=set(ids.tolist())
        wheel=f['processing/behavior/wheel/wheel_position_processed'];lo=float(wheel['starting_time'][()]);hi=lo+len(wheel['data'])/float(wheel['starting_time'].attrs['rate'])
        sp=f['units/spike_times'][:];ends=f['units/spike_times_index'][:].astype(int);beg=np.r_[0,ends[:-1]];assert ends[-1]==len(sp) and np.isfinite(sp).all()
        trains=[sp[a:b] for a,b in zip(beg,ends)];assert all(np.all(np.diff(a)>=0) for a in trains)
        blocks=np.zeros(len(ids),int)
        for b,ix in enumerate(np.array_split(np.arange(len(ids)),4)):blocks[ix]=b
        counts=np.zeros((len(ids),len(unitids),2),int);rows=[]
        for i,tid in enumerate(ids):
            current=float(tr['current_uA'][i]);j=lookup.get(int(tid));assert (j is None)==(current==0)
            anchor=float(starts[j]) if j is not None else float(tr['start_time'][i])
            valid=True
            for w,(a,b) in enumerate([(-.7,-.2),(.8,1.3)]):
                left,right=anchor+a,anchor+b;valid=valid and left>=lo and right<=hi and not np.any((starts<right)&(stops>left))
                for u,s in enumerate(trains):
                    ia,ib=np.searchsorted(s,[left,right]);counts[i,u,w]=ib-ia
            rows.append(dict(trial_id=int(tid),current=current,block=int(blocks[i]),good=bool(tr['is_good_trial'][i]),geometry_pass=bool(valid),anchor=anchor))
    deltas=(counts[:,:,1]-counts[:,:,0])/.5;currents=np.array([r['current'] for r in rows]);summaries=[];blockresults=[]
    for quality in ('good_only','all_quality'):
        eligible=np.array([r['geometry_pass'] and (quality=='all_quality' or r['good']) for r in rows])
        for c in sorted(set(currents)-{0.}):
            total=np.zeros(len(unitids));n=0;unsupported=[]
            for b in range(4):
                sel=eligible&(currents==c)&(blocks==b);ctl=eligible&(currents==0)&(blocks==b)
                if not sel.any():continue
                if not ctl.any():unsupported.append(b);continue
                difference=deltas[sel].mean(axis=0)-deltas[ctl].mean(axis=0)
                total+=sel.sum()*difference;n+=int(sel.sum())
                blockresults.append(dict(quality=quality,current=float(c),block=b,stim_trials=int(sel.sum()),catch_trials=int(ctl.sum()),mean=float(difference.mean()),per_unit=difference.tolist()))
            if unsupported or not n:
                summaries.append(dict(quality=quality,current=float(c),status='UNDEFINED',missing_catch_blocks=unsupported,eligible_stim_trials=int((eligible&(currents==c)).sum())));continue
            observed=total/n
            direct=np.array([deltas[i]-deltas[eligible&(currents==0)&(blocks==blocks[i])].mean(axis=0) for i in np.flatnonzero(eligible&(currents==c))]).mean(axis=0)
            assert np.allclose(observed,direct,atol=1e-12)
            summaries.append(dict(quality=quality,current=float(c),status='DEFINED',trials=n,mean=float(observed.mean()),per_unit=observed.tolist(),positive_units=int((observed>0).sum()),negative_units=int((observed<0).sum())))
    dest=HERE/(prefix+'_counts.npz')
    if not dest.exists():
        with dest.open('xb') as f:np.savez_compressed(f,counts=counts,unit_ids=unitids,trial_ids=ids)
    else:
        with np.load(dest) as a:assert np.array_equal(a['counts'],counts)
    save(prefix+'_result.json',dict(status='ANALYZED',subject=subject,trials=rows,unit_ids=unitids.tolist(),summaries=summaries,blocks=blockresults,
        geometry_failures=sum(not r['geometry_pass'] for r in rows),counts_sha256=sha(dest),code_sha256=sha(Path(__file__))))
    print(subject,'units',len(unitids),'trials',len(ids))
    for s in summaries:print({k:v for k,v in s.items() if k!='per_unit'})
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('subject');main(p.parse_args().subject)
