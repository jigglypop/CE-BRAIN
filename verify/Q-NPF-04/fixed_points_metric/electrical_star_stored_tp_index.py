"""Index stored-TP times and channel/state properties; no TP waveform decoding."""
import json
from datetime import datetime
from pathlib import Path

import h5py
import numpy as np

from allen_joint_inventory import BASE,raw,sha
from electrical_star_stored_tp_metadata import convert

HERE=Path(__file__).resolve().parent
OUTPUT=HERE/'electrical_star_stored_tp_index_result.json'
EPOCH_SHIFT=2082844800
FIELDS=['HoldingCmd_VC','HoldingCmd_IC','TimeStampSinceIgorEpochUTC','ADC','DAC','Headstage','ClampMode','ValidState']


def main():
    if OUTPUT.exists():raise FileExistsError(OUTPUT)
    code_hash=sha(Path(__file__))
    metadata_path=HERE/'electrical_star_stored_tp_metadata_result.json'
    metadata=json.loads(metadata_path.read_text(encoding='utf8'))
    calibration_path=HERE/'electrical_star_tp_calibration_result.json'
    calibration=json.loads(calibration_path.read_text(encoding='utf8'))
    property_meta=next(r for r in metadata['records'] if r['path'].endswith('/TPStorage'))
    labels=[row[2] for row in property_meta['attributes']['IGORWaveDimensionLabels'][1:]]
    assert len(labels)==property_meta['shape'][2] and len(labels)==len(set(labels))
    indices=sorted(labels.index(field) for field in FIELDS)
    names=[labels[i] for i in indices]
    cache=BASE/'raw_ranges'/'1552517188.758'
    manifest=json.loads((cache/'manifest.json').read_text())
    initial=sum(b['bytes'] for b in manifest['blocks'].values())
    raw.URL,raw.CACHE,raw.LIMIT=metadata['provenance']['remote']['url'],cache,initial+16*1024*1024
    with raw.CachedRanges() as reader:
        assert reader.remote==metadata['provenance']['remote']
        with h5py.File(reader,'r') as f:
            # Excludes PeakResistance, SteadyStateResistance, Baseline and slope.
            values=np.asarray(f[property_meta['path']][:,:,indices],float)
        provenance=dict(remote=reader.remote,initial_cached_bytes=initial,new_download_bytes=reader.downloaded_this_session,blocks=reader.manifest['blocks'])
    utc=values[:,:,names.index('TimeStampSinceIgorEpochUTC')]-EPOCH_SHIFT
    earliest=datetime.fromisoformat('2019-03-13T22:45:35.431+00:00').timestamp()-60
    valid=np.isfinite(utc)&(utc>=earliest)&(utc<earliest+24*3600)
    row_indices=np.flatnonzero(valid.any(axis=1))
    times=np.nanmedian(np.where(valid[row_indices],utc[row_indices],np.nan),axis=1)
    row_time=dict(zip(row_indices.tolist(),times.tolist()))
    def snapshot(row):
        channel_times=utc[row][valid[row]]
        return dict(row=int(row),median_utc_unix_s=row_time[int(row)],
            timestamp_span_s=float(np.ptp(channel_times)),fields={name:convert(values[row,:,j]) for j,name in enumerate(names)})
    def nearest(t):
        index=int(np.argmin(np.abs(times-t)));row=int(row_indices[index])
        return dict(candidate=snapshot(row),candidate_time_minus_target_s=float(times[index]-t))
    wave_matches=[]
    for wave in metadata['records']:
        if '/StoredTestPulses_' not in wave['path']:continue
        stamp=wave['attributes']['IGORWaveNote'].split('TimeStamp: ',1)[1]
        target=datetime.fromisoformat(stamp.replace('Z','+00:00')).timestamp()
        number=int(wave['path'].rsplit('_',1)[1])
        wave_matches.append(dict(waveform_path=wave['path'],waveform_note_utc=stamp,
            same_number_row_time_minus_waveform_s=row_time[number]-target if number in row_time else None,
            **nearest(target)))
    notebook_matches=[]
    for match in calibration['matched_sweeps']:
        start=datetime.fromisoformat(match['nwb_utc']).timestamp()
        target=start+match['tp_time_minus_sweep_start_s']
        notebook_matches.append(dict(sweep=match['sweep'],notebook_measurement_row=match['nearest_tp_measurement_row'],
            target_tp_utc_unix_s=target,**nearest(target)))
    distinct={}
    for name in ['ADC','DAC','Headstage','ClampMode','ValidState']:
        a=values[row_indices,:,names.index(name)]
        distinct[name]=[np.unique(a[:,col][np.isfinite(a[:,col])]).tolist() for col in range(8)]
    assert sha(Path(__file__))==code_hash
    result=dict(code_sha256=code_hash,metadata_sha256=sha(metadata_path),calibration_sha256=sha(calibration_path),
        raw_reader_sha256=sha(Path(raw.__file__)),conversion_helper_sha256=sha(HERE/'electrical_star_stored_tp_metadata.py'),
        scope='Selected TPStorage timestamp, holding, ADC/DAC/headstage/mode/valid-state property columns; no resistance, baseline, or waveform datasets',
        fields_selected=names,source_labels=labels,provenance=provenance,
        summary=dict(time_index_rows=len(row_indices),first_index=int(row_indices[0]),last_index=int(row_indices[-1]),
            first_utc=datetime.fromtimestamp(times[0],tz=datetime.fromisoformat('2000-01-01T00:00:00+00:00').tzinfo).isoformat(),
            last_utc=datetime.fromtimestamp(times[-1],tz=datetime.fromisoformat('2000-01-01T00:00:00+00:00').tzinfo).isoformat(),
            row_time_monotonic=bool(np.all(np.diff(times)>=0))),
        time_index=[dict(row=int(row),median_utc_unix_s=float(t)) for row,t in zip(row_indices,times)],
        distinct_finite_field_values_by_storage_column=distinct,waveform_attribute_matches=wave_matches,
        notebook_tp_matches=notebook_matches,
        limitations=['Temporal nearest matches are candidates, not proven identical TP events',
            'Storage axis has eight headstage slots whereas waveform columns can be packed seven; channel order is not assumed',
            'Holding command values are stored as raw numbers; their physical units require cross-checks',
            'Median timestamp is only a search index; individual selected-row timestamp span must be checked'],
        claim_ceiling='BIO_EVIDENCE_L0 time and channel-state association; no intrinsic circuit or metric identified')
    with OUTPUT.open('x',encoding='utf8') as stream:
        json.dump(result,stream,ensure_ascii=False,indent=2,allow_nan=False);stream.write('\n')
    print('DONE',json.dumps(result['summary']),'new_bytes',provenance['new_download_bytes'],'sha256',sha(OUTPUT),flush=True)
    for row in notebook_matches:
        print('NB_TP_MATCH',row['sweep'],row['candidate']['row'],row['candidate_time_minus_target_s'],flush=True)


if __name__=='__main__':main()
