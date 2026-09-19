"""Check the installed distribution as a CE consumer, outside the source tree."""
from __future__ import annotations
import json
from pathlib import Path
import subprocess
import sys

def test_installed_reality_stone_clarus_example_runs(tmp_path: Path) -> None:
    code = """
import json
from importlib.metadata import version
import torch
import reality_stone as rs
from reality_stone.clarus.runtime import BrainRuntime, BrainRuntimeConfig, RuntimeMode
x = torch.tensor([[0.1, 0.2]], requires_grad=True)
rs.poincare_add(x, torch.zeros_like(x), c=1.0).sum().backward()
assert torch.isfinite(x.grad).all()
runtime = BrainRuntime(torch.zeros(8, 8), config=BrainRuntimeConfig(dim=8, noise_sigma=0.0), backend="torch", device="cpu")
step = runtime.step(external_input=torch.ones(8) * 0.1, force_mode=RuntimeMode.WAKE)
assert step.mode == RuntimeMode.WAKE
print(json.dumps({"version": rs.__version__, "distribution": version("reality_stone"), "package": rs.__file__}))
"""
    result = subprocess.run([sys.executable, "-I", "-B", "-c", code],
                            cwd=tmp_path, check=True, capture_output=True, text=True, timeout=120)
    report = json.loads(result.stdout)
    assert report["version"] == report["distribution"] == "0.3.0"
    assert not Path(report["package"]).resolve().is_relative_to(Path(__file__).resolve().parents[1])
