import json
from funnel_core_v2 import ROOT,sha,write
def main():
 c=json.loads((ROOT/'f2-config-v3.json').read_text());c['schema']='BA-SRM8-F2-config-v4';c['promoted_ids']=json.loads((ROOT/'f1-receipt-v6.json').read_text())['promoted_ids'];write(ROOT/'f2-config-v4.json',c);write(ROOT/'f2-config-v4-receipt.json',{'schema':'BA-SRM8-F2-config-v4-receipt','config':sha(ROOT/'f2-config-v4.json'),'f0_v3':sha(ROOT/'f0-receipt-v3.json'),'f1_v6':sha(ROOT/'f1-receipt-v6.json'),'generator_v2':sha(ROOT/'f2_common_v2.py'),'behavior_loaded':False,'numerical_F2_gate':False})
if __name__=='__main__':main()
