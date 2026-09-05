"""pickle 함수를 실행하지 않고 사전·스칼라만 복원하는 제한 해석기."""
import json,pickletools,math
from pathlib import Path
import numpy as np
from population_reciprocity import ROOT,sha
from superficial_ee_eligibility import save
HERE=Path(__file__).resolve().parent
def decode(raw):
    stack=[];memo=[];mark=object()
    for op,arg,pos in pickletools.genops(raw):
        n=op.name
        if n in ('PROTO','FRAME'):continue
        if n=='MARK':stack.append(mark)
        elif n=='EMPTY_DICT':stack.append({})
        elif n=='EMPTY_TUPLE':stack.append(())
        elif n in ('BININT','BININT1','BININT2','BINFLOAT','SHORT_BINUNICODE','BINBYTES','SHORT_BINBYTES'):stack.append(arg)
        elif n=='NONE':stack.append(None)
        elif n in ('NEWTRUE','NEWFALSE'):stack.append(n=='NEWTRUE')
        elif n=='MEMOIZE':memo.append(stack[-1])
        elif n=='BINGET':stack.append(memo[arg])
        elif n=='STACK_GLOBAL':
            name=stack.pop();module=stack.pop();stack.append({'symbolic_global':(module,name)})
        elif n=='REDUCE':
            args=stack.pop();fn=stack.pop()
            if fn=={'symbolic_global':('collections','OrderedDict')}:
                assert args==();stack.append({})
            else:stack.append({'symbolic_reduce':fn,'arguments':args})
        elif n=='BUILD':
            state=stack.pop();assert 'symbolic_reduce' in stack[-1];stack[-1]['symbolic_state']=state
        elif n.startswith('TUPLE'):
            if n=='TUPLE':
                i=next(i for i in range(len(stack)-1,-1,-1) if stack[i] is mark);items=stack[i+1:];del stack[i:]
            else:
                k=int(n[-1]);items=stack[-k:];del stack[-k:]
            stack.append(tuple(items))
        elif n=='SETITEM':
            v=stack.pop();k=stack.pop();stack[-1][k]=v
        elif n=='SETITEMS':
            i=next(i for i in range(len(stack)-1,-1,-1) if stack[i] is mark);items=stack[i+1:];del stack[i:]
            assert len(items)%2==0
            for k,v in zip(items[::2],items[1::2]):stack[-1][k]=v
        elif n=='STOP':
            assert len(stack)==1;return stack[0]
        else:raise ValueError((n,pos))
    raise ValueError('missing STOP')
def finite(x):return isinstance(x,(int,float)) and math.isfinite(x)
def main():
    base=ROOT/'data/external/xie_icms_plasticity_2025';paths=sorted(base.glob('*_pop_coupling_control.pkl'))
    save('icms_passive_coupling_extract_contract.json',dict(code_sha256=sha(Path(__file__)),inputs={p.name:sha(p) for p in paths},
        method='Static pickle opcode interpreter. GLOBAL/REDUCE/BUILD represented symbolically, no imports or callable execution. Extract PC and normalized PC scalar dictionaries; arrays left symbolic.',
        question='Which animal/session/unit/condition scalar observations are present and finite? Preserve PL/NPL switches, no significance or biological causal interpretation.'))
    rows=[]
    for p in paths:
        obj=decode(p.read_bytes());animal=p.name.split('_')[0]
        for session,conditions in obj.items():
            for (current,channel),values in conditions.items():
                for label in ('pl','npl'):
                    pc=values[label+'_pc_dict'];norm=values[label+'_pc_norm_dict'];assert set(pc)==set(norm)
                    for uid,v in pc.items():
                        assert isinstance(v,(int,float)) and isinstance(norm[uid],(int,float,type(None)))
                        rows.append(dict(animal=animal,session=session,current=int(current),channel=int(channel),unit=int(uid),label=label,pc=float(v) if finite(v) else None,pc_norm=float(norm[uid]) if finite(norm[uid]) else None))
    summaries=[]
    for animal in sorted({r['animal'] for r in rows}):
        rr=[r for r in rows if r['animal']==animal];units={}
        for r in rr:units.setdefault((r['session'],r['unit']),set()).add(r['label'])
        summaries.append(dict(animal=animal,rows=len(rr),sessions=len({r['session'] for r in rr}),session_units=len(units),label_switch_units=sum(len(v)>1 for v in units.values()),finite_pc=sum(r['pc'] is not None for r in rr),finite_norm=sum(r['pc_norm'] is not None for r in rr),positive_pc=sum(r['pc'] is not None and r['pc']>0 for r in rr),negative_pc=sum(r['pc'] is not None and r['pc']<0 for r in rr)))
    assert len({(r['animal'],r['session'],r['current'],r['channel'],r['unit'],r['label']) for r in rows})==len(rows)
    save('icms_passive_coupling_extract_result.json',dict(rows=rows,summaries=summaries))
    print(summaries)
if __name__=='__main__':main()
