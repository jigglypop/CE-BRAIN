"""20시행 양성 연결의 제작자 pulse별 적합값을 원시 자극에 대응시킨다."""
import json
from pathlib import Path
import numpy as np
import medium_recording_lookup as medium
from population_reciprocity import ROOT,sha
from superficial_ee_eligibility import save

HERE=Path(__file__).resolve().parent

def main():
    names=['connection_recording_state_result.json','recovery_train_responses_result.json']
    save('producer_pulse_fits_contract.json',dict(question='Are producer fit rows available and pulse-matched for the same20 positive-pair train records?',
        scope='Pair104272; all responses on target-device4 in sweeps37..56; retain QC failures and missing fits; no sign/outcome exclusion.',
        checks='Presynaptic recording matches device5; actual onset nearest within one100kHz sample; same240 unique sweep/pulse keys.',
        limits='Stored source-conditioned fits are not independent connection evidence; exact historical software version unverified; not a reproduction of fitting.',
        inputs={n:sha(HERE/n) for n in names},code_sha256=sha(Path(__file__)),
        sources={n:sha(HERE/'source_snapshots'/n) for n in ['aisynphys__pulse_response_strength.py','aisynphys__pipeline__multipatch__pulse_response.py']}))
    state,train=[json.loads((HERE/n).read_text(encoding='utf-8')) for n in names]
    records={(r['sweep'],r['device']):r['recording'] for r in state['records']}
    events={(r['sweep'],r['pulse']):r for r in train['records']}
    raw=medium.raw;prior=json.loads((HERE/'medium_recording_lookup_result.json').read_text(encoding='utf-8'))
    raw.URL=prior['remote']['url'];raw.CACHE=ROOT/'data/external/allen_synphys_r21/medium_ranges';raw.LIMIT=128*1024*1024
    rows=[]
    with raw.CachedRanges() as reader:
        assert reader.remote==prior['remote'];vfs=medium.ReadVFS(reader)
        db=medium.apsw.Connection('remote.sqlite',flags=medium.apsw.SQLITE_OPEN_READONLY,vfs='ce_medium_readonly')
        def query(sql,args=()):
            c=db.cursor();it=c.execute(sql,args)
            try:keys=[d[0] for d in c.get_description()]
            except medium.apsw.ExecutionCompleteError:return []
            return [dict(zip(keys,v)) for v in it]
        syn=query('select * from synapse where pair_id=?',(104272,));assert len(syn)==1
        for sw in range(37,57):
            prs=query('select id,recording_id,stim_pulse_id,pair_id,baseline_id,data_start_time,ex_qc_pass,in_qc_pass from pulse_response where recording_id=? and pair_id=?',(records[sw,4]['id'],104272))
            for pr in prs:
                sp=query('select id,recording_id,pulse_number,onset_time,duration,n_spikes,first_spike_time,qc_pass,previous_pulse_dt from stim_pulse where id=?',(pr['stim_pulse_id'],));assert len(sp)==1;sp=sp[0]
                assert sp['recording_id']==records[sw,5]['id']
                pulse=min(range(1,13),key=lambda p:abs(events[sw,p]['command_start_s']-sp['onset_time']))
                error=sp['onset_time']-events[sw,pulse]['command_start_s'];assert abs(error)<=1e-5+1e-9
                fits=query('select * from pulse_response_fit where pulse_response_id=?',(pr['id'],));assert len(fits)<=1
                rows.append(dict(sweep=sw,pulse=pulse,onset_error_s=error,pulse_response=pr,stim_pulse=sp,fits=fits))
            print('queried',sw,len(prs),flush=True)
        db.close();vfs.unregister();downloaded=reader.downloaded_this_session
    assert len(rows)==240 and {(r['sweep'],r['pulse']) for r in rows}==set(events)
    summary=[]
    for p in range(1,13):
        rr=[r for r in rows if r['pulse']==p]
        vals={}
        for key in ['fit_amp','baseline_fit_amp','dec_fit_reconv_amp','baseline_dec_fit_reconv_amp']:
            x=[r['fits'][0][key]*1e6 for r in rr if r['fits'] and r['fits'][0][key] is not None]
            vals[key]=dict(n=len(x),mean_uV=float(np.mean(x)) if x else None,median_uV=float(np.median(x)) if x else None)
        summary.append(dict(pulse=p,ex_qc_pass=sum(r['pulse_response']['ex_qc_pass']==1 for r in rr),fits=sum(bool(r['fits']) for r in rr),values=vals))
    save('producer_pulse_fits_result.json',dict(contract_sha256=sha(HERE/'producer_pulse_fits_contract.json'),synapse=syn[0],records=rows,summary=summary,new_bytes=downloaded))
    print(json.dumps(dict(summary=summary,new_bytes=downloaded),indent=2))

if __name__=='__main__':main()
