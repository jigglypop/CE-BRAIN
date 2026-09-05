"""Extract sparse recorded MIES notebook values, preserving rows and columns."""
import json
from collections import Counter
from pathlib import Path

import h5py
import numpy as np

from allen_joint_inventory import BASE, raw, sha, text

HERE=Path(__file__).resolve().parent
OUTPUT=HERE/'electrical_star_notebook_values_result.json'


def main():
    if OUTPUT.exists():raise FileExistsError(OUTPUT)
    inventory_path=HERE/'electrical_star_notebook_inventory_result.json'
    inventory=json.loads(inventory_path.read_text(encoding='utf8'))
    protocol=json.loads((HERE/'electrical_star_protocol_result.json').read_text(encoding='utf8'))
    cache=BASE/'raw_ranges'/protocol['selection']['ext_id']
    manifest=json.loads((cache/'manifest.json').read_text())
    initial=sum(b['bytes'] for b in manifest['blocks'].values())
    raw.URL,raw.CACHE,raw.LIMIT=protocol['remote']['url'],cache,initial+32*1024*1024
    assert len(inventory['groups'])==1
    group_path=inventory['groups'][0]['path']
    with raw.CachedRanges() as reader:
        assert reader.remote==protocol['remote']
        with h5py.File(reader,'r') as f:
            nb=f[group_path]
            numerical_keys=np.asarray(nb['numericalKeys'])
            keys=[text(k) for k in numerical_keys[0]]
            values=np.asarray(nb['numericalValues'])
            assert values.shape[1:]==(len(keys),9)
            records=[]
            for index,row in enumerate(values):
                fields={key:[float(v) if np.isfinite(v) else None for v in row[k]]
                        for k,key in enumerate(keys) if np.isfinite(row[k]).any()}
                if fields:records.append(dict(row=index,fields=fields))
            print('NUMERIC_RECORDS',len(records),'shape',values.shape,flush=True)
            text_keys=[text(k) for k in nb['textualKeys'][0]]
            selected=[key for key in text_keys if key in ['SweepNum','TimeStamp','TimeStampSinceIgorEpochUTC',
                'EntrySourceType','High precision sweep start','MIES version','Igor Pro version','OperatingModeString','AD unit','DA unit']]
            # Selection in the field dimension; no stimulus notes or acquisition arrays decoded.
            indices=sorted(text_keys.index(key) for key in selected)
            text_values=np.asarray(nb['textualValues'][:,indices,:])
            textual=[]
            for index,row in enumerate(text_values):
                fields={text_keys[k]:[text(v) for v in row[j]] for j,k in enumerate(indices) if any(text(v) for v in row[j])}
                if fields:textual.append(dict(row=index,fields=fields))
            root_times={}
            for key in ['session_start_time','timestamps_reference_time','file_create_date']:
                if key in f:
                    root_times[key]=[text(v) for v in np.asarray(f[key]).ravel()]
            key_metadata=[[text(v) for v in row] for row in numerical_keys]
        provenance=dict(remote=reader.remote,initial_cached_bytes=initial,new_download_bytes=reader.downloaded_this_session,blocks=reader.manifest['blocks'])
    result=dict(code_sha256=sha(Path(__file__)),inventory_sha256=sha(inventory_path),raw_reader_sha256=sha(Path(raw.__file__)),
        scope='Sparse numeric lab notebook and selected text fields, preserving original row/channel/global columns; no ADC data',
        group_path=group_path,numerical_key_metadata=key_metadata,numerical_shape=list(values.shape),
        numerical_records=records,textual_fields_selected=[text_keys[k] for k in indices],textual_records=textual,
        root_times=root_times,provenance=provenance,claim_ceiling='Recorded instrument measurements and settings, not calibrated intrinsic brain parameters')
    with OUTPUT.open('x',encoding='utf8') as stream:
        json.dump(result,stream,ensure_ascii=False,indent=2,allow_nan=False);stream.write('\n')
    source=Counter(str(r['fields'].get('EntrySourceType',[None])[0]) for r in records)
    peaks=[r for r in records if 'TP Peak Resistance' in r['fields']]
    versions=sorted({v for r in textual for v in r['fields'].get('MIES version',[]) if v})
    print('DONE',json.dumps(dict(source_counts=dict(source),peak_rows=len(peaks),versions=versions,root_times=root_times,
        new_bytes=provenance['new_download_bytes'],sha256=sha(OUTPUT))),flush=True)


if __name__=='__main__':main()
