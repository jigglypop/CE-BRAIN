"""Small structural regression checks. No animal observations enter training."""
from collections import Counter
import json
import numpy as np
from hpi1 import propose_path, forward, score, kernel, NEAR, FAR


def main():
    results = []
    seq = np.concatenate([NEAR, FAR] * 3)
    for seed in range(8):
        rng = np.random.default_rng(7481 + seed)
        T = rng.uniform(.1, 1., (8, 8, 8, 8))
        T /= T.sum((1, 3), keepdims=True)
        old = T.copy()
        U, event = propose_path(T, seq)
        assert U is not None and np.array_equal(T, old)
        assert U.shape == T.shape and np.isfinite(U).all() and np.min(U) >= 0
        error = float(abs(U.sum((1, 3)) - 1).max())
        assert error < 1e-12
        word = event['word']
        occurrences = Counter(tuple(seq[i:i + len(word)]) for i in range(len(seq) - len(word) + 1))
        assert occurrences[tuple(word)] == event['occurrences'] >= 2
        ids = event['reused_state_ids']
        assert len(ids) == len(set(ids)) == 6 and [x // 8 for x in ids] == word[1:]
        perm = rng.permutation(8)
        Tp = np.empty_like(T)
        Tp[perm[:, None], perm[None, :]] = T
        Up, ep = propose_path(Tp, perm[seq])
        relabel_error = float(abs(Up[perm[:, None], perm[None, :]] - U).max())
        assert ep['word'] == [int(perm[x]) for x in word] and relabel_error < 1e-12
        _, scales = forward(T, seq)
        assert abs(score(T, seq) - np.log(scales).sum()) < 1e-10
        before, _ = forward(T, seq[:20])
        full, _ = forward(T, seq)
        assert np.array_equal(before, full[:20])
        K = kernel(U, hold=.05, skip=.1, protected=True)
        kernel_error = float(abs(K.sum((1, 3)) - 1).max())
        assert np.min(K) >= 0 and kernel_error < 1e-12
        results.append(dict(seed=seed, row_error=error, relabel_error=relabel_error, kernel_error=kernel_error))
    print(json.dumps(dict(status='PASS', conditions=results, scope='Software regression only; not biological validation.'), indent=2))


if __name__ == '__main__':
    main()
