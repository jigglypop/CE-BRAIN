"""VC 원파형10개와 부분 캐시 스냅샷을 직렬 등록한다."""
import importlib.util
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]


def main():
    spec=importlib.util.spec_from_file_location('registry',ROOT/'.codex/hooks/data_registry.py')
    registry=importlib.util.module_from_spec(spec);spec.loader.exec_module(registry)
    result=json.loads((HERE/'different_donor_vc_response_result.json').read_text(encoding='utf-8'))
    paths=[ROOT/a['path'] for a in result['assets']]+[HERE/'different_donor_vc_response_cache_snapshot.json']
    for path in paths:
        _,added=registry.register(registry.DEFAULT_LEDGER,'allen_synphys_1623269658.635',
            'nwb-etag-eca1a0ddcbd4bcb133a5fcd11cdde76c-77',path.name,path,result['remote']['url'],
            'VC10시행의 전후 전류·명령 부분 수집 및 캐시 스냅샷. 유지 전압별5시행을 분리해 분석. 기존 범위 캐시 재사용.',False)
        print(path.name,added)


if __name__=='__main__':main()
