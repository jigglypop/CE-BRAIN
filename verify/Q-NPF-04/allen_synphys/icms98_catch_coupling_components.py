"""동일 catch PC의 시행 평균/시행 내 성분과 같은 구간 타시행 대조."""
import json
from pathlib import Path
import numpy as np
import h5py
from scipy.ndimage import gaussian_filter1d
from population_reciprocity import ROOT,sha
from superficial_ee_eligibility import save
HERE=Path(__file__).resolve().parent
def read(n):return json.loads((HERE/n).read_text(encoding='utf-8'))
def main():
    base=read('icms98_catch_boundary_comparison_result.json');prior=read('icms98_next_session_result.json');p=ROOT/'data/external/xie_icms_plasticity_2025/sub-ICMS98_ses-2023-10-24_behavior+ecephys+ophys.nwb'
    cp=read('icms98_catch_boundary_comparison_contract.json');assert sha(p)==cp['input_sha256']
    save('icms98_catch_coupling_components_contract.json',dict(code_sha256=sha(Path(__file__)),input_sha256=sha(p),
        parent_sha256=sha(HERE/'icms98_catch_boundary_comparison_result.json'),trial_source_sha256=sha(HERE/'icms98_next_session_result.json'),
        method='Same36 catches and21 units; 1ms bins in trialstart+0.8..1.3s, separate sigma10bins truncate4 smoothing, interior100:400. Decompose prior PC exactly into trigger-weighted trial-interior population mean minus global mean, and within-trial centered population component. Leave-target-out population. Compare each target trial to mean population trace of all other catches in same original100-trial block, both raw and trial-demeaned. No permutations or p-values.',
        scope='Report all units, descriptive direction counts restricted to prior13 eligible units with at least50 interior spikes. No new quality selection.',
        ceiling='Exploratory L1 scope-limited coactivity; not direct connection, causal mechanism or independent replication. Cross-trial contrast can retain within-block state and behavior differences.'))
    with h5py.File(p,'r') as f:
        tr=f['intervals/trials'];idx={int(t):i for i,t in enumerate(tr['trial_index'][:])};sp=f['units/spike_times'][:];ends=f['units/spike_times_index'][:].astype(int);uids=f['units/id'][:]
        trains=[sp[a:b] for a,b in zip(np.r_[0,ends[:-1]],ends)];counts=np.zeros((36,len(uids),500),int)
        assert [r['trial_id'] for r in prior['trials']]==base['trial_ids']
        for t,row in enumerate(prior['trials']):
            start=float(tr['start_time'][idx[row['trial_id']]])+.8
            for u,train in enumerate(trains):
                a,b=np.searchsorted(train,[start,start+.5]);bins=np.floor((train[a:b]-start)/.001).astype(int);assert ((bins>=0)&(bins<500)).all()
                counts[t,u]=np.bincount(bins,minlength=500)
    blocks=np.array([r['block'] for r in prior['trials']]);total=counts.sum(axis=1);old={r['unit']:r for r in base['units']};rows=[]
    for u,uid in enumerate(uids):
        pop=(total-counts[:,u])/.001;globalmean=float(pop.mean());smooth=gaussian_filter1d(pop,10,axis=1,truncate=4,mode='nearest')[:,100:400]
        weights=counts[:,u,100:400];n=int(weights.sum());assert n==old[int(uid)]['interior_trigger_spikes']
        if not n:continue
        means=smooth.mean(axis=1);centered=smooth-means[:,None]
        avg=lambda v:float(np.sum(weights*v)/n)
        actual=avg(smooth-globalmean);between=avg(means[:,None]-globalmean);within=avg(centered)
        assert abs(actual-old[int(uid)]['pc_trialwise_same_interior'])<1e-10 and abs(actual-between-within)<1e-10
        cross=np.zeros_like(smooth);cross_centered=np.zeros_like(smooth)
        for t in range(36):
            mask=(blocks==blocks[t])&(np.arange(36)!=t);assert mask.sum()>=2
            cross[t]=smooth[mask].mean(axis=0);cross_centered[t]=centered[mask].mean(axis=0)
        control=avg(cross-globalmean);withincontrol=avg(cross_centered)
        rows.append(dict(unit=int(uid),eligible=old[int(uid)]['eligible'],interior_spikes=n,total_pc=actual,trial_mean_component=between,within_trial_component=within,
            other_trial_control=control,same_minus_other=actual-control,within_other_trial_control=withincontrol,within_same_minus_other=within-withincontrol,
            trial_trigger_counts=weights.sum(axis=1).tolist(),trial_population_means=means.tolist()))
    eligible=[r for r in rows if r['eligible']];fields=['total_pc','trial_mean_component','within_trial_component','same_minus_other','within_same_minus_other']
    summary={k:dict(positive=sum(r[k]>0 for r in eligible),negative=sum(r[k]<0 for r in eligible),median=float(np.median([r[k] for r in eligible]))) for k in fields}
    save('icms98_catch_coupling_components_result.json',dict(units=rows,eligible_units=len(eligible),summary=summary))
    print(summary)
    for r in eligible:print({k:r[k] for k in ['unit']+fields})
if __name__=='__main__':main()
