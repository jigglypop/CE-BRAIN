"""Official-family Poisson choice decoder R2 for DANDI 001371."""
from __future__ import annotations

import json
import sys
from urllib.request import Request, urlopen

import fsspec
import h5py
import numpy as np


SESSIONS = {
    "S29-211118": {
        "url": "https://dandiarchive.s3.amazonaws.com/blobs/901/6f3/9016f363-a91f-4905-ab13-710fff634ba7",
        "sha256": "7919c495c2c5e21d1fbd0b0edc7c2607a42c99477df3187878fb0e1ecedb7a72",
        "spike_times_offset": 302_178_905_898,
        "spike_times_count": 2_785_047,
    },
    "S20-210519": {
        "url": "https://dandiarchive.s3.amazonaws.com/blobs/32b/39e/32b39e0e-de4d-4e1a-af2d-b65861e16ef9",
        "sha256": "5c7240159fe40e9b0fb089b522fd5ca15afa45e7370d7788b224125002d80b9b",
        "spike_times_offset": 238_042_610_507,
        "spike_times_count": 2_289_030,
    },
}
CELL_TYPES = {"Pyramidal Cell", "Narrow Interneuron", "Wide Interneuron"}
PRE = (-1.0, -0.2)
POST = (0.2, 1.0)


def _strings(values: np.ndarray) -> np.ndarray:
    return np.asarray([value.decode() if isinstance(value, bytes) else str(value) for value in values])


def load_remote(session: str) -> dict[str, object]:
    spec = SESSIONS[session]
    remote = fsspec.open(spec["url"], "rb", block_size=1024 * 1024, cache_type="bytes").open()
    nwb = h5py.File(remote, "r", driver="fileobj")
    try:
        group = nwb["intervals/trials"]
        trials = {
            name: np.asarray(group[name])
            for name in (
                "start_time", "stop_time", "maze_id", "update_type", "choice", "correct",
                "t_update",
            )
        }
        units = nwb["units"]
        spike_index = np.asarray(units["spike_times_index"], dtype=int)
        metadata = {
            "session": session,
            "sha256": spec["sha256"],
            "trials": trials,
            "regions": _strings(np.asarray(units["region"])),
            "cell_types": _strings(np.asarray(units["cell_type"])),
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


def _counts(unit_spikes: list[np.ndarray], starts: np.ndarray, stops: np.ndarray) -> np.ndarray:
    result = np.empty((len(starts), len(unit_spikes)), dtype=float)
    for column, spikes in enumerate(unit_spikes):
        left = np.searchsorted(spikes, starts, side="left")
        right = np.searchsorted(spikes, stops, side="left")
        result[:, column] = right - left
    return result


def _fit_rates(counts: np.ndarray, durations: np.ndarray, target: np.ndarray) -> np.ndarray:
    rates = []
    for label in (-1, 1):
        mask = target == label
        rates.append(counts[mask].sum(axis=0) / durations[mask].sum())
    return np.maximum(np.asarray(rates), 1e-6)


def _log_odds(counts: np.ndarray, durations: np.ndarray, rates: np.ndarray) -> np.ndarray:
    expected = durations[:, None, None] * rates[None, :, :]
    log_likelihood = (counts[:, None, :] * np.log(expected) - expected).sum(axis=2)
    return log_likelihood[:, 1] - log_likelihood[:, 0]


def _balanced_accuracy(target: np.ndarray, predicted: np.ndarray) -> float:
    return float(np.mean([np.mean(predicted[target == label] == label) for label in (-1, 1)]))


def _did(delta: np.ndarray, update_type: np.ndarray) -> float:
    return float(delta[update_type == 2].mean() - delta[update_type == 3].mean())


def _split(indices: np.ndarray, seed: int) -> tuple[np.ndarray, np.ndarray]:
    shuffled = np.random.RandomState(seed).permutation(indices)
    test_size = int(np.ceil(0.2 * len(indices)))
    return np.sort(shuffled[test_size:]), np.sort(shuffled[:test_size])


def analyze_region(
    trials: dict[str, np.ndarray],
    unit_spikes: list[np.ndarray],
    unit_mask: np.ndarray,
    *,
    permutations: int = 2000,
    bootstraps: int = 2000,
    seed: int = 21,
) -> dict[str, object]:
    spikes = [values for values, keep in zip(unit_spikes, unit_mask) if keep]
    target = np.where(trials["choice"] == 2, 1, -1)
    encoder = (trials["update_type"] == 1) & np.isin(trials["maze_id"], [3, 4])
    encoder_indices = np.flatnonzero(encoder)
    train, test = _split(encoder_indices, seed)
    starts, stops = trials["start_time"], trials["stop_time"]
    train_counts = _counts(spikes, starts[train], stops[train])
    test_counts = _counts(spikes, starts[test], stops[test])
    train_duration = stops[train] - starts[train]
    test_duration = stops[test] - starts[test]
    rates = _fit_rates(train_counts, train_duration, target[train])
    odds = _log_odds(test_counts, test_duration, rates)
    accuracy = _balanced_accuracy(target[test], np.where(odds >= 0, 1, -1))

    rng = np.random.default_rng(seed)
    null_accuracy = np.empty(permutations, dtype=float)
    for index in range(permutations):
        permuted = rng.permutation(target[train])
        null_rates = _fit_rates(train_counts, train_duration, permuted)
        null_odds = _log_odds(test_counts, test_duration, null_rates)
        null_accuracy[index] = _balanced_accuracy(target[test], np.where(null_odds >= 0, 1, -1))
    accuracy_p = float((1 + np.sum(null_accuracy >= accuracy)) / (1 + permutations))

    update = np.flatnonzero(
        (trials["maze_id"] == 4)
        & np.isin(trials["update_type"], [2, 3])
        & (trials["correct"] == 1)
        & np.isfinite(trials["t_update"])
    )
    align = trials["t_update"][update]
    pre_counts = _counts(spikes, align + PRE[0], align + PRE[1])
    post_counts = _counts(spikes, align + POST[0], align + POST[1])
    window_duration = np.full(len(update), PRE[1] - PRE[0])
    pre_odds = _log_odds(pre_counts, window_duration, rates) * target[update]
    post_odds = _log_odds(post_counts, window_duration, rates) * target[update]
    delta = post_odds - pre_odds
    update_type = trials["update_type"][update]
    choices = trials["choice"][update]
    did = _did(delta, update_type)

    null_did = np.empty(permutations, dtype=float)
    halves = np.arange(len(update)) >= len(update) / 2
    for index in range(permutations):
        permuted = update_type.copy()
        for choice in (1, 2):
            for half in (False, True):
                stratum = (choices == choice) & (halves == half)
                permuted[stratum] = rng.permutation(permuted[stratum])
        null_did[index] = _did(delta, permuted)
    did_p = float((1 + np.sum(null_did >= did)) / (1 + permutations))
    switch, stay = delta[update_type == 2], delta[update_type == 3]
    bootstrap = np.empty(bootstraps, dtype=float)
    for index in range(bootstraps):
        bootstrap[index] = rng.choice(switch, len(switch), replace=True).mean() - rng.choice(stay, len(stay), replace=True).mean()
    ci = np.quantile(bootstrap, [0.025, 0.975])
    sensitivity = bool(accuracy >= 0.60 and accuracy_p < 0.01)
    correction = bool(sensitivity and did > 0 and did_p < 0.01 and ci[0] > 0)
    return {
        "units": int(unit_mask.sum()),
        "encoder_train": int(len(train)),
        "encoder_test": int(len(test)),
        "switch_correct": int(np.sum(update_type == 2)),
        "stay_correct": int(np.sum(update_type == 3)),
        "choice_balanced_accuracy": accuracy,
        "choice_permutation_p": accuracy_p,
        "choice_sensitivity": sensitivity,
        "switch_delta": float(switch.mean()),
        "stay_delta": float(stay.mean()),
        "did": did,
        "did_permutation_p": did_p,
        "did_bootstrap_ci95": ci.tolist(),
        "rapid_correction_code": correction,
    }


def analyze_session(data: dict[str, object]) -> dict[str, object]:
    regions = np.asarray(data["regions"])
    cell_types = np.asarray(data["cell_types"])
    cell_mask = np.isin(cell_types, list(CELL_TYPES))
    return {
        "session": data["session"],
        "sha256": data["sha256"],
        "regions": {
            region: analyze_region(
                data["trials"], data["unit_spikes"], (regions == region) & cell_mask,
            )
            for region in ("CA1", "PFC")
        },
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
            "RAPID_CORRECTION_POISSON_CODE_ESTABLISHED_REPLICATED"
            if replicated else "RAPID_CORRECTION_POISSON_CODE_NOT_ESTABLISHED_REPLICATED"
        ),
        "sessions": sessions,
        "claim_ceiling": "within-trial correction only; persistent v_C and READ/WRITE separation untested",
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, sort_keys=True))
