"""고정 첫 대응 스캔의 NWB 메타데이터를 부분 캐시로 확인한다."""
import json
import urllib.request
from pathlib import Path
import h5py
import raw_metadata as raw
from population_reciprocity import ROOT, sha
from superficial_ee_eligibility import save

HERE=Path(__file__).resolve().parent
NAME='microns_nwb_metadata'
API='https://api.dandiarchive.org/api/'
VERSION='0.230307.2132'


def get(path):
    with urllib.request.urlopen(API+path,timeout=30) as r:return json.load(r)


def main():
    manifest=HERE/'microns_dandi_assets.json'
    if manifest.exists():assets=json.loads(manifest.read_text(encoding='utf-8'))
    else:
        assets=get(f'dandisets/000402/versions/{VERSION}/assets/?page_size=100')
        assert assets['next'] is None
        save(manifest.name,assets)
    joined=json.loads((HERE/'microns_coregistration_join_result.json').read_text(encoding='utf-8'))['analysis']
    first=min((r['session'],r['scan_idx']) for r in joined['per_scan'])
    assert first==(4,7)
    chosen=[a for a in assets['results'] if f'_ses-{first[0]}-scan-{first[1]}_' in a['path']]
    assert len(chosen)==1
    a=chosen[0];mp=HERE/'microns_first_scan_asset.json'
    if mp.exists():meta=json.loads(mp.read_text(encoding='utf-8'))
    else:meta=get(f"assets/{a['asset_id']}/");save(mp.name,meta)
    raw.URL=next(u for u in meta['contentUrl'] if u.startswith('https://dandiarchive.s3.amazonaws.com/'))
    raw.CACHE=ROOT/'data/external/microns_functional_nwb/scan_4_7_ranges'
    raw.LIMIT=32*1024*1024
    save(NAME+'_contract.json',dict(question='첫 대응 스캔의 공개 NWB에 어떤 추출 반응·시간축·식별자·자극 정보가 있는가?',
        selection='대응표 session/scan 오름차순 첫 항목4/7. 반응으로 재선정 없음.',
        limits='NWB 메타데이터만, 대형 영상 배열을 읽지 않는다. 부분 캐시32MiB 상한. L0 입력 점검.',
        code_sha256=sha(Path(__file__)),asset_manifest_sha256=sha(manifest),asset_metadata_sha256=sha(mp),range_reader_sha256=sha(Path(raw.__file__))))
    nodes=[]
    with raw.CachedRanges() as reader:
        assert reader.remote['bytes']==a['size']
        with h5py.File(reader,'r') as f:
            def visit(name,node):
                if isinstance(node,h5py.Dataset):
                    item=dict(path=node.name,shape=list(node.shape),dtype=str(node.dtype))
                    if node.size<=10 and node.dtype.kind in 'OSU':item['value']=str(node[()])
                    for key in ('unit','conversion','offset','rate','description','neurodata_type'):
                        if key in node.attrs:item[key]=str(node.attrs[key])
                    nodes.append(item)
            f.visititems(visit)
        result=dict(remote=reader.remote,asset=a,nodes=nodes,new_bytes=reader.downloaded_this_session,
            total_cached_bytes=sum(b['bytes'] for b in reader.manifest['blocks'].values()))
        save(NAME+'_cache_snapshot.json',reader.manifest)
    save(NAME+'_result.json',result)
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
