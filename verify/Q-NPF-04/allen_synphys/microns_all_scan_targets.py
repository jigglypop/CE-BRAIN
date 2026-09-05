"""이미 확보한 ScanUnit에서 고정 코호트의 모든 스캔 대응을 확인한다."""
import json,re
from collections import Counter,defaultdict
from pathlib import Path
from population_reciprocity import ROOT,sha
from superficial_ee_eligibility import save
from microns_decode_scan_unit import integer,FIELDS

HERE=Path(__file__).resolve().parent


def decode():
    source=ROOT/'data/external/microns_scan_unit_v8/scan_unit.ibd'
    assert sha(source)=='f5325279d5b85e0f495caf5bef962d78d54e0c2ce96537050156e61291b265e1'
    raw=source.read_bytes();rows=[];secondary=[]
    for start in range(0,len(raw),16384):
        p=raw[start:start+16384]
        if int.from_bytes(p[24:26],'big')!=17855 or int.from_bytes(p[64:66],'big')!=0:continue
        idx=int.from_bytes(p[66:74],'big');assert idx in (61,62)
        assert int.from_bytes(p[42:44],'big')&0x8000
        assert p[99:107]==b'infimum\0' and p[112:120]==b'supremum'
        pos=99;seen=set();keys=[]
        while True:
            pos=(pos+int.from_bytes(p[pos-2:pos],'big'))%65536
            if pos==112:break
            assert 120<=pos<16376 and pos not in seen;seen.add(pos)
            assert not p[pos-5]&32 and int.from_bytes(p[pos-4:pos-2],'big')&7==0
            if idx==61:
                values=[integer(p[pos:pos+2]),integer(p[pos+2:pos+4]),integer(p[pos+4:pos+8])]+[integer(p[pos+i:pos+i+2]) for i in range(21,37,2)]
                rows.append(dict(zip(FIELDS,values)));keys.append(tuple(values[:3]))
            else:
                values=[integer(p[pos+i:pos+i+2]) for i in (0,2,4,6)]+[integer(p[pos+8:pos+12])]
                secondary.append(tuple(values));keys.append(tuple(values))
        assert len(seen)==int.from_bytes(p[54:56],'big') and keys==sorted(keys)
    lookup={(r['session'],r['scan_idx'],r['unit_id']):r for r in rows};assert len(lookup)==len(rows)
    projection={(r['session'],r['scan_idx'],r['field'],r['mask_id'],r['unit_id']) for r in rows}
    assert len(secondary)==len(rows) and set(secondary)==projection
    return lookup


def main():
    lookup=decode();source=json.loads((HERE/'microns_coregistration_join_result.json').read_text())['analysis']['matches']
    assets=json.loads((HERE/'microns_dandi_assets.json').read_text())['results'];by_scan={}
    for asset in assets:
        match=re.search(r'ses-(\d+)-scan-(\d+)',asset['path'])
        if match:by_scan[tuple(map(int,match.groups()))]=asset
    groups=defaultdict(list)
    for t in source:
        r=lookup[t['session'],t['scan_idx'],t['unit_id']];assert r['field']==t['field']
        groups[t['session'],t['scan_idx']].append(dict(**t,mask_id=r['mask_id'],ms_delay=r['ms_delay']))
    summaries=[];first={r['nucleus_id'] for r in groups[4,7]}
    for (session,scan),targets in sorted(groups.items()):
        asset=by_scan.get((session,scan));nuclei=Counter(t['nucleus_id'] for t in targets)
        summaries.append(dict(session=session,scan_idx=scan,cells=len(nuclei),units=len(targets),multi_unit_cells=sum(n>1 for n in nuclei.values()),shared_with_first=len(set(nuclei)&first),asset_id=asset['asset_id'] if asset else None,asset_path=asset['path'] if asset else None))
    save('microns_all_scan_targets_result.json',dict(unique_cells=len({t['nucleus_id'] for t in source}),target_units=len(source),scans=summaries,targets=[t for key in sorted(groups) for t in groups[key]],code_sha256=sha(Path(__file__)),limits='Same mouse with repeated cells across scans; NWB schemas and historical annotations for later scans still require direct validation.'))
    print(json.dumps(summaries,indent=2))


if __name__=='__main__':main()
