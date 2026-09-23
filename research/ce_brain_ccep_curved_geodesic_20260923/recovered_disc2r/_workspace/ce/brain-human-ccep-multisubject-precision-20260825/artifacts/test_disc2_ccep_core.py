from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pytest

from disc2_ccep_core import (
    ApparatusError,
    BIN_CENTERS_X,
    SourceData,
    candidate_mean,
    compute_source_endpoints,
    decode_selected_channels,
    fetch_locked_range,
    fit_candidate,
    make_range_spec,
    profiled_huber_location,
    time_masks,
)


@pytest.mark.parametrize(
    (
        "fs",
        "samples",
        "expected_bytes_per_channel",
        "baseline",
        "post_counts",
        "pre_counts",
    ),
    [
        (512, 574, 574 * 4, 461, [4, 6, 10, 15, 21], [4, 6, 10, 16, 20]),
        (
            2048,
            2294,
            2294 * 4,
            1844,
            [16, 25, 41, 61, 82],
            [16, 25, 40, 62, 82],
        ),
    ],
)
def test_exact_range_geometry_and_physical_time_masks(
    fs, samples, expected_bytes_per_channel, baseline, post_counts, pre_counts
):
    spec = make_range_spec(fs, 7, fs * 3, fs * 10)
    assert spec.sample_count_in_range == samples
    assert spec.expected_bytes == expected_bytes_per_channel * 7
    masks = time_masks(spec)
    assert int(masks["baseline"].sum()) == baseline
    assert [int(mask.sum()) for mask in masks["post"]] == post_counts
    assert [int(mask.sum()) for mask in masks["pre"]] == pre_counts
    assert masks["times_s"][0] == -1.0
    assert masks["times_s"][-1] <= 0.120


def test_range_geometry_fails_closed_at_recording_edges():
    with pytest.raises(ApparatusError, match="before sample zero"):
        make_range_spec(512, 4, 511, 10_000)
    with pytest.raises(ApparatusError, match="after the recording"):
        make_range_spec(512, 4, 9_950, 10_000)
    with pytest.raises(ApparatusError, match="unsupported"):
        make_range_spec(1000, 4, 2_000, 10_000)


@dataclass
class FakeResponse:
    status_code: int
    headers: dict[str, str]
    content: bytes


def test_locked_range_verifies_http_identity_and_payload():
    spec = make_range_spec(512, 2, 1_024, 5_000)
    payload = bytes(spec.expected_bytes)
    etag = '"sealed-etag"'
    version = "sealed-version"
    total = spec.byte_end + 10_000
    response = FakeResponse(
        206,
        {
            "Content-Range": f"bytes {spec.byte_start}-{spec.byte_end}/{total}",
            "ETag": etag,
            "x-amz-version-id": version,
        },
        payload,
    )

    def get(url, **kwargs):
        assert kwargs["headers"] == {"Range": spec.range_header, "If-Match": etag}
        return response

    decoded, receipt = fetch_locked_range(
        get,
        locked_url=f"https://example.test/raw.eeg?versionId={version}",
        etag=etag,
        version_id=version,
        content_length=total,
        spec=spec,
    )
    assert decoded == payload
    assert receipt["expected_bytes"] == len(payload)

    response.headers["ETag"] = '"wrong"'
    with pytest.raises(ApparatusError, match="ETag"):
        fetch_locked_range(
            get,
            locked_url=f"https://example.test/raw.eeg?versionId={version}",
            etag=etag,
            version_id=version,
            content_length=total,
            spec=spec,
        )


def test_little_endian_multiplex_decode_and_unit_scaling():
    spec = make_range_spec(512, 3, 1_024, 5_000)
    raw = np.arange(spec.sample_count_in_range * 3, dtype="<f4").reshape(-1, 3)
    selected = decode_selected_channels(
        raw.tobytes(), spec, [2, 0], [2.0, 0.5], ["µV", "mV"]
    )
    assert np.allclose(selected[:, 0], raw[:, 2] * 2.0)
    assert np.allclose(selected[:, 1], raw[:, 0] * 500.0)
    damaged = bytearray(raw.tobytes())
    damaged[0:4] = np.asarray([np.nan], dtype="<f4").tobytes()
    with pytest.raises(ApparatusError, match="nonfinite"):
        decode_selected_channels(bytes(damaged), spec, [0], [1.0], ["µV"])


def test_voltage_endpoint_is_dimensionless_and_trial_groups_are_separate():
    spec = make_range_spec(512, 2, 1_024, 5_000)
    masks = time_masks(spec)
    tau = masks["times_s"]
    rng = np.random.default_rng(20260825)
    trials = rng.normal(0.0, 1.0, size=(10, tau.size, 2))
    pulse = np.exp(-np.square((tau - 0.045) / 0.015))
    trials[:, :, 0] += 7.0 * pulse[None, :]
    trials[5:, :, 0] += 0.5 * pulse[None, :]
    result = compute_source_endpoints(
        trials,
        spec,
        {"receiver": (0, 1)},
        (range(0, 10, 2), range(1, 10, 2)),
        {"forward": range(5), "reverse": range(5, 10)},
    )["receiver"]
    assert len(result["z"]) == 5
    assert len(result["pre_z"]) == 5
    assert len(result["temporal_half_energy"]) == 2
    assert set(result["orientation_energy"]) == {"forward", "reverse"}
    assert np.median(result["energy"]) > np.median(result["pre_energy"])
    assert result["baseline_sigma_uv"] > 0.0


def test_endpoint_is_invariant_to_a_common_voltage_unit_rescaling():
    spec = make_range_spec(512, 2, 1_024, 5_000)
    tau = time_masks(spec)["times_s"]
    rng = np.random.default_rng(991)
    trials = rng.normal(0.0, 0.5, size=(10, tau.size, 2))
    trials[:, :, 0] += 3.0 * np.exp(-np.square((tau - 0.035) / 0.012))
    arguments = (
        spec,
        {"receiver": (0, 1)},
        (range(0, 10, 2), range(1, 10, 2)),
    )
    original = compute_source_endpoints(trials, *arguments)["receiver"]
    rescaled = compute_source_endpoints(1_000.0 * trials, *arguments)["receiver"]
    assert np.allclose(original["energy"], rescaled["energy"], rtol=1.0e-12)
    assert np.allclose(original["z"], rescaled["z"], rtol=1.0e-12)
    assert rescaled["baseline_sigma_uv"] == pytest.approx(
        1_000.0 * original["baseline_sigma_uv"]
    )


def test_profiled_huber_location_has_exact_shift_equivariance():
    values = np.asarray([-3.0, -0.2, 0.1, 0.2, 4.0])
    original = profiled_huber_location(values)
    shifted = profiled_huber_location(values + 1.75)
    assert shifted == pytest.approx(original + 1.75, abs=1.0e-10)


def _synthetic_sources(candidate: str, theta: np.ndarray) -> list[SourceData]:
    rng = np.random.default_rng(87)
    result = []
    for subject_index, age in enumerate((-0.5, -0.1, 0.3, 0.7)):
        anchor_delta = rng.normal(0.0, 1.0, size=(4, 3))
        query_delta = rng.normal(0.0, 1.0, size=(12, 3))
        offset = -0.7 + 0.4 * subject_index
        anchor_z = candidate_mean(candidate, theta, age, anchor_delta) + offset
        query_z = candidate_mean(candidate, theta, age, query_delta) + offset
        result.append(
            SourceData(
                subject=f"s{subject_index}",
                source_id=f"src{subject_index}",
                age_tilde=age,
                anchor_delta=anchor_delta,
                query_delta=query_delta,
                anchor_z=anchor_z,
                query_z=query_z,
            )
        )
    return result


def test_frozen_candidate_has_no_global_intercept_or_current_column():
    theta = np.asarray([0.2, -0.1, 0.15, 0.05])
    sources = _synthetic_sources("S0", theta)
    fit = fit_candidate(sources, "S0", max_iterations=500)
    assert fit.parameters.shape == (4,)
    assert fit.numerical_gate["rank"] == 4
    assert fit.objective < 1.0e-10
    assert np.allclose(fit.parameters, theta, atol=2.0e-4)
    assert np.all(BIN_CENTERS_X > 0.0)
