"""다음 개체의 제작자 평균 선택 규칙을 재현하고 저장 평균을 안전하게 추출한다."""
import argparse
import io
import json
import sqlite3
from pathlib import Path
import numpy as np
import medium_recording_lookup as m
from population_reciprocity import ROOT,DB,sha
from superficial_ee_eligibility import save

HERE=Path(__file__).resolve().parent
NAME='producer_average_membership'


def classify(rows):
    included={};excluded={}
    for r in rows:
        reason=None;key=None
        if r['induction_frequency'] is None or r['induction_frequency']>50:reason='frequency_not_le_50'
        elif r['spike_rows']==0:reason='no_stim_spike_join'
        elif r['clamp_mode'] not in ('ic','vc'):reason='unsupported_mode'
        elif r['baseline_potential'] is None:reason='missing_potential'
        elif -.080<=r['baseline_potential']<-.060:key=(r['clamp_mode'],-70);qc=r['ex_qc_pass']
        elif -.060<=r['baseline_potential']<-.050:key=(r['clamp_mode'],-55);qc=r['in_qc_pass']
        else:reason='outside_holding_bins'
        if reason is None:
            if not qc:reason='pulse_qc'
            elif r['n_spikes']!=1:reason='not_single_spike'
            elif r['first_spike_time'] is None:reason='missing_spike_time'
        if reason is not None:excluded[r['response_id']]=reason;continue
        assert r['spike_rows']==1,'원join중복으로분모불일치가능'
        included.setdefault(f'{key[0]}_{key[1]}',[]).append(r['response_id'])
    return dict(included=included,excluded=excluded)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verify',action='store_true');args=parser.parse_args()
    output=HERE/f'{NAME}_result.json'
    if args.verify:
        r=json.loads(output.read_text(encoding='utf-8'))
        c=json.loads((HERE/f'{NAME}_contract.json').read_text(encoding='utf-8'))
        assert c['code_sha256']==sha(Path(__file__))
        now=classify(r['rows']);now['excluded']={str(k):v for k,v in now['excluded'].items()}
        assert now==r['membership']
        for a in r['averages']:
            assert sha(ROOT/a['array_path'])==a['array_sha256']
            assert len(r['membership']['included'][a['group']])==a['n_averaged_responses']
        print('PRODUCER_AVERAGE_MEMBERSHIP_PASS');return
    save(f'{NAME}_contract.json',dict(
        question='pair121538の制作側平均IC458/VC60/60の選択分母を再現できるか?',
        scope='固定した次個体の全1042pulse_response。source response_query/sort_responsesの条件を読み取り適用し、stored avg_dataも抽出。',
        selection='post記録→patch_clamp_recording→multi_patch_probe induction_frequency<=50;StimSpike inner join;holding[-80,-60)mVはexQC、[-60,-50)mVはinQC;単一spike+first_spike_time必須。',
        safety='原DB読み取り専用。avg_dataはNPY magic確認後np.load allow_pickle=False。原blobは独立npyとして保管し上書きしない。',
        limits='同じ数が一致しても歴史的平均へのID完全一致や波形再構成を証明しない。選択ID候補として保存。平均は独立ground truthではない。L0測定再現。',
        code_sha256=sha(Path(__file__)),db_sha256=sha(DB),
        selection_source_sha256=sha(HERE/'qc_sources/avg_response_fit.py'),schema_sha256=sha(HERE/'qc_sources/schema_init.py'),
        inventory_sha256=sha(HERE/'next_donor_recording_inventory_result.json')))
    remote=json.loads((HERE/'medium_recording_lookup_result.json').read_text(encoding='utf-8'))['remote']
    raw=m.raw;raw.URL=remote['url'];raw.CACHE=ROOT/'data/external/allen_synphys_r21/medium_ranges';raw.LIMIT=128*1024*1024
    with raw.CachedRanges() as reader:
        assert reader.remote==remote
        vfs=m.ReadVFS(reader);db=m.apsw.Connection('remote.sqlite',flags=m.apsw.SQLITE_OPEN_READONLY,vfs='ce_medium_readonly')
        try:
            cursor=db.cursor();it=cursor.execute('select pr.id response_id,pr.recording_id,pr.stim_pulse_id,pr.ex_qc_pass,pr.in_qc_pass,'
                'sp.n_spikes,sp.first_spike_time,sp.pulse_number,pc.clamp_mode,pc.baseline_potential,mp.induction_frequency,'
                '(select count(*) from stim_spike ss where ss.stim_pulse_id=sp.id) spike_rows '
                'from pulse_response pr join stim_pulse sp on sp.id=pr.stim_pulse_id '
                'join patch_clamp_recording pc on pc.recording_id=pr.recording_id '
                'left join multi_patch_probe mp on mp.patch_clamp_recording_id=pc.id '
                'where pr.pair_id=121538 order by pr.id')
            keys=[d[0] for d in cursor.get_description()];rows=[dict(zip(keys,r)) for r in it]
        finally:db.close();vfs.unregister()
        new_bytes=reader.downloaded_this_session
    inventory=json.loads((HERE/'next_donor_recording_inventory_result.json').read_text(encoding='utf-8'))['pairs'][0]
    assert len(rows)==len({r['response_id'] for r in rows})==1042
    assert {r['response_id'] for r in rows}=={p['response_id'] for r in inventory['records'] for p in r['pulses']}
    membership=classify(rows);averages=[]
    destdir=ROOT/'data/external/allen_synphys_r21/producer_averages';destdir.mkdir(exist_ok=True)
    with sqlite3.connect(DB.as_uri()+'?mode=ro',uri=True) as db:
        db.row_factory=sqlite3.Row
        for value in db.execute('select id,clamp_mode,holding,n_averaged_responses,manual_qc_pass,avg_data,avg_data_start_time from avg_response_fit where synapse_id=2985 order by id'):
            a=dict(value);blob=a.pop('avg_data');assert blob.startswith(b'\x93NUMPY')
            arr=np.load(io.BytesIO(blob),allow_pickle=False);assert arr.ndim==1 and np.isfinite(arr).all()
            dest=destdir/f"avg_response_fit_{a['id']}.npy"
            if dest.exists():assert dest.read_bytes()==blob
            else:
                with dest.open('xb') as stream:stream.write(blob)
            group=f"{a['clamp_mode']}_{int(a['holding'])}"
            a.update(group=group,array_path=dest.relative_to(ROOT).as_posix(),array_sha256=sha(dest),samples=len(arr),rate_hz=20000,
                selected_count=len(membership['included'].get(group,[])))
            averages.append(a)
    result=dict(contract_sha256=sha(HERE/f'{NAME}_contract.json'),remote=remote,rows=rows,membership=membership,averages=averages,new_bytes=new_bytes,
        all_counts_match=all(a['selected_count']==a['n_averaged_responses'] for a in averages))
    save(f'{NAME}_result.json',result)
    print(json.dumps(dict(averages=averages,all_counts_match=result['all_counts_match'],new_bytes=new_bytes),indent=2))


if __name__=='__main__':main()
