"""Preregistered rapid-correction analysis for DANDI 001371 development sessions."""
from __future__ import annotations

import json
import sys
from collections import Counter
from urllib.request import Request, urlopen

import fsspec
import h5py
import numpy as np


SESSIONS = {
    "S34-220623": {
        "url": "https://dandiarchive.s3.amazonaws.com/blobs/228/335/22833560-350d-4b1f-a5ac-4d3ae852ed54",
        "sha256": "49e1d8083b930a11b93b59fe278c875adfd75009646d4dc76bcc4f611bb24726",
        "spike_times_offset": 348_125_311_952,
        "spike_times_count": 3_393_215,
    },
    "S25-210916": {
        "url": "https://dandiarchive.s3.amazonaws.com/blobs/96b/dbc/96bdbcdd-4b59-472e-8fbd-e612fc3135e5",
        "sha256": "04c32ace10b668710605b05fc40d75c678364d54f749dafc94affa5c0b8a3b9b",
        "spike_times_offset": 198_943_705_899,
        "spike_times_count": 1_504_386,
    },
}
WINDOWS = {"pre": (-1.0, -0.2), "post": (0.2, 1.0)}


def _strings(values: np.ndarray) -> np.ndarray:
    return np.asarray([value.decode() if isinstance(value, bytes) else str(value) for value in values])


def load_remote(session: str) -> dict[str, object]:
    spec = SESSIONS[session]
    remote = fsspec.open(spec["url"], "rb", block_size=4 * 1024 * 1024, cache_type="bytes").open()
    nwb = h5py.File(remote, "r", driver="fileobj")
    try:
        trials = nwb["intervals/trials"]
        trial_columns = {
            name: np.asarray(trials[name])
            for name in (
                "start_time", "stop_time", "maze_id", "update_type", "choice", "correct",
                "duration", "t_update", "t_choice_made",
            )
        }
        units = nwb["units"]
        spike_index = np.asarray(units["spike_times_index"], dtype=int)
        metadata = {
            "session": session,
            "sha256": spec["sha256"],
            "trials": trial_columns,
            "regions": _strings(np.asarray(units["region"])),
            "quality": _strings(np.asarray(units["quality"])),
        }
    finally:
        nwb.close()
        remote.close()
    byte_count = int(spec["spike_times_count"]) * 8
    offset = int(spec["spike_times_offset"])
    request = Request(spec["url"], headers={"Range": f"bytes={offset}-{offset + byte_count - 1}"})
    with urlopen(request, timeout=180) as response:
        payload = response.read()
    if len(payload) != byte_count:
        raise RuntimeError("UPDATE_TASK_APPARATUS_STOP: incomplete spike-time range")
    spike_times = np.frombuffer(payload, dtype="<f8").copy()
    starts = np.r_[0, spike_index[:-1]]
    metadata["unit_spikes"] = [spike_times[start:stop] for start, stop in zip(starts, spike_index)]
    return metadata


def _rates(unit_spikes: list[np.ndarray], centers: np.ndarray, window: tuple[float, float]) -> np.ndarray:
    width = window[1] - window[0]
    result = np.empty((len(centers), len(unit_spikes)), dtype=float)
    for column, spikes in enumerate(unit_spikes):
        left = np.searchsorted(spikes, centers + window[0], side="left")
        right = np.searchsorted(spikes, centers + window[1], side="left")
        result[:, column] = (right - left) / width
    return np.log1p(result)


def _balanced_accuracy(target: np.ndarray, predicted: np.ndarray) -> float:
    scores = [np.mean(predicted[target == label] == label) for label in (-1, 1) if np.any(target == label)]
    return float(np.mean(scores)) if len(scores) == 2 else float("nan")


def _fit_axis(x: np.ndarray, target: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    center = x.mean(axis=0)
    scale = x.std(axis=0)
    scale[scale < 1e-8] = 1.0
    z = (x - center) / scale
    axis = z[target == 1].mean(axis=0) - z[target == -1].mean(axis=0)
    norm = np.linalg.norm(axis)
    if not np.isfinite(norm) or norm == 0:
        raise RuntimeError("CHOICE_AXIS_SENSITIVITY_NOT_ESTABLISHED: degenerate axis")
    return axis / norm, np.vstack([center, scale])


def _project(x: np.ndarray, axis: np.ndarray, normalization: np.ndarray) -> np.ndarray:
    return ((x - normalization[0]) / normalization[1]) @ axis


def _did(delta: np.ndarray, update_type: np.ndarray) -> float:
    return float(delta[update_type == 2].mean() - delta[update_type == 3].mean())


def analyze_region(
    trials: dict[str, np.ndarray],
    unit_spikes: list[np.ndarray],
    region_mask: np.ndarray,
    *,
    permutations: int = 2000,
    bootstraps: int = 2000,
    seed: int = 1371,
) -> dict[str, object]:
    duration_limit = float(np.nanmean(trials["duration"]) * 2)
    base = (trials["maze_id"] == 4) & (trials["duration"] <= duration_limit)
    correct = base & (trials["correct"] == 1)
    switch_lags = trials["t_choice_made"][correct & (trials["update_type"] == 2)] - trials["t_update"][correct & (trials["update_type"] == 2)]
    lag = float(np.nanmedian(switch_lags))
    if not np.isfinite(lag):
        raise RuntimeError("UPDATE_TASK_APPARATUS_STOP: no switch lag")
    centers = np.asarray(trials["t_update"], dtype=float).copy()
    non_update = trials["update_type"] == 1
    centers[non_update] = trials["t_choice_made"][non_update] - lag
    selected_spikes = [spikes for spikes, keep in zip(unit_spikes, region_mask) if keep]
    pre = _rates(selected_spikes, centers, WINDOWS["pre"])
    post = _rates(selected_spikes, centers, WINDOWS["post"])
    target = np.where(trials["choice"] == 2, 1, -1)

    non_indices = np.flatnonzero(correct & non_update & np.isfinite(centers))
    cut = int(np.floor(0.7 * len(non_indices)))
    train, test = non_indices[:cut], non_indices[cut:]
    axis, normalization = _fit_axis(pre[train], target[train])
    test_projection = _project(pre[test], axis, normalization)
    observed_accuracy = _balanced_accuracy(target[test], np.where(test_projection >= 0, 1, -1))

    rng = np.random.default_rng(seed)
    null_accuracy = []
    for _ in range(permutations):
        permuted = rng.permutation(target[train])
        if len(np.unique(permuted)) < 2:
            continue
        null_axis, null_norm = _fit_axis(pre[train], permuted)
        null_projection = _project(pre[test], null_axis, null_norm)
        null_accuracy.append(_balanced_accuracy(target[test], np.where(null_projection >= 0, 1, -1)))
    accuracy_p = float((1 + np.sum(np.asarray(null_accuracy) >= observed_accuracy)) / (1 + len(null_accuracy)))

    update_indices = np.flatnonzero(correct & np.isin(trials["update_type"], [2, 3]) & np.isfinite(centers))
    pre_projection = _project(pre[update_indices], axis, normalization) * target[update_indices]
    post_projection = _project(post[update_indices], axis, normalization) * target[update_indices]
    delta = post_projection - pre_projection
    update_types = trials["update_type"][update_indices]
    choices = trials["choice"][update_indices]
    did = _did(delta, update_types)

    null_did = []
    halves = np.arange(len(update_indices)) >= len(update_indices) / 2
    for _ in range(permutations):
        permuted = update_types.copy()
        for choice in (1, 2):
            for half in (False, True):
                stratum = (choices == choice) & (halves == half)
                permuted[stratum] = rng.permutation(permuted[stratum])
        null_did.append(_did(delta, permuted))
    did_p = float((1 + np.sum(np.asarray(null_did) >= did)) / (1 + len(null_did)))

    switch_delta, stay_delta = delta[update_types == 2], delta[update_types == 3]
    bootstrap_did = np.empty(bootstraps, dtype=float)
    for index in range(bootstraps):
        bootstrap_did[index] = float(
            rng.choice(switch_delta, len(switch_delta), replace=True).mean()
            - rng.choice(stay_delta, len(stay_delta), replace=True).mean()
        )
    ci = np.quantile(bootstrap_did, [0.025, 0.975])
    sensitivity = bool(observed_accuracy >= 0.60 and accuracy_p < 0.01)
    correction = bool(sensitivity and did > 0 and did_p < 0.01 and ci[0] > 0)
    return {
        "units": int(region_mask.sum()),
        "lag_seconds": lag,
        "non_update_train": int(len(train)),
        "non_update_test": int(len(test)),
        "switch_correct": int(np.sum(update_types == 2)),
        "stay_correct": int(np.sum(update_types == 3)),
        "choice_axis_balanced_accuracy": observed_accuracy,
        "choice_axis_permutation_p": accuracy_p,
        "choice_axis_sensitivity": sensitivity,
        "switch_delta": float(switch_delta.mean()),
        "stay_delta": float(stay_delta.mean()),
        "did": did,
        "did_permutation_p": did_p,
        "did_bootstrap_ci95": ci.tolist(),
        "rapid_correction_code": correction,
    }


def analyze_session(data: dict[str, object], **kwargs: int) -> dict[str, object]:
    regions = np.asarray(data["regions"])
    quality = np.asarray(data["quality"])
    results = {
        region: analyze_region(
            data["trials"], data["unit_spikes"], (regions == region) & (quality == "good"), **kwargs,
        )
        for region in ("CA1", "PFC")
    }
    return {
        "session": data["session"],
        "sha256": data["sha256"],
        "trial_counts": dict(Counter(np.asarray(data["trials"]["update_type"]).tolist())),
        "regions": results,
    }


def run() -> dict[str, object]:
    sessions = []
    for session in SESSIONS:
        print(f"loading {session}", file=sys.stderr, flush=True)
        sessions.append(analyze_session(load_remote(session)))
        print(f"scored {session}", file=sys.stderr, flush=True)
    replicated = all(item["regions"]["PFC"]["rapid_correction_code"] for item in sessions)
    return {
        "decision": (
            "RAPID_CORRECTION_CODE_ESTABLISHED_REPLICATED"
            if replicated else "RAPID_CORRECTION_CODE_NOT_ESTABLISHED_REPLICATED"
        ),
        "sessions": sessions,
        "claim_ceiling": "within-trial correction only; persistent v_C and READ/WRITE separation untested",
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, sort_keys=True))
