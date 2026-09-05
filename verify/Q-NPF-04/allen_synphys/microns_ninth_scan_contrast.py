"""첫 스캔에서 고정한 대비와 거리 경계를 다음 스캔에 적용한다."""
import json,csv,sys
from collections import Counter
from pathlib import Path
import numpy as np
from population_reciprocity import ROOT,sha
from superficial_ee_eligibility import save
from microns_structure_response import contrasts

HERE=Path(__file__).resolve().parent


def main():
    save('microns_ninth_scan_contrast_contract.json',dict(question='Apply the existing first-window structural contrast to the next scan7/3 with36 nonoverlapping nuclei in the same mouse.',
        method='Keep >=1 annotated synapse in either direction, Pearson raw fluorescence correlation, common/positive-delay timing, first1250 frames trimmed to internal1248. Keep original scan4/7 numerical distance quartile boundaries and field-pair weighting.',
        limits='Same animal; different stimulus mixture and cells. No behavioral correction, causal interpretation or independent animal replication. Report absent strata/edges without relaxing criteria.',code_sha256=sha(Path(__file__))))
    meta=json.loads((HERE/'microns_ninth_scan_result.json').read_text());assert meta['all_finite'] and meta['nonconstant']==36
    path=ROOT/'data/external/microns_functional_nwb/scan_7_3_first1250.npz';assert sha(path)==meta['artifact_sha256']
    data=np.load(path);by_unit={t['unit_id']:t for t in meta['targets']};targets=[by_unit[int(u)] for u in data['unit_ids']]
    first=json.loads((HERE/'microns_structure_response_result.json').read_text());cuts=np.array(first['distance_quartiles_um'])
    with (ROOT/'data/external/microns_v1718_cosyne/v1718_cell_info.csv').open(encoding='utf-8',newline='') as f:cells={int(r['id']):r for r in csv.DictReader(f)}
    xyz=np.array([[int(cells[t['nucleus_id']]['pt_position_'+a]) for a in 'xyz'] for t in targets])*[.004,.004,.040]
    source=ROOT/'data/external/microns_v1718_cosyne/v1718_v1_column_synapses.feather';assert sha(source)=='fee7afc8c37528e3e1c1a4365f016f74c8ff42b6dad0f06100ef32d38adb0434'
    sys.path.insert(0,str(ROOT/'data/external/analysis_tools/arrow_reader'))
    import pyarrow.feather as feather
    table=feather.read_table(source,columns=['pre_pt_root_id','post_pt_root_id']).to_pydict();edges=Counter(zip(table['pre_pt_root_id'],table['post_pt_root_id']))
    times=data['frame_times'];grid=times[1:-1];values=data['values'];results=[];outputs=[]
    for mode in ('common_frame','positive_delay_sensitivity'):
        if mode=='common_frame':x=values[1:-1]
        else:
            for d in data['ms_delay']:assert grid[0]>=times[0]+d/1000 and grid[-1]<=times[-1]+d/1000
            x=np.column_stack([np.interp(grid,times+d/1000,values[:,i]) for i,d in enumerate(data['ms_delay'])])
        corr=np.corrcoef(x,rowvar=False);pairs=[]
        for i,a in enumerate(targets):
            for j in range(i+1,len(targets)):
                b=targets[j];distance=float(np.linalg.norm(xyz[i]-xyz[j]));n=edges[a['root_v1718'],b['root_v1718']]+edges[b['root_v1718'],a['root_v1718']]
                pairs.append(dict(unit_a=a['unit_id'],unit_b=b['unit_id'],fields=sorted([a['field'],b['field']]),distance_um=distance,distance_bin=int(np.searchsorted(cuts,distance)),synapse_annotations=n,linked=bool(n),correlation=float(corr[i,j])))
        assert len(pairs)==630
        results.append(dict(timing=mode,cells=36,dyads=630,**contrasts(pairs)))
        outputs.append(dict(timing=mode,pairs=pairs))
    save('microns_ninth_scan_contrast_pairs.json',outputs)
    save('microns_ninth_scan_contrast_result.json',dict(results=results,fixed_distance_boundaries_um=cuts.tolist(),limits='Conditional registered-cell descriptive observation in same mouse; not replicated causal mechanism.'))
    print(json.dumps(results,indent=2))


if __name__=='__main__':main()
