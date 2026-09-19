"""Post-result sensitivity: anchor the effective waveform to its pretrain mean.

The parent best depression fit uses a large learned offset. Preserve that result
and ask whether its predictive advantage survives b=0, with the SAME grid/split.
This is an exploratory measurement-model comparison, not a new blind validation.
"""
import argparse
import importlib.util
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
spec = importlib.util.spec_from_file_location('parent_waveform',HERE/'recovery_waveform_prediction.py')
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)


def fit_zero_offset(x,y,weights):
    x = np.asarray(x,float)
    if x.ndim == 1:
        x = x[:,None]
    y,w = np.asarray(y,float),np.asarray(weights,float)
    if len(x) != len(y) or w.shape != y.shape or np.any(w<0) or w.sum()<=0:
        raise ValueError('Invalid weighted regression')
    w = w/w.sum()
    xx = np.sum(w[:,None]*x*x,axis=0)
    xy = np.sum(w[:,None]*x*y[:,None],axis=0)
    amplitude = np.maximum(0.,np.divide(xy,xx,out=np.zeros_like(xy),where=xx>1e-20))
    mse = np.sum(w[:,None]*(y[:,None]-x*amplitude)**2,axis=0)
    return amplitude,mse


def fit_models(records):
    training = [r for r in records if r['sweep'] in base.TRAIN_SWEEPS]
    assert len(training) == 10
    y = np.concatenate([r['y'][r['initial']] for r in training])
    w = np.concatenate([np.full(int(r['initial'].sum()),1/r['initial'].sum()/10) for r in training])
    q = [np.array([base.efficacy(r['spikes'],*g) for g in base.HISTORY_GRID]) for r in training]
    best = {name:dict(model=name,offset_uV=0.,amplitude_uV=0.,train_mse_uV2=float(w@(y*y)))
            for name in ('zero','offset')}
    # 'offset' is retained as a zero-valued alias for exact parent schema parity.
    for lag,rise,decay in base.KERNEL_GRID:
        x = np.concatenate([base.kernel_basis(r['left_times'][r['initial']],r['spikes'],lag/1000,rise/1000,decay/1000)@weights.T
                            for r,weights in zip(training,q)])
        amplitude,mse = fit_zero_offset(x,y,w)
        for i,(name,strength,tau) in enumerate(base.HISTORY_GRID):
            row = dict(model=name,strength=strength,tau_s=tau,lag_ms=lag,rise_ms=rise,decay_ms=decay,
                       amplitude_uV=float(amplitude[i]),offset_uV=0.,train_mse_uV2=float(mse[i]))
            if name not in best or row['train_mse_uV2'] < best[name]['train_mse_uV2']:
                best[name] = row
    return best


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,default=HERE/'recovery_offset_sensitivity_result.json')
    parser.add_argument('--array-output',type=Path,default=ROOT/'data/local/allen-synphys-analysis/recovery-offset-sensitivity-v1/recovery_anchored_arrays.npz')
    args = parser.parse_args()
    if args.output.exists() or args.array_output.exists():
        raise FileExistsError('Preserve prior sensitivity outputs')
    parent_path = HERE/'recovery_waveform_prediction_result.json'
    parent = json.loads(parent_path.read_text(encoding='utf-8'))
    assert base.sha(HERE/'recovery_waveform_prediction.py') == parent['code_sha256']
    assert base.sha(ROOT/'tests/test_recovery_waveform_prediction.py') == parent['test_sha256']
    assert base.sha(ROOT/parent['arrays']['path']) == parent['arrays']['sha256']
    records = []
    with np.load(ROOT/parent['arrays']['path'],allow_pickle=False) as arrays:
        for metadata in parent['records']:
            key = str(metadata['sweep'])+'_'+metadata['target']
            records.append(dict(metadata,**{name:arrays[key+'_'+name] for name in
                ('left_times','y','initial','gap','recovery','tail','valid','spikes')}))
    models = {target:fit_models([r for r in records if r['target']==target]) for target in base.TARGETS}
    per_sweep,summary,arrays = base.evaluate(records,models)
    args.array_output.parent.mkdir(parents=True,exist_ok=True)
    with args.array_output.open('xb') as stream:
        np.savez_compressed(stream,**arrays)
    comparisons = []
    for row in summary:
        if row['rmse_uV'] is None:
            continue
        old = next(r for r in parent['summary'] if all(r[k] == row[k] for k in ('target','cohort','region','method')))
        comparisons.append(dict(target=row['target'],cohort=row['cohort'],region=row['region'],method=row['method'],
                                shared_offset_rmse_uV=old['rmse_uV'],anchored_rmse_uV=row['rmse_uV']))
    result = dict(question='Does the history-model advantage survive anchoring the offset to the pretrain mean?',
        status='Post-result exploratory sensitivity; parent predictions and split preserved',
        trigger='Parent positive depression selected offset -413.328uV and128ms decay at grid ceiling',
        change='Set shared offset to zero for every candidate; refit only initial8 of37..46 with exactly the parent kernel/history grid and sign constraint',
        caveat='Neither zero offset nor a free shared offset is established as the true physiological baseline model. Dependence on this choice weakens mechanistic identification.',
        parent_path=parent_path.relative_to(ROOT).as_posix(),parent_sha256=base.sha(parent_path),
        parent_source_sha256=parent['code_sha256'],parent_array_sha256=parent['arrays']['sha256'],
        source_sha256=base.sha(__file__),test_sha256=base.sha(ROOT/'tests/test_recovery_offset_sensitivity.py'),
        models=models,per_sweep=per_sweep,summary=summary,comparisons=comparisons,
        arrays=dict(path=args.array_output.relative_to(ROOT).as_posix(),sha256=base.sha(args.array_output),bytes=args.array_output.stat().st_size))
    with args.output.open('x',encoding='utf-8',newline='\n') as stream:
        json.dump(result,stream,indent=2,ensure_ascii=False,allow_nan=False)
        stream.write('\n')
    print('SENSITIVITY_RESULT',args.output,base.sha(args.output))
    print(json.dumps(dict(models=models,temporal=[r for r in summary if r['cohort']=='temporal' and r['region'] in ('initial','recovery')]),indent=2))


if __name__ == '__main__':
    main()
