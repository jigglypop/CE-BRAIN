"""선정된 별도 실험의 첫20개 IC 기록에서 첫pulse 적합과 기준선을 비교한다."""
import json
from pathlib import Path
import numpy as np
import medium_recording_lookup as medium
from population_reciprocity import ROOT,sha
from superficial_ee_eligibility import save

HERE=Path(__file__).resolve().parent

def main():
    selection=HERE/'mouse_donor_identity_result.json'
    selected=json.loads(selection.read_text(encoding='utf-8'))['selected']
    save('different_donor_first_pulses_contract.json',dict(
        question='What does the fixed producer measurement show in the first20 IC records of the separately selected experiment?',
        selection='All pair responses grouped by recording; keep IC records ordered by DB start time then ID, first20. Within each use earliest presynaptic onset. No amplitude/QC exclusion.',
        endpoint='Stored dec_fit_reconv_amp minus its assigned baseline; mean/median/sign count. Report missing fits and exQC.',
        limits='Separate experiment, different named donor under producer convention; producer waveform parameters use unknown full-record scope. Not blinded discovery or raw reproduction.',
        selected_sha256=sha(selection),prior_method_sha256=sha(HERE/'separate_experiment_first_pulses.py'),code_sha256=sha(Path(__file__))))
    raw=medium.raw;prior=json.loads((HERE/'medium_recording_lookup_result.json').read_text(encoding='utf-8'))
    raw.URL=prior['remote']['url'];raw.CACHE=ROOT/'data/external/allen_synphys_r21/medium_ranges';raw.LIMIT=128*1024*1024
    rows=[]
    with raw.CachedRanges() as reader:
        assert reader.remote==prior['remote'];vfs=medium.ReadVFS(reader);db=medium.apsw.Connection('remote.sqlite',flags=medium.apsw.SQLITE_OPEN_READONLY,vfs='ce_medium_readonly')
        def query(sql,args=()):
            c=db.cursor();it=c.execute(sql,args)
            try:keys=[x[0] for x in c.get_description()]
            except medium.apsw.ExecutionCompleteError:return []
            return [dict(zip(keys,v)) for v in it]
        groups=query('select distinct recording_id from pulse_response where pair_id=?',(selected['pair_id'],))
        candidates=[]
        for g in groups:
            r=query('select * from recording where id=?',(g['recording_id'],))[0]
            assert r['electrode_id']==selected['post_electrode_id']
            qc=query('select * from patch_clamp_recording where recording_id=?',(r['id'],));assert len(qc)==1
            if qc[0]['clamp_mode']=='ic':candidates.append((r,qc[0]))
        candidates.sort(key=lambda x:(x[0]['start_time'],x[0]['id']))
        for rec,qc in candidates[:20]:
            pulses=query('select pr.id,pr.stim_pulse_id,pr.baseline_id,pr.ex_qc_pass,sp.onset_time,sp.recording_id pre_recording_id,sp.n_spikes from pulse_response pr join stim_pulse sp on sp.id=pr.stim_pulse_id where pr.pair_id=? and pr.recording_id=? order by sp.onset_time,pr.id',(selected['pair_id'],rec['id']))
            first=pulses[0];pre=query('select electrode_id from recording where id=?',(first['pre_recording_id'],))[0]
            assert pre['electrode_id']==selected['pre_electrode_id']
            fits=query('select * from pulse_response_fit where pulse_response_id=?',(first['id'],));assert len(fits)<=1
            row=dict(recording=rec,qc=qc,first_pulse=first,fits=fits,difference_uV=None)
            if fits and fits[0]['dec_fit_reconv_amp'] is not None and fits[0]['baseline_dec_fit_reconv_amp'] is not None:
                row['difference_uV']=(fits[0]['dec_fit_reconv_amp']-fits[0]['baseline_dec_fit_reconv_amp'])*1e6
            rows.append(row)
        db.close();vfs.unregister();downloaded=reader.downloaded_this_session
    values=[r['difference_uV'] for r in rows if r['difference_uV'] is not None]
    summary=dict(candidate_ic_records=len(candidates),selected=len(rows),usable=len(values),ex_qc_pass=sum(r['first_pulse']['ex_qc_pass']==1 for r in rows),
        mean_difference_uV=float(np.mean(values)) if values else None,median_difference_uV=float(np.median(values)) if values else None,positive=sum(v>0 for v in values))
    save('different_donor_first_pulses_result.json',dict(contract_sha256=sha(HERE/'different_donor_first_pulses_contract.json'),selection=selected,records=rows,summary=summary,new_bytes=downloaded))
    print(json.dumps(dict(summary=summary,new_bytes=downloaded),indent=2))

if __name__=='__main__':main()
