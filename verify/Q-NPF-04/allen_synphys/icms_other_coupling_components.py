"""기존 다른 동물의 고정 catch에서 평균/내부 성분과 타시행 대조."""
import json
from pathlib import Path
import h5py
import numpy as np
from scipy.ndimage import gaussian_filter1d
from icms98_unit_overlap import nearest
from population_reciprocity import ROOT,sha
from superficial_ee_eligibility import save
HERE=Path(__file__).resolve().parent
def read(n):return json.loads((HERE/n).read_text(encoding='utf-8'))
def main():
    prior=read('icms_coupling_other_animals_result.json');contract=read('icms_coupling_other_animals_contract.json')
    save('icms_other_coupling_components_contract.json',dict(code_sha256=sha(Path(__file__)),parent_sha256=sha(HERE/'icms_coupling_other_animals_result.json'),
        method='Reuse exact prior catches and eligibility in ICMS100/101. Split raw and15-sample-censored PC into interior trial population mean relative global mean and within-trial component. Compare within-trial centered traces against mean of other selected catches in same original100-trial block. Censor other-trial traces relative to their own target events, as sensitivity only.',
        limits='No randomization test, causal inference or independent cells. Trial mean component includes full-vs-interior mean shift. Censored cross-trial comparison is not an exchangeable null.',
        prediction='Describe whether within-trial component and same-minus-other contrast stay positive for all prior eligible units; preserve nonpositive results.'))
    outputs=[]
    for session in prior['subjects']:
        subject=session['subject'];date=contract['subjects'][subject];p=ROOT/f'data/external/xie_icms_plasticity_2025/sub-{subject}_ses-{date}_behavior+ecephys+ophys.nwb'
        assert sha(p)==contract['inputs'][subject]
        with h5py.File(p,'r') as f:
            tr=f['intervals/trials'];lookup={int(v):i for i,v in enumerate(tr['trial_index'][:])};ids=f['units/id'][:];sp=f['units/spike_times'][:];ends=f['units/spike_times_index'][:].astype(int)
            trains=[sp[a:b] for a,b in zip(np.r_[0,ends[:-1]],ends)];events=[];bins=[];blocks=[]
            for tid in session['trials']:
                i=lookup[tid];blocks.append(i//100);start=float(tr['start_time'][i])+.8;ev=[];bi=[]
                for s in trains:
                    a,b=np.searchsorted(s,[start,start+.5]);v=s[a:b];ix=np.floor((v-start)/.001).astype(int);assert ((ix>=0)&(ix<500)).all()
                    ev.append(np.rint(v*30000).astype(np.int64));bi.append(ix)
                events.append(ev);bins.append(bi)
        blocks=np.array(blocks);old={r['unit']:r for r in session['units']};rows=[]
        for u,uid in enumerate(ids):
            weights=np.array([np.bincount(b[u],minlength=500) for b in bins])[:,100:400];n=int(weights.sum());assert n==old[int(uid)]['interior_spikes']
            if not n:continue
            raw=np.zeros((len(bins),500));removed=np.zeros_like(raw)
            for t in range(len(bins)):
                for v in range(len(ids)):
                    if v==u:continue
                    raw[t]+=np.bincount(bins[t][v],minlength=500)
                    mask=nearest(events[t][v],events[t][u])<=15
                    removed[t]+=np.bincount(bins[t][v][mask],minlength=500)
            variants=[]
            for label,counts,key in [('raw',raw,'original_pc'),('censored',raw-removed,'retained_pc')]:
                rate=counts/.001;globalmean=float(rate.mean());smooth=gaussian_filter1d(rate,10,axis=1,truncate=4,mode='nearest')[:,100:400]
                means=smooth.mean(axis=1);centered=smooth-means[:,None];avg=lambda a:float(np.sum(weights*a)/n)
                total=avg(smooth-globalmean);between=avg(means[:,None]-globalmean);within=avg(centered)
                assert abs(total-old[int(uid)][key])<1e-9 and abs(total-between-within)<1e-9
                cross=np.zeros_like(centered)
                for t in range(len(bins)):
                    other=(blocks==blocks[t])&(np.arange(len(bins))!=t);assert other.sum()>=2
                    cross[t]=centered[other].mean(axis=0)
                control=avg(cross)
                variants.append(dict(method=label,total_pc=total,trial_mean_component=between,within_trial_component=within,other_trial_within_control=control,within_same_minus_other=within-control))
            rows.append(dict(unit=int(uid),eligible=old[int(uid)]['eligible'],variants=variants))
        summary=[]
        for k in (0,1):
            vv=[r['variants'][k] for r in rows if r['eligible']]
            summary.append(dict(method=('raw','censored')[k],eligible=len(vv),positive_within=sum(v['within_trial_component']>0 for v in vv),positive_contrast=sum(v['within_same_minus_other']>0 for v in vv),median_within=float(np.median([v['within_trial_component'] for v in vv])),median_contrast=float(np.median([v['within_same_minus_other'] for v in vv]))))
        outputs.append(dict(subject=subject,units=rows,summary=summary));print(subject,summary)
    save('icms_other_coupling_components_result.json',dict(subjects=outputs))
if __name__=='__main__':main()
