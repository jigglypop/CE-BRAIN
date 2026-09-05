"""Read ten preselected stored TP waveforms and their same-number properties.

Keep physical units and packed column mapping as hypotheses until checked.
The simple feature estimator uses nominal TP timing and is not 2019 MIES.
"""
import json
from datetime import datetime
from pathlib import Path

import h5py
import numpy as np

from allen_joint_inventory import BASE,raw,sha
from electrical_star_stored_tp_metadata import convert

HERE=Path(__file__).resolve().parent
OUTPUT=HERE/'electrical_star_stored_tp_waveforms_result.json'


def raw_features(values,dt_ms):
    values=np.asarray(values,float)
    def interval(lo,hi):return values[round(lo/dt_ms):round(hi/dt_ms)]
    baseline=float(interval(5.9,7.4).mean())
    lo,hi=round(7.52/dt_ms),round(7.77/dt_ms)
    peak_index=lo+int(np.argmin(values[lo:hi]))
    peak=float(values[peak_index-1:peak_index+2].mean())
    late=float(interval(15.9,17.4).mean())
    return dict(baseline_raw=baseline,whole_pre7p5ms_mean_raw=float(interval(0,7.5).mean()),
        peak_raw=peak,peak_delta_raw=peak-baseline,late_raw=late,late_delta_raw=late-baseline,
        peak_time_ms=peak_index*dt_ms,
        all_time_min_raw=float(values.min()),all_time_max_raw=float(values.max()))


def main():
    if OUTPUT.exists():raise FileExistsError(OUTPUT)
    code_hash=sha(Path(__file__))
    index_path=HERE/'electrical_star_stored_tp_index_result.json'
    index=json.loads(index_path.read_text(encoding='utf8'))
    metadata_path=HERE/'electrical_star_stored_tp_metadata_result.json'
    metadata=json.loads(metadata_path.read_text(encoding='utf8'))
    calibration_path=HERE/'electrical_star_tp_calibration_result.json'
    calibration=json.loads(calibration_path.read_text(encoding='utf8'))
    properties=next(r for r in metadata['records'] if r['path'].endswith('/TPStorage'))
    labels=[row[2] for row in properties['attributes']['IGORWaveDimensionLabels'][1:]]
    assert len(labels)==22
    chosen=index['notebook_tp_matches']
    cache=BASE/'raw_ranges'/'1552517188.758'
    manifest=json.loads((cache/'manifest.json').read_text())
    initial=sum(b['bytes'] for b in manifest['blocks'].values())
    raw.URL,raw.CACHE,raw.LIMIT=index['provenance']['remote']['url'],cache,initial+8*1024*1024
    records=[]
    with raw.CachedRanges() as reader:
        assert reader.remote==index['provenance']['remote']
        with h5py.File(reader,'r') as f:
            prop=f[properties['path']]
            for selected in chosen:
                number=selected['candidate']['row'];sweep=selected['sweep']
                path='/general/testpulse/ITC1600_Dev_0/StoredTestPulses_'+str(number)
                node=f[path]
                attrs={k:convert(v) for k,v in node.attrs.items()}
                values=np.asarray(node[()],float)
                assert values.ndim==2 and values.shape[0]==1250 and np.isfinite(values).all()
                raw_props=np.asarray(prop[number:number+1,:,:],float)[0]
                assert raw_props.shape==(8,22)
                field_values={name:convert(raw_props[:,i]) for i,name in enumerate(labels)}
                valid=raw_props[:,labels.index('ValidState')]==1
                heads=raw_props[:,labels.index('Headstage')]
                active_columns=np.flatnonzero(valid&np.isfinite(heads))
                headstage_candidates=[int(heads[c]) for c in active_columns]
                dt=attrs['IGORWaveScaling'][1][0]
                assert attrs['IGORWaveUnits'][1]=='ms' and abs(dt-.02)<1e-10
                stamp=attrs['IGORWaveNote'].split('TimeStamp: ',1)[1]
                wave_time=datetime.fromisoformat(stamp.replace('Z','+00:00')).timestamp()
                features=[raw_features(values[:,c],dt) for c in range(values.shape[1])]
                notebook=next(m for m in calibration['matched_sweeps'] if m['sweep']==sweep)
                records.append(dict(sweep=sweep,property_row=number,waveform_path=path,attributes=attrs,
                    waveform_shape=list(values.shape),waveform_raw=values.tolist(),features_by_waveform_column=features,
                    property_fields=field_values,valid_property_axis_columns=active_columns.tolist(),
                    sorted_valid_headstage_mapping_hypothesis=headstage_candidates,
                    mapping_column_count_agrees=len(headstage_candidates)==values.shape[1],
                    property_time_minus_waveform_note_s=selected['candidate']['median_utc_unix_s']-wave_time,
                    waveform_time_minus_notebook_tp_s=wave_time-selected['target_tp_utc_unix_s'],
                    notebook_stimulus=notebook['stimulus'],notebook_cells=notebook['cells']))
                print('STORED_TP',sweep,number,'shape',list(values.shape),'first_baseline_raw',features[0]['baseline_raw'],
                    'new_bytes',reader.downloaded_this_session,flush=True)
        provenance=dict(remote=reader.remote,initial_cached_bytes=initial,new_download_bytes=reader.downloaded_this_session,blocks=reader.manifest['blocks'])
    assert sha(Path(__file__))==code_hash
    result=dict(code_sha256=code_hash,index_sha256=sha(index_path),metadata_sha256=sha(metadata_path),
        calibration_sha256=sha(calibration_path),raw_reader_sha256=sha(Path(raw.__file__)),
        conversion_helper_sha256=sha(HERE/'electrical_star_stored_tp_metadata.py'),provenance=provenance,
        scope='Ten preselected StoredTestPulses and same-number TPStorage full property rows, chosen from previous timestamp index',
        stage='Posthoc measurement association and unit/mapping assessment; no intrinsic circuit fitting',
        feature_definition='Raw numerical units; baseline5.9..7.4ms, minimum7.52..7.77ms averaged3points, late15.9..17.4ms. Nominal pulse7.5..17.5ms; not a replication of historical MIES.',
        records=records,limitations=['Physical waveform units are not declared by its value-unit attribute',
            'Sorted valid headstage order is recorded as a hypothesis, not assumed true solely from seven columns',
            'Time proximity alone does not prove identity with a lab notebook TP measurement',
            'Measured TP indices do not identify true Rs, reference resistance, junctions, or a spatial metric'],
        claim_ceiling='BIO_EVIDENCE_L1 stored TP waveform observations; physical-unit and channel association require cross-checks')
    with OUTPUT.open('x',encoding='utf8') as stream:
        json.dump(result,stream,ensure_ascii=False,indent=2,allow_nan=False);stream.write('\n')
    print('DONE','new_bytes',provenance['new_download_bytes'],'sha256',sha(OUTPUT),flush=True)


if __name__=='__main__':main()
