import hashlib,json,scipy,numpy as np
from pathlib import Path
from funnel_core_v2 import ROOT,sha,write
from f2_common_v2 import generate
OUT=ROOT/'f2-generator-fixture-v2.json'
def h(a):return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()
def main():
 rows=[]
 for s in ['ROT10','MISS30','MISS50','BLOCK30','ART10','JUMP','ISO_NULL','ZERO_NULL','REVERSE']:
  a,b=generate(s,20269999),generate(s,20269999)
  for x in [a,b]:assert all(np.isfinite(x[k]).all() for k in ['clean','noisy','clock']) and np.diff(x['clock']).min()>0 and all(x[k].flags.c_contiguous for k in ['clean','noisy','mask','clock'])
  if s=='ZERO_NULL':assert not a['clean'].any() and not a['noisy'].any()
  hashes={k:h(a[k]) for k in ['clean','noisy','clock','mask']};assert hashes=={k:h(b[k]) for k in hashes};rows.append({'scenario':s,'hashes':hashes,'shapes':{k:list(a[k].shape) for k in hashes},'dtypes':{k:str(a[k].dtype) for k in hashes},'gap_indices':a['meta']['gap_indices'],'block_starts':a['meta'].get('block_starts'),'artifact_count':a['meta'].get('artifact_count')})
 r={'schema':'BA-SRM8-F2-generator-fixture-v2','fixture_seed':20269999,'rows':rows,'input_hashes':{'common_v2':sha(ROOT/'f2_common_v2.py'),'config_v3':sha(ROOT/'f2-config-v3.json'),'script':sha(Path(__file__))},'versions':{'numpy':np.__version__,'scipy':scipy.__version__},'behavior_loaded':False,'model_fit':False,'candidate_Q_run':False,'numerical_F2_gate':False,'deterministic_in_process':True};write(OUT,r);print(json.dumps({'receipt':sha(OUT),'scenarios':len(rows)}))
if __name__=='__main__':
 import funnel_core_v2
 original=funnel_core_v2.sha
 funnel_core_v2.sha=lambda value: original(Path(value)) if isinstance(value,str) else original(value)
 main()
