"""원장에 없는 공개 자료를 세션 형식으로 가져와 등록한다: python -m research.fetch <이름>.

항목마다 판본, 겨냥하는 전제, 가져올 표·시계열의 HDF5 경로, 원 논문을 적는다. 원격 NWB는 HTTP 범위 읽기로
필요한 부분만 읽고, 이미 등록된 자산과 필요한 표가 없는 세션은 건너뛴다.
"""

import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from research import harness, store

SOURCES = {
    "dandi-000056": {
        "dandiset": "000056", "version": "0.250624.0430",
        "premises": "C3-2 흔적의 독립 재현, C4-4 논렘 지연 공분산",
        "tables": {"states": "processing/behavior/states"},
        "series": {"blue": "processing/behavior/SubjectPosition/BlueLED",
                   "red": "processing/behavior/SubjectPosition/RedLED"},
        "citation": "Peyrache A, Lacroix MM, Petersen PC, Buzsáki G (2015) Nat Neurosci 18:569–575, "
                    "doi:10.1038/nn.3968 (CRCNS th-1)",
    },
    "dandi-000044": {
        "dandiset": "000044", "version": "0.250624.0426",
        "premises": "C6 활동 이력에 따른 관계 변화(트랙 뒤 수면의 재활성), C7 해마 주소·검색",
        "tables": {"epochs": "intervals/epochs", "states": "processing/behavior/states"},
        "series": {"position": "processing/behavior/*LinearizedPosition/*"},
        "citation": "Grosmark AD, Buzsáki G (2016) Science 351:1440–1443, doi:10.1126/science.aad1935 (CRCNS hc-11)",
    },
    "dandi-001699": {
        "dandiset": "001699", "version": "0.260917.2322", "genotype": "WT",
        "premises": "C1-3 공통 식 매개변수의 이전(다른 연구실·종의 수면 머리방향 기록)",
        "tables": None,
        "series": {"head": "processing/behavior/CompassDirection/head-direction"},
        "citation": "Moore JL, Duszkiewicz AJ, Asiminas A, Dudchenko PA, Peyrache A, Wood ER (2025) bioRxiv "
                    "doi:10.1101/2025.01.09.632139 (쥐 후구상, 야생형만)",
    },
}


def fetch(name, workers=4):
    spec = SOURCES[name]
    try:
        done = {row["asset"] for row in harness.registered(name)}
    except LookupError:
        done = set()
    assets = [a for a in store.dandi_assets(spec["dandiset"], spec["version"])
              if a[0].endswith(".nwb") and f"{Path(a[0]).stem}.npz" not in done]
    if "genotype" in spec:
        assets = [a for a in assets if store.dandi_genotype(spec["dandiset"], spec["version"], a[1]) == spec["genotype"]]
    reason = f"{spec['premises']}. {spec['citation']}. 표 {spec['tables']}, 시계열 {spec['series']}"

    def one(asset):
        path, asset_id, _ = asset
        try:
            store.extract(name, f"DANDI {spec['dandiset']} {spec['version']}", path, store.dandi_url(asset_id),
                          reason, spec["series"], spec["tables"])
            return f"등록 {path}"
        except KeyError as missing:
            return f"건너뜀 {path}: {missing}"

    with ThreadPoolExecutor(workers) as pool:
        for line in pool.map(one, assets):
            print(line, flush=True)


if __name__ == "__main__":
    fetch(sys.argv[1])
