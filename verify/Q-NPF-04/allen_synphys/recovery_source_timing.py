"""Retrospective source-time controls with matched target waveform observations.

Previous registered artifacts are read only. Shifted source schedules are timing
controls, not causal mechanisms or exchangeable statistical null samples.
"""
import argparse
import importlib.util
import json
import platform
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
spec = importlib.util.spec_from_file_location('timing_parent',HERE/'recovery_waveform_prediction.py')
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
DT = .0005
SHIFTS_MS = (-10.,-5.,0.,5.,10.)
WINDOWS = {'short':(.002,.008),'long':(.002,.018)}
METHODS = ('none','constant','depression','facilitation')


def observation_design(record,window):
    """Both windows and all source shifts share the same past-only anchors."""
    left = np.asarray(record['left_times'],float)
    spikes = np.asarray(record['spikes'],float)
    valid = np.asarray(record['valid'],bool)
    right = left+DT
    # Parent valid starts at t=0. Restore only pre bins before the first guard.
    update = (right<=-.0005+1e-12)|valid
    for spike in spikes:
        update &= ~((left<spike+.018)&(right>spike+.002))
    indices,pulses,anchors = [],[],[]
    lo,hi = WINDOWS[window]
    for pulse,spike in enumerate(spikes):
        score = np.flatnonzero((left>=spike+lo)&(right<=spike+hi)&valid)
        if not len(score):
            raise ValueError('Response has no complete bins')
        available = np.flatnonzero(update & (np.arange(len(left))<score[0]))
        if not len(available):
            raise ValueError('No past baseline observation')
        anchor = int(available[-1])
        assert not update[score].any()
        indices.extend(score.tolist())
        pulses.extend([pulse]*len(score))
        anchors.extend([anchor]*len(score))
    indices,pulses,anchors = map(np.array,(indices,pulses,anchors))
    assert len(np.unique(indices))==len(indices), 'Overlapping scored pulses'
    assert np.all(anchors<indices)
    assert right[anchors[0]]<=-.0005+1e-12
    y = np.asarray(record['y'],float)
    counts = np.bincount(pulses,minlength=len(spikes))
    return dict(sweep=record['sweep'],target=record['target'],gap_s=record['gap_s'],window=window,
        spikes=spikes,indices=indices,pulses=pulses,anchors=anchors,counts=counts,
        left=left[indices],anchor_left=left[anchors],relative_ms=(left[indices]+DT/2-spikes[pulses])*1000,
        observed=y[indices],baseline=y[anchors],innovation=y[indices]-y[anchors])


def basis_difference(record,shift_ms,lag_ms,rise_ms,decay_ms):
    shifted = record['spikes']+shift_ms/1000
    args = (shifted,lag_ms/1000,rise_ms/1000,decay_ms/1000)
    return base.kernel_basis(record['left'],*args)-base.kernel_basis(record['anchor_left'],*args)


def fit_models(records,shift_ms):
    """Fit actual or shifted schedules independently using only initial training."""
    training = [r for r in records if r['sweep'] in base.TRAIN_SWEEPS]
    assert len(training)==10
    masks = [r['pulses']<8 for r in training]
    y = np.concatenate([r['innovation'][m] for r,m in zip(training,masks)])
    weights = np.concatenate([1/r['counts'][r['pulses'][m]] for r,m in zip(training,masks)])/(10*8)
    np.testing.assert_allclose(weights.sum(),1.)
    q = [np.array([base.efficacy(r['spikes'],*grid) for grid in base.HISTORY_GRID]) for r in training]
    best = {'none':dict(model='none',amplitude_uV=0.,training_mse_uV2=float(np.dot(weights,y*y)),shift_ms=shift_ms)}
    profiles = []
    for lag,rise,decay in base.KERNEL_GRID:
        x = np.concatenate([basis_difference(r,shift_ms,lag,rise,decay)[m]@history.T
                            for r,m,history in zip(training,masks,q)])
        xx = np.sum(weights[:,None]*x*x,axis=0)
        xy = np.sum(weights[:,None]*x*y[:,None],axis=0)
        a = np.maximum(0.,np.divide(xy,xx,out=np.zeros_like(xy),where=xx>1e-20))
        mse = np.sum(weights[:,None]*(y[:,None]-x*a)**2,axis=0)
        kernel_best = {}
        for i,(name,strength,tau) in enumerate(base.HISTORY_GRID):
            row = dict(model=name,shift_ms=shift_ms,lag_ms=lag,rise_ms=rise,decay_ms=decay,
                strength=strength,tau_s=tau,amplitude_uV=float(a[i]),training_mse_uV2=float(mse[i]))
            if name not in best or mse[i]<best[name]['training_mse_uV2']:
                best[name] = row
            if name not in kernel_best or mse[i]<kernel_best[name]['training_mse_uV2']:
                kernel_best[name] = row
        if shift_ms==0:
            profiles.extend(kernel_best.values())
    return best,profiles


def predict_innovation(record,model):
    if model['model']=='none':
        return np.zeros_like(record['innovation'])
    x = basis_difference(record,model['shift_ms'],model['lag_ms'],model['rise_ms'],model['decay_ms'])
    q = base.efficacy(record['spikes'],model['model'],model['strength'],model['tau_s'])
    return model['amplitude_uV']*(x@q)


def error_metrics(record,prediction,region):
    pulse_ids = range(8) if region=='initial' else range(8,12)
    squared,mean_squared,shape_squared,bias = [],[],[],[]
    for pulse in pulse_ids:
        error = prediction[record['pulses']==pulse]-record['innovation'][record['pulses']==pulse]
        squared.append(float(np.mean(error**2)))
        mean_squared.append(float(error.mean()**2))
        shape_squared.append(float(np.mean((error-error.mean())**2)))
        bias.append(float(error.mean()))
    result = dict(waveform_mse_uV2=float(np.mean(squared)),pulse_mean_mse_uV2=float(np.mean(mean_squared)),
                  within_pulse_mse_uV2=float(np.mean(shape_squared)),bias_uV=float(np.mean(bias)))
    np.testing.assert_allclose(result['waveform_mse_uV2'],result['pulse_mean_mse_uV2']+result['within_pulse_mse_uV2'],rtol=1e-12,atol=1e-9)
    return result


def load_records():
    paths = [HERE/'recovery_waveform_prediction_result.json',HERE/'recovery_causal_baseline_result.json']
    parent,causal = [json.loads(p.read_text(encoding='utf-8')) for p in paths]
    assert base.sha(paths[0])==causal['provenance']['parent_sha256']
    assert base.sha(HERE/'recovery_waveform_prediction.py')==parent['code_sha256']
    assert base.sha(ROOT/'tests/test_recovery_waveform_prediction.py')==parent['test_sha256']
    assert base.sha(HERE/'recovery_causal_baseline.py')==causal['source_sha256']
    assert base.sha(ROOT/parent['arrays']['path'])==parent['arrays']['sha256']
    assert base.sha(ROOT/causal['arrays']['path'])==causal['arrays']['sha256']
    with np.load(ROOT/parent['arrays']['path'],allow_pickle=False) as z:
        records = [dict(row,**{name:z[str(row['sweep'])+'_'+row['target']+'_'+name] for name in ('left_times','spikes','y','valid')}) for row in parent['records']]
    assert len(records)==43
    eligibility = parent['provenance']['eligibility']
    assert len(eligibility)==50 and sum(r['included'] for r in eligibility)==43
    provenance = dict(parent_path=paths[0].relative_to(ROOT).as_posix(),parent_sha256=base.sha(paths[0]),
        causal_path=paths[1].relative_to(ROOT).as_posix(),causal_sha256=base.sha(paths[1]),
        parent_source_sha256=parent['code_sha256'],causal_source_sha256=causal['source_sha256'],
        parent_arrays=parent['arrays'],causal_arrays=causal['arrays'],eligibility=eligibility)
    return records,provenance


def summarize(rows):
    lookup = {(r['target'],r['window'],r['sweep'],r['region'],r['method'],r['shift_ms']):r for r in rows}
    summary = []
    cohorts = dict(training=base.TRAIN_SWEEPS,temporal=base.TEMPORAL_SWEEPS,variable_gap=range(32,37))
    for target in base.TARGETS:
        for window in WINDOWS:
            for cohort,sweeps in cohorts.items():
                for region in ('initial','recovery'):
                    for shift in SHIFTS_MS:
                        for method in METHODS:
                            selected = [lookup[target,window,sw,region,method,shift] for sw in sweeps if (target,window,sw,region,method,shift) in lookup]
                            if not selected:
                                continue
                            row = dict(target=target,window=window,cohort=cohort,region=region,shift_ms=shift,method=method,sweeps=len(selected))
                            for metric in ('waveform','pulse_mean','within_pulse'):
                                row[metric+'_rmse_uV'] = float(np.sqrt(np.mean([r[metric+'_mse_uV2'] for r in selected])))
                            comparators = {}
                            for label,ref_method,ref_shift in [('state_only','none',0.),('fixed_same_shift','constant',shift),('same_model_actual_time',method,0.)]:
                                gain = [lookup[target,window,r['sweep'],region,ref_method,ref_shift]['waveform_mse_uV2']-r['waveform_mse_uV2'] for r in selected]
                                comparators[label] = dict(mean_gain_uV2=float(np.mean(gain)),median_gain_uV2=float(np.median(gain)),improved_sweeps=int(np.sum(np.array(gain)>0)))
                            row['comparators'] = comparators
                            summary.append(row)
    return summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,default=HERE/'recovery_source_timing_result.json')
    parser.add_argument('--array-output',type=Path,default=ROOT/'data/local/allen-synphys-analysis/recovery-source-timing-v1/source_timing_arrays.npz')
    args = parser.parse_args()
    if args.output.exists() or args.array_output.exists():
        raise FileExistsError('Preserve earlier timing outputs')
    raw,provenance = load_records()
    arrays,models,profiles,rows,design_checks = {},{},[],[],[]
    for window in WINDOWS:
        prepared = [observation_design(r,window) for r in raw]
        for r in prepared:
            key = window+'_'+str(r['sweep'])+'_'+r['target']
            for field in ('indices','pulses','anchors','left','anchor_left','relative_ms','observed','baseline','innovation'):
                arrays[key+'_'+field] = r[field]
            design_checks.append(dict(window=window,sweep=r['sweep'],target=r['target'],bins_per_pulse=r['counts'].tolist(),
                first_anchor_right_ms=float((r['anchor_left'][0]+DT)*1000),
                anchor_to_AP_ms=[float((r['spikes'][pulse]-r['anchor_left'][r['pulses']==pulse][0])*1000) for pulse in range(12)]))
        for target in base.TARGETS:
            records = [r for r in prepared if r['target']==target]
            for shift in SHIFTS_MS:
                best,profile = fit_models(records,shift)
                model_key = window+'_'+target+'_'+str(int(shift))
                models[model_key] = best
                profiles += [dict(target=target,window=window,**r) for r in profile]
                for r in records:
                    key = window+'_'+str(r['sweep'])+'_'+target
                    for method,model in best.items():
                        prediction = predict_innovation(r,model)
                        arrays[key+'_shift'+str(int(shift))+'_'+method] = prediction
                        for region in ('initial','recovery'):
                            rows.append(dict(window=window,target=target,sweep=r['sweep'],gap_ms=r['gap_s']*1000,
                                shift_ms=shift,method=method,region=region,**error_metrics(r,prediction,region)))
                print('TIMING_FIT',model_key,json.dumps(best),flush=True)
    summary = summarize(rows)
    args.array_output.parent.mkdir(parents=True,exist_ok=True)
    with args.array_output.open('xb') as stream:
        np.savez_compressed(stream,**arrays)
    result = dict(question='Does actual source AP timing improve conditional waveform prediction over shifted schedules and past target voltage?',
        status='Retrospective timing specificity diagnostic; shifted controls are not exchangeable nulls or causal mechanisms',
        source_sha256=base.sha(__file__),test_sha256=base.sha(ROOT/'tests/test_recovery_source_timing.py'),
        runtime=dict(python=platform.python_version(),numpy=np.__version__),provenance=provenance,
        design=dict(train_sweeps=list(base.TRAIN_SWEEPS),temporal_sweeps=list(base.TEMPORAL_SWEEPS),
            training_pulses=list(range(1,9)),window_bounds_s=WINDOWS,shifts_ms=SHIFTS_MS,
            observation='Parent actual target bins and artifact masks remain fixed across source-time shifts. Each pulse uses the last available 0.5ms bin before its artifact/response blackout. All AP+[2,18]ms excluded from baseline updates for both windows.',
            first_guard='Only pre bins ending at or before command0 minus0.5ms are restored. Earlier causal code restored all negative-time bins, including first guard; old registered code is preserved.',
            fitting='Each target/window/shift independently fits initial8 of37..46; 140 original kernels and46 efficacy candidates, nonnegative common amplitude and no free offset. Equal sweep/pulse weight, all bins retained.',
            equation='Prediction = baseline + A*(kernel_history_at_score - kernel_history_at_anchor). Actual and shifted conditions share identical target observations and anchors.',
            interpretation='Only zero-shift model uses actual causal source timing. Negative shifts may use future source events; all nonzero shifts are descriptive controls. Shift and fitted latency can offset; 50Hz half-cycle shifts alias. No permutation p-value or uniquely identified delay.',
            metric='Waveform MSE equals mean pulse-error squared plus within-pulse centered error MSE. Means are computed from the same waveform-fitted candidate, not refitted mean models.',
            boundaries='Not directly comparable with prior open-loop waveform RMSE, nor identical to prior short response mean fit. Same previously inspected cells; no blind validation or identified plasticity.'),
        observation_checks=design_checks,models=models,actual_time_kernel_profiles=profiles,per_sweep=rows,summary=summary,
        arrays=dict(path=args.array_output.relative_to(ROOT).as_posix(),sha256=base.sha(args.array_output),bytes=args.array_output.stat().st_size))
    with args.output.open('x',encoding='utf-8',newline='\n') as stream:
        json.dump(result,stream,indent=2,ensure_ascii=False,allow_nan=False)
        stream.write('\n')
    print('TIMING_RESULT',args.output,base.sha(args.output),flush=True)
    print(json.dumps([r for r in summary if r['shift_ms']==0 and r['cohort']=='temporal'],indent=2))


if __name__=='__main__':
    main()
