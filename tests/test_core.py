import numpy as np
import pytest

from research import core


def ring(n, shift=0.0, base=0.3):
    """Cosine ring coupling W_ij = cos(θ_i − θ_j − shift) + base on n evenly spaced neurons."""
    theta = np.arange(n) * 360 / n
    return np.cos(np.radians(theta[:, None] - theta[None, :] - shift)) + base


def test_split_reconstructs_metric_and_direction():
    w = np.random.default_rng(0).normal(size=(6, 6))
    ws, wa = core.split(w)
    assert np.allclose(ws, ws.T) and np.allclose(wa, -wa.T) and np.allclose(ws + wa, w)


def test_metric_must_be_positive_definite():
    ws, _ = core.split(ring(16))
    top = np.linalg.eigvalsh(ws)[-1]
    assert np.linalg.eigvalsh(core.metric(ws, 0.9 / top))[0] > 0
    with pytest.raises(ValueError):
        core.metric(ws, 1.1 / top)


def test_ring_plane_is_a_circle_ordered_by_position():
    ws, _ = core.split(ring(16))
    _, basis = core.plane(ws, np.zeros(16))
    angle, spread = core.circle(basis)
    slope, r = core.angle_slope(angle, np.arange(16))
    assert spread < 1e-6 and abs(abs(slope) - 22.5) < 0.5 and r > 0.999


def test_opposite_shifts_rotate_the_plane_oppositely():
    _, basis = core.plane(core.split(ring(16))[0], np.zeros(16))
    rates = []
    for shift in (30, -30):
        psi, scale, share = core.conformal(basis.T @ core.split(ring(16, shift))[1] @ basis)
        assert share > 0.999 and abs(abs(psi) - 90) < 1e-6
        rates.append(np.sign(psi) * scale)
    assert rates[0] == pytest.approx(-rates[1])
