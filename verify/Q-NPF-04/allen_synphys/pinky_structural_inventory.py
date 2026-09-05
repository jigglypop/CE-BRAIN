"""Pinky 교정 시냅스 표의 연결 목록 감사. 좌표와 세포 모집단은 아직 확정하지 않는다."""
import csv
import json
from collections import Counter
from pathlib import Path
from reference_spike_audit import sha

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
DATA=ROOT/'data/external/microns_pinky_v185'


def main():
    sources=json.loads((HERE/'pinky_acquisition_receipt.json').read_text())['files']
    spec=dict(scope='all records of published QC soma-subgraph synapse file, count positive edges only; endpoint union is not full cell population',
        thresholds=[1,3],exclusions='report self links and duplicate synapse IDs; do not silently deduplicate or exclude labels',
        coordinates='audit redundant nm columns and parse original pt_position only; no distance-based biological result',
        gates='server checksum previously verified, current hashes; unique synapse IDs, partner IDs in soma table; IDs parsed as Python integers',
        ceiling='new source inventory and observed connections, not replication of conditional reciprocity excess or E-I circuit',
        source_sha256={r['path']:r['sha256'] for r in sources},code_sha256=sha(Path(__file__)))
    cp=HERE/'pinky_inventory_contract.json'
    if cp.exists():assert json.loads(cp.read_text())==spec
    else:cp.write_text(json.dumps(spec,indent=2),encoding='utf-8')
    for p,h in spec['source_sha256'].items():assert sha(ROOT/p)==h
    with (DATA/'soma_valence_v185.csv').open(newline='') as stream:cells=list(csv.DictReader(stream))
    with (DATA/'soma_subgraph_synapses_spines_v185.csv').open(newline='') as stream:syn=list(csv.DictReader(stream))
    mapping={int(r['pt_root_id']):r for r in cells};assert len(mapping)==len(cells)
    assert len({int(r['id']) for r in syn})==len(syn)
    edges=Counter((int(r['pre_root_id']),int(r['post_root_id'])) for r in syn)
    roots={i for p in edges for i in p};assert roots<=set(mapping)
    selfrows=sum(n for (u,v),n in edges.items() if u==v)
    assert selfrows==0
    coords=[list(map(int,r['pt_position'].strip('[]').split())) for r in cells]
    assert all(len(p)==3 for p in coords)
    coordinate_audit=dict(rows=len(cells),x_equals_y_and_z_equals10x=sum(int(r['soma_x_nm'])==int(r['soma_y_nm']) and int(r['soma_z_nm'])==10*int(r['soma_x_nm']) for r in cells),
        nm_disagrees_with_pt_position_nominal=sum([int(r[k]) for k in ('soma_x_nm','soma_y_nm','soma_z_nm')]!=[p[0]*4,p[1]*4,p[2]*40] for r,p in zip(cells,coords)),
        action='do not use convenience nm columns; independently verify pt_position scale and population before spatial comparison')
    results=[]
    for t in spec['thresholds']:
        selected={p for p,n in edges.items() if n>=t}
        mutual=sum((v,u) in selected for u,v in selected)//2
        results.append(dict(threshold=t,directed_edges=len(selected),mutual_pairs=mutual,one_way_pairs=len(selected)-2*mutual,
                            endpoints_with_retained_edges=len({i for p in selected for i in p})))
    result=dict(contract_sha256=sha(cp),synapse_rows=len(syn),soma_rows=len(cells),endpoint_cells=len(roots),
        all_soma_labels=dict(Counter(r['cell_type'] for r in cells)),endpoint_labels=dict(Counter(mapping[i]['cell_type'] for i in roots)),
        soma_cells_not_in_synapse_endpoints=len(cells)-len(roots),self_synapses=selfrows,coordinate_audit=coordinate_audit,thresholds=results)
    out=HERE/'pinky_inventory_result.json'
    if out.exists():assert json.loads(out.read_text())==result
    else:out.write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
