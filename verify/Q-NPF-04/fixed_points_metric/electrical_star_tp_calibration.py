"""Time-matched notebook TP measurements and explicitly defined inserted-TP indices."""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import h5py
import numpy as np

from allen_joint_inventory import BASE, OfflineRanges, raw, sha

HERE=Path(__file__).resolve().parent
OUTPUT=HERE/'electrical_star_tp_calibration_result.json'
DEVICES=[0,1,2,4,5,6,7]
IGOR_OFFSET=2082844800


def global_or_channel(fields,key,device):
    values=fields.get(key,[None]*9)
    return values[8] if values[8] is not None else values[device]


def tp_pairs(records):
    rows={row['row']:row['fields'] for row in records}
    pairs=[]
    for index,fields in rows.items():
        if 'TP Peak Resistance' not in fields:continue
        if fields.get('EntrySourceType',[None])[0]!=1:raise ValueError('Unexpected TP source')
        second=rows.get(index+1,{})
        if second.get('EntrySourceType',[None])[0]!=1 or 'TP Pulse Duration' not in second:
            raise ValueError('Missing typed TP settings partner')
        delta=second['TimeStampSinceIgorEpochUTC'][0]-fields['TimeStampSinceIgorEpochUTC'][0]
        if not 0<=delta<=.01:raise ValueError('TP row timestamps do not match')
        pairs.append(dict(measurement_row=index,settings_row=index+1,row_time_difference_s=delta,
            igor_utc=fields['TimeStampSinceIgorEpochUTC'][0],local_igor=fields['TimeStamp'][0],
            fields=fields,settings=second))
    return pairs


def step_current(time_ms,conductance_uS,capacitance_nF,series_MOhm,reference_MOhm,command_mV):
    """Exact passive linear step, including common electrode; current in nA."""
    time=np.asarray(time_ms,float)
    g=np.asarray(conductance_uS,float);c=np.asarray(capacitance_nF,float)
    n=len(c);e=np.diag(series_MOhm)+reference_MOhm*np.ones((n,n))
    a=np.linalg.inv(e);cinv=np.diag(1/np.sqrt(c))
    values,vectors=np.linalg.eigh(cinv@(g+a)@cinv)
    if values.min()<=0:raise ValueError('Passive relaxation must be stable')
    forcing=vectors.T@cinv@a@np.asarray(command_mV,float)
    modes=(-np.expm1(-time[:,None]*values)/values)*forcing
    voltage=modes@vectors.T@cinv
    return (np.asarray(command_mV,float)-voltage)@a.T


def measure_inserted(values,onset,end,amplitude_mV,rate=50000):
    """Explicit new estimator, not a claimed reproduction of 2019 MIES code."""
    def mean(lo,hi):return float(np.mean(values[round(lo*rate):round(hi*rate)]))
    baseline=mean(onset-.0016,onset-.0001)
    early=mean(end-.0031,end-.0016)
    late=mean(end-.0016,end-.0001)
    onset_index=round(onset*rate)
    lo,hi=onset_index+int(np.ceil(.00002*rate)),onset_index+int(np.ceil(.00027*rate))
    peak_index=lo+int(np.argmin(values[lo:hi]))
    peak=float(values[peak_index-1:peak_index+2].mean())
    dp,ds=peak-baseline,late-baseline
    signed_peak=1000*amplitude_mV/dp if dp else None
    signed_steady=1000*amplitude_mV/ds if ds else None
    return dict(baseline_pA=baseline,peak_delta_pA=dp,late_delta_pA=ds,
        peak_time_after_onset_ms=(peak_index/rate-onset)*1000,
        defined_peak_resistance_MOhm=signed_peak,defined_late_resistance_MOhm=signed_steady,
        relative_late_change=abs(late-early)/abs(ds) if ds else None,
        definition='Signed delta ratios; peak = three samples around minimum in onset+0.02..0.27 ms; baseline/late use 1.5 ms ending 0.1 ms before transitions')


def main(fetch):
    if OUTPUT.exists():raise FileExistsError(OUTPUT)
    code_sha=sha(Path(__file__))
    notebook=json.loads((HERE/'electrical_star_notebook_values_result.json').read_text(encoding='utf8'))
    protocol=json.loads((HERE/'electrical_star_protocol_result.json').read_text(encoding='utf8'))
    inputs=json.loads((HERE/'electrical_star_vc_inputs_result.json').read_text(encoding='utf8'))
    tps=tp_pairs(notebook['numerical_records'])
    session=datetime.fromisoformat(notebook['root_times']['session_start_time'][0].replace('Z','+00:00')).timestamp()
    adc={(r['sweep'],r['device']):r for r in protocol['records'] if r['kind']=='acquisition'}
    precise={}
    for row in notebook['textual_records']:
        fields=row['fields']
        if 'High precision sweep start' not in fields:continue
        sweep=int(fields['SweepNum'][0]);value=fields['High precision sweep start'][8]
        if value:precise[sweep]=datetime.fromisoformat(value.replace('Z','+00:00')).timestamp()
    matched=[]
    for sweep in range(10):
        utc=session+adc[sweep,4]['start']
        assert abs(utc-precise[sweep])<1e-5
        nearest=min(tps,key=lambda row:abs(row['igor_utc']-IGOR_OFFSET-utc))
        age=nearest['igor_utc']-IGOR_OFFSET-utc
        cells=[]
        for device in DEVICES:
            fields=nearest['fields']
            cells.append(dict(device=device,mode=global_or_channel(fields,'Clamp Mode',device),
                active=global_or_channel(fields,'Headstage Active',device),
                peak_resistance_MOhm=global_or_channel(fields,'TP Peak Resistance',device),
                steady_resistance_MOhm=global_or_channel(fields,'TP Steady State Resistance',device),
                baseline_pA=global_or_channel(fields,'TP Baseline pA',device),
                fast_compensation_F=global_or_channel(fields,'Fast compensation capacitance',device),
                slow_compensation_F=global_or_channel(fields,'Slow compensation capacitance',device)))
        matched.append(dict(sweep=sweep,nwb_utc=datetime.fromtimestamp(utc,timezone.utc).isoformat(),
            precise_time_difference_s=utc-precise[sweep],nearest_tp_measurement_row=nearest['measurement_row'],
            nearest_tp_settings_row=nearest['settings_row'],tp_time_minus_sweep_start_s=age,
            timestamp_utc_minus_local_s=nearest['igor_utc']-nearest['local_igor'],cells=cells,
            stimulus={key:global_or_channel(nearest['settings'],key,0) for key in ['TP Amplitude VC','TP Pulse Duration','TP Baseline Fraction']},
            holding_at_tp='Not stored in the paired TP rows; same-mode temporal proximity does not independently prove exact holding equality'))
    cache=BASE/'raw_ranges'/protocol['selection']['ext_id']
    manifest=json.loads((cache/'manifest.json').read_text());initial=sum(b['bytes'] for b in manifest['blocks'].values())
    raw.URL,raw.CACHE,raw.LIMIT=protocol['remote']['url'],cache,initial+16*1024*1024
    traces=[]
    with (raw.CachedRanges() if fetch else OfflineRanges(cache)) as reader:
        assert reader.remote==protocol['remote']
        with h5py.File(reader,'r') as f:
            numeric=np.asarray(f[notebook['group_path']+'/numericalValues'])
            inf=np.argwhere(np.isinf(numeric))
            infinity_audit=dict(count=int(len(inf)),indices=inf.tolist(),
                signs=[int(np.sign(numeric[tuple(index)])) for index in inf],
                note='Earlier sparse extraction encoded nonfinite entries as null; this audit preserves infinity positions separately')
            for match in matched:
                sweep=match['sweep'];descriptors={d['device']:d for d in inputs['sweeps'][sweep]['devices']}
                for cell in match['cells']:
                    device=cell['device'];a=adc[sweep,device]
                    assert a['unit']=='A' and a['rate']==50000
                    pulses=[p for p in descriptors[device]['command_segments'] if p['command_mV']<-1]
                    assert len(pulses)==1
                    pulse=pulses[0]
                    values=(np.asarray(f[a['path']+'/data'][:1250],float)*a['conversion']+a['offset'])*1e12
                    assert len(values)==1250 and np.isfinite(values).all()
                    observation=measure_inserted(values,pulse['start_s'],pulse['end_s'],pulse['command_mV'])
                    comparison={}
                    for label,defined,recorded in [('peak','defined_peak_resistance_MOhm','peak_resistance_MOhm'),
                                                   ('late','defined_late_resistance_MOhm','steady_resistance_MOhm')]:
                        comparison[label+'_ratio_to_nearby_notebook']=observation[defined]/cell[recorded] if observation[defined] is not None and cell[recorded] else None
                    cell.update(inserted=observation,comparison=comparison)
                    traces.append(dict(sweep=sweep,device=device,current_pA=values.tolist()))
                print('INSERTED_TP',sweep,flush=True)
        provenance=dict(remote=reader.remote,initial_cached_bytes=initial,new_download_bytes=getattr(reader,'downloaded_this_session',0),
            blocks=reader.manifest['blocks'] if fetch else reader.used)
    time=np.linspace(0,25,501);n=7;u=np.full(n,-10.);g=.01*np.eye(n);cap=np.full(n,.1)
    first=step_current(time,g,cap,np.full(n,14.),0.,u)
    second=step_current(time,g,cap,np.full(n,7.),1.,u)
    edge=np.zeros(n);edge[0]=1;edge[1]=-1
    third=step_current(time,g+.1*np.outer(edge,edge),cap,np.full(n,14.),0.,u)
    assert sha(Path(__file__))==code_sha
    mode_match=all(cell['mode']==0 and cell['active']==1 for match in matched for cell in match['cells'])
    result=dict(created_utc=datetime.now(timezone.utc).isoformat(),code_sha256=code_sha,
        source_sha256={name:sha(HERE/name) for name in ['electrical_star_notebook_values_result.json',
            'electrical_star_protocol_result.json','electrical_star_vc_inputs_result.json','allen_joint_inventory.py']},
        raw_reader_sha256=sha(Path(raw.__file__)),provenance=provenance,
        stage='Post hoc measurement/calibration assessment after prior VC response analysis; inserted-TP windows defined before their first acquisition read',
        tp_pair_count=len(tps),all_matched_tp_channels_active_vc=mode_match,matched_sweeps=matched,traces=traces,infinity_audit=infinity_audit,
        counterexamples=dict(units='ms, nF, MOhm, uS, mV, nA',
            common_command_mV=-10.,neurons=7,capacitance_nF=.1,leak_uS=.01,
            series_reference_cases=[[14.,0.],[7.,1.]],
            max_reference_confounded_waveform_difference_nA=float(np.max(np.abs(first-second))),
            added_gap_uS=.1,max_invisible_gap_waveform_difference_nA=float(np.max(np.abs(first-third)))),
        conclusion=('Time-matched active VC TP measurements exist; agreement is a measurement consistency check, not unique Rs, membrane, junction or metric identification'
                    if mode_match else 'Nearest TP records include inactive or non-VC channels; do not adopt as VC calibration'),
        claim_ceiling='BIO_EVIDENCE_L1 recorded test-pulse quantities; intrinsic spatial metric remains unestablished')
    with OUTPUT.open('x',encoding='utf8') as stream:
        json.dump(result,stream,ensure_ascii=False,indent=2,allow_nan=False);stream.write('\n')
    print('DONE',json.dumps(dict(tp_pairs=len(tps),infinities=len(inf),new_bytes=provenance['new_download_bytes'],sha256=sha(OUTPUT))),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--fetch-missing',action='store_true')
    main(parser.parse_args().fetch_missing)
