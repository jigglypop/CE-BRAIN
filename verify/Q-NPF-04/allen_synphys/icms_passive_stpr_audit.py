"""기호 pickle에서 고정 float64 STPR만 복원하고 0지연·대칭성을 검사."""
import json,math
from pathlib import Path
import numpy as np
from icms_passive_coupling_extract import decode
from population_reciprocity import ROOT,sha
from superficial_ee_eligibility import save
HERE=Path(__file__).resolve().parent
def array(v):
    assert v['symbolic_reduce']=={'symbolic_global':('dill._dill','_create_array')}
    fn,args,state,extra=v['arguments']
    assert fn['symbolic_global'] in [('numpy._core.multiarray','_reconstruct'),('numpy.core.multiarray','_reconstruct')]
    assert args==({'symbolic_global':('numpy','ndarray')},(0,),b'b') and extra is None
    version,shape,dtype,fortran,payload=state
    assert version==1 and shape==(201,) and fortran is False and len(payload)==1608
    assert dtype['symbolic_reduce']=={'symbolic_global':('numpy','dtype')} and dtype['arguments']==('f8',False,True)
    assert dtype['symbolic_state']==(3,'<',None,None,None,-1,-1,0)
    return np.frombuffer(payload,dtype='<f8').copy()
def main():
    base=ROOT/'data/external/xie_icms_plasticity_2025';paths=sorted(base.glob('*_pop_coupling_control.pkl'))
    save('icms_passive_stpr_audit_contract.json',dict(code_sha256=sha(Path(__file__)),decoder_sha256=sha(HERE/'icms_passive_coupling_extract.py'),inputs={p.name:sha(p) for p in paths},
        method='Static decode only; accept exactly little-endian float64 201-element arrays. Verify sample100 equals saved PC. Under producer1ms lag convention compare mean +10..+100ms minus -100..-10ms; compute odd/even RMS. Preserve all missing arrays and no independent-unit inference.',
        boundary='Source-summary consistency and descriptive shape, not causal direction or synaptic delay. Time axis inferred from producer configuration; not serialized lags.'))
    rows=[];arrays={};missing=0
    for p in paths:
        animal=p.name.split('_')[0]
        for session,conditions in decode(p.read_bytes()).items():
            for (current,channel),c in conditions.items():
                for label in ('pl','npl'):
                    for uid,obj in c[label+'_stpr_dict'].items():
                        pc=c[label+'_pc_dict'][uid]
                        if obj is None:
                            assert not math.isfinite(pc);missing+=1;continue
                        a=array(obj);assert np.isfinite(a).all() and math.isclose(float(a[100]),pc,abs_tol=1e-12,rel_tol=1e-12)
                        even=(a+a[::-1])/2;odd=(a-a[::-1])/2
                        assert np.allclose(even+odd,a,rtol=1e-12,atol=1e-12)
                        key='a'+str(len(rows));arrays[key]=a
                        rows.append(dict(array_key=key,animal=animal,session=session,current=int(current),channel=int(channel),unit=int(uid),label=label,
                            pc=float(pc),post_minus_pre=float(a[110:201].mean()-a[:91].mean()),odd_rms=float(np.sqrt(np.mean(odd**2))),even_rms=float(np.sqrt(np.mean(even**2)))))
    dest=HERE/'icms_passive_stpr_arrays.npz'
    if not dest.exists():
        with dest.open('xb') as f:np.savez_compressed(f,**arrays)
    else:
        with np.load(dest,allow_pickle=False) as prior:assert all(np.array_equal(prior[k],v) for k,v in arrays.items())
    summaries=[]
    for animal in sorted({r['animal'] for r in rows}):
        rr=[r for r in rows if r['animal']==animal]
        summaries.append(dict(animal=animal,arrays=len(rr),positive_asymmetry=sum(r['post_minus_pre']>0 for r in rr),negative_asymmetry=sum(r['post_minus_pre']<0 for r in rr),median_asymmetry=float(np.median([r['post_minus_pre'] for r in rr])),odd_dominant=sum(r['odd_rms']>r['even_rms'] for r in rr)))
    save('icms_passive_stpr_audit_result.json',dict(missing_arrays=missing,finite_arrays=len(rows),zero_lag_matches=len(rows),arrays_sha256=sha(dest),rows=rows,summaries=summaries))
    print('finite',len(rows),'missing',missing,'all zero-lag values match')
    print(summaries)
if __name__=='__main__':main()
