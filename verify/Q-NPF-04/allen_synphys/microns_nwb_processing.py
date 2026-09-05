"""전체 순회 상한 중단 후 processing 구조만 제한적으로 확인한다."""
import json
from pathlib import Path
import h5py
import raw_metadata as raw
from population_reciprocity import ROOT,sha
from superficial_ee_eligibility import save

HERE=Path(__file__).resolve().parent


def main():
    meta=json.loads((HERE/'microns_first_scan_asset.json').read_text(encoding='utf-8'))
    raw.URL=next(u for u in meta['contentUrl'] if u.startswith('https://dandiarchive.s3.amazonaws.com/'))
    raw.CACHE=ROOT/'data/external/microns_functional_nwb/scan_4_7_ranges';raw.LIMIT=40*1024*1024
    save('microns_nwb_metadata_failure.json',dict(status='METADATA_ENUMERATION_INCOMPLETE',reason='whole-file visititems reached configured32MiB cumulative cache cap; error string says64MiB but actual LIMIT was32MiB',session=55947,exit_code=1))
    save('microns_nwb_processing_contract.json',dict(question='첫스캔 processing의 반응 시계열 경로는 무엇인가?',
        adjustment='전체 순회 중단을 보존하고 processing 상위4단계만 목록화. 데이터 배열 읽기 없음. 기존32MiB 재사용, 추가8MiB 이내.',
        code_sha256=sha(Path(__file__)),prior_contract_sha256=sha(HERE/'microns_nwb_metadata_contract.json')))
    with raw.CachedRanges() as reader:
        with h5py.File(reader,'r') as f:
            nodes=[]
            def walk(node,depth):
                item=dict(path=node.name,neurodata_type=str(node.attrs.get('neurodata_type','')))
                if isinstance(node,h5py.Dataset):item.update(shape=list(node.shape),dtype=str(node.dtype))
                else:item['children']=list(node)
                nodes.append(item)
                if isinstance(node,h5py.Group) and depth:
                    for key in node:walk(node[key],depth-1)
            roots=list(f)
            walk(f['processing'],4)
        result=dict(remote=reader.remote,root_keys=roots,nodes=nodes,new_bytes=reader.downloaded_this_session,total_cached_bytes=sum(b['bytes'] for b in reader.manifest['blocks'].values()))
        save('microns_nwb_processing_cache_snapshot.json',reader.manifest)
    save('microns_nwb_processing_result.json',result)
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
