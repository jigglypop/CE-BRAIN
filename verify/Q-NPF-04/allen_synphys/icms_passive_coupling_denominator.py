"""저장된 PC/PCnorm의 분모 복원과 집단 차이 방향 변화 감사."""
import json,math
from pathlib import Path
from statistics import median
from population_reciprocity import sha
from superficial_ee_eligibility import save
HERE=Path(__file__).resolve().parent
def read(n):return json.loads((HERE/n).read_text(encoding='utf-8'))
def sign(v):return (v>0)-(v<0)
def main():
    inputs=['icms_passive_coupling_extract_result.json','icms_passive_coupling_matched_v2_result.json']
    save('icms_passive_coupling_denominator_contract.json',dict(code_sha256=sha(Path(__file__)),inputs={n:sha(HERE/n) for n in inputs},
        method='For finite nonzero PCnorm recover denominator=PC/PCnorm, require positive finite value. Zero/zero is unidentifiable. For matched conditions report PL/NPL denominator medians and span, and contrast after a single pooled median denominator. No reclassification or row removal.',
        limitation='Algebraic reconstruction, not an independent validation of shuffle distribution; common-denominator comparison is diagnostic not replacement estimator.'))
    rows=read(inputs[0])['rows'];derived=[];lookup={}
    for r in rows:
        v=dict(r);a,b=r['pc'],r['pc_norm']
        if a is None or b is None:v.update(denominator=None,status='NONFINITE_INPUT')
        elif b==0:v.update(denominator=None,status='UNIDENTIFIABLE_ZERO' if a==0 else 'INCONSISTENT_ZERO')
        else:
            d=a/b
            assert math.isfinite(d) and d>0
            assert math.isclose(a/d,b,rel_tol=1e-12,abs_tol=1e-12)
            v.update(denominator=d,status='RECOVERED')
        derived.append(v);lookup[(r['animal'],r['session'],r['current'],r['channel'],r['unit'],r['label'])]=v
    conditions=[]
    for c in read(inputs[1])['conditions']:
        if c['status']!='DEFINED':continue
        groups={label:[lookup[(c['animal'],c['session'],c['current'],c['channel'],u,label)] for u in c['units'][label]] for label in ('pl','npl')}
        v={k:c[k] for k in ('animal','session','current','channel')};v['raw_difference']=c['pc']['npl_minus_pl'];v['normalized_difference']=c['pc_norm']['npl_minus_pl'];v['direction_changed']=sign(v['raw_difference'])!=sign(v['normalized_difference'])
        if any(r['denominator'] is None for rr in groups.values() for r in rr):v['status']='DENOMINATOR_INCOMPLETE'
        else:
            ds=[r['denominator'] for rr in groups.values() for r in rr];common=median(ds)
            common_difference=median(r['pc']/common for r in groups['npl'])-median(r['pc']/common for r in groups['pl'])
            assert math.isclose(common_difference,v['raw_difference']/common,rel_tol=1e-10,abs_tol=1e-10)
            v.update(status='RECOVERED',denominator_medians={label:median(r['denominator'] for r in rr) for label,rr in groups.items()},
                denominator_range=[min(ds),max(ds)],common_denominator=common,common_denominator_difference=common_difference)
        conditions.append(v)
    statuses={s:sum(r['status']==s for r in derived) for s in sorted({r['status'] for r in derived})}
    save('icms_passive_coupling_denominator_result.json',dict(statuses=statuses,rows=derived,conditions=conditions))
    print(statuses)
    for c in conditions:
        if c['direction_changed']:print(c)
if __name__=='__main__':main()
