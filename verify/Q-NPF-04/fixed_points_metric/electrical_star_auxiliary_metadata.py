"""Inventory auxiliary TP/stimulus dataset structure, without reading values."""
import json
from pathlib import Path

import h5py
import numpy as np

from allen_joint_inventory import BASE, raw, sha

HERE=Path(__file__).resolve().parent
OUTPUT=HERE/'electrical_star_auxiliary_metadata_result.json'


def main():
    if OUTPUT.exists():raise FileExistsError(OUTPUT)
    code_hash=sha(Path(__file__))
    prior_path=HERE/'electrical_star_all_protocols_result.json'
    prior=json.loads(prior_path.read_text(encoding='utf8'))
    cache=BASE/'raw_ranges'/'1552517188.758'
    manifest=json.loads((cache/'manifest.json').read_text())
    initial=sum(b['bytes'] for b in manifest['blocks'].values())
    raw.URL,raw.CACHE,raw.LIMIT=prior['provenance']['remote']['url'],cache,initial+8*1024*1024
    records=[]
    with raw.CachedRanges() as reader:
        assert reader.remote==prior['provenance']['remote']
        with h5py.File(reader,'r') as f:
            def record(name,node):
                attrs={}
                for k,v in node.attrs.items():
                    array=np.asarray(v)
                    attrs[k]=str(v) if array.size<=32 else dict(shape=list(array.shape),dtype=str(array.dtype))
                row=dict(path=node.name,kind='group' if isinstance(node,h5py.Group) else 'dataset',attributes=attrs)
                if isinstance(node,h5py.Dataset):
                    row.update(shape=list(node.shape),dtype=str(node.dtype),chunks=node.chunks,
                               compression=node.compression,storage_bytes=node.id.get_storage_size())
                else:row['children']=list(node)
                records.append(row)
            for path in ['/general/testpulse','/general/stimsets','/stimulus/templates','/acquisition/images']:
                if path not in f:
                    records.append(dict(path=path,kind='absent'))
                    continue
                record('',f[path]);f[path].visititems(record)
                print('AUX_METADATA',path,'nodes',len(records),'new_bytes',reader.downloaded_this_session,flush=True)
        provenance=dict(remote=reader.remote,initial_cached_bytes=initial,new_download_bytes=reader.downloaded_this_session,
                        blocks=reader.manifest['blocks'])
    assert sha(Path(__file__))==code_hash
    result=dict(code_sha256=code_hash,prior_sha256=sha(prior_path),raw_reader_sha256=sha(Path(raw.__file__)),
        scope='Only auxiliary group names, dataset shapes/dtypes/storage and small attributes; no dataset values',
        records=records,provenance=provenance,claim_ceiling='BIO_EVIDENCE_L0 inventory; structure does not establish a calibrated auxiliary measurement')
    with OUTPUT.open('x',encoding='utf8') as stream:
        json.dump(result,stream,ensure_ascii=False,indent=2,allow_nan=False);stream.write('\n')
    print('DONE',len(records),'new_bytes',provenance['new_download_bytes'],'sha256',sha(OUTPUT),flush=True)


if __name__=='__main__':main()
