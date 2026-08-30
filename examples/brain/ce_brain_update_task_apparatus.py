"""Endpoint-blind apparatus gate for DANDI 001371 update-task sessions."""
from __future__ import annotations

import hashlib


SUBJECTS = ("S17", "S20", "S25", "S28", "S29", "S33", "S34")
SESSIONS = {
    "S34-220623": {"trials": 257, "non_update": 190, "switch": 51, "stay": 16, "CA1": 54, "PFC": 50},
    "S29-211123": {"trials": 104, "non_update": 77, "switch": 17, "stay": 10, "CA1": 41, "PFC": 16},
    "S20-210521": {"trials": 78, "non_update": 62, "switch": 12, "stay": 4, "CA1": 78, "PFC": 29},
    "S25-210916": {"trials": 161, "non_update": 112, "switch": 34, "stay": 15, "CA1": 56, "PFC": 30},
}


def subject_split() -> dict[str, list[str]]:
    ordered = sorted(SUBJECTS, key=lambda value: hashlib.sha256(value.encode()).hexdigest())
    return {
        "development": ordered[:4],
        "calibration": ordered[4:5],
        "confirmation": ordered[5:],
    }


def eligible_session(values: dict[str, int]) -> bool:
    return bool(
        values["switch"] >= 30
        and values["stay"] >= 10
        and values["CA1"] >= 20
        and values["PFC"] >= 20
    )


def audit() -> dict[str, object]:
    sessions = {
        name: {**values, "eligible": eligible_session(values)}
        for name, values in SESSIONS.items()
    }
    split = subject_split()
    eligible_development = [
        name for name, values in sessions.items()
        if name.split("-")[0] in split["development"] and values["eligible"]
    ]
    return {
        "decision": (
            "UPDATE_TASK_RAPID_CORRECTION_APPARATUS_ELIGIBLE"
            if len(eligible_development) >= 2
            else "UPDATE_TASK_APPARATUS_STOP"
        ),
        "dandiset": "001371@draft",
        "inventory_assets": 66,
        "inventory_subjects": 7,
        "inventory_bytes": 14_536_769_171_479,
        "split": split,
        "sessions": sessions,
        "eligible_development": eligible_development,
        "claim_ceiling": (
            "within-trial prospective-code correction; no persistent learning or READ/WRITE separation claim"
        ),
    }
