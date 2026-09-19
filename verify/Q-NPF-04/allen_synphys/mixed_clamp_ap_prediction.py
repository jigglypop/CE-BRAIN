"""Retrospective current readout conditional on observed source voltage events.

Train on early pulses in five recordings; retain later/recovery/transport
responses and response-QC failures. No identified PSC, plasticity or metric.
"""
import itertools
import json
from pathlib import Path
import platform

import numpy as np

from vc20hz_source_inputs import HERE, ROOT, sha

PINS={
    'mixed_clamp_raw_inputs_result.json':'311e4ecca0709b306651090ca210d12637d92a32659ed13dc9a9609d018b323b',
    'mixed_clamp_waveform_audit_result.json':'dd10c80caac8ce44b37918773f8ee3f520242fd7010cd7c62f882927cbc49d7a',
    'mixed_clamp_measurement_state_result.json':'371fcc95828ef19cb8e38e54bae85ea5bdad363d9a6cf8a1b8ea21c95117ec37',
    'mixed_clamp_pulses_result.json':'f023db5b41d40c4ccbb5bb91c89af926898f38d7fb607c09b8446bb341aa76c7',
}
TRAIN=(69,70,71,72,73)
FS=50000
BIN=10
OFFSETS=np.arange(50,350,BIN)
LAMBDAS=(.001,.01,.1,1.,10.)
DELAYS=(.0005,.001,.002)
DECAYS=(.002,.005,.01)
TAUS=(.02,.05,.15,.5,1.5)
FEATURES=('target_pre_pA','target_pre_late_minus_early_pA','source_pre_mV','target_access_MOhm','log1p_since_target_command_end_s')


def history_at(current,previous,tau):
    previous=np.asarray(previous,float)
    if tau<=0 or not np.isfinite(tau) or not np.isfinite(current) or not np.isfinite(previous).all():
        raise ValueError('Invalid observed event history')
    return float(np.exp(-(current-previous[previous<current])/tau).sum())


def kernel(t,delay,decay):
    if delay<0 or decay<=.0005:raise ValueError('Invalid causal kernel')
    age=np.maximum(np.asarray(t)-delay,0.)
    # Difference of exponentials with a fixed 0.5ms rise, normalized at its peak.
    rise=.0005;peak=np.log(decay/rise)/(1/rise-1/decay)
    normal=np.exp(-peak/decay)-np.exp(-peak/rise)
    return (np.exp(-age/decay)-np.exp(-age/rise))/normal


def cohort(sweep,pulse):
    if sweep in TRAIN:return 'train_initial' if pulse<8 else 'within_sweep_recovery'
    if 74<=sweep<=76:return 'later_50Hz'
    if 77<=sweep<=78:return 'transport_20Hz'
    if 82<=sweep<=87:return 'transport_100Hz'
    return 'outside_fitting_cohorts'


def supported_slice(values,lo,hi):
    a=int(np.ceil(lo*FS-1e-8));b=int(np.ceil(hi*FS-1e-8))
    if not 0<=a<b<=len(values):raise ValueError('Window outside observed array')
    result=np.asarray(values[a:b],float)
    if not np.isfinite(result).all():raise ValueError('Nonfinite observed samples')
    return result


def extract(inputs,audit,state,pulses):
    raw={(r['sweep'],r['device'],r['kind']):r for r in inputs['records']}
    states={(r['sweep'],r['device']):r for r in state['records']}
    own_gaps={r['pulse_id']:r['since_target_command_end_s'] for r in state['command_history']}
    sweeps={s['sweep']:s for s in pulses['sweeps']}
    histories={};first_onsets={}
    for event in audit['events']:
        key=(event['sweep'],event['source_device'])
        first_onsets[key]=min(first_onsets.get(key,float('inf')),event['onset_s'])
        if event['upward_zero_crossings']==1 and not event['starts_above_zero']:
            histories.setdefault(key,[]).append(event['raw_max_dvdt_s'])
    accepted=[];excluded=[]
    with np.load(ROOT/inputs['arrays']['path'],allow_pickle=False) as arrays:
        cache={}
        for e in audit['events']:
            reasons=[]
            if e['source_recording_qc']!=1 or e['target_recording_qc']!=1:reasons.append('recording_qc')
            if e['upward_zero_crossings']!=1 or e['starts_above_zero']:reasons.append('source_voltage_event')
            if cohort(e['sweep'],e['pulse_number'])=='outside_fitting_cohorts':reasons.append('outside_cohorts')
            if reasons:
                excluded.append(dict(pulse_id=e['pulse_id'],sweep=e['sweep'],pair_id=e['pair_id'],reasons=reasons));continue
            s,d=e['sweep'],e['source_device'];onset=e['onset_s'];ap=e['raw_max_dvdt_s']
            target_meta=raw[s,1,'acquisition'];source_meta=raw[s,d,'acquisition']
            if target_meta['rate']!=FS or source_meta['rate']!=FS:raise ValueError('Unexpected sample rate')
            if (target_meta['start'],target_meta['samples'])!=(source_meta['start'],source_meta['samples']):
                raise ValueError('Shared clock disagreement')
            for meta,scale in ((target_meta,1e12),(source_meta,1e3)):
                if meta['array_key'] not in cache:cache[meta['array_key']]=arrays[meta['array_key']]*scale
            target=cache[target_meta['array_key']];source=cache[source_meta['array_key']]
            anchor=int(np.floor(ap*FS+.5));indices=anchor+OFFSETS[:,None]+np.arange(BIN)
            lo,hi=indices.min()/FS,(indices.max()+1)/FS
            # Whole response support must precede every later source command.
            later=[p['onset_time'] for group in sweeps[s]['source_pulses'].values() for p in group if p['onset_time']>onset]
            own=raw[s,1,'command']['command_intervals']
            support_reasons=[]
            if indices.min()<0 or indices.max()>=len(target):support_reasons.append('array_support')
            if later and hi>min(later)+1e-12:support_reasons.append('next_source_command')
            if any(c['start_s']<hi and c['stop_s']>onset-.002 for c in own):support_reasons.append('target_command_overlap')
            if support_reasons:
                excluded.append(dict(pulse_id=e['pulse_id'],sweep=s,pair_id=e['pair_id'],reasons=support_reasons));continue
            before=supported_slice(target,onset-.002,onset-.0002)
            vm=supported_slice(source,onset-.002,onset-.0002)
            tp=states[s,1]['test_pulse'];gap=own_gaps[e['pulse_id']]
            if gap is None or gap<0 or tp['stop_index']/FS>=onset-.002:
                raise ValueError('Missing prior measurement support')
            first=first_onsets[s,d]
            baseline=float(before.mean())
            row={k:e[k] for k in ('sweep','source_device','pair_id','pulse_id','pulse_number','response_ex_qc','stored_time_finite')}
            row.update(cohort=cohort(s,e['pulse_number']),ap_s=ap,onset_s=onset,baseline_pA=baseline,
                time_from_ap_s=indices.mean(axis=1)/FS-ap,time_from_command_s=indices.mean(axis=1)/FS-onset,
                observed_pA=target[indices].mean(axis=1),
                state_features=np.array([baseline,before[len(before)//2:].mean()-before[:len(before)//2].mean(),
                    vm.mean(),tp['access_resistance']*1e-6,np.log1p(gap)]),
                schedule_features=np.array([e['pulse_number'],np.log1p((onset-first)/.02)]),
                history_values={tau:history_at(ap,histories[s,d],tau) for tau in TAUS},
                response_first_index=int(indices.min()),response_stop_index=int(indices.max()+1))
            accepted.append(row)
    return accepted,excluded


def stack(rows):
    return dict(q=np.stack([r['state_features'] for r in rows]),schedule=np.stack([r['schedule_features'] for r in rows]),
        ta=np.stack([r['time_from_ap_s'] for r in rows]),tc=np.stack([r['time_from_command_s'] for r in rows]),
        h={tau:np.array([r['history_values'][tau] for r in rows]) for tau in TAUS},
        y=np.stack([r['observed_pA']-r['baseline_pA'] for r in rows]),
        sweep=np.array([r['sweep'] for r in rows]),pulse=np.array([r['pulse_number'] for r in rows]))


def normalize(values,train):
    center=values[train].mean(axis=0);scale=values[train].std(axis=0)
    scale=np.where(scale<1e-9,1.,scale)
    return (values-center)/scale,dict(center=center.tolist(),scale=scale.tolist())


def design(data,train,config):
    q,qnorm=normalize(data['q'],train);n,t=data['y'].shape
    # Same observed pre-response state and slow time basis in every model.
    q=np.column_stack((np.ones(n),q));slow=data['tc']/.01
    columns=[np.broadcast_to(q[:,j,None],(n,t)) for j in range(q.shape[1])]
    columns += [q[:,j,None]*slow for j in range(q.shape[1])]
    normalization=dict(state=qnorm)
    if config['family']!='state':
        clock=data['tc'] if config['alignment']=='command' else data['ta']
        k=kernel(clock-config['shift_s'],config['delay_s'],config['decay_s'])
        if np.sqrt(np.mean(k[train]**2))<1e-10:raise ValueError('Zero kernel support')
        columns.append(k)
        if 'order' in config['family']:
            z,norm=normalize(data['schedule'],train);normalization['schedule']=norm
            columns += [k*z[:,j,None] for j in range(z.shape[1])]
        if 'history' in config['family']:
            z,norm=normalize(data['h'][config['tau_s']][:,None],train);normalization['history']=norm
            columns.append(k*z)
    x=np.stack(columns,axis=-1)
    scales=np.sqrt(np.mean(x[train]**2,axis=(0,1)));scales=np.where(scales<1e-10,1.,scales)
    return x/scales,dict(**normalization,column_rms=scales.tolist())


def ridge(x,y,penalty):
    x=x.reshape(-1,x.shape[-1]);y=y.reshape(-1)
    if penalty<=0:raise ValueError('Positive ridge penalty required')
    return np.linalg.solve(x.T@x/len(y)+penalty*np.eye(x.shape[1]),x.T@y/len(y))


def configurations(family,alignment='ap',shift=0.):
    if family=='state':return [dict(family=family,alignment='none',shift_s=0.)]
    delays=(.001,.002,.003,.004) if alignment=='command' else DELAYS
    taus=TAUS if 'history' in family else (None,)
    return [dict(family=family,alignment=alignment,shift_s=shift,delay_s=delay,decay_s=decay,tau_s=tau)
        for delay,decay,tau in itertools.product(delays,DECAYS,taus)]


def fit_model(data,candidates,lambdas=LAMBDAS,train_sweeps=TRAIN):
    train=np.isin(data['sweep'],train_sweeps)&(data['pulse']<8)
    if set(data['sweep'][train])!=set(train_sweeps):raise ValueError('Training sweep missing')
    scores=[];best=None
    for config in candidates:
        fold_values={lam:[] for lam in lambdas};invalid=None
        for held in train_sweeps:
            use=train&(data['sweep']!=held);valid=train&(data['sweep']==held)
            try:x,_=design(data,use,config)
            except ValueError as error:invalid=str(error);break
            for lam in lambdas:
                beta=ridge(x[use],data['y'][use],lam)
                mse=float(np.mean((np.einsum('ntp,p->nt',x[valid],beta)-data['y'][valid])**2))
                fold_values[lam].append(mse)
        if invalid:
            scores.append(dict(config=config,invalid=invalid));continue
        for lam in lambdas:
            entry=dict(config=config,lambda_=lam,cv_mse_pA2=float(np.mean(fold_values[lam])),fold_mse_pA2=fold_values[lam])
            scores.append(entry)
            if best is None or entry['cv_mse_pA2']<best['cv_mse_pA2']:best=entry
    if best is None:raise ValueError('No supported training model')
    x,norm=design(data,train,best['config']);beta=ridge(x[train],data['y'][train],best['lambda_'])
    prediction=np.einsum('ntp,p->nt',x,beta)
    return prediction,dict(selected=best,normalization=norm,beta_pA=beta.tolist(),
        training_events=int(train.sum()),training_sweeps=list(train_sweeps),
        design_rank=int(np.linalg.matrix_rank(x[train].reshape(-1,x.shape[-1]))),columns=x.shape[-1],cv_candidates=scores)


def analyze(rows):
    arrays={};fits=[];scores=[];metadata=[]
    specs=[('state','state','none',0.),('command_fixed','fixed','command',0.),
        ('ap_fixed','fixed','ap',0.),('ap_order','order','ap',0.),('ap_history','history','ap',0.),
        ('ap_order_history','order_history','ap',0.),('ap_early5ms','order_history','ap',-.005),
        ('ap_late5ms','order_history','ap',.005)]
    for pair in sorted({r['pair_id'] for r in rows}):
        group=[r for r in rows if r['pair_id']==pair];data=stack(group);predictions={'pre_level':np.zeros_like(data['y'])}
        for name,family,alignment,shift in specs:
            prediction,fit=fit_model(data,configurations(family,alignment,shift))
            predictions[name]=prediction;fits.append(dict(pair_id=pair,model=name,**fit))
            print(f'Fitted pair {pair} model {name}',flush=True)
        arrays[f'p{pair}_observed_pA']=data['y']+np.array([r['baseline_pA'] for r in group])[:,None]
        arrays[f'p{pair}_baseline_pA']=np.array([r['baseline_pA'] for r in group])
        arrays[f'p{pair}_time_from_ap_s']=data['ta'];arrays[f'p{pair}_state_features']=data['q']
        for name,pred in predictions.items():
            arrays[f'p{pair}_{name}_residual_prediction_pA']=pred
            for s in sorted({r['sweep'] for r in group}):
                for label in sorted({r['cohort'] for r in group if r['sweep']==s}):
                    for qc in ('recording_qc_primary','response_ex_qc_subset'):
                        take=np.array([r['sweep']==s and r['cohort']==label and (qc=='recording_qc_primary' or r['response_ex_qc']==1) for r in group])
                        if not take.any():continue
                        mse=float(np.mean((pred[take]-data['y'][take])**2))
                        scores.append(dict(pair_id=pair,model=name,sweep=s,cohort=label,qc_scope=qc,
                            events=int(take.sum()),mse_pA2=mse,rmse_pA=float(np.sqrt(mse))))
        for r in group:
            metadata.append({k:r[k] for k in ('sweep','source_device','pair_id','pulse_id','pulse_number','response_ex_qc',
                'stored_time_finite','cohort','ap_s','onset_s','baseline_pA','response_first_index','response_stop_index')})
    summaries=[]
    for pair,name,label,qc in sorted({(r['pair_id'],r['model'],r['cohort'],r['qc_scope']) for r in scores}):
        selected=[r for r in scores if (r['pair_id'],r['model'],r['cohort'],r['qc_scope'])==(pair,name,label,qc)]
        summaries.append(dict(pair_id=pair,model=name,cohort=label,qc_scope=qc,sweeps=len(selected),
            events=sum(r['events'] for r in selected),equal_sweep_rmse_pA=float(np.sqrt(np.mean([r['mse_pA2'] for r in selected])))))
    return fits,scores,summaries,metadata,arrays


def main():
    output=HERE/'mixed_clamp_ap_prediction_result.json'
    npz=ROOT/'data/local/allen-synphys-analysis/mixed-clamp-ap-prediction-v1/predictions.npz'
    if output.exists() or npz.exists():raise FileExistsError('Preserve existing prediction outputs')
    loaded={}
    for name,digest in PINS.items():
        if sha(HERE/name)!=digest:raise ValueError('Frozen input changed: '+name)
        loaded[name]=json.loads((HERE/name).read_text(encoding='utf-8'))
    inputs=loaded['mixed_clamp_raw_inputs_result.json']
    if sha(ROOT/inputs['arrays']['path'])!=inputs['arrays']['sha256']:raise ValueError('Raw archive changed')
    rows,excluded=extract(inputs,loaded['mixed_clamp_waveform_audit_result.json'],loaded['mixed_clamp_measurement_state_result.json'],loaded['mixed_clamp_pulses_result.json'])
    fits,scores,summary,events,arrays=analyze(rows)
    result=dict(schema='allen.mixed-clamp.ap-prediction.v1',source_sha256=sha(__file__),
        test_sha256=sha(ROOT/'tests/test_mixed_clamp_ap_prediction.py'),input_sha256=PINS,raw_archive=inputs['arrays'],
        python=platform.python_version(),numpy=np.__version__,events=events,excluded=excluded,fits=fits,per_sweep=scores,summary=summary,
        method=dict(training_sweeps=TRAIN,training_pulses=list(range(8)),state_features=FEATURES,
            response='Observed AP+[1,7)ms, nearest raw sample; 0.2ms bin means; no interpolation.',
            baseline='Command[-2,-0.2)ms; same observed past-current budget in every model.',
            selection='Recording QC and one raw upward0mV event; target response QC retained, not primary selection.',
            tuning='Five leave-one-training-sweep-out folds, equal-sweep MSE; normalization and ridge fitted in training fold only.',
            history='Sum exp(-(current-prior)/tau) over earlier commanded voltage events within sweep, before response-QC selection. Unknown pre-sweep/spontaneous history not assumed absent.',
            controls='Command alignment, pulse number/log elapsed command time, combined order+history and +/-5ms AP-kernel shifts on identical target samples.',
            observation='Retrospective conditional readout given observed source voltage event, not a pre-stimulus forecast. Later observed baselines can include earlier responses.',
            interpretation='Only five training recordings per pair. Ridge coefficients/selected tau are predictive candidates, not identified state effects or physiology. '
                'Within-sweep recovery differs from sequential and frequency/order-confounded transport. No independent causal null or population validation.'),
        conclusion_scope='Conditional clamp-current prediction only; no isolated PSC, synaptic plasticity, metric or hippocampal retrieval proved.')
    json.dumps(result,allow_nan=False)
    npz.parent.mkdir(parents=True,exist_ok=True)
    with npz.open('xb') as stream:np.savez_compressed(stream,**arrays)
    result['predictions']=dict(path=npz.relative_to(ROOT).as_posix(),sha256=sha(npz),bytes=npz.stat().st_size)
    with output.open('x',encoding='utf-8') as stream:json.dump(result,stream,indent=2,allow_nan=False)
    print(json.dumps(dict(events=len(rows),excluded=len(excluded),fits=len(fits),output=str(output))))


if __name__=='__main__':main()
