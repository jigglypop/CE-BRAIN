"""Read-only validation of the sealed BA-SRM9 F2-C receipt chain."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent

EXPECTED = {
    "f2a": "24c1099c63b0e7e59f107788e57bc122c62a267936a0313b03c12d88e2be6aab",
    "f2b": "ad402c8a872af3461d9600cad4b792eb1440761f5f8222c5b653511cf35f72b2",
    "f2c": "a43e14da1e099f30d3cb970f35db199159be83916b9ce33e685f494641958bf2",
    "runner": "361fa1b7b8d6af1576d5a02d76159f5f9e2a6215ecedf5b95bc66cee1e209b80",
    "authorization": "727606ea4a8d7dbc74374bbc6ed7b1b2614a75cf6c106cfb977310d2a02c48fb",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(name: str) -> dict:
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def compact_sha(value: object) -> str:
    payload = json.dumps(
        value, ensure_ascii=True, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def main() -> None:
    f2a = load("f2a-receipt.json")
    f2b = load("f2b-receipt.json")
    f2c = load("f2c-receipt.json")

    assert sha256(ROOT / "f2a-receipt.json") == EXPECTED["f2a"]
    assert sha256(ROOT / "f2b-receipt.json") == EXPECTED["f2b"]
    assert sha256(ROOT / "f2c-receipt.json") == EXPECTED["f2c"]
    assert sha256(ROOT / "run_f2c.py") == EXPECTED["runner"]

    assert (f2a["schema"], f2a["stage"]) == ("BA-SRM9-F2A-v1", "F2-A")
    assert (f2b["schema"], f2b["stage"]) == ("BA-SRM9-F2B-v1", "F2-B")
    assert (f2c["schema"], f2c["stage"]) == ("BA-SRM9-F2C-v1", "F2-C")
    assert f2c["authorization_audit_sha256"] == EXPECTED["authorization"]
    assert f2c["runner_sha256"] == EXPECTED["runner"]
    assert f2c["input_hashes"]["f2a_receipt"] == EXPECTED["f2a"]
    assert f2c["input_hashes"]["f2b_receipt"] == EXPECTED["f2b"]

    assert f2b["promoted_ids"] == f2c["input_promoted_ids"]
    assert len(f2c["input_promoted_ids"]) == 20
    assert compact_sha(f2c["input_promoted_ids"]) == f2c["input_promoted_ids_sha256"]

    candidates = f2c["candidates"]
    assert len(candidates) == len({row["id"] for row in candidates}) == 20
    assert f2c["preflight"]["status"] == "PASS"
    assert f2c["preflight"]["entries"] == 16
    assert f2c["counts"] == {
        "PROMOTE": 0,
        "DROPPED_BUDGET": 0,
        "FUTILITY_KILL": 20,
        "ABSTAIN": 0,
        "INVALID_KILL": 0,
    }
    assert f2c["promoted_ids"] == []
    assert compact_sha([]) == f2c["promoted_ids_sha256"]

    for row in candidates:
        medians = row["metrics"]["scenario_medians"]
        passed = all(
            value["median_rho"] >= 0.80 and value["median_nmae"] <= 0.20
            for value in medians.values()
        )
        assert row["status"] == ("PASS" if passed else "FUTILITY_KILL")
        assert not passed

    for flag in (
        "behavior_loaded",
        "model_fit",
        "real_endpoint_opened",
        "biological_claim",
        "downstream_authorized",
    ):
        assert f2c[flag] is False

    art_rho = [
        row["metrics"]["scenario_medians"]["ART10"]["median_rho"]
        for row in candidates
    ]
    block_rho = [
        row["metrics"]["scenario_medians"]["BLOCK30"]["median_rho"]
        for row in candidates
    ]
    assert max(art_rho) < 0.80
    assert min(block_rho) >= 0.80

    print(
        json.dumps(
            {
                "status": "PASS",
                "candidates": 20,
                "futility_kill": 20,
                "promote": 0,
                "art10_median_rho_range": [min(art_rho), max(art_rho)],
                "block30_median_rho_range": [min(block_rho), max(block_rho)],
                "receipt_sha256": EXPECTED["f2c"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
