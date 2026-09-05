"""MICrONS 공개 V1 column 추출의 교정 상태·식별자·관측 연결을 점검한다."""
import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path
from reference_spike_audit import sha

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
DATA=ROOT/'data/external/microns_v1718_cosyne'
RECEIPT=HERE/'microns_acquisition_receipt.json'
CONTRACT=HERE/'microns_structural_inventory_contract.json'
OUTPUT=HERE/'microns_structural_inventory_result.json'


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--verify',action='store_true');args=parser.parse_args()
    receipt=json.loads(RECEIPT.read_text(encoding='utf-8'))
    for item in receipt['files']:assert sha(ROOT/item['path'])==item['sha256']
    sys.path.insert(0,str(ROOT/'data/external/analysis_tools/arrow_reader'))
    import pyarrow
    import pyarrow.feather as feather
    spec=dict(question='What structural directed and reciprocal contacts are present in the independent-modality MICrONS column export with both partners axon/dendrite proofread?',
        status='cross-dataset measurement bridge; not direct replication of electrophysiological has_synapse or proof of specimen independence',
        selection='all cell_info rows with is_column AND status_axon AND status_dendrite True, chosen before connection counts; all integer root IDs preserved',
        connection='at least1 distinct synapse annotation between two selected different roots; at least3 annotations sensitivity fixed in advance',
        missing='unlisted edges mean no annotation in this export, not biological absence; unproofread/noncolumn IDs excluded with counts',
        comparison='descriptive counts only; no null excess or degree-preserving comparison until export and sampling coverage qualified',
        source_receipt_sha256=sha(RECEIPT),code_sha256=sha(Path(__file__)),pyarrow=pyarrow.__version__)
    if CONTRACT.exists():assert spec==json.loads(CONTRACT.read_text(encoding='utf-8'))
    elif args.verify:raise RuntimeError('계약 없음')
    else:
        with CONTRACT.open('x',encoding='utf-8') as stream:json.dump(spec,stream,indent=2)
    with (DATA/'v1718_cell_info.csv').open(encoding='utf-8',newline='') as stream:cells=list(csv.DictReader(stream))
    roots=[int(c['pt_root_id']) for c in cells];assert len(roots)==len(set(roots))
    by_id={int(c['pt_root_id']):c for c in cells}
    for c in cells:
        assert all(c[k] in ('True','False') for k in ('is_column','status_axon','status_dendrite'))
    selected={root for root,c in by_id.items() if root!=0 and all(c[k]=='True' for k in ('is_column','status_axon','status_dendrite'))}
    table=feather.read_table(DATA/'v1718_v1_column_synapses.feather')
    columns={k:table[k].to_pylist() for k in ('syn_id','size','pre_pt_root_id','post_pt_root_id')}
    assert len(columns['syn_id'])==len(set(columns['syn_id']))
    edges=Counter();excluded=Counter();missing_roots=set();self_rows=0;kept=0
    for pre,post in zip(columns['pre_pt_root_id'],columns['post_pt_root_id']):
        assert isinstance(pre,int) and isinstance(post,int)
        if pre not in by_id:missing_roots.add(pre)
        if post not in by_id:missing_roots.add(post)
        if pre not in selected or post not in selected:
            excluded['outside_selected_partners']+=1;continue
        if pre==post:self_rows+=1;continue
        edges[pre,post]+=1;kept+=1
    summaries={}
    for threshold in (1,3):
        included={pair for pair,count in edges.items() if count>=threshold}
        mutual=sum(pre<post and (post,pre) in included for pre,post in included)
        touched={v for pair in included for v in pair}
        summaries[str(threshold)]=dict(directed_edges=len(included),reciprocal_dyads=mutual,
            one_way_annotated_dyads=len(included)-2*mutual,selected_nodes_without_retained_edge=len(selected-touched))
    result=dict(contract_sha256=sha(CONTRACT),cell_rows=len(cells),zero_root_rows=roots.count(0),
        selected_cells=len(selected),column_cells=sum(c['is_column']=='True' for c in cells),
        column_axon_proofread_cells=sum(c['is_column']=='True' and c['status_axon']=='True' for c in cells),
        selected_broad_types=dict(Counter(by_id[r]['broad_type'] or 'unknown' for r in selected)),
        total_synapse_rows=table.num_rows,selected_nonself_synapses=kept,self_synapse_rows=self_rows,
        excluded=dict(excluded),synapse_roots_absent_from_cell_table=sorted(missing_roots),
        nonpositive_or_missing_size_rows=sum(v is None or v<=0 for v in columns['size']),
        thresholds=summaries,selected_roots=sorted(selected),
        limitations=['one EM volume, not independent animals','finite volume and reconstruction errors','proofreading selection','export query completeness not independently reproduced','specimen nonoverlap with synphys not yet verified at ID level'])
    if args.verify:
        assert result==json.loads(OUTPUT.read_text(encoding='utf-8'));print('MICRONS_STRUCTURAL_INVENTORY_REPRODUCED')
    else:
        with OUTPUT.open('x',encoding='utf-8') as stream:json.dump(result,stream,indent=2)
    print(json.dumps({k:v for k,v in result.items() if k!='selected_roots'},indent=2))


if __name__=='__main__':main()
