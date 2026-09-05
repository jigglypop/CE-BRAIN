"""컨테이너를 실행하지 않고 공개 tar의 파일 위치만 읽는다."""
import io,json,hashlib,tarfile,urllib.request
from population_reciprocity import ROOT

URL='https://bossdb-open-data.s3.amazonaws.com/iarpa_microns/minnie/functional_data/two_photon_processed_data_and_metadata/database_v8/functional_data_database_container_image_v8.tar'
SIZE=103798314496
DEST=ROOT/'data/external/microns_tar_v8_ranges'
BLOCK=65536


class Reader(io.RawIOBase):
    def __init__(self,base=0,size=SIZE):
        self.base=base;self.size=size;self.pos=0
        DEST.mkdir(parents=True,exist_ok=True)
    def readable(self):return True
    def seekable(self):return True
    def tell(self):return self.pos
    def seek(self,offset,whence=0):
        self.pos=offset if whence==0 else self.pos+offset if whence==1 else self.size+offset
        assert 0<=self.pos<=self.size
        return self.pos
    def read(self,n=-1):
        if n<0:n=self.size-self.pos
        assert n<=8*1024*1024
        n=min(n,self.size-self.pos);out=bytearray()
        while len(out)<n:
            absolute=self.base+self.pos
            start=absolute//BLOCK*BLOCK;end=min(start+BLOCK,SIZE)-1
            path=DEST/f'{start}.bin';meta=path.with_suffix('.json')
            if path.exists():
                b=path.read_bytes();r=json.loads(meta.read_text())
                assert hashlib.sha256(b).hexdigest()==r['sha256']
            else:
                assert len(list(DEST.glob('*.bin')))<512
                request=urllib.request.Request(URL,headers={'Range':f'bytes={start}-{end}'})
                with urllib.request.urlopen(request,timeout=30) as response:
                    assert response.status==206
                    assert response.headers['Content-Range']==f'bytes {start}-{end}/{SIZE}'
                    b=response.read(BLOCK+1);assert len(b)==end-start+1
                    r=dict(start=start,end=end,etag=response.headers['ETag'],sha256=hashlib.sha256(b).hexdigest())
                for p in DEST.glob('*.json'):assert json.loads(p.read_text())['etag']==r['etag']
                with path.open('xb') as f:f.write(b)
                with meta.open('x') as f:json.dump(r,f)
            count=min(n-len(out),len(b)-(absolute-start))
            assert count>0
            out.extend(b[absolute-start:absolute-start+count]);self.pos+=count
        return bytes(out)


def index(base=0,size=SIZE):
    output=DEST/f'index_{base}.txt'
    if output.exists():return json.loads(output.read_text())
    records=[]
    with tarfile.open(fileobj=Reader(base,size),mode='r:') as tar:
        for entry in tar:
            records.append(dict(name=entry.name,size=entry.size,offset=base+entry.offset_data,type=entry.type.decode()))
    with output.open('x') as f:json.dump(records,f,indent=2)
    return records


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--base',type=int,default=0);parser.add_argument('--size',type=int,default=SIZE)
    args=parser.parse_args()
    print(json.dumps(index(args.base,args.size),indent=2))
