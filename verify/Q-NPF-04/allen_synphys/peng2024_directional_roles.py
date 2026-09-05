"""세포별 순출력 제곱합을 같은 연결쌍의 독립 방향 기준과 비교한다."""
import csv
import io
import json
import zipfile
from collections import defaultdict
from itertools import combinations,product
from pathlib import Path
import numpy as np
from scipy.io import loadmat
from population_reciprocity import ROOT,sha
from superficial_ee_eligibility import save

def score(n,edges):
    net=[0]*n;degree=[0]*n
    for a,b in edges:
        net[a]+=1;net[b]-=1;degree[a]+=1;degree[b]+=1
    value=sum(x*x for x in net)
    expected=2*len(edges)
    variance=4*sum(d*(d-1)//2 for d in degree)
    # Independent equivalent sum over pairs of incident edge signs.
    wedge=0
    for v in range(n):
        signs=[1 if a==v else -1 for a,b in edges if v in (a,b)]
        wedge+=sum(a*b for a,b in combinations(signs,2))
    assert value==expected+2*wedge and sum(net)==0
    return value,expected,variance

def check():
    pairs=list(combinations(range(4),2));tested=0
    for mask in product((0,1),repeat=6):
        skeleton=[e for e,on in zip(pairs,mask) if on]
        values=[]
        for directions in product((0,1),repeat=len(skeleton)):
            graph=[e if bit==0 else e[::-1] for e,bit in zip(skeleton,directions)]
            value,expected,variance=score(4,graph);values.append(value);tested+=1
        assert np.mean(values)==expected and np.var(values)==variance
    return {'skeletons':64,'orientations':tested,'status':'PASS'}

def main():
    here=Path(__file__).resolve().parent;archive=ROOT/'data/external/peng2024_human/data.zip'
    assert sha(archive)=='3711f8b8b911a24b0e5fd69e6e6c845f9e8601539807a9b960118c77ba5ad68d'
    save('peng2024_directional_roles_contract.json',{
        'question':'Within recorded human microcircuits, is input/output imbalance larger than independent fair orientations of the same one-way edges?',
        'endpoint':'S=sum_v(out_v-in_v)^2; E[S]=2m; Var[S]=4 sum_v choose(degree_v,2)',
        'null':'Each one-way dyad independently oriented with probability 1/2; preserve skeleton, mutual/absent dyads and undirected edge distances; do not preserve directed degree',
        'scope':'ER/TR separate; published and both-raw-finite branches; all clusters; no amplitude selection',
        'patient':'sum observed and expected per patient; number positive and delete-one-patient total residual; no pooled p-value',
        'verification':'all 64 four-node skeletons and 729 orientations reproduce expectation/variance; independent signed-wedge identity per real graph',
        'limits':'observational L1; measurement asymmetry and laminar order are alternatives to intrinsic cell roles; prior topology result motivated endpoint',
        'archive_sha256':sha(archive),'code_sha256':sha(Path(__file__))})
    selfcheck=check();results={}
    with zipfile.ZipFile(archive) as z:
        for cohort in ('er','tr'):
            def read(prefix):return list(csv.DictReader(io.StringIO(z.read('data/'+prefix+'_'+cohort+'.csv').decode('utf-8-sig'))))
            cells={r['cellid'].replace(' ',''):r for r in read('tcell')}
            groups=defaultdict(list)
            for r in read('tconnection'):groups[r['clusterid']].append(r)
            dm={str(int(d['data_index'])):d for d in loadmat(io.BytesIO(z.read('data/data_matrix_'+cohort+'.mat')),simplify_cells=True)['data']}
            for branch in ('published','finite_raw'):
                records=[];patients=defaultdict(lambda:[0,0])
                for cluster,rows in groups.items():
                    nodes=sorted({r[k] for r in rows for k in ('cellid_pre','cellid_post')})
                    lookup={(r['cellid_pre'],r['cellid_post']):r for r in rows};edges=[];excluded=0
                    assert len(lookup)==len(rows)
                    for a,b in combinations(nodes,2):
                        r=lookup[a,b];rev=lookup[b,a]
                        ai=int(cells[a]['channel'])-1;bi=int(cells[b]['channel'])-1
                        mat=dm[str(int(r['data_index']))]['matrix']
                        assert int(mat['monosynaptic'][ai,bi])==int(r['connected']) and int(mat['monosynaptic'][bi,ai])==int(rev['connected'])
                        if branch=='finite_raw' and not(np.isfinite(mat['connection'][ai,bi]) and np.isfinite(mat['connection'][bi,ai])):
                            excluded+=1;continue
                        if int(r['connected'])+int(rev['connected'])==1:
                            edges.append((nodes.index(a),nodes.index(b)) if r['connected']=='1' else (nodes.index(b),nodes.index(a)))
                    observed,expected,variance=score(len(nodes),edges)
                    patient=rows[0]['patientid'];assert {r['patientid'] for r in rows}=={patient}
                    patients[patient][0]+=observed;patients[patient][1]+=expected
                    records.append({'cluster':cluster,'patient':patient,'oneway_edges':len(edges),'excluded_dyads':excluded,
                        'observed':observed,'expected':expected,'null_variance':variance})
                obs=sum(r['observed'] for r in records);exp=sum(r['expected'] for r in records)
                residuals=[v[0]-v[1] for v in patients.values()]
                results[cohort+'_'+branch]={'clusters':len(records),'patients':len(patients),'observed':obs,'expected':exp,
                    'ratio':obs/exp,'residual':obs-exp,'patients_positive':sum(v>0 for v in residuals),
                    'patients_zero':sum(v==0 for v in residuals),'delete_one_patient_residual_range':[obs-exp-max(residuals),obs-exp-min(residuals)],
                    'patients_detail':{p:{'observed':v[0],'expected':v[1]} for p,v in patients.items()},'records':records}
    save('peng2024_directional_roles_result.json',{'contract_sha256':sha(here/'peng2024_directional_roles_contract.json'),
        'selfcheck':selfcheck,'results':results})
    print(json.dumps({k:{a:b for a,b in v.items() if a not in ('records','patients_detail')} for k,v in results.items()},indent=2))

if __name__=='__main__':main()
