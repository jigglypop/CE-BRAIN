"""Check source command/timing metadata against actual mixed-clamp waveforms.

Voltage crossings and window means are diagnostics, not a fitted AP detector,
identified PSCs, an independent frequency intervention or a learning model.
"""
import json
import math
from pathlib import Path
import platform

import numpy as np

from vc20hz_source_inputs import HERE, ROOT, sha

INPUT=HERE/'mixed_clamp_raw_inputs_result.json'
INPUT_SHA='311e4ecca0709b306651090ca210d12637d92a32659ed13dc9a9609d018b323b'
PULSES=HERE/'mixed_clamp_pulses_result.json'
PULSES_SHA='f023db5b41d40c4ccbb5bb91c89af926898f38d7fb607c09b8446bb341aa76c7'


def window(values, rate, lo, hi):
    """Half-open sample support; no padding or interpolation."""
    if not np.isfinite([rate,lo,hi]).all() or rate<=0 or hi<=lo:
        raise ValueError('Invalid window')
    a=int(np.ceil(lo*rate-1e-8));b=int(np.ceil(hi*rate-1e-8))
    if a<0 or b>len(values) or b<=a:return None
    return a,b,np.asarray(values[a:b],float)


def measure(source, target, rate, onset, next_onset, stored_time):
    end=min(onset+.008,next_onset)
    raw=window(source,rate,onset,end)
    before=window(target,rate,onset-.002,onset-.0002)
    after=window(target,rate,onset+.002,end)
    result=dict(window_start_s=onset,window_stop_s=end,
        source_window_complete=raw is not None,target_windows_complete=before is not None and after is not None,
        stored_time_finite=stored_time is not None and math.isfinite(stored_time))
    if raw is not None:
        start,stop,values=raw
        peak=int(np.argmax(values))
        result.update(raw_peak_V=float(values[peak]),raw_peak_s=float((start+peak)/rate),
            raw_min_V=float(values.min()),raw_reaches_zero_mV=bool(values.max()>=0.),
            upward_zero_crossings=int(np.count_nonzero((values[:-1]<0.)&(values[1:]>=0.))),
            starts_above_zero=bool(values[0]>=0.))
        if len(values)>1:
            dv=np.diff(values)*rate;at=int(np.argmax(dv))
            result.update(raw_max_dvdt_V_per_s=float(dv[at]),raw_max_dvdt_s=float((start+at+.5)/rate))
        if result['stored_time_finite']:
            result['stored_time_inside_source_window']=bool(onset<=stored_time<end)
            result['raw_max_dvdt_minus_stored_s']=result['raw_max_dvdt_s']-stored_time if len(values)>1 else None
            result['raw_peak_minus_stored_s']=result['raw_peak_s']-stored_time
    if before is not None and after is not None:
        baseline=float(before[2].mean())
        result.update(target_pre_mean_A=baseline,target_post_mean_A=float(after[2].mean()),
            target_post_minus_pre_A=float(after[2].mean()-baseline),
            target_post_min_A=float(after[2].min()),target_post_max_A=float(after[2].max()))
    return result


def match_commands(pulses, command, rate):
    positive=sorted((c for c in command['command_intervals'] if c['delta_min']>0),key=lambda c:c['start_s'])
    ordered=sorted(pulses,key=lambda p:p['onset_time'])
    if len(positive)!=len(ordered):
        return dict(matches=False,db_count=len(ordered),raw_count=len(positive),comparisons=[])
    comparisons=[]
    for p,c in zip(ordered,positive):
        errors=dict(onset_s=c['start_s']-p['onset_time'],duration_s=c['duration_s']-p['duration'],
            delta_min_A=c['delta_min']-p['amplitude'],delta_max_A=c['delta_max']-p['amplitude'])
        matches=(abs(errors['onset_s'])<=2/rate+1e-12 and abs(errors['duration_s'])<=2/rate+1e-12 and
            all(math.isclose(c[k],p['amplitude'],rel_tol=1e-5,abs_tol=1e-14) for k in ('delta_min','delta_max')))
        comparisons.append(dict(pulse_id=p['id'],pulse_number=p['pulse_number'],matches=matches,errors=errors))
    return dict(matches=all(c['matches'] for c in comparisons),db_count=len(ordered),raw_count=len(positive),comparisons=comparisons)


def overlaps(start, stop, intervals):
    return [r for r in intervals if r['start_s']<stop and r['stop_s']>start]


def main():
    output=HERE/'mixed_clamp_waveform_audit_result.json'
    if output.exists():raise FileExistsError('Preserve waveform audit')
    if sha(INPUT)!=INPUT_SHA or sha(PULSES)!=PULSES_SHA:raise ValueError('Frozen input changed')
    inputs=json.loads(INPUT.read_text(encoding='utf-8'));pulse_inventory=json.loads(PULSES.read_text(encoding='utf-8'))
    if sha(ROOT/inputs['arrays']['path'])!=inputs['arrays']['sha256']:raise ValueError('Signal archive changed')
    rows={(r['sweep'],r['device'],r['kind']):r for r in inputs['records']}
    events,schedules=[],[]
    with np.load(ROOT/inputs['arrays']['path'],allow_pickle=False) as arrays:
        for sweep in pulse_inventory['sweeps']:
            number=sweep['sweep'];target_row=rows[number,1,'acquisition']
            target=arrays[target_row['array_key']]
            target_command=rows[number,1,'command']
            for candidate in sweep['candidates']:
                pre=next(r for r in sweep['records'] if r['id']==candidate['source_recording'])
                source_row=rows[number,pre['device_id'],'acquisition'];command=rows[number,pre['device_id'],'command']
                source=arrays[source_row['array_key']]
                pulses=sorted(sweep['source_pulses'][str(pre['id'])],key=lambda p:p['onset_time'])
                schedule=match_commands(pulses,command,source_row['rate'])
                schedules.append(dict(sweep=number,device=pre['device_id'],**schedule))
                responses={r['stim_pulse_id']:r for rr in sweep['target_responses'].values() for r in rr if r['pair_id']==candidate['pair_id']}
                for index,pulse in enumerate(pulses):
                    next_onset=pulses[index+1]['onset_time'] if index+1<len(pulses) else len(source)/source_row['rate']
                    measurement=measure(source,target,source_row['rate'],pulse['onset_time'],next_onset,pulse['first_spike_time'])
                    response=responses.get(pulse['id'])
                    lo,hi=pulse['onset_time']-.002,measurement['window_stop_s']
                    own_overlap=overlaps(lo,hi,target_command['command_intervals'])
                    other=[dict(pulse_id=p['id'],start_s=p['onset_time'],stop_s=p['onset_time']+p['duration'])
                        for rid,items in sweep['source_pulses'].items() if int(rid)!=pre['id'] for p in items]
                    other_overlap=overlaps(lo,hi,other)
                    previous=[p['stop_s'] for p in other if p['stop_s']<=lo]
                    events.append(dict(sweep=number,source_device=pre['device_id'],pair_id=candidate['pair_id'],
                        pulse_id=pulse['id'],pulse_number=pulse['pulse_number'],onset_s=pulse['onset_time'],
                        stored_n_spikes=pulse['n_spikes'],stored_first_spike_s=pulse['first_spike_time'],
                        source_recording_qc=pre['qc_pass'],target_recording_qc=target_row['recording_qc'],
                        response_ex_qc=response['ex_qc_pass'] if response is not None else None,
                        target_command_excursions_overlapping_window=len(own_overlap),
                        other_source_pulses_overlapping_window=[p['pulse_id'] for p in other_overlap],
                        since_other_source_command_end_s=pulse['onset_time']-max(previous) if previous else None,
                        source_command_matches_db=schedule['matches'],**measurement))
    groups=[]
    for pair in sorted({r['pair_id'] for r in events}):
        subset=[r for r in events if r['pair_id']==pair]
        for label,group in [('all',subset),('stored_time_finite',[r for r in subset if r['stored_time_finite']]),
                            ('stored_time_missing',[r for r in subset if not r['stored_time_finite']])]:
            eligible=[r for r in group if r['source_window_complete']]
            groups.append(dict(pair_id=pair,group=label,events=len(group),complete_source_windows=len(eligible),
                raw_reaches_zero_mV=sum(r['raw_reaches_zero_mV'] for r in eligible),
                upward_zero_crossings=sum(r['upward_zero_crossings'] for r in eligible),
                starts_above_zero=sum(r['starts_above_zero'] for r in eligible)))
    result=dict(schema='allen.mixed-clamp.waveform-audit.v1',source_sha256=sha(__file__),
        test_sha256=sha(ROOT/'tests/test_mixed_clamp_waveform_audit.py'),input_sha256=INPUT_SHA,pulse_inventory_sha256=PULSES_SHA,
        signal_archive=inputs['arrays'],python=platform.python_version(),numpy=np.__version__,
        schedules=schedules,events=events,groups=groups,
        method=dict(source_window='onset to min(onset+8ms,next pulse)',target_pre='onset[-2,-0.2)ms',
            target_post='onset[2,min(8,next pulse))ms',threshold='0mV crossing is a diagnostic only',
            time_alignment='DB source onsets checked against actual SI command on shared raw clock'),
        interpretation='No waveform fitting or effect-based exclusions. Stored spike counts/times and raw voltage features '
        'retained separately. Zero crossings do not prove exact AP count; raw target-current differences do not isolate PSCs. '
        'Failed recording/response QC retained; condition/order and measurement state still require separate control.')
    serialized=json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)
    with output.open('x',encoding='utf-8') as stream:stream.write(serialized)
    print(json.dumps(dict(events=len(events),schedules=len(schedules),schedule_matches=sum(s['matches'] for s in schedules),groups=groups)))


if __name__=='__main__':main()
