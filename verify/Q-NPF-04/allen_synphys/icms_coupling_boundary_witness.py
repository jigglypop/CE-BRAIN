"""합성 경계 witness: 원거리 사건이 구간 연결 후 STPR 이웃이 되는가."""
import ast
from pathlib import Path
import numpy as np
from scipy.ndimage import gaussian_filter1d
from population_reciprocity import ROOT,sha
from superficial_ee_eligibility import save
HERE=Path(__file__).resolve().parent
def main():
    source=ROOT/'data/external/xie_icms_plasticity_2025/code/processing/pop_coupling/pop_coupling_control.py'
    save('icms_coupling_boundary_witness_contract.json',dict(code_sha256=sha(Path(__file__)),producer_sha256=sha(source),
        fixture='240 one-second retained segments starting every10s. Target spikes at end-5ms of even segments; other unit at start+5ms of odd segments. Original paired gaps9.010s; rebased gaps10ms.',
        method='Execute only AST-extracted concat_segments_rebased and compute_stpr_and_pc from reviewed producer; numpy and scipy Gaussian injected. Default1ms bins/10ms smoothing/100ms window and200 shifts seed0. Count eligible targets against original segment boundaries separately.',
        ceiling='L0 synthetic computational counterexample, not estimated contamination in real records.'))
    tree=ast.parse(source.read_text(encoding='utf-8'));names={'concat_segments_rebased','compute_stpr_and_pc'}
    nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names];assert len(nodes)==2
    ns={'np':np,'gaussian_filter1d':gaussian_filter1d}
    exec(compile(ast.Module(body=nodes,type_ignores=[]),str(source),'exec'),ns)
    segments=[(float(i*10),float(i*10+1)) for i in range(240)]
    target=np.array([segments[i][1]-.005 for i in range(0,240,2)])
    other=np.array([segments[i][0]+.005 for i in range(1,240,2)])
    assert np.allclose(other-target,9.010)
    rebased={0:ns['concat_segments_rebased'](target,segments),1:ns['concat_segments_rebased'](other,segments)}
    assert np.allclose(rebased[1]-rebased[0],.010)
    lags,stpr,pc,n_used,norm=ns['compute_stpr_and_pc'](rebased,0,rng=np.random.default_rng(0))
    eligible=sum(t-.1>=a and t+.1<=b for t,(a,b) in zip(target,segments[::2]))
    assert eligible==0 and n_used>=50 and pc>0
    original_local_pairs=sum(int(np.sum(abs(other-t)<=.1)) for t in target)
    assert original_local_pairs==0
    save('icms_coupling_boundary_witness_result.json',dict(original_gap_s=9.010,rebased_gap_s=.010,original_local_pairs=original_local_pairs,
        target_spikes=len(target),producer_used_triggers=int(n_used),within_original_segment_triggers=int(eligible),
        pc=float(pc),normalized_pc=float(norm),peak_lag_ms=float(lags[np.argmax(stpr)]*1000),
        boundary_aware_status='UNASSESSED_NO_VALID_TRIGGERS',
        interpretation='Producer includes internal-join-crossing windows; positive synthetic coupling possible without original-time local pairs. Real-record effect size unknown.',
        lags_ms=(lags*1000).tolist(),stpr=stpr.tolist()))
    print('original local pairs',original_local_pairs,'used',n_used,'boundary-valid',eligible,'pc',pc,'norm',norm,'peak_ms',lags[np.argmax(stpr)]*1000)
if __name__=='__main__':main()
