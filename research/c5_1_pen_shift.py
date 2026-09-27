"""C5-1: 방향 성분과 대칭 성분은 다른 경로에 실린다 (전제 C5).

명제: 초파리 방향 고리에서 기억 평면(대칭 결합 W_s의 선도 쌍이 EPG 위에 놓는 원)을 돌리는 방향 성분은 PEN의 PB
경로(EPG→PEN 시냅스가 PB에 있는 길)에만 실리고, 같은 PEN의 EB 경로는 평면을 돌리지 않는다. 이는 세 개체의
연결체에서 모두 성립한다. 공통 식에서 F(방향)가 W_s(지형·유지)와 해부학적으로 분리된다는 구조 근거다.
식: 경로 행렬 P = W(PEN→EPG, EB)·W(EPG→PEN, 영역)을 평면에 사영해 척도·회전(등각)으로 적는다(1·2b단계와 같다).
생물 기준값: PEN은 PB 사구체에서 받은 EPG 입력을 EB에서 한 타일(45°) 옆으로 보내고, 좌·우 PB의 PEN은 서로 반대쪽으로
어긋난다 (Green et al. 2017 Nature 546:101; Turner-Evans et al. 2017 eLife 6:e23496; Hulse et al. 2021 eLife 10:e66039).
자료(원장): malecns (수컷 전신경계 v1.0; 가설을 세운 자료), hemibrain-v1.2 (암컷 반뇌), flywire-783 (암컷 전뇌).
세포형 EPG·PEN_a(PEN1)·PEN_b(PEN2)·PEG·Delta7, 부호는 문헌값(아세틸콜린 +, Δ7 글루탐산 −)을 세 자료에 같게 쓴다.
PEN의 좌·우는 PB 반쪽이다(MaleCNS에서 사구체 이름의 반쪽과 세포체 쪽이 106/106 일치하여 FlyWire는 세포체 쪽을 쓴다).
판정(실행 전 고정), 연결체마다:
- 도구: EPG 반지름 변동 < 0.25 (평면이 원)
- PB 경로: 두 쪽 등각 비율 > 0.9, 회전 부호 반대, |회전각| 30–60°
- EB 경로: 두 쪽 |회전각| < 15°
역증명: PB 경로의 |회전각|이 45°에서 벗어난 최댓값 ≤ 15° < PB·EB를 가르지 않은 전체 PEN 경로의 벗어남 최솟값
"""

from functools import cache

import numpy as np
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.csv as pcsv
import pyarrow.feather as feather

from research import core, harness, malecns
from research.step02_pen_rotation import describe

TYPES = ["EPG", "PEN_a(PEN1)", "PEN_b(PEN2)", "PEG", "Delta7"]
PEN = ["PEN_a(PEN1)", "PEN_b(PEN2)"]
SIGN = {"EPG": 1.0, "PEN_a(PEN1)": 1.0, "PEN_b(PEN2)": 1.0, "PEG": 1.0, "Delta7": -1.0}
TILE, TOLERANCE, EB_MAX, RADIUS = 45.0, 15.0, 15.0, 0.25


def matrices(ids, pre, post, weight, roi):
    """W[post, pre] among ids: total and per PB/EB, from connection rows."""
    local = {b: i for i, b in enumerate(ids)}
    n = len(ids)
    out = {k: np.zeros((n, n)) for k in ("total", "PB", "EB")}
    for a, b, w, r in zip(pre, post, weight, roi):
        i, j = local[b], local[a]
        out["total"][i, j] += w
        if r in ("PB", "EB"):
            out[r][i, j] += w
    return out


def rows_among(table, ids, pre, post):
    keep = pa.array(np.asarray(ids, np.int64))
    return table.filter(pc.and_(pc.is_in(table[pre], value_set=keep), pc.is_in(table[post], value_set=keep)))


@cache
def male():
    index = malecns.neurons(TYPES)
    kinds = np.array(malecns.cell_types(index))
    sides = np.array([(malecns.glomerulus(s) or ("",))[0] for s in malecns.instances(index)])
    w = {"total": malecns.weights(index), "PB": malecns.weights_in(index, "PB"), "EB": malecns.weights_in(index, "EB")}
    rows = [harness.registered(*malecns.SOURCES[k])[0] for k in ("graph", "roi", "annotations")]
    return kinds, sides, w, rows


@cache
def hemibrain():
    rows = harness.registered("hemibrain-v1.2")
    path = {r["asset"].split(" ")[0]: harness.path(r) for r in rows}
    neurons = pcsv.read_csv(path["traced-neurons.csv"])
    types = np.array(neurons["type"].to_pylist(), dtype=object)
    keep = np.isin(types, TYPES)
    ids = np.array(neurons["bodyId"].to_pylist())[keep]
    order = np.argsort(ids)
    ids, kinds = ids[order], types[keep][order].astype(str)
    instance = np.array(neurons["instance"].to_pylist(), dtype=object)[keep][order]
    sides = np.array([(malecns.glomerulus(s or "") or ("",))[0] for s in instance])
    roi = rows_among(pcsv.read_csv(path["traced-roi-connections.csv"]), ids, "bodyId_pre", "bodyId_post")
    total = rows_among(pcsv.read_csv(path["traced-total-connections.csv"]), ids, "bodyId_pre", "bodyId_post")
    w = matrices(ids, roi["bodyId_pre"].to_pylist(), roi["bodyId_post"].to_pylist(), roi["weight"].to_pylist(),
                 roi["roi"].to_pylist())
    w["total"] = matrices(ids, total["bodyId_pre"].to_pylist(), total["bodyId_post"].to_pylist(),
                          total["weight"].to_pylist(), [None] * total.num_rows)["total"]
    used = [r for r in rows if r["asset"].split(" ")[0] in ("traced-neurons.csv", "traced-roi-connections.csv",
                                                              "traced-total-connections.csv")]
    return kinds, sides, w, used


@cache
def flywire():
    rows = harness.registered("flywire-783")
    path = {r["asset"]: harness.path(r) for r in rows}
    notes = pcsv.read_csv(path["Supplemental_file1_neuron_annotations.tsv"],
                          parse_options=pcsv.ParseOptions(delimiter="\t"),
                          convert_options=pcsv.ConvertOptions(column_types={"root_id": pa.int64()}))
    types = np.array(notes["cell_type"].to_pylist(), dtype=object)
    keep = np.isin(types, TYPES)
    ids = np.array(notes["root_id"].to_pylist())[keep]
    order = np.argsort(ids)
    ids, kinds = ids[order], types[keep][order].astype(str)
    sides = np.array([{"left": "L", "right": "R"}.get(s, "") for s in
                      np.array(notes["side"].to_pylist(), dtype=object)[keep][order]])
    edges = rows_among(feather.read_table(path["proofread_connections_783.feather"], memory_map=True,
                                          columns=["pre_pt_root_id", "post_pt_root_id", "neuropil", "syn_count"]),
                       ids, "pre_pt_root_id", "post_pt_root_id")
    w = matrices(ids, edges["pre_pt_root_id"].to_pylist(), edges["post_pt_root_id"].to_pylist(),
                 edges["syn_count"].to_pylist(), edges["neuropil"].to_pylist())
    return kinds, sides, w, rows


def analyse(kinds, sides, w):
    """Memory plane from W_s, then the PB, EB and whole PEN paths on it for each PB side."""
    sign = np.array([SIGN[k] for k in kinds])
    raw = w["total"]
    total = np.abs(raw * sign).sum(1, keepdims=True)
    leg = {roi: np.divide(w[roi] * sign, total, out=np.zeros_like(raw), where=total > 0) for roi in ("PB", "EB")}
    values, basis = core.plane(core.split(core.normalize(raw, sign))[0], kinds)
    epg = kinds == "EPG"
    plane = basis[epg]
    _, spread = core.circle(plane)
    out = {"neurons": {t: int((kinds == t).sum()) for t in TYPES}, "pair_eigenvalues": values.tolist(),
           "epg_radius_variation": float(spread)}
    for side in "LR":
        pen = np.isin(kinds, PEN) & (sides == side)
        back = leg["EB"][np.ix_(epg, pen)]
        pb, eb = back @ leg["PB"][np.ix_(pen, epg)], back @ leg["EB"][np.ix_(pen, epg)]
        out[side] = {"pen": int(pen.sum()), "pb_path": describe(pb, plane), "eb_path": describe(eb, plane),
                     "whole_path": describe(pb + eb, plane)}
    return out


def checks(name, r):
    left, right = r["L"], r["R"]
    return {
        f"{name}_ring": harness.check(r["epg_radius_variation"], high=RADIUS),
        f"{name}_pb_conformal": harness.check(min(left["pb_path"]["conformal"], right["pb_path"]["conformal"]), 0.9),
        f"{name}_pb_opposite": harness.check(-np.sign(left["pb_path"]["angle_deg"]) * np.sign(right["pb_path"]["angle_deg"]), 1),
        f"{name}_pb_tile": harness.check(max(abs(abs(p["pb_path"]["angle_deg"]) - TILE) for p in (left, right)), high=TOLERANCE),
        f"{name}_eb_holds": harness.check(max(abs(p["eb_path"]["angle_deg"]) for p in (left, right)), high=EB_MAX),
    }


def main():
    loaded = {"malecns": male(), "hemibrain": hemibrain(), "flywire": flywire()}
    rows = [r for *_, used in loaded.values() for r in used]
    harness.verify([r for r in rows if harness.path(r).is_file()])
    results = {name: analyse(*x[:3]) for name, x in loaded.items()}
    judged = {k: v for name, r in results.items() for k, v in checks(name, r).items()}
    off = lambda path: [abs(abs(r[s][path]["angle_deg"]) - TILE) for r in results.values() for s in "LR"]
    result = harness.record(
        "c5_1_pen_shift", "C5",
        "방향 고리의 기억 평면을 돌리는 방향 성분은 PEN의 PB 경로에만 실려 좌·우 반대로 한 타일(45°) 돌리고, 같은 PEN의 "
        "EB 경로는 평면을 돌리지 않는다. 수컷 전신경계·암컷 반뇌·암컷 전뇌 세 연결체에서 모두 성립한다",
        "Green et al. 2017 Nature 546:101; Turner-Evans et al. 2017 eLife 6:e23496; Hulse et al. 2021 eLife 10:e66039: "
        "PEN의 PB→EB 한 타일(45°) 어긋남, 좌·우 반대",
        judged, rows, proof=harness.reverse("PB·EB 경로 분리", max(off("pb_path")), min(off("whole_path")), TOLERANCE),
        **results)
    print(result["verdict"])
    for name, r in results.items():
        print(name, r["neurons"], "반지름 변동 %.3f" % r["epg_radius_variation"])
        for s in "LR":
            print("   ", s, "PEN", r[s]["pen"], {p: (round(r[s][p]["angle_deg"], 1), round(r[s][p]["conformal"], 3))
                                                 for p in ("pb_path", "eb_path", "whole_path")})


if __name__ == "__main__":
    main()
