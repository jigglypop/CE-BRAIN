"""36 생리 기록에 연결된 test-pulse와 전극·시각을 조회한다."""
import json
from datetime import datetime
from pathlib import Path
import medium_recording_lookup as medium
from population_reciprocity import ROOT,sha
from superficial_ee_eligibility import save

HERE=Path(__file__).resolve().parent
SOURCE=HERE/'medium_recording_lookup_result.json'
def main():
    save('intrinsic_test_pulse_binding_contract.json',{
        'question':'Are nearest-test-pulse measurements linked to the same electrode and how far are their recording timestamps from intrinsic recordings?',
        'scope':'All36 previously matched intrinsic records; no access-resistance threshold or outcome selection.',
        'checks':'One row per test pulse; electrode identity; recording identity; signed difference of DB timestamps, not mixed NWB/notebook clocks.',
        'limits':'DB nearest designation does not establish cell stability; units follow schema, exact event timing needs sampling metadata.',
        'source_sha256':sha(SOURCE),'code_sha256':sha(Path(__file__)),'vfs_sha256':sha(Path(medium.__file__))})
    prior=json.loads(SOURCE.read_text(encoding='utf-8'))
    raw=medium.raw;raw.URL=prior['remote']['url'];raw.CACHE=ROOT/'data/external/allen_synphys_r21/medium_ranges';raw.LIMIT=128*1024*1024
    rows=[]
    with raw.CachedRanges() as reader:
        assert reader.remote==prior['remote']
        vfs=medium.ReadVFS(reader);db=medium.apsw.Connection('remote.sqlite',flags=medium.apsw.SQLITE_OPEN_READONLY,vfs='ce_medium_readonly')
        def query(sql,args):
            cursor=db.cursor();it=cursor.execute(sql,args);keys=[x[0] for x in cursor.get_description()]
            return [dict(zip(keys,r)) for r in it]
        for r in prior['records']:
            tid=r['qc'][0]['nearest_test_pulse_id'];assert tid is not None
            found=query('select * from test_pulse where id=?',(tid,));assert len(found)==1;tp=found[0]
            assert tp['electrode_id']==r['recording']['electrode_id']
            linked=query('select * from recording where id=?',(tp['recording_id'],));assert len(linked)==1
            rec=linked[0];assert rec['electrode_id']==tp['electrode_id']
            delta=(datetime.fromisoformat(rec['start_time'])-datetime.fromisoformat(r['recording']['start_time'])).total_seconds()
            rows.append({'sweep':r['sweep'],'device':r['device'],'intrinsic_recording_id':r['recording']['id'],
                         'test_pulse':tp,'test_recording':rec,'same_recording':tp['recording_id']==r['recording']['id'],
                         'recording_start_difference_s':delta})
        db.close();vfs.unregister();new_bytes=reader.downloaded_this_session
    summary={}
    for hs in (2,4,5):
        rr=[r for r in rows if r['device']==hs]
        fields={}
        for key in ('access_resistance','access_resistance_lowpass','input_resistance'):
            vals=[r['test_pulse'][key] for r in rr if r['test_pulse'][key] is not None]
            fields[key]={'present':len(vals),'range_ohm':[min(vals),max(vals)] if vals else None}
        summary[str(hs)]={'records':len(rr),'same_recording':sum(r['same_recording'] for r in rr),
                          'recording_start_difference_s_range':[min(r['recording_start_difference_s'] for r in rr),max(r['recording_start_difference_s'] for r in rr)],'measurements':fields}
    out={'contract_sha256':sha(HERE/'intrinsic_test_pulse_binding_contract.json'),'new_bytes':new_bytes,'records':rows,'summary':summary,
         'verification':'PASS unique test-pulse rows and electrode links; same-DB time differences only'}
    save('intrinsic_test_pulse_binding_result.json',out)
    print(json.dumps({k:v for k,v in out.items() if k!='records'},indent=2))
if __name__=='__main__':main()
