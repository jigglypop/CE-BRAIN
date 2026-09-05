"""Target known auxiliary notebook paths after a bounded census attempt failed.

Reads field-name datasets only if they contain strings; never reads response
or stimulus values. Limited group iteration records incompleteness explicitly.
"""
import json
from pathlib import Path

import h5py
import numpy as np

from allen_joint_inventory import BASE, raw, sha, text

HERE=Path(__file__).resolve().parent
OUTPUT=HERE/'electrical_star_auxiliary_targeted_result.json'


def main():
    if OUTPUT.exists():raise FileExistsError(OUTPUT)
    code_hash=sha(Path(__file__))
    prior_path=HERE/'electrical_star_all_protocols_result.json'
    prior=json.loads(prior_path.read_text(encoding='utf8'))
    cache=BASE/'raw_ranges'/'1552517188.758'
    manifest=json.loads((cache/'manifest.json').read_text())
    initial=sum(b['bytes'] for b in manifest['blocks'].values())
    raw.URL,raw.CACHE,raw.LIMIT=prior['provenance']['remote']['url'],cache,initial+2*1024*1024
    records=[]
    with raw.CachedRanges() as reader:
        assert reader.remote==prior['provenance']['remote']
        with h5py.File(reader,'r') as f:
            def describe(path):
                try:node=f[path]
                except KeyError:return dict(path=path,kind='absent')
                row=dict(path=path,kind='group' if isinstance(node,h5py.Group) else 'dataset')
                if isinstance(node,h5py.Dataset):
                    row.update(shape=list(node.shape),dtype=str(node.dtype),chunks=node.chunks,compression=node.compression,
                               attribute_names=list(node.attrs))
                    if path.endswith('Keys') and node.size<=4096 and node.dtype.kind in ['O','S','U']:
                        row['field_name_values']=np.vectorize(text,otypes=[str])(node[()]).tolist()
                return row
            for key in ['numericalKeys','numericalValues','textualKeys','textualValues']:
                path='/general/testpulse/ITC1600_Dev_0/'+key
                try:row=describe(path)
                except (RuntimeError,OSError) as error:row=dict(path=path,kind='unresolved',error=str(error))
                records.append(row)
                print('TARGET',path,row.get('kind'),row.get('shape'),'new_bytes',reader.downloaded_this_session,flush=True)
            for path in ['/general/testpulse/ITC1600_Dev_0','/general/stimsets','/stimulus/templates','/acquisition/images']:
                row=dict(path=path,kind='group',children_sample=[],enumeration_complete=False)
                try:
                    def collect(name):
                        row['children_sample'].append(text(name))
                        return len(row['children_sample'])>=8
                    group=f[path]
                    stop,_=group.id.links.iterate(collect,order=h5py.h5.ITER_NATIVE)
                    row['enumeration_complete']=not bool(stop)
                    row['child_metadata']=[describe(path+'/'+name) for name in row['children_sample']]
                except (RuntimeError,OSError,ValueError) as error:row['error']=str(error)
                records.append(row)
                print('GROUP',path,row['children_sample'],row['enumeration_complete'],row.get('error'),'new_bytes',reader.downloaded_this_session,flush=True)
        provenance=dict(remote=reader.remote,initial_cached_bytes=initial,new_download_bytes=reader.downloaded_this_session,
                        blocks=reader.manifest['blocks'])
    assert sha(Path(__file__))==code_hash
    result=dict(code_sha256=code_hash,prior_sha256=sha(prior_path),raw_reader_sha256=sha(Path(raw.__file__)),
        previous_failed_attempt_sha256=sha(HERE/'electrical_star_auxiliary_metadata.py'),
        previous_unfrozen_targeted_source_sha256='2b1e6dfe4741bccf5b08d256d4e38cc8fb831c4e916ecab62365d787630988e3',
        attempt_history=['Exhaustive auxiliary traversal reached 8MiB additional cache cap without a result',
            'Initial targeted attempt reached 2MiB cap and failed at temporary group link iterator lifetime; no result was written',
            'Targeted revision retains the group reference, uses direct path lookup, and preserves unresolved errors'],
        scope='Known auxiliary dataset metadata, optional string field names, and at most eight native-order child names per group; no response or command values',
        records=records,provenance=provenance,claim_ceiling='BIO_EVIDENCE_L0 partial auxiliary inventory; unresolved or unenumerated data are not absent')
    with OUTPUT.open('x',encoding='utf8') as stream:
        json.dump(result,stream,ensure_ascii=False,indent=2,allow_nan=False);stream.write('\n')
    print('DONE','new_bytes',provenance['new_download_bytes'],'sha256',sha(OUTPUT),flush=True)


if __name__=='__main__':main()
