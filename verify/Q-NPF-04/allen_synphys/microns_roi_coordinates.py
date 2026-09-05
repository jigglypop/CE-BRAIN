"""NWB에 저장된 EM 좌표로 대상 세포의 ROI 후보를 확인한다."""
import csv,json,re
from pathlib import Path
import h5py
import numpy as np
import raw_metadata as raw
from population_reciprocity import ROOT,sha
from superficial_ee_eligibility import save

HERE=Path(__file__).resolve().parent
NAME='microns_roi_coordinates'


def main():
    source=ROOT/'data/external/microns_nwb_conversion_source/ophys.py'
    identity=json.loads((HERE/'microns_roi_identity_result.json').read_text(encoding='utf-8'))
    with (ROOT/'data/external/microns_v1718_cosyne/v1718_cell_info.csv').open(encoding='utf-8',newline='') as f:
        cells={int(c['id']):c for c in csv.DictReader(f)}
    meta=json.loads((HERE/'microns_first_scan_asset.json').read_text(encoding='utf-8'))
    raw.URL=next(u for u in meta['contentUrl'] if u.startswith('https://dandiarchive.s3.amazonaws.com/'))
    raw.CACHE=ROOT/'data/external/microns_functional_nwb/scan_4_7_ranges';raw.LIMIT=48*1024*1024
    save(NAME+'_contract.json',dict(question='첫 스캔53대상을 NWB 저장 EM좌표와 field로 유일하게 ROI에 대응할 수 있는가?',
        method='같은field에서 세 정수 EM좌표의 완전 일치. root float 비교 금지. 동일위치 후보0/복수는 보존. 변환 소스는 mask_id 순서로 ROI/trace 저장.',
        limits='NWB 저장 대응 열의 정확성에 조건부이며 현미경 원영상 독립 재검증 아님. 변환 코드 ScanUnit fetch에는 명시 order_by가 없어 원테이블 행순서 보장은 후속 확인 필요. L0 후보 대응.',
        source_sha256=sha(source),identity_sha256=sha(HERE/'microns_roi_identity_result.json'),code_sha256=sha(Path(__file__))))
    arrays={};matches=[];planes=[]
    with raw.CachedRanges() as reader:
        with h5py.File(reader,'r') as f:
            for p in identity['planes']:
                field=int(re.search(r'field (\d+)',p['image_description']).group(1))
                t=f[p['table_path']]
                if 'pt_x_position' not in t:continue
                ids=t['id'][:];coords=np.column_stack([t['pt_'+k+'_position'][:] for k in 'xyz'])
                roi=f['processing/ophys/Fluorescence/'+p['series']+'/rois'][:]
                arrays[p['series']+'_coordinates']=coords;arrays[p['series']+'_mask_ids']=ids;arrays[p['series']+'_roi_indices']=roi
                planes.append(dict(field=field,rows=len(ids),coordinate_shape=list(coords.shape),finite_rows=int(np.isfinite(coords).all(axis=1).sum())))
                for target in identity['targets']:
                    if target['field']!=field:continue
                    cell=cells[target['nucleus_id']];position=np.array([int(cell['pt_position_'+k]) for k in 'xyz'])
                    rows=np.flatnonzero(np.all(coords==position,axis=1))
                    candidates=[dict(table_row=int(i),mask_id=int(ids[i]),response_columns=[int(j) for j in np.flatnonzero(roi==i)]) for i in rows]
                    matches.append(dict(**target,series=p['series'],position=position.tolist(),candidates=candidates))
        new=reader.downloaded_this_session
        save(NAME+'_cache_snapshot.json',reader.manifest)
    dest=raw.CACHE/'roi_coordinate_arrays.npz'
    with dest.open('xb') as out:np.savez_compressed(out,**arrays)
    summary=dict(targets=len(identity['targets']),evaluated=len(matches),unique=sum(len(m['candidates'])==1 and len(m['candidates'][0]['response_columns'])==1 for m in matches),
        absent=sum(not m['candidates'] for m in matches),ambiguous=sum(len(m['candidates'])>1 for m in matches))
    save(NAME+'_result.json',dict(summary=summary,planes=planes,matches=matches,new_bytes=new,array_path=dest.relative_to(ROOT).as_posix(),array_sha256=sha(dest)))
    print(json.dumps(dict(summary=summary,planes=planes,new_bytes=new),indent=2))


if __name__=='__main__':main()
