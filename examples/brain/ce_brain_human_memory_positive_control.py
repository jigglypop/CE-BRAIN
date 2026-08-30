"""Preregistered known old/new memory-selective-cell sensitivity control."""
from __future__ import annotations

import hashlib
from pathlib import Path

import h5py
import numpy as np

from examples.brain import ce_brain_human_memory_apparatus as apparatus

PERMUTATIONS = 2000
SEED = 4004001
WINDOW_START = 0.2
WINDOW_STOP = 1.2

# First outcome-blind enrollment point with >=8 schema-eligible subjects and
# >=250 schema units. P19/P16 are excluded because their CE endpoint was open.
SESSIONS = {
    "P14HMH": ("sub-P14HMH_ses-20070601_obj-1t8wrd5_ecephys+image.nwb", "3483afd0275f396fd5097d317534e8cce7a2563a053e12b4f3ad21ee12b54eb9"),
    "P53CS": ("sub-P53CS_ses-20171101_obj-lj04dr_ecephys+image.nwb", "ca804703001f7ec1103e3738507c110e4a57c431a1f7559fc4b1d31d71f0e539"),
    "P25CS": ("sub-P25CS_ses-20120901_obj-uhyr63_ecephys+image.nwb", "7445795c9c61dbb99dae3c7c58801fd87a516ec4362990e24323fbe7de449a38"),
    "P49CS": ("sub-P49CS_ses-20170501_obj-1ft8efg_ecephys+image.nwb", "e312524bf9afedbb8f7f877f2996e83f9ff5fb4537134161f9594e4d024f4c67"),
    "P44HMH": ("sub-P44HMH_ses-20000101_ecephys+image.nwb", "f99cc029a2034c79e62c71436036f7b9ec68dcdee015b0071ddc26f86c3609ef"),
    "P57CS": ("sub-P57CS_ses-20180601_obj-12hkdgu_ecephys+image.nwb", "0bf92850b0fb8a4fb918580b07c488c469b615f047f3ecd936fc5606678bd713"),
    "P37CS": ("sub-P37CS_ses-20150301_ecephys+image.nwb", "f01661782351056101ce0f1a33f8e02f1aec7735e2dc89c46ccd7030dc1a3a1f"),
    "P33CS": ("sub-P33CS_ses-20140301_obj-1ps6q26_ecephys+image.nwb", "04cf2d720cf2c384ba2675ac2f9b4b25a49a2a520831e13a78ad2eacc39ade2e"),
    "P62CS": ("sub-P62CS_ses-20190401_ecephys+image.nwb", "866a9d8ac6bfa6295bf1474f99f7b7ba6a0df599fa9668ff700e982c4659b354"),
    "P44CS": ("sub-P44CS_ses-20160901_ecephys+image.nwb", "55eab2c5f5f0b747d239faf6805b547f306927d1dcfa6137eaef9f23de648ada"),
    "P24CS": ("sub-P24CS_ses-20120901_obj-enj8r0_ecephys+image.nwb", "c78ada20cef87217332d39533d35e413ae999a4a5dd2ddb65fdb1fa95345bb5e"),
    "TWH098": ("sub-TWH098_ses-20180901_ecephys+image.nwb", "1b3ec78259b1040cc4ac822c189ec45ddc320e14b6e7a8bb385d48c0060f9185"),
    "P9HMH": ("sub-P9HMH_ses-20060301_obj-1otd1m8_ecephys+image.nwb", "0c9409255f5802393af3f00fd6248f8956e1a64100c3e8ec14fd7108e0f6a0a0"),
}


def _category_permutations(categories: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    permutations = np.tile(np.arange(len(categories)), (PERMUTATIONS, 1))
    for category in np.unique(categories):
        indices = np.flatnonzero(categories == category)
        for row in range(PERMUTATIONS):
            permutations[row, indices] = rng.permutation(indices)
    return permutations


def _session(subject: str, path: Path, expected_hash: str) -> dict[str, object]:
    if apparatus.audit_file(path, expected_hash)["decision"] != "HUMAN_MEMORY_RELATIONAL_APPARATUS_ELIGIBLE":
        raise RuntimeError(f"HUMAN_MEMORY_POSITIVE_CONTROL_STOP: {subject} apparatus")
    with h5py.File(path, "r") as nwb:
        trials = nwb["intervals/trials"]
        phases = np.asarray([value.decode() for value in trials["stim_phase"][:]])
        categories = np.asarray([value.decode() for value in trials["category_name"][:]])
        onset = np.asarray(trials["stim_on_time"], dtype=float)
        start_time = np.asarray(trials["start_time"], dtype=float)
        stop_time = np.asarray(trials["stop_time"], dtype=float)
        images = nwb["stimulus/presentation/StimulusPresentation/data"]
        hashes = np.asarray([hashlib.sha256(images[index].tobytes()).hexdigest() for index in range(len(images))])
        spikes = np.asarray(nwb["units/spike_times"])
        spike_index = np.asarray(nwb["units/spike_times_index"], dtype=int)
    learning_hashes = set(hashes[phases == "learn"])
    recognition = np.flatnonzero(phases == "recog")
    old = np.asarray([hashes[index] in learning_hashes for index in recognition])
    recognition_categories = categories[recognition]
    starts = np.r_[0, spike_index[:-1]]
    duration = float(stop_time.max() - start_time.min())
    rates = np.zeros((len(recognition), len(spike_index)), dtype=float)
    for unit, (left, right) in enumerate(zip(starts, spike_index)):
        unit_spikes = spikes[left:right]
        edges_left = onset[recognition] + WINDOW_START
        edges_right = onset[recognition] + WINDOW_STOP
        rates[:, unit] = np.searchsorted(unit_spikes, edges_right) - np.searchsorted(unit_spikes, edges_left)
    firing_rate = (spike_index - starts) / duration
    keep = (firing_rate >= 0.05) & ((rates > 0).mean(axis=0) >= 0.05)
    rates = rates[:, keep]
    if not len(rates.T):
        raise RuntimeError(f"HUMAN_MEMORY_POSITIVE_CONTROL_STOP: {subject} units")
    observed = np.abs(rates[old].mean(axis=0) - rates[~old].mean(axis=0))
    rng = np.random.default_rng(SEED + int(hashlib.sha256(subject.encode()).hexdigest()[:8], 16))
    orders = _category_permutations(recognition_categories, rng)
    null = np.empty((PERMUTATIONS, rates.shape[1]), dtype=float)
    for row, order in enumerate(orders):
        shuffled = old[order]
        null[row] = np.abs(rates[shuffled].mean(axis=0) - rates[~shuffled].mean(axis=0))
    p_values = (1 + (null >= observed).sum(axis=0)) / (PERMUTATIONS + 1)
    thresholds = np.quantile(null, 0.95, axis=0)
    null_counts = (null > thresholds).sum(axis=1)
    selective = p_values < 0.05
    return {
        "subject": subject,
        "eligible_units": int(keep.sum()),
        "selective_units": int(selective.sum()),
        "p_values": p_values,
        "observed_statistics": observed,
        "null_counts": null_counts,
    }


def analyze() -> dict[str, object]:
    results = []
    for subject, (filename, expected_hash) in SESSIONS.items():
        results.append(_session(subject, apparatus.DATA / filename, expected_hash))
    eligible_units = sum(int(result["eligible_units"]) for result in results)
    selective_units = sum(int(result["selective_units"]) for result in results)
    subjects_with_selective = sum(int(result["selective_units"]) > 0 for result in results)
    null_counts = np.sum([result["null_counts"] for result in results], axis=0)
    null_95 = float(np.quantile(null_counts, 0.95))
    proportion = selective_units / eligible_units
    enrollment_pass = len(results) >= 8 and eligible_units >= 250
    passed = bool(
        enrollment_pass and proportion >= 0.07
        and selective_units > null_95 and subjects_with_selective >= 3
    )
    return {
        "decision": (
            "KNOWN_MEMORY_SIGNAL_DETECTED" if passed
            else "MEMORY_POSITIVE_CONTROL_ENROLLMENT_CONTINUES" if not enrollment_pass
            else "MEMORY_APPARATUS_SENSITIVITY_NOT_ESTABLISHED"
        ),
        "subjects": len(results),
        "eligible_units": eligible_units,
        "selective_units": selective_units,
        "selective_fraction": proportion,
        "subjects_with_selective_units": subjects_with_selective,
        "cohort_null_count_95pct": null_95,
        "session_results": {
            str(result["subject"]): {
                "eligible_units": int(result["eligible_units"]),
                "selective_units": int(result["selective_units"]),
            }
            for result in results
        },
        "paper_reference_fraction": 146 / 1863,
        "claim_ceiling": "known old/new sensitivity control only; not CE relational retrieval evidence",
    }


def official_method_diagnostic() -> dict[str, object]:
    """Outcome-known diagnostic matching the released MATLAB analysis.

    This is not allowed to replace the preregistered result. It diagnoses the
    consequences of the official 0.2--1.7 s, correct-trials-only, centered
    bootstrap method after the stricter control has already been scored.
    """
    session_results: dict[str, dict[str, int]] = {}
    total_units = 0
    selective_units = 0
    for subject, (filename, expected_hash) in SESSIONS.items():
        path = apparatus.DATA / filename
        if apparatus.audit_file(path, expected_hash)["decision"] != "HUMAN_MEMORY_RELATIONAL_APPARATUS_ELIGIBLE":
            raise RuntimeError(f"HUMAN_MEMORY_OFFICIAL_DIAGNOSTIC_STOP: {subject}")
        with h5py.File(path, "r") as nwb:
            trials = nwb["intervals/trials"]
            phases = np.asarray([value.decode() for value in trials["stim_phase"][:]])
            responses = np.asarray(trials["response_value"], dtype=float)
            onset = np.asarray(trials["stim_on_time"], dtype=float)
            images = nwb["stimulus/presentation/StimulusPresentation/data"]
            hashes = np.asarray([hashlib.sha256(images[index].tobytes()).hexdigest() for index in range(len(images))])
            spikes = np.asarray(nwb["units/spike_times"])
            spike_index = np.asarray(nwb["units/spike_times_index"], dtype=int)
        learning_hashes = set(hashes[phases == "learn"])
        recognition = np.flatnonzero(phases == "recog")
        old = np.asarray([hashes[index] in learning_hashes for index in recognition])
        correct = np.where(old, responses[recognition] >= 34, responses[recognition] <= 33)
        old_use = old & correct
        new_use = ~old & correct
        starts = np.r_[0, spike_index[:-1]]
        rng = np.random.default_rng(SEED + 17 + int(hashlib.sha256(subject.encode()).hexdigest()[:8], 16))
        session_selective = 0
        for left, right in zip(starts, spike_index):
            unit_spikes = spikes[left:right]
            counts = (
                np.searchsorted(unit_spikes, onset[recognition] + 1.7)
                - np.searchsorted(unit_spikes, onset[recognition] + 0.2)
            ) / 1.5
            old_counts = counts[old_use]
            new_counts = counts[new_use]
            observed = abs(float(old_counts.mean() - new_counts.mean()))
            pooled_mean = float(np.r_[old_counts, new_counts].mean())
            centered_old = old_counts - old_counts.mean() + pooled_mean
            centered_new = new_counts - new_counts.mean() + pooled_mean
            null = np.empty(1000)
            for iteration in range(1000):
                old_sample = rng.choice(centered_old, len(centered_old), replace=True)
                new_sample = rng.choice(centered_new, len(centered_new), replace=True)
                null[iteration] = abs(old_sample.mean() - new_sample.mean())
            p_value = float(np.mean(null >= observed))
            session_selective += p_value < 0.05
        units = len(spike_index)
        total_units += units
        selective_units += session_selective
        session_results[subject] = {"units": units, "selective_units": session_selective}
    return {
        "status": "OUTCOME_KNOWN_OFFICIAL_METHOD_DIAGNOSTIC",
        "subjects": len(SESSIONS),
        "units": total_units,
        "selective_units": selective_units,
        "selective_fraction": selective_units / total_units,
        "paper_reference_fraction": 146 / 1863,
        "session_results": session_results,
        "cannot_replace_preregistered_decision": True,
    }
