"""R2 relational retrieval test using the official memory-signal window."""
from __future__ import annotations

import hashlib
from pathlib import Path

import h5py
import numpy as np
from scipy.stats import spearmanr

from examples.brain import ce_brain_human_memory_apparatus as apparatus
from examples.brain import ce_brain_human_memory_relational as r1

SESSIONS = {
    "P11HMH": (apparatus.DATA / "sub-P11HMH_ses-20061101_ecephys+image.nwb", "ed70cbaa4c9ac65a4365bb805e4fb2f8689de7e0f867f9a8247285980acf7781"),
    "P48CS": (apparatus.DATA / "sub-P48CS_ses-20170301_ecephys+image.nwb", "581bcea63021620e9cebfd24a407f2a0c28e7c0cefefb4b1b4c1f54c6e9f4e23"),
}
BIN_EDGES = np.linspace(0.2, 1.7, 7)
PERMUTATIONS = 5000
BOOTSTRAPS = 2000
SEED = 40042


def analyze_session(subject: str, path: Path, expected_hash: str) -> dict[str, object]:
    if apparatus.audit_file(path, expected_hash)["decision"] != "HUMAN_MEMORY_RELATIONAL_APPARATUS_ELIGIBLE":
        raise RuntimeError(f"HUMAN_MEMORY_R2_STOP: {subject} apparatus")
    with h5py.File(path, "r") as nwb:
        trials = nwb["intervals/trials"]
        phases = np.asarray([value.decode() for value in trials["stim_phase"][:]])
        categories = np.asarray([value.decode() for value in trials["category_name"][:]])
        responses = np.asarray(trials["response_value"], dtype=float)
        onset = np.asarray(trials["stim_on_time"], dtype=float)
        images = nwb["stimulus/presentation/StimulusPresentation/data"]
        hashes = np.asarray([hashlib.sha256(images[index].tobytes()).hexdigest() for index in range(len(images))])
        spikes = np.asarray(nwb["units/spike_times"])
        spike_index = np.asarray(nwb["units/spike_times_index"], dtype=int)
    starts = np.r_[0, spike_index[:-1]]
    counts = np.zeros((len(onset), len(spike_index), 6), dtype=float)
    for unit, (left, right) in enumerate(zip(starts, spike_index)):
        unit_spikes = spikes[left:right]
        for trial, trial_onset in enumerate(onset):
            counts[trial, unit] = np.diff(np.searchsorted(unit_spikes, trial_onset + BIN_EDGES)) / 0.25
    recognition_indices = np.flatnonzero(phases == "recog")
    keep = counts[recognition_indices].sum(axis=(0, 2)) > 0
    counts = counts[:, keep]
    if keep.sum() < 10:
        raise RuntimeError(f"HUMAN_MEMORY_R2_STOP: {subject} units")
    learning_indices = np.flatnonzero(phases == "learn")
    representation = np.zeros_like(counts)
    representation[learning_indices] = r1._phase_zscore(counts[learning_indices])
    representation[recognition_indices] = r1._phase_zscore(counts[recognition_indices])
    learning_by_hash = {hashes[index]: index for index in learning_indices}
    old_recognition = np.asarray([index for index in recognition_indices if hashes[index] in learning_by_hash])
    encoding = np.asarray([representation[learning_by_hash[hashes[index]]] for index in old_recognition])
    recognition = representation[old_recognition]
    old_categories = categories[old_recognition]
    old_responses = responses[old_recognition]
    correct = old_responses >= 34
    incorrect = ~correct
    if correct.sum() < 20 or incorrect.sum() < 5:
        raise RuntimeError(f"HUMAN_MEMORY_R2_STOP: {subject} behavior")
    if min(np.sum(old_categories[correct] == category) for category in np.unique(old_categories)) < 2:
        raise RuntimeError(f"HUMAN_MEMORY_R2_STOP: {subject} category coverage")
    encoding_flat = encoding.reshape(len(encoding), -1)
    recognition_flat = recognition.reshape(len(recognition), -1)
    pair_cosine = r1._cosine(encoding_flat, recognition_flat)
    correct_encoding = encoding_flat[correct]
    correct_recognition = recognition_flat[correct]
    correct_categories = old_categories[correct]
    observed_pair = float(pair_cosine[correct].mean())
    upper = np.triu_indices(correct.sum(), 1)
    encoding_distance = np.linalg.norm(correct_encoding[:, None] - correct_encoding[None, :], axis=2)[upper]
    recognition_distance_matrix = np.linalg.norm(
        correct_recognition[:, None] - correct_recognition[None, :], axis=2
    )
    geometry_rho = float(spearmanr(encoding_distance, recognition_distance_matrix[upper]).statistic)
    rng = np.random.default_rng(SEED + int(hashlib.sha256(subject.encode()).hexdigest()[:8], 16))
    pair_null = np.empty(PERMUTATIONS)
    geometry_null = np.empty(PERMUTATIONS)
    for iteration in range(PERMUTATIONS):
        order = r1._category_permutation(correct_categories, rng)
        shuffled = correct_recognition[order]
        pair_null[iteration] = r1._cosine(correct_encoding, shuffled).mean()
        shuffled_distance = np.linalg.norm(shuffled[:, None] - shuffled[None, :], axis=2)[upper]
        geometry_null[iteration] = spearmanr(encoding_distance, shuffled_distance).statistic
    pair_advantage = float(observed_pair - pair_null.mean())
    pair_p = r1._one_sided_p(observed_pair, pair_null)
    geometry_p = r1._one_sided_p(geometry_rho, geometry_null)
    confidence_rho = float(spearmanr(pair_cosine, old_responses).statistic)
    confidence_null = np.empty(PERMUTATIONS)
    for iteration in range(PERMUTATIONS):
        confidence_null[iteration] = spearmanr(
            pair_cosine, old_responses[r1._category_permutation(old_categories, rng)]
        ).statistic
    confidence_p = r1._one_sided_p(confidence_rho, confidence_null)
    correct_incorrect = float(pair_cosine[correct].mean() - pair_cosine[incorrect].mean())
    memory_bootstrap = np.empty(BOOTSTRAPS)
    for iteration in range(BOOTSTRAPS):
        good = rng.choice(pair_cosine[correct], correct.sum(), replace=True)
        bad = rng.choice(pair_cosine[incorrect], incorrect.sum(), replace=True)
        memory_bootstrap[iteration] = good.mean() - bad.mean()
    memory_ci = np.quantile(memory_bootstrap, (0.025, 0.975))
    reversed_recognition = recognition[correct, ::-1, :].reshape(correct.sum(), -1)
    order_difference = r1._cosine(correct_encoding, correct_recognition) - r1._cosine(
        correct_encoding, reversed_recognition
    )
    order_bootstrap = np.empty(BOOTSTRAPS)
    for iteration in range(BOOTSTRAPS):
        order_bootstrap[iteration] = rng.choice(order_difference, len(order_difference), replace=True).mean()
    order_advantage = float(order_difference.mean())
    order_ci = np.quantile(order_bootstrap, (0.025, 0.975))
    relational = bool(
        pair_advantage >= 0.05 and pair_p <= 0.01
        and geometry_rho >= 0.20 and geometry_p <= 0.01
        and confidence_rho >= 0.20 and confidence_p <= 0.01
        and correct_incorrect >= 0.05 and memory_ci[0] > 0
    )
    temporal = relational and order_advantage >= 0.03 and order_ci[0] > 0
    return {
        "decision": (
            "TEMPORAL_RELATIONAL_RETRIEVAL_R2_DEVELOPMENT_CANDIDATE" if temporal
            else "RELATIONAL_RETRIEVAL_R2_DEVELOPMENT_CANDIDATE" if relational
            else "HUMAN_RELATIONAL_RETRIEVAL_R2_NOT_ESTABLISHED"
        ),
        "eligible_units": int(keep.sum()),
        "old_pairs": len(old_recognition),
        "correct_old_pairs": int(correct.sum()),
        "incorrect_old_pairs": int(incorrect.sum()),
        "matched_cosine_advantage": pair_advantage,
        "matched_cosine_permutation_p": pair_p,
        "relational_geometry_spearman_rho": geometry_rho,
        "relational_geometry_permutation_p": geometry_p,
        "confidence_spearman_rho": confidence_rho,
        "confidence_permutation_p": confidence_p,
        "correct_minus_incorrect_cosine": correct_incorrect,
        "correct_minus_incorrect_95ci": memory_ci.tolist(),
        "correct_minus_reversed_time_order_cosine": order_advantage,
        "time_order_95ci": order_ci.tolist(),
    }


def analyze() -> dict[str, object]:
    sessions = {
        subject: analyze_session(subject, path, expected_hash)
        for subject, (path, expected_hash) in SESSIONS.items()
    }
    passed = all("DEVELOPMENT_CANDIDATE" in str(result["decision"]) for result in sessions.values())
    return {
        "decision": (
            "HUMAN_RELATIONAL_RETRIEVAL_R2_REPLICATED_DEVELOPMENT_CANDIDATE"
            if passed else "HUMAN_RELATIONAL_RETRIEVAL_R2_NOT_ESTABLISHED_REPLICATED"
        ),
        "sessions": sessions,
        "claim_ceiling": "new-subject development only; calibration and confirmation remain sealed",
    }
