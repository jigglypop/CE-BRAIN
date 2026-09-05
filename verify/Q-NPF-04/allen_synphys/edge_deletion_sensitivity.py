"""같은 연결 삭제 규모에서 무작위 및 상호연결 표적 민감도를 비교한다."""
import csv,hashlib,json,math
from pathlib import Path
import numpy as np
import microns_constrained_swaps as base
from joint_degree_refit_bootstrap import refine
HERE=base.HERE


def main():
    spec=dict(question='How sensitive is fitted reciprocity residual to edge deletions targeted at mutual pairs versus uniformly selected observed edges?',
        scope='original minnie23P347 and Pinky e362, threshold1 only; all cells retained',
        budgets='ceil(0.001E),ceil(0.005E),ceil(0.01E) directed edges, where E is original nonself edge count',
        seeds=[2026090514,2026090515,2026090516],
        deletion='uniform:random permutation of all observed edges; targeted:random permutation of original reciprocal dyads, one randomly chosen direction per dyad; prefix nested budgets; no optimization',
        measurement='deleting an edge removes every annotation supporting that direction; report affected synapse counts separately; these fractions are not estimated biological error rates',
        refit='same joint expected margin model, refine function and1e-5 gate; no bootstrap p value carried over from unperturbed graph',
        inference='hypothetical perturbation only; does not identify actual false positives, false negatives or optimal minimum edits; no raw source deletion',
        source_sha256=json.loads((HERE/'joint_expected_degree_contract.json').read_text())['source_sha256'],
        baseline_sha256=base.sha(HERE/'joint_degree_refit_bootstrap_result.json'),
        code_sha256=base.sha(Path(__file__)),refitter_sha256=base.sha(HERE/'joint_degree_refit_bootstrap.py'),
        model_sha256=base.sha(HERE/'joint_expected_degree_reference.py'),loader_sha256=base.sha(Path(base.__file__)))
    cp=HERE/'edge_deletion_contract.json'
    if cp.exists():assert json.loads(cp.read_text())==spec
    else:cp.write_text(json.dumps(spec,indent=2),encoding='utf-8')
    for p,h in spec['source_sha256'].items():assert base.sha(base.ROOT/p)==h
    full,cats=base.load_graph();roots=json.loads(base.SELECTED.read_text())['selected_roots']
    with (base.DATA/'v1718_cell_info.csv').open(encoding='utf-8',newline='') as stream:cells={int(r['pt_root_id']):r for r in csv.DictReader(stream)}
    ids=[i for i,r in enumerate(roots) if cells[r]['broad_type']=='excitatory' and cells[r]['cell_type']=='23P']
    datasets=[('minnie23P',full[np.ix_(ids,ids)],cats[np.ix_(ids,ids)]%6,[roots[i] for i in ids])]
    data=base.ROOT/'data/external/microns_pinky_v185'
    cs=sorted([r for r in csv.DictReader((data/'soma_valence_v185.csv').open()) if r['cell_type']=='e'],key=lambda r:int(r['pt_root_id']))
    proots=[int(r['pt_root_id']) for r in cs];index={r:i for i,r in enumerate(proots)}
    xyz=np.array([list(map(int,r['pt_position'].strip('[]').split())) for r in cs])*[.00354,.00354,.04]
    c=np.digitize(np.linalg.norm(xyz[:,None,:]-xyz[None,:,:],axis=2),[50,100,200,400,800]);counts=np.zeros((362,362),dtype=int)
    for r in csv.DictReader((data/'soma_subgraph_synapses_spines_v185.csv').open()):
        u,v=index[int(r['pre_root_id'])],index[int(r['post_root_id'])]
        if u!=v:counts[u,v]+=1
    datasets.append(('pinky',counts,c,proots))
    folder=base.ROOT/'data/external/edge_deletion_sensitivity';folder.mkdir(exist_ok=True);results=[]
    for name,counts,c,selected in datasets:
        original=counts>=1;edges=np.argwhere(original);E=len(edges);mutual=np.argwhere(np.triu(original&original.T,1));original_mutual=len(mutual)
        for seed in spec['seeds']:
            uniform=edges[np.random.default_rng(seed).permutation(E)]
            rng=np.random.default_rng(seed+100);targeted=mutual[rng.permutation(len(mutual))].copy()
            for i in range(len(targeted)):
                if rng.integers(0,2):targeted[i]=targeted[i][::-1]
            for strategy,ordered in [('uniform',uniform),('targeted',targeted)]:
                for rate in (.001,.005,.01):
                    k=math.ceil(E*rate);assert k<=len(ordered)
                    removed=ordered[:k];a=original.copy();a[removed[:,0],removed[:,1]]=False
                    assert int((a!=original).sum())==k and not np.any(a&~original)
                    digest=hashlib.sha256(a.tobytes()).hexdigest();path=folder/f'{name}_{seed}_{strategy}_{k}.json'
                    if path.exists():
                        record=json.loads(path.read_text());assert record['contract_sha256']==base.sha(cp) and record['graph_sha256']==digest
                    else:
                        fitted,diag=refine(a,c);observed=int((a&a.T).sum()//2);mean=float(np.triu(fitted*fitted.T,1).sum())
                        if strategy=='targeted':assert observed==original_mutual-k
                        record=dict(contract_sha256=base.sha(cp),dataset=name,seed=seed,strategy=strategy,nominal_fraction=rate,
                            original_edges=E,deleted_edges=k,actual_deleted_fraction=k/E,deleted_synapse_annotations=int(counts[removed[:,0],removed[:,1]].sum()),
                            removed_root_pairs=[[int(selected[u]),int(selected[v])] for u,v in removed],graph_sha256=digest,
                            observed_mutual=observed,refitted_mean=mean if diag['gate_pass'] else None,
                            residual=observed-mean if diag['gate_pass'] else None,diagnostic=diag)
                        with path.open('x') as stream:json.dump(record,stream,indent=2)
                    results.append(dict(**{k:v for k,v in record.items() if k not in ('removed_root_pairs','diagnostic')},
                        gate_pass=record['diagnostic']['gate_pass'],max_margin_error=record['diagnostic']['max_absolute_margin_error'],
                        record_path=path.relative_to(base.ROOT).as_posix(),record_sha256=base.sha(path)))
            print(name,seed,'completed',flush=True)
    summary=[]
    for name in ('minnie23P','pinky'):
        for strategy in ('uniform','targeted'):
            for rate in (.001,.005,.01):
                rows=[r for r in results if r['dataset']==name and r['strategy']==strategy and r['nominal_fraction']==rate]
                valid=all(r['gate_pass'] for r in rows)
                summary.append(dict(dataset=name,strategy=strategy,nominal_fraction=rate,deleted_edges=rows[0]['deleted_edges'],
                    all_pass=valid,residual_range=[min(r['residual'] for r in rows),max(r['residual'] for r in rows)] if valid else None,
                    deleted_annotation_range=[min(r['deleted_synapse_annotations'] for r in rows),max(r['deleted_synapse_annotations'] for r in rows)]))
    output=dict(contract_sha256=base.sha(cp),results=results,summary=summary,status='HYPOTHETICAL_EDGE_DELETION_NOT_ERROR_RATE_ESTIMATE')
    out=HERE/'edge_deletion_result.json'
    if out.exists():assert json.loads(out.read_text())==output
    else:out.write_text(json.dumps(output,indent=2),encoding='utf-8')
    print(json.dumps(summary,indent=2))


if __name__=='__main__':main()
