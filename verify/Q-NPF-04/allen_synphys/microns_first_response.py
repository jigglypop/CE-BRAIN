"""판본을 명시한 53개 대상의 첫 고정 구간을 읽고 유효성을 확인한다."""
import json
from pathlib import Path
import h5py,numpy as np
import raw_metadata as raw
from population_reciprocity import ROOT,sha
from superficial_ee_eligibility import save

HERE=Path(__file__).resolve().parent


def main():
    identity=json.loads((HERE/'microns_scan_unit_decoding_result.json').read_text())
    targets=sorted(identity['targets'],key=lambda t:(t['field'],t['mask_id']))
    frames=1250
    save('microns_first_response_contract.json',dict(question='Can all fixed53 targets be read under the explicit v1412 coregistration plus v8 ScanUnit mapping?',
        selection='All53 predefined scan4/7 targets; first1250 frames, chosen before response values. No response-based exclusions.',
        endpoint='Finite count, variation and observed range per trace; no connectivity, correlation or causal test.',
        timing='Preserve NWB frame clock and per-unit ms_delay separately. No interpolation or assumed offset correction.',
        identity='Use v1412 registration for all53. Unit3151 uses mask601; retain historical disagreement with v343 mask598 in audit.',
        limits='GCaMP fluorescence in source unit n.a.; not spikes or deltaF/F. L0 acquisition/QC only.',code_sha256=sha(Path(__file__))))
    dest=ROOT/'data/external/microns_functional_nwb/scan_4_7_first1250.npz'
    meta=json.loads((HERE/'microns_first_scan_asset.json').read_text())
    raw.URL=next(u for u in meta['contentUrl'] if u.startswith('https://dandiarchive.s3.amazonaws.com/'))
    raw.CACHE=ROOT/'data/external/microns_functional_nwb/scan_4_7_ranges';raw.LIMIT=96*1024*1024
    if not dest.exists():
        values=np.empty((frames,len(targets)),dtype=np.float32)
        with raw.CachedRanges() as reader:
            with h5py.File(reader,'r') as f:
                for field in sorted({t['field'] for t in targets}):
                    indexes=[i for i,t in enumerate(targets) if t['field']==field]
                    cols=[targets[i]['mask_id']-1 for i in indexes]
                    series=f[f'processing/ophys/Fluorescence/RoiResponseSeries{field}']
                    values[:,indexes]=series['data'][:frames,cols]
                times=f['processing/ophys/Fluorescence/RoiResponseSeries2/timestamps'][:frames]
            print('NEW_RANGE_BYTES',reader.downloaded_this_session,flush=True)
        with dest.open('xb') as out:np.savez_compressed(out,values=values,frame_times=times,unit_ids=np.array([t['unit_id'] for t in targets]),ms_delay=np.array([t['ms_delay'] for t in targets]))
    data=np.load(dest);values=data['values'];assert values.shape==(frames,53)
    assert data['unit_ids'].tolist()==[t['unit_id'] for t in targets]
    summaries=[]
    for i,t in enumerate(targets):
        x=values[:,i];finite=x[np.isfinite(x)]
        summaries.append(dict(unit_id=t['unit_id'],field=t['field'],mask_id=t['mask_id'],finite=len(finite),minimum=float(finite.min()) if len(finite) else None,maximum=float(finite.max()) if len(finite) else None,std=float(finite.std(dtype=np.float64)) if len(finite) else None))
    save('microns_first_response_result.json',dict(shape=list(values.shape),time_start=float(data['frame_times'][0]),time_stop=float(data['frame_times'][-1]),
        all_finite=bool(np.isfinite(values).all()),nonconstant=sum(s['std'] is not None and s['std']>0 for s in summaries),summaries=summaries,
        artifact_sha256=sha(dest),claim_ceiling='L0 acquisition/QC only; no structural-functional association evaluated'))
    print('FIRST_RESPONSE',values.shape,'finite',bool(np.isfinite(values).all()))


if __name__=='__main__':main()
