"""재판정 단계(C3-1r, C1-4r, C1-6r, C1-8r)의 계산을 합성 자료로 검사한다. 관측값은 원래 단계와 같고 오차만 바뀌어야 한다."""

import numpy as np

from research import c1_4_common_trace_time as c14
from research import c1_4r_common_trace_time as c14r
from research import c1_5_common_equation_v2 as c15
from research import c1_6r_common_equation_precise as c16r
from research import c1_8r_joint_v3 as c18r
from research import c3_1_sleep_trace as c31
from research import c3_1r_sleep_trace as c31r
from research import ring
from tests.test_c1_equation_v2 import synthetic as ring_events
from tests.test_c1_trace_time import synthetic as trace_sessions
from tests.test_c3_trace import simulate


def test_c3_1r_keeps_the_alignment_and_judges_the_trace_with_the_full_covariance():
    pool = c31.Pool([c31.events(*simulate(seed=s, events=30)) for s in range(6)])
    old, new = c31.analyse(pool), c31r.analyse(pool)
    assert np.allclose(old["alignment"], new["alignment"]) and old["first_bin_null_top"] == new["first_bin_null_top"]
    assert new["sessions"] == 6 and new["precision"]["method"] == "ledoit_wolf"
    assert new["alignment"][0] > new["first_bin_null_top"] and new["chi2_trace"] <= c31.CHI2 < new["chi2_none"]
    assert 30 < new["tau_s"] < 120


def test_c1_4r_keeps_the_alignment_and_tests_equivalence_of_tau():
    same = [c14.cohort(trace_sessions(300, 400, 3000, sessions=20, seed=s)) for s in (1, 2)]
    assert np.allclose(c14.curve(same[0])["alignment"], c14r.curve(same[0])["alignment"])
    r = c14r.analyse(same)
    assert abs(np.log(r["common"]["tau"][0] / 300)) < np.log(1.5) and r["spread"] <= 1.5
    apart = c14r.analyse([c14.cohort(trace_sessions(120, 400, 3000, sessions=20, seed=1)),
                          c14.cohort(trace_sessions(600, 400, 3000, sessions=20, seed=2))])
    assert apart["spread"] > 1.5 and not apart["equivalence"]["0-1"]["passed"]


def test_c1_6r_and_c1_8r_fit_the_true_equation_and_need_the_trace():
    p = {"D": 0.2, "A": 3.0, "tau": 700.0, "sigma0": 0.8}
    events = ring_events(p, events=160, sessions=8)
    data = c16r.Data(events, np.random.default_rng(0))
    assert np.allclose(data.value[c15.INDEX], c15.Data(events, np.random.default_rng(0)).value[c15.INDEX])
    assert data.rule["clusters"] == 8 and np.all(np.linalg.eigvalsh(data.precision) > 0)
    dof = len(c15.INDEX) - 1
    for model in (c16r.Precise(data, 4, 1), c18r.Model(data, 4, 1)):
        with_trace, without = model.cost(p)[0], model.cost({**p, "A": 0.0})[0]
        assert with_trace / dof <= 2 < without / dof
    short = {"maxiter": 3, "restarts": 1}  # 적합·판정 경로가 새 모형으로 도는지만 본다
    f6 = c15.fit([c16r.Precise(data, 2, 1)], ("A", "tau"), ("D", "sigma0"), {}, p, **short)
    f8 = ring.fit([c18r.Model(data, 2, 1)], ("A",), ("tau", "D", "sigma0"), {}, p, **short)
    assert np.isfinite(c16r.judged([data], f6, 4)["chi2_dof"]) and np.isfinite(c18r.judged([data], f8, 4)["chi2_dof"])
