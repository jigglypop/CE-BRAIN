"""기존 비교층 안에 남은 거리 불균형을 모든 ROI 조합에서 진단한다."""
import csv,itertools,json,sys
from collections import Counter,defaultdict
from pathlib import Path
import numpy as np
from population_reciprocity import ROOT,sha
from superficial_ee_eligibility import save
from microns_repeat_shift_control import weights
from microns_structure_response import contrasts

HERE=Path(__file__).resolve().parent


def read(name):
    return json.loads((HERE/name).read_text(encoding='utf-8'))


def main():
    cellfile=ROOT/'data/external/microns_v1718_cosyne/v1718_cell_info.csv'
    synfile=ROOT/'data/external/microns_v1718_cosyne/v1718_v1_column_synapses.feather'
    assert sha(synfile)=='fee7afc8c37528e3e1c1a4365f016f74c8ff42b6dad0f06100ef32d38adb0434'
    save('microns_distance_balance_contract.json',dict(
        question='Within the existing field-pair and fixed-distance-quartile strata, do annotated dyads retain different soma distances from unlisted dyads?',
        method='Use unchanged linked-count-weighted strata. Apply same contrast weights to soma distance in microns. Report weighted linked/unlisted means and descriptive pooled-SD standardized difference, individual strata and linked distances outside unlisted min/max.',
        selection='All14 analyzed scans; all32/384 ROI assignments; scan4/7 disputed-unit exclusion also reported. No new cutpoints or outcome-based selection.',
        limits='Post-observation balance diagnosis, not an effect correction, p-value or causal attribution. Soma distance may not capture optical overlap. Min/max support is only one-dimensional.',
        code_sha256=sha(Path(__file__)),cells_sha256=sha(cellfile),synapses_sha256=sha(synfile),
        coverage_sha256=sha(HERE/'microns_scan_coverage_result.json'),targets_sha256=sha(HERE/'microns_all_scan_targets_result.json'),
        cuts_sha256=sha(HERE/'microns_structure_response_result.json'),weight_code_sha256=sha(HERE/'microns_repeat_shift_control.py')))
    with cellfile.open(encoding='utf-8',newline='') as f:cells={int(r['id']):r for r in csv.DictReader(f)}
    sys.path.insert(0,str(ROOT/'data/external/analysis_tools/arrow_reader'))
    import pyarrow.feather as feather
    tab=feather.read_table(synfile,columns=['pre_pt_root_id','post_pt_root_id']).to_pydict();edges=Counter(zip(tab['pre_pt_root_id'],tab['post_pt_root_id']))
    cuts=np.array(read('microns_structure_response_result.json')['distance_quartiles_um'])
    targets=read('microns_all_scan_targets_result.json')['targets'];coverage=read('microns_scan_coverage_result.json')['scans']
    results=[];summaries=[]
    for scan in coverage:
        if scan['status']!='RESPONSE_ANALYZED':continue
        key=(scan['session'],scan['scan_idx']);ts=[t for t in targets if (t['session'],t['scan_idx'])==key]
        old=read(scan['source']);assert sha(HERE/scan['source'])==scan['source_sha256']
        multi=scan['assignment_count']>1
        assignments=[dict(unit_ids=a['unit_ids'],exclude_disputed=False) for a in old['assignments']] if multi else [dict(unit_ids=[t['unit_id'] for t in ts],exclude_disputed=False)]
        if key==(4,7):assignments.append(dict(unit_ids=[t['unit_id'] for t in ts if t['unit_id']!=3151],exclude_disputed=True))
        pairs=[]
        for a,b in itertools.combinations(ts,2):
            if a['nucleus_id']==b['nucleus_id']:continue
            xyz=lambda t:np.array([int(cells[t['nucleus_id']]['pt_position_'+x]) for x in 'xyz'])*[.004,.004,.040]
            dist=float(np.linalg.norm(xyz(a)-xyz(b)))
            label=bool(edges[a['root_v1718'],b['root_v1718']]+edges[b['root_v1718'],a['root_v1718']])
            pairs.append(dict(unit_a=a['unit_id'],unit_b=b['unit_id'],fields=sorted([a['field'],b['field']]),distance_bin=int(np.searchsorted(cuts,dist)),distance_um=dist,linked=label))
        local=[]
        for ai,assignment in enumerate(assignments):
            chosen=set(assignment['unit_ids']);pp=[p for p in pairs if p['unit_a'] in chosen and p['unit_b'] in chosen]
            _,w=weights(pp);dist=np.array([p['distance_um'] for p in pp]);pos=np.maximum(w,0);neg=-np.minimum(w,0)
            assert abs(pos.sum()-1)<1e-12 and abs(neg.sum()-1)<1e-12
            ml=float(pos@dist);mu=float(neg@dist);diff=float(w@dist)
            assert abs(diff-(ml-mu))<1e-10
            diag=contrasts([dict(p,correlation=p['distance_um']) for p in pp])
            assert abs(diag['matched_mean_difference']-diff)<1e-10
            sd=float(np.sqrt((pos@((dist-ml)**2)+neg@((dist-mu)**2))/2))
            groups=defaultdict(list)
            for p in pp:groups[(tuple(p['fields']),p['distance_bin'])].append(p)
            strata=[]
            for (fields,bin_id),group in sorted(groups.items()):
                linked=np.array([p['distance_um'] for p in group if p['linked']]);unlisted=np.array([p['distance_um'] for p in group if not p['linked']])
                if not len(linked) or not len(unlisted):continue
                strata.append(dict(fields=list(fields),distance_bin=bin_id,linked=len(linked),unlisted=len(unlisted),
                    linked_mean_um=float(linked.mean()),unlisted_mean_um=float(unlisted.mean()),difference_um=float(linked.mean()-unlisted.mean()),
                    linked_below_unlisted_range=int((linked<unlisted.min()).sum()),linked_above_unlisted_range=int((linked>unlisted.max()).sum())))
            prior=next(r for r in old['results'] if r['timing']=='positive_delay_sensitivity' and r['subset']=='all10' and ((r['assignment_index']==ai) if multi else r.get('exclude_disputed',False)==assignment['exclude_disputed']))
            total=prior['total'] if multi else prior['total_matched']
            row=dict(session=key[0],scan_idx=key[1],assignment_index=ai,exclude_disputed=assignment['exclude_disputed'],
                linked_distance_mean_um=ml,weighted_unlisted_distance_mean_um=mu,matched_distance_difference_um=diff,
                descriptive_standardized_difference=diff/sd if sd else None,observed_total_all10=total,
                matched_linked=diag['matched_linked_dyads'],linked_below_unlisted_range=sum(s['linked_below_unlisted_range'] for s in strata),
                linked_above_unlisted_range=sum(s['linked_above_unlisted_range'] for s in strata),strata=strata)
            results.append(row)
            if not assignment['exclude_disputed']:local.append(row)
        summary=dict(session=key[0],scan_idx=key[1],assignments=len(local),
            distance_difference_range_um=[min(r['matched_distance_difference_um'] for r in local),max(r['matched_distance_difference_um'] for r in local)],
            linked_closer_count=sum(r['matched_distance_difference_um']<0 for r in local),
            outside_range_counts=[min(r['linked_below_unlisted_range']+r['linked_above_unlisted_range'] for r in local),max(r['linked_below_unlisted_range']+r['linked_above_unlisted_range'] for r in local)])
        summaries.append(summary);print(summary)
    save('microns_distance_balance_result.json',dict(results=results,summaries=summaries,
        limits='Distance balance of existing strata only; no correction of activity and no independent-dyad or independent-animal inference.'))


if __name__=='__main__':main()
