"""고정 정수 열의 ScanUnit을 읽고 두 인덱스의 대응을 교차검사한다."""
import csv,hashlib,json
from collections import Counter
from pathlib import Path
from population_reciprocity import ROOT
from superficial_ee_eligibility import save

HERE=Path(__file__).resolve().parent
FIELDS=['session','scan_idx','unit_id','field','mask_id','um_x','um_y','um_z','px_x','px_y','ms_delay']


def integer(data):
    return int.from_bytes(data,'big')-(1<<(8*len(data)-1))


def main():
    source=ROOT/'data/external/microns_scan_unit_v8/scan_unit.ibd'
    b=source.read_bytes()
    assert hashlib.sha256(b).hexdigest()=='f5325279d5b85e0f495caf5bef962d78d54e0c2ce96537050156e61291b265e1'
    rows=[];secondary=[];counts=Counter()
    for start in range(0,len(b),16384):
        p=b[start:start+16384]
        if int.from_bytes(p[24:26],'big')!=17855 or int.from_bytes(p[64:66],'big')!=0:continue
        idx=int.from_bytes(p[66:74],'big');assert idx in (61,62)
        assert int.from_bytes(p[42:44],'big') & 0x8000
        assert p[99:107]==b'infimum\0' and p[112:120]==b'supremum'
        pos=99;seen=set();page_rows=[]
        while True:
            pos=(pos+int.from_bytes(p[pos-2:pos],'big'))%65536
            if pos==112:break
            assert 120<=pos<16376 and pos not in seen
            seen.add(pos)
            assert not p[pos-5]&32 and int.from_bytes(p[pos-4:pos-2],'big')&7==0
            if idx==61:
                values=[integer(p[pos:pos+2]),integer(p[pos+2:pos+4]),integer(p[pos+4:pos+8])]
                values += [integer(p[pos+i:pos+i+2]) for i in range(21,37,2)]
                row=dict(zip(FIELDS,values));rows.append(row);page_rows.append(tuple(values[:3]))
            else:
                values=[integer(p[pos+i:pos+i+2]) for i in (0,2,4,6)]+[integer(p[pos+8:pos+12])]
                secondary.append(tuple(values));page_rows.append(tuple(values))
        assert len(seen)==int.from_bytes(p[54:56],'big')
        assert page_rows==sorted(page_rows)
        counts[idx]+=1
    keys={(r['session'],r['scan_idx'],r['unit_id']) for r in rows}
    assert len(keys)==len(rows)
    primary_projection={(r['session'],r['scan_idx'],r['field'],r['mask_id'],r['unit_id']) for r in rows}
    assert len(secondary)==len(rows) and set(secondary)==primary_projection
    selected=sorted((r for r in rows if (r['session'],r['scan_idx'])==(4,7)),key=lambda r:r['unit_id'])
    identity=json.loads((HERE/'microns_roi_identity_result.json').read_text(encoding='utf-8'))
    candidates=json.loads((HERE/'microns_roi_coordinates_result.json').read_text(encoding='utf-8'))
    lookup={r['unit_id']:r for r in selected}
    targets=[]
    for t in identity['targets']:
        r=lookup[t['unit_id']];assert r['field']==t['field']
        targets.append(dict(**t,mask_id=r['mask_id'],ms_delay=r['ms_delay']))
    comparisons=[]
    for t in candidates['matches']:
        r=lookup[t['unit_id']]
        for c in t['candidates']:
            comparisons.append(dict(unit_id=t['unit_id'],field=r['field'],scan_unit_mask_id=r['mask_id'],nwb_coordinate_mask_id=c['mask_id'],equal=r['mask_id']==c['mask_id']))
    output=HERE/'microns_scan_unit_scan_4_7.csv'
    if not output.exists():
        with output.open('x',newline='',encoding='utf-8') as f:
            w=csv.DictWriter(f,fieldnames=FIELDS);w.writeheader();w.writerows(selected)
    else:
        with output.open(encoding='utf-8',newline='') as f:assert [{k:int(v) for k,v in r.items()} for r in csv.DictReader(f)]==selected
    result=dict(status='PRIMARY_SECONDARY_INDEX_AGREEMENT',source_sha256=hashlib.sha256(b).hexdigest(),
        total_rows=len(rows),scan_4_7_rows=len(selected),leaf_pages=dict(counts),targets=targets,
        field_counts=dict(Counter(r['field'] for r in selected)),coordinate_comparisons=comparisons,
        coordinate_equal=sum(c['equal'] for c in comparisons),limits='Offline decoder verified by both indexes; MySQL engine query and exact historical NWB build not independently verified. Timing includes ms_delay per unit; common frame timestamps alone do not establish simultaneity.')
    save('microns_scan_unit_decoding_result.json',result)
    print(json.dumps({k:v for k,v in result.items() if k not in ('targets','coordinate_comparisons')},indent=2))


if __name__=='__main__':main()
