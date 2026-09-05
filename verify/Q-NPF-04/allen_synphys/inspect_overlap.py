"""반응값을 출력하지 않고 동일 세포 결합·결측·출처만 확인한다."""
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
DB = ROOT / "data/external/allen_synphys_r21/synphys_r2.1_small.sqlite"
JOIN = """FROM synapse s JOIN pair p ON p.id=s.pair_id
 JOIN cell post ON post.id=p.post_cell_id
 JOIN cell pre ON pre.id=p.pre_cell_id
 JOIN experiment e ON e.id=p.experiment_id
 JOIN slice sl ON sl.id=e.slice_id
 LEFT JOIN intrinsic i ON i.cell_id=post.id"""


def main():
    with sqlite3.connect(DB.as_uri() + "?mode=ro", uri=True) as db:
        result = {"metadata": db.execute("SELECT meta FROM metadata").fetchall(),
                  "integrity": db.execute("PRAGMA quick_check").fetchone()[0],
                  "duplicate_intrinsic_cells": db.execute("SELECT count(*) FROM (SELECT cell_id FROM intrinsic GROUP BY cell_id HAVING count(*)>1)").fetchone()[0],
                  "duplicate_synapse_pairs": db.execute("SELECT count(*) FROM (SELECT pair_id FROM synapse GROUP BY pair_id HAVING count(*)>1)").fetchone()[0],
                  "identity_mismatches": db.execute("SELECT count(*) " + JOIN + " WHERE post.experiment_id!=p.experiment_id OR pre.experiment_id!=p.experiment_id").fetchone()[0]}
        result["overlap"] = [dict(zip(
            ["species", "region", "type", "synapses", "psp_present", "psc_present", "resistance_present", "joint_present", "joint_slices"], row))
            for row in db.execute("""SELECT sl.species,e.target_region,s.synapse_type,count(*),
            sum(s.psp_amplitude IS NOT NULL),sum(s.psc_amplitude IS NOT NULL),
            sum(i.input_resistance IS NOT NULL),
            sum(s.psp_amplitude IS NOT NULL AND s.psc_amplitude IS NOT NULL AND i.input_resistance IS NOT NULL),
            count(DISTINCT CASE WHEN s.psp_amplitude IS NOT NULL AND s.psc_amplitude IS NOT NULL AND i.input_resistance IS NOT NULL THEN sl.id END)
            """ + JOIN + " GROUP BY sl.species,e.target_region,s.synapse_type")]
        result["slice_meta_keys"] = sorted({key for (raw,) in db.execute("SELECT meta FROM slice WHERE meta IS NOT NULL") for key in (json.loads(raw or '{}') or {})})
    (HERE / "overlap_receipt.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
