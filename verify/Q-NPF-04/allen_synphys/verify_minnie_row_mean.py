"""주 23P 결과의 평균을 유리수 쌍별 확률 합으로 대조한다."""
import json,math
from fractions import Fraction
from pathlib import Path
import numpy as np
import microns_constrained_swaps as base
HERE=Path(__file__).resolve().parent
rp=HERE/'minnie_matched_row_result.json'
r=json.loads(rp.read_text());full,cats=base.load_graph()
roots=json.loads(base.SELECTED.read_text())['selected_roots'];index={v:i for i,v in enumerate(roots)}
ids=[index[v] for v in r['selected_roots']['23P']]
matrix=full[np.ix_(ids,ids)];c=cats[np.ix_(ids,ids)]%6;n=len(ids);checks=[]
for record in r['results']:
    if record['scope']!='23P':continue
    a=matrix>=record['threshold']
    if record['model']=='incoming':a=a.T
    probabilities=[]
    for i in range(n):
        bybin={}
        for b in range(6):
            targets=[j for j in range(n) if j!=i and c[i,j]==b]
            bybin[b]=Fraction(sum(int(a[i,j]) for j in targets),len(targets)) if targets else Fraction(0)
        probabilities.append(bybin)
    exact=sum((probabilities[i][int(c[i,j])]*probabilities[j][int(c[j,i])] for i in range(n) for j in range(i+1,n)),Fraction(0))
    assert abs(float(exact)-record['analytic_mean'])<1e-10
    h={int(k):v for k,v in record['histogram'].items()}
    assert sum(h.values())==2000 and sum(v for k,v in h.items() if k>=record['observed'])==record['exceedances']
    checks.append(dict(threshold=record['threshold'],model=record['model'],exact_mean=str(exact),
        zero_exceedance_mc_upper95=(-math.expm1(math.log(.05)/2000)) if record['exceedances']==0 else None))
out=HERE/'minnie_row_mean_verification.json'
receipt=dict(result_sha256=base.sha(rp),verifier_sha256=base.sha(Path(__file__)),checks=checks,status='RATIONAL_PRIMARY_MEANS_AND_HISTOGRAMS_MATCH')
if out.exists():assert json.loads(out.read_text())==receipt
else:out.write_text(json.dumps(receipt,indent=2),encoding='utf-8')
print('FOUR_PRIMARY_RATIONAL_MEANS_AND_HISTOGRAMS_MATCH')
