"""Frozen numerical core for BA-OBS-DISC2.

This module contains no dataset discovery and performs no network I/O unless
``fetch_locked_range`` is called explicitly.  The split/runner layer supplies
sealed record identities and stage membership.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
import os
from typing import Any, Callable, Iterable, Mapping, Sequence

for _thread_variable in (
    "OMP_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "MKL_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
    "NUMEXPR_NUM_THREADS",
):
    os.environ.setdefault(_thread_variable, "1")

import numpy as np
from scipy.optimize import minimize


BASELINE_S = (-1.0, -0.1)
POST_BINS_S = (
    (0.010, 0.018),
    (0.018, 0.030),
    (0.030, 0.050),
    (0.050, 0.080),
    (0.080, 0.120),
)
PRE_SHIFT_S = -0.300
BIN_CENTERS_X = np.asarray((0.014, 0.024, 0.040, 0.065, 0.100)) / 0.050
HUBER_DELTA = 0.5
ENERGY_FLOOR = 1.0e-6


class ApparatusError(RuntimeError):
    """A fail-closed raw-data or endpoint apparatus error."""


class ProfileError(RuntimeError):
    """The frozen anchor-only nuisance profile could not be solved."""


class FitError(RuntimeError):
    """A numerical candidate gate failed."""


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def canonical_sha256(value: Any) -> str:
    payload = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return sha256_bytes(payload)


@dataclass(frozen=True)
class RangeSpec:
    sampling_frequency_hz: int
    channel_count: int
    anchor_sample_zero_based: int
    sample_count: int
    first_sample: int
    last_sample: int
    byte_start: int
    byte_end: int
    expected_bytes: int

    @property
    def sample_count_in_range(self) -> int:
        return self.last_sample - self.first_sample + 1

    @property
    def range_header(self) -> str:
        return f"bytes={self.byte_start}-{self.byte_end}"


def make_range_spec(
    sampling_frequency_hz: float,
    channel_count: int,
    anchor_sample_zero_based: int,
    sample_count: int,
) -> RangeSpec:
    fs_float = float(sampling_frequency_hz)
    fs = int(round(fs_float))
    if not math.isclose(fs_float, fs, rel_tol=0.0, abs_tol=1.0e-9):
        raise ApparatusError("sampling frequency must be an exact integer Hz")
    if fs not in (512, 2048):
        raise ApparatusError(f"unsupported frozen sampling frequency: {fs}")
    if not isinstance(channel_count, int) or channel_count <= 0:
        raise ApparatusError("channel count must be a positive integer")
    if not isinstance(anchor_sample_zero_based, int):
        raise ApparatusError("anchor sample must be a zero-based integer")
    if not isinstance(sample_count, int) or sample_count <= 0:
        raise ApparatusError("sample count must be a positive integer")

    first = anchor_sample_zero_based - fs
    last = anchor_sample_zero_based + math.floor(0.120 * fs)
    if first < 0:
        raise ApparatusError("requested range starts before sample zero")
    if last >= sample_count:
        raise ApparatusError("requested range ends after the recording")

    byte_start = first * channel_count * 4
    byte_end = (last + 1) * channel_count * 4 - 1
    expected = (last - first + 1) * channel_count * 4
    return RangeSpec(
        sampling_frequency_hz=fs,
        channel_count=channel_count,
        anchor_sample_zero_based=anchor_sample_zero_based,
        sample_count=sample_count,
        first_sample=first,
        last_sample=last,
        byte_start=byte_start,
        byte_end=byte_end,
        expected_bytes=expected,
    )


def relative_times_s(spec: RangeSpec) -> np.ndarray:
    offsets = np.arange(spec.first_sample, spec.last_sample + 1, dtype=np.int64)
    offsets = offsets - spec.anchor_sample_zero_based
    return offsets.astype(np.float64) / float(spec.sampling_frequency_hz)


def time_masks(spec: RangeSpec) -> dict[str, Any]:
    tau = relative_times_s(spec)
    eps = 1.0e-14
    baseline = (tau >= BASELINE_S[0] - eps) & (tau <= BASELINE_S[1] + eps)
    post: list[np.ndarray] = []
    pre: list[np.ndarray] = []
    for index, (lo, hi) in enumerate(POST_BINS_S):
        if index == len(POST_BINS_S) - 1:
            post_mask = (tau >= lo - eps) & (tau <= hi + eps)
            pre_mask = (tau >= lo + PRE_SHIFT_S - eps) & (
                tau <= hi + PRE_SHIFT_S + eps
            )
        else:
            post_mask = (tau >= lo - eps) & (tau < hi - eps)
            pre_mask = (tau >= lo + PRE_SHIFT_S - eps) & (
                tau < hi + PRE_SHIFT_S - eps
            )
        post.append(post_mask)
        pre.append(pre_mask)
    masks = {"times_s": tau, "baseline": baseline, "post": post, "pre": pre}
    if not baseline.any() or any(not mask.any() for mask in (*post, *pre)):
        raise ApparatusError("one or more frozen endpoint masks are empty")
    return masks


def _lower_headers(headers: Mapping[str, Any]) -> dict[str, str]:
    return {str(key).lower(): str(value) for key, value in headers.items()}


def fetch_locked_range(
    get: Callable[..., Any],
    *,
    locked_url: str,
    etag: str,
    version_id: str,
    content_length: int,
    spec: RangeSpec,
    timeout_s: float = 60.0,
) -> tuple[bytes, dict[str, Any]]:
    if f"versionId={version_id}" not in locked_url:
        raise ApparatusError("locked URL does not contain the sealed VersionId")
    response = get(
        locked_url,
        headers={"Range": spec.range_header, "If-Match": etag},
        timeout=timeout_s,
    )
    if int(response.status_code) != 206:
        raise ApparatusError(f"expected HTTP 206, got {response.status_code}")
    headers = _lower_headers(response.headers)
    expected_content_range = (
        f"bytes {spec.byte_start}-{spec.byte_end}/{int(content_length)}"
    )
    if headers.get("content-range") != expected_content_range:
        raise ApparatusError(
            f"Content-Range mismatch: {headers.get('content-range')!r}"
        )
    if headers.get("etag") != etag:
        raise ApparatusError("ETag mismatch")
    if headers.get("x-amz-version-id") != version_id:
        raise ApparatusError("VersionId mismatch")
    payload = bytes(response.content)
    if len(payload) != spec.expected_bytes:
        raise ApparatusError(
            f"payload length mismatch: {len(payload)} != {spec.expected_bytes}"
        )
    receipt = {
        "locked_url": locked_url,
        "version_id": version_id,
        "etag": etag,
        "byte_start": spec.byte_start,
        "byte_end": spec.byte_end,
        "expected_bytes": spec.expected_bytes,
        "payload_sha256": sha256_bytes(payload),
        "http_status": 206,
        "content_range": expected_content_range,
    }
    return payload, receipt


def voltage_scale_to_uv(unit: str) -> float:
    normalized = str(unit).strip().replace("μ", "µ").lower()
    scales = {
        "v": 1.0e6,
        "mv": 1.0e3,
        "uv": 1.0,
        "µv": 1.0,
    }
    if normalized not in scales:
        raise ApparatusError(f"unsupported voltage unit: {unit!r}")
    return scales[normalized]


def decode_selected_channels(
    payload: bytes,
    spec: RangeSpec,
    channel_indices: Sequence[int],
    resolutions: Sequence[float],
    units: Sequence[str],
) -> np.ndarray:
    if not (len(channel_indices) == len(resolutions) == len(units)):
        raise ApparatusError("channel metadata lengths differ")
    if len(channel_indices) == 0 or len(set(channel_indices)) != len(channel_indices):
        raise ApparatusError("selected channel indexes must be nonempty and unique")
    if any(
        not isinstance(index, (int, np.integer))
        or int(index) < 0
        or int(index) >= spec.channel_count
        for index in channel_indices
    ):
        raise ApparatusError("selected channel index is outside the recording")
    expected_values = spec.sample_count_in_range * spec.channel_count
    values = np.frombuffer(payload, dtype="<f4")
    if values.size != expected_values:
        raise ApparatusError("float32 payload shape mismatch")
    if not np.isfinite(values).all():
        raise ApparatusError("raw payload contains nonfinite values")
    multiplexed = values.reshape(spec.sample_count_in_range, spec.channel_count)
    scale = np.asarray(resolutions, dtype=np.float64) * np.asarray(
        [voltage_scale_to_uv(unit) for unit in units], dtype=np.float64
    )
    if not np.isfinite(scale).all() or np.any(scale <= 0.0):
        raise ApparatusError("channel resolution must be finite and positive")
    selected = multiplexed[:, np.asarray(channel_indices, dtype=np.int64)].astype(
        np.float64, copy=True
    )
    selected *= scale[None, :]
    if not np.isfinite(selected).all():
        raise ApparatusError("scaled voltage contains nonfinite values")
    return selected


def _energy_rows(signal: np.ndarray, masks: Sequence[np.ndarray], sigma: float) -> np.ndarray:
    rows = []
    for mask in masks:
        values = signal[mask] / sigma
        if values.size == 0 or not np.isfinite(values).all():
            raise ApparatusError("empty or nonfinite energy bin")
        rows.append(float(np.sqrt(np.mean(np.square(values)))))
    result = np.asarray(rows, dtype=np.float64)
    if not np.isfinite(result).all():
        raise ApparatusError("nonfinite endpoint energy")
    return result


def _robust_baseline_scale(values: np.ndarray) -> float:
    flat = np.asarray(values, dtype=np.float64).reshape(-1)
    if flat.size == 0 or not np.isfinite(flat).all():
        raise ApparatusError("baseline values are empty or nonfinite")
    median = float(np.median(flat))
    sigma = 1.4826 * float(np.median(np.abs(flat - median)))
    if not math.isfinite(sigma) or sigma <= 0.0:
        raise ApparatusError("baseline MAD scale is not finite and positive")
    return sigma


def compute_source_endpoints(
    trial_voltages_uv: np.ndarray,
    spec: RangeSpec,
    target_pairs: Mapping[str, tuple[int, int]],
    temporal_halves: tuple[Sequence[int], Sequence[int]],
    orientation_groups: Mapping[str, Sequence[int]] | None = None,
) -> dict[str, dict[str, Any]]:
    """Compute frozen endpoints for one source's ten trials.

    ``target_pairs`` indexes the selected-channel axis of ``trial_voltages_uv``.
    Trial group indexes are zero-based positions in the sealed ten-trial order.
    """

    trials = np.asarray(trial_voltages_uv, dtype=np.float64)
    if trials.ndim != 3 or trials.shape[0] != 10:
        raise ApparatusError("endpoint requires exactly ten trial windows")
    if trials.shape[1] != spec.sample_count_in_range:
        raise ApparatusError("trial time axis does not match the range geometry")
    if not np.isfinite(trials).all():
        raise ApparatusError("trial voltage contains nonfinite values")
    masks = time_masks(spec)
    baseline = masks["baseline"]
    centered = trials - np.median(trials[:, baseline, :], axis=1)[:, None, :]

    half_a = tuple(int(index) for index in temporal_halves[0])
    half_b = tuple(int(index) for index in temporal_halves[1])
    if len(half_a) != 5 or len(half_b) != 5 or set(half_a).intersection(half_b):
        raise ApparatusError("temporal repeatability groups must be disjoint 5/5")
    if set(half_a).union(half_b) != set(range(10)):
        raise ApparatusError("temporal repeatability groups must cover all ten trials")

    normalized_orientation: dict[str, tuple[int, ...]] = {}
    if orientation_groups:
        for label, indexes in orientation_groups.items():
            group = tuple(int(index) for index in indexes)
            if len(group) != 5 or any(index not in range(10) for index in group):
                raise ApparatusError("orientation groups must each contain five trials")
            normalized_orientation[str(label)] = group
        if len(normalized_orientation) == 2:
            groups = list(normalized_orientation.values())
            if set(groups[0]).intersection(groups[1]) or set(groups[0]).union(groups[1]) != set(
                range(10)
            ):
                raise ApparatusError("two orientation groups must partition ten trials")

    output: dict[str, dict[str, Any]] = {}
    for target_id, pair in target_pairs.items():
        first, second = (int(pair[0]), int(pair[1]))
        if first == second or min(first, second) < 0 or max(first, second) >= centered.shape[2]:
            raise ApparatusError(f"invalid bipolar target pair: {target_id}")
        bipolar_trials = centered[:, :, first] - centered[:, :, second]
        mean_trials = centered[:, :, first] / 2.0 + centered[:, :, second] / 2.0
        sigma_bipolar = _robust_baseline_scale(bipolar_trials[:, baseline])
        sigma_mean = _robust_baseline_scale(mean_trials[:, baseline])

        bipolar_primary = np.mean(bipolar_trials, axis=0)
        contact_primary = np.mean(mean_trials, axis=0)
        energy = _energy_rows(bipolar_primary, masks["post"], sigma_bipolar)
        pre_energy = _energy_rows(bipolar_primary, masks["pre"], sigma_bipolar)
        contact_energy = _energy_rows(contact_primary, masks["post"], sigma_mean)
        contact_pre_energy = _energy_rows(contact_primary, masks["pre"], sigma_mean)

        temporal_energy = []
        for indexes in (half_a, half_b):
            temporal_energy.append(
                _energy_rows(
                    np.mean(bipolar_trials[np.asarray(indexes)], axis=0),
                    masks["post"],
                    sigma_bipolar,
                )
            )
        orientation_energy: dict[str, list[float]] = {}
        for label, indexes in normalized_orientation.items():
            orientation_energy[label] = _energy_rows(
                np.mean(bipolar_trials[np.asarray(indexes)], axis=0),
                masks["post"],
                sigma_bipolar,
            ).tolist()

        output[str(target_id)] = {
            "baseline_sigma_uv": sigma_bipolar,
            "contact_mean_baseline_sigma_uv": sigma_mean,
            "energy": energy.tolist(),
            "z": np.log(energy + ENERGY_FLOOR).tolist(),
            "pre_energy": pre_energy.tolist(),
            "pre_z": np.log(pre_energy + ENERGY_FLOOR).tolist(),
            "contact_mean_energy": contact_energy.tolist(),
            "contact_mean_z": np.log(contact_energy + ENERGY_FLOOR).tolist(),
            "contact_mean_pre_energy": contact_pre_energy.tolist(),
            "contact_mean_pre_z": np.log(contact_pre_energy + ENERGY_FLOOR).tolist(),
            "temporal_half_energy": [row.tolist() for row in temporal_energy],
            "orientation_energy": orientation_energy,
        }
    return output


def huber_loss(residual: np.ndarray, delta: float = HUBER_DELTA) -> np.ndarray:
    values = np.asarray(residual, dtype=np.float64)
    absolute = np.abs(values)
    return np.where(
        absolute <= delta,
        0.5 * np.square(values),
        delta * (absolute - 0.5 * delta),
    )


def profiled_huber_location(
    residual_without_offset: np.ndarray,
    *,
    delta: float = HUBER_DELTA,
    lower: float = -20.0,
    upper: float = 20.0,
    iterations: int = 80,
    score_tolerance: float = 1.0e-10,
) -> float:
    values = np.asarray(residual_without_offset, dtype=np.float64).reshape(-1)
    if values.size == 0 or not np.isfinite(values).all():
        raise ProfileError("PROFILE_STOP: anchor residuals are empty or nonfinite")

    def score(location: float) -> float:
        return float(np.sum(np.clip(values - location, -delta, delta)))

    # The score is continuous, monotone and piecewise linear with breakpoints
    # v_i +/- delta.  Scanning those breakpoints gives the exact root (or the
    # midpoint of the exact zero interval) without an iterative optimizer.
    score_lower = score(lower)
    score_upper = score(upper)
    if score_lower < 0.0 or score_upper > 0.0:
        raise ProfileError("PROFILE_STOP: Huber root lies outside [-20,20]")
    del iterations  # retained in the public signature for frozen call compatibility
    points = np.unique(
        np.clip(
            np.concatenate(
                (np.asarray([lower, upper]), values - delta, values + delta)
            ),
            lower,
            upper,
        )
    )
    scores = np.sum(
        np.clip(values[:, None] - points[None, :], -delta, delta), axis=0
    )
    zero = np.flatnonzero(np.abs(scores) <= score_tolerance)
    if zero.size:
        root = 0.5 * (float(points[zero[0]]) + float(points[zero[-1]]))
    else:
        crossings = np.flatnonzero(
            (scores[:-1] > 0.0) & (scores[1:] < 0.0)
        )
        if crossings.size != 1:
            raise ProfileError("PROFILE_STOP: Huber breakpoint scan found no unique root")
        index = int(crossings[0])
        left, right = float(points[index]), float(points[index + 1])
        score_left, score_right = float(scores[index]), float(scores[index + 1])
        root = left - score_left * (right - left) / (score_right - score_left)
    if not math.isfinite(root) or abs(score(root)) > score_tolerance:
        raise ProfileError("PROFILE_STOP: Huber root did not meet score tolerance")
    return root


@dataclass(frozen=True)
class SourceData:
    subject: str
    source_id: str
    age_tilde: float
    anchor_delta: np.ndarray
    query_delta: np.ndarray
    anchor_z: np.ndarray
    query_z: np.ndarray

    def validated(self) -> "SourceData":
        arrays = {
            "anchor_delta": np.asarray(self.anchor_delta, dtype=np.float64),
            "query_delta": np.asarray(self.query_delta, dtype=np.float64),
            "anchor_z": np.asarray(self.anchor_z, dtype=np.float64),
            "query_z": np.asarray(self.query_z, dtype=np.float64),
        }
        if arrays["anchor_delta"].shape != (4, 3):
            raise FitError("each source must have four 3-D anchor coordinates")
        if arrays["query_delta"].shape != (12, 3):
            raise FitError("each source must have twelve 3-D query coordinates")
        if arrays["anchor_z"].shape != (4, 5):
            raise FitError("each source must have four-by-five anchor endpoints")
        if arrays["query_z"].shape != (12, 5):
            raise FitError("each source must have twelve-by-five query endpoints")
        if not math.isfinite(float(self.age_tilde)) or any(
            not np.isfinite(value).all() for value in arrays.values()
        ):
            raise FitError("source model arrays must be finite")
        return SourceData(
            subject=str(self.subject),
            source_id=str(self.source_id),
            age_tilde=float(self.age_tilde),
            **arrays,
        )


@dataclass(frozen=True)
class _PackedSources:
    sources: tuple[SourceData, ...]
    age_tilde: np.ndarray
    anchor_delta: np.ndarray
    query_delta: np.ndarray
    anchor_z: np.ndarray
    query_z: np.ndarray
    source_weights: np.ndarray


def _pack_sources(sources: Sequence[SourceData]) -> _PackedSources:
    validated = tuple(source.validated() for source in sources)
    if not validated:
        raise FitError("fit dataset is empty")
    source_counts: dict[str, int] = {}
    for source in validated:
        source_counts[source.subject] = source_counts.get(source.subject, 0) + 1
    participant_count = len(source_counts)
    weights = np.asarray(
        [
            1.0 / (participant_count * source_counts[source.subject])
            for source in validated
        ],
        dtype=np.float64,
    )
    return _PackedSources(
        sources=validated,
        age_tilde=np.asarray([source.age_tilde for source in validated]),
        anchor_delta=np.stack([source.anchor_delta for source in validated]),
        query_delta=np.stack([source.query_delta for source in validated]),
        anchor_z=np.stack([source.anchor_z for source in validated]),
        query_z=np.stack([source.query_z for source in validated]),
        source_weights=weights,
    )


def _profiled_huber_locations(
    residual_without_offset: np.ndarray,
    *,
    delta: float = HUBER_DELTA,
    lower: float = -20.0,
    upper: float = 20.0,
    score_tolerance: float = 1.0e-10,
) -> np.ndarray:
    values = np.asarray(residual_without_offset, dtype=np.float64)
    if values.ndim != 2 or values.shape[1] == 0 or not np.isfinite(values).all():
        raise ProfileError("PROFILE_STOP: packed anchor residuals are invalid")
    score_lower = np.sum(np.clip(values - lower, -delta, delta), axis=1)
    score_upper = np.sum(np.clip(values - upper, -delta, delta), axis=1)
    if np.any(score_lower < 0.0) or np.any(score_upper > 0.0):
        raise ProfileError("PROFILE_STOP: packed Huber root lies outside [-20,20]")
    row_count = values.shape[0]
    points = np.concatenate(
        (
            np.full((row_count, 1), lower),
            np.full((row_count, 1), upper),
            values - delta,
            values + delta,
        ),
        axis=1,
    )
    points = np.sort(np.clip(points, lower, upper), axis=1)
    scores = np.sum(
        np.clip(values[:, :, None] - points[:, None, :], -delta, delta), axis=1
    )
    roots = np.empty(row_count, dtype=np.float64)
    zero = np.abs(scores) <= score_tolerance
    has_zero = np.any(zero, axis=1)
    if np.any(has_zero):
        zero_rows = np.flatnonzero(has_zero)
        first = np.argmax(zero[zero_rows], axis=1)
        last = zero.shape[1] - 1 - np.argmax(zero[zero_rows, ::-1], axis=1)
        roots[zero_rows] = 0.5 * (
            points[zero_rows, first] + points[zero_rows, last]
        )
    nonzero_rows = np.flatnonzero(~has_zero)
    if nonzero_rows.size:
        crossings = (scores[nonzero_rows, :-1] > 0.0) & (
            scores[nonzero_rows, 1:] < 0.0
        )
        if np.any(np.sum(crossings, axis=1) != 1):
            raise ProfileError("PROFILE_STOP: packed breakpoint root is not unique")
        indexes = np.argmax(crossings, axis=1)
        left = points[nonzero_rows, indexes]
        right = points[nonzero_rows, indexes + 1]
        score_left = scores[nonzero_rows, indexes]
        score_right = scores[nonzero_rows, indexes + 1]
        roots[nonzero_rows] = left - score_left * (right - left) / (
            score_right - score_left
        )
    final_score = np.sum(
        np.clip(values - roots[:, None], -delta, delta), axis=1
    )
    if not np.isfinite(roots).all() or np.any(np.abs(final_score) > score_tolerance):
        raise ProfileError("PROFILE_STOP: packed Huber root failed tolerance")
    return roots


@dataclass(frozen=True)
class CandidateSpec:
    name: str
    parameter_names: tuple[str, ...]
    lower: np.ndarray
    upper: np.ndarray


def candidate_spec(name: str) -> CandidateSpec:
    common = ("beta_logx", "beta_x", "gamma_age_logx", "gamma_age_x")
    common_lower = [-20.0] * 4
    common_upper = [20.0] * 4
    definitions = {
        "S0": (common, common_lower, common_upper),
        "SC": (common + ("a",), common_lower + [0.0], common_upper + [20.0]),
        "SH0": (
            common + ("kappa",),
            common_lower + [0.0],
            common_upper + [20.0],
        ),
        "SAC": (
            common + ("a", "g_x", "g_y"),
            common_lower + [0.0, -1.0, -1.0],
            common_upper + [20.0, 1.0, 1.0],
        ),
        "SHA0": (
            common + ("kappa", "g_x", "g_y"),
            common_lower + [0.0, -1.0, -1.0],
            common_upper + [20.0, 1.0, 1.0],
        ),
    }
    if name not in definitions:
        raise FitError(f"unknown candidate: {name}")
    names, lower, upper = definitions[name]
    return CandidateSpec(
        name=name,
        parameter_names=tuple(names),
        lower=np.asarray(lower, dtype=np.float64),
        upper=np.asarray(upper, dtype=np.float64),
    )


def deterministic_starts(
    name: str, common_start: np.ndarray | None = None
) -> list[np.ndarray]:
    spec = candidate_spec(name)
    common = (
        np.zeros(4, dtype=np.float64)
        if common_start is None
        else np.asarray(common_start, dtype=np.float64)
    )
    if common.shape != (4,) or not np.isfinite(common).all():
        raise FitError("common deterministic start is invalid")
    common = np.clip(common, -19.0, 19.0)
    if name == "S0":
        return [
            common.copy(),
            np.clip(common + 0.1, -19.0, 19.0),
            np.clip(common - 0.1, -19.0, 19.0),
            np.zeros(4, dtype=np.float64),
        ]
    if name in ("SC", "SH0"):
        return [
            np.concatenate((common, np.asarray([attenuation])))
            for attenuation in (0.1, 0.5, 1.0, 2.0, 5.0)
        ]
    starts = []
    for attenuation in (0.1, 1.0, 5.0):
        for g_x in (-0.5, 0.0, 0.5):
            for g_y in (-0.5, 0.0, 0.5):
                starts.append(
                    np.asarray(
                        [*common.tolist(), attenuation, g_x, g_y],
                        dtype=np.float64,
                    )
                )
    if any(start.shape != spec.lower.shape for start in starts):
        raise AssertionError("internal deterministic start shape error")
    return starts


def common_within_source_ols_start(sources: Sequence[SourceData]) -> np.ndarray:
    design_rows: list[np.ndarray] = []
    response_rows: list[np.ndarray] = []
    log_x = np.log(BIN_CENTERS_X)
    for source in sources:
        temporal = np.column_stack(
            (
                log_x,
                BIN_CENTERS_X,
                source.age_tilde * log_x,
                source.age_tilde * BIN_CENTERS_X,
            )
        )
        design = np.tile(temporal, (12, 1))
        response = np.asarray(source.query_z, dtype=np.float64).reshape(-1)
        design_rows.append(design - np.mean(design, axis=0, keepdims=True))
        response_rows.append(response - np.mean(response))
    if not design_rows:
        raise FitError("OLS start dataset is empty")
    design = np.vstack(design_rows)
    response = np.concatenate(response_rows)
    solution, _, rank, _ = np.linalg.lstsq(design, response, rcond=1.0e-10)
    if rank != 4 or not np.isfinite(solution).all():
        raise FitError("common within-source OLS start is rank deficient")
    return np.clip(solution, -19.0, 19.0)


def candidate_mean(
    name: str,
    parameters: np.ndarray,
    age_tilde: float,
    delta_xyz: np.ndarray,
) -> np.ndarray:
    spec = candidate_spec(name)
    theta = np.asarray(parameters, dtype=np.float64)
    delta_xyz = np.asarray(delta_xyz, dtype=np.float64)
    if theta.shape != spec.lower.shape or delta_xyz.ndim != 2 or delta_xyz.shape[1] != 3:
        raise FitError("candidate parameter or geometry shape mismatch")
    x = BIN_CENTERS_X
    log_x = np.log(x)
    temporal = (
        theta[0] * log_x
        + theta[1] * x
        + theta[2] * float(age_tilde) * log_x
        + theta[3] * float(age_tilde) * x
    )
    result = np.broadcast_to(temporal[None, :], (delta_xyz.shape[0], 5)).copy()
    if name == "S0":
        return result
    attenuation = theta[4]
    if name in ("SC", "SH0"):
        distance_squared = np.sum(np.square(delta_xyz), axis=1)
    else:
        g_x, g_y = theta[5], theta[6]
        diagonal = np.asarray(
            [math.exp(g_x), math.exp(g_y), math.exp(-g_x - g_y)],
            dtype=np.float64,
        )
        distance_squared = np.sum(np.square(delta_xyz) * diagonal[None, :], axis=1)
    if name in ("SC", "SAC"):
        result -= attenuation * np.sqrt(distance_squared)[:, None]
    else:
        result -= attenuation * distance_squared[:, None] / x[None, :]
    if not np.isfinite(result).all():
        raise FitError("candidate prediction is nonfinite")
    return result


def _packed_candidate_mean(
    name: str,
    parameters: np.ndarray,
    age_tilde: np.ndarray,
    delta_xyz: np.ndarray,
) -> np.ndarray:
    spec = candidate_spec(name)
    theta = np.asarray(parameters, dtype=np.float64)
    age = np.asarray(age_tilde, dtype=np.float64)
    delta_xyz = np.asarray(delta_xyz, dtype=np.float64)
    if (
        theta.shape != spec.lower.shape
        or delta_xyz.ndim != 3
        or delta_xyz.shape[0] != age.size
        or delta_xyz.shape[2] != 3
    ):
        raise FitError("packed candidate parameter or geometry shape mismatch")
    x = BIN_CENTERS_X
    log_x = np.log(x)
    temporal = (
        theta[0] * log_x[None, :]
        + theta[1] * x[None, :]
        + theta[2] * age[:, None] * log_x[None, :]
        + theta[3] * age[:, None] * x[None, :]
    )
    target_count = delta_xyz.shape[1]
    result = np.broadcast_to(
        temporal[:, None, :], (age.size, target_count, 5)
    ).copy()
    if name == "S0":
        return result
    attenuation = theta[4]
    if name in ("SC", "SH0"):
        distance_squared = np.sum(np.square(delta_xyz), axis=2)
    else:
        g_x, g_y = theta[5], theta[6]
        diagonal = np.asarray(
            [math.exp(g_x), math.exp(g_y), math.exp(-g_x - g_y)],
            dtype=np.float64,
        )
        distance_squared = np.sum(
            np.square(delta_xyz) * diagonal[None, None, :], axis=2
        )
    if name in ("SC", "SAC"):
        result -= attenuation * np.sqrt(distance_squared)[:, :, None]
    else:
        result -= attenuation * distance_squared[:, :, None] / x[None, None, :]
    if not np.isfinite(result).all():
        raise FitError("packed candidate prediction is nonfinite")
    return result


def _packed_profile_and_loss(
    packed: _PackedSources, name: str, parameters: np.ndarray
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    anchor_mean = _packed_candidate_mean(
        name, parameters, packed.age_tilde, packed.anchor_delta
    )
    offsets = _profiled_huber_locations(
        (packed.anchor_z - anchor_mean).reshape(len(packed.sources), -1)
    )
    query_prediction = _packed_candidate_mean(
        name, parameters, packed.age_tilde, packed.query_delta
    ) + offsets[:, None, None]
    source_loss = np.mean(huber_loss(packed.query_z - query_prediction), axis=(1, 2))
    if not np.isfinite(source_loss).all():
        raise FitError("packed source loss is nonfinite")
    return offsets, source_loss, query_prediction


def _packed_equal_weight_objective(
    packed: _PackedSources, name: str, parameters: np.ndarray
) -> float:
    _, source_loss, _ = _packed_profile_and_loss(packed, name, parameters)
    result = float(np.dot(packed.source_weights, source_loss))
    if not math.isfinite(result):
        raise FitError("packed training objective is nonfinite")
    return result


def source_profile_and_loss(
    source: SourceData, name: str, parameters: np.ndarray
) -> tuple[float, float, np.ndarray]:
    anchor_mean = candidate_mean(name, parameters, source.age_tilde, source.anchor_delta)
    offset = profiled_huber_location(source.anchor_z - anchor_mean)
    query_prediction = (
        candidate_mean(name, parameters, source.age_tilde, source.query_delta) + offset
    )
    residual = source.query_z - query_prediction
    loss = float(np.mean(huber_loss(residual)))
    if not math.isfinite(loss):
        raise FitError("source loss is nonfinite")
    return offset, loss, query_prediction


def equal_weight_objective(
    sources: Sequence[SourceData], name: str, parameters: np.ndarray
) -> float:
    by_subject: dict[str, list[float]] = {}
    for source in sources:
        _, loss, _ = source_profile_and_loss(source, name, parameters)
        by_subject.setdefault(source.subject, []).append(loss)
    if not by_subject:
        raise FitError("fit dataset is empty")
    subject_losses = [float(np.mean(losses)) for losses in by_subject.values()]
    result = float(np.mean(subject_losses))
    if not math.isfinite(result):
        raise FitError("training objective is nonfinite")
    return result


def profiled_query_vector(
    sources: Sequence[SourceData], name: str, parameters: np.ndarray
) -> tuple[np.ndarray, list[float]]:
    predictions: list[np.ndarray] = []
    offsets: list[float] = []
    for source in sources:
        offset, _, prediction = source_profile_and_loss(source, name, parameters)
        offsets.append(offset)
        predictions.append(prediction.reshape(-1))
    if not predictions:
        raise FitError("prediction dataset is empty")
    return np.concatenate(predictions), offsets


def normalized_profiled_jacobian(
    sources: Sequence[SourceData],
    name: str,
    parameters: np.ndarray,
    *,
    step: float = 1.0e-5,
) -> np.ndarray:
    packed = _pack_sources(sources)
    return _normalized_profiled_jacobian_packed(
        packed, name, parameters, step=step
    )


def _normalized_profiled_jacobian_packed(
    packed: _PackedSources,
    name: str,
    parameters: np.ndarray,
    *,
    step: float = 1.0e-5,
) -> np.ndarray:
    spec = candidate_spec(name)
    theta = np.asarray(parameters, dtype=np.float64)
    span = spec.upper - spec.lower
    normalized = (theta - spec.lower) / span
    if np.any(normalized <= step) or np.any(normalized >= 1.0 - step):
        raise FitError("central-difference point is on a parameter boundary")
    columns = []
    for index in range(theta.size):
        plus = normalized.copy()
        minus = normalized.copy()
        plus[index] += step
        minus[index] -= step
        _, _, prediction_plus_array = _packed_profile_and_loss(
            packed, name, spec.lower + plus * span
        )
        _, _, prediction_minus_array = _packed_profile_and_loss(
            packed, name, spec.lower + minus * span
        )
        prediction_plus = prediction_plus_array.reshape(-1)
        prediction_minus = prediction_minus_array.reshape(-1)
        columns.append((prediction_plus - prediction_minus) / (2.0 * step))
    jacobian = np.column_stack(columns)
    if not np.isfinite(jacobian).all():
        raise FitError("normalized profiled Jacobian is nonfinite")
    return jacobian


def numerical_gate(
    sources: Sequence[SourceData],
    name: str,
    parameters: np.ndarray,
    *,
    _packed: _PackedSources | None = None,
) -> dict[str, Any]:
    spec = candidate_spec(name)
    theta = np.asarray(parameters, dtype=np.float64)
    if np.any(theta < spec.lower) or np.any(theta > spec.upper):
        raise FitError("solution is outside frozen parameter bounds")
    if name != "S0":
        if theta[4] <= 1.0e-4:
            raise FitError("GEOMETRY_NULL_COLLAPSE")
        if spec.upper[4] - theta[4] <= 1.0e-5:
            raise FitError("ATTENUATION_UPPER_BOUND")
    if name in ("SAC", "SHA0") and (
        1.0 - abs(theta[5]) <= 1.0e-5 or 1.0 - abs(theta[6]) <= 1.0e-5
    ):
        raise FitError("ANISOTROPY_BOUNDARY")
    packed = _pack_sources(sources) if _packed is None else _packed
    jacobian = _normalized_profiled_jacobian_packed(packed, name, theta)
    singular = np.linalg.svd(jacobian, compute_uv=False)
    if singular.size != theta.size or singular[0] <= 0.0:
        raise FitError("JACOBIAN_RANK_DEFICIENT")
    tolerance = singular[0] * 1.0e-8
    rank = int(np.sum(singular > tolerance))
    if rank != theta.size or singular[-1] <= 0.0:
        raise FitError("JACOBIAN_RANK_DEFICIENT")
    condition = float(singular[0] / singular[-1])
    if not math.isfinite(condition) or condition > 1.0e7:
        raise FitError("JACOBIAN_ILL_CONDITIONED")
    return {
        "rank": rank,
        "condition_number": condition,
        "singular_values": singular.tolist(),
    }


@dataclass(frozen=True)
class FitResult:
    candidate: str
    parameters: np.ndarray
    objective: float
    source_offsets: tuple[float, ...]
    anchor_profile_sha256: str
    numerical_gate: Mapping[str, Any]
    admissible_start_count: int
    optimizer_runs: tuple[Mapping[str, Any], ...]

    def as_dict(self) -> dict[str, Any]:
        spec = candidate_spec(self.candidate)
        return {
            "candidate": self.candidate,
            "parameters": {
                key: float(value)
                for key, value in zip(spec.parameter_names, self.parameters)
            },
            "objective": float(self.objective),
            "source_offsets": [float(value) for value in self.source_offsets],
            "anchor_profile_sha256": self.anchor_profile_sha256,
            "numerical_gate": dict(self.numerical_gate),
            "admissible_start_count": self.admissible_start_count,
            "optimizer_runs": [dict(value) for value in self.optimizer_runs],
        }


def fit_candidate(
    sources: Sequence[SourceData],
    name: str,
    *,
    starts: Sequence[np.ndarray] | None = None,
    max_iterations: int = 300,
) -> FitResult:
    packed = _pack_sources(sources)
    validated = packed.sources
    spec = candidate_spec(name)
    starts = list(
        deterministic_starts(name, common_within_source_ols_start(validated))
        if starts is None
        else starts
    )
    search_successful: list[tuple[float, np.ndarray, np.ndarray, list[float]]] = []
    run_receipts: list[dict[str, Any]] = []

    def objective(theta: np.ndarray) -> float:
        try:
            return _packed_equal_weight_objective(packed, name, theta)
        except (ProfileError, FitError, FloatingPointError):
            return 1.0e30

    def run_optimizer(
        start: np.ndarray, *, phase: str, run_index: int, require_gate: bool
    ) -> tuple[float, np.ndarray, np.ndarray, list[float], dict[str, Any] | None] | None:
        start_array = np.asarray(start, dtype=np.float64)
        if start_array.shape != spec.lower.shape:
            raise FitError("optimizer start shape mismatch")
        result = minimize(
            objective,
            start_array,
            method="L-BFGS-B",
            bounds=list(zip(spec.lower, spec.upper)),
            options={
                "maxiter": int(max_iterations),
                "maxfun": int(max_iterations) * 20,
                "ftol": 1.0e-12,
                "gtol": 1.0e-8,
                "maxls": 80,
            },
        )
        receipt: dict[str, Any] = {
            "phase": phase,
            "run_index": run_index,
            "start": start_array.tolist(),
            "success": bool(result.success),
            "status": int(result.status),
            "message": str(result.message),
            "objective": float(result.fun) if math.isfinite(float(result.fun)) else None,
            "iterations": int(getattr(result, "nit", -1)),
        }
        if bool(result.success) and np.isfinite(result.x).all() and math.isfinite(float(result.fun)):
            try:
                offsets_array, _, prediction_array = _packed_profile_and_loss(
                    packed, name, result.x
                )
                prediction = prediction_array.reshape(-1)
                offsets = offsets_array.tolist()
                gate = (
                    numerical_gate(validated, name, result.x, _packed=packed)
                    if require_gate
                    else None
                )
            except (ProfileError, FitError, FloatingPointError) as error:
                receipt["gate_error"] = str(error)
            else:
                receipt["admissible"] = True
        run_receipts.append(receipt)
        if receipt.get("admissible"):
            return float(result.fun), result.x.copy(), prediction, offsets, gate
        return None

    for run_index, start in enumerate(starts):
        outcome = run_optimizer(
            np.asarray(start), phase="basin_search", run_index=run_index, require_gate=False
        )
        if outcome is not None:
            search_successful.append(outcome[:4])

    search_successful.sort(
        key=lambda item: (item[0], tuple(float(value) for value in item[1]))
    )
    if not search_successful:
        raise FitError(
            f"MULTISTART_SEARCH_STOP: {name} has no finite basin-search solution"
        )
    search_best = search_successful[0][1]
    span = spec.upper - spec.lower
    normalized_best = (search_best - spec.lower) / span
    direction = np.where(np.arange(search_best.size) % 2 == 0, 1.0, -1.0)
    confirmation_starts = []
    for shift in (0.0, 1.0e-3, -1.0e-3):
        normalized = np.clip(
            normalized_best + shift * direction, 2.0e-5, 1.0 - 2.0e-5
        )
        confirmation_starts.append(spec.lower + normalized * span)

    confirmed: list[
        tuple[float, np.ndarray, np.ndarray, list[float], dict[str, Any]]
    ] = []
    for run_index, start in enumerate(confirmation_starts):
        outcome = run_optimizer(
            start,
            phase="best_basin_confirmation",
            run_index=run_index,
            require_gate=True,
        )
        if outcome is not None and outcome[4] is not None:
            confirmed.append(
                (outcome[0], outcome[1], outcome[2], outcome[3], outcome[4])
            )
    confirmed.sort(key=lambda item: (item[0], tuple(float(value) for value in item[1])))
    if len(confirmed) != 3:
        raise FitError(
            f"MULTISTART_CONFIRMATION_STOP: {name} has {len(confirmed)}/3 admissible confirmations"
        )
    best_three = confirmed
    base_loss = best_three[0][0]
    denominator = max(1.0, abs(base_loss))
    if any(abs(item[0] - base_loss) / denominator > 2.0e-4 for item in best_three[1:]):
        raise FitError(
            "MULTISTART_LOSS_DISAGREEMENT_STOP::"
            f"{name}::objectives={[item[0] for item in best_three]}::"
            f"parameters={[item[1].tolist() for item in best_three]}"
        )
    base_prediction = best_three[0][2]
    disagreement_rms = []
    for item in best_three[1:]:
        rms = float(np.sqrt(np.mean(np.square(item[2] - base_prediction))))
        disagreement_rms.append(rms)
        if not math.isfinite(rms) or rms > 5.0e-2:
            raise FitError(
                "MULTISTART_PREDICTION_DISAGREEMENT_STOP::"
                f"{name}::rms={disagreement_rms}::"
                f"objectives={[item[0] for item in best_three]}::"
                f"parameters={[item[1].tolist() for item in best_three]}"
            )

    objective_value, parameters, _, offsets, gate = best_three[0]
    offsets_tuple = tuple(float(value) for value in offsets)
    return FitResult(
        candidate=name,
        parameters=parameters,
        objective=objective_value,
        source_offsets=offsets_tuple,
        anchor_profile_sha256=canonical_sha256(offsets_tuple),
        numerical_gate=gate,
        admissible_start_count=len(confirmed),
        optimizer_runs=tuple(run_receipts),
    )


def source_losses(
    sources: Sequence[SourceData], name: str, parameters: np.ndarray
) -> dict[tuple[str, str], float]:
    result: dict[tuple[str, str], float] = {}
    for source in sources:
        _, loss, _ = source_profile_and_loss(source, name, parameters)
        key = (source.subject, source.source_id)
        if key in result:
            raise FitError(f"duplicate source key: {key}")
        result[key] = loss
    return result


def participant_improvements(
    sources: Sequence[SourceData],
    baseline_parameters: np.ndarray,
    winner_name: str,
    winner_parameters: np.ndarray,
) -> tuple[dict[str, float], dict[tuple[str, str], float]]:
    baseline = source_losses(sources, "S0", baseline_parameters)
    winner = source_losses(sources, winner_name, winner_parameters)
    improvements = {key: baseline[key] - winner[key] for key in baseline}
    by_subject: dict[str, list[float]] = {}
    for (subject, _), value in improvements.items():
        by_subject.setdefault(subject, []).append(value)
    participant = {subject: float(np.mean(values)) for subject, values in by_subject.items()}
    return participant, improvements


def deterministic_u64(seed_material: str, index: int) -> int:
    digest = hashlib.sha256(f"{seed_material}::{index}".encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big", signed=False)


def participant_bootstrap(
    participant_values: Mapping[str, float],
    *,
    replicates: int,
    seed_material: str,
    lower_quantile: float,
) -> dict[str, Any]:
    subjects = sorted(participant_values)
    values = np.asarray([participant_values[subject] for subject in subjects], dtype=np.float64)
    if values.size == 0 or not np.isfinite(values).all():
        raise FitError("participant bootstrap values are empty or nonfinite")
    replicate_means = np.empty(replicates, dtype=np.float64)
    index_hash = hashlib.sha256()
    for replicate in range(replicates):
        generator = np.random.Generator(np.random.PCG64(deterministic_u64(seed_material, replicate)))
        indexes = generator.integers(0, values.size, size=values.size, dtype=np.int64)
        index_hash.update(indexes.astype("<i8", copy=False).tobytes())
        replicate_means[replicate] = float(np.mean(values[indexes]))
    return {
        "replicates": int(replicates),
        "observed_mean": float(np.mean(values)),
        "positive_participants": int(np.sum(values > 0.0)),
        "participant_count": int(values.size),
        "lower_quantile": float(lower_quantile),
        "lower_bound": float(
            np.quantile(replicate_means, lower_quantile, method="linear")
        ),
        "index_array_sha256": index_hash.hexdigest(),
    }
