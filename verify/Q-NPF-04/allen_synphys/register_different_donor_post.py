"""두 시행의 추가 원파형과 부분 캐시를 등록하고 이전 사유의 문자 손상을 정정한다."""
import importlib.util
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]


def main():
    spec=importlib.util.spec_from_file_location('data_registry',ROOT/'.codex/hooks/data_registry.py')
    registry=importlib.util.module_from_spec(spec);spec.loader.exec_module(registry)
    dataset='allen_synphys_1623269658.635'
    version='nwb-etag-eca1a0ddcbd4bcb133a5fcd11cdde76c-77'
    result=json.loads((HERE/'different_donor_post_response_result.json').read_text(encoding='utf-8'))
    for asset in result['analysis']['assets']:
        path=ROOT/asset['path']
        _,added=registry.register(registry.DEFAULT_LEDGER,dataset,version,path.name,path,result['remote']['url'],
            '정렬 누락 두 시행의 시냅스후 전압·명령 부분 수집. 기존 전세포 파형과 범위 캐시 재사용.',False)
        print('registered',path.name,added)
    path=HERE/'different_donor_post_response_cache_snapshot.json'
    _,added=registry.register(registry.DEFAULT_LEDGER,dataset,version,path.name,path,result['remote']['url'],
        '후세포 파형 추가 수집 뒤 부분 NWB 블록별 해시 스냅샷. 전체 NWB 보유 아님.',False)
    print('registered',path.name,added)
    for old in registry.find(registry.DEFAULT_LEDGER,dataset):
        if '?' not in old['reason']:continue
        reason=('이전 등록 사유의 문자 인코딩 손상 정정. 원파일·해시·판본은 동일. '
                '발화 정렬 누락 진단을 위해 두 시행의 전세포 전압·명령과 부분 캐시 스냅샷을 수집했음.')
        _,added=registry.register(registry.DEFAULT_LEDGER,old['dataset'],old['version'],old['asset'],
            ROOT/old['path'],old['source'],reason,False)
        print('corrected_reason',old['asset'],added)


if __name__=='__main__':main()
