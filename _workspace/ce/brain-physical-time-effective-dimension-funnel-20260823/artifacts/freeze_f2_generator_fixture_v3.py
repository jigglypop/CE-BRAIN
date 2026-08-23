import json
from pathlib import Path
from funnel_core_v2 import ROOT,sha,write
from f2_common_v2 import generate
def h(x):import hashlib,numpy as np;return hashlib.sha256(np.ascontiguousarray(x).tobytes()).hexdigest()
def main():
 rows=[]
 for s in ['ROT10','MISS30','MISS50','BLOCK30','ART10','JUMP','ISO_NULL','ZERO_NULL','REVERSE']:
  a,b=generate(s,20269999),generate(s,20269999);assert all(h(a[k])==h(b[k]) for k in ['clean','noisy','clock','mask']);rows.append({'scenario':s,'hashes':{k:h(a[k]) for k in ['clean','noisy','clock','mask']}})
 write(ROOT/'f2-generator-fixture-v3.json',{'schema':'BA-SRM8-F2-generator-fixture-v3','rows':rows,'input_hashes':{'config_v4':sha(ROOT/'f2-config-v4.json'),'common_v2':sha(ROOT/'f2_common_v2.py'),'script':sha(Path(__file__))},'behavior_loaded':False,'candidate_Q_run':False,'numerical_F2_gate':False})
if __name__=='__main__':main()
