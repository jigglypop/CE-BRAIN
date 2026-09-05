"""Fixed operational small-response gate and conditional IC transfer prediction.

The sweep split and thresholds precede the first FastRheo ADC-array access.
Notebook response/QC summaries were already exposed: this is development,
not pristine prospective confirmation. No intrinsic conductance is estimated.
"""
import json
from datetime import datetime, timezone
from pathlib import Path

import h5py
import numpy as np

from allen_joint_inventory import BASE, raw, sha
from electrical_star_vc_inputs import settings

HERE=Path(__file__).resolve().parent
OUTPUT=HERE/'electrical_star_fastrheo_response_result.json'
CONTRACT=HERE/'electrical_star_fastrheo_response_specification.json'
DEVICES=[0,1,2,4,5,6,7]
PRIMARY=[4,1,2,5]
SWEEPS=list(range(16,35))
TRAIN=list(range(16,35,2))
HELD=list(range(17,35,2))
RATE=50000
BASELINE=slice(250,1000)  # 5..20 ms, pre-stimulus only
RESPONSE=slice(1250,5000)  # 25..100 ms; includes the 25..28 ms command


def matrix_quality(a):
    a=np.asarray(a,float)
    if not len(a):return dict(rows=0,rank=0,singular_pA=[],condition=None)
    singular=np.linalg.svd(a,compute_uv=False)
    threshold=max(1e-4,1e-6*singular[0])
    rank=int(np.sum(singular>threshold))
    condition=float(singular[0]/singular[-1]) if rank==a.shape[1] else None
    return dict(rows=len(a),rank=rank,singular_pA=singular.tolist(),condition=condition)


def channel_quality(voltage):
    voltage=np.asarray(voltage,float)
    assert voltage.shape==(6400,) and np.isfinite(voltage).all()
    baseline=float(voltage[BASELINE].mean())
    noise=float(np.sqrt(np.mean((voltage[BASELINE]-baseline)**2)))
    response=voltage[RESPONSE]
    excursion=float(np.max(np.abs(response-baseline)))
    vmax=float(response.max())
    quality=dict(baseline_mV=baseline,baseline_rms_mV=noise,
        baseline_half_difference_mV=float(voltage[625:1000].mean()-voltage[250:625].mean()),
        response_peak_abs_delta_mV=excursion,response_max_mV=vmax,
        baseline_noise_pass=noise<=.5,small_recorded_excursion_pass=excursion<=10,
        high_voltage_exclusion_pass=vmax< -20,
        local_waveform_pass=bool(noise<=.5 and excursion<=10 and vmax< -20))
    return quality,(response-baseline).reshape(750,5).mean(axis=1)


def rms(a):return float(np.sqrt(np.mean(np.asarray(a)**2)))


def predict_if_eligible(records):
    train=[r for r in records if r['split']=='train' and r['all_seven_quality_pass']]
    held=[r for r in records if r['split']=='held' and r['all_seven_quality_pass']]
    x=np.asarray([r['currents_pA'] for r in train],float).reshape(-1,7)
    z=np.asarray([r['currents_pA'] for r in held],float).reshape(-1,7)
    design=matrix_quality(x)
    result=dict(eligible_train_sweeps=[r['sweep'] for r in train],eligible_held_sweeps=[r['sweep'] for r in held],
        training_design=design,held_design=matrix_quality(z),executed=False)
    if design['rank']!=7 or design['condition'] is None or design['condition']>100 or len(held)<3:
        result['reason']='Insufficient fixed-split eligible training rank/conditioning or fewer than three eligible held sweeps'
        return result
    y=np.asarray([r['response_delta_mV_0p1ms'] for r in train])
    observed=np.asarray([r['response_delta_mV_0p1ms'] for r in held])
    x=x/1000;z=z/1000  # nA, so fitted coefficients have MOhm units
    full_coef=np.linalg.lstsq(x,y.reshape(len(train),-1),rcond=None)[0].reshape(7,7,750)
    full=np.einsum('hs,stv->htv',z,full_coef)
    diagonal_coef=np.einsum('st,stv->tv',x,y)/np.sum(x*x,axis=0)[:,None]
    diagonal=z[:,:,None]*diagonal_coef
    zero_own=np.abs(z)<5e-6
    zero_own &= np.any(np.abs(z)>5e-6,axis=1)[:,None]
    full_error=rms(full-observed);diagonal_error=rms(diagonal-observed)
    scores=dict(full_rmse_mV=full_error,diagonal_rmse_mV=diagonal_error,
        ratio_full_to_diagonal=full_error/diagonal_error if diagonal_error>0 else None,
        zero_own_case_count=int(zero_own.sum()),zero_own_target_count=int(np.any(zero_own,axis=0).sum()))
    if zero_own.any():
        zero_error=rms(observed[zero_own]);cross_error=rms((full-observed)[zero_own])
        noise=np.array([[c['baseline_rms_mV'] for c in r['channels']] for r in held])
        scores.update(zero_own_full_rmse_mV=cross_error,zero_own_zero_rmse_mV=zero_error,
            zero_own_ratio=cross_error/zero_error if zero_error>0 else None,
            zero_own_baseline_rms_mV=rms(noise[zero_own]))
    candidate_pass=bool(scores['zero_own_case_count']>=3 and scores['zero_own_target_count']>=2
        and scores['ratio_full_to_diagonal'] is not None and scores['ratio_full_to_diagonal']<=1.05
        and scores.get('zero_own_ratio') is not None and scores['zero_own_ratio']<=.8)
    result.update(executed=True,full_coefficients_MOhm=full_coef.tolist(),diagonal_coefficients_MOhm=diagonal_coef.tolist(),
        held_full_prediction_delta_mV=full.tolist(),held_diagonal_prediction_delta_mV=diagonal.tolist(),scores=scores,
        waveform_development_gate=candidate_pass,full_seven_input_validation_possible=result['held_design']['rank']==7)
    return result


def main():
    if OUTPUT.exists():raise FileExistsError(OUTPUT)
    code_hash=sha(Path(__file__))
    protocol_path=HERE/'electrical_star_all_protocols_result.json'
    command_path=HERE/'electrical_star_ic_input_census_result.json'
    protocol=json.loads(protocol_path.read_text(encoding='utf8'))
    commands=json.loads(command_path.read_text(encoding='utf8'))
    cmd={r['sweep']:r for r in commands['sweeps']}
    adc={(r['sweep'],r['device']):r for r in protocol['records'] if r['kind']=='acquisition'}
    inputs={}
    for sweep in SWEEPS:
        inputs[sweep]=[]
        for ch in cmd[sweep]['channels']:
            assert ch['device']==DEVICES[len(inputs[sweep])]
            active=[s for s in ch['segments'] if abs(s['command_pA']-ch['baseline_command_pA'])>.005]
            assert len(active)<=1
            if active:
                assert abs(active[0]['start_s']-.025)<1e-8 and abs(active[0]['end_s']-.028)<1e-8
            inputs[sweep].append(active[0]['command_pA']-ch['baseline_command_pA'] if active else 0.)
    specification=dict(created_utc=datetime.now(timezone.utc).isoformat(),code_sha256=code_hash,
        inputs_sha256={protocol_path.name:sha(protocol_path),command_path.name:sha(command_path)},
        stage='Development; notebook response/QC summaries already exposed; fixed before first FastRheo ADC access',
        train_sweeps=TRAIN,held_sweeps=HELD,devices=DEVICES,primary_devices=PRIMARY,
        primary_window_ms=[25,100],baseline_ms=[5,20],bin_ms=.1,
        baseline='Same per-record pre-stimulus constant mean for data, full model and diagonal model; no post-stimulus detrending',
        thresholds=dict(baseline_rms_mV=.5,peak_abs_recorded_delta_mV=10,high_voltage_mV=-20,
            baseline_difference_from_sweep16_mV=2,training_condition_max=100,eligible_held_min=3),
        selection='All seven channels must pass; anchor sweep16 must have all seven baseline RMS <=0.5mV; QC failures never move held into training',
        prediction='If eligible train rank7/condition<=100 and >=3 held: time-bin full7x7 OLS vs diagonal own-input OLS, no post-response refit',
        prediction_gate='>=3 held zero-own-current cases across>=2 targets; full all-response RMSE<=1.05*diagonal and zero-own RMSE<=0.8*zero; report absolute noise and held rank',
        measurement='Recorded bridge-compensated voltage, not calibrated intrinsic membrane voltage; -20mV rule is high-voltage exclusion not a complete spike detector',
        original_train_design=matrix_quality([inputs[s] for s in TRAIN]),original_held_design=matrix_quality([inputs[s] for s in HELD]),
        claim_ceiling='BIO_EVIDENCE_L1 descriptive operational eligibility and conditional waveform development; no G,C,E or spatial metric identification')
    if CONTRACT.exists():raise FileExistsError(CONTRACT)
    with CONTRACT.open('x',encoding='utf8') as stream:
        json.dump(specification,stream,ensure_ascii=False,indent=2,allow_nan=False);stream.write('\n')
    contract_hash=sha(CONTRACT)
    cache=BASE/'raw_ranges'/'1552517188.758'
    manifest=json.loads((cache/'manifest.json').read_text())
    initial=sum(b['bytes'] for b in manifest['blocks'].values())
    raw.URL,raw.CACHE,raw.LIMIT=protocol['provenance']['remote']['url'],cache,initial+16*1024*1024
    state={d:{} for d in DEVICES}
    settings_by_sweep={}
    for sweep in range(35):
        for d in DEVICES:state[d].update(settings(adc[sweep,d]['attributes'].get('comment',''),d))
        if sweep in SWEEPS:settings_by_sweep[sweep]={d:dict(v) for d,v in state.items()}
    records=[]
    with raw.CachedRanges() as reader:
        assert reader.remote==protocol['provenance']['remote']
        with h5py.File(reader,'r') as f:
            for sweep in SWEEPS:
                channels,responses=[],[]
                for device in DEVICES:
                    row=adc[sweep,device]
                    assert row['unit']=='V' and row['rate']==RATE and row['samples']==6400
                    node=f[row['path']]
                    voltage=(np.asarray(node['data'][()],float)*row['conversion']+row['offset'])*1000
                    quality,response=channel_quality(voltage)
                    quality.update(device=device,acquisition_path=row['path'],
                        reconstructed_instrument_settings=settings_by_sweep[sweep][device],
                        waveform_mV_0p1ms=voltage.reshape(1280,5).mean(axis=1).tolist())
                    channels.append(quality);responses.append(response)
                if sweep==16:
                    anchor=np.array([c['baseline_mV'] for c in channels])
                    anchor_noise_ok=all(c['baseline_noise_pass'] for c in channels)
                for c,reference in zip(channels,anchor):
                    delta=c['baseline_mV']-reference
                    c.update(baseline_delta_from_anchor_mV=float(delta),same_operating_domain_pass=bool(abs(delta)<=2),
                        quality_pass=bool(c['local_waveform_pass'] and abs(delta)<=2 and anchor_noise_ok))
                records.append(dict(sweep=sweep,split='train' if sweep in TRAIN else 'held',currents_pA=inputs[sweep],
                    channels=channels,response_delta_mV_0p1ms=np.asarray(responses).tolist(),
                    all_seven_quality_pass=all(c['quality_pass'] for c in channels),
                    primary_four_quality_pass=all(c['quality_pass'] for c in channels if c['device'] in PRIMARY)))
                print('RESPONSE_QC',sweep,'all7',records[-1]['all_seven_quality_pass'],
                    'primary4',records[-1]['primary_four_quality_pass'],
                    'max_delta_mV',max(c['response_peak_abs_delta_mV'] for c in channels),
                    'new_bytes',reader.downloaded_this_session,flush=True)
        provenance=dict(remote=reader.remote,initial_cached_bytes=initial,new_download_bytes=reader.downloaded_this_session,blocks=reader.manifest['blocks'])
    prediction=predict_if_eligible(records)
    assert sha(Path(__file__))==code_hash and sha(CONTRACT)==contract_hash
    result=dict(code_sha256=code_hash,contract_sha256=contract_hash,specification=specification,
        raw_reader_sha256=sha(Path(raw.__file__)),metadata_reader_sha256=sha(HERE/'allen_joint_inventory.py'),
        settings_reader_sha256=sha(HERE/'electrical_star_vc_inputs.py'),provenance=provenance,records=records,prediction=prediction,
        summary=dict(all_seven_eligible_sweeps=[r['sweep'] for r in records if r['all_seven_quality_pass']],
            primary_four_eligible_sweeps=[r['sweep'] for r in records if r['primary_four_quality_pass']],
            original_input_rank=matrix_quality(list(inputs.values()))['rank'],
            eligible_input_design=matrix_quality([r['currents_pA'] for r in records if r['all_seven_quality_pass']]),
            new_download_bytes=provenance['new_download_bytes']),
        claim_ceiling=specification['claim_ceiling'])
    with OUTPUT.open('x',encoding='utf8') as stream:
        json.dump(result,stream,ensure_ascii=False,indent=2,allow_nan=False);stream.write('\n')
    print('DONE',json.dumps(result['summary']),'prediction_executed',prediction['executed'],'sha256',sha(OUTPUT),flush=True)


if __name__=='__main__':main()
