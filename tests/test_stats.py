import numpy as np

from research import stats


def test_cluster_bootstrap_resamples_whole_sessions():
    groups = np.repeat([3, 7, 9], [2, 3, 4])
    w = stats.cluster_bootstrap(groups, 200, np.random.default_rng(0))
    assert w.shape == (200, 9)
    for g in np.unique(groups):  # 한 세션의 사건은 같은 무게를 받는다
        assert np.all(w[:, groups == g] == w[:, groups == g][:, :1])
    assert np.all(w[:, [0, 2, 5]].sum(1) == 3)  # 세션 셋을 복원 추출


def test_precision_follows_the_rule_and_recovers_a_known_covariance():
    rng = np.random.default_rng(1)
    cov = np.array([[1.0, 0.8, 0.5], [0.8, 1.0, 0.8], [0.5, 0.8, 1.0]]) * 0.01
    boot = rng.multivariate_normal(np.zeros(3), cov, 20000)
    p, info = stats.precision(boot, 500)
    assert info["method"] == "hartlap" and np.allclose(p, info["factor"] * np.linalg.inv(cov), rtol=0.05)
    r = np.array([0.1, 0.05, -0.02])
    assert np.isclose(stats.chi2_cov(r, boot, 500), r @ p @ r)
    few, info = stats.precision(boot, 8)  # 세션 8 < 2(k + 2) = 10
    assert info["method"] == "ledoit_wolf" and 0 < info["shrinkage"] < 1 and np.all(np.linalg.eigvalsh(few) > 0)


def test_precision_stays_invertible_with_fewer_sessions_than_observables():
    rng = np.random.default_rng(2)
    sessions = rng.standard_normal((6, 10))  # 세션 6개가 관측 10개의 복제를 만든다: 순위 ≤ 5
    boot = rng.dirichlet(np.ones(6), 1000) @ sessions
    p, info = stats.precision(boot, 6)
    assert info["method"] == "ledoit_wolf" and np.all(np.linalg.eigvalsh(p) > 0)


def test_equivalence_needs_the_whole_90_percent_interval_inside_the_margin():
    rng = np.random.default_rng(3)
    assert stats.equivalence(np.exp(rng.normal(np.log(1.1), 0.05, 2000)))["passed"]
    wide = stats.equivalence(np.exp(rng.normal(0, 0.5, 2000)))
    assert not wide["passed"] and wide["spread"] > 1.5
    assert not stats.equivalence(np.exp(rng.normal(np.log(2), 0.05, 2000)))["passed"]


def test_true_model_chi2_is_near_one_only_with_the_full_covariance():
    r = stats.synthetic(sessions=31, observables=6, per=15, reps=80, draws=400)
    assert 0.75 < r["full_session"]["mean"] < 1.3
    assert r["diagonal_event"]["mean"] < 0.7 and r["diagonal_session"]["mean"] < 0.7
