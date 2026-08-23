import hashlib,json,os
from pathlib import Path
import numpy as np
from funnel_core_v2 import ROOT,sha,write
from f2_common_v2 import generate
OUT=ROOT/'f2a-dgp-stop-receipt.json'
def main():
 rows=[]
 for seed in range(20261101,20261109):
  x=generate('JUMP',seed)['clean'];sd=x[:,:460].std(axis=1,ddof=0);assert np.array_equal(np.flatnonzero(sd==0),np.array([8,9,10,11]));rows.append({'seed':seed,'prefix_std_ddof0':sd.tolist(),'zero_scale_indices':np.flatnonzero(sd==0).tolist()})
 r={'schema':'BA-SRM8-F2A-DGP-stop-v1','verdict':'SYNTHETIC_DGP_STOP_ZERO_PREFIX_SCALE','evidence':rows,'input_hashes':{'run_f2a':sha(ROOT/'run_f2a.py'),'config_v4':sha(ROOT/'f2-config-v4.json'),'generator_v2':sha(ROOT/'f2_common_v2.py'),'fixture_v3':sha(ROOT/'f2-generator-fixture-v3.json'),'f1_v6':sha(ROOT/'f1-receipt-v6.json'),'recorder':sha(Path(__file__))},'completed_f2a_receipt':False,'candidate_Q_run':False,'candidate_status_or_promotion':False,'F2B_C_D_F2R':False,'behavior_loaded':False,'model_fit':False,'recommendation':'successor DGP should use dense fixed orthogonal sensor mixing'};write(OUT,r);print(json.dumps({'receipt':sha(OUT),'seeds':len(rows)}))
if __name__=='__main__':main()
