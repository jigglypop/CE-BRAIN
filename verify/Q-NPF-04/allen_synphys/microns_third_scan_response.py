"""고정 스캔 순서의 다음 기록에서 mask·시간과 첫 반응을 확인한다."""
import json,csv
from collections import Counter
from pathlib import Path
import h5py,numpy as np
import raw_metadata as raw
from microns_repeat_response import prefetch
from microns_all_scan_targets import decode
from population_reciprocity import ROOT,sha
from superficial_ee_eligibility import save

HERE=Path(__file__).resolve().parent


def main():
    all_targets=json.loads((HERE/'microns_all_scan_targets_result.json').read_text())['targets']
    targets=sorted([t for t in all_targets if (t['session'],t['scan_idx'])==(5,6)],key=lambda t:(t['field'],t['mask_id']))
    assert len(targets)==len({t['nucleus_id'] for t in targets})==39
    save('microns_third_scan_contract.json',dict(question='Open the next lexicographically ordered scan with registered structural targets and verify the same mask-domain/time/first1250-frame input checks.',
        selection='session5 scan6; all39 targets, no response selection; zero nucleus overlap with first scan, same mouse17797.',
        limits='Current v1412 registration plus v8 ScanUnit. Historical NWB annotations audited separately. Input acquisition not hypothesis confirmation.',code_sha256=sha(Path(__file__))))
    mapping=decode();meta=json.loads((HERE/'microns_scan_5_6_asset.json').read_text())
    raw.URL=next(u for u in meta['contentUrl'] if u.startswith('https://dandiarchive.s3.amazonaws.com/'))
    raw.CACHE=ROOT/'data/external/microns_functional_nwb/scan_5_6_ranges';raw.LIMIT=64*1024*1024
    with (ROOT/'data/external/microns_v1718_cosyne/v1718_cell_info.csv').open(encoding='utf-8',newline='') as f:cells={int(r['id']):r for r in csv.DictReader(f)}
    fields=[];coordinates=[];spans=set();values=np.empty((1250,39));times=None;trial_counts={}
    with raw.CachedRanges() as reader:
        with h5py.File(reader,'r') as f:
            for field in sorted({t['field'] for t in targets}):
                series=f[f'processing/ophys/Fluorescence/RoiResponseSeries{field}'];ds=series['data']
                table=f[series['rois'].attrs['table']];ids=table['id'][:];roi=series['rois'][:]
                expected=sorted(r['mask_id'] for r in mapping.values() if (r['session'],r['scan_idx'],r['field'])==(5,6,field))
                assert ids.tolist()==expected and roi.tolist()==list(range(len(ids))) and ds.shape[1]==len(ids)
                t=series['timestamps'][:1250];assert np.isfinite(t).all() and (np.diff(t)>0).all()
                if times is None:times=t
                else:assert np.array_equal(times,t)
                fields.append(dict(field=field,shape=list(ds.shape),ids=len(ids),unit=str(ds.attrs.get('unit','')),mask_domain_match=True))
                if all('pt_'+a+'_position' in table for a in 'xyz'):
                    xyz=np.column_stack([table['pt_'+a+'_position'][:] for a in 'xyz'])
                    for target in targets:
                        if target['field']!=field:continue
                        actual=xyz[target['mask_id']-1];cell=cells[target['nucleus_id']];expected_pos=[int(cell['pt_position_'+a]) for a in 'xyz']
                        coordinates.append(dict(unit_id=target['unit_id'],field=field,mask_id=target['mask_id'],finite=bool(np.isfinite(actual).all()),equal=bool(np.array_equal(actual,expected_pos))))
                ch=ds.chunks;cols={int((t['mask_id']-1)//ch[1]*ch[1]) for t in targets if t['field']==field}
                for row in range(0,1250,ch[0]):
                    for col in cols:
                        info=ds.id.get_chunk_info_by_coord((row,col));spans.add((int(info.byte_offset),int(info.size)))
            for kind in ('Clip','Monet2','Trippy'):
                g=f['intervals/'+kind];hashes=g['condition_hash'][:];trial_counts[kind]=dict(trials=len(hashes),repeat_counts=dict(Counter(Counter(hashes.tolist()).values())))
            prefetch(reader,spans)
            for field in sorted({t['field'] for t in targets}):
                indices=[i for i,t in enumerate(targets) if t['field']==field];cols=[targets[i]['mask_id']-1 for i in indices]
                values[:,indices]=f[f'processing/ophys/Fluorescence/RoiResponseSeries{field}/data'][:1250,cols]
    output=ROOT/'data/external/microns_functional_nwb/scan_5_6_first1250.npz'
    if not output.exists():
        with output.open('xb') as f:np.savez_compressed(f,values=values,frame_times=times,unit_ids=np.array([t['unit_id'] for t in targets]),ms_delay=np.array([t['ms_delay'] for t in targets]))
    else:assert np.array_equal(np.load(output)['values'],values,equal_nan=True)
    save('microns_third_scan_result.json',dict(targets=targets,fields=fields,coordinates=coordinates,trial_counts=trial_counts,shape=list(values.shape),all_finite=bool(np.isfinite(values).all()),nonconstant=int((np.std(values,axis=0)>0).sum()),time_start=float(times[0]),time_stop=float(times[-1]),artifact_sha256=sha(output),limits='Different cells in same mouse; first-segment QC only; full response and historical registrations not globally validated.'))
    print('NEXT_SCAN',values.shape,'finite',bool(np.isfinite(values).all()),'coordinates',Counter('equal' if c['equal'] else 'different' if c['finite'] else 'missing' for c in coordinates))


if __name__=='__main__':main()
