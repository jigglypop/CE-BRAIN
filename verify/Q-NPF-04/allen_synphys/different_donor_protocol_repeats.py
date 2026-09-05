"""같은 연결 전체 기록의 실제 자극 조건·전후세포 QC·반복 수를 대조한다."""
import argparse
import json
from collections import defaultdict
from pathlib import Path
import numpy as np
import medium_recording_lookup as m
from population_reciprocity import ROOT,sha
from superficial_ee_eligibility import save

HERE=Path(__file__).resolve().parent
SOURCE=HERE/'different_donor_fit_coverage_result.json'
NAME='different_donor_protocol_repeats'


def summarize(records):
    groups=defaultdict(list)
    for r in records:
        groups[json.dumps(r['condition'],sort_keys=True)].append(r)
    result=[]
    for key,rr in groups.items():
        result.append(dict(condition=json.loads(key),recordings=[r['post']['recording'] for r in rr],
            sweeps=[r['post']['sweep'] for r in rr],repeats=len(rr),
            both_recording_qc_pass=sum(r['pre']['qc_pass']==1 and r['post']['qc_pass']==1 for r in rr),
            all_pulses_ex_qc_pass=sum(r['ex_qc_count']==r['pulse_count'] for r in rr),
            all_pulses_single_spike=sum(r['single_spike_count']==r['pulse_count'] for r in rr),
            all_pulses_aligned=sum(r['aligned_count']==r['pulse_count'] for r in rr)))
    return result


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verify',action='store_true');args=parser.parse_args()
    if args.verify:
        out=json.loads((HERE/f'{NAME}_result.json').read_text(encoding='utf-8'))
        contract=json.loads((HERE/f'{NAME}_contract.json').read_text(encoding='utf-8'))
        assert contract['code_sha256']==sha(Path(__file__)) and contract['source_sha256']==sha(SOURCE)
        assert summarize(out['records'])==out['groups']
        assert sum(g['repeats'] for g in out['groups'])==15
        print('OFFLINE_GROUPING_PASS');return
    save(f'{NAME}_contract.json',dict(
        question='다른 donor pair116053에 같은 자극 조건의 반복이 있는가? 전후세포 모드·QC는 어떠한가?',
        context='기존 coverage의 시각을 읽은 후 수행하는 기술 재고 조사. 새 생물 예측 사전등록 아님.',
        selection='기존180 pulse_response 전부, 15개 후세포 기록. QC·진폭으로 제외하지 않음.',
        condition='전/후 clamp mode, stim_pulse amplitude 전체 순서, duration_us 전체 순서, pulse 간 onset interval_us 전체 순서. 시간은1us로 반올림하여 부동소수점 오차 제거; 원 실수값도 보존.',
        identity='각 stim_pulse를 DB 재조회해 앞선 id/recording/pulse/onset/n_spikes/first_spike_time과 정확히 대조. 전후 recording은 동일 sync_rec·experiment4251, 각각 electrode33930/33926이어야 함.',
        qc='전후 recording QC와 pulse exQC, n_spikes=1, alignment 보유를 각각 집계. QC 미달도 조건별 분모에 보존.',
        interpretation='서로 다른 회복간격·모드·진폭의 반복을 합치지 않음. 동일 명령 조건은 세포 상태 동일성이나 통계적 충분성을 보증하지 않음. BIO_EVIDENCE_L0 조건 재고.',
        next_gate='IC 조건별 반복 부족이면 같은 두 시행 창 조정 중단. 다른 모드 반복은 별도 단위·측정 모형을 고정한 뒤에만 분석.',
        source_sha256=sha(SOURCE),code_sha256=sha(Path(__file__))))
    coverage=json.loads(SOURCE.read_text(encoding='utf-8'))
    remote=json.loads((HERE/'medium_recording_lookup_result.json').read_text(encoding='utf-8'))['remote']
    raw=m.raw;raw.URL=remote['url'];raw.CACHE=ROOT/'data/external/allen_synphys_r21/medium_ranges';raw.LIMIT=128*1024*1024
    records=[]
    with raw.CachedRanges() as reader:
        assert reader.remote==remote
        vfs=m.ReadVFS(reader);db=m.apsw.Connection('remote.sqlite',flags=m.apsw.SQLITE_OPEN_READONLY,vfs='ce_medium_readonly')
        def query(sql,params):
            cursor=db.cursor();rows=cursor.execute(sql,params)
            keys=[d[0] for d in cursor.get_description()]
            return [dict(zip(keys,r)) for r in rows]
        def recording(rid):
            rows=query('select r.id recording,r.sync_rec_id,r.start_time,r.stim_name,r.stim_meta,'
                       's.ext_id sweep,s.experiment_id,el.id electrode,el.device_id,p.clamp_mode,p.qc_pass,'
                       'p.baseline_potential,p.baseline_current,p.baseline_noise_stdev,p.meta qc_meta '
                       'from recording r join sync_rec s on s.id=r.sync_rec_id '
                       'join electrode el on el.id=r.electrode_id '
                       'join patch_clamp_recording p on p.recording_id=r.id where r.id=?',(rid,))
            assert len(rows)==1;return rows[0]
        try:
            for summary in coverage['summary']:
                rid=summary['recording']['id']
                old=sorted([r for r in coverage['records'] if r['response']['recording_id']==rid],key=lambda r:r['stimulus']['pulse_number'])
                pulses=[]
                for r in old:
                    rows=query('select id,recording_id,pulse_number,onset_time,n_spikes,first_spike_time,amplitude,duration from stim_pulse where id=?',(r['stimulus']['id'],))
                    assert len(rows)==1
                    pulse=rows[0];assert all(pulse[k]==v for k,v in r['stimulus'].items());pulses.append(pulse)
                assert len({p['recording_id'] for p in pulses})==1
                pre=recording(pulses[0]['recording_id']);post=recording(rid)
                assert pre['sync_rec_id']==post['sync_rec_id'] and pre['experiment_id']==post['experiment_id']==4251
                assert pre['electrode']==33930 and post['electrode']==33926
                onsets=[p['onset_time'] for p in pulses]
                assert len(pulses)==12 and [p['pulse_number'] for p in pulses]==list(range(12))
                condition=dict(pre_mode=pre['clamp_mode'],post_mode=post['clamp_mode'],
                    amplitude=[p['amplitude'] for p in pulses],
                    duration_us=[round(p['duration']*1e6) for p in pulses],
                    onset_intervals_us=[round((b-a)*1e6) for a,b in zip(onsets,onsets[1:])])
                records.append(dict(pre=pre,post=post,pulses=pulses,condition=condition,pulse_count=len(pulses),
                    recovery_onset_gap_s=onsets[8]-onsets[7],aligned_count=sum(p['first_spike_time'] is not None for p in pulses),
                    single_spike_count=sum(p['n_spikes']==1 for p in pulses),ex_qc_count=sum(r['response']['ex_qc_pass']==1 for r in old)))
        finally:
            db.close();vfs.unregister()
        new_bytes=reader.downloaded_this_session
    out=dict(contract_sha256=sha(HERE/f'{NAME}_contract.json'),remote=remote,records=records,groups=summarize(records),new_bytes=new_bytes)
    save(f'{NAME}_result.json',out)
    print(json.dumps(dict(groups=out['groups'],new_bytes=new_bytes),indent=2))


if __name__=='__main__':main()
