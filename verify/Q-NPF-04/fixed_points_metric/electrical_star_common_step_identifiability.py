"""Exact conditional identification example for a common voltage step.

Ideal baseline-subtracted currents are divided by the nonzero voltage step.
C is positive diagonal, G symmetric positive definite, and E is diagonal
positive series resistance plus nonnegative rank-one reference resistance.
No measurement filter, parasitic current, or unknown initial state is included.
"""
import hashlib
import json
from pathlib import Path

import sympy as sp

HERE = Path(__file__).resolve().parent
OUTPUT = HERE / 'electrical_star_common_step_identifiability_result.json'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def step_observables(E, C, G):
    n = E.rows
    one = sp.ones(n, 1)
    A = E.inv() * C.inv() * (sp.eye(n) + G * E)
    i0 = E.inv() * one
    steady = (sp.eye(n) + G * E).inv() * G * one
    derivative0 = -E.inv() * C.inv() * i0
    assert sp.simplify(-A * (i0 - steady) - derivative0) == sp.zeros(n, 1)
    return A, i0, steady, derivative0


def candidate_family(A, i0, derivative0, alpha):
    n = A.rows
    S = sum(i0)
    E = alpha * sp.diag(*[1 / v for v in i0]) + (1 - alpha) * sp.ones(n) / S
    voltage_derivative = E * derivative0
    C = sp.diag(*[sp.factor(-i0[k] / voltage_derivative[k]) for k in range(n)])
    G = (C * E * A * E.inv() - E.inv()).applyfunc(sp.factor)
    return E, C, G


def exact_example():
    alpha = sp.Symbol('alpha', real=True)
    reference = sp.Rational(2, 5)
    E = sp.diag(2, 3) + reference * sp.ones(2)
    C = sp.diag(sp.Rational(1, 2), sp.Rational(4, 5))
    G = sp.Matrix([[1, -sp.Rational(1, 5)], [-sp.Rational(1, 5), sp.Rational(7, 10)]])
    A, i0, steady, derivative0 = step_observables(E, C, G)
    krylov = sp.Matrix.hstack(derivative0, A * derivative0)
    Et, Ct, Gt = candidate_family(A, i0, derivative0, alpha)
    skew = sp.factor(Gt[0, 1] - Gt[1, 0])
    roots = sp.solve(sp.together(skew).as_numer_denom()[0], alpha)
    admissible = [r for r in roots if 0 < r <= 1]
    return dict(alpha=alpha, E=E, C=C, G=G, A=A, i0=i0, steady=steady,
                derivative0=derivative0, krylov=krylov, candidate_E=Et,
                candidate_C=Ct, candidate_G=Gt, skew=skew,
                roots=roots, admissible_roots=admissible)


def main():
    if OUTPUT.exists():
        raise FileExistsError(OUTPUT)
    code_hash = sha(__file__)
    example = exact_example()
    alpha = example['alpha']
    unique = example['admissible_roots'] == [sp.Rational(3, 4)]
    root = example['admissible_roots'][0]
    recovered = {name: example['candidate_' + name].subs(alpha, root) == example[name] for name in ('E', 'C', 'G')}
    # A symmetric equal-cell common mode does not span both dynamical modes.
    _, _, _, d_equal = step_observables(sp.eye(2), sp.eye(2), sp.Matrix([[2, -1], [-1, 2]]))
    A_equal = sp.Matrix([[3, -1], [-1, 3]])
    equal_rank = sp.Matrix.hstack(d_equal, A_equal * d_equal).rank()
    result = dict(code_sha256=code_hash, sympy_version=sp.__version__,
        stage='Exact rational synthetic example and conditional algebra, BIO_EVIDENCE_L0',
        required_assumptions=['Known ideal common voltage step u != 0; baseline-subtracted current divided by u',
            'Initial incremental membrane voltage equals zero; no filter or extra parasitic current',
            'C positive diagonal, G symmetric positive definite, E=diag(Rs)+r_ref*ones with Rs>0 and r_ref>=0',
            'Exact derivative trajectory spans all n modes so A is identifiable',
            'Instantaneous i0 has all positive entries; admissible candidate C and G remain positive'],
        exact_matrices={name: [[str(v) for v in row] for row in example[name].tolist()] for name in
            ('E', 'C', 'G', 'A', 'i0', 'steady', 'derivative0', 'candidate_E', 'candidate_C', 'candidate_G')},
        krylov_determinant=str(sp.factor(example['krylov'].det())),
        candidate_G12_minus_G21=str(example['skew']), roots=[str(v) for v in example['roots']],
        admissible_alpha_interval='0 < alpha <= 1', admissible_roots=[str(v) for v in example['admissible_roots']],
        exactly_one_admissible_root=unique, exact_parameter_recovery=recovered,
        equal_cell_common_mode_krylov_rank=equal_rank,
        conclusion='One common input CAN identify this heterogeneous two-cell circuit under the stated exact observation and reciprocity assumptions. This is not global identifiability of every circuit.',
        limitations=['The selected real TP data have not been shown to satisfy full-mode observability or the ideal observation model',
            'Stored finite-window peak must not be substituted for ideal i(0+)',
            'No real Rs, C, G, spatial metric, or independent directional cost is estimated here'])
    assert example['krylov'].det() != 0 and unique and all(recovered.values()) and equal_rank == 1
    assert sha(__file__) == code_hash
    with OUTPUT.open('x', encoding='utf8') as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write('\n')
    print('KRYLOV_DET', result['krylov_determinant'])
    print('SKEW', result['candidate_G12_minus_G21'])
    print('ADMISSIBLE_ROOTS', result['admissible_roots'], 'RECOVERY', recovered)
    print('SHA256', sha(OUTPUT))


if __name__ == '__main__':
    main()
