"""tar 목록의 정확한 오프셋으로 ScanUnit 파일만 추출한다."""
import hashlib,json,urllib.request
from pathlib import Path
from microns_tar_index import DEST,URL,SIZE,BLOCK
from population_reciprocity import ROOT


def main():
    target=ROOT/'data/external/microns_scan_unit_v8';target.mkdir(exist_ok=True)
    receipt=target/'receipt.json'
    if receipt.exists():
        for r in json.loads(receipt.read_text())['files']:
            assert hashlib.sha256((target/r['file']).read_bytes()).hexdigest()==r['sha256']
        print('SCAN_UNIT_CACHE_VERIFIED');return
    entries=json.loads((DEST/'index_398580224.txt').read_text())
    cached={int(p.stem):p for p in DEST.glob('*.bin')}
    etags={json.loads(p.with_suffix('.json').read_text())['etag'] for p in cached.values()}
    assert len(etags)==1
    etag=etags.pop();files=[]
    for e in entries:
        if e['name'] not in ('var/lib/mysql/microns_phase3_nda/scan_unit.frm','var/lib/mysql/microns_phase3_nda/scan_unit.ibd'):continue
        name=e['name'].split('/')[-1];path=target/name
        assert not path.exists()
        pos=e['offset'];stop=pos+e['size'];data=bytearray();fresh=0;reused=0
        while pos<stop:
            start=pos//BLOCK*BLOCK
            if start in cached:
                b=cached[start].read_bytes();r=json.loads(cached[start].with_suffix('.json').read_text())
                assert hashlib.sha256(b).hexdigest()==r['sha256']
                part=b[pos-start:min(len(b),stop-start)];reused+=len(part)
            else:
                end=min(stop,pos+4*1024*1024,min((s for s in cached if s>pos),default=stop))-1
                req=urllib.request.Request(URL,headers={'Range':f'bytes={pos}-{end}','If-Match':etag})
                with urllib.request.urlopen(req,timeout=30) as response:
                    assert response.status==206 and response.headers['ETag']==etag
                    assert response.headers['Content-Range']==f'bytes {pos}-{end}/{SIZE}'
                    part=response.read(end-pos+2);assert len(part)==end-pos+1
                fresh+=len(part)
            assert part
            data.extend(part);pos+=len(part)
        assert len(data)==e['size']
        with path.open('xb') as f:f.write(data)
        files.append(dict(file=name,offset=e['offset'],bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),new_bytes=fresh,reused_bytes=reused))
    assert len(files)==2
    with receipt.open('x') as f:json.dump(dict(url=URL,etag=etag,files=files),f,indent=2)
    print(json.dumps(files,indent=2))


if __name__=='__main__':main()
