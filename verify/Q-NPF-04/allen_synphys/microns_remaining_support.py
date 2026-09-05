"""보유 구조 자료로 남은 스캔의 비교 가능성과 중복 ROI를 확인한다."""
import csv,json,sys
from collections import Counter,defaultdict
from pathlib import Path
import numpy as np
from population_reciprocity import ROOT,sha
from superficial_ee_eligibility import save

HERE=Path(__file__).resolve().parent


def main():
    source=ROOT/'data/external/microns_v1718_cosyne/v1718_v1_column_synapses.feather'
    assert sha(source)=='fee7afc8c37528e3e1c1a4365f016f74c8ff42b6dad0f06100ef32d38adb0434'
    cellfile=ROOT/'data/external/microns_v1718_cosyne/v1718_cell_info.csv'
    targetfile=HERE/'microns_all_scan_targets_result.json'
    cutfile=HERE/'microns_structure_response_result.json'
    save('microns_remaining_support_contract.json',dict(
        question='Which remaining scans support the fixed linked-versus-unlisted field-distance contrast before further fluorescence acquisition?',
        method='Same v1718 either-direction annotated synapse labels and scan4/7 numerical distance cuts. Unique nucleus with exactly one unit can enter fixed geometry. Multi-unit nuclei are listed and excluded only from the diagnostic singleton subset, not silently resolved.',
        gate='At least one stratum containing both linked and unlisted dyads is necessary. Multi-unit identity requires a separate declared rule. No fluorescence used, no geometry threshold relaxation.',
        code_sha256=sha(Path(__file__)),structure_sha256=sha(source),cells_sha256=sha(cellfile),targets_sha256=sha(targetfile),cut_source_sha256=sha(cutfile)))
    with cellfile.open(encoding='utf-8',newline='') as f:cells={int(r['id']):r for r in csv.DictReader(f)}
    sys.path.insert(0,str(ROOT/'data/external/analysis_tools/arrow_reader'))
    import pyarrow.feather as feather
    table=feather.read_table(source,columns=['pre_pt_root_id','post_pt_root_id']).to_pydict()
    edges=Counter(zip(table['pre_pt_root_id'],table['post_pt_root_id']))
    cuts=np.array(json.loads(cutfile.read_text())['distance_quartiles_um'])
    targets=json.loads(targetfile.read_text())['targets'];groups=defaultdict(list)
    for t in targets:groups[(t['session'],t['scan_idx'])].append(t)
    rows=[]
    for (session,scan),ts in sorted(groups.items()):
        nuclei=defaultdict(list)
        for t in ts:nuclei[t['nucleus_id']].append(t)
        assert all(len({t['root_v1718'] for t in v})==1 for v in nuclei.values())
        singleton=sorted([v[0] for v in nuclei.values() if len(v)==1],key=lambda t:t['unit_id'])
        strata=defaultdict(lambda:Counter());linked=0;pair_rows=[]
        for i,a in enumerate(singleton):
            for b in singleton[i+1:]:
                pa=np.array([int(cells[a['nucleus_id']]['pt_position_'+x]) for x in 'xyz'])*[.004,.004,.040]
                pb=np.array([int(cells[b['nucleus_id']]['pt_position_'+x]) for x in 'xyz'])*[.004,.004,.040]
                count=edges[a['root_v1718'],b['root_v1718']]+edges[b['root_v1718'],a['root_v1718']]
                label=bool(count);linked+=label
                key=(tuple(sorted([a['field'],b['field']])),int(np.searchsorted(cuts,np.linalg.norm(pa-pb))))
                strata[key][label]+=1
                if len(singleton)<=2:pair_rows.append(dict(nucleus_a=a['nucleus_id'],nucleus_b=b['nucleus_id'],annotations=count,linked=label))
        valid=[v for v in strata.values() if v[True] and v[False]]
        multiple=[dict(nucleus_id=k,units=[dict(unit_id=t['unit_id'],field=t['field'],mask_id=t['mask_id'],residual=t['residual'],score=t['score']) for t in v]) for k,v in nuclei.items() if len(v)>1]
        status='NEEDS_MULTI_UNIT_RULE' if multiple else 'GEOMETRY_SUPPORTED' if valid else 'NO_MATCHED_CONTRAST_SUPPORT'
        rows.append(dict(session=session,scan_idx=scan,nuclei=len(nuclei),units=len(ts),singleton_cells=len(singleton),
            singleton_dyads=len(singleton)*(len(singleton)-1)//2,singleton_linked=linked,
            singleton_matched_strata=len(valid),singleton_matched_dyads=sum(sum(v.values()) for v in valid),
            singleton_matched_linked=sum(v[True] for v in valid),multi_unit_nuclei=multiple,small_population_pairs=pair_rows,status=status))
    # Agreement with every already acquired fixed population prevents redefining support.
    prefixes=['next','third','fourth','fifth','sixth','seventh','eighth','ninth','tenth']
    for prefix in prefixes:
        scanmeta=json.loads((HERE/f'microns_{prefix}_scan_result.json').read_text())
        target=scanmeta['targets'][0]
        r=next(r for r in rows if (r['session'],r['scan_idx'])==(target['session'],target['scan_idx']))
        prior=json.loads((HERE/f'microns_{prefix}_scan_contrast_result.json').read_text())['results'][0]
        for new,old in [('singleton_dyads','dyads'),('singleton_linked','linked_dyads'),('singleton_matched_strata','matched_strata'),('singleton_matched_dyads','matched_dyads'),('singleton_matched_linked','matched_linked_dyads')]:
            assert r[new]==prior[old],(prefix,new)
    save('microns_remaining_support_result.json',dict(scans=rows,existing_nine_followup_scans_agree=True,limits='Geometry/identity support only. No biological effect or power assertion. Singleton diagnostic does not authorize a new confirmatory subset.'))
    for r in rows:
        if (r['session'],r['scan_idx'])>(7,4):print({k:v for k,v in r.items() if k!='multi_unit_nuclei'},'multi_unit_cells',len(r['multi_unit_nuclei']))


if __name__=='__main__':main()
