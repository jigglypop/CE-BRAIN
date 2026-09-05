"""LP 기록의 notebook 메타데이터와 기존 recording QC 조건을 확인한다."""
import json
from pathlib import Path
import h5py
import numpy as np
import raw_metadata as raw
from reference_spike_audit import reference
from population_reciprocity import sha
from superficial_ee_eligibility import save

HERE=Path(__file__).resolve().parent
SOURCE=HERE/'same_cell_long_pulse_result.json'
requested=['Clamp Mode','I-Clamp Holding Enable','I-Clamp Holding Level','Delay onset auto','Delay onset user','Delay termination',
           'Bridge Bal Enable','Bridge Bal Value','Series Resistance','TP Peak Resistance','TP Steady State Resistance','USER_F Rheo E Sweep QC']
save('long_pulse_recording_qc_ordered_contract.json',{
    'repair':'Preserve failed original. Read increasing HDF5 column indices then reorder in memory; no criteria changed.',
    'question':'Do the 24 LP traces satisfy the previously used recording-level quality subset and what amplifier metadata are available?',
    'metadata':'EntrySourceType0; within-sweep last finite field; global column8 overrides; no across-sweep carry; missing fields explicit.',
    'criteria':'Finite full trace; zeros<=floor(n/10); IC mode1; holding +/-800pA; notebook-baseline float_mode [-85,-45]mV; baseline SD<=5mV.',
    'limits':'Subset reconstruction, not full producer QC; resistance units/physical meaning and cell stability not inferred; user QC field is metadata only.',
    'source_sha256':sha(SOURCE),'code_sha256':sha(Path(__file__)),'reader_sha256':sha(Path(raw.__file__)),
    'baseline_source_sha256':sha(raw.ROOT/'data/external/analysis_tools/neuroanalysis_source/neuroanalysis/baseline.py')})
reference()
from neuroanalysis.baseline import float_mode
raw.LIMIT=128*1024*1024
with raw.CachedRanges() as reader:
    with h5py.File(reader,'r') as f:
        nb=f['general/labnotebook/ITC1600_Dev_0']
        keys=[x.decode() if isinstance(x,bytes) else str(x) for x in nb['numericalKeys'][0]]
        assert all(k in keys for k in requested)
        columns=['SweepNum','EntrySourceType']+requested
        indices=sorted(keys.index(k) for k in columns)
        selected=nb['numericalValues'][:,indices,:]
        values=selected[:,[indices.index(keys.index(k)) for k in columns],:]
        merged={}
        for row in values:
            if not np.isfinite(row[0,0]) or row[1,0]!=0:continue
            sw=int(row[0,0])
            if sw not in range(82,90):continue
            if sw not in merged:merged[sw]=row.copy()
            else:
                valid=np.isfinite(row);merged[sw][valid]=row[valid]
    new_bytes=reader.downloaded_this_session
rows=[]
for r in json.loads(SOURCE.read_text(encoding='utf-8'))['records']:
    sw=r['sweep'];hs=int(r['electrode'].split('_')[-1]);values=merged[sw].copy()
    glob=np.isfinite(values[:,8]);values[glob]=values[glob,8:9]
    fields={k:float(values[columns.index(k),hs]) if np.isfinite(values[columns.index(k),hs]) else None for k in requested}
    path=raw.ROOT/r['array_path'];assert sha(path)==r['array_sha256']
    with np.load(path,allow_pickle=False) as a:v=a['voltage']
    fs=r['rate'];duration=len(v)/fs;regions=[]
    if all(fields[k] is not None for k in ('Delay onset auto','Delay onset user','Delay termination')):
        start=fields['Delay onset auto']/1000;delay=fields['Delay onset user']/1000;tail=fields['Delay termination']/1000
        if delay>0:regions.append([start,start+delay])
        if tail>0:regions.append([duration-tail,duration])
    assert all(0<=a<b<=duration for a,b in regions)
    base=np.concatenate([v[round(a*fs):round(b*fs)] for a,b in regions]) if regions else np.array([])
    base=base[np.isfinite(base)];potential=float(float_mode(base)) if len(base) else None;sd=float(base.std()) if len(base) else None
    failures=[]
    if fields['Clamp Mode']!=1:failures.append('clamp')
    if not np.isfinite(v).all():failures.append('nonfinite')
    if np.sum(v==0)>len(v)//10:failures.append('zeros')
    h=fields['I-Clamp Holding Level']
    if h is None or not -800<=h<=800:failures.append('holding')
    if potential is None or not -.085<=potential<=-.045:failures.append('baseline_voltage')
    if sd is None or sd>.005:failures.append('baseline_noise')
    rows.append({'sweep':sw,'electrode':r['electrode'],'fields':fields,'baseline_regions_s':regions,
                 'baseline_mV':None if potential is None else potential*1000,'baseline_sd_uV':None if sd is None else sd*1e6,
                 'failures':failures,'subset_pass':not failures})
out={'contract_sha256':sha(HERE/'long_pulse_recording_qc_ordered_contract.json'),'new_bytes':new_bytes,'records':rows,
     'passed':sum(r['subset_pass'] for r in rows),'total':len(rows),
     'missing_fields':{k:sum(r['fields'][k] is None for r in rows) for k in requested},
     'claim':'Recording-level subset only; no full QC, resistance interpretation, cell-state stability or mechanistic identification.'}
save('long_pulse_recording_qc_ordered_result.json',out)
print(json.dumps({k:v for k,v in out.items() if k!='records'},indent=2))
for r in rows:print(r['sweep'],r['electrode'],r['fields'],r['failures'])
