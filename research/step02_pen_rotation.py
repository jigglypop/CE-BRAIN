"""2단계: 방향 연산자.

질문: 좌·우 PEN 경로(EPG→PEN→EPG)가 1단계 기억 평면을 서로 반대 방향으로 돌리는가.
문헌 기준: PEN은 EPG 입력을 받은 PB 사구체에서 한 타일(45°) 옆 EB로 투사하고, 좌·우 PB의
PEN은 서로 반대쪽으로 어긋난다(Green et al. 2017; Turner-Evans et al. 2017).
판정(실행 전 고정): 두 쪽 모두 등각 비율 > 0.9, 회전각 부호가 반대, |회전각| 30–60°.
"""

import json
from pathlib import Path

import numpy as np

from research import core, malecns
from research.step01_ring_plane import TYPES

PEN = {"PEN": ["PEN_a(PEN1)", "PEN_b(PEN2)"], "PEN_a": ["PEN_a(PEN1)"], "PEN_b": ["PEN_b(PEN2)"]}
OUT = Path(__file__).with_name("results") / "02_pen_rotation.json"


def describe(path, plane):
    """Scale·rotation that best describes an EPG → EPG path on the memory plane."""
    m = np.linalg.pinv(plane) @ path @ plane
    angle, scale, share = core.conformal(m)
    inplane = 1 - np.sum((path @ plane - plane @ m) ** 2) / np.sum((path @ plane) ** 2)
    return {"angle_deg": float(angle), "scale": float(scale), "conformal": float(share),
            "inplane": float(inplane)}


def rotation(w, plane, epg, pen):
    """EPG → PEN → EPG through the selected PEN neurons."""
    return {"pen": int(pen.sum()), **describe(w[np.ix_(epg, pen)] @ w[np.ix_(pen, epg)], plane)}


def main():
    index = malecns.neurons(TYPES)
    kinds = np.array(malecns.cell_types(index))
    w = core.normalize(malecns.weights(index), malecns.signs(index))
    _, basis = core.plane(core.split(w)[0], kinds)
    epg = kinds == "EPG"
    sides = np.array([(malecns.glomerulus(s) or ("",))[0] for s in malecns.instances(index)])
    paths = {f"{name}_{side}": rotation(w, basis[epg], epg, np.isin(kinds, types) & (sides == side))
             for name, types in PEN.items() for side in "LR"}
    left, right = paths["PEN_L"], paths["PEN_R"]
    passed = (min(left["conformal"], right["conformal"]) > 0.9
              and np.sign(left["angle_deg"]) != np.sign(right["angle_deg"])
              and all(30 <= abs(p["angle_deg"]) <= 60 for p in (left, right)))
    result = {"paths": paths, "verdict": "SUPPORTED" if passed else "NOT_SUPPORTED"}
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(result, indent=1), encoding="utf-8")
    print(json.dumps(result, indent=1))


if __name__ == "__main__":
    main()
