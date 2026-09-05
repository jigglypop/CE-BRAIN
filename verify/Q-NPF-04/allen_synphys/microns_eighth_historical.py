"""세 번째 스캔의 NWB 좌표를 해당 과거 등록판과 대조한다."""
import json
from pathlib import Path
import h5py
import numpy as np
import raw_metadata as raw
from population_reciprocity import ROOT,sha
from microns_registration_versions import table
from superficial_ee_eligibility import save

HERE=Path(__file__).resolve().parent


def main():
    targets=json.loads((HERE/'microns_eighth_scan_result.json').read_text())['targets']
    old=table(ROOT/'data/external/microns_coregistration_v343','functional_coreg')
    old=[r for r in old if (int(r['session']),int(r['scan_idx']))==(6,7)]
    raw.URL=next(u for u in json.loads((HERE/'microns_scan_6_7_asset.json').read_text())['contentUrl'] if u.startswith('https://dandiarchive.s3.amazonaws.com/'))
    raw.CACHE=ROOT/'data/external/microns_functional_nwb/scan_6_7_ranges';raw.LIMIT=160*1024*1024
    rows=[]
    with raw.CachedRanges() as reader:
        with h5py.File(reader,'r') as f:
            for t in targets:
                series=f[f"processing/ophys/Fluorescence/RoiResponseSeries{t['field']}"]
                tab=f[series['rois'].attrs['table']]
                pos=np.array([tab['pt_'+a+'_position'][t['mask_id']-1] for a in 'xyz'])
                prior=[r for r in old if int(r['unit_id'])==t['unit_id']]
                matches=[r for r in prior if np.array_equal(pos,[int(r['pt_position_'+a]) for a in 'xyz'])]
                rows.append(dict(unit_id=t['unit_id'],nwb_finite=bool(np.isfinite(pos).all()),old_unit_rows=len(prior),old_coordinate_matches=len(matches)))
    save('microns_eighth_historical_result.json',dict(rows=rows,code_sha256=sha(Path(__file__)),old_sha256=sha(ROOT/'data/external/microns_coregistration_v343/functional_coreg_merged.csv.gz'),limits='Historical provenance check only; does not adjudicate current biological identity or replace v1412 assignment.'))
    from collections import Counter
    print(Counter((r['nwb_finite'],r['old_unit_rows'],r['old_coordinate_matches']) for r in rows))


if __name__=='__main__':main()
