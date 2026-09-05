"""같은 잔차를 거리와 세포로 가법 분해한다. 국소 유의성 검정이 아니다."""
import csv
import json
from pathlib import Path
import numpy as np
import sgsg_refit_residual as run

HERE=run.HERE


def parts(a,p,c):
    dyad=(a&a.T).astype(float)-p*p.T
    np.fill_diagonal(dyad,0)
    upper=np.triu(np.ones_like(a,dtype=bool),1)
    bins=[dict(opportunities=int(np.sum(upper&(c==b))),
               mutual=int(np.sum(upper&(c==b)&a&a.T)),
               expectation=float((p*p.T)[upper&(c==b)].sum()),
               residual=float(dyad[upper&(c==b)].sum())) for b in range(6)]
    node=dyad.sum(1)/2
    positive=np.maximum(node,0)
    rank=np.argsort(-positive,kind='stable')
    concentration=dict(positive_cells=int(np.sum(node>0)),negative_cells=int(np.sum(node<0)),
                       positive_mass=float(positive.sum()),negative_mass=float(np.minimum(node,0).sum()),
                       top10_positive_fraction=float(positive[rank[:10]].sum()/positive.sum()) if positive.sum() else None)
    assert np.isclose(node.sum(),sum(b['residual'] for b in bins),atol=1e-10)
    return bins,node,concentration


def main():
    prior_path=HERE/'sgsg_refit_residual_result.json'
    prior=json.loads(prior_path.read_text())
    assert prior['failed']==0
    spec=dict(question='Where in distance and node allocation does the descriptive residual difference occur?',
              design='Exploratory additive decomposition of all347nodes and six existingdistancebins; no new fits, draws, thresholds, or biological conclusions',
              allocation='Dyad residual Aij*Aji-pij*pji; assign half to each endpoint so node sum equals global residual',
              distance_bins_um=[50,100,200,400,800],
              concentration='Count positive/negative nodes and top10positive contribution divided by totalpositive contribution. Rank each graph separately; never divide by signed global residual.',
              reporting='All cells CSV, six distance bins including empty bins. MC variation across64modelgraphs only. No multiple-testing claims or error labels for ranked rootIDs.',
              source_result_sha256=run.BASE.sha(prior_path),source_verification_sha256=run.BASE.sha(HERE/'sgsg_refit_residual_verification.json'),
              code_sha256=run.BASE.sha(Path(__file__)))
    cp=HERE/'sgsg_residual_location_contract.json'
    run.source.run.shared.source.write_once(cp,spec)
    roots,xyz,obs,c=run.source.run.shared.source.data()
    old=json.loads((HERE/'joint_expected_polish_result.json').read_text())
    fp=run.BASE.ROOT/old['fitted_file'];assert run.BASE.sha(fp)==old['fitted_sha256']
    with np.load(fp,allow_pickle=False) as f:
        assert f['roots'].tolist()==roots
        p=f['p']
    ob,ov,oc=parts(obs,p,c)
    allbins=[];allnodes=[];concentrations=[]
    for r in prior['records']:
        name=f'{r["index"]:02}.npz'
        ap=run.source.STORE/name;pp=run.STORE/name
        assert run.BASE.sha(ap)==r['input_sha256'] and run.BASE.sha(pp)==r['fitted_sha256']
        with np.load(ap,allow_pickle=False) as f:
            a=f['adjacency'];assert f['roots'].tolist()==roots
        with np.load(pp,allow_pickle=False) as f:
            p=f['p'];assert f['roots'].tolist()==roots
        b,v,con=parts(a,p,c)
        assert np.isclose(v.sum(),r['residual'],atol=1e-9)
        allbins.append(b);allnodes.append(v);concentrations.append(con)
    nodes=np.array(allnodes)
    rows=[dict(root_id=roots[i],x_um=xyz[i,0],y_um=xyz[i,1],z_um=xyz[i,2],
               observed_half_residual=ov[i],generated_mean_half_residual=float(nodes[:,i].mean()),
               generated_sd_half_residual=float(nodes[:,i].std(ddof=1)),
               difference=float(ov[i]-nodes[:,i].mean())) for i in range(len(roots))]
    csv_path=HERE/'sgsg_residual_by_cell.csv'
    import io
    buffer=io.StringIO(newline='');writer=csv.DictWriter(buffer,fieldnames=list(rows[0]))
    writer.writeheader();writer.writerows(rows)
    if csv_path.exists():assert csv_path.read_bytes()==buffer.getvalue().encode('utf-8')
    else:csv_path.write_bytes(buffer.getvalue().encode('utf-8'))
    distance=[]
    for b in range(6):
        values=np.array([row[b]['residual'] for row in allbins])
        distance.append(dict(bin=b,observed=ob[b],generated_mean_residual=float(values.mean()),
                             generated_range=[float(values.min()),float(values.max())],
                             generated_mc_se=float(values.std(ddof=1)/8),
                             residual_difference=float(ob[b]['residual']-values.mean())))
    result=dict(contract_sha256=run.BASE.sha(cp),distance=distance,observed_concentration=oc,
                generated_concentrations=concentrations,
                generated_top10_positive_fraction_mean=float(np.mean([r['top10_positive_fraction'] for r in concentrations])),
                node_csv_sha256=run.BASE.sha(csv_path),node_sum=float(ov.sum()),
                node_difference_sum=float(sum(row['difference'] for row in rows)))
    assert np.isclose(result['node_difference_sum'],prior['comparison']['residual_gap'],atol=1e-9)
    run.source.run.shared.source.write_once(HERE/'sgsg_residual_location_result.json',result)
    print(json.dumps({k:v for k,v in result.items() if k!='generated_concentrations'}),flush=True)


if __name__=='__main__':main()
