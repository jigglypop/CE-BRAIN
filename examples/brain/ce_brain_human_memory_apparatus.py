"""Neural-score-blind apparatus audit for DANDI 000004 human memory."""
from __future__ import annotations

import hashlib
from pathlib import Path

import h5py
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "external" / "ce_brain_human_memory_dandi000004"
FILE = DATA / "sub-P19HMH_ses-20080601_obj-1tmj21e_ecephys+image.nwb"
EXPECTED_SHA256 = "451697a72654a4d742c872a66edc56ab59f94cfdbfa1cbb37f93f0a70b39f998"
P16_FILE = DATA / "sub-P16HMH_ses-20071001_obj-1jfnx96_ecephys+image.nwb"
P16_SHA256 = "29ff7b0cede49b731de90b3741ff456d1cf4220944ccb88f364b5924d39bae2c"


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as source:
        while block := source.read(8 * 1024 * 1024):
            value.update(block)
    return value.hexdigest()


def audit_file(path: Path, expected_sha256: str) -> dict[str, object]:
    if digest(path) != expected_sha256:
        raise RuntimeError("HUMAN_MEMORY_APPARATUS_STOP: SHA-256")
    with h5py.File(path, "r") as nwb:
        trials = nwb["intervals/trials"]
        phases = np.asarray([item.decode() for item in trials["stim_phase"][:]])
        metadata_labels = np.asarray([item.decode() for item in trials["new_old_labels_recog"][:]])
        images = nwb["stimulus/presentation/StimulusPresentation/data"]
        image_hashes = np.asarray([hashlib.sha256(images[index].tobytes()).hexdigest() for index in range(len(images))])
        responses = np.asarray(trials["response_value"])
        units = len(nwb["units/id"])
        unit_spike_values_unread = len(nwb["units/spike_times"])
    learning = phases == "learn"
    recognition = phases == "recog"
    learned_hashes = set(image_hashes[learning])
    exact_old = recognition & np.asarray([value in learned_hashes for value in image_hashes])
    exact_new = recognition & ~exact_old
    label_zero = recognition & (metadata_labels == "0")
    label_one = recognition & (metadata_labels == "1")
    response_valid = np.isin(responses[recognition], np.arange(31, 37)).all()
    passed = bool(
        learning.sum() == 100 and recognition.sum() == 100
        and exact_old.sum() == 50 and exact_new.sum() == 50
        and np.unique(image_hashes[learning]).size == 100
        and np.unique(image_hashes[recognition]).size == 100
        and response_valid and units >= 10
    )
    return {
        "decision": "HUMAN_MEMORY_RELATIONAL_APPARATUS_ELIGIBLE" if passed else "HUMAN_MEMORY_APPARATUS_STOP",
        "file": path.name,
        "sha256": expected_sha256,
        "trials": len(phases),
        "learning_trials": int(learning.sum()),
        "recognition_trials": int(recognition.sum()),
        "exact_image_old_trials": int(exact_old.sum()),
        "exact_image_new_trials": int(exact_new.sum()),
        "metadata_label_zero_exact_old": int((label_zero & exact_old).sum()),
        "metadata_label_one_exact_old": int((label_one & exact_old).sum()),
        "recognition_response_codes_valid_31_to_36": bool(response_valid),
        "units_present": units,
        "unit_spike_values_unread_count": unit_spike_values_unread,
        "semantic_rule": "old/new is derived from exact embedded-image SHA-256 identity, not the contradictory metadata description",
        "claim_ceiling": "apparatus only; human development session, not Phase 14 confirmation",
    }


def audit() -> dict[str, object]:
    return audit_file(FILE, EXPECTED_SHA256)
