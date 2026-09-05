"""사용한 양성 연결 표지와 모드별 수동 평균 적합의 근거를 구분한다."""
import argparse
import ast
import json
import sqlite3
from pathlib import Path
from population_reciprocity import DB,sha
from superficial_ee_eligibility import save

HERE=Path(__file__).resolve().parent
NAME='connection_label_provenance'
FILES=['source_snapshots/aisynphys__pipeline__multipatch__synapse.py','qc_sources/avg_response_fit.py',
       'source_snapshots/aisynphys__pipeline__multipatch__pulse_response.py','source_snapshots/aisynphys__database__schema__synapse.py']


def extract():
    sources={}
    for name in FILES:
        text=(HERE/name).read_text(encoding='utf-8');ast.parse(text)
        sources[name]=dict(sha256=sha(HERE/name),references=[dict(line=i,text=line.strip()) for i,line in enumerate(text.splitlines(),1)
            if any(token in line for token in ("pair.has_synapse =",'notes_db.get_pair_notes_record',"notes_rec.notes['synapse_type']",'manual_qc_pass',
                "notes['fit_pass']",'expected_fit_params =',"if not pr.pair.has_synapse",'latency_window = (init_latency'))])
    with sqlite3.connect(DB.as_uri()+'?mode=ro',uri=True) as db:
        db.row_factory=sqlite3.Row
        records=[]
        for pid in (104272,116053,121538):
            pair=dict(db.execute('select id,experiment_id,pre_cell_id,post_cell_id,has_synapse,has_polysynapse,has_electrical,n_ex_test_spikes,n_in_test_spikes,meta from pair where id=?',(pid,)).fetchone())
            syn=dict(db.execute('select * from synapse where pair_id=?',(pid,)).fetchone())
            fits=[dict(r) for r in db.execute('select id,synapse_id,clamp_mode,holding,manual_qc_pass,n_averaged_responses,initial_xoffset,fit_xoffset,fit_amp,fit_rise_time,fit_decay_tau,nrmse,avg_baseline_noise,meta from avg_response_fit where synapse_id=? order by clamp_mode,holding',(syn['id'],))]
            assert pair['has_synapse']==1 and all(f['synapse_id']==syn['id'] for f in fits)
            records.append(dict(pair=pair,synapse=syn,average_fits=fits))
        note_tables=[r[0] for r in db.execute("select name from sqlite_master where type='table' and name like '%note%'")]
    return dict(records=records,source_evidence=sources,note_named_tables_in_small_db=note_tables,
        conclusion='양성 표지는제작자수동주석의전파. 모드별평균적합QC와연결양성은별개. 동일전기생리로만든주석과적합을독립외부정답으로간주하지않음.')


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verify',action='store_true');args=parser.parse_args()
    contract=dict(
        question='현재사용한3pair의양성표지와모드별평균적합QC는무엇이며,독립검증으로사용할수있는가?',
        selection='개발104272,다른개체116053,다음개체121538 전체;결과에따라범위변경없음.',
        data='보유smallDB의pair/synapse/avg_response_fit스칼라필드;평균파형배열은읽지않음.기존소스의주석→표지→적합의존관계와줄번호·해시보존.',
        limits='DB notes이름테이블조회는small판본내범위.공개주석전체부재로확대안함. 수동표지가틀렸다는판정아님.원생산환경·평가자이력·독립EM/개입확인미확보. L0출처감사.',
        primary_sources=[
            'https://brain-map.org/support/documentation/synaptic-physiology-analysis-methods',
            'https://brain-map.org/support/documentation/synaptic-physiology-analysis-methods-connection-characterization'],
        db_sha256=sha(DB),code_sha256=sha(Path(__file__)),sources={f:sha(HERE/f) for f in FILES})
    if args.verify:assert json.loads((HERE/f'{NAME}_contract.json').read_text(encoding='utf-8'))==contract
    else:save(f'{NAME}_contract.json',contract)
    result=dict(contract_sha256=sha(HERE/f'{NAME}_contract.json'),analysis=extract())
    if args.verify:
        assert json.loads((HERE/f'{NAME}_result.json').read_text(encoding='utf-8'))==result
        print('LABEL_PROVENANCE_REPRODUCTION_PASS');return
    save(f'{NAME}_result.json',result)
    for row in result['analysis']['records']:
        print('pair',row['pair']['id'],'synapse',row['synapse']['id'])
        for f in row['average_fits']:
            print(f['clamp_mode'],f['holding'],'manualQC',f['manual_qc_pass'],'n',f['n_averaged_responses'],'amp',f['fit_amp'],'meta',f['meta'])


if __name__=='__main__':main()
