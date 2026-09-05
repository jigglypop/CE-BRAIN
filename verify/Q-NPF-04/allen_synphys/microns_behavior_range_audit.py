"""기존 회귀를 그대로 재현해 학습 범위 안팎의 예측 실패를 분리한다."""
import json
from pathlib import Path
import numpy as np
from population_reciprocity import ROOT,sha
from superficial_ee_eligibility import save

HERE=Path(__file__).resolve().parent


def score(base,error,mask):
    if not mask.any():return dict(rows=0,median_relative_skill=None,cells_improved=None)
    a=(base[mask]**2).sum(axis=0);b=(error[mask]**2).sum(axis=0);assert (a>0).all()
    return dict(rows=int(mask.sum()),median_relative_skill=float(np.median(1-b/a)),cells_improved=int((b<a).sum()))


def main():
    contract=json.loads((HERE/'microns_behavior_crossfit_contract.json').read_text())
    previous=json.loads((HERE/'microns_behavior_crossfit_result.json').read_text())
    yp=ROOT/'data/external/microns_functional_nwb/scan_4_7_repeated_clips.npz';bp=ROOT/'data/external/microns_functional_nwb/scan_4_7_repeated_behavior.npz'
    assert sha(yp)==contract['response_sha256'] and sha(bp)==contract['behavior_sha256']
    assert sha(HERE/'microns_behavior_crossfit.py')==contract['code_sha256']
    save('microns_behavior_range_contract.json',dict(question='Does prediction failure persist on validation rows inside every fitted covariate marginal training range?',
        method='Reproduce existing folds, centering, scaling, OLS and rcond exactly. Partition the same held-repeat errors into all/inside/outside. No retraining on favorable subset or threshold tuning.',
        limits='Marginal min-max containment is not joint support or causal positivity. Small subsets retained with row counts; not independent statistical tests.',
        code_sha256=sha(Path(__file__)),prior_contract_sha256=sha(HERE/'microns_behavior_crossfit_contract.json')))
    yd=np.load(yp);bd=np.load(bp)
    xx=np.stack([np.abs(bd['speed']),bd['pupil_major'],bd['pupil_minor'],bd['eye_x'],bd['eye_y'],bd['query_time']],axis=-1)
    valid=np.isfinite(xx).all(axis=-1);models={'time_only':[5],'behavior_only':list(range(5)),'combined':list(range(6))};out=[];pooled=[]
    for mode,timing in enumerate(('common_frame','positive_delay_sensitivity')):
        buckets={name:[] for name in models}
        for held in range(10):
            test=valid.copy();test[:,:held]=False;test[:,held+1:]=False
            if not test.any():continue
            train=valid&~test;counts=train.sum(axis=1,keepdims=True);assert (counts>0).all()
            y=yd['values'][mode];my=np.where(train[...,None],y,0).sum(axis=1,keepdims=True)/counts[...,None]
            mx=np.where(train[...,None],xx,0).sum(axis=1,keepdims=True)/counts[...,None]
            ry=y-my;dx=xx-mx;z=dx/dx[train].std(axis=0)
            for name,cols in models.items():
                a=z[train][:,cols];b=z[test][:,cols]
                coef,_,rank,_=np.linalg.lstsq(a,ry[train],rcond=1e-12);assert rank==len(cols)
                baseline=ry[test];error=baseline-b@coef;inside=((b>=a.min(axis=0))&(b<=a.max(axis=0))).all(axis=1)
                scores={key:score(baseline,error,mask) for key,mask in [('all',np.ones(len(b),dtype=bool)),('inside',inside),('outside',~inside)]}
                old=next(r for r in previous['prediction_scores'] if r['timing']==timing and r['held_repeat_one_based']==held+1 and r['model']==name)
                assert np.isclose(scores['all']['median_relative_skill'],old['median_relative_skill'],rtol=0,atol=1e-12)
                assert scores['inside']['rows']+scores['outside']['rows']==scores['all']['rows']
                assert np.allclose((error**2).sum(axis=0),(error[inside]**2).sum(axis=0)+(error[~inside]**2).sum(axis=0))
                out.append(dict(timing=timing,model=name,held_repeat_one_based=held+1,**scores));buckets[name].append((baseline,error,inside))
        for name,parts in buckets.items():
            baseline=np.concatenate([v[0] for v in parts]);error=np.concatenate([v[1] for v in parts]);inside=np.concatenate([v[2] for v in parts])
            pooled.append(dict(timing=timing,model=name,inside=score(baseline,error,inside),outside=score(baseline,error,~inside),limits='Pooled held-repeat errors; not independent samples or a confidence interval.'))
    save('microns_behavior_range_result.json',dict(folds=out,pooled=pooled,status='FIXED_MODEL_RANGE_DIAGNOSTIC',limits='A positive subgroup does not rescue full-population adjustment; no causal interpretation.'))
    for r in pooled:
        if r['timing']=='positive_delay_sensitivity':print(r)
    for r in out:
        if r['timing']=='positive_delay_sensitivity' and r['model']=='behavior_only':print('behavior',r['held_repeat_one_based'],r['inside'])


if __name__=='__main__':main()
