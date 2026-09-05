"""저장된 삭제 대상 ID로 그래프를 복원하고 부호 반전 대표 두 건을 재적합한다."""
import csv,hashlib,json
from pathlib import Path
import numpy as np
import microns_constrained_swaps as base
from joint_degree_refit_bootstrap import refine
HERE=base.HERE
rp=HERE/'edge_deletion_result.json';result=json.loads(rp.read_text())
full,cats=base.load_graph();roots=json.loads(base.SELECTED.read_text())['selected_roots'];lookup={r:i for i,r in enumerate(roots)}
with np.load(base.ROOT/'data/external/joint_expected_degree_models/minnie23P_t1_polished.npz',allow_pickle=False) as saved:mroots=saved['roots'].tolist()
ids=[lookup[r] for r in mroots];datasets={'minnie23P':(full[np.ix_(ids,ids)],cats[np.ix_(ids,ids)]%6,mroots)}
data=base.ROOT/'data/external/microns_pinky_v185'
cells=sorted([r for r in csv.DictReader((data/'soma_valence_v185.csv').open()) if r['cell_type']=='e'],key=lambda r:int(r['pt_root_id']))
proots=[int(r['pt_root_id']) for r in cells];index={r:i for i,r in enumerate(proots)};counts=np.zeros((len(cells),len(cells)),dtype=int)
for row in csv.DictReader((data/'soma_subgraph_synapses_spines_v185.csv').open()):
    u,v=index[int(row['pre_root_id'])],index[int(row['post_root_id'])]
    if u!=v:counts[u,v]+=1
xyz=np.array([list(map(int,r['pt_position'].strip('[]').split())) for r in cells])*[.00354,.00354,.04]
c=np.digitize(np.linalg.norm(xyz[:,None,:]-xyz[None,:,:],axis=2),[50,100,200,400,800]);datasets['pinky']=(counts,c,proots)
replays=[]
for row in result['results']:
    path=base.ROOT/row['record_path'];assert base.sha(path)==row['record_sha256'];record=json.loads(path.read_text())
    counts,c,roots=datasets[row['dataset']];idx={r:i for i,r in enumerate(roots)};a=counts>=1
    removed=[(idx[u],idx[v]) for u,v in record['removed_root_pairs']]
    assert len(set(removed))==row['deleted_edges'] and all(a[p] for p in removed)
    assert sum(int(counts[p]) for p in removed)==row['deleted_synapse_annotations']
    if row['strategy']=='targeted':
        assert all(a[v,u] for u,v in removed) and len({tuple(sorted(p)) for p in removed})==len(removed)
    for p in removed:a[p]=False
    assert hashlib.sha256(a.tobytes()).hexdigest()==record['graph_sha256']
    assert int((a&a.T).sum()//2)==record['observed_mutual']
    if row['seed']==2026090514 and row['strategy']=='targeted' and ((row['dataset']=='minnie23P' and row['deleted_edges']==60) or (row['dataset']=='pinky' and row['deleted_edges']==9)):
        p,diagnostic=refine(a,c);assert diagnostic['gate_pass']
        residual=int((a&a.T).sum()//2)-sum(float(p[i,j]*p[j,i]) for i in range(len(a)) for j in range(i+1,len(a)))
        assert abs(residual-row['residual'])<1e-7
        replays.append(dict(dataset=row['dataset'],deleted_edges=len(removed),residual=residual))
receipt=dict(result_sha256=base.sha(rp),verifier_sha256=base.sha(Path(__file__)),reconstructed_graphs=len(result['results']),refitted_cases=replays,
    status='ALL36_DELETION_GRAPHS_VERIFIED_TWO_SIGN_REVERSALS_REFITTED')
out=HERE/'edge_deletion_verification.json'
if out.exists():assert json.loads(out.read_text())==receipt
else:out.write_text(json.dumps(receipt,indent=2),encoding='utf-8')
print(json.dumps(receipt,indent=2))
