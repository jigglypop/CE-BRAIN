"""공식 v185 소규모 표만 수집하고 서버 MD5와 로컬 SHA-256을 확인한다."""
import hashlib
import json
import urllib.request
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
DATA=ROOT/'data/external/microns_pinky_v185'
FILES={
    'soma_subgraph_synapses_spines_v185.csv':(274298,'5bbb8ff59dcad4ccea6d46930920cd04'),
    'soma_valence_v185.csv':(30881,'a8ce8aa4e5cdf4202caa5ae10411c333'),
}


def main():
    DATA.mkdir(exist_ok=True)
    records=[]
    for name,(size,md5) in FILES.items():
        path=DATA/name
        url=f'https://zenodo.org/records/3710459/files/{name}?download=1'
        if not path.exists():
            partial=path.with_suffix(path.suffix+'.partial')
            if partial.exists():
                raise RuntimeError('existing partial requires inspection')
            with urllib.request.urlopen(url,timeout=60) as response:
                data=response.read(size+1)
            assert len(data)==size and hashlib.md5(data).hexdigest()==md5
            with partial.open('xb') as stream:stream.write(data)
            partial.rename(path)
        data=path.read_bytes()
        assert len(data)==size and hashlib.md5(data).hexdigest()==md5
        records.append(dict(path=path.relative_to(ROOT).as_posix(),source=url,bytes=size,
            server_md5=md5,sha256=hashlib.sha256(data).hexdigest()))
    receipt=dict(record='https://zenodo.org/records/3710459',
        selection='only two official small tables; no full3.2million synapse table or meshes',files=records,
        script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    output=Path(__file__).with_name('pinky_acquisition_receipt.json')
    if output.exists():assert json.loads(output.read_text())==receipt
    else:output.write_text(json.dumps(receipt,indent=2),encoding='utf-8')
    print(json.dumps(receipt,indent=2))


if __name__=='__main__':main()
