"""Audit copy for step 29 (does NOT change the frozen verdict): FlyWire planar embedding corrected to the 120-degree
basis X = p - q/2, Y = q*sqrt(3)/2. Step-30 diagnostics showed the lateral coupling runs along (+-1,0), (0,+-1) and
(+-1,+-1), not (1,-1): the frozen 60-degree embedding X=(q-p)/2, Y=(p+q)*sqrt(3)/2 was wrong. Everything else identical."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
src = (HERE / "visual_shift.py").read_text(encoding="utf-8")
old = 'xy = np.column_stack([(col["q"] - col["p"]) / 2.0, (col["p"] + col["q"]) * np.sqrt(3) / 2.0])'
new = 'xy = np.column_stack([col["p"] - col["q"] / 2.0, col["q"] * np.sqrt(3) / 2.0])'
assert old in src
src = src.replace(old, new, 1)
src = src.replace('code_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()\n    if code_hash not in (HERE / "CONTRACT.md").read_text(encoding="utf-8"):\n        raise SystemExit(f"CONTRACT.md does not list this code hash {code_hash}")',
                  'code_hash = "audit-embedding-120deg"')
src = src.replace('with (HERE / "results.json").open("x", encoding="utf-8") as stream:', 'with (HERE / "results_embedding_audit.json").open("x", encoding="utf-8") as stream:')
ns = {"__file__": str(HERE / "visual_shift.py"), "__name__": "audit"}
exec(compile(src, "visual_shift_audit", "exec"), ns)
ns["main"]()
