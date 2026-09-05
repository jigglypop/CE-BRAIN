"""결과를 본 뒤 수행한 기술적 진단. 원 분석의 포함 기준이나 결과는 바꾸지 않는다."""
import json
import sqlite3
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
DB = HERE.parents[2] / "data/external/allen_synphys_r21/synphys_r2.1_small.sqlite"


def main():
    original = json.loads((HERE / "component_result.json").read_text(encoding="utf-8"))
    result = {"purpose": "Post-result descriptive audit only; original cohort/model/result unchanged",
              "quantile_levels": [0, .01, .5, .99, 1], "cohorts": []}
    with sqlite3.connect(DB.as_uri() + "?mode=ro", uri=True) as db:
        for cohort in original["cohorts"]:
            ids = cohort["synapse_ids"]
            query = ("SELECT s.psp_amplitude,s.psc_amplitude,i.input_resistance FROM synapse s "
                     "JOIN pair p ON p.id=s.pair_id JOIN intrinsic i ON i.cell_id=p.post_cell_id "
                     "WHERE s.id IN (" + ",".join("?" for _ in ids) + ")")
            values = abs(np.array(db.execute(query, ids).fetchall())) * [1e3, 1e12, 1e-6]
            result["cohorts"].append({"cohort": cohort["cohort"], "units": ["PSP_mV", "PSC_pA", "R_Mohm"],
                                      "quantiles": np.quantile(values, result["quantile_levels"], axis=0).tolist()})
    path = HERE / "post_result_diagnostic.json"
    if path.exists():
        assert result == json.loads(path.read_text(encoding="utf-8"))
        print("기존 진단 결과와 일치")
    else:
        with path.open("x", encoding="utf-8") as stream:
            json.dump(result, stream, ensure_ascii=False, indent=2, allow_nan=False)


if __name__ == "__main__":
    main()
