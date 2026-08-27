"""Dimension audit for the R2 normalized variables; not a model-validity test."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


def load_dimensionless():
    root = next(
        parent
        for parent in Path(__file__).resolve().parents
        if (parent / "reality_stone/python/reality_stone/clarus/dimensionless.py").exists()
    )
    path = root / "reality_stone/python/reality_stone/clarus/dimensionless.py"
    spec = importlib.util.spec_from_file_location("ce_r2_dimensionless", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def main() -> None:
    dm = load_dimensionless()
    length_per_time = dm.dim(0, 1, -1, 0)
    quantities = [
        dm.Quantity("spike_count", 3.0),
        dm.nondimensionalize(
            dm.Quantity("centered_position", 0.25, dm.LENGTH),
            [dm.Quantity("train_position_scale", 0.5, dm.LENGTH)],
        ),
        dm.nondimensionalize(
            dm.Quantity("centered_velocity", 0.2, length_per_time),
            [dm.Quantity("train_velocity_scale", 0.4, length_per_time)],
        ),
        dm.Quantity("head_direction_radians", 1.2),
        dm.Quantity("standardized_neural_state", -0.3),
        dm.Quantity("ridge_lambda", 1e-2),
        dm.Quantity("fiber_gain_q", 0.9),
        dm.Quantity("nmse", 0.96),
        dm.Quantity("projector_distance", 0.4),
    ]
    result = dm.audit_dimensionless(quantities, context="R2 local-bundle core")
    if not result.passed:
        raise AssertionError(result.errors)
    assert all(item.dimensionless for item in result.unwrap())
    print("PASS R2 normalized state, chart distance, ridge, contraction, and NMSE are dimensionless")


if __name__ == "__main__":
    main()
