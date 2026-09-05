"""넓은 교정 세포 출력 추출과 column 추출을 시냅스 ID 수준에서 비교한다."""
import argparse
import hashlib
import json
import sys
import urllib.request
from pathlib import Path
from reference_spike_audit import sha

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
DATA=ROOT/'data/external/microns_v1718_cosyne'
NAME='v1718_proofread_output_synapses.feather'
URL='https://raw.githubusercontent.com/AllenInstitute/connectomics_at_cosyne/513a6fe738f91ce179650f1cadf26d4a4728b21a/docs/resources/data/'+NAME
SIZE=95916378
CONTRACT=HERE/'microns_export_overlap_contract.json'
OUTPUT=HERE/'microns_export_overlap_result.json'
ACQUISITION=HERE/'microns_broad_acquisition_receipt.json'


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--verify',action='store_true');args=parser.parse_args()
    selected_path=HERE/'microns_structural_inventory_result.json'
    narrow_path=DATA/'v1718_v1_column_synapses.feather'
    spec=dict(question='Does the wider proofread-output export contain exactly the same selected-to-selected annotations as the V1-column export?',
        selection='same fixed1348 selected roots from structural inventory; compare all synapse IDs and shared data fields after filtering BOTH partners',
        interpretation='file-to-file coverage only; shared omissions/reconstruction errors or database query completeness not excluded',
        broad_url=URL,broad_expected_bytes=SIZE,selected_sha256=sha(selected_path),narrow_sha256=sha(narrow_path),code_sha256=sha(Path(__file__)))
    if CONTRACT.exists():assert spec==json.loads(CONTRACT.read_text(encoding='utf-8'))
    elif args.verify:raise RuntimeError('계약 없음')
    else:
        with CONTRACT.open('x',encoding='utf-8') as stream:json.dump(spec,stream,indent=2)
    path=DATA/NAME
    if not path.exists():
        if args.verify:raise RuntimeError('원 파일 없음')
        partial=path.with_suffix('.feather.partial')
        if partial.exists():raise RuntimeError('부분 파일 존재: 진행 상태부터 확인')
        with urllib.request.urlopen(URL,timeout=30) as response,partial.open('xb') as stream:
            count=0
            while True:
                block=response.read(1024*1024)
                if not block:break
                count+=len(block);assert count<=SIZE;stream.write(block)
            assert count==SIZE
        partial.rename(path)
    assert path.stat().st_size==SIZE
    receipt=dict(url=URL,bytes=SIZE,sha256=sha(path),path=path.relative_to(ROOT).as_posix())
    if ACQUISITION.exists():assert receipt==json.loads(ACQUISITION.read_text(encoding='utf-8'))
    else:
        with ACQUISITION.open('x',encoding='utf-8') as stream:json.dump(receipt,stream,indent=2)
    print('broad export cached and hashed',SIZE,flush=True)
    sys.path.insert(0,str(ROOT/'data/external/analysis_tools/arrow_reader'))
    import pyarrow as pa
    import pyarrow.compute as pc
    import pyarrow.feather as feather
    selected=pa.array(json.loads(selected_path.read_text(encoding='utf-8'))['selected_roots'],type=pa.int64())
    broad=feather.read_table(path);narrow=feather.read_table(narrow_path)
    def filtered(table):
        mask=pc.and_(pc.is_in(table['pre_pt_root_id'],value_set=selected),pc.is_in(table['post_pt_root_id'],value_set=selected))
        table=table.filter(mask)
        return table.take(pc.sort_indices(table,sort_keys=[('syn_id','ascending')]))
    large=filtered(broad);small=filtered(narrow)
    a=set(large['syn_id'].to_pylist());b=set(small['syn_id'].to_pylist())
    assert len(a)==large.num_rows and len(b)==small.num_rows
    shared=sorted(set(large.column_names)&set(small.column_names))
    mismatches={}
    if a==b:
        mismatches={name:not large[name].equals(small[name]) for name in shared}
    result=dict(contract_sha256=sha(CONTRACT),broad_sha256=receipt['sha256'],broad_total_rows=broad.num_rows,
        broad_columns=broad.column_names,narrow_columns=narrow.column_names,
        broad_selected_rows=large.num_rows,narrow_selected_rows=small.num_rows,
        only_broad_ids=sorted(a-b),only_narrow_ids=sorted(b-a),shared_field_mismatches=mismatches,
        status='EXACT_SELECTED_SUBSET_MATCH' if a==b and not any(mismatches.values()) else 'EXPORT_MISMATCH',
        limitation='Not independent biological evidence or guarantee of true negative pairs; both files share publisher and reconstruction.')
    if args.verify:
        assert result==json.loads(OUTPUT.read_text(encoding='utf-8'));print('EXPORT_OVERLAP_REPRODUCED')
    else:
        with OUTPUT.open('x',encoding='utf-8') as stream:json.dump(result,stream,indent=2)
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
