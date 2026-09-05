"""고정 물리 좌표에서 소모 성분과 총전류의 전력 비용을 구별한다."""
import hashlib
import json
import sys
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent


def current_metric(K, D):
    inverse = np.linalg.inv(K+D)
    return inverse.T@K@inverse


def main():
    contract_path = HERE/'contract.json'
    c = json.loads(contract_path.read_text(encoding='utf-8'))
    tol = c['tolerance']
    fixture = c['fixture']
    p = np.array(fixture['points'], dtype=float)
    edges = fixture['edges']
    b = np.zeros((6,4))
    for row,(i,j) in enumerate(edges): b[row,i] = -1; b[row,j] = 1
    k = np.array(fixture['edge_k'])
    lap = b.T@np.diag(k)@b
    s = np.zeros((4,4))
    for cycle,strength in fixture['cycles']:
        for i,j in zip(cycle,cycle[1:]+cycle[:1]): s[i,j] += strength; s[j,i] -= strength
    y = lap+s
    assert np.max(np.abs(s+s.T)) < tol and np.max(np.abs(s.sum(axis=1))) < tol
    assert np.max((y-np.diag(np.diag(y)))) <= tol
    K = p.T@lap@p; D = p.T@s@p
    assert np.linalg.eigvalsh(K).min() > 0
    g = np.linalg.inv(K)
    gc = current_metric(K, D)
    assert np.linalg.eigvalsh(g).min() > 0 and np.linalg.eigvalsh(gc).min() > 0
    probes = np.array(fixture['probes'])
    voltages = p@probes.T
    power = np.einsum('ij,ij->j',voltages,y@voltages)
    recovered = np.diag(power[:3])
    for t,(i,j) in enumerate([(0,1),(0,2),(1,2)],3):
        recovered[i,j] = recovered[j,i] = (power[t]-power[i]-power[j])/2
    metric_error = float(np.max(np.abs(recovered-K)))
    displacements = b@p
    design = np.array([[d[0]**2,d[1]**2,d[2]**2,2*d[0]*d[1],2*d[0]*d[2],2*d[1]*d[2]] for d in probes])
    assert np.linalg.matrix_rank(design) == 6
    # 고정된 여섯 간선의 외적이 이 배치에서 독립인지 별도로 확인한다.
    edge_design = np.column_stack([np.outer(d,d)[np.triu_indices(3)] for d in displacements])
    assert np.linalg.matrix_rank(edge_design) == 6
    recovered_k = np.linalg.solve(edge_design,recovered[np.triu_indices(3)])
    k_error = float(np.max(np.abs(recovered_k-k)))
    M = p.T@(y@voltages[:,:3])
    symmetric_error = float(np.max(np.abs((M+M.T)/2-K)))
    skew_error = float(np.max(np.abs((M-M.T)/2-D)))
    reversed_y = lap-s
    reversed_power = np.einsum('ij,ij->j',voltages,reversed_y@voltages)
    power_reversal_error = float(np.max(np.abs(power-reversed_power)))
    current_reversal_change = float(np.linalg.norm(p.T@(y-reversed_y)@p))
    current_metric_reversal_error = float(np.max(np.abs(gc-current_metric(K,-D))))
    current_metric_direction_change = float(np.linalg.norm(gc-current_metric(K,np.zeros_like(D))))
    current_metric_identity_error = float(np.max(np.abs(gc-np.linalg.inv(K-D@g@D))))
    h = c['finite_difference_step']; d = displacements[fixture['sensitivity_edge_index']]; outer = np.outer(d,d)
    analytic = -g@outer@g
    finite = (np.linalg.inv(K+h*outer)-np.linalg.inv(K-h*outer))/(2*h)
    derivative_error = float(np.max(np.abs(analytic-finite)))
    inverse = np.linalg.inv(M)
    analytic_current = -inverse.T@outer@gc-gc@outer@inverse+inverse.T@outer@inverse
    finite_current = (current_metric(K+h*outer,D)-current_metric(K-h*outer,D))/(2*h)
    current_derivative_error = float(np.max(np.abs(analytic_current-finite_current)))
    # 순환 크기 t를 바꾸는 경로 D(t)=tD에서 t=1의 민감도.
    analytic_cycle = inverse.T@D@gc-gc@D@inverse
    finite_cycle = (current_metric(K,(1+h)*D)-current_metric(K,(1-h)*D))/(2*h)
    cycle_derivative_error = float(np.max(np.abs(analytic_cycle-finite_cycle)))
    transform = np.array(fixture['coordinate_transform'])
    pp = p@transform.T
    gp = np.linalg.inv(pp.T@lap@pp)
    gcp = current_metric(pp.T@lap@pp,pp.T@s@pp)
    v = np.array(fixture['fixed_current']); vp = transform@v
    coordinate_error = float(abs(v@g@v-vp@gp@vp))
    current_coordinate_error = float(abs(v@gc@v-vp@gcp@vp))
    required_gradient = np.linalg.solve(M,v)
    required_voltage = p@required_gradient
    direct_power = float(required_voltage@y@required_voltage)
    current_power_error = float(abs(direct_power-v@gc@v))
    current_reconstruction_error = float(np.max(np.abs(gc-current_metric((M+M.T)/2,(M-M.T)/2))))
    flat = p.copy();flat[:,2] = 0
    flat_rank = int(np.linalg.matrix_rank(flat.T@lap@flat))
    assert flat_rank < 3  # 여기서는 역행렬이나 ridge를 계산하지 않는다.
    # 측정 이득이 미지이면 두 다른 연결망이 같은 전류를 낼 수 있다.
    gain_ambiguity_error = float(np.max(np.abs(y-.5*(2*lap+2*s))))
    errors = dict(metric_reconstruction=metric_error,edge_reconstruction=k_error,
                  symmetric_separation=symmetric_error,skew_separation=skew_error,
                  power_reversal=power_reversal_error,derivative=derivative_error,
                  coordinate_invariance=coordinate_error,gain_ambiguity=gain_ambiguity_error,
                  current_metric_reversal=current_metric_reversal_error,
                  current_metric_identity=current_metric_identity_error,
                  current_metric_reconstruction=current_reconstruction_error,
                  current_derivative=current_derivative_error,cycle_derivative=cycle_derivative_error,
                  current_coordinate_invariance=current_coordinate_error,current_power=current_power_error)
    assert max(errors.values()) < tol
    assert current_reversal_change > fixture['minimum_direction_response_change']
    assert current_metric_direction_change > tol
    result = {'contract_sha256':hashlib.sha256(contract_path.read_bytes()).hexdigest(),
              'code_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'runtime':{'executable':sys.executable,'python':sys.version,'numpy':np.__version__},
              'points':p.tolist(),'edge_k':k.tolist(),'K':K.tolist(),'g_passive':g.tolist(),'g_current':gc.tolist(),'D':D.tolist(),
              'eigenvalues_K':np.linalg.eigvalsh(K).tolist(),'eigenvalues_g_current':np.linalg.eigvalsh(gc).tolist(),
              'power_probe_rank':int(np.linalg.matrix_rank(design)),
              'axes_only_rank':int(np.linalg.matrix_rank(design[:3])),
              'planar_rank':flat_rank,'current_reversal_change':current_reversal_change,
              'current_metric_direction_change':current_metric_direction_change,
              'fixed_current_power':direct_power,
              'cycle_derivative_norm':float(np.linalg.norm(analytic_cycle)),
              'probe_condition_number':float(np.linalg.cond(design)),
              'edge_condition_number':float(np.linalg.cond(edge_design)),
              'response_condition_number':float(np.linalg.cond(M)),
              'errors':errors,'passed':True,'claim_ceiling':c['claim_ceiling'],'limits':c['limits']}
    output = HERE/'result.json'
    with output.open('x',encoding='utf-8') as f: json.dump(result,f,ensure_ascii=False,indent=2,allow_nan=False)
    print(json.dumps({k:result[k] for k in ['eigenvalues_K','eigenvalues_g_current','power_probe_rank','axes_only_rank','planar_rank','current_reversal_change','current_metric_direction_change','cycle_derivative_norm','errors','passed']}))


if __name__ == '__main__': main()
