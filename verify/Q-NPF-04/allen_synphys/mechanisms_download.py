"""RL127 투사 세션 한 개를 중복 실행 없이 순차 수집한다."""
import hashlib
import json
import sys
import time
from pathlib import Path
import requests

sys.path.insert(0,'.codex/hooks')
import data_registry as registry

base=Path('data/external/cortical_propagation_2023')
target=base/'2021-02-18_RL127.pkl'
partial=target.with_suffix('.pkl.partial')
url='https://gin.g-node.org/vdplasthijs/S1S2_mechanisms_data/raw/master/pkl_files/projection_2sec_test/2021-02-18_RL127.pkl'
expected=1861537717
assert not target.exists() and not partial.exists(), 'Existing payload requires inspection, not restart'
digest=hashlib.sha256();total=0;start=time.monotonic();last=start
with partial.open('xb') as stream:
    registry.register(registry.DEFAULT_LEDGER,'s1s2_mechanisms_projection','RL127-2021-02-18',
                      'payload_in_progress',partial,url,'First acquisition; complete file not yet verified',location_only=True)
    with requests.get(url,stream=True,timeout=(30,60)) as response:
        response.raise_for_status()
        assert int(response.headers['Content-Length'])==expected
        for block in response.iter_content(4*1024*1024):
            stream.write(block);digest.update(block);total+=len(block)
            if time.monotonic()-last>=20:
                stream.flush();print(json.dumps({'bytes':total,'expected':expected}),flush=True);last=time.monotonic()
assert total==expected
with partial.open('rb') as stream:
    prefix=(base/'mechanisms_RL127_prefix.bin').read_bytes()
    assert stream.read(len(prefix))==prefix
partial.rename(target)
receipt=base/'mechanisms_RL127_download_receipt.json'
receipt.write_text(json.dumps({'url':url,'bytes':total,'sha256':digest.hexdigest(),
                             'server_sha256_available':False,'elapsed_seconds':time.monotonic()-start},indent=2),encoding='utf-8')
for asset,path in [('payload',target),('download_receipt',receipt)]:
    registry.register(registry.DEFAULT_LEDGER,'s1s2_mechanisms_projection','RL127-2021-02-18',asset,path,url,'First acquisition completed; HTTP length and prefix verified')
print(receipt.read_text(),flush=True)
