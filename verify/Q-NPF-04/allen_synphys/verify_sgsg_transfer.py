"""저장 그래프와 저자 코드 재실행을 대조하고 영합 행 경고를 추적한다."""
import json
import warnings
from pathlib import Path
import numpy as np
import sgsg_fixed_transfer_seed32 as run


def main():
    config, geometry, spread = run.load_modules()
    roots, xyz, observed, bins = run.data()
    result_path = run.HERE / 'sgsg_fixed_transfer_seed32_result.json'
    result = json.loads(result_path.read_text())
    original = spread._evaluate_probs_less_random
    diagnostic = dict(zero_sum_rows=0, positive_pick_rows=0)

    def checked(p_mat, adjust=None):
        matrix = p_mat.tocsr()
        sums = np.asarray(matrix.sum(axis=1)).ravel()
        assert np.isfinite(matrix.data).all() and (matrix.data >= 0).all()
        scaled = sums if adjust is None else sums * adjust
        assert np.isfinite(scaled).all()
        picks = np.round(scaled).astype(int)
        # A zero denominator must never reach numpy.random.choice.
        assert np.all(picks[sums == 0] == 0)
        assert np.all(sums[picks > 0] > 0)
        diagnostic['zero_sum_rows'] += int(np.sum(sums == 0))
        diagnostic['positive_pick_rows'] += int(np.sum(picks > 0))
        return original(p_mat, adjust=adjust)

    spread._evaluate_probs_less_random = checked
    verified = []
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        for record in result['records']:
            assert record['status'] == 'PASS'
            path = run.STORE / f'{record["seed"]}.npz'
            assert run.base.sha(path) == record['file_sha256']
            with np.load(path, allow_pickle=False) as saved:
                a = saved['adjacency']
                assert saved['roots'].tolist() == roots and np.array_equal(saved['xyz'], xyz)
            assert a.dtype == bool and not np.diag(a).any()
            # Independent direct pair counting, not the production vectorized sum.
            mutual = sum(bool(a[i, j] and a[j, i]) for i in range(len(a)) for j in range(i + 1, len(a)))
            assert mutual == record['summary']['reciprocal_pairs']
            assert int(np.count_nonzero(a)) == record['summary']['edges']
            np.random.seed(record['seed'])
            m = geometry.cand2_point_nn_matrix(xyz, **config['nngraph'])
            generated, history, _ = spread.build_instance(xyz, m, **config['instance'])
            assert np.isfinite(generated.data).all() and np.isfinite(history).all()
            assert np.array_equal(generated.toarray(), a)
            assert list(history) == record['history']
            verified.append(record['seed'])
    messages = sorted({str(w.message) for w in caught})
    assert messages == ['invalid value encountered in divide'], messages
    outcome = dict(result_sha256=run.base.sha(result_path), verifier_sha256=run.base.sha(Path(__file__)),
                   replayed_seeds=verified, direct_pair_counts_match=True,
                   warnings=messages, warning_events=len(caught), diagnostic=diagnostic,
                   interpretation='Zero-sum candidate rows divide by zero internally but have zero picks and never call random.choice; finite emitted graph and exact replay verified. Source preserved.',
                   biological_validation=False)
    run.write_once(run.HERE / 'sgsg_transfer_verification.json', outcome)
    print(json.dumps(outcome))


if __name__ == '__main__':
    main()
