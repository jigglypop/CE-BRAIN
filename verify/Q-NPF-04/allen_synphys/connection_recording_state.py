"""동일 실험의 연결 자극37..56시행을 DB 시계·QC·test-pulse에 결박한다."""
import json
from pathlib import Path
from statistics import median
import medium_recording_lookup as medium
from population_reciprocity import ROOT,sha
from superficial_ee_eligibility import save

HERE=Path(__file__).resolve().parent

def main():
    source=HERE/'medium_recording_lookup_result.json'
    prior=json.loads(source.read_text(encoding='utf-8'))
    save('connection_recording_state_contract.json',dict(
        question='What recording state and DB timestamps accompany the20 existing connection-stimulation sweeps?',
        selection='All sweeps37..56, devices2/4/5 in experiment3337; no outcome or resistance exclusions.',
        checks='Exact60 sweep/device keys, original raw inventory stimulus names; unique QC and nearest-test-pulse rows; report same-recording links.',
        endpoint='Descriptive time range, holding/baseline/access/input resistance ranges and medians by device.',
        limits='No cross-clock arithmetic, causal drift correction, cell stability certification or mechanistic fit.',
        source_sha256=sha(source),inventory_sha256=sha(HERE/'same_cell_intrinsic_inventory_result.json'),
        code_sha256=sha(Path(__file__)),vfs_sha256=sha(Path(medium.__file__))))
    raw=medium.raw;raw.URL=prior['remote']['url'];raw.CACHE=ROOT/'data/external/allen_synphys_r21/medium_ranges';raw.LIMIT=128*1024*1024
    inventory=json.loads((HERE/'same_cell_intrinsic_inventory_result.json').read_text(encoding='utf-8'))['records']
    expected={(r['sweep'],int(r['electrode'].split('_')[-1])):r for r in inventory if 37<=r['sweep']<=56}
    assert len(expected)==60
    rows=[]
    with raw.CachedRanges() as reader:
        assert reader.remote==prior['remote']
        vfs=medium.ReadVFS(reader);db=medium.apsw.Connection('remote.sqlite',flags=medium.apsw.SQLITE_OPEN_READONLY,vfs='ce_medium_readonly')
        def query(sql,args=()):
            cursor=db.cursor();values=cursor.execute(sql,args)
            try:keys=[x[0] for x in cursor.get_description()]
            except medium.apsw.ExecutionCompleteError:return []
            return [dict(zip(keys,v)) for v in values]
        electrodes={r['id']:r['device_id'] for r in query('select id,device_id from electrode where experiment_id=?',(3337,))}
        for s in query('select id,ext_id from sync_rec where experiment_id=?',(3337,)):
            sweep=int(s['ext_id'])
            if not 37<=sweep<=56:continue
            for r in query('select * from recording where sync_rec_id=?',(s['id'],)):
                device=electrodes[r['electrode_id']]
                if device not in (2,4,5):continue
                assert r['stim_name']==expected[sweep,device]['stimulus']
                qc=query('select * from patch_clamp_recording where recording_id=?',(r['id'],));assert len(qc)==1
                assert qc[0]['clamp_mode']=='ic'
                tp=query('select * from test_pulse where id=?',(qc[0]['nearest_test_pulse_id'],));assert len(tp)==1
                assert tp[0]['electrode_id']==r['electrode_id']
                rows.append(dict(sweep=sweep,device=device,recording=r,qc=qc[0],test_pulse=tp[0],same_recording=tp[0]['recording_id']==r['id']))
        db.close();vfs.unregister();downloaded=reader.downloaded_this_session
    assert len(rows)==60 and {(r['sweep'],r['device']) for r in rows}==set(expected)
    summary={}
    for d in (2,4,5):
        rr=[r for r in rows if r['device']==d];measurements={}
        for origin,key,factor in [('qc','baseline_current',1e12),('qc','baseline_potential',1e3),('test_pulse','access_resistance',1e-6),('test_pulse','input_resistance',1e-6)]:
            values=[r[origin][key]*factor for r in rr if r[origin][key] is not None]
            measurements[key]=dict(n=len(values),min=min(values),median=median(values),max=max(values)) if values else dict(n=0)
        times=sorted(r['recording']['start_time'] for r in rr)
        summary[str(d)]=dict(records=len(rr),same_recording=sum(r['same_recording'] for r in rr),qc_pass=sum(r['qc']['qc_pass']==1 for r in rr),
            first_start=times[0],last_start=times[-1],measurements=measurements)
    save('connection_recording_state_result.json',dict(contract_sha256=sha(HERE/'connection_recording_state_contract.json'),records=rows,summary=summary,new_bytes=downloaded,
        units='baseline_current pA; baseline_potential mV; resistance MOhm in summary; original SI units in records'))
    print(json.dumps(dict(summary=summary,new_bytes=downloaded),indent=2))

if __name__=='__main__':main()
