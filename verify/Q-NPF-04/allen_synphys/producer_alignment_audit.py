"""제작자240발화 시각·추출 시작과 원시 분석을 비교하고 기준선 위치를 보존한다."""
import json
from pathlib import Path
import medium_recording_lookup as medium
from population_reciprocity import ROOT,sha
from superficial_ee_eligibility import save

HERE=Path(__file__).resolve().parent

def main():
    fits_path=HERE/'producer_pulse_fits_result.json';train_path=HERE/'recovery_train_responses_result.json'
    save('producer_alignment_audit_contract.json',dict(
        question='Do producer spike times and extraction starts agree with raw pulse-aligned events, and are source arrays present in medium?',
        scope='All240 previously bound responses; no outcome exclusions.',
        checks='Max-slope DB time versus actual onset plus local detector time; extraction start versus actual onset minus10ms; baseline recording identity.',
        limits='Inferred stop uses inspected code50ms cap and next-pulse truncation, not a stored array length. Missing medium blobs do not imply missing raw recordings.',
        sources={p.name:sha(p) for p in [fits_path,train_path,HERE/'qc_sources/dataset_pipeline.py',HERE/'qc_sources/multipatch_data.py']},code_sha256=sha(Path(__file__))))
    fits=json.loads(fits_path.read_text(encoding='utf-8'));train=json.loads(train_path.read_text(encoding='utf-8'))
    events={(r['sweep'],r['pulse']):r for r in train['records']}
    prior=json.loads((HERE/'medium_recording_lookup_result.json').read_text(encoding='utf-8'))
    raw=medium.raw;raw.URL=prior['remote']['url'];raw.CACHE=ROOT/'data/external/allen_synphys_r21/medium_ranges';raw.LIMIT=128*1024*1024
    rows=[]
    with raw.CachedRanges() as reader:
        assert reader.remote==prior['remote'];vfs=medium.ReadVFS(reader)
        db=medium.apsw.Connection('remote.sqlite',flags=medium.apsw.SQLITE_OPEN_READONLY,vfs='ce_medium_readonly')
        for r in fits['records']:
            sw,p=r['sweep'],r['pulse'];e=events[sw,p];pr=r['pulse_response'];sp=r['stim_pulse']
            bl=list(db.execute('select id,recording_id,data_start_time,length(data),ex_qc_pass,in_qc_pass from baseline where id=?',(pr['baseline_id'],)))
            assert len(bl)==1 and bl[0][1]==pr['recording_id']
            b=dict(zip(['id','recording_id','start_s','blob_bytes','ex_qc_pass','in_qc_pass'],bl[0]))
            length=list(db.execute('select length(data) from pulse_response where id=?',(pr['id'],)))[0][0]
            delta=sp['first_spike_time']-(e['command_start_s']+e['spikes'][0]['max_slope_time'])
            start_delta=pr['data_start_time']-(e['command_start_s']-.01)
            inferred_stop=min(pr['data_start_time']+.05,events[sw,p+1]['command_start_s']) if p<12 else pr['data_start_time']+.05
            rows.append(dict(sweep=sw,pulse=p,spike_difference_s=delta,start_difference_s=start_delta,
                response_blob_bytes=length,baseline=b,inferred_response_duration_s=inferred_stop-pr['data_start_time']))
        db.close();vfs.unregister();downloaded=reader.downloaded_this_session
    assert len(rows)==240
    summary=dict(n=len(rows),max_abs_spike_difference_s=max(abs(r['spike_difference_s']) for r in rows),
        max_abs_start_difference_s=max(abs(r['start_difference_s']) for r in rows),
        response_blobs_present=sum(r['response_blob_bytes'] is not None for r in rows),baseline_blobs_present=sum(r['baseline']['blob_bytes'] is not None for r in rows),
        baseline_start_range_s=[min(r['baseline']['start_s'] for r in rows),max(r['baseline']['start_s'] for r in rows)],
        inferred_duration_range_s=[min(r['inferred_response_duration_s'] for r in rows),max(r['inferred_response_duration_s'] for r in rows)])
    save('producer_alignment_audit_result.json',dict(contract_sha256=sha(HERE/'producer_alignment_audit_contract.json'),records=rows,summary=summary,new_bytes=downloaded))
    print(json.dumps(dict(summary=summary,new_bytes=downloaded),indent=2))

if __name__=='__main__':main()
