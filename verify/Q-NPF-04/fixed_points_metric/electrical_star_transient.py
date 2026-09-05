"""Development-only command-locked RC predictions; never reads sweeps 13--15."""
import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

import h5py
import numpy as np

from allen_joint_inventory import BASE, OfflineRanges, raw, sha

HERE = Path(__file__).resolve().parent
OUTPUT = HERE/'electrical_star_transient_result.json'
SWEEPS = [10, 11, 12]
DEVICES = [4, 1, 2, 5]
TAUS = np.array([.005, .01, .02, .04, .08, .16])
EDGES = np.linspace(-.3, 1.2, 301)
TIMES = (EDGES[:-1]+EDGES[1:])/2
KEEP = (np.abs(TIMES) > .005) & (np.abs(TIMES-1) > .005)
TIME = TIMES[KEEP]


def project(values):
    """Fixed affine-drift quotient, NOT causal baseline prediction."""
    values = np.asarray(values, float)
    basis = np.column_stack([np.ones(len(TIME)), TIME])
    flat = values.reshape(-1, len(TIME))
    trend = np.linalg.lstsq(basis, flat.T, rcond=None)[0]
    return (flat-(basis@trend).T).reshape(values.shape)


def primitive(t, taus):
    """Integral from zero of the causal unit-step response."""
    t = np.maximum(np.asarray(t, float), 0.)
    if not taus:
        return t
    a = taus[0]
    if len(taus) == 1:
        return t+a*np.expm1(-t/a)
    b = taus[1]
    if a == b:
        return t-2*a+(t+2*a)*np.exp(-t/a)
    return t+(a*a*np.expm1(-t/a)-b*b*np.expm1(-t/b))/(a-b)


def kernel(taus=()):
    """Exact 5 ms bin means of a one-second rectangular input response."""
    integrated = primitive(EDGES, taus)-primitive(EDGES-1., taus)
    return (np.diff(integrated)/np.diff(EDGES))[KEEP]


def fit_model(voltage, currents):
    """Only training sweeps enter this function; no held response argument."""
    voltage = project(voltage)
    currents = np.asarray(currents, float)/1000  # pA*MOhm -> mV
    n = currents.shape[1]
    instant = project(kernel())
    own = []
    for cell in range(n):
        candidates = []
        target = voltage[:, cell, cell].reshape(-1)
        for tau in TAUS:
            templates = np.stack([instant, project(kernel((tau,)))], axis=1)
            design = (currents[:, cell, None, None]*templates).reshape(-1, 2)
            coef = np.linalg.lstsq(design, target, rcond=None)[0]
            mse = float(np.mean((design@coef-target)**2))
            candidates.append(dict(tau_s=float(tau), coefficients_MOhm=coef.tolist(), mse=mse,
                                   condition=float(np.linalg.cond(design))))
        selected = min(candidates, key=lambda item:item['mse'])
        own.append(dict(selected=selected, candidates=candidates))
    gains = {name:np.zeros((n,n)) for name in ['cascade', 'instant']}
    for target in range(n):
        for source in range(n):
            if target == source:
                continue
            taus = (own[target]['selected']['tau_s'], own[source]['selected']['tau_s'])
            for name, template in [('cascade', project(kernel(taus))), ('instant', instant)]:
                design = currents[:, source, None]*template
                gains[name][target,source] = np.sum(design*voltage[:,target,source])/np.sum(design**2)
    return dict(own=own, gains_MOhm={name:value.tolist() for name,value in gains.items()})


def predict(model, currents, name):
    """Prediction depends on held commands only; returns the filtered endpoint."""
    currents = np.asarray(currents, float)/1000
    n = len(currents)
    values = np.zeros((n,n,len(TIME)))
    for target in range(n):
        for source in range(n):
            if target == source:
                tau = model['own'][target]['selected']['tau_s']
                a,b = model['own'][target]['selected']['coefficients_MOhm']
                values[target,source] = currents[source]*project(a*kernel()+b*kernel((tau,)))
            else:
                taus = (model['own'][target]['selected']['tau_s'],model['own'][source]['selected']['tau_s'])
                template = kernel(taus) if name == 'cascade' else kernel()
                values[target,source] = currents[source]*model['gains_MOhm'][name][target][source]*project(template)
    return values


def extract():
    protocol = json.loads((HERE/'electrical_star_protocol_result.json').read_text(encoding='utf8'))
    commands = json.loads((HERE/'electrical_star_commands_result.json').read_text(encoding='utf8'))
    prior = json.loads((HERE/'electrical_star_transfer_result.json').read_text(encoding='utf8'))
    assert prior['all_quality_checks_pass']
    adc = {(r['sweep'],r['device']):r for r in protocol['records'] if r['kind']=='acquisition'}
    cmd = {(r['sweep'],r['device']):r for r in commands['commands']}
    records = []
    cache = BASE/'raw_ranges'/protocol['selection']['ext_id']
    with OfflineRanges(cache) as reader:
        assert reader.remote == protocol['remote']
        with h5py.File(reader, 'r') as f:
            for sweep in SWEEPS:
                v = np.zeros((4,4,len(TIME)))
                inputs = []
                for source_index,source in enumerate(DEVICES):
                    pulses = [p for p in cmd[sweep,source]['segments'] if p['duration_s']>=.1 and abs(p['current_pA'])>.05]
                    assert len(pulses)==1 and abs(pulses[0]['duration_s']-1)<1e-8
                    onset = pulses[0]['start_s']
                    inputs.append(pulses[0]['current_pA'])
                    for target_index,target in enumerate(DEVICES):
                        row = adc[sweep,target]
                        assert row['unit']=='V' and row['rate']==50000
                        assert row['start']==adc[sweep,source]['start']
                        start,end = round((onset-.3)*row['rate']),round((onset+1.2)*row['rate'])
                        raw_values = np.asarray(f[row['path']+'/data'][start:end],float)
                        assert raw_values.size==75000 and np.isfinite(raw_values).all()
                        values = (raw_values*row['conversion']+row['offset'])*1000
                        v[target_index,source_index] = values.reshape(300,250).mean(axis=1)[KEEP]
                records.append(dict(sweep=sweep, currents_pA=inputs, voltage_mV=v.tolist()))
                print('EXTRACTED_SEEN', sweep, flush=True)
        provenance = dict(remote=reader.remote,used_blocks=reader.used,new_download_bytes=0)
    return records, provenance


def evaluate(records):
    voltage = np.array([r['voltage_mV'] for r in records])
    currents = np.array([r['currents_pA'] for r in records])
    off = ~np.eye(4,dtype=bool)
    direct = np.zeros((4,4),bool); direct[0,1:]=True; direct[1:,0]=True
    rms = lambda value:float(np.sqrt(np.mean(value**2)))
    folds = []
    for held in range(3):
        train = [index for index in range(3) if index != held]
        model = fit_model(voltage[train],currents[train])
        observed = project(voltage[held])
        scores = {}
        for name in ['cascade','instant']:
            prediction = predict(model,currents[held],name)
            scores[name] = dict(prediction_mV=prediction.tolist())
            for label,mask in [('cross',off),('direct',direct)]:
                zero = rms(observed[mask]); error = rms((prediction-observed)[mask])
                scores[name][label] = dict(zero_rmse_mV=zero, rmse_mV=error,ratio_to_zero=error/zero if zero>0 else None)
            scores[name]['own_rmse_mV'] = rms((prediction-observed)[np.eye(4,dtype=bool)])
        passive_own = all(row['selected']['coefficients_MOhm'][1]>0 for row in model['own'])
        fold_pass = passive_own and all(scores['cascade'][label]['ratio_to_zero'] is not None and
                        scores['cascade'][label]['ratio_to_zero']<=.8 for label in ['cross','direct'])
        folds.append(dict(held_sweep=records[held]['sweep'],train_sweeps=[records[i]['sweep'] for i in train],
                          model=model,scores=scores,positive_own_slow_terms=passive_own,development_gate=fold_pass))
    return folds


def main():
    if OUTPUT.exists():
        raise FileExistsError(OUTPUT)
    records, provenance = extract()
    folds = evaluate(records)
    result = dict(created_utc=datetime.now(timezone.utc).isoformat(),code_sha256=sha(Path(__file__)),
        source_sha256={name:sha(HERE/name) for name in ['electrical_star_protocol_result.json',
            'electrical_star_commands_result.json','electrical_star_transfer_result.json','allen_joint_inventory.py']},
        raw_reader_sha256=sha(Path(raw.__file__)),
        execution=dict(python=platform.python_version(),numpy=np.__version__,h5py=h5py.__version__,executable=sys.executable),
        stage='POST_HOC_DEVELOPMENT; all three response sweeps already seen in the prior analysis',
        specification=dict(devices_center_then_leaves=DEVICES,seen_sweeps=SWEEPS,unopened_response_sweeps=[13,14,15],
            epoch_s=[-.3,1.2],bin_s=.005,excluded_transition_radius_s=.005,time_s=TIME.tolist(),
            nuisance='Fixed orthogonal removal of constant and linear time terms from data AND model; acausal contrast, not a raw-voltage prediction',
            own_model='Measured own response = instant command term + one RC pole; common amplitudes across each training fold',
            cross_model='Weak-coupling source/target two-RC cascade with one unconstrained gain per ordered pair',
            tau_grid_s=TAUS.tolist(),comparison='Instantaneous command-locked gain, fit on the same training sweeps',
            next_data_gate='Every leave-one-seen-sweep-out fold: positive own slow terms and cascade cross/direct RMSE <=0.8 times filtered zero response',
            claim_ceiling='BIO_EVIDENCE_L1 descriptive development; no independent biological confirmation or identified metric'),
        provenance=provenance,records=records,folds=folds,development_gate=all(f['development_gate'] for f in folds),
        final_model_all_seen=fit_model(np.array([r['voltage_mV'] for r in records]),np.array([r['currents_pA'] for r in records])),
        limits=['Affine drift removal does not remove curved drift or correlated synaptic background',
                'Cross-talk with the same filtered kernel is observationally indistinguishable from coupling',
                'Own pole estimates include electrode and network dynamics; they are not calibrated membrane constants',
                'Two-pole cascade is a weak-coupling approximation, not the exact coupled-network transfer',
                'Three already-seen sweeps are not independent validation; bins are not independent biological replicates',
                'A constant cross gain is not a junction conductance; no inversion to a spatial metric is performed'])
    with OUTPUT.open('x',encoding='utf8') as stream:
        json.dump(result,stream,ensure_ascii=False,indent=2,allow_nan=False);stream.write('\n')
    print('DONE',json.dumps(dict(development_gate=result['development_gate'],folds=[dict(sweep=f['held_sweep'],
        cascade_cross=f['scores']['cascade']['cross']['ratio_to_zero'],cascade_direct=f['scores']['cascade']['direct']['ratio_to_zero'],
        instant_cross=f['scores']['instant']['cross']['ratio_to_zero']) for f in folds],sha256=sha(OUTPUT))),flush=True)


if __name__ == '__main__':
    main()
