"""중복 ROI의 모든 단일 선택 조합에서 구조 비교층을 확인한다."""
import csv,itertools,json,sys
from collections import Counter,defaultdict
from pathlib import Path
import numpy as np
from population_reciprocity import ROOT,sha
from superficial_ee_eligibility import save

HERE=Path(__file__).resolve().parent


def main():
    targetfile=HERE/'microns_all_scan_targets_result.json'
    source=ROOT/'data/external/microns_v1718_cosyne/v1718_v1_column_synapses.feather'
    assert sha(source)=='fee7afc8c37528e3e1c1a4365f016f74c8ff42b6dad0f06100ef32d38adb0434'
    save('microns_multi_unit_contract.json',dict(
        question='Can fixed per-nucleus structural contrasts be evaluated under every recorded ROI assignment for scans9/3 and9/4?',
        rule='Enumerate Cartesian product choosing exactly one observed unit for every nucleus. Do not rank by response, score, residual or desired effect. Same nucleus is never counted as two cells or paired with itself.',
        future_response_rule='Acquire all recorded units, apply unchanged alignment/decomposition. Calculate every assignment with its selected field strata and original distance cuts. Report full set/range, not favorable representative. Shared repeat-control shifts indexed by nucleus, reused across alternative ROI assignments; alternatives are not independent experiments.',
        limits='Assignment uncertainty sensitivity, not biological adjudication or new confirmatory evidence. Support here is structural only; functional inputs not acquired by this program.',
        targets_sha256=sha(targetfile),structure_sha256=sha(source),code_sha256=sha(Path(__file__))))
    targets=json.loads(targetfile.read_text())['targets']
    with (ROOT/'data/external/microns_v1718_cosyne/v1718_cell_info.csv').open(encoding='utf-8',newline='') as f:cells={int(r['id']):r for r in csv.DictReader(f)}
    cuts=np.array(json.loads((HERE/'microns_structure_response_result.json').read_text())['distance_quartiles_um'])
    sys.path.insert(0,str(ROOT/'data/external/analysis_tools/arrow_reader'))
    import pyarrow.feather as feather
    tab=feather.read_table(source,columns=['pre_pt_root_id','post_pt_root_id']).to_pydict();edges=Counter(zip(tab['pre_pt_root_id'],tab['post_pt_root_id']))
    results=[]
    for scan,expected in [(3,32),(4,384)]:
        ts=[t for t in targets if (t['session'],t['scan_idx'])==(9,scan)]
        groups=defaultdict(list)
        for t in ts:groups[t['nucleus_id']].append(t)
        nuclei=sorted(groups);pairdata={}
        for a,b in itertools.combinations(ts,2):
            if a['nucleus_id']==b['nucleus_id']:continue
            pa=np.array([int(cells[a['nucleus_id']]['pt_position_'+x]) for x in 'xyz'])*[.004,.004,.040]
            pb=np.array([int(cells[b['nucleus_id']]['pt_position_'+x]) for x in 'xyz'])*[.004,.004,.040]
            label=bool(edges[a['root_v1718'],b['root_v1718']]+edges[b['root_v1718'],a['root_v1718']])
            pairdata[tuple(sorted((a['unit_id'],b['unit_id'])))]=(tuple(sorted((a['field'],b['field']))),int(np.searchsorted(cuts,np.linalg.norm(pa-pb))),label)
        assignments=[]
        for selected in itertools.product(*(sorted(groups[n],key=lambda t:t['unit_id']) for n in nuclei)):
            units=[t['unit_id'] for t in selected];strata=defaultdict(Counter);linked=0
            for a,b in itertools.combinations(units,2):
                field,dist,label=pairdata[tuple(sorted((a,b)))];strata[(field,dist)][label]+=1;linked+=label
            valid=[v for v in strata.values() if v[True] and v[False]]
            assignments.append(dict(unit_ids=units,linked=linked,matched_strata=len(valid),matched_dyads=sum(sum(v.values()) for v in valid),matched_linked=sum(v[True] for v in valid)))
        assert len(assignments)==expected
        assert len({a['linked'] for a in assignments})==1
        result=dict(session=9,scan_idx=scan,nuclei=nuclei,assignments=assignments,
            all_have_support=all(a['matched_strata']>0 for a in assignments),
            ranges={k:[min(a[k] for a in assignments),max(a[k] for a in assignments)] for k in ('linked','matched_strata','matched_dyads','matched_linked')})
        results.append(result)
        print('SCAN',scan,'ASSIGNMENTS',len(assignments),'SUPPORT',result['all_have_support'],result['ranges'])
    save('microns_multi_unit_support_result.json',dict(scans=results,status='ALL_RECORDED_SINGLE_ROI_ASSIGNMENTS_ENUMERATED',limits='No fluorescence result; no assumption that any recorded assignment is biologically correct.'))


if __name__=='__main__':main()
