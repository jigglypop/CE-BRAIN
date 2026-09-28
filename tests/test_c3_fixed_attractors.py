import cefast
import numpy as np

from research import c1_1_common_equation as c11
from research import c3_10_fixed_attractors as c310


def sessions(fixed_well, n_sessions=8, events=60, seed=0):
    """NREM-like events from the v3 ring (trace well at each event's own start) with, optionally, a static well at a
    session-specific direction that every event of the session shares. Events start near a session 'nest' direction."""
    rng = np.random.default_rng(seed)
    out = []
    for g in range(n_sessions):
        nest, attractor = rng.uniform(-np.pi, np.pi, 2)
        lengths = rng.integers(120, 481, events).astype(np.int64)
        start = nest + rng.normal(0, 0.6, events)
        heads = np.angle(np.exp(1j * (attractor - start)))  # 고정 우물을 ring_trace의 '머리 입력' 자리에 둔다
        theta = cefast.ring_trace(heads, lengths, c11.SPAN, 0.43, 4.45, 45.0, 2.0 if fixed_well else 0.0, c11.BETA, 200, seed + g)
        out.append([row[:k] + s0 + rng.vonmises(0, 1.0, k) for row, k, s0 in zip(theta, lengths, start)])
    return out


def test_shared_static_wells_are_found_and_nests_alone_are_not():
    none = c310.analyse(sessions(False), np.random.default_rng(1))
    fixed = c310.analyse(sessions(True), np.random.default_rng(1))
    assert none["p"] > c310.ALPHA and fixed["effect"] > 0 and fixed["p"] <= c310.ALPHA
