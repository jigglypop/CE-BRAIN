"""q=1.5 부근의 첫 보호 단계 선택 수를 식과 저자 함수로 대조한다."""
import json
from pathlib import Path
import warnings
import numpy as np
from scipy import sparse
import sgsg_calibration_grid as grid


def main():
    cfg, geometry, spread = grid.source.load_modules()
    roots, xyz, _, _ = grid.source.data()
    cfg['nngraph'].update(dist_neighbors=65., p_pick=.1)
    records = []
    for seed in range(2026091900, 2026091916):
        np.random.seed(seed)
        m = geometry.cand2_point_nn_matrix(xyz, **cfg['nngraph'])
        initial = sparse.eye(len(xyz), format='csr')
        candidates = initial * m.transpose() - 100 * initial
        candidates.data = np.clip(candidates.data, 0., 1.)
        candidates = candidates.tocsr()
        sums = np.asarray(candidates.sum(1)).ravel()
        capacities = np.diff(candidates.copy().astype(bool).indptr)
        # Explicit zeros must not count as positive candidates.
        capacities = np.array([np.count_nonzero(candidates.data[a:b] > 0)
                               for a,b in zip(candidates.indptr[:-1], candidates.indptr[1:])])
        by_q = {}
        for q in (1.5, 1.55):
            adjust = q / (sums + 1e-3)
            predicted = np.minimum(np.round(sums * adjust).astype(int), capacities)
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter('always')
                selected = spread._evaluate_probs_less_random(candidates, adjust=adjust)
            assert all(str(w.message) == 'invalid value encountered in divide' for w in caught)
            actual = np.asarray(selected.sum(1)).ravel().astype(int)
            assert np.array_equal(actual, predicted)
            by_q[str(q)] = dict(total_selected=int(actual.sum()),
                               per_row_count_histogram={str(int(k)):int(v) for k,v in zip(*np.unique(actual,return_counts=True))})
        records.append(dict(seed=seed, first_step=by_q))
    result = dict(code_sha256=grid.source.base.sha(Path(__file__)),
                  archive_sha256=grid.source.base.sha(grid.source.ARCHIVE),
                  local_contract_sha256=grid.source.base.sha(grid.HERE/'sgsg_local_calibration_contract.json'),
                  question='Does protected-step integer rounding create a discontinuity between q1.5 and1.55?',
                  records=records, all_first_step_counts_verified=True,
                  limitation='First step only, not a decomposition of the full-graph density difference; not a biological mechanism')
    grid.source.write_once(grid.HERE/'sgsg_rounding_diagnostic.json',result)
    print(json.dumps(result))


if __name__ == '__main__':
    main()
