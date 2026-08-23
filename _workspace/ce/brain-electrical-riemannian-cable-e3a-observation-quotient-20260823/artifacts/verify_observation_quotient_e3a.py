from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import sys
from pathlib import Path
from typing import Any

import numpy as np


RUN_DIR = Path(__file__).resolve().parent.parent
ARTIFACT_DIR = Path(__file__).resolve().parent
PREDECESSOR_DIR = RUN_DIR.parent / "brain-electrical-riemannian-cable-e2-crosssolver-20260823"

EXPECTED_INPUT_SHA256 = {
    "00-contract.md": "daf732762f6418191cbe15671e68baa027578b7b5c59107f4bec7eaeb1478df2",
    "10-sources.md": "5ddfe50b64f3378069f0821f5a0eccc604a81054a92a865a6585ac7fc3af3579",
    "11-math.md": "85065c545a582e362efab549b5ae52e4241785238ac5b85cd4b882ebd8e55e15",
    "12-routes.md": "35a6d2018164409006edeb46164c1a6b150472710d576a69a3f8ada0fcc366f1",
    "20-audit.md": "d6112b508ce8c82c9a3f34d100896ca9c201a947eed84bae6c9618b55ab71391",
}

EXPECTED_PREDECESSOR_SHA256 = {
    "00-contract.md": "090873c753c3c69b2360435a2989de62092ccd63bc1f4a56cfcbfa3c24f6477d",
    "10-sources.md": "ca6b7e4fb3b42d2a5f0ef6703982aee3c47b49517bd3d43fafd6c9d9811bb506",
    "11-math.md": "974b1dbc0f4441985140c55d8f9ffc07fe21662b7e44a3f5bcbe54be0c6e5c95",
    "12-routes.md": "dc2f9ab90b3b06c9d910c61f45d54ddd5d5164b6740e5ef4d159d4140d63929e",
    "20-audit.md": "2e64fe533dba988363346f2425d22d1601b3897ccb39676170c5a501d0e8f0d3",
    "31-validation.md": "e49e321350e43e37313f89eb2c26843991798e881f55bcb9d63a4b2953f73a32",
    "40-final-report.md": "836d429b5ce899d4b4149b81a05e8ba1108f9abaa2b9cf0630117a5dfad1b6cb",
    "artifacts/verify_passive_y_crosssolver_e2.py": "a32c833acf740ca9c28764d50230807e391adf247f6790ca593ec183bcbdbb46",
    "artifacts/e2-receipt.json": "badb1ec5246976b723a257aec4ffb16be1d1e015bb6ebe38afe509b34024ded6",
}

THRESHOLDS = {
    "projector_algebra_max": 1.0e-14,
    "symmetric_eta_max": 1.0e-24,
    "antisymmetric_eta_min": 1.0 - 1.0e-12,
    "mixed_eta_min": 0.2,
    "collapsed_antisymmetric_max": 1.0e-15,
}


def sha256_path(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def eta_perp(projector: np.ndarray, data: np.ndarray) -> float:
    residual = (np.eye(3) - projector) @ data
    denominator = float(np.sum(data**2))
    if denominator <= 0.0:
        raise ValueError("zero observation energy")
    return float(np.sum(residual**2) / denominator)


def all_finite(value: Any) -> bool:
    if isinstance(value, dict):
        return all(all_finite(item) for item in value.values())
    if isinstance(value, (list, tuple)):
        return all(all_finite(item) for item in value)
    if isinstance(value, (float, np.floating)):
        return math.isfinite(float(value))
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Sealed BA-ERC1 E3a observation quotient verifier")
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    output = args.output.resolve()
    if output.parent != ARTIFACT_DIR.resolve():
        raise SystemExit("output must be inside this run's artifacts directory")
    if output.exists():
        raise SystemExit(f"refusing to overwrite existing receipt: {output}")

    actual_inputs = {name: sha256_path(RUN_DIR / name) for name in EXPECTED_INPUT_SHA256}
    actual_predecessor = {
        name: sha256_path(PREDECESSOR_DIR / name) for name in EXPECTED_PREDECESSOR_SHA256
    }
    source_match = actual_inputs == EXPECTED_INPUT_SHA256
    predecessor_match = actual_predecessor == EXPECTED_PREDECESSOR_SHA256
    preflight_archive_hash = sha256_path(ARTIFACT_DIR / "20-audit-preflight.md")
    preflight_archive_match = preflight_archive_hash == EXPECTED_INPUT_SHA256["20-audit.md"]

    environment = {
        "python": platform.python_version(),
        "python_executable": sys.executable,
        "numpy": np.__version__,
        "platform": platform.platform(),
        "bytecode_disabled": bool(sys.dont_write_bytecode),
    }
    environment_match = (
        environment["python"] == "3.11.9"
        and environment["numpy"] == "2.4.6"
        and environment["bytecode_disabled"]
    )

    ones = np.ones(3, dtype=float)
    anti = np.array([1.0, -1.0, 0.0], dtype=float) / math.sqrt(2.0)
    projector = np.outer(ones, ones) / 3.0
    times = np.linspace(0.0, 0.2, 41)
    s0 = 0.6
    rate_s = 0.2 * math.pi**2 + 0.3
    rate_a = 0.2 * (0.5 * math.pi) ** 2 + 0.3
    symmetric_amplitude = math.cos(math.pi * s0) * np.exp(-rate_s * times)
    antisymmetric_amplitude = math.sin(0.5 * math.pi * s0) * np.exp(-rate_a * times)

    panels = {
        "S1": np.outer(ones, symmetric_amplitude),
        "A0": np.outer(anti, antisymmetric_amplitude),
        "M1": (
            0.7 * np.outer(ones, symmetric_amplitude)
            + 0.3 * np.outer(anti, antisymmetric_amplitude)
        ),
    }

    algebra = {
        "symmetry_error": float(np.linalg.norm(projector.T - projector, ord="fro")),
        "idempotence_error": float(np.linalg.norm(projector @ projector - projector, ord="fro")),
        "shared_subspace_error": float(np.linalg.norm(projector @ ones - ones)),
        "antisymmetric_kernel_error": float(np.linalg.norm(projector @ anti)),
        "rank": int(np.linalg.matrix_rank(projector)),
    }

    scores: dict[str, dict[str, float]] = {}
    for panel, data in panels.items():
        eta = eta_perp(projector, data)
        scores[panel] = {
            "eta_perp": eta,
            "point_oracle_relative_error": math.sqrt(max(0.0, eta)),
            "observation_energy": float(np.sum(data**2)),
            "branch_mean_max_abs": float(np.max(np.abs(np.mean(data, axis=0)))),
        }
    collapsed_a0_max = float(np.max(np.abs(np.mean(panels["A0"], axis=0))))

    payload = {
        "s0": s0,
        "time_count": len(times),
        "time_start": float(times[0]),
        "time_end": float(times[-1]),
        "projector": projector.tolist(),
        "algebra": algebra,
        "scores": scores,
        "collapsed_A0_max_abs": collapsed_a0_max,
    }

    checks = {
        "source_seal": source_match,
        "predecessor_seal": predecessor_match,
        "preflight_archive_seal": preflight_archive_match,
        "environment_seal": environment_match,
        "projector_algebra": (
            algebra["rank"] == 1
            and algebra["symmetry_error"] <= THRESHOLDS["projector_algebra_max"]
            and algebra["idempotence_error"] <= THRESHOLDS["projector_algebra_max"]
            and algebra["shared_subspace_error"] <= THRESHOLDS["projector_algebra_max"]
            and algebra["antisymmetric_kernel_error"] <= THRESHOLDS["projector_algebra_max"]
        ),
        "S1_symmetric_control": scores["S1"]["eta_perp"] <= THRESHOLDS["symmetric_eta_max"],
        "A0_resolved_confirmation": (
            scores["A0"]["eta_perp"] >= THRESHOLDS["antisymmetric_eta_min"]
        ),
        "M1_mixed_confirmation": scores["M1"]["eta_perp"] >= THRESHOLDS["mixed_eta_min"],
        "A0_collapsed_no_go": collapsed_a0_max <= THRESHOLDS["collapsed_antisymmetric_max"],
        "all_outputs_finite": all_finite(payload),
    }

    apparatus_names = (
        "source_seal",
        "predecessor_seal",
        "preflight_archive_seal",
        "environment_seal",
        "projector_algebra",
        "A0_collapsed_no_go",
        "all_outputs_finite",
    )
    if not all(checks[name] for name in apparatus_names):
        status = "APPARATUS_INVALID"
        claim_status = "NO_PROMOTION"
    elif all(checks.values()):
        status = "PASS"
        claim_status = "E3A_OBSERVATION_QUOTIENT_SYNTHETIC_ONLY"
    else:
        status = "STOP"
        claim_status = "NO_PROMOTION"

    receipt = {
        "schema": "BA-ERC1-E3a-v1",
        "status": status,
        "claim_status": claim_status,
        "failed_checks": [name for name, passed in checks.items() if not passed],
        "checks": checks,
        "thresholds": THRESHOLDS,
        "results": payload,
        "expected_input_sha256": EXPECTED_INPUT_SHA256,
        "actual_input_sha256": actual_inputs,
        "source_match": source_match,
        "expected_predecessor_sha256": EXPECTED_PREDECESSOR_SHA256,
        "actual_predecessor_sha256": actual_predecessor,
        "predecessor_match": predecessor_match,
        "preflight_archive_sha256": preflight_archive_hash,
        "script_sha256": sha256_path(Path(__file__).resolve()),
        "environment": environment,
        "apparatus_revision": {"attempt": 0, "scope": "none"},
        "real_endpoint_opened": False,
        "behavior_loaded": False,
        "model_fit": False,
        "biological_claim": False,
        "consciousness_claim": False,
        "downstream_authorized": False,
    }
    output.write_text(
        json.dumps(receipt, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"status": status, "claim_status": claim_status, "failed_checks": receipt["failed_checks"], "scores": scores, "receipt": str(output)}, sort_keys=True))
    return 0 if status == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
