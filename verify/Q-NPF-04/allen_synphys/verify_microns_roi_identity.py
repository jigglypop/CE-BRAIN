"""보유 ROI와 시각 배열로 직접 ID 연결의 부적합을 재검증한다."""
import json
import re
from pathlib import Path
import numpy as np
from population_reciprocity import ROOT,sha
from superficial_ee_eligibility import save

HERE=Path(__file__).resolve().parent


def main():
    result=json.loads((HERE/'microns_roi_identity_result.json').read_text(encoding='utf-8'))
    contract=json.loads((HERE/'microns_roi_identity_contract.json').read_text(encoding='utf-8'))
    assert sha(HERE/'microns_roi_identity.py')==contract['code_sha256']
    assert sha(ROOT/result['array_path'])==result['array_sha256']
    checks=[]
    with np.load(ROOT/result['array_path'],allow_pickle=False) as arrays:
        for p in result['planes']:
            units=arrays[p['series']+'_units'];t=arrays[p['series']+'_times']
            assert np.array_equal(units,np.arange(1,len(units)+1))
            assert np.isfinite(t).all() and np.all(np.diff(t)>0) and len(t)==40000
            assert float(np.median(np.diff(t)))==p['median_dt']
            field=int(re.search(r'field (\d+)',p['image_description']).group(1))
            candidates=[r for r in result['targets'] if r['unit_id'] in set(units.tolist())]
            assert len(candidates)==len(p['hits'])
            checks.append(dict(series=p['series'],field=field,numeric_id_candidates=len(candidates),
                candidates_with_correct_field=sum(r['field']==field for r in candidates)))
    save('microns_roi_identity_gate.json',dict(result_sha256=sha(HERE/'microns_roi_identity_result.json'),
        status='DIRECT_UNIT_ID_JOIN_REJECTED',checks=checks,
        required='explicit ScanUnit unit_id to field/mask_id map and NWB conversion identity provenance',
        time_checks='all8 arrays finite and strictly increasing; stored unit seconds, fluorescence unit n.a.',
        limits='No target fluorescence extracted; numeric coincidences are not matches.'))
    print('MICRONS_ROI_IDENTITY_VERIFIED',checks)


if __name__=='__main__':main()
