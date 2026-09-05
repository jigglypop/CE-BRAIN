"""작은 연결 그래프에서 송신·수신 효과와 상호연결 표지의 선형 식별성을 열거한다."""
import json
from collections import Counter
from pathlib import Path
import numpy as np
from population_reciprocity import sha
from superficial_ee_eligibility import save

HERE=Path(__file__).resolve().parent
save('strength_identifiability_motifs_contract.json',{
    'question':'검출 연결의 log강도에서 송신·수신 효과와 상호연결 대비를 분리하는 최소2~4세포 패턴은 무엇인가?',
    'scope':'자기연결 없는2~4노드 모든 유향단순그래프; 실제 신규 생물 측정 아님',
    'method':'관측 edge마다 sender/receiver indicator 구성; reciprocal indicator의 열공간 밖 잔차제곱합>1e-10 여부',
    'gate':'SVD 잔차와 rank증가 판정 일치; 모든2^(n(n-1)) 그래프 검사',
    'limits':'형식적 식별성만 보장; 잡음·검출 선택·독립 동물·통계 검정력·인과 식별을 보장하지 않음',
    'code_sha256':sha(Path(__file__))})
results={}
for n in (2,3,4):
    positions=[(i,j) for i in range(n) for j in range(n) if i!=j]
    totals=Counter();identified=Counter();witness=None
    for bits in range(1<<len(positions)):
        edges=[e for k,e in enumerate(positions) if bits&(1<<k)];m=len(edges);totals[m]+=1
        if not m:continue
        z=np.array([(b,a) in edges for a,b in edges],float)
        x=np.zeros((m,2*n))
        for k,(a,b) in enumerate(edges):x[k,a]=1;x[k,n+b]=1
        u,s,_=np.linalg.svd(x,full_matrices=False);rank=int(sum(s>1e-10));q=u[:,:rank]
        rz=z-q@(q.T@z);info=float(rz@rz);can=info>1e-10
        augmented_rank=int(sum(np.linalg.svd(np.column_stack([x,z]),compute_uv=False)>1e-10))
        assert can==(augmented_rank==rank+1)
        if can:
            identified[m]+=1
            if witness is None or m<witness['edges_count']:
                witness={'edges_count':m,'edges':edges,'reciprocal_indicator':z.tolist(),
                         'residual_indicator':rz.tolist(),'information':info,'nuisance_rank':rank}
    assert sum(totals.values())==1<<(n*(n-1))
    results[str(n)]={'total_graphs':sum(totals.values()),'identifiable_graphs':sum(identified.values()),
        'by_edge_count':{str(k):{'all':v,'identifiable':identified[k]} for k,v in sorted(totals.items())},
        'minimum_witness':witness}
save('strength_identifiability_motifs_result.json',{'contract_sha256':sha(HERE/'strength_identifiability_motifs_contract.json'),
    'results':results,'verification':'PASS: exhaustive counts, SVD residual and augmented rank agree'})
print(json.dumps({k:{a:b for a,b in v.items() if a!='by_edge_count'} for k,v in results.items()},indent=2))
