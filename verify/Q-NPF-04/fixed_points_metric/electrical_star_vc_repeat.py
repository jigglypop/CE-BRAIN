"""Frozen large-command cross-current repeatability, not junction conductance."""
import argparse
import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

import h5py
import numpy as np

from allen_joint_inventory import BASE, OfflineRanges, raw, sha

HERE=Path(__file__).resolve().parent
CONTRACT=HERE/'electrical_star_vc_repeat_contract.json'
OUTPUT=HERE/'electrical_star_vc_repeat_result.json'
DEVICES=[4,1,2,5]
TIME=(np.arange(400)+.5)*.0001-.01
MASK=(TIME>=.0003)&(TIME<.020)&~((TIME>=.0013)&(TIME<.0018))
BLOCKS=[dict(nominal_holding_mV=-70,train=[0,1],held=[2,3,4]),
        dict(nominal_holding_mV=-55,train=[5,6],held=[7,8,9])]


def save(path,value):
    with path.open('x',encoding='utf8') as stream:
        json.dump(value,stream,ensure_ascii=False,indent=2,allow_nan=False);stream.write('\n')


def observed_transfer(admittance,series,reference=0.):
    """Static calibrated-port counterexample; consistent arbitrary units."""
    y=np.asarray(admittance,float)
    return np.linalg.inv(np.linalg.inv(y)+np.diag(series)+reference*np.ones_like(y))


def center_epoch(values):
    """50 kHz, -10..30 ms; fixed -10..-2 ms local baseline, 0.1 ms bins."""
    values=np.asarray(values,float)
    if values.shape[-1]!=2000: raise ValueError('Expected 2000 samples')
    return (values-values[...,:400].mean(axis=-1,keepdims=True)).reshape(*values.shape[:-1],400,5).mean(axis=-1)


def summarize_block(records):
    voltage=np.asarray([row['aligned_current_pA'] for row in records])
    sham=np.asarray([row['sham_current_pA'] for row in records])
    train=voltage[:2].mean(axis=0)
    symmetric=(train+train.transpose(1,0,2))/2
    sham_template=sham[:2].mean(axis=0)
    cross=~np.eye(4,dtype=bool)
    direct=np.zeros((4,4),bool);direct[0,1:]=True;direct[1:,0]=True
    rms=lambda x:float(np.sqrt(np.mean(x*x)))
    denominator=rms(sham_template[cross][:,MASK])
    train_snr=rms(train[cross][:,MASK])/denominator if denominator>0 else None
    scores=[]
    for index,row in enumerate(records):
        score=dict(sweep=row['sweep'],partition='train' if index<2 else 'held',models={})
        for name,predicted in [('repeat',train),('symmetric',symmetric),('shifted_sham',sham_template)]:
            model={}
            for label,mask in [('cross',cross),('direct',direct)]:
                obs=voltage[index][mask][:,MASK]
                error=predicted[mask][:,MASK]-obs
                zero=rms(obs); rmse=rms(error)
                model[label]=dict(zero_rmse_pA=zero,rmse_pA=rmse,ratio_to_zero=rmse/zero if zero>0 else None)
            score['models'][name]=model
        scores.append(score)
    held=scores[2:]
    gate=train_snr is not None and train_snr>=3 and all(
        row['models']['repeat'][key]['ratio_to_zero'] is not None and row['models']['repeat'][key]['ratio_to_zero']<=.8
        for row in held for key in ['cross','direct'])
    return dict(training_template_pA=train.tolist(),symmetric_template_pA=symmetric.tolist(),
                training_sham_template_pA=sham_template.tolist(),training_cross_signal_to_sham=train_snr,
                scores=scores,repeatability_necessary_gate=gate)


def summarize(records):
    by_sweep={row['sweep']:row for row in records}
    blocks=[]
    for block in BLOCKS:
        selected=[by_sweep[s] for s in block['train']+block['held']]
        blocks.append(dict(**block,**summarize_block(selected)))
    return dict(blocks=blocks,repeatability_necessary_gate=all(b['repeatability_necessary_gate'] for b in blocks))


def holding_states(inputs):
    states={device:{} for device in inputs['devices']}
    resolved=[]
    for sweep in inputs['sweeps']:
        values={}
        for row in sweep['devices']:
            device=row['device'];states[device].update(row['incremental_instrument_settings'])
            assert states[device]['V-Clamp Holding Enable']=='On'
            assert states[device]['OperatingModeString']=='V-Clamp'
            values[device]=float(states[device]['V-Clamp Holding Level'].split()[0])
        expected=-70 if sweep['sweep']<5 else -55
        assert all(abs(value-expected)<.05 for value in values.values())
        resolved.append(dict(sweep=sweep['sweep'],nominal_holding_mV=expected,recorded_holding_mV=values))
    return resolved


def freeze():
    inputs=json.loads((HERE/'electrical_star_vc_inputs_result.json').read_text(encoding='utf8'))
    assert all(s['after_50ms']['rank']==7 for s in inputs['sweeps'])
    c=dict(created_utc=datetime.now(timezone.utc).isoformat(),code_sha256=sha(Path(__file__)),
        sources_sha256={name:sha(HERE/name) for name in ['electrical_star_vc_inputs_result.json',
            'electrical_star_protocol_result.json','allen_joint_inventory.py']},raw_reader_sha256=sha(Path(raw.__file__)),
        execution=dict(python=platform.python_version(),numpy=np.__version__,h5py=h5py.__version__,executable=sys.executable),
        objective='Fixed neurons -> independently commanded cross-current repeatability -> calibration before conductance or metric',
        selection='Same metadata-selected electrical star; electrical annotations may use the same experiment',
        prior_exposure='VC commands and metadata only; no VC acquisition data decoded. IC sweeps 10-12 already examined.',
        blocks=BLOCKS,holding_states=holding_states(inputs),devices=DEVICES,
        command='70 mV, 1.50 or 1.52 ms; 12 pulses per source (8 at 20 Hz, then 4 at 20 Hz after a gap)',
        command_scope='Large voltage excursions: no small-signal, linear amplitude, or static junction-conductance claim',
        observation=dict(epoch_s=[-.01,.03],baseline_s=[-.01,-.002],bin_s=.0001,
            primary_s=[.0003,.020],exclude_s=[.0013,.0018],sham_onset_shift_s=-.025,
            within_sweep='Average all 12 command-aligned pulse epochs separately for each ordered source-target pair'),
        model='Separate fixed mean waveforms for -70 and -55 mV holding: first two sweeps train, next three held in each block; no held fit or pulse selection',
        comparisons=['zero cross-response','reciprocal symmetric training template','training template aligned 25 ms before each pulse'],
        gate=dict(training_cross_signal_to_sham_min=3.,max_held_rmse_ratio_to_zero=.8,
            required='Each of three held sweeps per holding block, all 12 cross directions AND six annotated direct directions; both blocks required'),
        limitations=['Shifted sham may contain a tail of the previous pulse; it is not a randomized sham intervention',
            'Transition exclusion does not establish removal of all capacitive or reference-electrode cross-talk',
            'Command voltage is not independently measured membrane voltage',
            'Identical-command reproducibility does not identify input-amplitude linearity, anatomy, or a Riemannian metric',
            'One experiment, six held sweeps across two holding states; time bins and 12 pulses are not independent animals',
            'Both source and target holding change between blocks; block differences do not isolate junction voltage dependence'],
        remote=inputs['provenance']['remote'],claim_ceiling='BIO_EVIDENCE_L1 pilot command-locked repeatability only')
    save(CONTRACT,c);print('FROZEN',sha(CONTRACT),flush=True)


def run(fetch):
    if OUTPUT.exists():raise FileExistsError(OUTPUT)
    c=json.loads(CONTRACT.read_text(encoding='utf8'))
    assert sha(Path(__file__))==c['code_sha256']
    for name,digest in c['sources_sha256'].items():assert sha(HERE/name)==digest
    assert sha(Path(raw.__file__))==c['raw_reader_sha256']
    inputs=json.loads((HERE/'electrical_star_vc_inputs_result.json').read_text(encoding='utf8'))
    assert holding_states(inputs)==[{**row,'recorded_holding_mV':{int(k):v for k,v in row['recorded_holding_mV'].items()}} for row in c['holding_states']]
    protocol=json.loads((HERE/'electrical_star_protocol_result.json').read_text(encoding='utf8'))
    adc={(r['sweep'],r['device']):r for r in protocol['records'] if r['kind']=='acquisition'}
    cache=BASE/'raw_ranges'/protocol['selection']['ext_id']
    manifest=json.loads((cache/'manifest.json').read_text())
    initial=sum(b['bytes'] for b in manifest['blocks'].values())
    raw.URL,raw.CACHE,raw.LIMIT=c['remote']['url'],cache,initial+64*1024*1024
    records=[]
    with (raw.CachedRanges() if fetch else OfflineRanges(cache)) as reader:
        assert reader.remote==c['remote']
        with h5py.File(reader,'r') as f:
            for sweep in [s for block in c['blocks'] for s in block['train']+block['held']]:
                descriptors={d['device']:d for d in inputs['sweeps'][sweep]['devices']}
                current=np.zeros((4,4,400));sham=np.zeros_like(current)
                baseline=np.zeros((4,4));baseline_sd=np.zeros_like(baseline)
                pulse_variation=np.zeros_like(baseline);peak=np.zeros_like(baseline)
                for source_index,source in enumerate(DEVICES):
                    pulses=[p for p in descriptors[source]['command_segments'] if p['command_mV']>1]
                    assert len(pulses)==12
                    assert all(abs(p['command_mV']-70)<.001 and .00149<=p['duration_s']<=.00153 for p in pulses)
                    for pulse in pulses:
                        for other,description in descriptors.items():
                            if other==source:continue
                            for segment in description['command_segments']:
                                if segment['start_s']<pulse['start_s']+.03 and segment['end_s']>pulse['start_s']-.035:
                                    assert abs(segment['command_mV']-description['baseline_command_mV'])<.005
                    for target_index,target in enumerate(DEVICES):
                        a=adc[sweep,target]
                        assert a['unit']=='A' and a['rate']==50000 and a['start']==adc[sweep,source]['start']
                        actual,shifted,baselines,peaks=[],[],[],[]
                        for pulse in pulses:
                            onset=round(pulse['start_s']*50000)
                            start,end=onset-1750,onset+1500
                            values=(np.asarray(f[a['path']+'/data'][start:end],float)*a['conversion']+a['offset'])*1e12
                            assert len(values)==3250 and np.isfinite(values).all()
                            real=values[1250:3250];control=values[:2000]
                            actual.append(center_epoch(real));shifted.append(center_epoch(control))
                            baselines.append(float(real[:400].mean()));peaks.append(float(np.max(np.abs(real))))
                        actual,shifted=np.asarray(actual),np.asarray(shifted)
                        current[target_index,source_index]=actual.mean(axis=0)
                        sham[target_index,source_index]=shifted.mean(axis=0)
                        baseline[target_index,source_index]=np.mean(baselines)
                        baseline_sd[target_index,source_index]=np.std(baselines)
                        pulse_variation[target_index,source_index]=np.sqrt(np.mean(np.var(actual[:,MASK],axis=0)))
                        peak[target_index,source_index]=max(peaks)
                records.append(dict(sweep=sweep,aligned_current_pA=current.tolist(),sham_current_pA=sham.tolist(),
                    mean_baseline_pA=baseline.tolist(),sd_pulse_baselines_pA=baseline_sd.tolist(),
                    within_record_pulse_variation_rms_pA=pulse_variation.tolist(),max_absolute_raw_current_pA=peak.tolist()))
                print('EXTRACTED_VC',sweep,'new_bytes',getattr(reader,'downloaded_this_session',0),flush=True)
        provenance=dict(remote=reader.remote,initial_cached_bytes=initial,new_download_bytes=getattr(reader,'downloaded_this_session',0),
            blocks=reader.manifest['blocks'] if fetch else reader.used)
    result=dict(code_sha256=sha(Path(__file__)),contract_sha256=sha(CONTRACT),provenance=provenance,
        devices=DEVICES,time_s=TIME.tolist(),primary_bin_mask=MASK.tolist(),records=records,**summarize(records),
        metric_verdict='NOT_IDENTIFIED; large commands and uncalibrated electrode/membrane/reference prevent conductance identification',
        claim_ceiling=c['claim_ceiling'],limitations=c['limitations'])
    save(OUTPUT,result)
    print('DONE',json.dumps(dict(gate=result['repeatability_necessary_gate'],blocks=[dict(holding=b['nominal_holding_mV'],
        snr=b['training_cross_signal_to_sham'],held=[dict(sweep=s['sweep'],cross=s['models']['repeat']['cross']['ratio_to_zero'],
        direct=s['models']['repeat']['direct']['ratio_to_zero']) for s in b['scores'][2:]]) for b in result['blocks']],
        new_bytes=provenance['new_download_bytes'],sha256=sha(OUTPUT))),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--freeze',action='store_true');parser.add_argument('--fetch-missing',action='store_true')
    args=parser.parse_args();freeze() if args.freeze else run(args.fetch_missing)
