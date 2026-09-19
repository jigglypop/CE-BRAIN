"""Conditional choice readout with time-blocked, nested validation.

Inputs are deposited sorted-event counts and observed position. This is a
retrospective association test conditional on cue and behavior, not an online
forecast, recall-content proof, or verification of biological silence.
"""
import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

import numpy as np
import scipy
from scipy.optimize import minimize
from scipy.special import expit

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
LAMBDAS=(.03,.3,3.)
MODELS=('behavior','ca1_current','pfc_current','joint_current','joint_current_history')
Q_NAMES=('cue_right','trial_ordinal','elapsed_s','previous_cue_right','previous_choice_right',
         'previous_correct','previous_known','previous_gap_s','neural_history_known',
         'mean_x_cm','mean_y_cm','mean_speed_cm_s','sd_speed_cm_s','delta_x_cm','delta_y_cm',
         'path_length_cm','max_speed_cm_s')


def sha(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def folds(original_ids, count=5, purge=1):
    ids=np.asarray(original_ids,int)
    if len(ids)<count or np.any(np.diff(ids)<=0):raise ValueError('Ordered distinct trial identities required')
    out=[]
    for held in np.array_split(np.arange(len(ids)),count):
        train=np.flatnonzero((ids<ids[held[0]]-purge)|(ids>ids[held[-1]]+purge))
        if len(train)<2:raise ValueError('Insufficient purged training trials')
        out.append((train,held))
    return out


def four_cells(cue,y):
    return all(np.any((cue==c)&(y==choice)) for c in (0,1) for choice in (0,1))


def fit_logistic(x,y,lam):
    x=np.asarray(x,float);y=np.asarray(y,float)
    if x.ndim!=2 or len(x)!=len(y) or not np.isfinite(x).all() or set(np.unique(y))!={0.,1.} or lam<=0:
        raise ValueError('Invalid logistic training data')
    mean=x.mean(axis=0);scale=x.std(axis=0);scale=np.where(scale>1e-10,scale,1.)
    z=(x-mean)/scale
    def objective(w):
        eta=w[0]+z@w[1:]
        residual=expit(eta)-y
        value=np.mean(np.logaddexp(0,eta)-y*eta)+.5*lam*np.dot(w[1:],w[1:])
        grad=np.r_[residual.mean(),z.T@residual/len(y)+lam*w[1:]]
        return value,grad
    initial=np.zeros(x.shape[1]+1);initial[0]=np.log((y.sum()+.5)/(len(y)-y.sum()+.5))
    result=minimize(objective,initial,method='L-BFGS-B',jac=True,
                    options=dict(maxiter=500,ftol=1e-12,gtol=1e-8))
    if not result.success or not np.isfinite(result.x).all():raise RuntimeError('Fit failed: '+str(result.message))
    return dict(mean=mean,scale=scale,coef=result.x,lambda_value=lam,training_trials=len(y),
                iterations=int(result.nit),gradient_max=float(np.max(np.abs(result.jac))))


def logits(x,model):
    return model['coef'][0]+((np.asarray(x)-model['mean'])/model['scale'])@model['coef'][1:]


def losses(eta,y):
    return np.logaddexp(0,eta)-np.asarray(y)*eta


def tune_fit(x,y,ids):
    inner=folds(ids,3)
    scores=[]
    for lam in LAMBDAS:
        values=[]
        for train,held in inner:
            if len(np.unique(y[train]))<2:continue
            fit=fit_logistic(x[train],y[train],lam)
            values.append(float(losses(logits(x[held],fit),y[held]).mean()))
        if len(values)<2:raise ValueError('Insufficient inner training class support')
        scores.append(float(np.mean(values)))
    selected=min(range(len(scores)),key=lambda i:(scores[i],-LAMBDAS[i]))
    model=fit_logistic(x,y,LAMBDAS[selected])
    return model,dict(lambdas=list(LAMBDAS),inner_mean_log_loss=scores,selected_lambda=LAMBDAS[selected])


def fit_outer_fold(x,y,ids,train,held):
    if set(train)&set(held):raise ValueError('Outer fold overlap')
    model,selection=tune_fit(x[train],y[train],ids[train])
    return logits(x[held],model),model,selection


def feature_sets(session,arrays,regions,wi):
    trials=session['trials'];valid=arrays['valid'].all(axis=1)
    selected=np.flatnonzero(valid)
    current=np.sqrt(arrays['counts'][selected,wi].astype(float)+.375)
    history=np.zeros_like(current)
    q=[]
    for row,j in enumerate(selected):
        t=trials[j];start=t['windows'][session['_window_names'][wi]]['start_s']
        previous=trials[j-1] if j else None
        known=bool(previous and previous['task_epoch_row']==t['task_epoch_row']
                   and previous['source_epoch']==t['source_epoch']
                   and previous['choice_time_s'] is not None and previous['choice_time_s']<start)
        history_known=bool(known and arrays['valid'][j-1,wi]
                           and previous['windows'][session['_window_names'][wi]]['stop_s']<=start)
        if history_known:history[row]=np.sqrt(arrays['counts'][j-1,wi].astype(float)+.375)
        q.append([int(t['odor_side']=='right'),j,t['start_s']-trials[0]['start_s'],
                  int(previous['odor_side']=='right') if known else 0,
                  previous['choice_right'] if known else 0,int(previous['correct']) if known else 0,
                  int(known),start-previous['stop_s'] if known else 0,int(history_known),
                  *arrays['motion'][j,wi].tolist()])
    q=np.asarray(q,float)
    masks={r:np.asarray(regions)==r for r in ('CA1','PFC')}
    if not all(np.any(v) for v in masks.values()):raise ValueError('Both source-supported regions required')
    joint=masks['CA1']|masks['PFC']
    designs=dict(behavior=q,ca1_current=np.c_[q,current[:,masks['CA1']]],
                 pfc_current=np.c_[q,current[:,masks['PFC']]],joint_current=np.c_[q,current[:,joint]],
                 joint_current_history=np.c_[q,current[:,joint],history[:,joint]])
    y=np.array([trials[j]['choice_right'] for j in selected],int)
    cue=np.array([int(trials[j]['odor_side']=='right') for j in selected],int)
    return selected,designs,y,cue


def metrics(eta,y,cue):
    p=expit(eta);loss=losses(eta,y)
    return dict(log_loss=float(loss.mean()),brier=float(np.mean((p-y)**2)),
                accuracy=float(np.mean((p>=.5)==y)),
                cue_equal_log_loss=float(np.mean([loss[cue==c].mean() for c in (0,1)])))


def evaluate(session,arrays,region):
    selected=np.flatnonzero(arrays['valid'].all(axis=1))
    if len(selected)<15:return dict(status='insufficient_common_windows',common_trials=len(selected)),{}
    y=np.array([session['trials'][j]['choice_right'] for j in selected],int)
    cue=np.array([int(session['trials'][j]['odor_side']=='right') for j in selected],int)
    outer=folds(selected,5)
    support=[four_cells(cue[train],y[train]) for train,_ in outer]
    if not all(support):return dict(status='outer_train_missing_cue_choice_cell',common_trials=len(selected),fold_support=support),{}
    rows={};payload={}
    for wi,window in enumerate(session['_window_names']):
        ids,designs,y,cue=feature_sets(session,arrays,region['regions'],wi)
        predictions={name:np.zeros(len(ids)) for name in MODELS};fits=[]
        for fold,(train,held) in enumerate(outer):
            record=dict(fold=fold,training_trial_ids=ids[train].tolist(),held_trial_ids=ids[held].tolist(),models={})
            for name in MODELS:
                x=designs[name]
                eta,model,selection=fit_outer_fold(x,y,ids,train,held);predictions[name][held]=eta
                record['models'][name]=dict(**selection,mean=model['mean'].tolist(),scale=model['scale'].tolist(),
                                            coef=model['coef'].tolist(),training_trials=len(train),
                                            iterations=model['iterations'],gradient_max=model['gradient_max'])
            fits.append(record)
        scores={name:metrics(predictions[name],y,cue) for name in MODELS}
        base=losses(predictions['behavior'],y)
        gain={name:float(np.mean(base-losses(predictions[name],y))) for name in MODELS if name!='behavior'}
        history_gain=float(np.mean(losses(predictions['joint_current'],y)-losses(predictions['joint_current_history'],y)))
        rows[window]=dict(scores=scores,gain_vs_behavior_nats=gain,history_increment_nats=history_gain,folds=fits)
        for name,eta in predictions.items():payload[window+'_'+name+'_logits']=eta
    payload.update(trial_ids=selected,choice_right=y,cue_right=cue)
    return dict(status='evaluated',common_trials=len(selected),windows=rows),payload


def aggregate(rows,windows):
    evaluated=[r for r in rows if r['status']=='evaluated']
    rats=sorted({r['rat'] for r in evaluated});out={}
    for window in windows:
        byrat={}
        for rat in rats:
            sample=[r for r in evaluated if r['rat']==rat]
            byrat[rat]=dict(sessions=len(sample),trials=sum(s['common_trials'] for s in sample),
                gains={name:float(np.mean([s['windows'][window]['gain_vs_behavior_nats'][name] for s in sample])) for name in MODELS if name!='behavior'},
                history_increment_nats=float(np.mean([s['windows'][window]['history_increment_nats'] for s in sample])))
        out[window]=dict(rats=byrat,rat_equal_gain_nats={name:float(np.mean([r['gains'][name] for r in byrat.values()])) for name in MODELS if name!='behavior'},
                        rat_equal_history_increment_nats=float(np.mean([r['history_increment_nats'] for r in byrat.values()])))
    return dict(input_sessions=len(rows),status_sessions=dict(Counter(r['status'] for r in rows)),
                status_common_trials={status:sum(r['common_trials'] for r in rows if r['status']==status) for status in sorted({r['status'] for r in rows})},
                evaluated_sessions=len(evaluated),evaluated_rats=rats,
                evaluated_trials=sum(r['common_trials'] for r in evaluated),windows=out)


def region_lookup(window_rows,region_rows):
    lookup={r['asset_id']:r for r in region_rows}
    window_ids={s['asset_id'] for s in window_rows}
    if len(lookup)!=len(region_rows) or len(window_ids)!=len(window_rows):raise ValueError('Duplicate asset identity')
    if window_ids!={r['asset_id'] for r in region_rows if r['eligible']}:raise ValueError('Regional cohort coverage differs')
    for s in window_rows:
        r=lookup[s['asset_id']];n=len(s['unit_ids'])
        if s['unit_ids']!=r['unit_ids'] or len(set(s['unit_ids']))!=n:raise ValueError('Unit identity/order differs')
        if len(r['regions'])!=n or len(r['source_area_verified'])!=n:raise ValueError('Region/unit lengths differ')
        if any(not isinstance(v,bool) for v in r['source_area_verified']):raise ValueError('Invalid source support flags')
        if any(not isinstance(v,str) or not v for v in r['regions']):raise ValueError('Invalid source region label')
    return lookup


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--windows',type=Path,required=True);parser.add_argument('--windows-sha',required=True)
    parser.add_argument('--regions',type=Path,required=True);parser.add_argument('--regions-sha',required=True)
    args=parser.parse_args()
    output=HERE/'odor_place_choice_readout_result.json'
    npz_path=ROOT/'data/local/hippocampal-reinstatement/odor-place-choice-readout-v1/predictions.npz'
    if output.exists() or npz_path.exists():raise FileExistsError('Preserve previous choice readout')
    if sha(args.windows)!=args.windows_sha or sha(args.regions)!=args.regions_sha:raise ValueError('Frozen inputs changed')
    windows=json.loads(args.windows.read_text(encoding='utf-8'));region=json.loads(args.regions.read_text(encoding='utf-8'))
    path=ROOT/windows['npz']['path']
    if sha(path)!=windows['npz']['sha256']:raise ValueError('Window arrays changed')
    npz=np.load(path,allow_pickle=False);regions=region_lookup(windows['sessions'],region['sessions'])
    rows=[];payload={}
    for session in windows['sessions']:
        r=regions[session['asset_id']]
        if session['unit_ids']!=r['unit_ids']:raise ValueError('Unit ordering differs')
        if not all(r['source_area_verified']):
            row=dict(status='original_region_support_incomplete',common_trials=0)
        else:
            session['_window_names']=windows['windows']
            arrays={k:npz[v] for k,v in session['npz_keys'].items()}
            row,values=evaluate(session,arrays,r)
            payload.update({session['identifier']+'_'+k:v for k,v in values.items()})
        row.update(identifier=session['identifier'],asset_id=session['asset_id'],rat=session['rat'])
        rows.append(row)
        print(json.dumps(dict(identifier=row['identifier'],status=row['status'],trials=row['common_trials'])),flush=True)
    summary=aggregate(rows,windows['windows'])
    npz_path.parent.mkdir(parents=True,exist_ok=True)
    with npz_path.open('xb') as f:np.savez_compressed(f,**payload)
    result=dict(schema='hippocampal.odor-place-choice-readout.v1',source_sha256=sha(__file__),
                test_sha256=sha(ROOT/'tests/test_odor_place_choice_readout.py'),
                inputs=dict(windows_path=str(args.windows),windows_sha256=args.windows_sha,
                            regions_path=str(args.regions),regions_sha256=args.regions_sha),
                versions=dict(numpy=np.__version__,scipy=scipy.__version__),
                models=list(MODELS),q_columns=list(Q_NAMES),lambdas=list(LAMBDAS),outer_blocks=5,inner_blocks=3,purge_trials=1,
                count_transform='sqrt(stored_count + 3/8); fold-training mean/std only',
                sessions=rows,summary=summary,
                npz=dict(path=npz_path.relative_to(ROOT).as_posix(),bytes=npz_path.stat().st_size,sha256=sha(npz_path)),
                interpretation='Positive gain is held-block choice log-score improvement over observed cue/motion/history covariates. '
                  'Current cue is conditioned on even in precue analysis, so these are retrospective conditional comparisons. '
                  'Trials are shared across windows and all windows use the same outer split. '
                  'Rat means weight sessions equally; no independent-unit or significance claim. '
                  'Sorted-count zeros are observations of the deposited event list, not verified biological silence. '
                  'Region evidence does not verify same-neuron continuity across source epochs; no cross-epoch lag is used. '
                  'Content reinstatement, causal direction, learning-induced coupling and a positive-definite brain metric remain unestablished.')
    with output.open('x',encoding='utf-8') as f:json.dump(result,f,indent=2,allow_nan=False)
    print(json.dumps(summary),flush=True)


if __name__=='__main__':main()
