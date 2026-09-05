"""고정된 다음 개체 후보의 전후 조건·QC·반복 수를 반응 진폭 없이 조사한다."""
import argparse
import json
from collections import defaultdict
from pathlib import Path
import medium_recording_lookup as m
from population_reciprocity import ROOT,sha
from superficial_ee_eligibility import save

HERE=Path(__file__).resolve().parent
SOURCE=HERE/'next_donor_batch_result.json'
NAME='next_donor_recording_inventory'


def summarize(records):
    groups=defaultdict(list)
    for row in records:
        groups[json.dumps(row['condition'],sort_keys=True)].append(row)
    return [dict(condition=json.loads(key),repeats=len(rr),post_recordings=[r['post']['id'] for r in rr],
        sweeps=[r['post']['sweep'] for r in rr],both_qc=sum(r['pre']['qc_pass']==r['post']['qc_pass']==1 for r in rr),
        all_aligned=sum(all(p['first_spike_time'] is not None for p in r['pulses']) for r in rr),
        all_single_spike=sum(all(p['n_spikes']==1 for p in r['pulses']) for r in rr),
        all_ex_qc=sum(all(p['ex_qc_pass']==1 for p in r['pulses']) for r in rr)) for key,rr in groups.items()]


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verify',action='store_true');args=parser.parse_args()
    if args.verify:
        result=json.loads((HERE/f'{NAME}_result.json').read_text(encoding='utf-8'))
        contract=json.loads((HERE/f'{NAME}_contract.json').read_text(encoding='utf-8'))
        assert contract['code_sha256']==sha(Path(__file__)) and contract['selection_sha256']==sha(SOURCE)
        for pair in result['pairs']:
            assert summarize(pair['records'])==pair['groups']
            assert sum(len(r['pulses']) for r in pair['records'])==pair['pulse_response_count']
        print('NEXT_DONOR_INVENTORY_REPRODUCTION_PASS');return
    selection=json.loads(SOURCE.read_text(encoding='utf-8'))['selected']
    save(f'{NAME}_contract.json',dict(
        scope='固定候補全pairのpulse_response全件。反応波形・fit振幅を読まない。',
        question='각 후보의 유지 조건을 포함한 동일 자극 반복·QC·발화 정렬·동시기 test pulse 상태가 있는가?',
        selection='next_donor_batch의 고정 목록 전부. 후보 부족을 더 느슨한 조건으로 채우지 않음.',
        condition='pair ID, 전후 모드·유지값(VC baseline_potential, IC baseline_current), 모든 pulse의 진폭·길이·상대 onset 간격. 시간만1us 반올림, 유지값은DB실수정확값.',
        qc='QC 탈락도 분모에 남김. 전후QC·pulseexQC·n_spikes·spikealignment 각각 집계. 각 test pulse의 같은recording/electrode 여부도 보존.',
        state='baseline noise/current/potential, nearest test pulse의 access/input resistance. 상태가 같다고 가정하지 않음.',
        limits='중복 pulse/전후 sync불일치는중단. 알려진 양성 표지조건부 모집단. 반복수는검정력증거아님. 결과크기기반교체없음. L0자료적격성.',
        selection_sha256=sha(SOURCE),code_sha256=sha(Path(__file__))))
    remote=json.loads((HERE/'medium_recording_lookup_result.json').read_text(encoding='utf-8'))['remote']
    raw=m.raw;raw.URL=remote['url'];raw.CACHE=ROOT/'data/external/allen_synphys_r21/medium_ranges';raw.LIMIT=128*1024*1024
    pairs=[]
    with raw.CachedRanges() as reader:
        assert reader.remote==remote
        vfs=m.ReadVFS(reader);db=m.apsw.Connection('remote.sqlite',flags=m.apsw.SQLITE_OPEN_READONLY,vfs='ce_medium_readonly')
        def query(sql,args):
            cursor=db.cursor();it=cursor.execute(sql,args)
            try:keys=[d[0] for d in cursor.get_description()]
            except m.apsw.ExecutionCompleteError:return []
            return [dict(zip(keys,r)) for r in it]
        cache={}
        def recording(rid):
            if rid in cache:return cache[rid]
            rows=query('select r.id,r.sync_rec_id,r.electrode_id,r.start_time,r.stim_name,r.stim_meta,'
                's.experiment_id,s.ext_id sweep,e.device_id,p.clamp_mode,p.qc_pass,p.baseline_potential,'
                'p.baseline_current,p.baseline_noise_stdev,p.nearest_test_pulse_id,p.meta qc_meta '
                'from recording r join sync_rec s on s.id=r.sync_rec_id join electrode e on e.id=r.electrode_id '
                'join patch_clamp_recording p on p.recording_id=r.id where r.id=?',(rid,))
            assert len(rows)==1;r=rows[0]
            tp=query('select id,electrode_id,recording_id,access_resistance,input_resistance from test_pulse where id=?',(r['nearest_test_pulse_id'],))
            r['test_pulse']=tp
            r['test_pulse_same_recording_electrode']=len(tp)==1 and tp[0]['recording_id']==rid and tp[0]['electrode_id']==r['electrode_id']
            cache[rid]=r;return r
        try:
            for candidate in selection:
                rows=query('select pr.id response_id,pr.recording_id post_recording,pr.ex_qc_pass,pr.in_qc_pass,'
                    'sp.id stimulus_id,sp.recording_id pre_recording,sp.pulse_number,sp.onset_time,sp.amplitude,sp.duration,'
                    'sp.n_spikes,sp.first_spike_time from pulse_response pr join stim_pulse sp on sp.id=pr.stim_pulse_id '
                    'where pr.pair_id=? order by pr.recording_id,sp.pulse_number',(candidate['pair_id'],))
                assert len({r['response_id'] for r in rows})==len(rows)
                by_record=defaultdict(list)
                for r in rows:by_record[r['post_recording']].append(r)
                records=[]
                for rid,pulses in by_record.items():
                    assert len({p['pre_recording'] for p in pulses})==1 and len({p['pulse_number'] for p in pulses})==len(pulses)
                    pre=recording(pulses[0]['pre_recording']);post=recording(rid)
                    assert pre['experiment_id']==post['experiment_id']==candidate['experiment_id']
                    assert pre['sync_rec_id']==post['sync_rec_id']
                    assert pre['electrode_id']==candidate['pre_electrode_id'] and post['electrode_id']==candidate['post_electrode_id']
                    condition=dict(pair_id=candidate['pair_id'],amplitudes=[p['amplitude'] for p in pulses],
                        duration_us=[round(p['duration']*1e6) for p in pulses],
                        intervals_us=[round((b['onset_time']-a['onset_time'])*1e6) for a,b in zip(pulses,pulses[1:])])
                    for role,r in [('pre',pre),('post',post)]:
                        mode=r['clamp_mode'];condition[f'{role}_mode']=mode
                        condition[f'{role}_holding_unit']='V' if mode=='vc' else 'A'
                        condition[f'{role}_holding_value']=r['baseline_potential'] if mode=='vc' else r['baseline_current']
                    records.append(dict(pre=pre,post=post,pulses=pulses,condition=condition))
                pairs.append(dict(selection=candidate,pulse_response_count=len(rows),records=records,groups=summarize(records)))
                print('PAIR_INVENTORY',candidate['pair_id'],len(records),'records',len(rows),'pulses',flush=True)
        finally:
            db.close();vfs.unregister()
        new_bytes=reader.downloaded_this_session
    result=dict(contract_sha256=sha(HERE/f'{NAME}_contract.json'),remote=remote,pairs=pairs,new_bytes=new_bytes)
    save(f'{NAME}_result.json',result)
    print(json.dumps(dict(new_bytes=new_bytes,groups=[p['groups'] for p in pairs]),indent=2))


if __name__=='__main__':main()
