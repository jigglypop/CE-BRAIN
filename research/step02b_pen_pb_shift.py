"""2b단계: PEN의 PB→EB 어긋남.

2단계에서 좌·우 PEN 경로는 반대로 돌았지만 약 6°에 그쳤다(NOT_SUPPORTED). 문헌의 한 타일(45°)
어긋남은 PB에서 받은 EPG 입력을 EB로 옮길 때의 진술이다. 그래서 EPG→PEN 시냅스를 영역별로 나눈다.
- PB 경로: EPG→PEN(PB) 다음 PEN→EPG(EB)
- EB 경로: EPG→PEN(EB) 다음 PEN→EPG(EB)
문헌 기준: Green et al. 2017; Turner-Evans et al. 2017; Hulse et al. 2021.
판정(실행 전 고정): PB 경로가 두 쪽 모두 등각 비율 > 0.9, 회전각 부호 반대, |회전각| 30–60°.
EB 경로와 두 경로 합의 각도는 설명용으로만 보고한다.
"""

import json
from pathlib import Path

import numpy as np

from research import core, malecns
from research.step01_ring_plane import TYPES
from research.step02_pen_rotation import PEN, describe

OUT = Path(__file__).with_name("results") / "02b_pen_pb_shift.json"


def main():
    index = malecns.neurons(TYPES)
    kinds = np.array(malecns.cell_types(index))
    sign = malecns.signs(index)
    raw = malecns.weights(index)
    total = np.abs(raw * sign).sum(1, keepdims=True)  # 1–2단계와 같은 행 척도
    count = {roi: malecns.weights_in(index, roi) for roi in ("PB", "EB")}
    leg = {roi: np.divide(c * sign, total, out=np.zeros_like(raw), where=total > 0)
           for roi, c in count.items()}
    _, basis = core.plane(core.split(core.normalize(raw, sign))[0], kinds)
    epg = kinds == "EPG"
    plane = basis[epg]
    sides = np.array([(malecns.glomerulus(s) or ("",))[0] for s in malecns.instances(index)])
    result = {}
    for side in "LR":
        pen = np.isin(kinds, PEN["PEN"]) & (sides == side)
        back = leg["EB"][np.ix_(epg, pen)]
        pb, eb = back @ leg["PB"][np.ix_(pen, epg)], back @ leg["EB"][np.ix_(pen, epg)]
        inputs = raw[np.ix_(pen, epg)].sum()
        result[side] = {
            "pen": int(pen.sum()),
            "epg_to_pen_share": {roi: float(c[np.ix_(pen, epg)].sum() / inputs) for roi, c in count.items()},
            "pb_path": describe(pb, plane), "eb_path": describe(eb, plane), "sum": describe(pb + eb, plane),
        }
    left, right = result["L"]["pb_path"], result["R"]["pb_path"]
    passed = (min(left["conformal"], right["conformal"]) > 0.9
              and np.sign(left["angle_deg"]) != np.sign(right["angle_deg"])
              and all(30 <= abs(p["angle_deg"]) <= 60 for p in (left, right)))
    result["verdict"] = "SUPPORTED" if passed else "NOT_SUPPORTED"
    OUT.write_text(json.dumps(result, indent=1), encoding="utf-8")
    print(json.dumps(result, indent=1))


if __name__ == "__main__":
    main()
