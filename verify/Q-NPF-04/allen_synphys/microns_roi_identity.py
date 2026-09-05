"""첫 스캔 ROI 참조와 실제 ID를 기능 대응표에 결박한다."""
import json
from pathlib import Path
import h5py
import numpy as np
import raw_metadata as raw
from population_reciprocity import ROOT,sha
from superficial_ee_eligibility import save

HERE=Path(__file__).resolve().parent
NAME='microns_roi_identity'


def main():
    joined=json.loads((HERE/'microns_coregistration_join_result.json').read_text(encoding='utf-8'))['analysis']['matches']
    targets=[r for r in joined if (r['session'],r['scan_idx'])==(4,7)]
    meta=json.loads((HERE/'microns_first_scan_asset.json').read_text(encoding='utf-8'))
    raw.URL=next(u for u in meta['contentUrl'] if u.startswith('https://dandiarchive.s3.amazonaws.com/'))
    raw.CACHE=ROOT/'data/external/microns_functional_nwb/scan_4_7_ranges';raw.LIMIT=48*1024*1024
    save(NAME+'_contract.json',dict(question='첫 스캔의 실제 ROI ID와 시간축을53개 구조 대상에 연결할 수 있는가?',
        rule='RoiResponseSeries rois의 table reference를 따라 id를 읽는다. unit_id와 직접 일치하는 후보만 기록. field는 번호 추정 없이 대응표 값과 imaging_plane 설명을 함께 보고한다.',
        scope='8개ROI id·index·시간축과 속성만 읽음. 반응값 제외. 누락/충돌 보존, 추가수집은 누적48MiB 이내. L0.',
        code_sha256=sha(Path(__file__)),join_sha256=sha(HERE/'microns_coregistration_join_result.json')))
    planes=[]; arrays={}
    with raw.CachedRanges() as reader:
        with h5py.File(reader,'r') as f:
            for name in f['processing/ophys/Fluorescence']:
                g=f['processing/ophys/Fluorescence'][name];roi=g['rois'];table=f[roi.attrs['table']]
                idx=np.asarray(roi[:],dtype=int);ids=np.asarray(table['id'][:],dtype=np.int64)
                assert np.all((idx>=0)&(idx<len(ids)))
                units=ids[idx];times=np.asarray(g['timestamps'][:],dtype=float)
                arrays[name+'_times']=times;arrays[name+'_units']=units
                image=table['imaging_plane']; desc=str(image['description'][()])
                hits=[dict(**r,column=int(i)) for r in targets for i in np.flatnonzero(units==r['unit_id'])]
                dt=np.diff(times)
                planes.append(dict(series=name,table_path=table.name,image_description=desc,
                    ids_count=len(units),unique_ids=len(set(units.tolist())),ids_min=int(units.min()),ids_max=int(units.max()),
                    unit=str(g['data'].attrs.get('unit','')),conversion=str(g['data'].attrs.get('conversion','')),offset=str(g['data'].attrs.get('offset','')),
                    series_description=str(g.attrs.get('description','')),data_shape=list(g['data'].shape),chunks=g['data'].chunks,
                    timestamps_unit=str(g['timestamps'].attrs.get('unit','')),time_count=len(times),time_finite=bool(np.isfinite(times).all()),
                    increasing=bool(np.all(dt>0)),start=float(times[0]),stop=float(times[-1]),median_dt=float(np.median(dt)),min_dt=float(dt.min()),max_dt=float(dt.max()),
                    hits=hits))
                print('ROI_IDENTITY_READ',name,len(hits),flush=True)
        new=reader.downloaded_this_session
        save(NAME+'_cache_snapshot.json',reader.manifest)
    dest=raw.CACHE/'roi_identity_arrays.npz'
    with dest.open('xb') as out:np.savez_compressed(out,**arrays)
    result=dict(targets=targets,planes=planes,new_bytes=new,array_path=dest.relative_to(ROOT).as_posix(),array_sha256=sha(dest))
    save(NAME+'_result.json',result)
    print(json.dumps([{k:v for k,v in p.items() if k!='hits'}|dict(hits=len(p['hits'])) for p in planes],indent=2))


if __name__=='__main__':main()
