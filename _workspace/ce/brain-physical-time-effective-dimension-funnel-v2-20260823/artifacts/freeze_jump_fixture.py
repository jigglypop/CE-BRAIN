from __future__ import annotations
import hashlib,json,platform,scipy,numpy as np
from pathlib import Path
from f2_common import generate,OLD
ROOT=Path(__file__).resolve().parent
def fh(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ah(a):return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()
def hashes(x):return {k:ah(x[k]) for k in ('clean','noisy','mask','clock')}
def main():
 rows=[]
 for seed in range(20261101,20261109):
  a,b=generate('JUMP',seed),generate('JUMP',seed);assert hashes(a)==hashes(b)
  H,x=a['meta']['H'],a['meta']['x'];assert ah(H)==ah(b['meta']['H']) and ah(x)==ah(b['meta']['x'])
  assert H.dtype==np.float64 and H.flags.c_contiguous and np.all(H!=0)
  orth=float(np.linalg.norm(H.T@H-np.eye(12),ord=np.inf));e2=np.sum(H[:,:2]**2,axis=1);e8=np.sum(H[:,:8]**2,axis=1)
  assert orth<=1e-12 and e2.min()>1e-12 and e8.min()>1e-12
  cov={};
  for r in (2,8):
   S=H[:,:r]@H[:,:r].T;target=np.r_[np.zeros(12-r),np.ones(r)];tr=abs(float(np.trace(S))-r);er=float(np.max(np.abs(np.linalg.eigvalsh(S)-target)));assert tr<=1e-10 and er<=1e-10;cov[str(r)]={'trace_abs_error':tr,'eig_inf_error':er}
  pre=float(np.max(np.abs(H[:,2:].T@x[:,:384])));post=float(np.max(np.abs(H[:,8:].T@x[:,384:])));assert pre<=1e-12 and post<=1e-12
  m,y=a['mask'],a['clean'];counts=m[:,:460].sum(axis=1);sd=np.array([np.std(y[i,:460][m[i,:460]==1],ddof=0) for i in range(12)]);assert counts.min()>=100 and sd.min()>1e-12
  assert all(np.isfinite(a[k]).all() for k in ('clean','noisy','clock')) and np.all(np.diff(a['clock'])>0) and set(np.unique(m)).issubset({0,1})
  assert all(a[k].flags.c_contiguous for k in ('clean','noisy','mask','clock')) and all(a[k].dtype==np.float64 for k in ('clean','noisy','clock')) and m.dtype==np.uint8
  rows.append({'seed':seed,'array_hashes':hashes(a),'H_sha256':ah(H),'x_sha256':ah(x),'orthogonality_inf':orth,'min_row_energy_2':float(e2.min()),'min_row_energy_8':float(e8.min()),'latent_covariance':cov,'pre_support_abs_max':pre,'post_support_abs_max':post,'min_observed_count':int(counts.min()),'min_clean_prefix_sd':float(sd.min())})
 old=json.loads((OLD/'f2-generator-fixture-v3.json').read_text(encoding='utf-8'));expected={r['scenario']:r['hashes'] for r in old['rows'] if r['scenario']!='JUMP'};mismatch=[]
 for s,want in expected.items():
  got=hashes(generate(s,20269999))
  if got!=want:mismatch.append({'scenario':s,'expected':want,'actual':got})
 assert not mismatch
 receipt={'schema':'BA-SRM9-JUMP-fixture-v1','status':'PASS','jump_rows':rows,'unchanged_nonjump_fixture_seed':20269999,'unchanged_nonjump_scenarios':sorted(expected),'unchanged_nonjump_hash_mismatches':mismatch,'input_hashes':{'carry':fh(ROOT/'carry-forward-receipt.json'),'config':fh(ROOT/'f2-config.json'),'config_receipt':fh(ROOT/'f2-config-receipt.json'),'successor_wrapper':fh(ROOT/'f2_common.py'),'predecessor_common_v2':fh(OLD/'f2_common_v2.py'),'predecessor_fixture_v3':fh(OLD/'f2-generator-fixture-v3.json'),'script':fh(Path(__file__))},'versions':{'python':platform.python_version(),'numpy':np.__version__,'scipy':scipy.__version__},'candidate_Q_run':False,'candidate_status_or_promotion':False,'numerical_F2A':False,'behavior_loaded':False,'model_fit':False}
 (ROOT/'jump-fixture-receipt.json').write_text(json.dumps(receipt,allow_nan=False,sort_keys=True,separators=(',',':'))+'\n',encoding='utf-8')
 print(json.dumps({'status':'PASS','jump_seeds':len(rows),'nonjump_mismatches':len(mismatch)}))
if __name__=='__main__':main()
