"""이미 열람한 두 세션 간 행동–발화 모형의 탐색적 수치 전이."""
import json
from pathlib import Path
import numpy as np
from population_reciprocity import sha
from superficial_ee_eligibility import save
HERE=Path(__file__).resolve().parent
def read(n):return json.loads((HERE/n).read_text(encoding='utf-8'))
def design(x):return np.column_stack([np.ones(len(x)),np.log1p(x)])
def metrics(y,p):
    e=y-p
    return dict(mse=float(np.mean(e**2)),mae=float(np.mean(abs(e))),mean_residual=float(e.mean()),residual_variance=float(np.mean((e-e.mean())**2)))
def main():
    inputs=['icms_catch_wheel_coupling_result.json','icms_supported_interval_result.json','icms98_next_session_result.json']
    save('icms98_behavior_model_transfer_contract.json',dict(
        code_sha256=sha(Path(__file__)),inputs={n:sha(HERE/n) for n in inputs},
        status='EXPLORATORY_BOTH_SESSIONS_PREVIOUSLY_OBSERVED',
        objective='Distinguish repeated association sign from portable firing magnitude in ICMS98 catch trials.',
        models=['constant training mean','OLS intercept plus log1p(post-window processed wheel TV)'],
        target='Mean-unit post minus pre firing Hz in same no-response good catch trials; preserve both anchors.',
        train='2023-10-20 only. Leave one original block out internally, then fit all31 development catches.',
        evaluation='Apply frozen development coefficients to36 catches on2023-10-24; report MSE MAE mean residual variance and development TV-range support. No target refit or offset correction.',
        gate='Descriptive improvement only if smaller MSE than training-mean baseline on both development block-CV and later-session transfer for both anchors.',
        limits='Post-window wheel is concurrent outcome information, not a prospective predictor or causal adjustment. Arbitrary wheel units and unit populations may drift. No L2 or causal promotion.'))
    dev=next(s for s in read(inputs[0])['subjects'] if s['subject']=='ICMS98')['trials']
    scope=next(s for s in read(inputs[1])['sessions'] if s['subject']=='ICMS98')
    mapping={r['trial_id']:r['block'] for r in scope['trials']}
    blocks=np.array([mapping[r['trial_id']] for r in dev]);later=read(inputs[2])['trials'];summaries=[]
    assert len(dev)==31 and len(later)==36
    for k in (0,1):
        x=np.array([r['variants'][k]['post']['tv'] for r in dev]);y=np.array([r['variants'][k]['mean_unit_change_hz'] for r in dev])
        tx=np.array([r['variants'][k]['wheel'][1]['tv'] for r in later]);ty=np.array([r['variants'][k]['mean_unit_change_hz'] for r in later])
        assert np.isfinite(np.r_[x,y,tx,ty]).all() and min(x)>=0 and min(tx)>=0
        cv=np.zeros(len(y));cv0=np.zeros(len(y));folds=[]
        for b in range(4):
            train=blocks!=b;test=~train
            coef=np.linalg.lstsq(design(x[train]),y[train],rcond=None)[0]
            cv[test]=design(x[test])@coef;cv0[test]=y[train].mean()
            folds.append(dict(block=b,coefficients=coef.tolist(),trials=int(test.sum()),model=metrics(y[test],cv[test]),baseline=metrics(y[test],cv0[test])))
        coef=np.linalg.lstsq(design(x),y,rcond=None)[0];pred=design(tx)@coef;baseline=np.full(len(ty),y.mean())
        # Verify the two-parameter fit without invoking the least-squares solver.
        z=np.log1p(x);slope=float(np.dot(z-z.mean(),y-y.mean())/np.dot(z-z.mean(),z-z.mean()))
        assert np.allclose(coef,[y.mean()-slope*z.mean(),slope],atol=1e-12)
        support=(tx>=x.min())&(tx<=x.max())
        summaries.append(dict(anchor=('trial_start','shifted')[k],coefficients=coef.tolist(),development_mean=float(y.mean()),later_mean=float(ty.mean()),
            block_cv=dict(model=metrics(y,cv),baseline=metrics(y,cv0),folds=folds),
            transfer=dict(model=metrics(ty,pred),baseline=metrics(ty,baseline),within_development_range=int(support.sum()),outside_trial_ids=[r['trial_id'] for r,ok in zip(later,support) if not ok]),
            development_tv_range=[float(x.min()),float(x.max())],later_tv_range=[float(tx.min()),float(tx.max())],
            predictions=[dict(trial_id=r['trial_id'],observed=float(a),predicted=float(p),baseline=float(v)) for r,a,p,v in zip(later,ty,pred,baseline)]))
    improved=all(s[stage]['model']['mse']<s[stage]['baseline']['mse'] for s in summaries for stage in ('block_cv','transfer'))
    save('icms98_behavior_model_transfer_result.json',dict(status='DESCRIPTIVE_IMPROVEMENT' if improved else 'DESCRIPTIVE_CRITERION_FAILED',summaries=summaries))
    for s in summaries:
        print(s['anchor'],'coef',s['coefficients'],'cv',s['block_cv']['model'],s['block_cv']['baseline'],'transfer',s['transfer'])
if __name__=='__main__':main()
