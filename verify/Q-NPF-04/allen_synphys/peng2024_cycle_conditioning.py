"""단방향 골격과 각 세포 차수를 고정한 순환 삼각형의 정확 기대값."""
import csv
import io
import json
import zipfile
from collections import defaultdict
from fractions import Fraction
from functools import lru_cache
from itertools import combinations, product
from pathlib import Path
import numpy as np
from scipy.io import loadmat
from population_reciprocity import ROOT,sha
from superficial_ee_eligibility import save

@lru_cache(maxsize=None)
def orientations(edges, quota):
    if not edges:
        return int(not any(quota))
    degree=[0]*len(quota)
    for a,b in edges:degree[a]+=1;degree[b]+=1
    if any(q<0 or q>d for q,d in zip(quota,degree)) or sum(quota)!=len(edges):return 0
    v=min((i for i,d in enumerate(degree) if d),key=lambda i:degree[i])
    neighbors=tuple(b if a==v else a for a,b in edges if v in (a,b))
    remaining=tuple(e for e in edges if v not in e)
    total=0
    for outgoing in combinations(neighbors,quota[v]):
        q=list(quota);q[v]=0
        for n in neighbors:
            if n not in outgoing:q[n]-=1
        total+=orientations(remaining,tuple(q))
    return total

def measure(n, directed):
    edges=tuple(sorted(tuple(sorted(e)) for e in directed))
    assert len(set(edges))==len(edges)
    edge_set=set(edges);quota=tuple(sum(a==i for a,b in directed) for i in range(n))
    support=orientations(edges,quota);assert support>0
    triangles=[t for t in combinations(range(n),3) if all(e in edge_set for e in combinations(t,2))]
    observed=0;expected=Fraction(0)
    for a,b,c in triangles:
        observed+=int(((a,b) in directed and (b,c) in directed and (c,a) in directed)
                      or ((b,a) in directed and (c,b) in directed and (a,c) in directed))
        removed={(a,b),(a,c),(b,c)}
        q=list(quota)
        for v in (a,b,c):q[v]-=1
        expected+=Fraction(2*orientations(tuple(e for e in edges if e not in removed),tuple(q)),support)
    adj=np.zeros((n,n),dtype=np.int64)
    for a,b in directed:adj[a,b]=1
    assert int(np.trace(adj@adj@adj))==3*observed
    return observed,expected,support,len(triangles)

def selfcheck():
    # Every simple directed orientation without mutual edges on four labeled vertices.
    pairs=list(combinations(range(4),2));groups=defaultdict(list)
    for codes in product((0,1,2),repeat=6):
        directed=frozenset((a,b) if code==1 else (b,a) for (a,b),code in zip(pairs,codes) if code)
        edges=tuple(sorted(tuple(sorted(e)) for e in directed))
        quota=tuple(sum(a==i for a,b in directed) for i in range(4))
        observed,expected,support,triangles=measure(4,directed)
        groups[edges,quota].append((observed,expected,support))
    for values in groups.values():
        mean=Fraction(sum(v[0] for v in values),len(values))
        assert all(v[1]==mean and v[2]==len(values) for v in values)
    orientations.cache_clear()
    return {'graphs':729,'conditional_groups':len(groups),'status':'PASS'}

def main():
    here=Path(__file__).resolve().parent;archive=ROOT/'data/external/peng2024_human/data.zip'
    assert sha(archive)=='3711f8b8b911a24b0e5fd69e6e6c845f9e8601539807a9b960118c77ba5ad68d'
    save('peng2024_cycle_conditioning_contract.json',{
        'question':'Do induced one-way 3-cycles depart from the exact skeleton-and-degree-conditioned orientation reference?',
        'scope':'ER and TR separately; published monosynaptic labels; primary all pairs; sensitivity both raw codes finite',
        'null':'uniform orientations of the observed one-way dyad skeleton with each vertex outdegree fixed; mutual and absent dyads fixed',
        'preserved':'full per-vertex in/outdegree and mutual neighbors; undirected distances of existing edges; not directional cell-type mixing',
        'endpoint':'observed induced 030C cycles and exact expected count; per-patient residuals; no p-value or independent-triangle assumption',
        'method':'memoized exact orientation count; each directed cycle uses one outgoing at each vertex; remove triangle and subtract quota one; two orientations',
        'checks':'exhaust all 729 four-vertex oriented graphs and group by skeleton/degrees; direct cycle enumeration vs trace(A^3)/3',
        'limits':'conditional topology reference, no causal mechanism; known raw-missing semantics and paper edge discrepancy unresolved; TR amplitude not used',
        'archive_sha256':sha(archive),'code_sha256':sha(Path(__file__))})
    check=selfcheck();results={}
    with zipfile.ZipFile(archive) as z:
        for cohort in ('er','tr'):
            def read(name):return list(csv.DictReader(io.StringIO(z.read('data/'+name+'_'+cohort+'.csv').decode('utf-8-sig'))))
            cells={r['cellid'].replace(' ',''):r for r in read('tcell')}
            rows=read('tconnection');groups=defaultdict(list)
            for r in rows:groups[r['clusterid']].append(r)
            dm={str(int(d['data_index'])):d for d in loadmat(io.BytesIO(z.read('data/data_matrix_'+cohort+'.mat')),simplify_cells=True)['data']}
            for branch in ('published','finite_raw'):
                records=[];patients=defaultdict(lambda:[0,Fraction(0)])
                for cluster,rr in groups.items():
                    nodes=sorted({r[k] for r in rr for k in ('cellid_pre','cellid_post')})
                    lookup={(r['cellid_pre'],r['cellid_post']):r for r in rr}
                    assert len(lookup)==len(rr)
                    directed=set();excluded=0
                    for a,b in combinations(nodes,2):
                        r=lookup[a,b];rev=lookup[b,a]
                        ai=int(cells[a]['channel'])-1;bi=int(cells[b]['channel'])-1
                        m=dm[str(int(r['data_index']))]['matrix']
                        assert int(m['monosynaptic'][ai,bi])==int(r['connected'])
                        assert int(m['monosynaptic'][bi,ai])==int(rev['connected'])
                        if branch=='finite_raw' and not(np.isfinite(m['connection'][ai,bi]) and np.isfinite(m['connection'][bi,ai])):
                            excluded+=1;continue
                        if int(r['connected'])+int(rev['connected'])==1:
                            directed.add((nodes.index(a),nodes.index(b)) if r['connected']=='1' else (nodes.index(b),nodes.index(a)))
                    observed,expected,support,triangles=measure(len(nodes),frozenset(directed))
                    patient=rr[0]['patientid'];assert {r['patientid'] for r in rr}=={patient}
                    patients[patient][0]+=observed;patients[patient][1]+=expected
                    records.append({'cluster':cluster,'patient':patient,'oneway_edges':len(directed),'excluded_dyads':excluded,
                        'triangles':triangles,'observed':observed,'expected_exact':str(expected),'orientation_support':support})
                    orientations.cache_clear()
                obs=sum(r['observed'] for r in records);exp=sum((v[1] for v in patients.values()),Fraction(0))
                result={'clusters':len(records),'triangles':sum(r['triangles'] for r in records),'observed':obs,'expected_exact':str(exp),
                    'expected':float(exp),'residual':float(obs-exp),'multiple_orientation_clusters':sum(r['orientation_support']>1 for r in records),
                    'patients':{p:{'observed':v[0],'expected_exact':str(v[1]),'residual':float(v[0]-v[1])} for p,v in patients.items()},'records':records}
                results[cohort+'_'+branch]=result
                print(cohort,branch,json.dumps({k:v for k,v in result.items() if k not in ('patients','records')}),flush=True)
    save('peng2024_cycle_conditioning_result.json',{'contract_sha256':sha(here/'peng2024_cycle_conditioning_contract.json'),
        'selfcheck':check,'results':results})

if __name__=='__main__':main()
