"""Read stored-TP time/scaling and property-wave labels, never waveform values."""
import json
import math
from pathlib import Path

import h5py
import numpy as np

from allen_joint_inventory import BASE,raw,sha

HERE=Path(__file__).resolve().parent
OUTPUT=HERE/'electrical_star_stored_tp_metadata_result.json'


def convert(value):
    if isinstance(value,np.ndarray):return convert(value.tolist())
    if isinstance(value,np.generic):return convert(value.item())
    if isinstance(value,bytes):
        try:return value.decode('utf8')
        except UnicodeDecodeError:return dict(encoding='hex',value=value.hex())
    if isinstance(value,(tuple,list)):return [convert(v) for v in value]
    if isinstance(value,float) and not math.isfinite(value):return dict(nonfinite=str(value))
    return value


def main():
    if OUTPUT.exists():raise FileExistsError(OUTPUT)
    code_hash=sha(Path(__file__))
    prior_path=HERE/'electrical_star_auxiliary_targeted_result.json'
    prior=json.loads(prior_path.read_text(encoding='utf8'))
    cache=BASE/'raw_ranges'/'1552517188.758'
    manifest=json.loads((cache/'manifest.json').read_text())
    initial=sum(b['bytes'] for b in manifest['blocks'].values())
    raw.URL,raw.CACHE,raw.LIMIT=prior['provenance']['remote']['url'],cache,initial+8*1024*1024
    names=['StoredTestPulses_'+str(i) for i in [0,1,10,100,1000,10000,10001,10002]]+['TPStorage']
    records=[]
    with raw.CachedRanges() as reader:
        assert reader.remote==prior['provenance']['remote']
        with h5py.File(reader,'r') as f:
            for name in names:
                path='/general/testpulse/ITC1600_Dev_0/'+name
                try:node=f[path]
                except KeyError:
                    records.append(dict(path=path,status='absent'));continue
                assert isinstance(node,h5py.Dataset)
                attrs={k:convert(v) for k,v in node.attrs.items()}
                row=dict(path=path,status='metadata_read',shape=list(node.shape),dtype=str(node.dtype),
                         chunks=node.chunks,compression=node.compression,attributes=attrs)
                records.append(row)
                print('TP_METADATA',name,row['shape'],'attr_keys',list(attrs),'new_bytes',reader.downloaded_this_session,flush=True)
        provenance=dict(remote=reader.remote,initial_cached_bytes=initial,new_download_bytes=reader.downloaded_this_session,blocks=reader.manifest['blocks'])
    assert sha(Path(__file__))==code_hash
    result=dict(code_sha256=code_hash,prior_sha256=sha(prior_path),raw_reader_sha256=sha(Path(raw.__file__)),
        scope='Nine known stored-TP/property datasets: attributes and shape only; no dataset body values',
        records=records,provenance=provenance,
        claim_ceiling='BIO_EVIDENCE_L0 recorded timestamp/scaling/field metadata, not calibrated current/voltage or intrinsic resistance')
    with OUTPUT.open('x',encoding='utf8') as stream:
        json.dump(result,stream,ensure_ascii=False,indent=2,allow_nan=False);stream.write('\n')
    print('DONE','new_bytes',provenance['new_download_bytes'],'sha256',sha(OUTPUT),flush=True)


if __name__=='__main__':main()
