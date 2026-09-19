"""Retrospective held-story identity calibration and within-identity story readout.

This is a new exploratory analysis of a previously inspected selected cohort.
No population holdout, chronological forecast, or causal retrieval claim.
"""
import hashlib
import importlib.util
import json
import platform
from pathlib import Path

import numpy as np
import scipy
from scipy.optimize import minimize
from scipy.special import expit

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PRIOR_SOURCE_SHA = 'e67c3dcfbedee1777104541743df8d619a34f1536a603a85a956e3bcc4a114de'
PRIOR_RESULT_SHA = '10d99fc4c7c8791035f33c6794c3c3308eda6d47d5f3f1a38b9bb336b9b5a210'


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def balanced_weights(labels):
    labels = np.asarray(labels,int)
    if labels.ndim!=1 or set(np.unique(labels))!={0,1}:
        raise ValueError('Two nonempty classes required')
    return np.asarray([.5/np.count_nonzero(labels==y) for y in labels])


def fit_logistic(features,labels,nonnegative=()):
    """Class-balanced loss plus fixed N(0,1) penalty on standardized coefficients.

Objective: balanced mean log loss + ||theta||^2/(2*n_training).
Feature centering/scaling and constant-column decisions use training only.
Nonnegative indices constrain direction of the frozen visual readout only.
"""
    x,y = np.asarray(features,float),np.asarray(labels,int)
    if x.ndim==1:
        x = x[:,None]
    if x.ndim!=2 or len(x)!=len(y) or not np.isfinite(x).all():
        raise ValueError('Invalid training data')
    weights = balanced_weights(y)
    mean = weights@x
    sd = np.sqrt(weights@((x-mean)**2))
    constant = sd<=1e-12
    scale = np.where(constant,1.,sd)
    design = np.column_stack([(x-mean)/scale,np.ones(len(x))])
    strength = 1./len(y)
    bounds = [(0.,0.) if constant[i] else (0.,None) if i in nonnegative else (None,None)
              for i in range(x.shape[1])]+[(None,None)]

    def loss_and_gradient(theta):
        score = design@theta
        loss = weights@(np.logaddexp(0.,score)-y*score)+.5*strength*(theta@theta)
        gradient = design.T@(weights*(expit(score)-y))+strength*theta
        return float(loss),gradient

    result = minimize(loss_and_gradient,np.zeros(design.shape[1]),jac=True,method='L-BFGS-B',
        bounds=bounds,options=dict(ftol=1e-13,gtol=1e-9,maxiter=2000,maxls=50))
    if not result.success or not np.isfinite(result.x).all():
        raise RuntimeError('Calibration did not converge: '+str(result.message))
    gradient = loss_and_gradient(result.x)[1]
    projected = gradient.copy()
    for i,(lower,upper) in enumerate(bounds):
        if lower is not None and upper==lower:
            projected[i] = 0.
        elif lower is not None and result.x[i]<=lower+1e-8 and gradient[i]>0:
            projected[i] = 0.
    if np.max(np.abs(projected))>1e-5:
        raise RuntimeError('Calibration gradient check failed')
    return dict(mean=mean.tolist(),scale=scale.tolist(),constant=constant.tolist(),
        coefficients=result.x.tolist(),nonnegative=list(nonnegative),regularization=strength,
        n_training=len(y),class_counts=[int(np.count_nonzero(y==i)) for i in (0,1)],
        objective=float(result.fun),projected_gradient_max=float(np.max(np.abs(projected))),iterations=int(result.nit))


def predict_logistic(features,model):
    x = np.asarray(features,float)
    if x.ndim==1:
        x = x[:,None]
    if x.ndim!=2 or x.shape[1]!=len(model['mean']) or not np.isfinite(x).all():
        raise ValueError('Invalid prediction features')
    design = np.column_stack([(x-model['mean'])/model['scale'],np.ones(len(x))])
    score = design@np.asarray(model['coefficients'])
    return np.column_stack([-np.logaddexp(0.,score),-np.logaddexp(0.,-score)])


def scores(log_probs,labels):
    log_probs,y = np.asarray(log_probs,float),np.asarray(labels,int)
    weights = balanced_weights(y)
    if log_probs.shape!=(len(y),2) or not np.isfinite(log_probs).all():
        raise ValueError('Invalid probabilities')
    if not np.allclose(np.exp(log_probs).sum(axis=1),1.,atol=1e-12,rtol=0):
        raise ValueError('Unnormalized probabilities')
    margin = log_probs[:,1]-log_probs[:,0]
    correct = np.where(margin==0,.5,((margin>0)==y).astype(float))
    delta = margin[y==1][:,None]-margin[y==0][None,:]
    log_loss = float(-weights@log_probs[np.arange(len(y)),y])
    return dict(accuracy=float(weights@correct),auc=float(np.mean((delta>0)+.5*(delta==0))),
        log_loss=log_loss,log_gain=float(np.log(2)-log_loss),
        brier=float(weights@((np.exp(log_probs[:,1])-y)**2)))


def identity_splits(stories,labels):
    stories,y = np.asarray(stories,int),np.asarray(labels,int)
    r,n = np.unique(stories[y==1]),np.unique(stories[y==0])
    if len(r)!=2 or len(n)!=2 or set(r)&set(n) or len(stories)!=len(y):
        raise ValueError('Two disjoint stories per identity required')
    result = []
    for rs in r:
        for ns in n:
            held = np.flatnonzero(np.isin(stories,[rs,ns]))
            train = np.flatnonzero(~np.isin(stories,[rs,ns]))
            result.append((train,held,dict(held_stories=[int(rs),int(ns)],train_stories=sorted(set(stories[train].tolist())))))
    return result


def story_splits(stories,trials,labels):
    """Within each identity, cross-fit two stored-trial halves of its two stories."""
    stories,trials,labels = np.asarray(stories,int),np.asarray(trials,int),np.asarray(labels,int)
    result = []
    for identity in (0,1):
        pair = sorted({int(story) for story in stories[labels==identity]})
        if len(pair)!=2:
            raise ValueError('Two stories per identity required')
        halves = [[],[]]
        for story in pair:
            indices = np.flatnonzero(stories==story)
            indices = indices[np.argsort(trials[indices],kind='stable')]
            if len(indices)<4 or len(set(trials[indices]))!=len(indices):
                raise ValueError('Insufficient or duplicated story repetitions')
            split = len(indices)//2
            halves[0].extend(indices[:split].tolist())
            halves[1].extend(indices[split:].tolist())
        for half in (0,1):
            train,held = np.asarray(halves[half],int),np.asarray(halves[1-half],int)
            context_labels = (stories==pair[1]).astype(int)
            result.append((train,held,context_labels,dict(identity=identity,stories=pair,training_stored_half=half)))
    return result


def story_eligibility(stories,trials):
    stories,trials = np.asarray(stories,int),np.asarray(trials,int)
    small = []
    for story in np.unique(stories):
        repeats = trials[stories==story]
        if len(set(repeats))!=len(repeats):
            raise ValueError('Duplicated story repetitions')
        if len(repeats)<4:
            small.append(dict(story=int(story),eligible_repetitions=len(repeats)))
    return dict(eligible=not small,minimum_repetitions_per_story=4,small_cells=small)


def mean_scores(folds):
    names = tuple(folds[0]['models'])
    return {name:{metric:float(np.mean([fold['models'][name]['scores'][metric] for fold in folds]))
                  for metric in ('accuracy','auc','log_loss','log_gain','brier')} for name in names}


def aggregate(units,branch):
    output = {}
    for region in ('all','H','A'):
        selected = [u for u in units if (region=='all' or u['region']==region) and u[branch].get('eligible',True)]
        sessions = sorted({u['session'] for u in selected})
        participants = sorted({u['participant'] for u in selected})
        block = dict(units=len(selected),sessions=len(sessions),participants=len(participants),models={})
        for name in selected[0][branch]['scores']:
            model = {}
            for metric in ('accuracy','auc','log_loss','log_gain','brier'):
                vals = [u[branch]['scores'][name][metric] for u in selected]
                per_session = {s:float(np.mean([u[branch]['scores'][name][metric] for u in selected if u['session']==s])) for s in sessions}
                per_person = {str(p):float(np.mean([per_session[s] for s in sorted({u['session'] for u in selected if u['participant']==p})])) for p in participants}
                model[metric] = dict(unit_mean=float(np.mean(vals)),session_mean=float(np.mean(list(per_session.values()))),
                    participant_mean=float(np.mean(list(per_person.values()))),by_participant=per_person,
                    by_session={str(k):v for k,v in per_session.items()})
            model['positive_log_gain_units'] = sum(u[branch]['scores'][name]['log_gain']>0 for u in selected)
            model['positive_log_gain_participants'] = sum(v>0 for v in model['log_gain']['by_participant'].values())
            block['models'][name] = model
        output[region] = block
    return output


def fitted_entry(train,held,features,labels,nonnegative,keys):
    if set(train)&set(held) or set(keys[train])&set(keys[held]):
        raise ValueError('Training/evaluation leakage')
    model = fit_logistic(features[train],labels[train],nonnegative)
    prediction = predict_logistic(features[held],model)
    return dict(fit=model,scores=scores(prediction,labels[held]),
                test_log_probs=prediction.tolist())


def main():
    output = HERE/'rey_story_transfer_result.json'
    if output.exists():
        raise FileExistsError('Preserve prior story-transfer evidence')
    prior_path,source_path = HERE/'rey_premention_readout_result.json',HERE/'rey_premention_readout.py'
    if sha(prior_path)!=PRIOR_RESULT_SHA or sha(source_path)!=PRIOR_SOURCE_SHA:
        raise ValueError('Frozen v1 input changed')
    prior = json.loads(prior_path.read_text(encoding='utf-8'))
    if sha(ROOT/prior['arrays']['path'])!=prior['arrays']['sha256']:
        raise ValueError('Frozen v1 arrays changed')
    spec = importlib.util.spec_from_file_location('rey_readout_frozen',source_path)
    previous = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(previous)
    units = []
    with np.load(ROOT/prior['arrays']['path'],allow_pickle=False) as arrays:
        for old in prior['units']:
            rows = [r for r in prior['rows'] if r['unit']==old['unit'] and r['eligible']]
            stories = np.asarray([r['story'] for r in rows],int)
            trials = np.asarray([r['trial'] for r in rows],int)
            labels = np.asarray([r['label'] for r in rows],int)
            keys = np.asarray([r['behavioural_key'] for r in rows])
            if len(set(keys))!=len(keys):
                raise ValueError('Duplicate unit trial')
            counts = {window:np.asarray([r['counts'][window] for r in rows],int) for window in ('precue','premention')}
            logs = {window:previous.posterior(counts[window],previous.WINDOWS[window][2],old['models']) for window in counts}
            for window in counts:
                if not np.array_equal(counts[window],arrays[f'u{old["index"]}_{window}_counts']):
                    raise ValueError('Count parity failed')
                if not np.array_equal(logs[window],arrays[f'u{old["index"]}_{window}_log_probs']):
                    raise ValueError('Frozen posterior parity failed')
            visual_score = logs['premention'][:,1]-logs['premention'][:,0]
            precue_score = logs['precue'][:,1]-logs['precue'][:,0]
            log_latency = np.log(np.asarray([r['mention_ms'] for r in rows])/1000.)
            identity_features = {
                'calibrated_vp':(visual_score[:,None],(0,)),
                'latency_only':(log_latency[:,None],()),
                'calibrated_vp_plus_latency':(np.column_stack([visual_score,log_latency]),(0,)),
                'precue_calibrated':(precue_score[:,None],(0,)),
            }
            identity_folds = []
            for train,held,meta in identity_splits(stories,labels):
                fold = dict(**meta,training_keys=keys[train].tolist(),test_keys=keys[held].tolist(),
                    test_labels=labels[held].tolist(),models={})
                fold['models']['frozen_vp'] = dict(fit=None,scores=scores(logs['premention'][held],labels[held]),test_log_probs=logs['premention'][held].tolist())
                fold['models']['chance'] = dict(fit=None,scores=scores(np.full((len(held),2),-np.log(2)),labels[held]))
                for name,(features,nonnegative) in identity_features.items():
                    fold['models'][name] = fitted_entry(train,held,features,labels,nonnegative,keys)
                identity_folds.append(fold)
            context_folds = []
            eligibility = story_eligibility(stories,trials)
            context_features = {
                'latency_only':log_latency[:,None],
                'premention_count':counts['premention'][:,None],
                'premention_plus_latency':np.column_stack([counts['premention'],log_latency]),
                'precue_plus_latency':np.column_stack([counts['precue'],log_latency]),
            }
            context_splits = story_splits(stories,trials,labels) if eligibility['eligible'] else []
            for train,held,context_labels,meta in context_splits:
                fold = dict(**meta,training_keys=keys[train].tolist(),test_keys=keys[held].tolist(),
                    test_labels=context_labels[held].tolist(),models={})
                fold['models']['chance'] = dict(fit=None,scores=scores(np.full((len(held),2),-np.log(2)),context_labels[held]))
                for name,features in context_features.items():
                    fold['models'][name] = fitted_entry(train,held,features,context_labels,(),keys)
                context_folds.append(fold)
            units.append(dict(unit=old['unit'],session=old['session'],participant=old['participant'],
                site=old['site'],region=previous.region_for_site(old['site']),eligible_trials=len(rows),
                identity=dict(scores=mean_scores(identity_folds),folds=identity_folds),
                conditional_story=dict(**eligibility,scores=mean_scores(context_folds) if context_folds else None,folds=context_folds)))
    boundary = {name:dict(fits=88,zero_slope=sum(u['identity']['folds'][fold]['models'][name]['fit']['coefficients'][0]<=1e-8
        for u in units for fold in range(4))) for name in ('calibrated_vp','calibrated_vp_plus_latency','precue_calibrated')}
    result = dict(schema='hippocampal.rey2025.story-transfer.v1',source_sha256=sha(__file__),
        test_sha256=sha(ROOT/'tests/test_rey_story_transfer.py'),
        provenance=dict(prior_source_path=source_path.relative_to(ROOT).as_posix(),prior_source_sha256=PRIOR_SOURCE_SHA,
            prior_result_path=prior_path.relative_to(ROOT).as_posix(),prior_result_sha256=PRIOR_RESULT_SHA,
            arrays=prior['arrays'],participant_mapping=prior['provenance']['participant_mapping_sha256']),
        environment=dict(python=platform.python_version(),numpy=np.__version__,scipy=scipy.__version__),
        methods=dict(selection=prior['selection'],penalty='Balanced mean log loss + ||theta||^2/(2*n_training), including intercept; no lambda search.',
            scaling='Training class-balanced feature mean/sd; sd<=1e-12 column fixed slope0; no test input to fitting.',
            identity='4 leave-story-pair-out folds: one R+one NR held, other2 train; VP direction nonnegative, latency unconstrained.',
            conditional_story='Within each true identity: two stored trial halves per story, cross-fit both directions; minimum4 eligible repeats in each story. Ineligible units retained in identity analysis and explicitly excluded only here. No chronology assumed, all slopes unconstrained.',
            aggregation='Equal class per fold, equal4fold per unit, units per session, sessions per participant, participants equally.',
            timing='Log mention seconds as a retrospective behavioural baseline; event-locked spikes depend on later known mention timing. Not an online predictor.',
            metrics='AUC/accuracy vs chance plus proper log-score gain/Brier; compare neural+latency to latency-only; no outcome-tuned threshold.'),
        limitations=['Retrospective exploratory same-unit/session analysis after all data were inspected in v1; not independent prospective replication or participant holdout.',
            'Identity folds overlap: each eligible neuron-trial evaluated twice; conditional-story folds evaluate each once. Folds are not independent experiments.',
            'The paper describes four distinct story contexts, not a shared 2x2 identity/context factorial. Exact cue/story semantics are absent from MAT; identity includes places in some sessions.',
            'Cue/identity/speech/common input confounding remains; story discrimination is not event-address identification.',
            'Linear log-latency adjustment does not remove all timing or behavioural confounding.',
            'Deposited subset is encoding-selected; trial correctness and acquisition coverage remain unknown.',
            'No intervention, unique event-address mechanism, physiological parameter or biological metric identified.'],
        cohort=dict(units=len(units),neuron_trials=sum(u['eligible_trials'] for u in units),
            unique_behavioural_trials=len({r['behavioural_key'] for r in prior['rows'] if r['eligible']})),
        positive_slope_boundaries=boundary,
        conditional_story_exclusions=[dict(unit=u['unit'],region=u['region'],session=u['session'],participant=u['participant'],
            small_cells=u['conditional_story']['small_cells']) for u in units if not u['conditional_story']['eligible']],
        summary=dict(identity=aggregate(units,'identity'),conditional_story=aggregate(units,'conditional_story')),units=units)
    if result['cohort']!=dict(units=22,neuron_trials=1095,unique_behavioural_trials=680):
        raise ValueError('Cohort changed')
    # Complete validation/serialization before creating the exclusive output.
    encoded = json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)
    with output.open('x',encoding='utf-8') as stream:
        stream.write(encoded)
    print(json.dumps(dict(output=str(output),cohort=result['cohort'],boundaries=boundary),ensure_ascii=True))


if __name__=='__main__':
    main()
