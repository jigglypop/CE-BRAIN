"""Fixed pre-well classifiers transferred to odor-period activity.

All fitting and model selection use approach windows only, within one original
recording epoch. Transfer scores are descriptive and do not establish retrieval.
"""
import argparse
import hashlib
import importlib.util
import json
from collections import Counter
from pathlib import Path

import numpy as np
import scipy
from scipy.special import expit

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
MODELS=('motion','ca1','pfc','joint','motion_ca1','motion_pfc','motion_joint')
FULL_RATS={'CS31','CS33','CS34','CS35','CS39'}
PINS={
 HERE/'odor_place_choice_readout.py':'7cbf0eeedd7b9f456fb3c29910095a4b6b1475ec4a9a648c94e5ca41cc55ec1e',
 HERE/'odor_place_windows_complete_result.json':'4df360cb600b6894cdaec746e6cb9843aedada5f4efc671f0aa8ca32a4dca166',
 HERE/'odor_place_tetrode_regions_result.json':'30c74fb53563a56a190469a62143f4c5ce0bef427307b7bc14c275820e4b7891',
}


def sha(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def estimator():
    path=HERE/'odor_place_choice_readout.py'
    if sha(path)!=PINS[path]:raise ValueError('Frozen estimator changed')
    spec=importlib.util.spec_from_file_location('frozen_choice_estimator',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def designs(counts,motion,regions):
    counts=np.asarray(counts);motion=np.asarray(motion,float)
    if counts.ndim!=2 or motion.shape!=(len(counts),8) or len(regions)!=counts.shape[1]:raise ValueError('Design dimensions differ')
    if np.any(counts<0) or not np.isfinite(counts).all() or not np.isfinite(motion).all():raise ValueError('Invalid observed features')
    c=np.sqrt(counts.astype(float)+.375)
    masks={r:np.asarray(regions)==r for r in ('CA1','PFC')}
    if not all(v.any() for v in masks.values()):raise ValueError('Both regions required')
    ca1=c[:,masks['CA1']];pfc=c[:,masks['PFC']];joint=c[:,masks['CA1']|masks['PFC']]
    return dict(motion=motion,ca1=ca1,pfc=pfc,joint=joint,motion_ca1=np.c_[motion,ca1],
                motion_pfc=np.c_[motion,pfc],motion_joint=np.c_[motion,joint])


def epoch_blocks(session,common):
    if common.shape!=(len(session['trials']),) or common.dtype!=bool:raise ValueError('Invalid common mask')
    groups={}
    for j,t in enumerate(session['trials']):
        key=(t['source_epoch'],t['task_epoch_row'])
        groups.setdefault(key,[])
        if common[j]:groups[key].append(j)
    return [(key,np.asarray(ids,int)) for key,ids in sorted(groups.items())]


def prior_logits(y,cue,target_cue):
    """Smoothed training-only marginal and cue-conditioned reference scores."""
    y=np.asarray(y);cue=np.asarray(cue)
    if set(np.unique(y))!={0,1}:raise ValueError('Both training outcomes required')
    marginal=float(np.log((y.sum()+.5)/(len(y)-y.sum()+.5)))
    bycue=[]
    for c in (0,1):
        values=y[cue==c]
        if not len(values):raise ValueError('Both training cues required')
        bycue.append(float(np.log((values.sum()+.5)/(len(values)-values.sum()+.5))))
    return marginal,np.asarray(bycue)[np.asarray(target_cue,int)]


def fit_transfer(source,targets,y,ids,train,held,engine):
    """No target-period activity or held labels enter source fitting/tuning."""
    if set(train)&set(held):raise ValueError('Training/held overlap')
    model,selection=engine.tune_fit(source[train],y[train],ids[train])
    predicted={name:engine.logits(x[held],model) for name,x in targets.items()}
    return predicted,model,selection


def auc(score,y):
    positive=np.asarray(score)[np.asarray(y)==1];negative=np.asarray(score)[np.asarray(y)==0]
    if not len(positive) or not len(negative):return None
    delta=positive[:,None]-negative[None,:]
    return float(np.mean((delta>0)+.5*(delta==0)))


def scores(eta,y,cue,fold_ids,engine):
    p=expit(eta);loss=engine.losses(eta,y);error=y!=cue
    cells=[]
    for fold in sorted(set(fold_ids.tolist())):
        for c in (0,1):
            mask=(fold_ids==fold)&(cue==c);value=auc(eta[mask],y[mask])
            if value is not None:cells.append(value)
    return dict(log_loss=float(loss.mean()),brier=float(np.mean((p-y)**2)),accuracy=float(np.mean((p>=.5)==y)),
        correct_trials=int((~error).sum()),incorrect_trials=int(error.sum()),
        correct_log_loss=float(loss[~error].mean()) if (~error).any() else None,
        incorrect_choice_log_loss=float(loss[error].mean()) if error.any() else None,
        incorrect_cue_log_loss=float(engine.losses(eta[error],cue[error]).mean()) if error.any() else None,
        incorrect_choice_over_cue_nats=float(np.mean(engine.losses(eta[error],cue[error])-loss[error])) if error.any() else None,
        within_fold_cue_auc_mean=float(np.mean(cells)) if cells else None,within_fold_cue_auc_cells=len(cells))


def bernoulli_metric(eta,covector):
    """Readout pullback in the supplied feature coordinates; rank at most one."""
    covector=np.asarray(covector,float)
    if covector.ndim!=1 or not np.isfinite(covector).all() or not np.isfinite(eta):raise ValueError('Invalid metric input')
    p=expit(eta)
    return p*(1-p)*np.outer(covector,covector)


def evaluate_block(session,ids,block_key,phase_designs,engine):
    base=dict(source_epoch=block_key[0],task_epoch_row=block_key[1],common_trials=len(ids))
    if len(ids)<15:return dict(**base,status='insufficient_common_windows'),{}
    y=np.array([session['trials'][j]['choice_right'] for j in ids],int)
    cue=np.array([int(session['trials'][j]['odor_side']=='right') for j in ids],int)
    outer=engine.folds(ids,5)
    support=[engine.four_cells(cue[train],y[train]) for train,_ in outer]
    if not all(support):return dict(**base,status='outer_train_missing_cue_choice_cell',fold_support=support),{}
    windows=list(phase_designs)
    predictions={w:{name:np.zeros(len(ids)) for name in MODELS} for w in windows}
    marginal=np.zeros(len(ids));cue_prior=np.zeros(len(ids));fold_ids=np.full(len(ids),-1,int);fits=[]
    for fold,(train,held) in enumerate(outer):
        fold_ids[held]=fold;marginal[held],cue_prior[held]=prior_logits(y[train],cue[train],cue[held])
        rec=dict(fold=fold,training_trial_indices=ids[train].tolist(),held_trial_indices=ids[held].tolist(),models={})
        for name in MODELS:
            source=phase_designs['approach'][name][ids]
            targets={w:phase_designs[w][name][ids] for w in windows}
            predicted,model,selection=fit_transfer(source,targets,y,ids,train,held,engine)
            for w in windows:predictions[w][name][held]=predicted[w]
            covector=model['coef'][1:]/model['scale']
            rec['models'][name]=dict(**selection,mean=model['mean'].tolist(),scale=model['scale'].tolist(),
                coef=model['coef'].tolist(),training_trials=len(train),iterations=model['iterations'],gradient_max=model['gradient_max'],
                readout_metric_feature_dimension=len(covector),readout_metric_rank_upper_bound=1,
                readout_covector_squared_norm=float(covector@covector))
        fits.append(rec)
    prior_loss=engine.losses(marginal,y);cue_loss=engine.losses(cue_prior,y)
    rows={};payload=dict(trial_indices=ids,choice_right=y,cue_right=cue,fold_ids=fold_ids,
                         marginal_prior_logits=marginal,cue_prior_logits=cue_prior)
    for window in windows:
        rows[window]=dict(models={name:scores(eta,y,cue,fold_ids,engine) for name,eta in predictions[window].items()},
            gain_vs_marginal_nats={name:float(np.mean(prior_loss-engine.losses(eta,y))) for name,eta in predictions[window].items()},
            gain_vs_cue_prior_nats={name:float(np.mean(cue_loss-engine.losses(eta,y))) for name,eta in predictions[window].items()},
            neural_increment_over_motion_nats={name:float(np.mean(engine.losses(predictions[window]['motion'],y)-engine.losses(predictions[window][name],y))) for name in ('motion_ca1','motion_pfc','motion_joint')})
        payload.update({window+'_'+name+'_logits':eta for name,eta in predictions[window].items()})
    return dict(**base,status='evaluated',correct_trials=int((y==cue).sum()),incorrect_trials=int((y!=cue).sum()),
                prior_log_loss=float(prior_loss.mean()),cue_prior_log_loss=float(cue_loss.mean()),windows=rows,folds=fits),payload


def mean_or_none(values):
    values=[v for v in values if v is not None]
    return float(np.mean(values)) if values else None


def aggregate(rows,windows):
    evaluated=[r for r in rows if r['status']=='evaluated']
    def window_mean(records,w):
        return dict(gain_vs_marginal_nats={n:mean_or_none([r['windows'][w]['gain_vs_marginal_nats'][n] for r in records]) for n in MODELS},
            gain_vs_cue_prior_nats={n:mean_or_none([r['windows'][w]['gain_vs_cue_prior_nats'][n] for r in records]) for n in MODELS},
            neural_increment_over_motion_nats={n:mean_or_none([r['windows'][w]['neural_increment_over_motion_nats'][n] for r in records]) for n in ('motion_ca1','motion_pfc','motion_joint')},
            incorrect_choice_over_cue_nats={n:mean_or_none([r['windows'][w]['models'][n]['incorrect_choice_over_cue_nats'] for r in records]) for n in MODELS},
            within_fold_cue_auc={n:mean_or_none([r['windows'][w]['models'][n]['within_fold_cue_auc_mean'] for r in records]) for n in MODELS})
    # Blocks -> equal session means -> equal rat means, preserving nesting.
    sessions={}
    for identifier in sorted({r['identifier'] for r in evaluated}):
        sample=[r for r in evaluated if r['identifier']==identifier]
        sessions[identifier]=dict(rat=sample[0]['rat'],blocks=len(sample),trials=sum(r['common_trials'] for r in sample),
                                  windows={w:window_mean(sample,w) for w in windows})
    def merge_windows(records):
        return {w:{metric:{name:mean_or_none([r['windows'][w][metric][name] for r in records])
                          for name in records[0]['windows'][w][metric]}
                   for metric in records[0]['windows'][w]} for w in windows} if records else {}
    rats={}
    for rat in sorted({r['rat'] for r in sessions.values()}):
        sample=[r for r in sessions.values() if r['rat']==rat]
        rats[rat]=dict(sessions=len(sample),blocks=sum(r['blocks'] for r in sample),trials=sum(r['trials'] for r in sample),windows=merge_windows(sample))
    strata={}
    for name,members in [('full_maze',FULL_RATS),('shortened_stem',{'CS44'}),('adjacent_wells',{'CS41','CS42'})]:
        sample=[r for rat,r in rats.items() if rat in members]
        strata[name]=dict(rats=sorted(set(rats)&members),sessions=sum(r['sessions'] for r in sample),
            trials=sum(r['trials'] for r in sample),rat_equal_windows=merge_windows(sample))
    return dict(input_blocks=len(rows),status_blocks=dict(Counter(r['status'] for r in rows)),
        evaluated_blocks=len(evaluated),evaluated_sessions=len(sessions),evaluated_rats=len(rats),
        evaluated_trials=sum(r['common_trials'] for r in evaluated),sessions=sessions,rats=rats,strata=strata)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--approach',type=Path,required=True);parser.add_argument('--approach-sha',required=True)
    args=parser.parse_args();output=HERE/'odor_place_phase_transfer_result.json'
    npz_path=ROOT/'data/local/hippocampal-reinstatement/odor-place-phase-transfer-v1/predictions.npz'
    if output.exists() or npz_path.exists():raise FileExistsError('Preserve previous phase transfer')
    for path,digest in {**PINS,args.approach:args.approach_sha}.items():
        if sha(path)!=digest:raise ValueError('Frozen input changed: '+str(path))
    engine=estimator();parent=json.loads((HERE/'odor_place_windows_complete_result.json').read_text(encoding='utf-8'))
    approach=json.loads(args.approach.read_text(encoding='utf-8'))
    regions=json.loads((HERE/'odor_place_tetrode_regions_result.json').read_text(encoding='utf-8'))
    region_lookup=engine.region_lookup(parent['sessions'],regions['sessions'])
    a_lookup={s['asset_id']:s for s in approach['sessions']}
    if len(a_lookup)!=len(approach['sessions']) or set(a_lookup)!={s['asset_id'] for s in parent['sessions']}:raise ValueError('Approach coverage differs')
    for result in (parent,approach):
        if sha(ROOT/result['npz']['path'])!=result['npz']['sha256']:raise ValueError('Window array changed')
    original=np.load(ROOT/parent['npz']['path'],allow_pickle=False);extra=np.load(ROOT/approach['npz']['path'],allow_pickle=False)
    rows=[];payload={};windows=['approach',*parent['windows']]
    for session in parent['sessions']:
        a=a_lookup[session['asset_id']];r=region_lookup[session['asset_id']]
        if a['unit_ids']!=session['unit_ids'] or not all(r['source_area_verified']):raise ValueError('Unit/region identity differs')
        if len(a['trials'])!=len(session['trials']):raise ValueError('Trial coverage differs')
        for j,(left,right) in enumerate(zip(a['trials'],session['trials'])):
            if left['trial_index']!=j or any(left[k]!=right[k] for k in ('trial_id','source_epoch','task_epoch_row')):raise ValueError('Trial identity differs')
        ac={k:extra[v] for k,v in a['npz_keys'].items()};old={k:original[v] for k,v in session['npz_keys'].items()}
        if not np.array_equal(ac['common_valid'],ac['valid']&old['valid'].all(axis=1)):raise ValueError('Common mask differs')
        phase_designs={'approach':designs(ac['counts'],ac['motion'],r['regions'])}
        phase_designs.update({w:designs(old['counts'][:,wi],old['motion'][:,wi],r['regions']) for wi,w in enumerate(parent['windows'])})
        for key,ids in epoch_blocks(session,ac['common_valid']):
            row,values=evaluate_block(session,ids,key,phase_designs,engine)
            prefix=session['identifier']+'_e'+str(key[0])+'_t'+str(key[1])
            row.update(identifier=session['identifier'],rat=session['rat'],asset_id=session['asset_id'],block_id=prefix)
            rows.append(row);payload.update({prefix+'_'+k:v for k,v in values.items()})
            print(json.dumps(dict(block_id=prefix,status=row['status'],trials=row['common_trials'])),flush=True)
    summary=aggregate(rows,windows)
    npz_path.parent.mkdir(parents=True,exist_ok=True)
    with npz_path.open('xb') as f:np.savez_compressed(f,**payload)
    result=dict(schema='hippocampal.odor-place-phase-transfer.v1',source_sha256=sha(__file__),
        test_sha256=sha(ROOT/'tests/test_odor_place_phase_transfer.py'),
        inputs=[dict(path=p.relative_to(ROOT).as_posix() if p.is_relative_to(ROOT) else str(p),sha256=h) for p,h in {**PINS,args.approach:args.approach_sha}.items()],
        versions=dict(numpy=np.__version__,scipy=scipy.__version__),models=list(MODELS),windows=windows,
        training='Approach only, same original source/task epoch; 5 ordered outer folds, purge +/-1 original trial; 3 inner folds choose L2 .03/.3/3.',
        transfer='One source-fitted normalization/intercept/coefficients/lambda applied unchanged to all held target phases. No target-phase tuning or recalibration.',
        cohort_rule='All five windows supported; >=15 trials; four cue-choice cells in every outer training set. No positive-control performance selection.',
        aggregation='Trial mean in each epoch block; equal blocks per session; equal sessions per rat; separate maze strata. No cross-rat fitting.',
        rows=rows,summary=summary,npz=dict(path=npz_path.relative_to(ROOT).as_posix(),bytes=npz_path.stat().st_size,sha256=sha(npz_path)),
        interpretation='Shared label-aligned approach/cue coding only if transfer supports it. Approach includes motion, location, expectation and action; Position does not identify head direction. '
                       'Correct trials confound cue and selected well; errors are scored separately. Motion-model transfer can also fail under phase shift, so its improvement alone does not establish conditional content information. '
                       'A scalar Bernoulli readout pullback has rank at most1; it does not identify a positive-definite full-neuron Riemannian metric, directed coupling, retrieval causality or learning-induced change.')
    with output.open('x',encoding='utf-8') as f:json.dump(result,f,indent=2,allow_nan=False)
    print(json.dumps({k:summary[k] for k in ('input_blocks','status_blocks','evaluated_blocks','evaluated_sessions','evaluated_rats','evaluated_trials')}),flush=True)


if __name__=='__main__':main()
