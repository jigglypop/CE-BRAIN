from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import sys
from pathlib import Path
from typing import Iterable

import numpy as np


SCHEMA = "BA-ERC1-L0-v1"
EXPECTED_INPUT_HASHES = {
    "00-contract.md": "97a0d6318ddd4ea4a11cd2aff01ab858c8381765b709212681bf5ef428c1cdd5",
    "10-sources.md": "6fb05ae378257ed666d34ca5c5cdd2611e7f6ce1fcf070dd988c9a231b9c0f35",
    "11-math.md": "a96c9cda861691ea0edabefcc1f7d34befae3e4ec4973d8ecdc8b9492ac15685",
    "12-routes.md": "6269d567bcb2c1328f8d6a7be945116499c1b6ed95d1383c4f30b7761400ce51",
    "20-audit.md": "f7333a259659a4fd758c1fdb7f008c282a777c8f31162f6f447f5eae2e76083a",
}
THRESHOLDS = {
    "kirchhoff_relative_imbalance_max": 1.0e-12,
    "energy_relative_increase_max": 1.0e-12,
    "fine_relative_l2_error_max": 2.0e-3,
    "refinement_ratio_min": 3.0,
    "nonlinearity_residual_min": 1.0e-4,
    "kernel_normalization_error_max": 1.0e-12,
    "kernel_endpoint_flatness_proxy_max": float(1024 * np.finfo(np.float64).eps),
}

Dim = tuple[int, int, int, int]  # kg, m, s, A
ZERO: Dim = (0, 0, 0, 0)


def dadd(*terms: Dim) -> Dim:
    return tuple(sum(term[k] for term in terms) for k in range(4))  # type: ignore[return-value]


def dsub(left: Dim, right: Dim) -> Dim:
    return tuple(left[k] - right[k] for k in range(4))  # type: ignore[return-value]


def dscale(value: Dim, power: int) -> Dim:
    return tuple(power * item for item in value)  # type: ignore[return-value]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def finite(values: Iterable[float]) -> bool:
    return all(math.isfinite(float(value)) for value in values)


def unit_check() -> dict[str, object]:
    mass: Dim = (1, 0, 0, 0)
    length: Dim = (0, 1, 0, 0)
    time: Dim = (0, 0, 1, 0)
    ampere: Dim = (0, 0, 0, 1)
    volt: Dim = (1, 2, -3, -1)
    siemens = dsub(ampere, volt)
    farad = dsub(dadd(ampere, time), volt)
    area = dscale(length, 2)
    conductivity = dsub(siemens, length)
    capacitance_density = dsub(farad, dscale(length, 2))
    conductance_density = dsub(siemens, dscale(length, 2))
    current_density = dsub(ampere, dscale(length, 2))
    joule = dadd(mass, dscale(length, 2), dscale(time, -2))

    lhs = dadd(capacitance_density, volt, dscale(time, -1))
    axial = dsub(
        dsub(dadd(conductivity, area, dsub(volt, length)), length), length
    )
    ionic = dadd(conductance_density, volt)
    capacitive_metric = dadd(length, capacitance_density, dscale(volt, 2), length)
    axial_metric = dadd(
        time, conductivity, area, dscale(dsub(volt, length), 2), length
    )
    soma_metric = dadd(farad, dscale(volt, 2))
    gate_metric = dadd(dsub(joule, length), length)
    diffusion_number = dsub(
        dadd(time, conductivity, area),
        dadd(capacitance_density, length, dscale(length, 2)),
    )
    current_scale = dadd(capacitance_density, volt, dscale(time, -1))

    signatures = {
        "c_m_dV_dt": lhs,
        "weighted_axial_divergence": axial,
        "conductance_times_voltage": ionic,
        "expected_current_density": current_density,
        "capacitive_metric_energy": capacitive_metric,
        "axial_metric_energy": axial_metric,
        "soma_metric_energy": soma_metric,
        "gate_metric_energy": gate_metric,
        "D0": diffusion_number,
        "i0": current_scale,
    }
    passed = (
        lhs == current_density
        and axial == current_density
        and ionic == current_density
        and capacitive_metric == joule
        and axial_metric == joule
        and soma_metric == joule
        and gate_metric == joule
        and diffusion_number == ZERO
        and current_scale == current_density
        and volt != ampere
    )
    return {
        "status": "PASS" if passed else "FAIL",
        "dimension_order": ["kg", "m", "s", "A"],
        "signatures": {key: list(value) for key, value in signatures.items()},
        "clamp_swap_detected": volt != ampere,
        "all_exponential_arguments_declared_dimensionless": True,
    }


def kirchhoff_and_ohm_check() -> dict[str, object]:
    # Every edge coordinate points outwards from the central Y vertex.
    conductances = np.asarray([1.0, 2.0, 4.0], dtype=np.float64)
    terminal_voltages = np.asarray([6.0, -1.0, -1.0], dtype=np.float64)
    vertex_voltage = float(np.dot(conductances, terminal_voltages) / conductances.sum())
    gradient_flux = conductances * (terminal_voltages - vertex_voltage)
    physical_outward_currents = -gradient_flux
    scale = float(np.abs(gradient_flux).sum())
    relative_imbalance = abs(float(gradient_flux.sum())) / scale

    voltage_gradient = -3.0
    sigma_area = 2.0
    axial_current = -sigma_area * voltage_gradient
    ohmic_sign_pass = axial_current > 0.0 and axial_current * voltage_gradient < 0.0
    passed = (
        relative_imbalance <= THRESHOLDS["kirchhoff_relative_imbalance_max"]
        and abs(float(physical_outward_currents.sum())) / scale
        <= THRESHOLDS["kirchhoff_relative_imbalance_max"]
        and ohmic_sign_pass
    )
    return {
        "status": "PASS" if passed else "FAIL",
        "orientation": "all edge coordinates point outward from the central vertex",
        "vertex_voltage": vertex_voltage,
        "gradient_fluxes": gradient_flux.tolist(),
        "physical_outward_currents": physical_outward_currents.tolist(),
        "relative_imbalance": relative_imbalance,
        "ohm_test_voltage_gradient": voltage_gradient,
        "ohm_test_axial_current": axial_current,
        "ohmic_sign_pass": ohmic_sign_pass,
    }


def passive_run(n_cells: int) -> dict[str, float | int]:
    diffusivity = 0.2
    leak_rate = 0.3
    final_time = 0.2
    dx = 1.0 / n_cells
    x = (np.arange(n_cells, dtype=np.float64) + 0.5) * dx
    voltage = np.cos(np.pi * x)
    max_dt = 0.2 * dx * dx / diffusivity
    n_steps = int(math.ceil(final_time / max_dt))
    dt = final_time / n_steps
    previous_energy = 0.5 * dx * float(np.dot(voltage, voltage))
    max_relative_increase = -math.inf

    for _ in range(n_steps):
        laplacian = np.empty_like(voltage)
        laplacian[1:-1] = (
            voltage[:-2] - 2.0 * voltage[1:-1] + voltage[2:]
        ) / (dx * dx)
        laplacian[0] = (voltage[1] - voltage[0]) / (dx * dx)
        laplacian[-1] = (voltage[-2] - voltage[-1]) / (dx * dx)
        voltage_next = voltage + dt * (diffusivity * laplacian - leak_rate * voltage)
        energy = 0.5 * dx * float(np.dot(voltage_next, voltage_next))
        relative_increase = (energy - previous_energy) / max(previous_energy, 1.0e-300)
        max_relative_increase = max(max_relative_increase, relative_increase)
        voltage = voltage_next
        previous_energy = energy

    exact = np.exp(-(diffusivity * np.pi**2 + leak_rate) * final_time) * np.cos(
        np.pi * x
    )
    relative_l2_error = float(np.linalg.norm(voltage - exact) / np.linalg.norm(exact))
    constant = np.ones(n_cells, dtype=np.float64)
    constant_laplacian = np.empty_like(constant)
    constant_laplacian[1:-1] = (
        constant[:-2] - 2.0 * constant[1:-1] + constant[2:]
    ) / (dx * dx)
    constant_laplacian[0] = (constant[1] - constant[0]) / (dx * dx)
    constant_laplacian[-1] = (constant[-2] - constant[-1]) / (dx * dx)
    return {
        "n_cells": n_cells,
        "n_steps": n_steps,
        "dt": dt,
        "relative_l2_error": relative_l2_error,
        "max_energy_relative_increase": max_relative_increase,
        "constant_voltage_axial_residual": float(np.max(np.abs(constant_laplacian))),
    }


def passive_check() -> dict[str, object]:
    coarse = passive_run(32)
    fine = passive_run(64)
    ratio = float(coarse["relative_l2_error"]) / float(fine["relative_l2_error"])
    energy_max = max(
        float(coarse["max_energy_relative_increase"]),
        float(fine["max_energy_relative_increase"]),
    )
    passed = (
        energy_max <= THRESHOLDS["energy_relative_increase_max"]
        and float(fine["relative_l2_error"])
        <= THRESHOLDS["fine_relative_l2_error_max"]
        and ratio >= THRESHOLDS["refinement_ratio_min"]
        and float(coarse["constant_voltage_axial_residual"]) == 0.0
        and float(fine["constant_voltage_axial_residual"]) == 0.0
    )
    return {
        "status": "PASS" if passed else "FAIL",
        "equation": "u_t = 0.2 u_xx - 0.3 u; sealed ends; u(x,0)=cos(pi x)",
        "exact_solution": "exp(-(0.2*pi^2+0.3)t)*cos(pi*x)",
        "coarse": coarse,
        "fine": fine,
        "refinement_ratio": ratio,
        "maximum_energy_relative_increase": energy_max,
    }


def sigmoid(value: float) -> float:
    if value >= 0.0:
        return 1.0 / (1.0 + math.exp(-value))
    exponential = math.exp(value)
    return exponential / (1.0 + exponential)


def active_current(voltage: float) -> float:
    gate = sigmoid((voltage + 0.15) / 0.35)
    return 0.2 * (voltage + 1.3) + gate**3 * (voltage - 1.1)


def nonlinearity_check() -> dict[str, object]:
    low, midpoint, high = -1.0, 0.0, 1.0
    values = [active_current(value) for value in (low, midpoint, high)]
    midpoint_residual = abs(values[1] - 0.5 * (values[0] + values[2]))
    normalized_residual = midpoint_residual / max(abs(value) for value in values)
    linear_values = [value - 1.1 for value in (low, midpoint, high)]
    linear_residual = abs(
        linear_values[1] - 0.5 * (linear_values[0] + linear_values[2])
    )
    passed = (
        normalized_residual >= THRESHOLDS["nonlinearity_residual_min"]
        and linear_residual <= 1.0e-15
        and finite(values)
    )
    return {
        "status": "PASS" if passed else "FAIL",
        "dimensionless_test_voltages": [low, midpoint, high],
        "active_current_values": values,
        "normalized_midpoint_nonlinearity": normalized_residual,
        "fixed_conductance_linear_control_residual": linear_residual,
    }


def raw_bump(unit_lag: np.ndarray | float) -> np.ndarray:
    values = np.asarray(unit_lag, dtype=np.float64)
    result = np.zeros_like(values)
    inside = (values > 0.0) & (values < 1.0)
    selected = values[inside]
    result[inside] = np.exp(-1.0 / (selected * (1.0 - selected)))
    return result


def history_check() -> dict[str, object]:
    grid = np.linspace(0.0, 1.0, 20001, dtype=np.float64)
    normalization = float(np.trapezoid(raw_bump(grid), grid))
    constant = 1.0 / normalization

    def bump(value: float) -> float:
        return constant * float(raw_bump(value))

    normalized_integral = float(np.trapezoid(constant * raw_bump(grid), grid))
    outside_values = [bump(value) for value in (-1.0, -0.2, 0.0, 1.0, 1.2)]
    inside_values = [bump(value) for value in (0.1, 0.25, 0.5, 0.75, 0.9)]
    step = 0.01
    endpoint_proxies = [
        abs(bump(step) / step),
        abs((bump(2.0 * step) - 2.0 * bump(step) + bump(0.0)) / step**2),
        abs(bump(1.0 - step) / step),
        abs(
            (
                bump(1.0 - 2.0 * step)
                - 2.0 * bump(1.0 - step)
                + bump(1.0)
            )
            / step**2
        ),
    ]
    g_min, g_max = 0.1, 2.0
    conductances = [
        g_min + (g_max - g_min) * sigmoid(argument)
        for argument in (-100.0, 0.0, 100.0)
    ]
    causal_before_event = bump(-0.5)
    reversed_before_event = bump(0.5)
    passed = (
        max(abs(value) for value in outside_values) == 0.0
        and min(inside_values) >= 0.0
        and finite(inside_values)
        and abs(normalized_integral - 1.0)
        <= THRESHOLDS["kernel_normalization_error_max"]
        and max(endpoint_proxies)
        <= THRESHOLDS["kernel_endpoint_flatness_proxy_max"]
        and min(conductances) >= g_min
        and max(conductances) <= g_max
        and causal_before_event == 0.0
        and reversed_before_event > 0.0
    )
    return {
        "status": "PASS" if passed else "FAIL",
        "normalized_integral": normalized_integral,
        "normalization_error": abs(normalized_integral - 1.0),
        "outside_support_values": outside_values,
        "inside_support_values": inside_values,
        "endpoint_flatness_proxies": endpoint_proxies,
        "bounded_conductances": conductances,
        "strict_past_no_atom_at_zero": bump(0.0) == 0.0,
        "causal_before_event": causal_before_event,
        "time_reversed_control_before_event": reversed_before_event,
        "time_reversal_detected": reversed_before_event > 0.0,
    }


def build_receipt(run_root: Path) -> dict[str, object]:
    actual_hashes = {
        name: sha256(run_root / name) for name in EXPECTED_INPUT_HASHES
    }
    source_match = actual_hashes == EXPECTED_INPUT_HASHES
    checks: dict[str, dict[str, object]] = {}
    if source_match:
        checks = {
            "U0_units": unit_check(),
            "K0_kirchhoff_ohm": kirchhoff_and_ohm_check(),
            "P0_passive_mode": passive_check(),
            "N0_active_nonlinearity": nonlinearity_check(),
            "H0_causal_history": history_check(),
        }
    failed = [name for name, result in checks.items() if result["status"] != "PASS"]
    status = "PASS" if source_match and not failed else "FAIL"
    if not source_match:
        status = "SOURCE_MISMATCH"
    script_path = Path(__file__).resolve()
    return {
        "schema": SCHEMA,
        "status": status,
        "claim_status": "L0_NUMERICAL_INTEGRITY_ONLY" if status == "PASS" else "NO_PROMOTION",
        "source_match": source_match,
        "expected_input_sha256": EXPECTED_INPUT_HASHES,
        "actual_input_sha256": actual_hashes,
        "script_sha256": sha256(script_path),
        "apparatus_revision": {
            "attempt": 1,
            "predecessor_receipt_sha256": "848a0a5ab528dc681eff9c384dbb0e733366ba3e89e45a2283399965658b41c4",
            "scope": "H0 numeric predicate only",
            "reason": "Use a machine-precision-scaled finite-difference tolerance and closed floating-point conductance bounds; electrical equations and all other gates are unchanged.",
        },
        "environment": {
            "python_executable": sys.executable,
            "python_version": platform.python_version(),
            "numpy_version": np.__version__,
            "platform": platform.platform(),
            "bytecode_disabled": sys.dont_write_bytecode,
        },
        "thresholds": THRESHOLDS,
        "checks": checks,
        "failed_checks": failed,
        "behavior_loaded": False,
        "model_fit": False,
        "real_endpoint_opened": False,
        "biological_claim": False,
        "consciousness_claim": False,
        "downstream_authorized": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).resolve().with_name("l0-receipt.json"),
    )
    args = parser.parse_args()
    run_root = Path(__file__).resolve().parents[1]
    receipt = build_receipt(run_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(receipt, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(receipt, sort_keys=True, allow_nan=False))
    return 0 if receipt["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
