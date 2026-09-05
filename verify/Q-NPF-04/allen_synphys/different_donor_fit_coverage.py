"""선택한 다른donor pair의 전체pulse 적합·기준선·발화 누락을 조사한다."""
import json
from pathlib import Path
import medium_recording_lookup as medium
from population_reciprocity import ROOT,sha
from superficial_ee_eligibility import save

HERE=Path(__file__).resolve().parent

def main():
    source=HERE/'different_donor_first_pulses_result.json'
    previous=json.loads(source.read_text(encoding='utf-8'));pair=previous['selection']['pair_id']
    save('different_donor_fit_coverage_contract.json',dict(
        question='Does missing fit coverage follow absent assigned baselines or spike/QC eligibility across the full selected pair?',
        scope='All pulse_response rows for pair116053, both clamp modes retained; no amplitude-based selection.',
        fields='Recording ID/mode, pulse number/onset, n_spikes, first_spike_time, ex/inQC, assigned baseline ID, fit row presence.',
        checks='Unique response IDs; baseline and stimulus foreign keys, first-response records agree with prior five-record query.',
        limits='Absent baseline explains exclusion by inspected inner join, but not the upstream cause of failed baseline assignment or historical job completion.',
        source_sha256=sha(source),pipeline_sha256=sha(HERE/'source_snapshots/aisynphys__pipeline__multipatch__pulse_response.py'),code_sha256=sha(Path(__file__))))
    raw=medium.raw;prior=json.loads((HERE/'medium_recording_lookup_result.json').read_text(encoding='utf-8'))
    raw.URL=prior['remote']['url'];raw.CACHE=ROOT/'data/external/allen_synphys_r21/medium_ranges';raw.LIMIT=128*1024*1024
    rows=[];recordings={}
    with raw.CachedRanges() as reader:
        assert reader.remote==prior['remote'];vfs=medium.ReadVFS(reader);db=medium.apsw.Connection('remote.sqlite',flags=medium.apsw.SQLITE_OPEN_READONLY,vfs='ce_medium_readonly')
        def query(sql,args=()):
            c=db.cursor();it=c.execute(sql,args)
            try:keys=[x[0] for x in c.get_description()]
            except medium.apsw.ExecutionCompleteError:return []
            return [dict(zip(keys,v)) for v in it]
        prs=query('select id,recording_id,stim_pulse_id,baseline_id,ex_qc_pass,in_qc_pass from pulse_response where pair_id=?',(pair,))
        for pr in prs:
            rid=pr['recording_id']
            if rid not in recordings:
                rec=query('select id,start_time,stim_name,electrode_id from recording where id=?',(rid,))[0]
                qc=query('select clamp_mode,qc_pass from patch_clamp_recording where recording_id=?',(rid,))[0]
                recordings[rid]={**rec,**qc}
            sp=query('select id,recording_id,pulse_number,onset_time,n_spikes,first_spike_time from stim_pulse where id=?',(pr['stim_pulse_id'],));assert len(sp)==1
            bl=query('select id,recording_id,ex_qc_pass,in_qc_pass from baseline where id=?',(pr['baseline_id'],)) if pr['baseline_id'] is not None else []
            assert pr['baseline_id'] is None or (len(bl)==1 and bl[0]['recording_id']==rid)
            fit=query('select id from pulse_response_fit where pulse_response_id=?',(pr['id'],));assert len(fit)<=1
            rows.append(dict(response=pr,stimulus=sp[0],baseline=bl,fit_ids=[f['id'] for f in fit],clamp_mode=recordings[rid]['clamp_mode']))
        db.close();vfs.unregister();downloaded=reader.downloaded_this_session
    assert len({r['response']['id'] for r in rows})==len(rows)
    for old in previous['records']:
        now=next(r for r in rows if r['response']['id']==old['first_pulse']['id'])
        assert now['response']['baseline_id']==old['first_pulse']['baseline_id'] and len(now['fit_ids'])==len(old['fits'])
    summary=[]
    for rid,rec in sorted(recordings.items()):
        rr=[r for r in rows if r['response']['recording_id']==rid]
        summary.append(dict(recording=rec,all_pulses=len(rr),fits=sum(bool(r['fit_ids']) for r in rr),baselines=sum(bool(r['baseline']) for r in rr),
            ex_qc_pass=sum(r['response']['ex_qc_pass']==1 for r in rr),with_spike_time=sum(r['stimulus']['first_spike_time'] is not None for r in rr),
            no_fit_with_baseline=sum(not r['fit_ids'] and bool(r['baseline']) for r in rr)))
    save('different_donor_fit_coverage_result.json',dict(contract_sha256=sha(HERE/'different_donor_fit_coverage_contract.json'),records=rows,summary=summary,new_bytes=downloaded))
    print(json.dumps(dict(total=len(rows),summary=summary,new_bytes=downloaded),indent=2))

if __name__=='__main__':main()
