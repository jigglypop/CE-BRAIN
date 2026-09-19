"""Join mixed-clamp raw clocks to recording/TP state and instrument settings."""
import argparse
import hashlib
import json
from pathlib import Path
import platform

import h5py
import numpy as np

import mixed_clamp_inventory as inv
from mixed_clamp_raw_inputs import BASE as RAW_BASE,BASE_SHA as RAW_BASE_SHA
from vc20hz_source_inputs import HERE, ROOT, LayeredRanges, sha
from vc20hz_measurement_state import FIELDS,indexed_query,split_join,stimulus_items
from vc20hz_compensation import NOTE_FIELDS,numeric_settings,plain

INPUT=HERE/'mixed_clamp_raw_inputs_result.json'
INPUT_SHA='311e4ecca0709b306651090ca210d12637d92a32659ed13dc9a9609d018b323b'
PULSE=HERE/'mixed_clamp_pulses_result.json'
PULSE_SHA='f023db5b41d40c4ccbb5bb91c89af926898f38d7fb607c09b8446bb341aa76c7'
DATA=ROOT/'data/external/allen_synphys_r21'
DB_OVERLAY=DATA/'mixed_clamp_state_medium_ranges/v1'
RAW_OVERLAY=DATA/'mixed_clamp_state_raw_ranges/v1'
RAW_PRIOR=DATA/'mixed_clamp_raw_ranges/v1'
RAW_PRIOR_SHA='c23f5c7a8925b76772511bfd3892adc125508c3393890449e1fac470f3df133c'
DB_PRIORS=((inv.PRIOR,inv.PRIOR_SHA),(inv.OVERLAY,'37e856069f55083c5489f705405bd7f5aa9d012391a27328e250dc003cc3abbf'),
    (DATA/'mixed_clamp_pulse_ranges/v1','7eab24d974d8de3d7f07e625f4dfe132991ade42c2eeec3e158db7f6ffdea473'))
SETTINGS=NOTE_FIELDS+('Clamp Mode','I-Clamp Holding Enable','I-Clamp Holding Level','Bridge Bal Enable','Bridge Bal Value',
    'TP Baseline Vm','TP Baseline pA','TP Peak Resistance','TP Steady State Resistance','TP Insert Checkbox')
DEPENDENCIES={
    'mixed_clamp_inventory.py':'31c37d3afdfa49e55c76c301e798eab843ae63763d52969cc28a3403b94f4870',
    'mixed_clamp_raw_inputs.py':'82997c409b5ba9507bf68eba5638f9c265153e74d0fd655fc12e6bb029cef279',
    'vc20hz_source_inputs.py':'2a10fbf34a3c15b0f33765baf6b335249ebb06647d47cda6429b4d6b123227cb',
    'vc20hz_measurement_state.py':'055db380bf1760661d96c95aa9ea479f1bba254952aa4d4dc4bf9cbf88810444',
    'vc20hz_compensation.py':'9cd450e30ee3a10e8751c2a530553e56d545cf15e08cf88361e2226f0e556023',
    'medium_recording_lookup.py':'0d2ee2f4a52cc21bbcf940b8c5642ffcb66f458d72aaf78bc3d4b69a85b6edf9',
    'raw_metadata.py':'5aa32fce7a19372183cf304ecf70bcd1d168dc723ffcffbc74f0711d83db50ae',
}
JOIN=('SELECT '+','.join(f'{a}.{k} AS {a}_{k}' for a,fields in FIELDS.items() for k in fields)+
    ' FROM recording r LEFT JOIN patch_clamp_recording p INDEXED BY ix_patch_clamp_recording_recording_id ON p.recording_id=r.id'
    ' LEFT JOIN test_pulse t ON t.id=p.nearest_test_pulse_id WHERE r.id=?')


class PriorRanges(LayeredRanges):
    def __init__(self,base,overlay,base_sha,priors,allow_download):
        super().__init__(base,overlay,allow_download,base_sha,4*1024*1024)
        self.parents=[];self.used_parents={}
        for path,digest in priors:
            if sha(path/'manifest.json')!=digest:raise ValueError('Frozen parent changed')
            manifest=json.loads((path/'manifest.json').read_text(encoding='utf-8'))
            if any(manifest[k]!=self.manifest[k] for k in ('remote','block_size','base_manifest_sha256')):
                raise ValueError('Parent version mismatch')
            self.parents.append((path,digest,manifest));self.used_parents[path.relative_to(ROOT).as_posix()]={}

    def block(self,start):
        key=str(start)
        if start not in self.memo and key not in self.base_manifest['blocks'] and key not in self.manifest['blocks']:
            for path,digest,manifest in self.parents:
                entry=manifest['blocks'].get(key)
                if entry is None:continue
                value=(path/f'{start:012d}.bin').read_bytes()
                if len(value)!=entry['bytes'] or hashlib.sha256(value).hexdigest()!=entry['sha256']:
                    raise ValueError('Corrupt frozen parent block')
                self.memo[start]=value;self.used_parents[path.relative_to(ROOT).as_posix()][key]=entry
                return value
        return super().block(start)

    def provenance(self):
        for path,digest,manifest in self.parents:
            if sha(path/'manifest.json')!=digest:raise ValueError('Parent changed during read')
        return dict(remote=self.remote,base_manifest_sha256=self.base_sha,used_base=self.used_base,
            parents=[dict(path=path.relative_to(ROOT).as_posix(),sha256=digest) for path,digest,_ in self.parents],
            used_parents=self.used_parents,used_overlay=self.used_overlay,downloaded_this_session=self.downloaded,
            overlay_manifest=self.manifest_path.relative_to(ROOT).as_posix(),
            overlay_manifest_sha256=sha(self.manifest_path) if self.manifest_path.exists() else None,
            overlay_bytes=sum(r['bytes'] for r in self.manifest['blocks'].values()))


def diagnose(recording,patch,test,command):
    items=list(stimulus_items(recording['stim_meta']))
    unit='V' if patch['clamp_mode']=='vc' else 'A'
    offsets=[x['args']['amplitude'] for x in items if x.get('type')=='Offset' and x.get('args',{}).get('units')==unit]
    holding=offsets[0] if len(offsets)==1 else None
    tp=[x['args'] for x in items if x.get('type')=='SquarePulse' and x.get('args',{}).get('description')=='test pulse']
    negative=[x for x in command['command_intervals'] if x['delta_max']<0]
    a,b=test['start_index'],test['stop_index']
    same=(test['id'] is not None and test['recording_id']==recording['id'] and test['electrode_id']==recording['electrode_id'])
    covered=bool(same and a is not None and b is not None and 0<=a<b<=command['samples'] and
        len(negative)==1 and a<=negative[0]['start_index']<negative[0]['stop_index']<=b)
    timing=bool(len(tp)==1 and len(negative)==1 and abs(tp[0]['start_time']-negative[0]['start_s'])<=2/command['rate'] and
        abs(tp[0]['duration']-negative[0]['duration_s'])<=2/command['rate'] and
        np.isclose(tp[0]['amplitude'],negative[0]['delta_min'],rtol=1e-5,atol=1e-14 if unit=='A' else 1e-9))
    terms=(patch['baseline_potential'],test['access_resistance_lowpass'],test['baseline_current'])
    estimate=terms[0]-terms[1]*terms[2] if patch['clamp_mode']=='vc' and all(v is not None and np.isfinite(v) for v in terms) else None
    stored=patch['access_adj_baseline_potential']
    return dict(holding_offset_SI=holding,holding_offset_unit=unit,holding_offset_count=len(offsets),
        embedded_tp_confirmed=bool(covered and timing),tp_same_recording_electrode=bool(same),
        tp_raw_indices_covered=covered,tp_stimulus_matches=timing,
        baseline_ir_drop_estimate_V=estimate,baseline_ir_drop_formula_residual_V=estimate-stored if estimate is not None and stored is not None else None,
        membrane_voltage='VC baseline estimate only; no independent target Vm measurement')


def prior_excursion_gap(onset,intervals):
    previous=[x['stop_s'] for x in intervals if x['stop_s']<=onset]
    return onset-max(previous) if previous else None


def classified_settings(keys,values,sweep,device,requested=SETTINGS):
    """Retain unclassified entries; use explicitly typed acquisition rows only."""
    candidate=np.flatnonzero(values[:,keys.index('SweepNum'),0]==sweep)
    types=values[candidate,keys.index('EntrySourceType'),0]
    finite=np.isfinite(types);known=candidate[finite]
    acquisition=candidate[finite&(types==0)]
    if not len(acquisition):raise ValueError('No explicit acquisition rows')
    result=numeric_settings(keys,values[known],sweep,device,requested=requested)
    for item in result.values():
        item['raw_row_indices']=[int(known[i]) for i in item['raw_row_indices']]
    selection=dict(acquisition_row_indices=acquisition.tolist(),
        unclassified_row_indices=candidate[~finite].tolist(),
        other_classified_rows=[dict(row=int(i),source_type=float(t)) for i,t in zip(candidate[finite],types[finite]) if t!=0])
    return result,selection


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--allow-download',action='store_true');args=parser.parse_args()
    output=HERE/'mixed_clamp_measurement_state_result.json'
    if output.exists():raise FileExistsError('Preserve measurement result')
    if sha(INPUT)!=INPUT_SHA or sha(PULSE)!=PULSE_SHA:raise ValueError('Frozen input changed')
    for name,digest in DEPENDENCIES.items():
        if sha(HERE/name)!=digest:raise ValueError('Frozen dependency changed: '+name)
    inputs=json.loads(INPUT.read_text(encoding='utf-8'));pulses=json.loads(PULSE.read_text(encoding='utf-8'))
    raw={(r['sweep'],r['device'],r['kind']):r for r in inputs['records']}
    plans,rows=[],[]
    with PriorRanges(inv.BASE,DB_OVERLAY,inv.BASE_SHA,DB_PRIORS,args.allow_download) as reader:
        vfs=inv.ReadVFS(reader);db=None
        try:
            db=inv.apsw.Connection('remote.sqlite',flags=inv.apsw.SQLITE_OPEN_READONLY,vfs='ce_medium_readonly')
            db.execute('PRAGMA query_only=ON');db.execute('PRAGMA temp_store=MEMORY')
            for sweep in pulses['sweeps']:
                for initial in sweep['records']:
                    result=indexed_query(db,JOIN,(initial['id'],),plans)
                    if len(result)!=1:raise ValueError('Recording join not unique')
                    state=split_join(result[0]);r,p,t=state['r'],state['p'],state['t']
                    if r['sync_rec_id']!=sweep['sync_rec_id'] or r['electrode_id']!=initial['electrode_id'] or p['clamp_mode']!=initial['clamp_mode']:
                        raise ValueError('Recording identity/mode mismatch')
                    r['stim_meta']=json.loads(r['stim_meta'])
                    command=raw[sweep['sweep'],initial['device_id'],'command']
                    rows.append(dict(sweep=sweep['sweep'],device=initial['device_id'],recording=r,patch=p,test_pulse=t,
                        raw_start=command['start'],raw_rate=command['rate'],diagnosis=diagnose(r,p,t,command)))
        finally:
            if db is not None:db.close()
            vfs.unregister()
        db_provenance=reader.provenance()
    with PriorRanges(RAW_BASE,RAW_OVERLAY,RAW_BASE_SHA,((RAW_PRIOR,RAW_PRIOR_SHA),),args.allow_download) as reader:
        with h5py.File(reader,'r') as nwb:
            notebook=nwb['general/labnotebook/ITC1600_Dev_0']
            all_keys=plain(notebook['numericalKeys'][0])
            selected=sorted({all_keys.index(k) for k in SETTINGS+('SweepNum','EntrySourceType','TimeStamp') if k in all_keys})
            keys=[all_keys[i] for i in selected];values=np.asarray(notebook['numericalValues'][:,selected,:])
            for row in rows:
                row['instrument_settings'],row['instrument_entry_selection']=classified_settings(keys,values,row['sweep'],row['device'])
        raw_provenance=reader.provenance()
    command_history=[]
    for sweep in pulses['sweeps']:
        intervals=raw[sweep['sweep'],1,'command']['command_intervals']
        positive=[x for x in intervals if x['delta_min']>0]
        for items in sweep['source_pulses'].values():
            for pulse in items:
                command_history.append(dict(sweep=sweep['sweep'],pulse_id=pulse['id'],
                    since_target_command_end_s=prior_excursion_gap(pulse['onset_time'],intervals),
                    since_target_positive_command_end_s=prior_excursion_gap(pulse['onset_time'],positive)))
    result=dict(schema='allen.mixed-clamp.measurement-state.v1',source_sha256=sha(__file__),
        test_sha256=sha(ROOT/'tests/test_mixed_clamp_measurement_state.py'),input_sha256=INPUT_SHA,pulse_inventory_sha256=PULSE_SHA,
        records=rows,command_history=command_history,query_plans=plans,db_provenance=db_provenance,raw_provenance=raw_provenance,
        dependency_sha256=DEPENDENCIES,python=platform.python_version(),numpy=np.__version__,h5py=h5py.__version__,apsw=inv.apsw.apswversion(),
        instrument_units='Native labnotebook units, retained without treating compensation settings as measured membrane C/R.',
        interpretation='Raw common clock, released QC/TP identity and instrument settings only. '
        'Nearest own-command time is within-sweep observed history; prior unobserved history is not assumed empty. '
        'Baseline IR estimate is not instantaneous target membrane voltage; no PSC/plasticity/metric identified.')
    serialized=json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)
    with output.open('x',encoding='utf-8') as stream:stream.write(serialized)
    print(json.dumps(dict(records=len(rows),events=len(command_history),db_new_bytes=db_provenance['downloaded_this_session'],raw_new_bytes=raw_provenance['downloaded_this_session'])))


if __name__=='__main__':main()
