"""다음 투사 세션을 고정 출처에서 한 번 수집한다."""
import hashlib
import json
import sys
import time
from pathlib import Path
import requests

sys.path.insert(0,'.codex/hooks')
import data_registry as registry


def main():
    base = Path('data/external/cortical_propagation_2023')
    target = base/'2021-02-22_RL128.pkl'
    partial = target.with_suffix('.pkl.partial')
    receipt = base/'mechanisms_RL128_download_receipt.json'
    revision = '30e73857ea16a69ec48bb42d942f94d4b4729b36'
    url = f'https://gin.g-node.org/vdplasthijs/S1S2_mechanisms_data/raw/{revision}/pkl_files/projection_2sec_test/2021-02-22_RL128.pkl'
    expected = 1840734539
    assert not target.exists() and not partial.exists() and not receipt.exists(), 'Inspect existing acquisition; do not restart'
    digest = hashlib.sha256(); total = 0; start = time.monotonic(); last = start
    with partial.open('xb') as stream:
        registry.register(registry.DEFAULT_LEDGER,'s1s2_mechanisms_projection','RL128-2021-02-22',
                          'payload_in_progress',partial,url,'Next listed projection session; compare frozen S1/S2 endpoints across sessions',location_only=True)
        with requests.get(url,stream=True,timeout=(30,60)) as response:
            response.raise_for_status()
            assert int(response.headers['Content-Length']) == expected
            for block in response.iter_content(4*1024*1024):
                if total == 0: assert block[:2] == b'\x80\x03', 'Unexpected payload format'
                stream.write(block); digest.update(block); total += len(block)
                if time.monotonic()-last >= 20:
                    stream.flush(); print(json.dumps({'bytes':total,'expected':expected}),flush=True); last = time.monotonic()
    assert total == expected
    partial.rename(target)
    with receipt.open('x',encoding='utf-8') as f:
        json.dump({'url':url,'revision':revision,'bytes':total,'sha256':digest.hexdigest(),
                   'server_sha256_available':False,'elapsed_seconds':time.monotonic()-start},f,indent=2)
    for asset,path in [('payload',target),('download_receipt',receipt)]:
        registry.register(registry.DEFAULT_LEDGER,'s1s2_mechanisms_projection','RL128-2021-02-22',asset,path,url,'Next projection session acquired; HTTP length and protocol prefix verified')
    print(receipt.read_text(encoding='utf-8'),flush=True)


if __name__ == '__main__': main()
