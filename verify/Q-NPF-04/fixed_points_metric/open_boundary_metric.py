"""Conditional port geometry and post-hoc identifiability witnesses; no new fit.

All circuit algebra uses dimensionless, real, incremental port variables.
Compensation denotes an imposed physical boundary, not centering measured current.
The observational examples reuse already-examined summaries, with no downloads.
"""
from __future__ import annotations

import hashlib
import json
import platform
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
BASE = HERE.parents[2]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def compensated_metric(points, admittance):
    """Impose sum(i)=0 on v=P*a+v0*1, with sym(Y)>0 and affine rank 4."""
    p, y = np.asarray(points, dtype=float), np.asarray(admittance, dtype=float)
    if p.ndim != 2 or p.shape[1] != 3 or y.shape != (len(p), len(p)):
        raise ValueError('Expected N-by-3 points and N-by-N admittance')
    if not np.isfinite(p).all() or not np.isfinite(y).all():
        raise ValueError('Nonfinite circuit input')
    u = np.ones(len(p))
    if np.linalg.matrix_rank(np.column_stack((p, u))) != 4:
        raise ValueError('Affine point rank must be 4')
    ys = (y+y.T)/2
    if np.linalg.eigvalsh(ys)[0] <= 0:
        raise ValueError('Symmetric incremental admittance must be positive definite')
    alpha = float(u@y@u)
    r = np.eye(len(p))-np.outer(u, u@y)/alpha
    ye = y@r
    k = p.T@((ye+ye.T)/2)@p
    d = p.T@((ye-ye.T)/2)@p
    m = k+d
    inv = np.linalg.solve(m, np.eye(3))
    g = inv.T@k@inv
    sym_row = u@ys@p
    kmin = p.T@ys@p-np.outer(sym_row, sym_row)/alpha
    skew_row = u@((y-y.T)/2)@p
    return dict(R=r, Y_eff=ye, K=k, D=d, M=m, g=g, alpha=alpha,
                K_minimum_at_fixed_gradient=kmin,
                compensation_excess_at_fixed_gradient=np.outer(skew_row, skew_row)/alpha)


def common_mode_family(delta_v, delta_i, edge_coefficient):
    """One-observation witnesses, not measured leak or synaptic conductances."""
    dv, di = np.asarray(delta_v, float), np.asarray(delta_i, float)
    if dv.ndim != 1 or di.shape != dv.shape or not len(dv):
        raise ValueError('Voltage and current vectors must have equal nonzero length')
    if not np.isfinite(dv).all() or not np.isfinite(di).all():
        raise ValueError('Nonfinite observation')
    if dv[0] == 0 or not np.allclose(dv, dv[0], rtol=1e-12, atol=0):
        raise ValueError('This witness requires a nonzero common voltage input')
    if not np.isfinite(edge_coefficient) or edge_coefficient < 0:
        raise ValueError('Edge coefficient must be finite and nonnegative')
    slopes = di/dv
    if np.any(slopes <= 0):
        raise ValueError('This passive witness requires positive port slopes')
    n = len(dv)
    return np.diag(slopes)+edge_coefficient*(n*np.eye(n)-np.ones((n, n)))


def conductance_witness(voltage_v, current_a, reversal_v):
    """Independent G_h for each state; E is a witness choice, not an estimate."""
    v, i = np.asarray(voltage_v, float), np.asarray(current_a, float)
    if v.shape != i.shape or not np.isfinite(v).all() or not np.isfinite(i).all():
        raise ValueError('Invalid state-dependent current/voltage observations')
    if not np.isfinite(reversal_v) or np.any(v == reversal_v):
        raise ValueError('Invalid reversal potential witness')
    return i/(v-reversal_v)


def no_direct_edge_example():
    p = np.vstack((np.zeros(3), np.eye(3)))
    y = np.eye(4)
    parts = compensated_metric(p, y)
    return dict(points=p, Y=y, Y_eff=parts['Y_eff'], K=parts['K'], g=parts['g'],
                expected_g=np.eye(3)+np.ones((3, 3)),
                direct_edges_at_fixed_reservoir=0,
                scope='Synthetic exact counterexample, not observed brain structure')


def observation_witness(common, annotations):
    records = common['records']
    cells = {c['cell']: c for c in annotations['cells']}
    ids = [r['cell_id'] for r in records]
    positions_m = np.array([cells[c]['position'] for c in ids])
    for r in records:
        if cells[r['cell_id']]['device'] != r['device']:
            raise ValueError('Cell/device identity mismatch')
    dv = np.array([r['command']['delta'] for r in records])
    di = np.array([r['acquisition']['delta'] for r in records])
    length_m, voltage_v, conductance_s = 100e-6, .01, 10e-9
    current_a = conductance_s*voltage_v
    p = (positions_m-positions_m[0])/length_m
    directions = []
    for pre, post in [(24114, 24118), (24119, 24115)]:
        displacement = positions_m[ids.index(post)]-positions_m[ids.index(pre)]
        directions.append(displacement/np.linalg.norm(displacement))
    witnesses = []
    for eta_ns in [0., 1., 10.]:
        y_s = common_mode_family(dv, di, eta_ns*1e-9)
        parts = compensated_metric(p, y_s/conductance_s)
        probe = np.eye(len(ids))[:, 0]*.001
        witnesses.append(dict(edge_coefficient_nS=eta_ns,
            direct_edges_at_fixed_reservoir=0 if eta_ns == 0 else len(ids)*(len(ids)-1)//2,
            Y_nS=y_s*1e9,
            common_prediction_error_pA=float(np.max(np.abs(y_s@dv-di)))*1e12,
            predicted_1mV_individual_probe_pA=(y_s@probe)*1e12,
            hypothetical_compensated_g=parts['g'],
            metric_eigenvalues=np.linalg.eigvalsh(parts['g']),
            metric_condition_number=float(np.linalg.cond(parts['g'])),
            fixed_direction_costs=[float(e@parts['g']@e) for e in directions]))
    shift_m = np.array([100e-6, 0., 0.])
    raw_j = positions_m.T@di
    translated_j = (positions_m+shift_m).T@di
    differences = []
    for first, second in zip(witnesses, witnesses[1:]):
        differences.append(dict(eta_from_nS=first['edge_coefficient_nS'],
            eta_to_nS=second['edge_coefficient_nS'],
            min_eigenvalue_of_g_decrease=float(np.linalg.eigvalsh(
                first['hypothetical_compensated_g']-second['hypothetical_compensated_g'])[0])))
    return dict(cell_ids=ids, positions_m=positions_m, dimensionless_points=p,
        affine_rank=int(np.linalg.matrix_rank(np.column_stack((p, np.ones(len(p)))))),
        scales=dict(length_m=length_m, voltage_v=voltage_v, conductance_s=conductance_s,
                    current_a=current_a, bilinear_cost_W=voltage_v*current_a),
        common_command_mV=dv*1e3, current_change_pA=di*1e12,
        total_current_change_pA=float(di.sum())*1e12,
        command_port_bilinear_proxy_pW=float(dv@di)*1e12,
        fitted_single_observation_port_slopes_nS=di/dv*1e9,
        origin_shift_um=shift_m*1e6,
        current_moment_change_pA_um=(translated_j-raw_j)*1e18,
        expected_current_moment_change_pA_um=shift_m*di.sum()*1e18,
        invisible_reciprocal_edge_parameters=len(ids)*(len(ids)-1)//2,
        directions=directions, witnesses=witnesses, metric_decreases=differences,
        scope='One already-seen common-command observation only; no full-waveform or cross-state fit',
        claim_ceiling='BIO_EVIDENCE_L1 reused clamp measurements; all candidate metrics remain L0',
        limitations=['Command is not access-corrected synaptic membrane voltage',
                    'Port slope is not an independent leak or synaptic conductance estimate',
                    'Compensated boundary has not been physically implemented in these records',
                    'The bilinear proxy reuses the same channels and is not independent power or ATP evidence',
                    'Zero-edge witness does not imply absence of the two annotated chemical synapses'])


def two_holding_witness(vc):
    groups = vc['groups']
    if len(groups) != 2:
        raise ValueError('Expected the two previously reported holding groups')
    conditions = []
    for group in groups:
        c = group['condition']
        if c['pair_id'] != 121538 or c['pre_mode'] != 'vc' or c['post_mode'] != 'vc':
            raise ValueError('Unexpected pair or clamp mode')
        if c['pre_holding_unit'] != 'V' or c['post_holding_unit'] != 'V':
            raise ValueError('Holding units must be V')
        first = next(s for s in group['analysis']['summary'] if s['pulse'] == 1)
        conditions.append(dict(sweeps=group['sweeps'],
            pre_holding_mV=1000*c['pre_holding_value'],
            pre_pulse_command_mV=1000*(c['pre_holding_value']+c['amplitudes'][0]),
            post_holding_mV=1000*c['post_holding_value'], first_pulse=first))
    v = np.array([c['post_holding_mV']/1000 for c in conditions])
    i = np.array([c['first_pulse']['mean_pA']*1e-12 for c in conditions])
    witnesses = []
    for reversal in [0., .020]:
        g = conductance_witness(v, i, reversal)
        witnesses.append(dict(reversal_mV=1000*reversal, state_conductances_nS=g*1e9,
                              reconstruction_error_pA=(g*(v-reversal)-i)*1e12))
    return dict(pair_id=121538, conditions=conditions, witnesses=witnesses,
        equal_conductance_secant_nS=float((i[1]-i[0])/(v[1]-v[0]))*1e9,
        scope='Post-hoc algebra on previously seen first-pulse means; no biological parameter estimation',
        nonidentifiability='Two currents cannot determine E, G_state1, G_state2 without additional assumptions',
        limitations=['Presynaptic holding and pulse command also change across groups',
                    'Every first-pulse trial lies inside its existing control range',
                    'First-pulse mean is not an independently isolated synaptic current',
                    'Chosen reversals are mathematical witnesses, not physiological estimates',
                    'Negative equal-G secant is not evidence for negative synaptic conductance'])


def serializable(value):
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    raise TypeError(type(value).__name__)


def main():
    files = dict(common=HERE/'allen_common_mode_result.json',
                 annotations=HERE/'allen_differential_annotations_result.json',
                 vc=HERE.parent/'allen_synphys/next_donor_vc_response_result.json')
    source = {key: json.loads(path.read_text(encoding='utf8')) for key, path in files.items()}
    result = dict(analysis_type='Post-hoc identifiability review; not preregistered or held-out validation',
        code_sha256=sha(__file__),
        test_sha256=sha(BASE/'tests/test_fixed_neuron_open_boundary.py'),
        environment=dict(python=platform.python_version(), numpy=np.__version__),
        inputs={key: dict(path=path.relative_to(BASE).as_posix(), sha256=sha(path))
                for key, path in files.items()}, new_download_bytes=0,
        no_direct_edge_example=no_direct_edge_example(),
        common_mode=observation_witness(source['common'], source['annotations']),
        two_holding=two_holding_witness(source['vc']),
        verdict='Conditional open-boundary metric constructed; actual neural metric not identified')
    output = HERE/'open_boundary_metric_result.json'
    with output.open('x', encoding='utf8', newline='\n') as handle:
        handle.write(json.dumps(result, default=serializable, ensure_ascii=False, indent=2, allow_nan=False)+'\n')
    print(json.dumps(dict(path=output.relative_to(BASE).as_posix(), sha256=sha(output),
                         verdict=result['verdict'])))


if __name__ == '__main__':
    main()
