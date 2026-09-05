"""거리 구간이 둘인 작은 그래프 전수 열거로 평균·공분산 계산을 독립 확인한다."""
import itertools,json
from pathlib import Path
import numpy as np
from pinky_row_reference import prepare
from reference_spike_audit import sha
HERE=Path(__file__).resolve().parent
pairs=list(itertools.permutations(range(4),2))
c=(np.abs(np.arange(4)[:,None]-np.arange(4)[None,:])>=2).astype(int)
checks=[]
for original_mask in (85,99,142,731,1549):
    original=np.zeros((4,4),dtype=bool)
    for bit,p in enumerate(pairs):original[p]=bool(original_mask&(1<<bit))
    for transpose in (False,True):
        a=original.T if transpose else original
        target=tuple(sum(int(a[i,j]) for j in range(4) if i!=j and c[i,j]==b) for i in range(4) for b in range(2))
        values=[]
        for mask in range(4096):
            selected={p for bit,p in enumerate(pairs) if mask&(1<<bit)}
            signature=tuple(sum((i,j) in selected for j in range(4) if i!=j and c[i,j]==b) for i in range(4) for b in range(2))
            if signature==target:values.append(sum((v,u) in selected for u,v in selected)//2)
        _,mean,variance=prepare(a,c)
        assert abs(mean-np.mean(values))<1e-12 and abs(variance-np.var(values))<1e-12
        checks.append(dict(mask=original_mask,transpose=transpose,graphs=len(values),mean=mean,variance=variance))
receipt=dict(code_sha256=sha(Path(__file__)),target_sha256=sha(HERE/'pinky_row_reference.py'),checks=checks,status='STRATIFIED_MOMENTS_EXHAUSTIVELY_MATCH')
out=HERE/'pinky_row_moment_verification.json'
if out.exists():assert json.loads(out.read_text())==receipt
else:out.write_text(json.dumps(receipt,indent=2),encoding='utf-8')
print('TEN_STRATIFIED_CASES_EXHAUSTIVELY_MATCH')
