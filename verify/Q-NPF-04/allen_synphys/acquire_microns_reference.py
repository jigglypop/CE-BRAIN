"""별도 EM 구조 자료의 공개 교육용 추출물을 판본 고정해 확보한다."""
import hashlib
import json
import urllib.request
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
PIN='513a6fe738f91ce179650f1cadf26d4a4728b21a'
BASE=f'https://raw.githubusercontent.com/AllenInstitute/connectomics_at_cosyne/{PIN}/'
DEST=ROOT/'data/external/microns_v1718_cosyne'
OUTPUT=HERE/'microns_acquisition_receipt.json'
ASSETS=[('docs/resources/data/v1718_cell_info.csv',19202665),
        ('docs/resources/data/v1718_v1_column_synapses.feather',5336978),
        ('examples/preprocessing_celltypes_v1718.ipynb',10450),('LICENSE',35149)]


def main():
    DEST.mkdir(parents=True,exist_ok=True)
    prior=json.loads(OUTPUT.read_text(encoding='utf-8')) if OUTPUT.exists() else None
    records=[]
    for relative,size in ASSETS:
        path=DEST/Path(relative).name
        if not path.exists():
            partial=path.with_suffix(path.suffix+'.partial')
            if partial.exists():raise RuntimeError('부분 파일 확인 필요; 자동 재다운로드하지 않음')
            with urllib.request.urlopen(BASE+relative,timeout=30) as response,partial.open('xb') as stream:
                count=0
                while True:
                    block=response.read(1024*1024)
                    if not block:break
                    count+=len(block);assert count<=size;stream.write(block)
            assert count==size;partial.rename(path)
        assert path.stat().st_size==size
        record=dict(path=path.relative_to(ROOT).as_posix(),url=BASE+relative,bytes=size,
                    sha256=hashlib.sha256(path.read_bytes()).hexdigest())
        records.append(record);print('cached',path.name,size,flush=True)
    receipt=dict(dataset='MICrONS minnie65 v1718, curated V1-column teaching export',git_commit=PIN,
        claim='acquired source files only; EM structural contacts not electrophysiological synapse labels; independence and denominator require provenance audit',files=records)
    if prior is not None:assert prior==receipt
    else:
        with OUTPUT.open('x',encoding='utf-8') as stream:json.dump(receipt,stream,indent=2)


if __name__=='__main__':main()
