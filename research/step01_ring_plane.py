"""1단계: 방향 고리의 기억 평면.

질문: EPG·PEN_a·PEN_b·PEG·Δ7 고리에서 계량 W_s의 최소 비용 쌍이 EPG 위에 원을 이루고,
그 원 위 각도가 PB 사구체 순서를 따라 사구체당 45°씩 도는가.
문헌 기준: PB 반쪽의 8사구체가 방향 360°를 나눈다(사구체당 45°; Wolff et al. 2015, Hulse et al. 2021).
판정(실행 전 고정): 쌍의 고유값 차 < 5%, EPG 반지름 변동 < 0.25, 두 반쪽 모두 |기울기| 35–55°이고 R > 0.9.
"""

import json
from pathlib import Path

import numpy as np

from research import core, malecns

TYPES = ["EPG", "PEN_a(PEN1)", "PEN_b(PEN2)", "PEG", "Delta7"]
OUT = Path(__file__).with_name("results") / "01_ring_plane.json"


def main():
    index = malecns.neurons(TYPES)
    kinds = malecns.cell_types(index)
    sign = malecns.signs(index)
    ws, _ = core.split(core.normalize(malecns.weights(index), sign))
    values, basis = core.plane(ws, kinds)
    epg = np.array([k == "EPG" for k in kinds])
    angle, spread = core.circle(basis[epg])
    glomeruli = [malecns.glomerulus(s) for s in np.array(malecns.instances(index))[epg]]
    halves = {}
    for side in "LR":
        mask = np.array([g is not None and g[0] == side for g in glomeruli])
        k = np.array([g[1] for g in glomeruli if g is not None and g[0] == side], float)
        slope, r = core.angle_slope(angle[mask], k)
        halves[side] = {"epg": int(mask.sum()), "slope_deg_per_glomerulus": float(slope), "R": float(r)}
    gap = float(abs(values[0] - values[1]) / abs(values[0]))
    passed = gap < 0.05 and spread < 0.25 and all(
        35 <= abs(h["slope_deg_per_glomerulus"]) <= 55 and h["R"] > 0.9 for h in halves.values())
    result = {
        "neurons": {t: kinds.count(t) for t in TYPES},
        "sign": {t: float(sign[kinds.index(t)]) for t in TYPES},
        "pair_eigenvalues": values.tolist(),
        "pair_gap": gap,
        "epg_radius_variation": float(spread),
        "halves": halves,
        "verdict": "SUPPORTED" if passed else "NOT_SUPPORTED",
    }
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(result, indent=1), encoding="utf-8")
    print(json.dumps(result, indent=1))


if __name__ == "__main__":
    main()
