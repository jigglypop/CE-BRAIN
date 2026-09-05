"""Locate actual MIES notebook fields without any acquisition data access."""
import json
from pathlib import Path

import h5py

from allen_joint_inventory import BASE, raw, sha, text

HERE=Path(__file__).resolve().parent
OUTPUT=HERE/'electrical_star_notebook_inventory_result.json'


def main():
    if OUTPUT.exists():raise FileExistsError(OUTPUT)
    protocol_path=HERE/'electrical_star_protocol_result.json'
    protocol=json.loads(protocol_path.read_text(encoding='utf8'))
    cache=BASE/'raw_ranges'/protocol['selection']['ext_id']
    manifest=json.loads((cache/'manifest.json').read_text())
    initial=sum(b['bytes'] for b in manifest['blocks'].values())
    raw.URL,raw.CACHE,raw.LIMIT=protocol['remote']['url'],cache,initial+32*1024*1024
    groups=[]
    with raw.CachedRanges() as reader:
        assert reader.remote==protocol['remote']
        with h5py.File(reader,'r') as f:
            for name in f['general/labnotebook']:
                group=f['general/labnotebook'][name]
                item=dict(path=group.name,datasets={})
                for key in group:
                    dataset=group[key]
                    if not isinstance(dataset,h5py.Dataset):continue
                    info=dict(path=dataset.name,shape=list(dataset.shape),dtype=str(dataset.dtype),chunks=dataset.chunks,compression=dataset.compression)
                    if key in ['numericalKeys','textualKeys']:
                        info['keys']=[text(value) for value in dataset[0].ravel()]
                    item['datasets'][key]=info
                groups.append(item)
                print('NOTEBOOK_GROUP',group.name,[(key,value['shape']) for key,value in item['datasets'].items()],flush=True)
                keys=item['datasets'].get('numericalKeys',{}).get('keys',[])
                print('RELEVANT_KEYS',[k for k in keys if any(word in k for word in ['TP ','Resistance','Time','Clamp','EntrySource','Sweep'])],flush=True)
        provenance=dict(remote=reader.remote,initial_cached_bytes=initial,new_download_bytes=reader.downloaded_this_session,blocks=reader.manifest['blocks'])
    result=dict(code_sha256=sha(Path(__file__)),protocol_sha256=sha(protocol_path),raw_reader_sha256=sha(Path(raw.__file__)),
        scope='Labnotebook keys and dataset metadata only; numericalValues, textualValues and acquisition arrays not read',
        groups=groups,provenance=provenance,claim_ceiling='BIO_EVIDENCE_L0 calibration-data eligibility')
    with OUTPUT.open('x',encoding='utf8') as stream:
        json.dump(result,stream,ensure_ascii=False,indent=2,allow_nan=False);stream.write('\n')
    print('DONE',json.dumps(dict(new_bytes=provenance['new_download_bytes'],sha256=sha(OUTPUT))),flush=True)


if __name__=='__main__':main()
