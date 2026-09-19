"""Conditional cross-task readout from the deposited Rey2025 spike subset.

All recall-bearing units are retained. The result concerns deposited counts,
conditional on author-provided clocks and assumed capture in the named windows.
It is not a behavioural recall-accuracy estimate or a synaptic/metric fit.
"""
import hashlib
import json
import platform
from pathlib import Path

import numpy as np
import scipy
from scipy.io import loadmat
from scipy.optimize import linear_sum_assignment
from scipy.special import gammaln, logsumexp

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
DATA = ROOT/'data/external/hippocampal_reinstatement/rey2025_processed_v1'
MAT_SHA = '736ad3947a0185a65a9194b0bfc8140b14d14185cab622923980dcc98cd19a08'
AUDIT_SHA = 'df9a25f791c5feb62da0ab700fdc360bc1fcaf1950786ce709e9abea139f1eda'
WINDOWS = {'precue':(-900.,-100.,.8),'premention':(-1500.,0.,1.5)}
SUPPORT = ROOT/'data/external/hippocampal_reinstatement/rey2025_support_v1'
MAPPING_SHA = '4f5b8e41c70b0de48b796374c04fd04b5524e1256281499109af1b8904dfe6f8'


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def spike_count(spikes,start,stop):
    spikes = np.asarray(spikes,float).ravel()
    if not np.isfinite(spikes).all() or not np.isfinite([start,stop]).all() or stop<=start:
        raise ValueError('Invalid spike window')
    return int(np.count_nonzero((spikes>=start)&(spikes<stop)))


def vp_counts(matrix):
    matrix = np.asarray(matrix,float)
    if matrix.ndim!=2 or not np.isfinite(matrix).all():
        raise ValueError('Invalid VP matrix')
    return np.asarray([spike_count(row[row!=10000],200,700) for row in matrix],dtype=int)


def fit_predictive(counts,duration):
    counts = np.asarray(counts)
    if not len(counts) or not np.isfinite(counts).all() or np.any(counts<0) or np.any(counts!=np.floor(counts)) or duration<=0:
        raise ValueError('Invalid training counts')
    # Jeffreys rate prior; positive exposure makes the posterior proper.
    return dict(shape=float(counts.sum()+.5),exposure=float(len(counts)*duration),
                training_trials=len(counts),training_spikes=int(counts.sum()))


def log_predictive(counts,duration,model):
    counts = np.asarray(counts,float)
    if np.any(counts<0) or np.any(counts!=np.floor(counts)) or not np.isfinite(counts).all() or duration<=0:
        raise ValueError('Invalid prediction counts')
    a,b = model['shape'],model['exposure']
    if a<=0 or b<=0:
        raise ValueError('Invalid posterior')
    return (gammaln(counts+a)-gammaln(a)-gammaln(counts+1)
            +a*np.log(b/(b+duration))+counts*np.log(duration/(b+duration)))


def posterior(counts,duration,models):
    logs = np.stack([log_predictive(counts,duration,models[k]) for k in ('NR','R')],axis=-1)
    normalizer = logsumexp(logs,axis=-1,keepdims=True)
    return logs-normalizer


def binary_scores(log_probs,labels,groups):
    """Equal weight per supplied story/class group, including ties as half."""
    labels,groups = np.asarray(labels,int),np.asarray(groups)
    log_probs = np.asarray(log_probs,float)
    if len(labels)!=len(log_probs) or log_probs.shape!=(len(labels),2):
        raise ValueError('Misaligned predictions')
    if set(np.unique(labels))!={0,1}:
        raise ValueError('Both identities required')
    p = np.exp(log_probs[:,1])
    margin = log_probs[:,1]-log_probs[:,0]
    correct = np.where(margin==0,.5,((margin>0)==labels).astype(float))
    loss = -log_probs[np.arange(len(labels)),labels]
    metrics = {}
    for key,values in (('accuracy',correct),('log_loss',loss),('brier',(p-labels)**2)):
        metrics[key] = float(np.mean([np.mean(values[groups==g]) for g in np.unique(groups)]))
    metrics['log_score_gain_vs_chance'] = float(np.log(2)-metrics['log_loss'])
    return metrics


def balanced_auc(values,labels,stories):
    values,labels,stories = np.asarray(values,float),np.asarray(labels,int),np.asarray(stories,int)
    r_groups = np.unique(stories[labels==1])
    nr_groups = np.unique(stories[labels==0])
    if len(r_groups)!=2 or len(nr_groups)!=2:
        raise ValueError('Four stories required')
    pieces = []
    for rg in r_groups:
        for ng in nr_groups:
            delta = values[stories==rg][:,None]-values[stories==ng][None,:]
            pieces.append(float(np.mean((delta>0)+.5*(delta==0))))
    return float(np.mean(pieces))


def contrast(values,labels,stories):
    means = {int(story):float(np.mean(values[stories==story])) for story in np.unique(stories)}
    r = [v for s,v in means.items() if labels[stories==s][0]==1]
    nr = [v for s,v in means.items() if labels[stories==s][0]==0]
    if len(r)!=2 or len(nr)!=2:
        raise ValueError('Four stories required')
    return float(np.mean(r)-np.mean(nr))


def match_latencies(responsive,nonresponsive,caliper=500.):
    responsive,nonresponsive = np.asarray(responsive,float),np.asarray(nonresponsive,float)
    if not len(responsive) or not len(nonresponsive):
        return []
    distance = np.abs(responsive[:,None]-nonresponsive[None,:])
    rr,nn = linear_sum_assignment(np.where(distance<=caliper,distance,1e12))
    return [(int(r),int(n)) for r,n in zip(rr,nn) if distance[r,n]<=caliper]


def matched_control(retained,models,spike_lookup):
    """Match by time only; both trials use the same cue-relative window.

The end is the earlier mention, so neither paired trial includes postmention
spikes. Four R-story/NR-story pairs are separately weighted. Pair comparisons
can reuse a trial across the two other-identity stories, not independent data.
"""
    comparisons,pair_summaries = [],[]
    r_stories = sorted({r['story'] for r in retained if r['label']==1})
    n_stories = sorted({r['story'] for r in retained if r['label']==0})
    for rs in r_stories:
        for ns in n_stories:
            rr = [r for r in retained if r['story']==rs]
            nn = [r for r in retained if r['story']==ns]
            matches = match_latencies([r['mention_ms'] for r in rr],[r['mention_ms'] for r in nn])
            logs,labels,differences,wins = [],[],[],[]
            for ri,ni in matches:
                r,n = rr[ri],nn[ni]
                end = min(r['mention_ms'],n['mention_ms'])
                counts = [spike_count(spike_lookup[(x['story'],x['trial'])],end-1500,end) for x in (r,n)]
                probs = posterior(counts,1.5,models)
                logs.extend(probs.tolist())
                labels.extend([1,0])
                differences.append((counts[0]-counts[1])/1.5)
                wins.append(float(counts[0]>counts[1])+.5*float(counts[0]==counts[1]))
                comparisons.append(dict(r_key=r['behavioural_key'],nr_key=n['behavioural_key'],
                    r_story=rs,nr_story=ns,r_mention_ms=r['mention_ms'],nr_mention_ms=n['mention_ms'],
                    latency_difference_ms=abs(r['mention_ms']-n['mention_ms']),
                    shared_window_ms=[end-1500,end],r_count=counts[0],nr_count=counts[1]))
            if matches:
                scores = binary_scores(logs,labels,labels)
                pair_summaries.append(dict(r_story=rs,nr_story=ns,pairs=len(matches),
                    contrast=float(np.mean(differences)),paired_win=float(np.mean(wins)),**scores))
    statistics = {key:float(np.mean([p[key] for p in pair_summaries])) for key in
        ('contrast','paired_win','accuracy','log_loss','brier','log_score_gain_vs_chance')} if pair_summaries else None
    return dict(caliper_ms=500,story_pairs_present=len(pair_summaries),complete_four_story_pairs=len(pair_summaries)==4,
                matched_comparisons=len(comparisons),statistics=statistics,pair_summaries=pair_summaries,comparisons=comparisons)


def region_for_site(site):
    if 'Hippocampus' in site:
        return 'H'
    if 'Amygdala' in site:
        return 'A'
    raise ValueError('Unknown anatomical site: '+str(site))


def summarize(units):
    output = {}
    for site in ('all','H','A'):
        selected = [u for u in units if site=='all' or region_for_site(u['site'])==site]
        sessions = sorted({u['session'] for u in selected})
        participants = sorted({u['participant'] for u in selected})
        region = dict(units=len(selected),sessions=len(sessions),participants=len(participants),statistics={})
        for metric in ('auc_gain','activity_auc_gain','contrast_gain','premention_auc','precue_auc',
                       'premention_activity_auc','precue_activity_auc',
                       'premention_contrast','precue_contrast','vp_holdout_accuracy',
                       'vp_holdout_log_gain','premention_accuracy','precue_accuracy',
                       'premention_log_gain','precue_log_gain'):
            values = np.asarray([u['statistics'][metric] for u in selected],float)
            session_values = [float(np.mean([u['statistics'][metric] for u in selected if u['session']==s])) for s in sessions]
            session_map = dict(zip(sessions,session_values))
            participant_values = {str(p):float(np.mean([session_map[s] for s in sorted({u['session'] for u in selected if u['participant']==p})])) for p in participants}
            region['statistics'][metric] = dict(unit_mean=float(values.mean()),unit_median=float(np.median(values)),
                unit_positive=int(np.count_nonzero(values>0)),session_mean=float(np.mean(session_values)),
                by_session=dict(zip(map(str,sessions),session_values)),
                participant_mean=float(np.mean(list(participant_values.values()))),by_participant=participant_values)
        matched = [u for u in selected if u['matched']['complete_four_story_pairs']]
        matched_sessions = sorted({u['session'] for u in matched})
        matched_participants = sorted({u['participant'] for u in matched})
        region['matched'] = dict(units=len(matched),sessions=len(matched_sessions),
            participants=len(matched_participants),
            comparisons=sum(u['matched']['matched_comparisons'] for u in matched),statistics={})
        for metric in ('contrast','paired_win','accuracy','log_loss','brier','log_score_gain_vs_chance'):
            values = [u['matched']['statistics'][metric] for u in matched]
            session_values = [float(np.mean([u['matched']['statistics'][metric] for u in matched if u['session']==s])) for s in matched_sessions]
            session_map = dict(zip(matched_sessions,session_values))
            participant_values = {str(p):float(np.mean([session_map[s] for s in sorted({u['session'] for u in matched if u['participant']==p})])) for p in matched_participants}
            region['matched']['statistics'][metric] = dict(unit_mean=float(np.mean(values)) if values else None,
                session_mean=float(np.mean(session_values)) if session_values else None,
                participant_mean=float(np.mean(list(participant_values.values()))) if participant_values else None,
                by_participant=participant_values,by_session=dict(zip(map(str,matched_sessions),session_values)))
        output[site] = region
    return output


def main():
    output = HERE/'rey_premention_readout_result.json'
    arrays_path = ROOT/'data/local/hippocampal-reinstatement/rey-premention-v1/counts.npz'
    if output.exists() or arrays_path.exists():
        raise FileExistsError('Preserve existing readout outputs')
    mat_path,audit_path = DATA/'Reyetal_CR_dataset.mat',HERE/'rey_input_audit_result.json'
    if sha(mat_path)!=MAT_SHA or sha(audit_path)!=AUDIT_SHA:
        raise ValueError('Input changed')
    audit = json.loads(audit_path.read_text(encoding='utf-8'))
    mapping_path = SUPPORT/'session_participants.json'
    if sha(mapping_path)!=MAPPING_SHA:
        raise ValueError('Participant mapping changed')
    mapping = json.loads(mapping_path.read_text(encoding='utf-8'))
    if sha(SUPPORT/'mmc1.pdf')!=mapping['pdf_sha256']:
        raise ValueError('Participant mapping source changed')
    participants = mapping['session_to_participant']
    if set(participants)!={str(i) for i in range(1,22)}:
        raise ValueError('Incomplete participant mapping')
    audit_by_unit = {u['unit']:u for u in audit['units']}
    records = np.atleast_1d(loadmat(mat_path,squeeze_me=True,struct_as_record=False)['resp'])
    units,rows,arrays = [],[],{}
    for index,record in enumerate(records):
        key = f'{int(record.sessionID)}:{int(record.channel_number)}:{str(record.cluster)}'
        prior = audit_by_unit[key]
        if not prior['has_recall']:
            continue
        models,vp_log_probs,vp_labels = {},[],[]
        vp = np.asarray(record.spike_times_VP,dtype=object).ravel()
        for name,label,field in (('NR',0,'nonresponsive_stilmulus_VPindex'),('R',1,'responsive_stilmulus_VPindex')):
            counts = vp_counts(vp[int(getattr(record,field))-1])
            split = len(counts)//2
            models[name] = fit_predictive(counts[:split],.5)
            arrays[f'u{index}_vp_{name}_train'] = counts[:split]
            arrays[f'u{index}_vp_{name}_test'] = counts[split:]
        for name,label in (('NR',0),('R',1)):
            test = arrays[f'u{index}_vp_{name}_test']
            vp_log_probs.extend(posterior(test,.5,models).tolist())
            vp_labels.extend([label]*len(test))
        vp_scores = binary_scores(vp_log_probs,vp_labels,vp_labels)
        recall = np.asarray(record.spike_times_Rec,dtype=object).ravel()
        timing = np.asarray(record.trecall_phasic_ms,dtype=object).ravel()
        retained,spike_lookup = [],{}
        for slot in range(4):
            spikes_by_trial = np.atleast_1d(recall[slot])
            times = np.asarray(timing[slot],float).ravel()
            if len(times)!=len(spikes_by_trial):
                raise ValueError('Trial clock mismatch')
            for trial,(spikes,mention) in enumerate(zip(spikes_by_trial,times)):
                eligible = bool(1500<=mention<=13000)
                row = dict(unit=key,session=prior['session'],participant=participants[str(prior['session'])],site=prior['site'],story=slot+1,trial=trial,
                           behavioural_key=f'{prior["session"]}:{slot+1}:{trial}',mention_ms=float(mention),
                           label=int(slot+1 in prior['responsive_stories']),eligible=eligible)
                if eligible:
                    spike_lookup[(slot+1,trial)] = np.asarray(spikes,float).ravel()
                    row['counts'] = {name:spike_count(spikes,left+(mention if name=='premention' else 0),
                                        right+(mention if name=='premention' else 0))
                                     for name,(left,right,duration) in WINDOWS.items()}
                    retained.append(row)
                rows.append(row)
        stories = np.asarray([r['story'] for r in retained],int)
        labels = np.asarray([r['label'] for r in retained],int)
        if set(stories)!={1,2,3,4}:
            raise ValueError('Timing guard removed a whole story')
        stats = dict(vp_holdout_accuracy=vp_scores['accuracy'],vp_holdout_log_gain=vp_scores['log_score_gain_vs_chance'])
        details = {}
        arrays[f'u{index}_stories'],arrays[f'u{index}_labels'] = stories,labels
        arrays[f'u{index}_mentions'] = np.asarray([r['mention_ms'] for r in retained])
        for name,(_,_,duration) in WINDOWS.items():
            counts = np.asarray([r['counts'][name] for r in retained],int)
            log_probs = posterior(counts,duration,models)
            arrays[f'u{index}_{name}_counts'],arrays[f'u{index}_{name}_log_probs'] = counts,log_probs
            scores = binary_scores(log_probs,labels,stories)
            stats[name+'_auc'] = balanced_auc(counts,labels,stories)
            stats[name+'_activity_auc'] = stats[name+'_auc']
            stats[name+'_auc'] = balanced_auc(log_probs[:,1]-log_probs[:,0],labels,stories)
            stats[name+'_contrast'] = contrast(counts/duration,labels,stories)
            stats[name+'_accuracy'],stats[name+'_log_gain'] = scores['accuracy'],scores['log_score_gain_vs_chance']
            details[name] = scores
        stats['auc_gain'] = stats['premention_auc']-stats['precue_auc']
        stats['activity_auc_gain'] = stats['premention_activity_auc']-stats['precue_activity_auc']
        stats['contrast_gain'] = stats['premention_contrast']-stats['precue_contrast']
        units.append(dict(unit=key,index=index,session=prior['session'],site=prior['site'],
            participant=participants[str(prior['session'])],
            models=models,retained_trials=len(retained),trials_per_story={str(s):int(np.count_nonzero(stories==s)) for s in range(1,5)},
            vp_holdout=vp_scores,vp_sanity_positive=bool(vp_scores['accuracy']>.5 and vp_scores['log_score_gain_vs_chance']>0),
            recall_scores=details,statistics=stats,matched=matched_control(retained,models,spike_lookup)))
    if len(units)!=22 or sum(r['eligible'] for r in rows)!=1095 or len(rows)!=1169:
        raise ValueError('Input audit cohort mismatch')
    summary = summarize(units)
    for region,block in summary.items():
        region_rows = [r for r in rows if region=='all' or region_for_site(r['site'])==region]
        complete = [u for u in units if (region=='all' or region_for_site(u['site'])==region) and u['matched']['complete_four_story_pairs']]
        matched_keys = {c[key] for u in complete for c in u['matched']['comparisons'] for key in ('r_key','nr_key')}
        block['behavioural_trials'] = dict(all=len({r['behavioural_key'] for r in region_rows}),
            eligible=len({r['behavioural_key'] for r in region_rows if r['eligible']}),
            matched_unique=len(matched_keys),
            matched_neuron_trials=len({(u['unit'],c[key]) for u in complete for c in u['matched']['comparisons'] for key in ('r_key','nr_key')}))
    if summary['all']['behavioural_trials']['eligible']!=680:
        raise ValueError('Behavioural cohort mismatch')
    arrays_path.parent.mkdir(parents=True,exist_ok=True)
    with arrays_path.open('xb') as stream:
        np.savez_compressed(stream,**arrays)
    result = dict(schema='hippocampal.rey2025.premention-readout.v1',source_sha256=sha(__file__),
        test_sha256=sha(ROOT/'tests/test_rey_premention_readout.py'),
        provenance=dict(mat_path=mat_path.relative_to(ROOT).as_posix(),mat_sha256=MAT_SHA,
                        audit_path=audit_path.relative_to(ROOT).as_posix(),audit_sha256=AUDIT_SHA,
                        participant_mapping_path=mapping_path.relative_to(ROOT).as_posix(),participant_mapping_sha256=sha(mapping_path)),
        environment=dict(python=platform.python_version(),numpy=np.__version__,scipy=scipy.__version__),
        windows=WINDOWS,selection='All22 recall-bearing encoding-selected units; mention1500..13000ms; no is_signif_recall selection.',
        decoder='VP[200,700)ms first half of stored rows per identity train, remaining rows sanity holdout; chronological ordering not established. Gamma-Poisson Jeffreys posterior predictive, equal identity priors. No recall fitting.',
        matched_control='Within-unit R-story/NR-story maximum-cardinality latency matching,500ms caliper,minimum distance; both use same1.5s cue-relative window ending at earlier mention. Four-story-pair complete units summarized separately. No spike outcomes used in matching.',
        score_definitions='AUC ranks frozen VP decoder log odds; activity_auc ranks raw count. Matched contrast/paired_win describe raw count differences, while accuracy/proper scores use the frozen decoder. Rate-normalized contrasts divide deposited counts by nominal window duration.',
        limitations=['Deposited counts conditional on supplied clocks and unknown recording coverage; not confirmed physiological rates.',
            'Units were selected on encoding responses; VP pools before/after the memory task.',
            'Participant mapping transcribed from Table S1; summaries average units within sessions, sessions within participants, then participants equally. No population p-values or patient confidence intervals.',
            'Trial correctness and silence-vs-missing masks unavailable.',
            'Cue identity, retrieval, speech preparation and common input are not causally separated.',
            'Readout accuracy is identity discrimination on deposited records, not behavioural recall accuracy or complete event reconstruction.',
            'No identified synaptic parameters, biological Riemannian metric or unique hippocampal indexing mechanism.'],
        summary=summary,units=units,rows=rows,
        arrays=dict(path=arrays_path.relative_to(ROOT).as_posix(),sha256=sha(arrays_path),bytes=arrays_path.stat().st_size))
    with output.open('x',encoding='utf-8') as stream:
        json.dump(result,stream,ensure_ascii=False,indent=2)
    print(json.dumps(dict(units=len(units),eligible=sum(r['eligible'] for r in rows),summary=result['summary'],output=str(output)),ensure_ascii=True))


if __name__=='__main__':
    main()
