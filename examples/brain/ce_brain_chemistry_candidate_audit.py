"""Frozen endpoint-blind audit of candidate neuromodulator write-gate datasets."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Candidate:
    dandiset: str
    assets: int
    ephys_assets: int
    chemical_assets: int
    joint_assets: int
    overlapping_subjects: int
    persistent_update_endpoint: bool
    availability: str = "usable"


CANDIDATES = (
    Candidate("001176@0.260610.2204", 132, 0, 132, 0, 0, False),
    # Remote .zmetadata inspection: five unit-bearing and three FIP-bearing
    # assets were observed, with no asset containing both. One draft asset
    # exposed neither signature at the audit date.
    Candidate("001950@draft", 9, 5, 3, 0, 0, False),
    Candidate("001955@0.260828.0749", 66, 34, 32, 0, 0, False),
    Candidate("001084@0.241023.2011", 180, 0, 180, 0, 0, False),
    Candidate("000298@draft", 1, 1, 0, 0, 0, False, "invalid_draft_buggy"),
    Candidate("001434@draft", 0, 0, 0, 0, 0, False, "invalid_draft_empty"),
)


def assess(candidate: Candidate) -> dict[str, object]:
    same_subject_modalities = candidate.overlapping_subjects > 0
    direct_gate = bool(
        candidate.availability == "usable"
        and candidate.joint_assets > 0
        and same_subject_modalities
        and candidate.persistent_update_endpoint
    )
    return {
        "dandiset": candidate.dandiset,
        "assets": candidate.assets,
        "ephys_assets": candidate.ephys_assets,
        "chemical_assets": candidate.chemical_assets,
        "joint_assets": candidate.joint_assets,
        "overlapping_subjects": candidate.overlapping_subjects,
        "persistent_update_endpoint": candidate.persistent_update_endpoint,
        "availability": candidate.availability,
        "direct_write_gate_identifiable": direct_gate,
    }


def audit() -> dict[str, object]:
    results = [assess(candidate) for candidate in CANDIDATES]
    eligible = [result["dandiset"] for result in results if result["direct_write_gate_identifiable"]]
    return {
        "decision": (
            "CHEMICAL_WRITE_GATE_CANDIDATE_FOUND"
            if eligible
            else "CHEMICAL_WRITE_GATE_NOT_IDENTIFIABLE_IN_AUDITED_CANDIDATES"
        ),
        "audit_date": "2026-08-31",
        "required_joint_axes": [
            "electrical population trajectory",
            "neuromodulator measurement or intervention",
            "matched condition",
            "subsequent persistent update endpoint",
        ],
        "candidates": results,
        "eligible": eligible,
        "claim_ceiling": "dataset-availability result; not a negative biological result",
    }
