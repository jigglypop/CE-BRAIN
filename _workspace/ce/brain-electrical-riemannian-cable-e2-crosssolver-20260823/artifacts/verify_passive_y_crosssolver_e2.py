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
import scipy
from scipy.linalg import eigh


SCHEMA = "BA-ERC1-E2-v1"
D_STAR = 0.2
KAPPA_STAR = 0.3
THETA_FINAL = 0.2
EDGE_COUNT = 3
GRIDS = (16, 32, 64)
PANELS = ("S1", "A0", "M1")
ANTI_COEFF = np.array([1.0, -1.0, 0.0], dtype=float) / math.sqrt(2.0)

RUN_DIR = Path(__file__).resolve().parent.parent
ARTIFACT_DIR = Path(__file__).resolve().parent
PREDECESSOR_DIR = RUN_DIR.parent / "brain-electrical-riemannian-cable-20260823"

EXPECTED_INPUT_SHA256 = {
    "00-contract.md": "090873c753c3c69b2360435a2989de62092ccd63bc1f4a56cfcbfa3c24f6477d",
    "10-sources.md": "ca6b7e4fb3b42d2a5f0ef6703982aee3c47b49517bd3d43fafd6c9d9811bb506",
    "11-math.md": "974b1dbc0f4441985140c55d8f9ffc07fe21662b7e44a3f5bcbe54be0c6e5c95",
    "12-routes.md": "dc2f9ab90b3b06c9d910c61f45d54ddd5d5164b6740e5ef4d159d4140d63929e",
    "20-audit.md": "f076aa9e62449f958db9f94c1d628c9acc149dd6c03902423e1f1391c4b8e2d3",
}

EXPECTED_PREDECESSOR_SHA256 = {
    "00-contract.md": "97a0d6318ddd4ea4a11cd2aff01ab858c8381765b709212681bf5ef428c1cdd5",
    "10-sources.md": "6fb05ae378257ed666d34ca5c5cdd2611e7f6ce1fcf070dd988c9a231b9c0f35",
    "11-math.md": "a96c9cda861691ea0edabefcc1f7d34befae3e4ec4973d8ecdc8b9492ac15685",
    "12-routes.md": "6269d567bcb2c1328f8d6a7be945116499c1b6ed95d1383c4f30b7761400ce51",
    "20-audit.md": "72ba6d2074afdb91c3c7867c4bd9c6abcdf76d285e08e77d4f58ecf7826f7cef",
    "40-final-report.md": "7a0989e50cdbaf7b8b6d5be4abdd0fc3259460c8528b2961a19e000c5d82a619",
    "artifacts/verify_electrical_cable_l0.py": "708740755c0b183aa37aaa7883baa96dcd2a7347a5c76a72df0f46f49b7e9ce8",
    "artifacts/l0-receipt.json": "9e643eaf70302ff4369f15bf1fa044f11660a45c9148869395fb65a643006501",
}

THRESHOLDS = {
    "fine_exact_error_max": 1.0e-3,
    "fine_crosssolver_error_max": 1.0e-3,
    "refinement_ratio_min": 3.0,
    "fv_kcl_residual_max": 1.0e-12,
    "fem_weak_residual_max": 1.0e-11,
    "energy_relative_increase_max": 1.0e-10,
    "generalized_eigenvalue_min": -1.0e-10,
    "modal_decay_relative_error_max": 1.0e-3,
    "disconnected_control_error_min": 2.0e-2,
}


def sha256_path(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def exact_edge(panel: str, edge: int, s: np.ndarray, theta: float) -> np.ndarray:
    symmetric_rate = D_STAR * math.pi**2 + KAPPA_STAR
    antisymmetric_rate = D_STAR * (0.5 * math.pi) ** 2 + KAPPA_STAR
    symmetric = np.cos(math.pi * s) * math.exp(-symmetric_rate * theta)
    antisymmetric = (
        ANTI_COEFF[edge]
        * np.sin(0.5 * math.pi * s)
        * math.exp(-antisymmetric_rate * theta)
    )
    if panel == "S1":
        return symmetric
    if panel == "A0":
        return antisymmetric
    if panel == "M1":
        return 0.7 * symmetric + 0.3 * antisymmetric
    raise ValueError(f"unknown panel: {panel}")


def exact_cells(panel: str, n_cell: int, theta: float) -> np.ndarray:
    h = 1.0 / n_cell
    s = (np.arange(n_cell, dtype=float) + 0.5) * h
    return np.vstack([exact_edge(panel, edge, s, theta) for edge in range(EDGE_COUNT)])


def relative_l2(candidate: np.ndarray, reference: np.ndarray, h: float) -> float:
    numerator = h * float(np.sum((candidate - reference) ** 2))
    denominator = h * float(np.sum(reference**2))
    if denominator <= 0.0:
        raise ValueError("relative norm has zero reference energy")
    return math.sqrt(numerator / denominator)


def fv_laplacian(state: np.ndarray, h: float, coupled: bool) -> np.ndarray:
    lap = np.empty_like(state)
    h2 = h * h
    if coupled:
        vertex = float(np.mean(state[:, 0]))
        lap[:, 0] = (
            (state[:, 1] - state[:, 0]) / h
            - (state[:, 0] - vertex) / (0.5 * h)
        ) / h
    else:
        lap[:, 0] = (state[:, 1] - state[:, 0]) / h2
    lap[:, 1:-1] = (state[:, 2:] - 2.0 * state[:, 1:-1] + state[:, :-2]) / h2
    lap[:, -1] = (state[:, -2] - state[:, -1]) / h2
    return lap


def fv_rhs(state: np.ndarray, h: float, coupled: bool) -> np.ndarray:
    return D_STAR * fv_laplacian(state, h, coupled) - KAPPA_STAR * state


def fv_energy(state: np.ndarray, h: float) -> float:
    return 0.5 * h * float(np.sum(state**2))


def fv_kcl_residual(state: np.ndarray, h: float) -> float:
    vertex = float(np.mean(state[:, 0]))
    outward_gradients = 2.0 * (state[:, 0] - vertex) / h
    return abs(float(np.sum(outward_gradients))) / max(
        1.0, float(np.sum(np.abs(outward_gradients)))
    )


def solve_fv(panel: str, n_cell: int, coupled: bool = True) -> tuple[np.ndarray, dict[str, Any]]:
    h = 1.0 / n_cell
    state = exact_cells(panel, n_cell, 0.0)
    max_dt = 0.05 * h * h / D_STAR
    n_step = int(math.ceil(THETA_FINAL / max_dt))
    dt = THETA_FINAL / n_step
    initial_energy = fv_energy(state, h)
    previous_energy = initial_energy
    max_relative_energy_increase = 0.0
    max_kcl = fv_kcl_residual(state, h) if coupled else None

    for _ in range(n_step):
        k1 = fv_rhs(state, h, coupled)
        k2 = fv_rhs(state + 0.5 * dt * k1, h, coupled)
        k3 = fv_rhs(state + 0.5 * dt * k2, h, coupled)
        k4 = fv_rhs(state + dt * k3, h, coupled)
        next_state = state + (dt / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4)
        next_energy = fv_energy(next_state, h)
        relative_increase = (next_energy - previous_energy) / max(initial_energy, np.finfo(float).tiny)
        max_relative_energy_increase = max(max_relative_energy_increase, relative_increase)
        state = next_state
        previous_energy = next_energy
        if coupled:
            max_kcl = max(float(max_kcl), fv_kcl_residual(state, h))

    diagnostics = {
        "n_step": n_step,
        "dt": dt,
        "initial_energy": initial_energy,
        "final_energy": previous_energy,
        "max_relative_energy_increase": max_relative_energy_increase,
        "max_kcl_residual": max_kcl,
    }
    return state, diagnostics


def edge_nodes(edge: int, n_element: int) -> list[int]:
    return [0] + [1 + edge * n_element + j for j in range(n_element)]


def prepare_fem(n_element: int) -> dict[str, Any]:
    h = 1.0 / n_element
    n_dof = 1 + EDGE_COUNT * n_element
    mass = np.zeros((n_dof, n_dof), dtype=float)
    stiffness = np.zeros((n_dof, n_dof), dtype=float)
    local_mass = (h / 6.0) * np.array([[2.0, 1.0], [1.0, 2.0]])
    local_stiffness = (1.0 / h) * np.array([[1.0, -1.0], [-1.0, 1.0]])

    for edge in range(EDGE_COUNT):
        nodes = edge_nodes(edge, n_element)
        for j in range(n_element):
            pair = (nodes[j], nodes[j + 1])
            for a in range(2):
                for b in range(2):
                    mass[pair[a], pair[b]] += local_mass[a, b]
                    stiffness[pair[a], pair[b]] += local_stiffness[a, b]

    cholesky_ok = True
    try:
        np.linalg.cholesky(mass)
    except np.linalg.LinAlgError:
        cholesky_ok = False

    eigenvalues, eigenvectors = eigh(stiffness, mass, check_finite=True)
    return {
        "h": h,
        "mass": mass,
        "stiffness": stiffness,
        "eigenvalues": eigenvalues,
        "eigenvectors": eigenvectors,
        "cholesky_ok": cholesky_ok,
    }


def fem_initial_nodes(panel: str, n_element: int) -> np.ndarray:
    initial = np.empty(1 + EDGE_COUNT * n_element, dtype=float)
    initial[0] = float(exact_edge(panel, 0, np.array([0.0]), 0.0)[0])
    s = np.arange(1, n_element + 1, dtype=float) / n_element
    for edge in range(EDGE_COUNT):
        nodes = edge_nodes(edge, n_element)
        initial[nodes[1:]] = exact_edge(panel, edge, s, 0.0)
    return initial


def fem_cells(state: np.ndarray, n_element: int) -> np.ndarray:
    values = np.empty((EDGE_COUNT, n_element), dtype=float)
    for edge in range(EDGE_COUNT):
        nodes = edge_nodes(edge, n_element)
        values[edge, :] = 0.5 * (state[nodes[:-1]] + state[nodes[1:]])
    return values


def solve_fem(panel: str, n_element: int, system: dict[str, Any]) -> tuple[np.ndarray, dict[str, Any]]:
    mass = system["mass"]
    stiffness = system["stiffness"]
    eigenvalues = system["eigenvalues"]
    eigenvectors = system["eigenvectors"]
    initial = fem_initial_nodes(panel, n_element)
    coefficients = eigenvectors.T @ (mass @ initial)
    rates = D_STAR * eigenvalues + KAPPA_STAR

    def state_at(theta: float) -> np.ndarray:
        return eigenvectors @ (np.exp(-rates * theta) * coefficients)

    def derivative_at(theta: float) -> np.ndarray:
        return eigenvectors @ (-rates * np.exp(-rates * theta) * coefficients)

    sample_times = np.linspace(0.0, THETA_FINAL, 11)
    energies = []
    for theta in sample_times:
        sample = state_at(float(theta))
        energies.append(0.5 * float(sample @ (mass @ sample)))
    initial_energy = energies[0]
    max_relative_energy_increase = max(
        0.0,
        max(
            (energies[j + 1] - energies[j]) / max(initial_energy, np.finfo(float).tiny)
            for j in range(len(energies) - 1)
        ),
    )

    terminal = state_at(THETA_FINAL)
    terminal_derivative = derivative_at(THETA_FINAL)
    weak_vector = (
        mass @ terminal_derivative
        + D_STAR * (stiffness @ terminal)
        + KAPPA_STAR * (mass @ terminal)
    )
    weak_denominator = (
        np.linalg.norm(mass @ terminal_derivative)
        + np.linalg.norm(D_STAR * (stiffness @ terminal))
        + np.linalg.norm(KAPPA_STAR * (mass @ terminal))
        + np.finfo(float).eps
    )
    diagnostics = {
        "initial_energy": initial_energy,
        "final_energy": energies[-1],
        "max_relative_energy_increase": max_relative_energy_increase,
        "weak_residual": float(np.linalg.norm(weak_vector) / weak_denominator),
        "center_continuity_residual": 0.0,
    }
    return fem_cells(terminal, n_element), diagnostics


def modal_decay_error(state: np.ndarray, panel: str, n_cell: int) -> float:
    if panel not in ("S1", "A0"):
        raise ValueError("modal decay is defined only for pure panels")
    spatial_mode = exact_cells(panel, n_cell, 0.0)
    amplitude = float(np.sum(state * spatial_mode) / np.sum(spatial_mode**2))
    if panel == "S1":
        rate = D_STAR * math.pi**2 + KAPPA_STAR
    else:
        rate = D_STAR * (0.5 * math.pi) ** 2 + KAPPA_STAR
    expected = math.exp(-rate * THETA_FINAL)
    return abs(amplitude - expected) / expected


def all_finite(value: Any) -> bool:
    if isinstance(value, dict):
        return all(all_finite(item) for item in value.values())
    if isinstance(value, (list, tuple)):
        return all(all_finite(item) for item in value)
    if isinstance(value, (float, np.floating)):
        return math.isfinite(float(value))
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Sealed BA-ERC1 E2 Y-cable cross-solver verifier")
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    output = args.output.resolve()
    if output.parent != ARTIFACT_DIR.resolve():
        raise SystemExit("output must be inside this run's artifacts directory")
    if output.exists():
        raise SystemExit(f"refusing to overwrite existing receipt: {output}")

    actual_inputs = {name: sha256_path(RUN_DIR / name) for name in EXPECTED_INPUT_SHA256}
    source_match = actual_inputs == EXPECTED_INPUT_SHA256
    actual_predecessor = {
        name: sha256_path(PREDECESSOR_DIR / name) for name in EXPECTED_PREDECESSOR_SHA256
    }
    predecessor_match = actual_predecessor == EXPECTED_PREDECESSOR_SHA256
    preflight_archive_hash = sha256_path(ARTIFACT_DIR / "20-audit-preflight-pass.md")
    preflight_archive_match = preflight_archive_hash == EXPECTED_INPUT_SHA256["20-audit.md"]

    environment = {
        "python": platform.python_version(),
        "python_executable": sys.executable,
        "numpy": np.__version__,
        "scipy": scipy.__version__,
        "platform": platform.platform(),
        "bytecode_disabled": bool(sys.dont_write_bytecode),
    }
    environment_match = (
        environment["python"] == "3.11.9"
        and environment["numpy"] == "2.4.6"
        and environment["scipy"] == "1.17.1"
        and environment["bytecode_disabled"]
    )

    systems: dict[str, Any] = {}
    panel_results: dict[str, dict[str, Any]] = {panel: {} for panel in PANELS}
    raw_states: dict[tuple[str, int, str], np.ndarray] = {}

    for n_grid in GRIDS:
        fem_system = prepare_fem(n_grid)
        systems[str(n_grid)] = {
            "mass_cholesky_ok": bool(fem_system["cholesky_ok"]),
            "generalized_eigenvalue_min": float(np.min(fem_system["eigenvalues"])),
            "generalized_eigenvalue_max": float(np.max(fem_system["eigenvalues"])),
        }
        for panel in PANELS:
            exact = exact_cells(panel, n_grid, THETA_FINAL)
            fv_state, fv_diag = solve_fv(panel, n_grid, coupled=True)
            fem_state, fem_diag = solve_fem(panel, n_grid, fem_system)
            raw_states[(panel, n_grid, "fv")] = fv_state
            raw_states[(panel, n_grid, "fem")] = fem_state
            panel_results[panel][str(n_grid)] = {
                "fv_exact_error": relative_l2(fv_state, exact, 1.0 / n_grid),
                "fem_exact_error": relative_l2(fem_state, exact, 1.0 / n_grid),
                "crosssolver_error": relative_l2(fv_state, fem_state, 1.0 / n_grid),
                "fv": fv_diag,
                "fem": fem_diag,
            }

    refinement: dict[str, dict[str, float]] = {}
    for panel in PANELS:
        refinement[panel] = {
            "fv_32_to_64": (
                panel_results[panel]["32"]["fv_exact_error"]
                / panel_results[panel]["64"]["fv_exact_error"]
            ),
            "fem_32_to_64": (
                panel_results[panel]["32"]["fem_exact_error"]
                / panel_results[panel]["64"]["fem_exact_error"]
            ),
        }

    modal_decay = {
        panel: {
            solver: modal_decay_error(raw_states[(panel, 64, solver)], panel, 64)
            for solver in ("fv", "fem")
        }
        for panel in ("S1", "A0")
    }

    disconnected_state, disconnected_diag = solve_fv("A0", 64, coupled=False)
    disconnected_error = relative_l2(
        disconnected_state, exact_cells("A0", 64, THETA_FINAL), 1.0 / 64
    )
    adverse_control = {
        "panel": "A0",
        "grid": 64,
        "center_condition": "three independent sealed Neumann faces",
        "exact_star_error": disconnected_error,
        "fv": disconnected_diag,
    }

    checks: dict[str, bool] = {
        "source_seal": source_match,
        "predecessor_seal": predecessor_match,
        "preflight_archive_seal": preflight_archive_match,
        "environment_seal": environment_match,
    }
    checks["fine_exact_errors"] = all(
        panel_results[panel]["64"][key] <= THRESHOLDS["fine_exact_error_max"]
        for panel in PANELS
        for key in ("fv_exact_error", "fem_exact_error")
    )
    checks["fine_crosssolver_errors"] = all(
        panel_results[panel]["64"]["crosssolver_error"]
        <= THRESHOLDS["fine_crosssolver_error_max"]
        for panel in PANELS
    )
    checks["refinement"] = all(
        ratio >= THRESHOLDS["refinement_ratio_min"]
        for values in refinement.values()
        for ratio in values.values()
    )
    checks["fv_strong_kirchhoff"] = all(
        panel_results[panel][str(n_grid)]["fv"]["max_kcl_residual"]
        <= THRESHOLDS["fv_kcl_residual_max"]
        for panel in PANELS
        for n_grid in GRIDS
    )
    checks["fem_continuity_and_weak_residual"] = all(
        panel_results[panel][str(n_grid)]["fem"]["center_continuity_residual"] == 0.0
        and panel_results[panel][str(n_grid)]["fem"]["weak_residual"]
        <= THRESHOLDS["fem_weak_residual_max"]
        for panel in PANELS
        for n_grid in GRIDS
    )
    checks["passive_energy"] = all(
        panel_results[panel][str(n_grid)][solver]["max_relative_energy_increase"]
        <= THRESHOLDS["energy_relative_increase_max"]
        for panel in PANELS
        for n_grid in GRIDS
        for solver in ("fv", "fem")
    )
    checks["mass_spd"] = all(item["mass_cholesky_ok"] for item in systems.values())
    checks["generalized_spectrum"] = all(
        item["generalized_eigenvalue_min"] >= THRESHOLDS["generalized_eigenvalue_min"]
        for item in systems.values()
    )
    checks["pure_modal_decay"] = all(
        value <= THRESHOLDS["modal_decay_relative_error_max"]
        for panel in modal_decay.values()
        for value in panel.values()
    )
    checks["disconnected_control_detected"] = (
        disconnected_error >= THRESHOLDS["disconnected_control_error_min"]
    )

    numerical_payload = {
        "systems": systems,
        "panels": panel_results,
        "refinement": refinement,
        "modal_decay": modal_decay,
        "adverse_control": adverse_control,
    }
    checks["all_outputs_finite"] = all_finite(numerical_payload)

    apparatus_checks = (
        "source_seal",
        "predecessor_seal",
        "preflight_archive_seal",
        "environment_seal",
        "disconnected_control_detected",
        "all_outputs_finite",
    )
    if not all(checks[name] for name in apparatus_checks):
        status = "APPARATUS_INVALID"
        claim_status = "NO_PROMOTION"
    elif all(checks.values()):
        status = "PASS"
        claim_status = "E2_CROSSSOLVER_MANUFACTURED_ONLY"
    else:
        status = "STOP"
        claim_status = "NO_PROMOTION"

    receipt = {
        "schema": SCHEMA,
        "status": status,
        "claim_status": claim_status,
        "failed_checks": [name for name, passed in checks.items() if not passed],
        "checks": checks,
        "thresholds": THRESHOLDS,
        "problem": {
            "edge_count": EDGE_COUNT,
            "edge_length_dimensionless": 1.0,
            "D_star": D_STAR,
            "kappa_star": KAPPA_STAR,
            "theta_final": THETA_FINAL,
            "grids": list(GRIDS),
            "panels": list(PANELS),
        },
        "results": numerical_payload,
        "expected_input_sha256": EXPECTED_INPUT_SHA256,
        "actual_input_sha256": actual_inputs,
        "source_match": source_match,
        "expected_predecessor_sha256": EXPECTED_PREDECESSOR_SHA256,
        "actual_predecessor_sha256": actual_predecessor,
        "predecessor_match": predecessor_match,
        "preflight_archive_sha256": preflight_archive_hash,
        "script_sha256": sha256_path(Path(__file__).resolve()),
        "environment": environment,
        "apparatus_revision": {
            "numerical_attempt": 0,
            "prebuild_math_revision": 1,
            "scope": "malformed cosine token only; before verifier creation and numerical execution",
            "preserved_stop_math_sha256": "36e133bf59a428c9658ad82ae3adc59c8cce708c30781a143447f2c161909713",
            "preserved_stop_audit_sha256": "91e6dc6797780a5b6f6545152c489111b514b613d449d0b42b7df6ac6a06419d",
        },
        "biological_claim": False,
        "consciousness_claim": False,
        "model_fit": False,
        "real_endpoint_opened": False,
        "behavior_loaded": False,
        "downstream_authorized": False,
    }

    output.write_text(
        json.dumps(receipt, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "status": status,
                "claim_status": claim_status,
                "failed_checks": receipt["failed_checks"],
                "receipt": str(output),
            },
            sort_keys=True,
        )
    )
    return 0 if status == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
