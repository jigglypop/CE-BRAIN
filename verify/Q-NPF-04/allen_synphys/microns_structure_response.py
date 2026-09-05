"""같은 세포의 관측 시냅스와 첫 형광 구간의 동반 변화를 기술한다."""
import csv,json,sys
from collections import Counter,defaultdict
from pathlib import Path
import numpy as np
from population_reciprocity import ROOT,sha
from superficial_ee_eligibility import save

HERE=Path(__file__).resolve().parent


def contrasts(pairs):
    linked=[p['correlation'] for p in pairs if p['linked']]
    unlisted=[p['correlation'] for p in pairs if not p['linked']]
    groups=defaultdict(list)
    for p in pairs:groups[(tuple(p['fields']),p['distance_bin'])].append(p)
    weighted=[];support=0;support_linked=0
    for group in groups.values():
        a=[p['correlation'] for p in group if p['linked']];b=[p['correlation'] for p in group if not p['linked']]
        if a and b:
            weighted.append((len(a),float(np.mean(a)-np.mean(b))))
            support+=len(group);support_linked+=len(a)
    return dict(linked_dyads=len(linked),unlisted_dyads=len(unlisted),
        linked_mean=float(np.mean(linked)) if linked else None,unlisted_mean=float(np.mean(unlisted)) if unlisted else None,
        mean_difference=float(np.mean(linked)-np.mean(unlisted)) if linked and unlisted else None,
        median_difference=float(np.median(linked)-np.median(unlisted)) if linked and unlisted else None,
        matched_mean_difference=sum(n*d for n,d in weighted)/sum(n for n,d in weighted) if weighted else None,
        matched_strata=len(weighted),matched_dyads=support,matched_linked_dyads=support_linked)


def main():
    artifact=ROOT/'data/external/microns_functional_nwb/scan_4_7_first1250.npz'
    receipt=json.loads((HERE/'microns_first_response_result.json').read_text())
    assert sha(artifact)==receipt['artifact_sha256']
    structural=ROOT/'data/external/microns_v1718_cosyne/v1718_v1_column_synapses.feather'
    assert sha(structural)=='fee7afc8c37528e3e1c1a4365f016f74c8ff42b6dad0f06100ef32d38adb0434'
    save('microns_structure_response_contract.json',dict(
        question='In the fixed53 scan4/7 cells and first1250 fluorescence frames, do dyads with an annotated EM synapse have different cofluctuation from dyads with no annotation in this export?',
        status='Exploratory descriptive observation; QC already viewed. No preregistered biological hypothesis, held-out prediction, or causal claim.',
        measurement='Pearson correlation of source fluorescence, not spikes or deltaF/F; unordered dyads with either-direction >=1 synapse annotation.',
        controls='Two time conventions: common frame grid or positive ms_delay with linear interpolation onto frames1..1248. All53 and excluding disputed unit3151. Report all four results.',
        geometry='Euclidean EM soma distances in microns, xyz scales .004,.004,.040. Four pooled distance quartiles fixed from full53 geometry and unordered field pair strata. Linked-count-weighted within-stratum mean differences; report support.',
        uncertainty='Dyads share cells and time samples autocorrelate; no independent-dyad p-values. Leave-one-cell-out range is sensitivity, not confidence interval.',
        limits='One mouse, first~198 seconds, same stimulus and behavior not removed, raw fluorescence common-input/optical confounding, missing annotations not proof of absent synapse.',
        code_sha256=sha(Path(__file__)),response_sha256=sha(artifact),structure_sha256=sha(structural)))
    data=np.load(artifact);times=data['frame_times'];values=data['values'].astype(float)
    targets=json.loads((HERE/'microns_scan_unit_decoding_result.json').read_text())['targets']
    by_unit={t['unit_id']:t for t in targets};ordered=[by_unit[int(u)] for u in data['unit_ids']]
    with (ROOT/'data/external/microns_v1718_cosyne/v1718_cell_info.csv').open(encoding='utf-8',newline='') as f:cells={int(r['pt_root_id']):r for r in csv.DictReader(f)}
    xyz=np.array([[int(cells[t['root_v1718']]['pt_position_'+a]) for a in 'xyz'] for t in ordered])*[.004,.004,.040]
    ii,jj=np.triu_indices(len(ordered),1);distances=np.linalg.norm(xyz[ii]-xyz[jj],axis=1)
    cuts=np.quantile(distances,[.25,.5,.75])
    sys.path.insert(0,str(ROOT/'data/external/analysis_tools/arrow_reader'))
    import pyarrow.feather as feather
    table=feather.read_table(structural,columns=['pre_pt_root_id','post_pt_root_id','syn_id']).to_pydict()
    assert len(set(table['syn_id']))==len(table['syn_id'])
    edges=Counter(zip(table['pre_pt_root_id'],table['post_pt_root_id']))
    scenarios=[];pair_outputs=[]
    grid=times[1:-1]
    assert all(grid[0]>=times[0]+d/1000 and grid[-1]<=times[-1]+d/1000 for d in data['ms_delay'])
    for timing in ('common_frame','positive_delay_sensitivity'):
        x=values[1:-1] if timing=='common_frame' else np.column_stack([np.interp(grid,times+d/1000,values[:,i]) for i,d in enumerate(data['ms_delay'])])
        corr=np.corrcoef(x,rowvar=False);assert np.isfinite(corr).all()
        for i,j in ((0,1),(10,20),(30,52)):
            a=x[:,i]-x[:,i].mean();b=x[:,j]-x[:,j].mean()
            assert abs(corr[i,j]-np.dot(a,b)/np.sqrt(np.dot(a,a)*np.dot(b,b)))<1e-12
        pairs=[]
        for n,(i,j) in enumerate(zip(ii,jj)):
            a,b=ordered[i],ordered[j];ra,rb=a['root_v1718'],b['root_v1718']
            count=edges[ra,rb]+edges[rb,ra]
            pairs.append(dict(unit_a=a['unit_id'],unit_b=b['unit_id'],fields=sorted([a['field'],b['field']]),distance_um=float(distances[n]),distance_bin=int(np.searchsorted(cuts,distances[n])),synapse_annotations=count,linked=bool(count),correlation=float(corr[i,j])))
        pair_outputs.append(dict(timing=timing,pairs=pairs))
        for exclude in (False,True):
            selected=[p for p in pairs if not exclude or 3151 not in (p['unit_a'],p['unit_b'])]
            summary=contrasts(selected)
            units=set(u for p in selected for u in (p['unit_a'],p['unit_b']))
            omitted=[contrasts([p for p in selected if u not in (p['unit_a'],p['unit_b'])])['mean_difference'] for u in sorted(units)]
            scenarios.append(dict(timing=timing,exclude_disputed=exclude,cells=len(units),**summary,leave_one_cell_out_range=[min(omitted),max(omitted)]))
    save('microns_structure_response_pairs.json',pair_outputs)
    save('microns_structure_response_result.json',dict(scenarios=scenarios,distance_quartiles_um=cuts.tolist(),frames=len(grid),
        status='DESCRIPTIVE_WITHIN_SPECIMEN_ASSOCIATION_ONLY',claim_ceiling='Restricted L1 observation conditional on registered identity; integrated mechanism remains L0.'))
    print(json.dumps(scenarios,indent=2))


if __name__=='__main__':main()
