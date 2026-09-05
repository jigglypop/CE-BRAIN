"""다음 개체의 VC 원자료10개와 부분 캐시 스냅샷을 등록한다."""
import importlib.util
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]


def main():
    spec=importlib.util.spec_from_file_location('registry',ROOT/'.codex/hooks/data_registry.py')
    registry=importlib.util.module_from_spec(spec);spec.loader.exec_module(registry)
    result=json.loads((HERE/'next_donor_vc_response_result.json').read_text(encoding='utf-8'))
    paths=[ROOT/a['path'] for a in result['assets']]+[HERE/'next_donor_vc_response_cache_snapshot.json']
    for path in paths:
        _,added=registry.register(registry.DEFAULT_LEDGER,'allen_synphys_1630015960.701',
            'nwb-etag-'+result['remote']['etag'].strip('"'),path.name,path,result['remote']['url'],
            '반응 크기와 무관하게 고정한 다음 개체593646의 VC 원전류·명령. 유지 전압별5시행 분리, 필요한 범위만 수집.',False)
        print('REGISTERED',path.name,added)


if __name__=='__main__':main()
