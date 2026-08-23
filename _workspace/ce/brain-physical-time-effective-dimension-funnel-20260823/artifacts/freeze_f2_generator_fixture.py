from __future__ import annotations
import hashlib,json,platform
from pathlib import Path
import numpy as np
from funnel_core_v2 import ROOT,sha,write
from f2_common import generate
OUT=ROOT/'f2-generator-fixture-receipt.json'
def h(a):return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()
def main():
 scenarios=['ROT10','MISS30','MISS50','BLOCK30','ART10','JUMP','ISO_NULL','ZERO_NULL','REVERSE'];rows=[]
 for s in scenarios:
  x=generate(s,20269999);rows.append({'scenario':s,'clean_sha256':h(x['clean']),'noisy_sha256':h(x['noisy']),'clock_sha256':h(x['clock']),'mask_sha256':h(x['mask']),'shapes':{k:list(x[k].shape) for k in ['clean','noisy','clock','mask']},'gap_indices':x['meta']['gap_indices'],'block_starts':x['meta'].get('block_starts'),'artifact_count':x['meta'].get('artifact_count')})
 r={'schema':'BA-SRM8-F2-generator-fixture-v1','fixture_seed':20269999,'rows':rows,'input_hashes':{'generator':sha(ROOT/'f2_common.py'),'config':sha(ROOT/'f2-config.json'),'script':sha(Path(__file__))},'versions':{'numpy':np.__version__,'python':platform.python_version()},'behavior_loaded':False,'model_fit':False,'candidate_Q_run':False,'numerical_F2_gate':False};write(OUT,r);print(json.dumps({'receipt':sha(OUT),'scenarios':len(rows)}))
if __name__=='__main__':main()
