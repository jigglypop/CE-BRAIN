"""공개 정적 기능 대응표를 재사용 가능하게 보관한다."""
import json
import urllib.request
from pathlib import Path
from population_reciprocity import ROOT, sha
from superficial_ee_eligibility import save

HERE = Path(__file__).resolve().parent
DEST = ROOT / 'data/external/microns_coregistration_v1412'
BASE = 'https://storage.googleapis.com/mat_dbs/public/minnie65_phase3_v1/v1412/'


def main():
    DEST.mkdir(exist_ok=True)
    output = HERE / 'microns_coregistration_acquisition.json'
    if output.exists():
        prior = json.loads(output.read_text(encoding='utf-8'))
        assert all(sha(ROOT / r['path']) == r['sha256'] for r in prior['files'])
        print('COREGISTRATION_CACHE_VERIFIED'); return
    records = []
    for suffix in ('_merged_header.csv', '_merged.csv.gz'):
        name = 'coregistration_manual_v4' + suffix
        path = DEST / name
        assert not path.exists() and not path.with_suffix(path.suffix + '.partial').exists()
        with urllib.request.urlopen(BASE + name, timeout=30) as response:
            data = response.read(10 * 1024 * 1024 + 1)
            assert len(data) <= 10 * 1024 * 1024
            metadata = dict(etag=response.headers.get('ETag'), last_modified=response.headers.get('Last-Modified'))
        with path.open('xb') as f: f.write(data)
        records.append(dict(path=path.relative_to(ROOT).as_posix(), url=BASE + name,
            bytes=len(data), sha256=sha(path), **metadata))
    save('microns_coregistration_acquisition.json', dict(version=1412,
        source='https://tutorial.microns-explorer.org/materialization-version.html',
        selection='v1718 static header returned404; official archived v1412 header returned200. No claim that v1412 and v1718 have identical root IDs.', files=records))
    print(json.dumps(records, indent=2))


if __name__ == '__main__': main()
