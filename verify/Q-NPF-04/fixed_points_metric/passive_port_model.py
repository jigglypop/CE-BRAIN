"""Positive passive one-port admittance, fitted in VC and inverted for IC.

Y(s) = g0 + sum(gq * s*tauq/(1+s*tauq)).
Conductances: nS, voltages: mV, currents: pA, time: seconds.
This is a port-equivalent circuit, not an identified neuronal morphology.
"""
from itertools import combinations

import numpy as np
from scipy.optimize import minimize, minimize_scalar, nnls


def validate(g0, conductance, tau):
    g = np.asarray(conductance, dtype=float)
    t = np.asarray(tau, dtype=float)
    if g.ndim != 1 or g.shape != t.shape or not g.size:
        raise ValueError('Matching nonempty one-dimensional modes required')
    if not np.isfinite(g0) or g0 <= 0 or not np.isfinite(g).all() or np.any(g < 0):
        raise ValueError('Positive DC and nonnegative branch conductances required')
    if not np.isfinite(t).all() or np.any(t <= 0):
        raise ValueError('Finite positive time constants required')
    return float(g0), g, t


def vc_basis(time, onset, offset, amplitude_mV, tau):
    time = np.asarray(time, dtype=float)
    tau = np.asarray(tau, dtype=float)
    if tau.ndim != 1 or not np.isfinite(tau).all() or np.any(tau <= 0):
        raise ValueError('Positive time constants required')
    if not np.isfinite(time).all() or not onset < offset or not np.isfinite(amplitude_mV):
        raise ValueError('Finite time, amplitude and ordered pulse edges required')
    on, off = time >= onset, time >= offset
    age_on = np.maximum(time - onset, 0)
    age_off = np.maximum(time - offset, 0)
    transient = (on[:, None] * np.exp(-age_on[:, None] / tau)
                 - off[:, None] * np.exp(-age_off[:, None] / tau))
    return amplitude_mV * np.column_stack((on.astype(float) - off, transient))


def vc_prediction(time, onset, offset, amplitude_mV, g0, conductance, tau):
    g0, g, tau = validate(g0, conductance, tau)
    return vc_basis(time, onset, offset, amplitude_mV, tau) @ np.r_[g0, g]


def impedance_modes(g0, conductance, tau):
    """Return direct resistance and positive relaxation modes, mV/pA and s.

    Branch capacitor states obey xdot_q=(V-x_q)/tau_q and
    V=(I+sum(g_q*x_q))/G. A diagonal similarity makes the state matrix
    symmetric: F=-diag(1/tau)+v v^T, v=sqrt(g/(G*tau)).
    Its eigenvalues are negative for g0>0. This yields the exact inverse
    impedance, without fitting any current-clamp response.
    """
    g0, g, tau = validate(g0, conductance, tau)
    total = g0 + g.sum()
    v = np.sqrt(g / (total * tau))
    eigenvalues, eigenvectors = np.linalg.eigh(-np.diag(1 / tau) + np.outer(v, v))
    if np.any(eigenvalues >= 0):
        raise ArithmeticError('Passive inverse lost strictly stable eigenvalues')
    resistance = (eigenvectors.T @ v) ** 2 / (-eigenvalues * total)
    return {'direct_mV_per_pA': float(1 / total),
            'resistance_mV_per_pA': resistance,
            'tau_s': -1 / eigenvalues}


def ic_prediction(time, onset, offset, amplitude_pA, g0, conductance, tau,
                  bridge_MOhm=0.):
    time = np.asarray(time, dtype=float)
    if (not np.isfinite(time).all() or not onset < offset
            or not np.isfinite(amplitude_pA) or not np.isfinite(bridge_MOhm)):
        raise ValueError('Finite pulse, compensation and time required')
    modes = impedance_modes(g0, conductance, tau)
    on, off = time >= onset, time >= offset
    u = amplitude_pA * (on.astype(float) - off)
    relax = (on[:, None] * -np.expm1(-np.maximum(time-onset, 0)[:, None] / modes['tau_s'])
             - off[:, None] * -np.expm1(-np.maximum(time-offset, 0)[:, None] / modes['tau_s']))
    return ((modes['direct_mV_per_pA'] - bridge_MOhm * 1e-3) * u
            + amplitude_pA * relax @ modes['resistance_mV_per_pA'])


def voltage_control_gramian(tau, horizon_s, input_cost=1.):
    """Finite-horizon reachability for xdot=-diag(1/tau)x+(1/tau)v.

    Cost is the selected integral input_cost*v(t)^2 dt. It is not total
    electrical power, ATP cost, Fisher information, or a zero-horizon metric.
    Coincident time constants yield a rank-deficient Gramian; do not regularize
    that into a claim of independently controllable biological states.
    """
    tau = np.asarray(tau, dtype=float)
    if tau.ndim != 1 or not tau.size or not np.isfinite(tau).all() or np.any(tau <= 0):
        raise ValueError('Finite positive time constants required')
    if not np.isfinite(horizon_s) or horizon_s <= 0 or not np.isfinite(input_cost) or input_cost <= 0:
        raise ValueError('Finite positive horizon and input cost required')
    d = 1 / tau
    rates = d[:, None] + d[None, :]
    return np.outer(d, d) * -np.expm1(-rates * horizon_s) / (input_cost * rates)


def fit_vc(records, order, tau_bounds=(5e-5, .03), grid_size=None):
    """Fit only supplied training records; evaluate every model separately.

    Records contain time, current, mask, onset, offset, amplitude_mV.
    Order one follows the frozen original log-grid/scalar search. Order two
    searches every distinct pair of 31 log-grid knots, then one bounded
    local Powell refinement. No evaluation responses enter this routine.
    """
    if order not in (1, 2):
        raise ValueError('Only the prespecified one- and two-mode comparison is supported')
    lower, upper = map(float, tau_bounds)
    if not 0 < lower < upper:
        raise ValueError('Positive ordered bounds required')
    size = (161 if order == 1 else 31) if grid_size is None else int(grid_size)
    if size < 3 or not records:
        raise ValueError('At least three grid points and training records required')
    target = np.concatenate([np.asarray(r['current'])[r['mask']] for r in records])
    if not target.size or not np.isfinite(target).all():
        raise ValueError('Finite nonempty training observations required')

    def solve(log_tau):
        times = np.exp(np.atleast_1d(log_tau))
        design = np.concatenate([vc_basis(r['time'], r['onset'], r['offset'],
                                         r['amplitude_mV'], times)[r['mask']]
                                 for r in records])
        coef, _ = nnls(design, target)
        return float(np.mean((design @ coef - target) ** 2)), coef

    grid = np.linspace(np.log(lower), np.log(upper), size)
    candidates = [(i,) for i in range(size)] if order == 1 else combinations(range(size), 2)
    best = None
    for indexes in candidates:
        point = grid[list(indexes)]
        mse, coef = solve(point)
        if best is None or mse < best[0]:
            best = (mse, coef, point, indexes)
    mse, coef, point, indexes = best
    grid_mse = mse
    refined = False
    if order == 1 and 0 < indexes[0] < size - 1:
        j = indexes[0]
        optimum = minimize_scalar(lambda x: solve(x)[0], bounds=(grid[j-1], grid[j+1]),
                                  method='bounded', options={'xatol': 1e-10})
        if optimum.success and optimum.fun <= mse:
            point = np.array([optimum.x])
            mse, coef = solve(point)
            refined = True
    elif order == 2:
        bounds = [(grid[max(j-1, 0)], grid[min(j+1, size-1)]) for j in indexes]
        optimum = minimize(lambda x: solve(x)[0], point, method='Powell', bounds=bounds,
                           options={'xtol': 1e-8, 'ftol': 1e-10, 'maxiter': 80})
        if optimum.success and optimum.fun <= mse:
            point = optimum.x
            mse, coef = solve(point)
            refined = True
    order_idx = np.argsort(point)
    taus = np.exp(point[order_idx])
    conductance = coef[1:][order_idx]
    return {'order': order, 'g0_nS': float(coef[0]), 'conductance_nS': conductance.tolist(),
            'tau_s': taus.tolist(), 'train_rmse_pA': float(np.sqrt(mse)),
            'grid_train_mse': float(grid_mse), 'grid_size': size,
            'local_refinement_accepted': refined,
            'tau_bound_hit': [bool(x <= lower*(1+1e-6) or x >= upper*(1-1e-6)) for x in taus],
            'positive_dc': bool(coef[0] > 0),
            'active_transient_modes': int(np.count_nonzero(conductance > 1e-12))}
