"""v185 e-표지 전체 세포의 국소 기준. 최종 논문 재현이나 완전한 생물 그래프 아님."""
import csv,json
from collections import Counter
from pathlib import Path
import numpy as np
from reference_spike_audit import sha
from microns_exact_quartets import universe,PAIRS
from microns_disjoint_reference import distribution
HERE=Path(__file__).resolve().parent
DATA=HERE.parents[2]/'data/external/microns_pinky_v185'


def main():
    receipt=json.loads((HERE/'pinky_acquisition_receipt.json').read_text())
    spec=dict(scope='all362 unique as-released e-labelled cells, including28 absent from positive endpoints; no claim this is corrected full biological excitatory population',
        discrepancy='released1961 synapses versus final-paper1960 unresolved; exclude both self annotations from intercell graph without deleting source rows',
        geometry='parse pt_position integer triplet; ignore erroneous convenience nm columns; primary voxel nm[3.54,3.54,40] from release notes, sensitivity[3.58,3.58,40] from paper; not in-vivo deformation correction',
        design='nearby disjoint quartets using original fixed seeds2026090509..511; unused final2 cells retained with all edges fixed; thresholds1and3',
        null='freeze cross-block edges and per-node internal degrees plus internal distance-bin edge counts; uniform product of admissible graphs; same six bins',
        interpretation='exploratory retained-QC-table comparison, no inference that unlisted synapses biologically absent; p values not independent confirmatory replication',
        source_sha256={r['path']:r['sha256'] for r in receipt['files']},code_sha256=sha(Path(__file__)),
        enumeration_sha256=sha(HERE/'microns_exact_quartets.py'),distribution_sha256=sha(HERE/'microns_disjoint_reference.py'))
    cp=HERE/'pinky_local_contract.json'
    if cp.exists():assert json.loads(cp.read_text())==spec
    else:cp.write_text(json.dumps(spec,indent=2),encoding='utf-8')
    for p,h in spec['source_sha256'].items():assert sha(HERE.parents[2]/p)==h
    cells=sorted([r for r in csv.DictReader((DATA/'soma_valence_v185.csv').open()) if r['cell_type']=='e'],key=lambda r:int(r['pt_root_id']))
    roots=[int(r['pt_root_id']) for r in cells];assert len(roots)==len(set(roots))==362
    idx={r:i for i,r in enumerate(roots)}
    voxels=np.array([list(map(int,r['pt_position'].strip('[]').split())) for r in cells]);assert voxels.shape==(362,3)
    counts=np.zeros((362,362),dtype=int);self_rows=[]
    for r in csv.DictReader((DATA/'soma_subgraph_synapses_spines_v185.csv').open()):
        u,v=int(r['pre_root_id']),int(r['post_root_id']);assert u in idx and v in idx
        if u==v:self_rows.append(int(r['id']))
        else:counts[idx[u],idx[v]]+=1
    assert len(self_rows)==2 and np.count_nonzero((counts.sum(0)+counts.sum(1))==0)==28
    graphs,index,reciprocal=universe();details=[];results=[]
    for xy in (3.54,3.58):
        xyz=voxels*np.array([xy,xy,40])/1000
        for seed in (2026090509,2026090510,2026090511):
            order=list(map(int,np.random.default_rng(seed).permutation(362)));remaining=set(order);blocks=[]
            for anchor in order:
                if len(remaining)<4:break
                if anchor not in remaining:continue
                others=sorted(remaining-{anchor});d=((xyz[others]-xyz[anchor])**2).sum(1)
                q=sorted([anchor]+[others[k] for k in np.lexsort((others,d))[:3]])
                blocks.append(q);remaining.difference_update(q)
            assert len(blocks)==90 and len(remaining)==2
            assert sorted([i for q in blocks for i in q]+list(remaining))==list(range(362))
            for threshold in (1,3):
                rows=[]
                for q in blocks:
                    a=counts[np.ix_(q,q)]>=threshold
                    c=np.digitize(np.linalg.norm(xyz[q][:,None,:]-xyz[q][None,:,:],axis=2),[50,100,200,400,800])
                    state=sum(1<<bit for bit,p in enumerate(PAIRS) if a[p])
                    ids=index[tuple(a.sum(0))+tuple(a.sum(1))];target=np.bincount(c[a],minlength=6)
                    ids=[s for s in ids if np.array_equal(np.bincount(c[graphs[s]],minlength=6),target)]
                    assert state in ids
                    rows.append(dict(indices=q,root_ids=[roots[i] for i in q],observed=int(reciprocal[state]),state=state,
                        joint=dict(admissible_states=ids,histogram={str(k):v for k,v in sorted(Counter(map(int,reciprocal[ids])).items())})))
                identity=dict(xy_voxel_nm=xy,seed=seed,threshold=threshold)
                details.append(dict(**identity,rows=rows,fixed_remaining_root_ids=[roots[i] for i in sorted(remaining)]))
                results.append(dict(**identity,**distribution(rows,'joint')))
    detail=dict(contract_sha256=sha(cp),selected_roots=roots,self_synapse_ids=self_rows,partitions=details)
    dp=HERE/'pinky_local_rows.json'
    if dp.exists():assert json.loads(dp.read_text())==detail
    else:dp.write_text(json.dumps(detail,separators=(',',':')),encoding='utf-8')
    result=dict(contract_sha256=sha(cp),detail_sha256=sha(dp),selected_cells=362,zero_observed_degree_cells=28,
        results=results,status='RELEASE_SPECIFIC_LOCAL_REFERENCE_NOT_FINAL_PAPER_REPLICATION')
    out=HERE/'pinky_local_result.json'
    if out.exists():assert json.loads(out.read_text())==result
    else:out.write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps([{k:v for k,v in r.items() if k not in ('histogram','total_combinations')} for r in results],indent=2))


if __name__=='__main__':main()
