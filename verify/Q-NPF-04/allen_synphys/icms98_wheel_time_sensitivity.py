"""ICMS98 탐색적 wheel–발화 관계의 시간 구간·시행 영향 검사."""
import json
from pathlib import Path
import numpy as np
from scipy.stats import rankdata
from population_reciprocity import sha
from superficial_ee_eligibility import save
HERE=Path(__file__).resolve().parent
def read(n):return json.loads((HERE/n).read_text(encoding='utf-8'))
def correlation(x,y):
    if len(x)<3 or np.ptp(x)==0 or np.ptp(y)==0:return None
    return float(np.corrcoef(x,y)[0,1])
def spearman(x,y):return correlation(rankdata(x),rankdata(y))
def centered_ranks(x,blocks):
    ranks=rankdata(x)
    for b in np.unique(blocks):ranks[blocks==b]-=ranks[blocks==b].mean()
    return ranks
def main():
    inputs=['icms_catch_wheel_coupling_result.json','icms_supported_interval_result.json']
    save('icms98_wheel_time_sensitivity_contract.json',dict(
        code_sha256=sha(Path(__file__)),input_sha256={n:sha(HERE/n) for n in inputs},
        selection='ICMS98 existing no-response good catches, both anchors; selected after prior positive wheel association.',
        method='Reuse original four ordinal blocks from supported first400 analysis. Global ranks demeaned within block; within-block Spearman and means. Recompute Spearman after each single-trial or whole-block omission. Report lower-post-TV half in each block, floor(n/2), trial-ID ties.',
        limits='Exploratory diagnostic, not causal adjustment or independent replication. Blocks cannot remove within-block drift. No significance test.'))
    source=next(r for r in read(inputs[0])['subjects'] if r['subject']=='ICMS98')
    scope=next(r for r in read(inputs[1])['sessions'] if r['subject']=='ICMS98')
    mapping={r['trial_id']:r for r in scope['trials']}
    rows=source['trials'];ids=np.array([r['trial_id'] for r in rows]);blocks=np.array([mapping[int(i)]['block'] for i in ids])
    assert len(set(ids.tolist()))==31 and all(mapping[int(i)]['good'] and mapping[int(i)]['current']==0 for i in ids)
    results=[]
    for k in (0,1):
        x=np.array([r['variants'][k]['post']['tv'] for r in rows]);y=np.array([r['variants'][k]['mean_unit_change_hz'] for r in rows])
        groups=[]
        for b in range(4):
            ix=np.flatnonzero(blocks==b);low=sorted(ix,key=lambda i:(x[i],ids[i]))[:len(ix)//2]
            groups.append(dict(block=b,trials=len(ix),trial_ids=ids[ix].tolist(),
                tv_median=float(np.median(x[ix])),mean_firing_change=float(y[ix].mean()),
                spearman=spearman(x[ix],y[ix]),lower_half_ids=ids[low].tolist(),
                lower_half_firing_change=float(y[low].mean())))
        leave_trial=[dict(omitted_trial=int(i),spearman=spearman(x[ids!=i],y[ids!=i])) for i in ids]
        leave_block=[dict(omitted_block=b,spearman=spearman(x[blocks!=b],y[blocks!=b])) for b in range(4)]
        xc=centered_ranks(x,blocks);yc=centered_ranks(y,blocks)
        # Independent one-hot least-squares reconstruction of rank residuals.
        design=np.column_stack([blocks==b for b in range(4)]).astype(float)
        for v,res in ((x,xc),(y,yc)):
            ranks=rankdata(v);expected=ranks-design@np.linalg.lstsq(design,ranks,rcond=None)[0]
            assert np.allclose(expected,res,atol=1e-12)
        results.append(dict(anchor=('trial_start','shifted')[k],spearman=spearman(x,y),
            block_centered_rank_correlation=correlation(xc,yc),
            trial_order_tv_spearman=spearman(ids,x),trial_order_firing_spearman=spearman(ids,y),
            blocks=groups,leave_one_trial=leave_trial,leave_one_block=leave_block))
    save('icms98_wheel_time_sensitivity_result.json',dict(subject='ICMS98',summaries=results))
    for s in results:
        print(s['anchor'],'rho',s['spearman'],'centered',s['block_centered_rank_correlation'],
            'trial_omission_range',[min(v['spearman'] for v in s['leave_one_trial']),max(v['spearman'] for v in s['leave_one_trial'])])
        print('blocks',s['blocks']);print('block_omissions',s['leave_one_block'])
if __name__=='__main__':main()
