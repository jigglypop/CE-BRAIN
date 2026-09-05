"""세포쌍 직접 순회로 65개 그래프의 거리·세포별 분해를 대조한다."""
import csv
import json
from pathlib import Path
import numpy as np
from scipy.spatial.distance import cdist
import sgsg_residual_location as study


def direct(a,p,c):
    nodes=np.zeros(len(a));bins=np.zeros(6)
    for i in range(len(a)):
        for j in range(i+1,len(a)):
            value=int(a[i,j] and a[j,i])-p[i,j]*p[j,i]
            nodes[i]+=value/2;nodes[j]+=value/2;bins[c[i,j]]+=value
    return nodes,bins


def main():
    run=study.run
    result_path=study.HERE/'sgsg_residual_location_result.json'
    result=json.loads(result_path.read_text())
    roots,xyz,obs,_=run.source.run.shared.source.data()
    c=np.digitize(cdist(xyz,xyz),[50,100,200,400,800])
    old=json.loads((study.HERE/'joint_expected_polish_result.json').read_text())
    with np.load(run.BASE.ROOT/old['fitted_file'],allow_pickle=False) as f:p=f['p']
    observed,obins=direct(obs,p,c)
    prior=json.loads((study.HERE/'sgsg_refit_residual_result.json').read_text())
    vectors=[];histograms=[]
    for r in prior['records']:
        name=f'{r["index"]:02}.npz'
        with np.load(run.source.STORE/name,allow_pickle=False) as f:a=f['adjacency']
        with np.load(run.STORE/name,allow_pickle=False) as f:p=f['p']
        nodes,bins=direct(a,p,c)
        assert abs(nodes.sum()-r['residual'])<1e-9
        vectors.append(nodes);histograms.append(bins)
    vectors=np.array(vectors)
    csvpath=study.HERE/'sgsg_residual_by_cell.csv'
    assert run.BASE.sha(csvpath)==result['node_csv_sha256']
    with csvpath.open(encoding='utf-8',newline='') as f:rows=list(csv.DictReader(f))
    assert [int(r['root_id']) for r in rows]==roots
    for i,row in enumerate(rows):
        assert abs(float(row['observed_half_residual'])-observed[i])<1e-9
        assert abs(float(row['generated_mean_half_residual'])-vectors[:,i].mean())<1e-9
        assert abs(float(row['difference'])-(observed[i]-vectors[:,i].mean()))<1e-9
    for i,row in enumerate(result['distance']):
        assert abs(obins[i]-row['observed']['residual'])<1e-9
        assert abs(np.mean(histograms,axis=0)[i]-row['generated_mean_residual'])<1e-9
    positive=observed[observed>0]
    assert abs(sum(sorted(positive,reverse=True)[:10])/positive.sum()-result['observed_concentration']['top10_positive_fraction'])<1e-9
    outcome=dict(result_sha256=run.BASE.sha(result_path),verifier_sha256=run.BASE.sha(Path(__file__)),
                 graphs_verified=65,dyads_per_graph=len(roots)*(len(roots)-1)//2,
                 node_rows_verified=len(rows),distance_bins_verified=6,all_additive_sums_match=True)
    run.source.run.shared.source.write_once(study.HERE/'sgsg_residual_location_verification.json',outcome)
    print(json.dumps(outcome))


if __name__=='__main__':main()
