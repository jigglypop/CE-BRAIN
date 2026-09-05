"""저장 SGSG 그래프마다 같은 입출력·거리 기대값 모형을 재적합한다."""
import json
from pathlib import Path
import sys
import numpy as np
import scipy
import sgsg_stochastic_evaluation as source
from joint_degree_refit_bootstrap import refine

HERE=source.HERE
BASE=source.run.shared.source.base
STORE=BASE.ROOT/'data/external/sgsg_refit_residual'


def margins(p,a,c):
    return float(max(np.max(abs(p.sum(1)-a.sum(1))),np.max(abs(p.sum(0)-a.sum(0))),
                     np.max(abs(np.bincount(c.ravel(),weights=p.ravel(),minlength=6)-np.bincount(c[a],minlength=6)))))


def main():
    source_result=HERE/'sgsg_stochastic_evaluation_result.json'
    original_result=HERE/'joint_expected_polish_result.json'
    spec=dict(question='Does a reciprocal residual difference remain after applying the same expected-degree-and-distance reference separately to observed and SGSG graphs?',
              design='Descriptive residual comparison on the existing64synthetic graphs; not a conditional test or independent biological confirmation',
              input='All64stored stochastic-round q1.5 graphs, same347roots/coordinates; no new graph draws, tuning, or dropped samples',
              model='p_ij=expit(alpha_i+beta_j+gamma_bin); match node in/out totals and global6distance-bin totals in expectation; use frozen refine, gate max absolute margin error<=1e-5',
              statistic='R-sum_i<j p_ij*p_ji, with a separate fit for every graph. Exact degrees are not conditioned on; graph-to-graph margins remain different.',
              decomposition='ObservedR-meanGeneratedR = (observedFitMean-meanGeneratedFitMean)+(observedResidual-meanGeneratedResidual)',
              failures='Record all failures, no replacement, no pooled interpretation if any fit fails',
              inference='Report64values, mean/range/sampleSD and MCSE of mean only; no tail pvalue, causal inference, or claim that reconstruction errors are corrected',
              source_result_sha256=BASE.sha(source_result),observed_result_sha256=BASE.sha(original_result),
              source_verification_sha256=BASE.sha(HERE/'sgsg_stochastic_evaluation_verification.json'),
              fit_sha256=BASE.sha(HERE/'joint_expected_degree_reference.py'),refine_sha256=BASE.sha(HERE/'joint_degree_refit_bootstrap.py'),
              loader_sha256=BASE.sha(Path(source.__file__)),code_sha256=BASE.sha(Path(__file__)),
              python=sys.version,interpreter=sys.executable,numpy=np.__version__,scipy=scipy.__version__)
    cp=HERE/'sgsg_refit_residual_contract.json'
    source.run.shared.source.write_once(cp,spec)
    roots,xyz,observed,c=source.run.shared.source.data()
    old=json.loads(original_result.read_text())
    observed_fit=BASE.ROOT/old['fitted_file']
    assert BASE.sha(observed_fit)==old['fitted_sha256']
    with np.load(observed_fit,allow_pickle=False) as f:
        assert f['roots'].tolist()==roots
        observed_p=f['p']
    assert margins(observed_p,observed,c)<=1e-5
    observed_mean=float(np.triu(observed_p*observed_p.T,1).sum())
    assert np.isclose(observed_mean,old['reciprocal_mean'],atol=1e-10)
    observed_r=int((observed&observed.T).sum()//2)
    previous=json.loads(source_result.read_text())
    STORE.mkdir(exist_ok=True)
    records=[]
    for name,digest in sorted(previous['receipt_sha256'].items()):
        input_receipt=source.STORE/name
        assert BASE.sha(input_receipt)==digest
        info=json.loads(input_receipt.read_text())
        input_graph=input_receipt.with_suffix('.npz')
        assert BASE.sha(input_graph)==info['file_sha256']
        with np.load(input_graph,allow_pickle=False) as f:
            assert f['roots'].tolist()==roots
            a=f['adjacency']
        receipt=STORE/name; fitted_path=receipt.with_suffix('.npz')
        if receipt.exists():
            record=json.loads(receipt.read_text())
            assert record['contract_sha256']==BASE.sha(cp) and record['input_sha256']==BASE.sha(input_graph)
            if record['gate_pass']:
                assert BASE.sha(fitted_path)==record['fitted_sha256']
        else:
            try:
                p,diag=refine(a,c)
                error=margins(p,a,c)
                passed=bool(diag['gate_pass'] and error<=1e-5 and np.isfinite(p).all() and np.all((p>=0)&(p<=1)) and not np.diag(p).any())
                r=int((a&a.T).sum()//2)
                mean=float(np.triu(p*p.T,1).sum())
                record=dict(gate_pass=passed,diagnostic=diag,checked_margin_error=error,mutual=r,fit_mean=mean if passed else None,residual=r-mean if passed else None)
                if passed:
                    with fitted_path.open('xb') as stream:np.savez_compressed(stream,p=p,roots=np.array(roots,dtype=np.int64))
                    record['fitted_sha256']=BASE.sha(fitted_path)
            except Exception as exc:
                record=dict(gate_pass=False,error=repr(exc),residual=None)
            record.update(index=info['index'],input_sha256=BASE.sha(input_graph),contract_sha256=BASE.sha(cp))
            source.run.shared.source.write_once(receipt,record)
        records.append(record)
        if len(records)%8==0:print('refitted',len(records),'failed',sum(not r['gate_pass'] for r in records),flush=True)
    assert len(records)==64
    comparison=None
    if all(r['gate_pass'] for r in records):
        residuals=[r['residual'] for r in records]
        mean_r=float(np.mean([r['mutual'] for r in records]))
        mean_fit=float(np.mean([r['fit_mean'] for r in records]))
        mean_res=float(np.mean(residuals))
        residual_gap=observed_r-observed_mean-mean_res
        expected_gap=observed_mean-mean_fit
        assert np.isclose(observed_r-mean_r,expected_gap+residual_gap,atol=1e-10)
        comparison=dict(observed_mutual=observed_r,observed_fit_mean=observed_mean,observed_residual=observed_r-observed_mean,
                        generated_mean_mutual=mean_r,generated_mean_fit_mean=mean_fit,generated_residual_mean=mean_res,
                        generated_residual_range=[min(residuals),max(residuals)],generated_residual_sd=float(np.std(residuals,ddof=1)),
                        generated_residual_mc_se=float(np.std(residuals,ddof=1)/8),
                        raw_gap=observed_r-mean_r,fit_mean_gap=expected_gap,residual_gap=residual_gap,
                        max_margin_error=max(r['checked_margin_error'] for r in records))
    result=dict(contract_sha256=BASE.sha(cp),failed=sum(not r['gate_pass'] for r in records),comparison=comparison,
                records=records,receipt_sha256={p.name:BASE.sha(p) for p in sorted(STORE.glob('*.json'))},
                status='DESCRIPTIVE_REFIT_COMPARISON' if comparison else 'FIT_FAILURE_NO_POOLED_INTERPRETATION')
    source.run.shared.source.write_once(HERE/'sgsg_refit_residual_result.json',result)
    print(json.dumps({k:v for k,v in result.items() if k not in ('records','receipt_sha256')}),flush=True)


if __name__=='__main__':main()
