"""전체 v185 그래프의 거리별 한쪽 차수 보존 기준. 직접 독립 표본화."""
import csv,itertools,json
from collections import Counter
from pathlib import Path
import numpy as np
from reference_spike_audit import sha
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
DATA=ROOT/'data/external/microns_pinky_v185'


def prepare(a,c):
    n=len(a);p=np.zeros((n,n));groups=[]
    for i in range(n):
        for b in range(6):
            targets=np.flatnonzero((c[i]==b)&(np.arange(n)!=i));N=len(targets)
            k=int(a[i,targets].sum())
            if N:
                p[i,targets]=k/N
                groups.append((i,b,targets,k))
    q=p*p.T
    mean=float(np.triu(q,1).sum());variance=float(np.triu(q*(1-q),1).sum())
    for i,b,targets,k in groups:
        N=len(targets)
        if N>1:
            covariance=-(k/N)*(1-k/N)/(N-1)
            w=p[targets,i]
            variance+=covariance*float(w.sum()**2-(w*w).sum())
    assert variance>=-1e-10
    return groups,mean,max(0,variance)


def fixtures():
    n=4;c=np.zeros((n,n),dtype=int)
    pairs=list(itertools.permutations(range(n),2))
    for degrees in ([1,1,1,1],[0,1,2,3],[2,2,1,0]):
        a=np.zeros((n,n),dtype=bool)
        for i,k in enumerate(degrees):a[i,[j for j in range(n) if j!=i][:k]]=True
        _,mean,var=prepare(a,c);values=[]
        for mask in range(4096):
            b=np.zeros((n,n),dtype=bool)
            for bit,pair in enumerate(pairs):b[pair]=bool(mask&(1<<bit))
            if np.array_equal(b.sum(1),degrees):values.append(int((b&b.T).sum()//2))
        assert abs(np.mean(values)-mean)<1e-12 and abs(np.var(values)-var)<1e-12


def main():
    fixtures()
    prior=json.loads((HERE/'pinky_local_contract.json').read_text())
    spec=dict(scope='same362 as-released e-labelled cells, all intercell dyads; preserve all source limitations of pinky_local_contract',
        models='outgoing:fixed per-neuron outgoing edge count in each distance bin; incoming:transpose graph then same model; neither preserves both degrees',
        sampling='uniform without replacement within each row/bin; rows/bins independent; 2000 independent graphs per setting, fixed seed2026090512',
        settings='both models x thresholds1,3 x xy voxel nm3.54,3.58; existing distance bins50,100,200,400,800um',
        moments='analytic mean=sum_i<j p_ij*p_ji; variance includes negative shared-row hypergeometric covariance; float evaluation',
        endpoints='observed, analytic mean/variance, sample mean/variance, full histogram and inclusive upper tail with MC SE; no confirmation threshold',
        gates='all four-node degree fixtures match full enumeration moments; every sample preserves row-bin counts; no loops; all files hashed',
        interpretation='new weaker conditional models, not replication of joint-degree null or independent confirmation; no biological absence assumption',
        source_sha256=prior['source_sha256'],prior_contract_sha256=sha(HERE/'pinky_local_contract.json'),code_sha256=sha(Path(__file__)))
    cp=HERE/'pinky_row_contract.json'
    if cp.exists():assert json.loads(cp.read_text())==spec
    else:cp.write_text(json.dumps(spec,indent=2),encoding='utf-8')
    for p,h in spec['source_sha256'].items():assert sha(ROOT/p)==h
    cells=sorted([r for r in csv.DictReader((DATA/'soma_valence_v185.csv').open()) if r['cell_type']=='e'],key=lambda r:int(r['pt_root_id']))
    ids={int(r['pt_root_id']):i for i,r in enumerate(cells)};assert len(ids)==362
    vox=np.array([list(map(int,r['pt_position'].strip('[]').split())) for r in cells])
    counts=np.zeros((362,362),dtype=int)
    for r in csv.DictReader((DATA/'soma_subgraph_synapses_spines_v185.csv').open()):
        u,v=ids[int(r['pre_root_id'])],ids[int(r['post_root_id'])]
        if u!=v:counts[u,v]+=1
    outputs=[]
    for xy in (3.54,3.58):
        xyz=vox*np.array([xy,xy,40])/1000
        c=np.digitize(np.linalg.norm(xyz[:,None,:]-xyz[None,:,:],axis=2),[50,100,200,400,800])
        keys=np.arange(362)[:,None]*6+c
        for threshold in (1,3):
            for model in ('outgoing','incoming'):
                a=counts>=threshold
                if model=='incoming':a=a.T
                groups,mean,var=prepare(a,c);observed=int((a&a.T).sum()//2)
                rng=np.random.default_rng(2026090512);hist=Counter();expected=np.bincount(keys[a],minlength=362*6)
                for sample in range(2000):
                    b=np.zeros_like(a)
                    for i,cat,targets,k in groups:
                        if k:b[i,rng.choice(targets,k,replace=False)]=True
                    assert np.array_equal(np.bincount(keys[b],minlength=362*6),expected) and not np.diag(b).any()
                    hist[int((b&b.T).sum()//2)]+=1
                sample_mean=sum(k*v for k,v in hist.items())/2000
                sample_var=sum((k-sample_mean)**2*v for k,v in hist.items())/2000
                exceed=sum(v for k,v in hist.items() if k>=observed);tail=exceed/2000
                entry=dict(xy_nm=xy,threshold=threshold,model=model,observed=observed,analytic_mean=mean,analytic_variance=var,
                    sample_mean=sample_mean,sample_variance=sample_var,draws=2000,exceedances=exceed,upper_tail_estimate=tail,
                    upper_tail_mc_se=float(np.sqrt(tail*(1-tail)/2000)),histogram={str(k):v for k,v in sorted(hist.items())})
                outputs.append(entry);print(json.dumps({k:v for k,v in entry.items() if k!='histogram'}),flush=True)
    result=dict(contract_sha256=sha(cp),results=outputs,status='DIRECT_INDEPENDENT_GRAPH_SAMPLING_NEW_NULL_ONLY')
    out=HERE/'pinky_row_result.json'
    if out.exists():assert json.loads(out.read_text())==result
    else:out.write_text(json.dumps(result,indent=2),encoding='utf-8')


if __name__=='__main__':main()
