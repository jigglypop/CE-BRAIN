# Reality Stone

Reality Stone is the vendored geometry backend used by Clarus Equation.

This copy is kept lean for integration: runtime code, Rust bindings, Python
fallbacks, and tests are retained; upstream repository metadata, build outputs,
experiments, and generated documentation are intentionally omitted.

## Layout

```text
reality_stone/
  src/                    Rust core and PyO3 bindings  -> reality_stone._rust
  python/reality_stone/   Python API and fallback implementations
  python/reality_stone/clarus/
                          Clarus runtime and CE modules
  python/reality_stone/clarus/core/
                          Second Rust crate (clarus_core) -> reality_stone.clarus._rust
  examples/               Single unified Clarus/Reality Stone demo
  tests/                  Rust and Python regression tests
  Cargo.toml              Rust crate metadata (outer crate)
  pyproject.toml          Python/maturin package metadata (outer crate)
```

## Python Usage

```python
import reality_stone as rs
from reality_stone.clarus.runtime import BrainRuntime

status = (rs.__version__, rs._has_rust_ext, rs._has_cuda)
```

`python/reality_stone/_rust.py` is a pure-Python stub (`IS_FALLBACK = True`). It is
what `import reality_stone._rust` resolves to until a compiled `_rust.pyd`/`.so`
is placed next to it. The layer modules, `core/mobius.py`, `optim/riemannian_adam.py`
and `layers/spline.py` detect the stub and switch to differentiable torch formulas
from `_fallback.py`, so forward values and autograd gradients stay correct without
the native build. `models/transformer_converter.py` (RS-ULF conversion) has no
Python fallback and raises until the extension is built.

## Native Build

Two independent pyo3 crates both name their cdylib `_rust`:

| crate | module | contents |
|---|---|---|
| `reality_stone/` (this directory) | `reality_stone._rust` | Mobius/Poincare/Lorentz/Klein ops, metrikey, RS-ULF, spline, geodesic memory |
| `python/reality_stone/clarus/core/` | `reality_stone.clarus._rust` | brain_step kernel, CE relax, Riemann attention, pre-eq |

The repository-root `pyproject.toml` builds only the clarus crate through maturin.
The venv-free path that builds both with cargo and installs them in-tree is

    .codex\hooks\build-native.cmd            # release build of both crates
    .codex\hooks\build-native.cmd --only outer
    .codex\hooks\build-native.cmd --cuda     # needs nvcc / CUDA_HOME

Set `PYO3_PYTHON` if the interpreter selected by `.codex/hooks/python.cmd` is not
the one you want the outer (non-abi3) crate linked against.

## Validation

From the repository root, using the harness Python (never the workspace `.venv`):

    .codex\hooks\python.cmd pytest reality_stone\tests\layer -q
    .codex\hooks\python.cmd pytest reality_stone\tests\test_unified_riemannian.py reality_stone\tests\llm\test_metric_attention.py reality_stone\tests\llm\test_metric_router.py reality_stone\tests\api\test_pipeline_api.py -q
    cargo test --manifest-path reality_stone\Cargo.toml --no-default-features
    cargo test --manifest-path reality_stone\python\reality_stone\clarus\core\Cargo.toml
    .codex\hooks\python.cmd python reality_stone\examples\unified_clarus_demo.py

Tests marked `cuda` skip without a GPU and without the native build; the GPT-2 and
Qwen inference tests under `tests/llm/` need network access or an explicit opt-in.
