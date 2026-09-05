"""각 자료 첫 부트스트랩 그래프를 재생성·재적합해 저장 잔차를 확인한다."""
import csv,hashlib,json
from pathlib import Path
import numpy as np
import microns_constrained_swaps as base
from joint_degree_refit_bootstrap import refine,STORE
HERE=base.HERE
old=json.loads((HERE/'joint_expected_degree_result.json').read_text())
polished=json.loads((HERE/'joint_expected_polish_result.json').read_text())
starts=[('minnie23P',polished),('pinky',next(r for r in old['results'] if r['dataset']=='pinky' and r['threshold']==1))]
_,allcats=base.load_graph();allroots=json.loads(base.SELECTED.read_text())['selected_roots'];lookup={r:i for i,r in enumerate(allroots)}
with (base.ROOT/'data/external/microns_pinky_v185/soma_valence_v185.csv').open(newline='') as stream:
    cells={int(r['pt_root_id']):r for r in csv.DictReader(stream) if r['cell_type']=='e'}
checks=[]
for name,start in starts:
    recordpath=STORE/f'{name}_000.json';record=json.loads(recordpath.read_text())
    path=base.ROOT/start['fitted_file'];assert base.sha(path)==start['fitted_sha256']
    with np.load(path,allow_pickle=False) as saved:p=saved['p'];roots=saved['roots'].tolist()
    a=np.random.default_rng(record['seed']).random(p.shape)<p
    assert hashlib.sha256(a.tobytes()).hexdigest()==record['graph_sha256']
    if name=='minnie23P':
        ids=[lookup[r] for r in roots];c=allcats[np.ix_(ids,ids)]%6
    else:
        xyz=np.array([list(map(int,cells[r]['pt_position'].strip('[]').split())) for r in roots])*[.00354,.00354,.04]
        c=np.digitize(np.linalg.norm(xyz[:,None,:]-xyz[None,:,:],axis=2),[50,100,200,400,800])
    fitted,diag=refine(a,c);assert diag['gate_pass']
    # Recompute moments by a direct pair loop rather than triangular matrix reduction.
    expected=sum(float(fitted[i,j]*fitted[j,i]) for i in range(len(a)) for j in range(i+1,len(a)))
    observed=sum(bool(a[i,j] and a[j,i]) for i in range(len(a)) for j in range(i+1,len(a)))
    assert observed==record['mutual'] and abs(expected-record['fit_mean'])<1e-7
    checks.append(dict(dataset=name,record_sha256=base.sha(recordpath),replayed_graph=True,
                       refitted_mean_difference=expected-record['fit_mean'],max_margin_error=diag['max_absolute_margin_error']))
result=dict(verifier_sha256=base.sha(Path(__file__)),checks=checks,status='TWO_SEEDED_GRAPHS_AND_REFITS_REPLAYED')
out=HERE/'joint_degree_refit_replay_verification.json'
if out.exists():assert json.loads(out.read_text())==result
else:out.write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result,indent=2))
