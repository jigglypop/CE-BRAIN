"""Quiet-calibrated causal state prediction, then matched AP-response forecasts.

Retrospective development. All source artifacts remain unchanged. The observation
budget differs from the previous open-loop waveform study: earlier target voltage
between responses is now available, but each scored response is withheld.
"""
import argparse
import importlib.util
import json
import platform
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
spec = importlib.util.spec_from_file_location('waveform_parent', HERE/'recovery_waveform_prediction.py')
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
DT = .0005
RATIOS = np.logspace(-6, 4, 41)
BURN = 200
ORIGINS = np.arange(200, 840, 20)  # 100 ms warmup; every10ms; all horizons fit.
HORIZONS = {'near':np.arange(8,20), 'far':np.arange(40,52)}


def state_matrices(kind, ratio):
    if not np.isfinite(ratio) or ratio <= 0:
        raise ValueError('Positive finite process/observation variance ratio required')
    if kind == 'local_level':
        return np.ones((1,1)), np.array([[ratio]])
    if kind == 'local_trend':
        return np.array([[1.,1.],[0.,1.]]), ratio*np.array([[1/3,.5],[.5,1.]])
    raise ValueError(kind)


def filter_values(values, kind, ratio, update=None):
    """Filter batches causally. One step is one0.5ms bin; velocity is uV/bin."""
    values = np.asarray(values,float)
    if values.ndim == 1:
        values = values[None,:]
    if values.ndim != 2 or not np.isfinite(values).all():
        raise ValueError('Finite two-dimensional observations required')
    f,q = state_matrices(kind,ratio)
    count,n = values.shape
    d = len(f)
    update = np.ones(n,dtype=bool) if update is None else np.asarray(update,dtype=bool)
    if update.shape != (n,) or not update[0]:
        raise ValueError('Initial observation must be available')
    states = np.zeros((count,n,d))
    states[:,0,0] = values[:,0]
    p = np.eye(d)*1e6
    covariances = np.zeros((n,d,d))
    covariances[0] = p
    errors,variances = np.zeros((count,n)),np.zeros(n)
    for k in range(1,n):
        prediction = states[:,k-1]@f.T
        prior = f@p@f.T+q
        error = values[:,k]-prediction[:,0]
        variance = prior[0,0]+1.
        errors[:,k],variances[k] = error,variance
        if update[k]:
            gain = prior[:,0]/variance
            states[:,k] = prediction+error[:,None]*gain
            residual = np.eye(d)
            residual[:,0] -= gain
            p = residual@prior@residual.T+np.outer(gain,gain)
        else:
            states[:,k] = prediction
            p = prior
        covariances[k] = p
    return states,covariances,errors,variances


def future_mean_geometry(kind,ratio,offsets):
    """Offsets relative to the first unavailable bin. Average future covariance."""
    f,q = state_matrices(kind,ratio)
    steps = np.asarray(offsets,dtype=int)+1
    if len(steps)<1 or np.any(steps<1):
        raise ValueError('Future offsets required')
    powers = [np.linalg.matrix_power(f,i) for i in range(int(steps.max())+1)]
    vector = np.mean([powers[int(h)][0] for h in steps],axis=0)
    process_variance = 0.
    for j in range(1,int(steps.max())+1):
        effect = sum((powers[int(h)-j][0] for h in steps if h>=j),start=np.zeros(len(f)))/len(steps)
        process_variance += float(effect@q@effect)
    return vector,process_variance+1/len(steps)


def quiet_forecasts(values,config):
    values = np.asarray(values,float)
    predictions,variances = {},{}
    if config['kind'] in ('last_bin','mean2ms'):
        for name,offsets in HORIZONS.items():
            if config['kind']=='last_bin':
                predictions[name] = values[:,ORIGINS-1]
            else:
                predictions[name] = np.stack([values[:,i-4:i].mean(axis=1) for i in ORIGINS],axis=1)
            variances[name] = None
        return predictions,variances,None
    states,cov,e,s = filter_values(values,config['kind'],config['ratio'])
    for name,offsets in HORIZONS.items():
        vector,extra = future_mean_geometry(config['kind'],config['ratio'],offsets)
        predictions[name] = states[:,ORIGINS-1]@vector
        variances[name] = config['observation_variance_uV2']*(np.einsum('i,kij,j->k',vector,cov[ORIGINS-1],vector)+extra)
    return predictions,variances,(e[:,BURN:],s[BURN:])


def calibrate_quiet(values):
    """Only the caller-supplied training quiet records may influence selection."""
    train = np.asarray(values,float)
    assert train.shape == (10,900)
    candidates,profiles = [dict(kind='last_bin'),dict(kind='mean2ms')],[]
    for kind in ('local_level','local_trend'):
        best = None
        for ratio in RATIOS:
            _,_,errors,variance = filter_values(train,kind,float(ratio))
            e,s = errors[:,BURN:],variance[BURN:]
            scale = float(np.mean(e*e/s))
            score = float(.5*(np.log(2*np.pi)+1+np.log(scale)+np.mean(np.log(s))))
            row = dict(kind=kind,ratio=float(ratio),observation_variance_uV2=scale,train_nll_per_bin=score)
            profiles.append(row)
            if best is None or score<best['train_nll_per_bin']:
                best = row
        candidates.append(dict(best))
    truth = {name:np.stack([train[:,i+offsets].mean(axis=1) for i in ORIGINS],axis=1)
             for name,offsets in HORIZONS.items()}
    for config in candidates:
        pred,_,_ = quiet_forecasts(train,config)
        config['training_near_rmse_uV'] = float(np.sqrt(np.mean((pred['near']-truth['near'])**2)))
    selected = min(candidates,key=lambda r:r['training_near_rmse_uV'])
    return selected,candidates,profiles


def summarize_quiet(values,candidates):
    summaries,arrays = [],{}
    truth = {name:np.stack([values[:,i+offsets].mean(axis=1) for i in ORIGINS],axis=1)
             for name,offsets in HORIZONS.items()}
    for name,y in truth.items():
        arrays['truth_'+name] = y
    for config in candidates:
        pred,variance,innovations = quiet_forecasts(values,config)
        for name in HORIZONS:
            arrays[config['kind']+'_prediction_'+name] = pred[name]
            for cohort,sl in [('training',slice(0,10)),('temporal',slice(10,20))]:
                error = pred[name][sl]-truth[name][sl]
                row = dict(model=config['kind'],horizon=name,cohort=cohort,sweeps=10,origins_per_sweep=len(ORIGINS),
                    rmse_uV=float(np.sqrt(np.mean(error**2))),bias_uV=float(error.mean()),
                    per_sweep_mse_uV2=np.mean(error**2,axis=1).tolist())
                if variance[name] is not None:
                    sd = np.sqrt(variance[name])
                    row['coverage_1_96sd'] = float(np.mean(np.abs(error)<=1.96*sd))
                summaries.append(row)
        if innovations is not None:
            e,s = innovations
            for cohort,sl in [('training',slice(0,10)),('temporal',slice(10,20))]:
                standardized = e[sl]/np.sqrt(s*config['observation_variance_uV2'])
                summaries.append(dict(model=config['kind'],cohort=cohort,horizon='one_bin_innovation',sweeps=10,
                    standardized_rms=float(np.sqrt(np.mean(standardized**2))),
                    mean_lag1_correlation=float(np.mean([np.corrcoef(v[:-1],v[1:])[0,1] for v in standardized]))))
    return summaries,arrays


def forecast_operators(left_times,spikes,valid,config):
    """Return future measurement M and causal baseline B, with response blackout.

For every pulse, B is built without any target sample from its command/spike
blackout or scored response. Later predictions may use subsequent inter-response
voltage, including residual tails; the observation budget is identical for all
efficacy models.
"""
    left,spikes = np.asarray(left_times),np.asarray(spikes)
    right = left+DT
    update = (left<0)|np.asarray(valid,dtype=bool)
    measurement = np.zeros((len(spikes),len(left)))
    for n,spike in enumerate(spikes):
        score = (left>=spike+.002)&(right<=spike+.008)&valid
        if not score.any():
            raise ValueError('No complete response bins')
        measurement[n,score] = 1/score.sum()
        update &= ~((left<spike+.008)&(right>spike+.002))
    assert update[0]
    baseline = np.zeros_like(measurement)
    if config['kind'] in ('last_bin','mean2ms'):
        history = [0]
        for k in range(1,len(left)):
            for n in np.flatnonzero(measurement[:,k]):
                previous = history[-1:] if config['kind']=='last_bin' else history[-4:]
                baseline[n,previous] += measurement[n,k]/len(previous)
            if update[k]:
                history.append(k)
    else:
        f,q = state_matrices(config['kind'],config['ratio'])
        d = len(f)
        weights = np.zeros((d,len(left)))
        weights[0,0] = 1.
        covariance = np.eye(d)*1e6
        for k in range(1,len(left)):
            weights = f@weights
            prior = f@covariance@f.T+q
            for n in np.flatnonzero(measurement[:,k]):
                baseline[n] += measurement[n,k]*weights[0]
            if update[k]:
                gain = prior[:,0]/(prior[0,0]+1.)
                residual_weights = -weights[0].copy()
                residual_weights[k] += 1.
                weights += np.outer(gain,residual_weights)
                residual = np.eye(d)
                residual[:,0] -= gain
                covariance = residual@prior@residual.T+np.outer(gain,gain)
            else:
                covariance = prior
    for n in range(len(spikes)):
        first_score = np.flatnonzero(measurement[n])[0]
        assert np.all(baseline[n,first_score:]==0), 'Target-outcome leakage'
    np.testing.assert_allclose(baseline.sum(axis=1),1.,atol=1e-8)
    return measurement,baseline,update


def fit_efficacy(records):
    train = [r for r in records if r['sweep'] in base.TRAIN_SWEEPS]
    assert len(train)==10
    y = np.concatenate([r['innovation'][:8] for r in train])
    q = [np.array([base.efficacy(r['spikes'],*g) for g in base.HISTORY_GRID]) for r in train]
    best = {'none':dict(model='none',amplitude_uV=0.,training_mse_uV2=float(np.mean(y*y)))}
    for lag,rise,decay in base.KERNEL_GRID:
        x = np.concatenate([(r['operator']@base.kernel_basis(r['left_times'],r['spikes'],lag/1000,rise/1000,decay/1000))[:8]@weights.T
                            for r,weights in zip(train,q)])
        xx,xy = np.sum(x*x,axis=0),np.sum(x*y[:,None],axis=0)
        amplitude = np.maximum(0.,np.divide(xy,xx,out=np.zeros_like(xy),where=xx>1e-20))
        mse = np.mean((y[:,None]-x*amplitude)**2,axis=0)
        for i,(name,strength,tau) in enumerate(base.HISTORY_GRID):
            model = dict(model=name,strength=strength,tau_s=tau,lag_ms=lag,rise_ms=rise,decay_ms=decay,
                         amplitude_uV=float(amplitude[i]),training_mse_uV2=float(mse[i]))
            if name not in best or mse[i]<best[name]['training_mse_uV2']:
                best[name] = model
    return best


def predict_efficacy(record,model):
    baseline = record['baseline_prediction']
    if model['model']=='none':
        return baseline.copy()
    signal = base.kernel_basis(record['left_times'],record['spikes'],model['lag_ms']/1000,
        model['rise_ms']/1000,model['decay_ms']/1000)@base.efficacy(record['spikes'],model['model'],model['strength'],model['tau_s'])
    return baseline+model['amplitude_uV']*(record['operator']@signal)


def load_inputs():
    parent_path = HERE/'recovery_waveform_prediction_result.json'
    parent = json.loads(parent_path.read_text(encoding='utf-8'))
    assert base.sha(HERE/'recovery_waveform_prediction.py')==parent['code_sha256']
    assert base.sha(ROOT/parent['arrays']['path'])==parent['arrays']['sha256']
    command_path = HERE/'ic_command_context_result.json'
    command = json.loads(command_path.read_text(encoding='utf-8'))
    archive = base.CACHE/'ic_all_command_context.npz'
    assert base.sha(archive)==command['archive_sha256']
    assert len(command['metadata'])==60
    with np.load(archive,allow_pickle=False) as z:
        for entry in command['metadata']:
            assert entry['unit']=='A' and entry['rate']==100000
            values = z[entry['key']+'_baseline']
            assert values.shape==(45000,) and np.all(values==0)
    assets = {row['path']:row for row in parent['provenance']['assets']}
    quiet,raw_checks = {target:[] for target in base.TARGETS},[]
    for sweep in range(37,57):
        source = base.CACHE/f'recovery_train_sources/{sweep}.npz'
        assert base.sha(source)==assets[source.relative_to(ROOT).as_posix()]['sha256']
        with np.load(source,allow_pickle=False) as z:
            assert np.all(z['current'][8000:53000]==0)
            assert len(base.spike_crossings(z['voltage'][8000:53000],100000))==0
        for target in base.TARGETS:
            path = base.CACHE/f'full_ic_targets/{sweep}_{target}.npz'
            assert base.sha(path)==assets[path.relative_to(ROOT).as_posix()]['sha256']
            with np.load(path,allow_pickle=False) as z:
                values = z['voltage'][8000:53000]*1e6
            assert len(values)==45000 and np.isfinite(values).all()
            bins = values.reshape(-1,50).mean(axis=1)
            quiet[target].append(bins)
            raw_checks.append(dict(sweep=sweep,target=target,quiet_sd_uV=float(bins.std(ddof=1)),
                difference_lag1_correlation=float(np.corrcoef(np.diff(bins)[:-1],np.diff(bins)[1:])[0,1])))
    records = []
    with np.load(ROOT/parent['arrays']['path'],allow_pickle=False) as z:
        for metadata in parent['records']:
            key = str(metadata['sweep'])+'_'+metadata['target']
            records.append(dict(metadata,**{name:z[key+'_'+name] for name in ('left_times','spikes','y','valid')}))
    provenance = dict(parent_path=parent_path.relative_to(ROOT).as_posix(),parent_sha256=base.sha(parent_path),
        parent_source_sha256=parent['code_sha256'],parent_arrays_sha256=parent['arrays']['sha256'],
        command_context_sha256=base.sha(command_path),command_archive_sha256=base.sha(archive),
        core_source_APs_in_quiet=0,command_checks=60,quiet_sample_bounds=[8000,53000],raw_checks=raw_checks,
        reused_eligibility=parent['provenance']['eligibility'])
    return {target:np.array(values) for target,values in quiet.items()},records,provenance


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,default=HERE/'recovery_causal_baseline_result.json')
    parser.add_argument('--array-output',type=Path,default=ROOT/'data/local/allen-synphys-analysis/recovery-causal-baseline-v1/causal_baseline_arrays.npz')
    args = parser.parse_args()
    if args.output.exists() or args.array_output.exists():
        raise FileExistsError('Preserve prior causal-baseline outputs')
    quiet,raw_records,provenance = load_inputs()
    calibration,quiet_summary,models,rows,arrays = {},[],{},[],{}
    for target in base.TARGETS:
        selected,candidates,profile = calibrate_quiet(quiet[target][:10])
        summaries,qa = summarize_quiet(quiet[target],candidates)
        quiet_summary += [dict(target=target,**r) for r in summaries]
        arrays.update({target+'_quiet_'+k:v for k,v in qa.items()})
        arrays[target+'_quiet_observed'] = quiet[target]
        calibration[target] = dict(selected=selected,candidates=candidates,likelihood_profile=profile)
        configs = {'selected':selected,'last_bin':dict(kind='last_bin')}
        models[target] = {}
        for baseline_name,config in configs.items():
            prepared = []
            for record in raw_records:
                if record['target']!=target:
                    continue
                measurement,baseline,update = forecast_operators(record['left_times'],record['spikes'],record['valid'],config)
                operator = measurement-baseline
                observed = measurement@record['y']
                forecast = baseline@record['y']
                prepared.append(dict(record,operator=operator,observed=observed,baseline_prediction=forecast,innovation=observed-forecast))
            best = fit_efficacy(prepared)
            models[target][baseline_name] = best
            for record in prepared:
                key = str(record['sweep'])+'_'+target+'_'+baseline_name
                arrays[key+'_observed'] = record['observed']
                arrays[key+'_baseline'] = record['baseline_prediction']
                for method,model in best.items():
                    prediction = predict_efficacy(record,model)
                    arrays[key+'_prediction_'+method] = prediction
                    for region,sl in [('initial',slice(0,8)),('recovery',slice(8,12))]:
                        error = prediction[sl]-record['observed'][sl]
                        rows.append(dict(sweep=record['sweep'],target=target,baseline=baseline_name,method=method,region=region,
                            pulses=len(error),mse_uV2=float(np.mean(error**2)),bias_uV=float(error.mean()),gap_ms=record['gap_s']*1000))
            print('CAUSAL_FIT',target,baseline_name,json.dumps(best),flush=True)
    summary = []
    for target in base.TARGETS:
        for baseline in ('selected','last_bin'):
            for cohort,sweeps in [('training',base.TRAIN_SWEEPS),('temporal',base.TEMPORAL_SWEEPS),('variable_gap',range(32,37))]:
                for region in ('initial','recovery'):
                    for method in ('none','constant','depression','facilitation'):
                        rr = [r for r in rows if r['target']==target and r['baseline']==baseline and r['sweep'] in sweeps and r['region']==region and r['method']==method]
                        if not rr:
                            continue
                        comparators = {}
                        for ref in ('none','constant'):
                            gains = [next(r['mse_uV2'] for r in rows if r['target']==target and r['baseline']==baseline and r['region']==region and r['method']==ref and r['sweep']==row['sweep'])-row['mse_uV2'] for row in rr]
                            comparators[ref] = dict(mean_gain_uV2=float(np.mean(gains)),median_gain_uV2=float(np.median(gains)),improved_sweeps=int(np.sum(np.array(gains)>0)))
                        summary.append(dict(target=target,baseline=baseline,cohort=cohort,region=region,method=method,sweeps=len(rr),
                            rmse_uV=float(np.sqrt(np.mean([r['mse_uV2'] for r in rr]))),comparators=comparators))
    args.array_output.parent.mkdir(parents=True,exist_ok=True)
    with args.array_output.open('xb') as stream:
        np.savez_compressed(stream,**arrays)
    result = dict(question='Does history-dependent efficacy improve response forecasts after quiet-only causal voltage-state calibration?',
        status='Retrospective conditional prediction; no blind validation or identified plasticity',
        source_sha256=base.sha(__file__),test_sha256=base.sha(ROOT/'tests/test_recovery_causal_baseline.py'),
        runtime=dict(python=platform.python_version(),numpy=np.__version__),provenance=provenance,
        quiet_design=dict(train_sweeps=list(base.TRAIN_SWEEPS),test_sweeps=list(base.TEMPORAL_SWEEPS),window_s=[.08,.53],
            dt_s=DT,warmup_bins=BURN,origins_bins=ORIGINS.tolist(),horizon_offsets={k:v.tolist() for k,v in HORIZONS.items()},
            ratio_grid=RATIOS.tolist(),parameter_rule='Profile Gaussian innovation likelihood on training quiet only; choose forecast family by training mean4..10ms prediction MSE',
            caveat='The Gaussian state-space model is a statistical candidate, not a membrane equation; overlapping forecasts and same-cell sweeps are not independent animals'),
        forecast_design=dict(input='Prior target voltage and detected source AP times; target response windows withheld',
            observation_budget_change='Earlier inter-response target voltages are available. Do not compare RMSE directly with prior open-loop whole-waveform results.',
            state_models='Local level random walk; local linear trend with integrated white acceleration. Time unit one0.5ms bin, normalized observation variance1.',
            operator='M averages complete0.5ms bins in spike[2,8]ms. B forecasts from causal available bins, excluding parent artifact mask AND every scored response. L=M-B.',
            response_prediction='B*y + A*(M-B)*kernel_history; fit nonnegative A and same140x46 candidate grid on initial8 of37..46 only; no added free offset',
            controls='Quiet-selected baseline and last-bin baseline; each used identically for none/fixed/depression/facilitation',
            uncertainty='Quiet innovation/coverage diagnostics are descriptive; no Fisher or metric calibration is claimed from an unverified Gaussian noise law'),
        calibration=calibration,quiet_summary=quiet_summary,models=models,per_sweep=rows,summary=summary,
        arrays=dict(path=args.array_output.relative_to(ROOT).as_posix(),sha256=base.sha(args.array_output),bytes=args.array_output.stat().st_size))
    with args.output.open('x',encoding='utf-8',newline='\n') as stream:
        json.dump(result,stream,indent=2,ensure_ascii=False,allow_nan=False)
        stream.write('\n')
    print('CAUSAL_RESULT',args.output,base.sha(args.output),flush=True)
    print(json.dumps([r for r in summary if r['cohort']=='temporal' and r['baseline']=='selected'],indent=2))


if __name__=='__main__':
    main()
