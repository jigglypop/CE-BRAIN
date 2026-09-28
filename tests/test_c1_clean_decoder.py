import numpy as np

from research import c1_12_clean_decoder as c112


class Fake:
    """Poisson counts of cells with uneven preferred directions, a bump at a random place, and global rate dips."""

    def __init__(self, seed=0, cells=30, windows=4000):
        rng = np.random.default_rng(seed)
        self.phi = np.angle(np.exp(1j * rng.vonmises(0.5, 1.5, cells)))  # 선호 방향이 한쪽으로 치우친 세포 배치
        self.theta = rng.uniform(-np.pi, np.pi, windows)
        gain = np.where(rng.random(windows) < 0.2, 0.05, 1.0)  # 창 20%는 집단 발화가 함께 준다
        rate = 1 + 20 * np.exp(5.2 * (np.cos(self.theta[None] - self.phi[:, None]) - 1))
        self.mean = rate.mean(1)
        self._counts = rng.poisson(rate * gain)

    def counts(self, edges):
        return self._counts


def test_the_clean_decoder_has_no_empty_direction_pull():
    s = Fake()
    empty = np.angle(-(s.mean * np.exp(1j * s.phi)).sum())
    low = s._counts.sum(0) < np.quantile(s._counts.sum(0), 0.1)
    edges = np.arange(s.theta.size + 1, dtype=float)
    pull = lambda f: np.cos(f(s, edges, s.mean, s.phi) - empty)[low].mean()
    assert pull(c112.excess_direction) > 0.5 and abs(pull(c112.clean_direction)) < 0.15
    ok = ~low
    assert np.cos(c112.clean_direction(s, edges, s.mean, s.phi) - s.theta)[ok].mean() > 0.7
