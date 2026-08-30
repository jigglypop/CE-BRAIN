"""Preregistered relational retrieval development test on DANDI 000004."""
from __future__ import annotations

import hashlib

import h5py
import numpy as np
from scipy.stats import spearmanr

from examples.brain import ce_brain_human_memory_apparatus as apparatus

SEED = 4004
PERMUTATIONS = 5000
BOOTSTRAPS = 2000
BIN_EDGES = np.linspace(0.0, 1.0, 5)


def _cosine(left: np.ndarray, right: np.ndarray) -> np.ndarray:
    numerator = np.sum(left * right, axis=1)
    denominator = np.linalg.norm(left, axis=1) * np.linalg.norm(right, axis=1)
    return numerator / np.maximum(denominator, 1e-12)


def _phase_zscore(values: np.ndarray) -> np.ndarray:
    mean = values.mean(axis=0, keepdims=True)
    scale = values.std(axis=0, keepdims=True)
    scale[scale < 1e-9] = 1.0
    return (values - mean) / scale


def _category_permutation(categories: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    order = np.arange(len(categories))
    for category in np.unique(categories):
        indices = np.flatnonzero(categories == category)
        order[indices] = rng.permutation(indices)
    return order


def _one_sided_p(observed: float, null: np.ndarray) -> float:
    return float((1 + np.sum(null >= observed)) / (len(null) + 1))


def analyze(path=apparatus.FILE, expected_sha256: str = apparatus.EXPECTED_SHA256) -> dict[str, object]:
    if apparatus.audit_file(path, expected_sha256)["decision"] != "HUMAN_MEMORY_RELATIONAL_APPARATUS_ELIGIBLE":
        raise RuntimeError("HUMAN_MEMORY_RELATIONAL_STOP: apparatus")
    with h5py.File(path, "r") as nwb:
        trials = nwb["intervals/trials"]
        phases = np.asarray([value.decode() for value in trials["stim_phase"][:]])
        categories = np.asarray([value.decode() for value in trials["category_name"][:]])
        responses = np.asarray(trials["response_value"], dtype=float)
        onset = np.asarray(trials["stim_on_time"], dtype=float)
        images = nwb["stimulus/presentation/StimulusPresentation/data"]
        image_hashes = np.asarray([hashlib.sha256(images[index].tobytes()).hexdigest() for index in range(len(images))])
        all_spikes = np.asarray(nwb["units/spike_times"])
        spike_index = np.asarray(nwb["units/spike_times_index"], dtype=int)
        unit_ids = np.asarray(nwb["units/id"], dtype=int)

    starts = np.r_[0, spike_index[:-1]]
    duration = float(onset.max() - onset.min() + 2.0)
    firing_rate = (spike_index - starts) / duration
    counts = np.zeros((len(onset), len(unit_ids), 4), dtype=float)
    nonzero = np.zeros((len(onset), len(unit_ids)), dtype=bool)
    for unit, (left, right) in enumerate(zip(starts, spike_index)):
        spikes = all_spikes[left:right]
        for trial, trial_onset in enumerate(onset):
            baseline_count = np.searchsorted(spikes, trial_onset) - np.searchsorted(spikes, trial_onset - 0.5)
            edges = trial_onset + BIN_EDGES
            binned = np.diff(np.searchsorted(spikes, edges))
            counts[trial, unit] = binned / 0.25 - baseline_count / 0.5
            nonzero[trial, unit] = binned.sum() > 0
    keep = (firing_rate >= 0.05) & (nonzero.mean(axis=0) >= 0.05)
    if keep.sum() < 10:
        raise RuntimeError("HUMAN_MEMORY_RELATIONAL_STOP: eligible units")
    counts = counts[:, keep]
    learning_indices = np.flatnonzero(phases == "learn")
    recognition_indices = np.flatnonzero(phases == "recog")
    representation = np.zeros_like(counts)
    representation[learning_indices] = _phase_zscore(counts[learning_indices])
    representation[recognition_indices] = _phase_zscore(counts[recognition_indices])

    learning_by_hash = {image_hashes[index]: index for index in learning_indices}
    old_recognition = np.asarray([index for index in recognition_indices if image_hashes[index] in learning_by_hash])
    encoding = np.asarray([representation[learning_by_hash[image_hashes[index]]] for index in old_recognition])
    recognition = representation[old_recognition]
    old_categories = categories[old_recognition]
    old_responses = responses[old_recognition]
    remembered = old_responses >= 34
    forgotten = ~remembered
    encoding_flat = encoding.reshape(len(encoding), -1)
    recognition_flat = recognition.reshape(len(recognition), -1)
    pair_cosine = _cosine(encoding_flat, recognition_flat)

    rng = np.random.default_rng(SEED)
    remembered_encoding = encoding_flat[remembered]
    remembered_recognition = recognition_flat[remembered]
    remembered_categories = old_categories[remembered]
    observed_pair = float(pair_cosine[remembered].mean())
    pair_null = np.empty(PERMUTATIONS)
    geometry_null = np.empty(PERMUTATIONS)
    upper = np.triu_indices(remembered.sum(), 1)
    encode_distance = np.linalg.norm(remembered_encoding[:, None] - remembered_encoding[None, :], axis=2)[upper]
    recognition_distance_matrix = np.linalg.norm(
        remembered_recognition[:, None] - remembered_recognition[None, :], axis=2
    )
    geometry_rho = float(spearmanr(encode_distance, recognition_distance_matrix[upper]).statistic)
    for iteration in range(PERMUTATIONS):
        order = _category_permutation(remembered_categories, rng)
        shuffled = remembered_recognition[order]
        pair_null[iteration] = _cosine(remembered_encoding, shuffled).mean()
        shuffled_distance = np.linalg.norm(shuffled[:, None] - shuffled[None, :], axis=2)[upper]
        geometry_null[iteration] = spearmanr(encode_distance, shuffled_distance).statistic
    pair_advantage = float(observed_pair - pair_null.mean())
    pair_p = _one_sided_p(observed_pair, pair_null)
    geometry_p = _one_sided_p(geometry_rho, geometry_null)

    confidence_rho = float(spearmanr(pair_cosine, old_responses).statistic)
    confidence_null = np.empty(PERMUTATIONS)
    for iteration in range(PERMUTATIONS):
        confidence_null[iteration] = spearmanr(
            pair_cosine, old_responses[_category_permutation(old_categories, rng)]
        ).statistic
    confidence_p = _one_sided_p(confidence_rho, confidence_null)

    remembered_forgotten = float(pair_cosine[remembered].mean() - pair_cosine[forgotten].mean())
    memory_bootstrap = np.empty(BOOTSTRAPS)
    for iteration in range(BOOTSTRAPS):
        remembered_sample = rng.choice(pair_cosine[remembered], remembered.sum(), replace=True)
        forgotten_sample = rng.choice(pair_cosine[forgotten], forgotten.sum(), replace=True)
        memory_bootstrap[iteration] = remembered_sample.mean() - forgotten_sample.mean()
    memory_ci = np.quantile(memory_bootstrap, (0.025, 0.975))

    reversed_recognition = recognition[remembered, ::-1, :].reshape(remembered.sum(), -1)
    correct_order = _cosine(remembered_encoding, remembered_recognition)
    reversed_order = _cosine(remembered_encoding, reversed_recognition)
    order_difference = correct_order - reversed_order
    order_bootstrap = np.empty(BOOTSTRAPS)
    for iteration in range(BOOTSTRAPS):
        order_bootstrap[iteration] = rng.choice(order_difference, len(order_difference), replace=True).mean()
    order_ci = np.quantile(order_bootstrap, (0.025, 0.975))
    order_advantage = float(order_difference.mean())

    relational = bool(
        pair_advantage >= 0.05 and pair_p <= 0.01
        and geometry_rho >= 0.20 and geometry_p <= 0.01
        and confidence_rho >= 0.20 and confidence_p <= 0.01
        and remembered_forgotten >= 0.05 and memory_ci[0] > 0
    )
    temporal = relational and order_advantage >= 0.03 and order_ci[0] > 0
    decision = (
        "TEMPORAL_RELATIONAL_RETRIEVAL_DEVELOPMENT_CANDIDATE" if temporal
        else "RELATIONAL_RETRIEVAL_DEVELOPMENT_CANDIDATE" if relational
        else "HUMAN_RELATIONAL_RETRIEVAL_NOT_ESTABLISHED"
    )
    return {
        "decision": decision,
        "file": path.name,
        "eligible_units": int(keep.sum()),
        "old_pairs": len(old_recognition),
        "remembered_pairs": int(remembered.sum()),
        "forgotten_pairs": int(forgotten.sum()),
        "remembered_matched_cosine": observed_pair,
        "category_shuffle_cosine_mean": float(pair_null.mean()),
        "matched_cosine_advantage": pair_advantage,
        "matched_cosine_permutation_p": pair_p,
        "relational_geometry_spearman_rho": geometry_rho,
        "relational_geometry_permutation_p": geometry_p,
        "confidence_spearman_rho": confidence_rho,
        "confidence_permutation_p": confidence_p,
        "remembered_minus_forgotten_cosine": remembered_forgotten,
        "remembered_minus_forgotten_95ci": memory_ci.tolist(),
        "correct_minus_reversed_time_order_cosine": order_advantage,
        "time_order_95ci": order_ci.tolist(),
        "claim_ceiling": "one human development session; not animal rescue or Phase 14 confirmation",
    }
