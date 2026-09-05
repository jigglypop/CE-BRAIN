"""첫 스캔에서 고정된 시행 평균/시행 내 공분산 분해를 비교한다."""
import json
from pathlib import Path
import numpy as np
from population_reciprocity import ROOT, sha
from superficial_ee_eligibility import save
from microns_repeat_shift_control import weights

HERE = Path(__file__).resolve().parent


def read(name):
    return json.loads((HERE / name).read_text(encoding='utf-8'))


def main():
    path = ROOT / 'data/external/microns_functional_nwb/scan_4_7_repeated_clips.npz'
    assert sha(path) == read('microns_repeat_response_acquisition.json')['artifact_sha256']
    save('microns_first_trial_level_contract.json', dict(
        question='Does the fixed trial-level covariance decomposition have the same component directions in scan4/7 as scan5/3?',
        method='LOO condition-time residual; trial mean over57 samples; centered within-trial component. Both covariance components normalized by total residual variances. Existing field-distance weights.',
        selection='All10/first5/last5; both timing conventions; include/exclude disputed unit3151. All12 cases reported. No response-selected exclusions.',
        limits='Post-observation descriptive comparison within one animal, not independent replication or causal identification. No new confirmation set.',
        input_sha256=sha(path), code_sha256=sha(Path(__file__)),
        weights_code_sha256=sha(HERE/'microns_repeat_shift_control.py'),
        pairs_sha256=sha(HERE/'microns_structure_response_pairs.json'),
        prior_result_sha256=sha(HERE/'microns_repeat_structure_result.json')))
    data = np.load(path)
    units = data['unit_ids'].tolist()
    lookup = {u:i for i,u in enumerate(units)}
    original = read('microns_structure_response_pairs.json')[0]['pairs']
    previous = read('microns_repeat_structure_result.json')['results']
    results = []
    for mode, timing in enumerate(('common_frame', 'positive_delay_sensitivity')):
        for subset, selection in [('all10',slice(None)),('first5',slice(0,5)),('last5',slice(5,10))]:
            x = data['values'][mode,:,selection]
            n = x.shape[1]
            r = x - (x.sum(axis=1,keepdims=True)-x)/(n-1)
            means = r.mean(axis=2,keepdims=True)
            within = r-means
            z = r.reshape(-1,len(units)); z = z-z.mean(axis=0)
            level = np.broadcast_to(means,r.shape).reshape(z.shape)
            level = level-level.mean(axis=0)
            within = within.reshape(z.shape); within = within-within.mean(axis=0)
            tt,bb,ww = z.T@z, level.T@level, within.T@within
            assert np.isfinite(tt).all() and (np.diag(tt)>0).all()
            assert np.allclose(tt,bb+ww,rtol=1e-12,atol=1e-6)
            assert np.allclose(level.T@within,0,rtol=0,atol=1e-6)
            denom = np.sqrt(np.outer(np.diag(tt),np.diag(tt)))
            total,between,inside = tt/denom,bb/denom,ww/denom
            assert np.allclose(total,np.corrcoef(z,rowvar=False),atol=1e-12)
            for exclude in (False,True):
                pairs = [p for p in original if not exclude or 3151 not in (p['unit_a'],p['unit_b'])]
                _,w = weights(pairs)
                a = np.array([lookup[p['unit_a']] for p in pairs])
                b = np.array([lookup[p['unit_b']] for p in pairs])
                full,mean,fluct = [float(w@m[a,b]) for m in (total,between,inside)]
                assert abs(full-mean-fluct)<1e-12
                old = next(p for p in previous if p['timing']==timing and p['repeat_subset']==subset and p['exclude_disputed']==exclude and p['component']=='leave_one_repeat_out_residual')
                assert abs(full-old['matched_mean_difference'])<1e-12
                results.append(dict(timing=timing,subset=subset,exclude_disputed=exclude,
                    total_matched=full,trial_mean_component=mean,within_trial_component=fluct,
                    linked_dyads=sum(p['linked'] for p in pairs),dyads=len(pairs)))
    save('microns_first_trial_level_result.json',dict(results=results,
        status='EXACT_DECOMPOSITION_AND_PRIOR_TOTAL_AGREEMENT',
        limits='Same animal; fixed scan-specific geometry weights; observational and post-observation. Components are not causal effects.'))
    for row in results:
        print(row)


if __name__ == '__main__':
    main()
