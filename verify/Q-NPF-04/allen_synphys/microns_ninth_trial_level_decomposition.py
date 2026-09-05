"""시행 평균과 시행 내 변동의 공분산을 정확히 분해한다."""
import json
from pathlib import Path
import numpy as np
from population_reciprocity import ROOT,sha
from superficial_ee_eligibility import save
from microns_structure_response import contrasts
from microns_repeat_shift_control import weights

HERE=Path(__file__).resolve().parent


def main():
    path=ROOT/'data/external/microns_functional_nwb/scan_7_3_repeated_clips.npz'
    receipt=json.loads((HERE/'microns_ninth_repeats_acquisition.json').read_text());assert sha(path)==receipt['artifact_sha256']
    save('microns_ninth_trial_level_contract.json',dict(question='How much of the pooled residual structural contrast comes from trial-level means versus within-trial fluctuations?',
        method='Same36 cells and fixed pair weights. First remove leave-one-repeat-out condition-time pattern, then decompose each trial into its57-point mean and centered within-trial component. Normalize component covariances by original total standard deviations to preserve exact additivity; also report separately renormalized within-trial correlations.',
        selection='Both timing conventions; all10/first5/last5. No exclusions based on this result.',
        limits='Post-observation algebraic measurement diagnosis, not neural baseline removal or causal decomposition. Trial mean may contain genuine responses, drift, state and artifacts.',code_sha256=sha(Path(__file__)),input_sha256=sha(path)))
    data=np.load(path);units=data['unit_ids'].tolist();lookup={u:i for i,u in enumerate(units)}
    pairs=json.loads((HERE/'microns_ninth_scan_contrast_pairs.json').read_text())[0]['pairs'];_,w=weights(pairs)
    a=np.array([lookup[p['unit_a']] for p in pairs]);b=np.array([lookup[p['unit_b']] for p in pairs]);out=[]
    for mode,timing in enumerate(('common_frame','positive_delay_sensitivity')):
        for subset,repeats in [('all10',list(range(10))),('first5',list(range(5))),('last5',list(range(5,10)))]:
            x=data['values'][mode][:,repeats];n=len(repeats);r=x-(x.sum(axis=1,keepdims=True)-x)/(n-1)
            means=r.mean(axis=2,keepdims=True);within=r-means
            total=r.reshape(-1,36);total=total-total.mean(axis=0)
            between=np.broadcast_to(means,r.shape).reshape(-1,36);between=between-between.mean(axis=0)
            within=within.reshape(-1,36);within=within-within.mean(axis=0)
            tt=total.T@total;bb=between.T@between;ww=within.T@within
            assert np.allclose(tt,bb+ww,atol=1e-6,rtol=1e-12)
            assert np.allclose(between.T@within,0,atol=1e-6,rtol=0)
            denom=np.sqrt(np.outer(np.diag(tt),np.diag(tt)));corr=tt/denom
            cb=bb/denom;cw=ww/denom;assert np.allclose(corr,cb+cw,atol=1e-12)
            own=ww/np.sqrt(np.outer(np.diag(ww),np.diag(ww)))
            assert np.allclose(own,np.corrcoef(within,rowvar=False),atol=1e-12)
            full=float(w@corr[a,b]);level=float(w@cb[a,b]);fluctuation=float(w@cw[a,b]);assert abs(full-level-fluctuation)<1e-12
            fractions=np.diag(bb)/np.diag(tt)
            out.append(dict(timing=timing,subset=subset,total_matched=full,trial_mean_component=level,within_trial_component=fluctuation,within_trial_renormalized_matched=float(w@own[a,b]),median_trial_mean_variance_fraction=float(np.median(fractions)),cell_variance_fractions=[dict(unit_id=u,fraction=float(v)) for u,v in zip(units,fractions)]))
    save('microns_ninth_trial_level_result.json',dict(results=out,status='EXACT_COVARIANCE_DECOMPOSITION',limits='Additive components use total variance denominators; separately normalized within correlation has a different estimand. No causal attribution.'))
    for r in out:
        if r['timing']=='positive_delay_sensitivity':print({k:v for k,v in r.items() if k!='cell_variance_fractions'})


if __name__=='__main__':main()
