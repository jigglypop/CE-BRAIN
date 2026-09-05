"""과거 NWB 등록과 후속 수동 등록의 차이를 원자료로 확인한다."""
import csv,gzip,json
from collections import Counter
from pathlib import Path
import numpy as np
from population_reciprocity import ROOT,sha
from superficial_ee_eligibility import save

HERE=Path(__file__).resolve().parent


def table(directory,stem):
    with (directory/(stem+'_merged_header.csv')).open() as f:header=[r[0] for r in csv.reader(f) if r]
    with gzip.open(directory/(stem+'_merged.csv.gz'),'rt') as f:return [dict(zip(header,r)) for r in csv.reader(f)]


def main():
    old=table(ROOT/'data/external/microns_coregistration_v343','functional_coreg')
    current=table(ROOT/'data/external/microns_coregistration_v1412','coregistration_manual_v4')
    with (HERE/'microns_scan_unit_scan_4_7.csv').open() as f:units={int(r['unit_id']):r for r in csv.DictReader(f)}
    arrays=np.load(ROOT/'data/external/microns_functional_nwb/scan_4_7_ranges/roi_coordinate_arrays.npz')
    counts=Counter();mismatches=[]
    for r in current:
        if (int(r['session']),int(r['scan_idx']))!=(4,7):continue
        field=int(r['field']);key=f'RoiResponseSeries{field}_coordinates'
        if key not in arrays:counts['field_unavailable']+=1;continue
        pos=[int(r['pt_position_'+x]) for x in 'xyz']
        hits=np.flatnonzero((arrays[key]==pos).all(axis=1))
        if len(hits)!=1:counts['absent_or_ambiguous']+=1;continue
        unit=units[int(r['unit_id'])]
        mask=int(arrays[f'RoiResponseSeries{field}_mask_ids'][hits[0]])
        if mask==int(unit['mask_id']):counts['equal']+=1
        else:
            counts['different']+=1
            prior=[o for o in old if (int(o['session']),int(o['scan_idx']))==(4,7) and [int(o['pt_position_'+x]) for x in 'xyz']==pos]
            mismatches.append(dict(position=pos,current=r,current_mask_id=int(unit['mask_id']),nwb_mask_id=mask,prior=prior))
    assert counts['equal']==313 and counts['different']==1
    assert len(mismatches[0]['prior'])==1
    assert int(mismatches[0]['prior'][0]['id'])==7657
    assert int(mismatches[0]['prior'][0]['unit_id'])==3148
    assert int(mismatches[0]['current']['unit_id'])==3151
    assert int(units[3148]['mask_id'])==598 and int(units[3151]['mask_id'])==601
    save('microns_registration_versions_result.json',dict(counts=dict(counts),mismatches=mismatches,
        status='HISTORICAL_REGISTRATION_DIFFERENCE_IDENTIFIED',
        limits='Identifies different assignments in two official snapshots. Does not independently adjudicate which optical ROI is biologically correct. Current analyses must explicitly use v1412 mapping; historical NWB annotations remain unchanged.',
        code_sha256=sha(Path(__file__)),old_sha256=sha(ROOT/'data/external/microns_coregistration_v343/functional_coreg_merged.csv.gz')))
    print(dict(counts))


if __name__=='__main__':main()
