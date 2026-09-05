"""완전 사례 선택과 회차 밖 예측을 이용한 행동 회귀를 구분한다."""
import json
from pathlib import Path
import numpy as np
from population_reciprocity import ROOT,sha
from superficial_ee_eligibility import save
from microns_structure_response import contrasts

HERE=Path(__file__).resolve().parent


def main():
    yp=ROOT/'data/external/microns_functional_nwb/scan_4_7_repeated_clips.npz'
    bp=ROOT/'data/external/microns_functional_nwb/scan_4_7_repeated_behavior.npz'
    assert sha(yp)==json.loads((HERE/'microns_repeat_response_acquisition.json').read_text())['artifact_sha256']
    assert sha(bp)==json.loads((HERE/'microns_repeat_behavior_result.json').read_text())['arrays_sha256']
    save('microns_behavior_crossfit_contract.json',dict(question='Separate complete-case sampling, stimulus-mean estimation, and held-repeat behavior/time prediction effects on the fixed structural contrast.',
        rows='Same complete mask for all models: abs(speed), pupil_major/minor, eye_x/y finite. No imputation; repeats9/10 have no validation rows.',
        folds='Leave one observed repeat out across all6 conditions. Condition-phase response and covariate means and covariate scales estimated only on other complete-case repeats.',
        models='Fixed linear least squares rcond1e-12: time only, five behavior variables only, combined. No tuning. Report rank and marginal training-range violations on test rows.',
        endpoints='Original residual contrast full vs complete rows; held-repeat baseline vs three regression residual contrasts; held-repeat squared-error ratio relative to stimulus-only baseline.',
        limits='Post-observation diagnostic, not causal confounder adjustment or independent animal prediction. Out-of-training-range behavior may invalidate extrapolative correction. Report failures rather than tuning.',
        code_sha256=sha(Path(__file__)),response_sha256=sha(yp),behavior_sha256=sha(bp)))
    yd=np.load(yp);bd=np.load(bp);names=['abs_speed','pupil_major','pupil_minor','eye_x','eye_y','time']
    xx=np.stack([np.abs(bd['speed']),bd['pupil_major'],bd['pupil_minor'],bd['eye_x'],bd['eye_y'],bd['query_time']],axis=-1)
    valid=np.isfinite(xx).all(axis=-1);assert int(valid.sum())==2595
    pairs=json.loads((HERE/'microns_structure_response_pairs.json').read_text())[0]['pairs']
    lookup={int(u):i for i,u in enumerate(yd['unit_ids'])}
    models={'time_only':[5],'behavior_only':[0,1,2,3,4],'combined':list(range(6))}
    output=[];diagnostics=[];prediction_scores=[]
    for mode,timing in enumerate(('common_frame','positive_delay_sensitivity')):
        y=yd['values'][mode];full_residual=y-(y.sum(axis=1,keepdims=True)-y)/9
        baseline=np.full_like(y,np.nan);corrected={name:np.full_like(y,np.nan) for name in models}
        for held in range(10):
            test=valid.copy();test[:,:held]=False;test[:,held+1:]=False
            if not test.any():continue
            train=valid&~test;assert not (train&test).any()
            counts=train.sum(axis=1,keepdims=True);assert (counts>0).all()
            my=np.where(train[...,None],y,0).sum(axis=1,keepdims=True)/counts[...,None]
            mx=np.where(train[...,None],xx,0).sum(axis=1,keepdims=True)/counts[...,None]
            ry=y-my;dx=xx-mx;scale=dx[train].std(axis=0);assert (scale>0).all()
            z=dx/scale;baseline[test]=ry[test]
            for name,columns in models.items():
                a=z[train][:,columns];b=z[test][:,columns]
                coef,_,rank,singular=np.linalg.lstsq(a,ry[train],rcond=1e-12)
                assert rank==len(columns)
                residual=ry[train]-a@coef
                assert np.linalg.norm(a.T@residual)<=1e-9*(np.linalg.norm(a)*np.linalg.norm(ry[train])+1)
                corrected[name][test]=ry[test]-b@coef
                outside=((b<a.min(axis=0))|(b>a.max(axis=0)))
                if mode==1:diagnostics.append(dict(held_repeat_one_based=held+1,model=name,train_rows=int(train.sum()),test_rows=int(test.sum()),rank=int(rank),condition_number=float(singular[0]/singular[-1]),outside_any=int(outside.any(axis=1).sum()),outside_by_variable={names[c]:int(outside[:,j].sum()) for j,c in enumerate(columns)}))
                sse0=(ry[test]**2).sum(axis=0);sse=(corrected[name][test]**2).sum(axis=0)
                prediction_scores.append(dict(timing=timing,held_repeat_one_based=held+1,model=name,median_relative_skill=float(np.median(1-sse/sse0)),cells_improved=int((sse<sse0).sum()),total53=53))
        scenarios={'original_full':full_residual.reshape(-1,53),'original_complete':full_residual[valid],'crossfit_stimulus_only':baseline[valid],**{k:v[valid] for k,v in corrected.items()}}
        for name,values in scenarios.items():
            assert np.isfinite(values).all() and (values.std(axis=0)>0).all()
            corr=np.corrcoef(values,rowvar=False)
            pp=[dict(p,correlation=float(corr[lookup[p['unit_a']],lookup[p['unit_b']]])) for p in pairs]
            for exclude in (False,True):
                selected=[p for p in pp if not exclude or 3151 not in (p['unit_a'],p['unit_b'])]
                output.append(dict(timing=timing,scenario=name,rows=len(values),exclude_disputed=exclude,**contrasts(selected)))
    save('microns_behavior_crossfit_result.json',dict(results=output,diagnostics=diagnostics,prediction_scores=prediction_scores,complete_rows=int(valid.sum()),unobserved_repeats_one_based=[9,10],limits='Same-row residualization diagnostic only. Predictive skill and extrapolation must be assessed before interpreting corrected contrast.'))
    for r in output:
        if r['timing']=='positive_delay_sensitivity' and not r['exclude_disputed']:print(r['scenario'],r['matched_mean_difference'])
    for r in prediction_scores:
        if r['timing']=='positive_delay_sensitivity' and r['model']=='combined':print('skill',r['held_repeat_one_based'],r['median_relative_skill'],r['cells_improved'])


if __name__=='__main__':main()
