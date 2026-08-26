"""Frozen v5 CAR75 site-tile endpoint and development gate."""
from __future__ import annotations

import math
from typing import Any, Mapping, Sequence

import numpy as np

BASELINE = slice(0, 1014)
EARLY = slice(1045, 1127)
PRESTIM = slice(512, 594)
WINDOW_SAMPLES = 1127
STOP = "APPARATUS_DEVELOPMENT_ENDPOINT_STOP"


def car75_masks(tile: np.ndarray, *, stimulated: Sequence[int]) -> np.ndarray:
    """Select floor(75%) reference channels per trial from baseline variance only."""
    values = np.asarray(tile, dtype=np.float64)
    if values.ndim != 3 or values.shape[2] != WINDOW_SAMPLES or not np.all(np.isfinite(values)):
        raise ValueError(f"{STOP}:tile")
    candidates = np.ones(values.shape[1], dtype=bool)
    for index in stimulated:
        if type(index) is not int or index < 0 or index >= values.shape[1]:
            raise ValueError(f"{STOP}:stimulated contact")
        candidates[index] = False
    candidate_indices = np.flatnonzero(candidates)
    count = math.floor(0.75 * len(candidate_indices))
    if count < 1 or count >= len(candidate_indices):
        raise ValueError(f"{STOP}:CAR75 cardinality")
    masks = np.zeros(values.shape[:2], dtype=bool)
    for trial in range(values.shape[0]):
        variance = np.var(values[trial, candidate_indices, BASELINE], axis=1, ddof=1)
        if not np.all(np.isfinite(variance)):
            raise ValueError(f"{STOP}:baseline variance")
        order = np.lexsort((candidate_indices, variance))
        ranked = candidate_indices[order]
        ranked_variance = variance[order]
        if ranked_variance[count - 1] == ranked_variance[count]:
            raise ValueError(f"{STOP}:CAR75 cutoff tie")
        masks[trial, ranked[:count]] = True
    return masks


def site_endpoints(tile: np.ndarray, *, stimulated: Sequence[int], halves: Sequence[str],
                   receiver_contacts: Mapping[str, tuple[int, int]]) -> dict[str, Any]:
    """Compute mean/bip early+prestim endpoints from one site's transient trial tile."""
    values = np.asarray(tile, dtype=np.float64)
    if values.ndim != 3 or values.shape[2] != WINDOW_SAMPLES or len(halves) != values.shape[0]:
        raise ValueError(f"{STOP}:site tile")
    labels = np.asarray(list(halves))
    if set(labels) != {"A", "B"}:
        raise ValueError(f"{STOP}:halves")
    masks = car75_masks(values, stimulated=stimulated)
    reference = np.empty((values.shape[0], WINDOW_SAMPLES), dtype=np.float64)
    for trial in range(values.shape[0]):
        reference[trial] = values[trial, masks[trial]].mean(axis=0)
    car = values - reference[:, None, :]
    residual = car - car[:, :, BASELINE].mean(axis=2, keepdims=True)
    output: dict[str, Any] = {}
    for node, pair in receiver_contacts.items():
        if (len(pair) != 2 or any(type(index) is not int or index < 0 or index >= values.shape[1] for index in pair)
                or pair[0] == pair[1]):
            raise ValueError(f"{STOP}:receiver pair")
        if not np.allclose(car[:, pair[0]] - car[:, pair[1]], values[:, pair[0]] - values[:, pair[1]],
                           rtol=1e-12, atol=1e-12):
            raise RuntimeError(f"{STOP}:bipolar CAR cancellation")
        per_half: dict[str, Any] = {}
        for half in ("A", "B"):
            selected = residual[labels == half][:, pair]
            if selected.shape[0] == 0:
                raise ValueError(f"{STOP}:empty half")
            contact_scale = np.std(selected[:, :, BASELINE], axis=(0, 2), ddof=0)
            contact_wave = selected.mean(axis=0)
            difference = selected[:, 0] - selected[:, 1]
            bip_scale = float(np.std(difference[:, BASELINE], ddof=0))
            bip_wave = difference.mean(axis=0)
            if (not np.all(np.isfinite(contact_scale)) or np.any(contact_scale <= 0)
                    or not math.isfinite(bip_scale) or bip_scale <= 0):
                raise ValueError(f"{STOP}:scale")
            per_half[half] = {
                "mean": {"early": float(np.mean(np.max(np.abs(contact_wave[:, EARLY]), axis=1) / contact_scale)),
                         "prestim": float(np.mean(np.max(np.abs(contact_wave[:, PRESTIM]), axis=1) / contact_scale))},
                "bip": {"early": float(np.max(np.abs(bip_wave[EARLY])) / bip_scale),
                        "prestim": float(np.max(np.abs(bip_wave[PRESTIM])) / bip_scale)},
            }
        output[node] = per_half
    mask_rows = [np.flatnonzero(row).tolist() for row in masks]
    return {"endpoints": output, "car75_masks": mask_rows, "selected_per_trial": int(masks[0].sum()),
            "trials": values.shape[0], "channels": values.shape[1]}


def _midranks(values: np.ndarray) -> np.ndarray:
    order = np.argsort(values, kind="mergesort")
    ranks = np.empty(len(values), dtype=np.float64)
    start = 0
    while start < len(values):
        end = start + 1
        while end < len(values) and values[order[end]] == values[order[start]]:
            end += 1
        ranks[order[start:end]] = (start + end - 1) / 2
        start = end
    return ranks


def development_gate(directed: Mapping[str, Mapping[str, Mapping[str, float]]], *, held_out_pairs: int) -> dict[str, Any]:
    """Evaluate frozen directed-edge development vectors for both readouts."""
    if type(held_out_pairs) is not int or held_out_pairs < 20 or not directed:
        raise ValueError(f"{STOP}:gate population")
    result: dict[str, Any] = {}
    for readout in ("mean", "bip"):
        a = np.asarray([directed[key]["A"][readout + "_early"] for key in sorted(directed)], dtype=np.float64)
        b = np.asarray([directed[key]["B"][readout + "_early"] for key in sorted(directed)], dtype=np.float64)
        p = np.asarray([directed[key][half][readout + "_prestim"] for key in sorted(directed) for half in ("A", "B")],
                       dtype=np.float64)
        if (len(a) < 2 or not np.all(np.isfinite(a)) or not np.all(np.isfinite(b)) or not np.all(np.isfinite(p))
                or np.ptp(a) == 0 or np.ptp(b) == 0 or np.median(p) <= 0):
            raise ValueError(f"{STOP}:undefined gate statistic")
        rho = float(np.corrcoef(_midranks(a), _midranks(b))[0, 1])
        ratio = float(np.median(np.concatenate((a, b))) / np.median(p))
        result[readout] = {"spearman": rho, "early_over_prestim": ratio, "directed_edges": len(a),
                           "pass": rho >= 0.50 and ratio >= 1.25}
    return {"status": "DEVELOPMENT_PASS" if all(row["pass"] for row in result.values()) else "APPARATUS_OR_EVOCATION_STOP",
            "readouts": result, "held_out_pairs": held_out_pairs, "confirmation_serialized": False}
