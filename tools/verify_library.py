"""Verify this checkout consumes the published library, without vendored source."""
from __future__ import annotations
from importlib.metadata import distribution
import json
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    assert not (root / "reality_stone").exists(), "vendored source directory still exists"
    dist = distribution("reality_stone")
    assert dist.version == "0.3.0", dist.version
    import torch
    import reality_stone as rs
    import reality_stone.clarus as clarus
    from reality_stone.clarus.runtime import BrainRuntime, BrainRuntimeConfig, RuntimeMode

    package_path = Path(rs.__file__).resolve()
    assert not package_path.is_relative_to(root), package_path
    assert rs.__version__ == clarus.__version__ == dist.version
    assert rs._has_rust_ext and clarus.has_native_kernels(), "release CPU extensions did not load"
    x = torch.tensor([[0.1, 0.2]], requires_grad=True)
    rs.poincare_add(x, torch.zeros_like(x), c=0.7).square().sum().backward()
    assert torch.isfinite(x.grad).all()
    runtime = BrainRuntime(torch.zeros(8, 8),
                           config=BrainRuntimeConfig(dim=8, noise_sigma=0.0, axon_delay=False),
                           backend="rust", device="cpu")
    step = runtime.step(external_input=torch.linspace(0, 0.2, 8), force_mode=RuntimeMode.WAKE)
    assert step.mode == RuntimeMode.WAKE and torch.isfinite(torch.tensor(step.energy))
    print(json.dumps({"status": "PASS", "version": dist.version, "package_path": str(package_path),
                      "geometry_native": rs._has_rust_ext, "runtime_native": clarus.has_native_kernels(),
                      "gradient": "PASS", "runtime_mode": step.mode.name}))


if __name__ == "__main__":
    main()
