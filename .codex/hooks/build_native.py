"""Build the two optional Rust extensions and install them in-tree.

The repository has two independent pyo3 crates:

* ``reality_stone/``  -> ``reality_stone._rust`` (hyperbolic layers, metrikey, RS-ULF)
* ``reality_stone/python/reality_stone/clarus/core/`` -> ``reality_stone.clarus._rust``
  (brain_step kernel, CE relax, Riemann attention, pre-eq)

Both crates name their cdylib ``_rust``; only their destination directory differs.
The root ``pyproject.toml`` builds the clarus crate through maturin; this script is
the venv-free path that builds both with ``cargo`` and copies the artifacts where
``import reality_stone`` and ``import reality_stone.clarus`` look for them. Without
these files every consumer falls back to the pure-Python paths.

Usage: ``.codex/hooks/build-native.cmd [--debug] [--only outer|inner] [--cuda]``
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import sysconfig
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PACKAGE = REPO_ROOT / "reality_stone" / "python" / "reality_stone"
CRATES = {
    "outer": {
        "manifest_dir": REPO_ROOT / "reality_stone",
        "features": [],
        "cuda_feature": "cuda",
        "destination": PACKAGE,
    },
    "inner": {
        "manifest_dir": PACKAGE / "clarus" / "core",
        "features": ["python"],
        "cuda_feature": "cuda",
        "destination": PACKAGE / "clarus",
    },
}


def _artifact_name(profile_dir: Path) -> Path:
    if sys.platform == "win32":
        return profile_dir / "_rust.dll"
    if sys.platform == "darwin":
        return profile_dir / "lib_rust.dylib"
    return profile_dir / "lib_rust.so"


def _module_filename() -> str:
    if sys.platform == "win32":
        return "_rust.pyd"
    suffix = sysconfig.get_config_var("EXT_SUFFIX") or ".so"
    return f"_rust{suffix}"


def build(name: str, *, release: bool, cuda: bool) -> Path:
    crate = CRATES[name]
    features = list(crate["features"])
    if cuda:
        features.append(crate["cuda_feature"])
    command = ["cargo", "build"]
    if release:
        command.append("--release")
    if features:
        command += ["--features", ",".join(features)]
    env = os.environ.copy()
    env.setdefault("PYO3_PYTHON", sys.executable)
    print(f"[{name}] {' '.join(command)} (cwd={crate['manifest_dir']})")
    subprocess.run(command, cwd=crate["manifest_dir"], env=env, check=True)
    profile_dir = crate["manifest_dir"] / "target" / ("release" if release else "debug")
    artifact = _artifact_name(profile_dir)
    if not artifact.exists():
        raise FileNotFoundError(f"[{name}] expected cargo artifact missing: {artifact}")
    destination = crate["destination"] / _module_filename()
    shutil.copy2(artifact, destination)
    print(f"[{name}] installed {destination}")
    return destination


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--debug", action="store_true", help="build the debug profile")
    parser.add_argument("--only", choices=sorted(CRATES), help="build a single crate")
    parser.add_argument("--cuda", action="store_true", help="enable the cuda feature")
    args = parser.parse_args(argv)
    names = [args.only] if args.only else ["inner", "outer"]
    for name in names:
        build(name, release=not args.debug, cuda=args.cuda)
    print("done; verify with: python.cmd python -c \"import reality_stone as rs, reality_stone.clarus as c; print(rs._has_rust_ext, c.has_native_kernels())\"")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
