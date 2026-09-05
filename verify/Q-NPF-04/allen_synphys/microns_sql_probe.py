"""공개 SQL 원본에서 표 위치를 찾는 제한된 범위 조회. 전체 DB는 받지 않는다."""
import argparse
import hashlib
import json
import re
import urllib.request
from pathlib import Path
from population_reciprocity import ROOT

URL = 'https://bossdb-open-data.s3.amazonaws.com/iarpa_microns/minnie/functional_data/two_photon_processed_data_and_metadata/database_v8/functional_data_database_sql_dump_v8.sql'
DEST = ROOT / 'data/external/microns_sql_v8_ranges'
SIZE = 116199864342
BLOCK = 2 * 1024 * 1024


def read(start):
    DEST.mkdir(parents=True, exist_ok=True)
    end = min(start + BLOCK, SIZE) - 1
    path = DEST / f'{start}-{end}.bin'
    receipt = path.with_suffix('.json')
    if path.exists():
        data = path.read_bytes()
        prior = json.loads(receipt.read_text())
        assert hashlib.sha256(data).hexdigest() == prior['sha256']
    else:
        assert not receipt.exists()
        assert sum(p.stat().st_size for p in DEST.glob('*.bin')) + end-start+1 <= 64*1024*1024
        request = urllib.request.Request(URL, headers={'Range': f'bytes={start}-{end}'})
        with urllib.request.urlopen(request, timeout=30) as r:
            assert r.status == 206
            assert r.headers['Content-Range'] == f'bytes {start}-{end}/{SIZE}'
            data = r.read(end-start+2)
            assert len(data) == end-start+1
            prior = dict(url=URL,start=start,end=end,total=SIZE,etag=r.headers['ETag'],
                         sha256=hashlib.sha256(data).hexdigest())
        for other in DEST.glob('*.json'):
            assert json.loads(other.read_text())['etag'] == prior['etag']
        with path.open('xb') as f: f.write(data)
        with receipt.open('x') as f: json.dump(prior,f,indent=2)
    hits = [(m.start()+start,m.group().decode('ascii',errors='replace')) for m in
            re.finditer(rb'(?:INSERT INTO|CREATE TABLE|LOCK TABLES) `[^`]+`',data)]
    print(json.dumps(dict(start=start,hits=hits[:12],tables=sorted(set(x[1] for x in hits)))))
    return data


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('offset',type=int,nargs='+')
    args=parser.parse_args()
    for offset in args.offset:
        assert 0 <= offset < SIZE
        read(offset)
