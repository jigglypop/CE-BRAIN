"""OSF의 같은 두 세션에서 필요한 raw_extracted 파일만 확보한다."""
import hashlib
import json
from pathlib import Path

import requests

from randi_target_response import BASE, HERE, save, sha


def main():
    first = BASE / 'raw_extracted_listing.json'
    page = json.loads(first.read_text(encoding='utf-8'))
    entries = list(page['data'])
    n = 1
    needed = {f'{sid}_{key}.txt' for sid in ('6', '9')
              for key in ('gcamp', 't', 'stim_volume_i', 'stim_neurons', 'labels', 'ds_name')}
    while not needed.issubset({x['attributes']['name'] for x in entries}):
        url = page['links'].get('next')
        assert url, 'missing requested files'
        n += 1
        cached = BASE / f'raw_extracted_listing_page{n}.json'
        if cached.exists():
            page = json.loads(cached.read_text(encoding='utf-8'))
        else:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            page = response.json()
            cached.write_text(json.dumps(page, indent=2), encoding='utf-8')
        entries.extend(page['data'])
    folder = BASE / 'raw_extracted'
    folder.mkdir(exist_ok=True)
    receipts = []
    for name in sorted(needed):
        x = next(x for x in entries if x['attributes']['name'] == name)
        attr = x['attributes']
        expected = attr['extra']['hashes']['sha256']
        assert expected
        p = folder / name
        if not p.exists():
            partial = p.with_suffix('.txt.partial')
            assert not partial.exists(), 'existing partial requires recovery'
            response = requests.get(x['links']['download'], timeout=60)
            response.raise_for_status()
            payload = response.content
            assert len(payload) == attr['size']
            assert hashlib.sha256(payload).hexdigest() == expected
            partial.write_bytes(payload)
            partial.rename(p)
        assert p.stat().st_size == attr['size'] and sha(p) == expected
        receipts.append({'name': name, 'source': x['links']['download'], 'osf_id': x['id'],
                         'bytes': attr['size'], 'sha256': expected, 'modified': attr['date_modified']})
        print(name, attr['size'], 'verified', flush=True)
    for sid in ('6', '9'):
        assert (folder / f'{sid}_ds_name.txt').read_bytes() == (BASE / 'exported_data' / f'{sid}_ds_name.txt').read_bytes()
    save('randi_raw_acquisition_result.json', {'files': receipts, 'session_name_match': True,
                                            'source_folder': 'https://osf.io/e2syt/',
                                            'claim_ceiling': 'BIO_EVIDENCE_L0',
                                            'code_sha256': sha(Path(__file__))})


if __name__ == '__main__':
    main()
