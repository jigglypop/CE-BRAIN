"""부분 요청을 지원하지 않는 공식 데이터 본체를 한 번 스트리밍 수집한다."""
import hashlib
import json
from pathlib import Path
import time

import requests

from randi_target_response import ROOT

BASE = ROOT / 'data/external/cortical_propagation_2023'
NAME = 'sessions_lite_flu_2022-08-11.pkl'
URL = 'https://gin.g-node.org/doi/S1S2_all-optical_data/raw/master/' + NAME
SIZE = 5405910737


def main():
    dest = BASE / NAME
    receipt = BASE / 'payload_download_receipt.json'
    if dest.exists():
        assert receipt.exists()
        r = json.loads(receipt.read_text(encoding='utf-8'))
        assert dest.stat().st_size == r['bytes'] == SIZE
        print('Existing completed payload; no download', flush=True)
        return
    partial = dest.with_suffix('.pkl.partial')
    assert not partial.exists(), 'Existing partial: inspect before retry; server does not support range'
    start = time.monotonic()
    digest = hashlib.sha256()
    count, mark = 0, 0
    with requests.get(URL, stream=True, timeout=(30, 60)) as response:
        response.raise_for_status()
        assert int(response.headers['Content-Length']) == SIZE
        modified = response.headers.get('Last-Modified')
        with partial.open('xb') as stream:
            for block in response.iter_content(4 * 1024 * 1024):
                if count == 0:
                    assert block[:1024] == (BASE / 'payload_prefix.bin').read_bytes()
                stream.write(block)
                digest.update(block)
                count += len(block)
                if count - mark >= 128 * 1024 * 1024:
                    mark = count
                    print(json.dumps({'bytes': count, 'total': SIZE, 'elapsed_s': round(time.monotonic()-start, 1)}), flush=True)
    assert count == SIZE
    result = {'source': URL, 'last_modified': modified, 'bytes': count, 'sha256': digest.hexdigest(),
              'server_sha256_available': False, 'prefix_matches_probe': True,
              'range_supported': False, 'elapsed_seconds': time.monotonic()-start}
    partial.rename(dest)
    receipt.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result), flush=True)


if __name__ == '__main__':
    main()
