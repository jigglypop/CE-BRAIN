import json
from pathlib import Path
from funnel_core_v2 import ROOT,sha,write
def main():
 cfg=json.loads((ROOT/'f2-config.json').read_text());cfg['schema']='BA-SRM8-F2-config-v3';cfg['generator_source_convention']='f2_common_v2.py corrected mutually-exclusive finite branches';cfg['promoted_ids']=json.loads((ROOT/'f1-receipt-v5.json').read_text())['promoted_ids'];write(ROOT/'f2-config-v3.json',cfg);write(ROOT/'f2-config-v3-receipt.json',{'schema':'BA-SRM8-F2-config-v3-receipt','config_sha256':sha(ROOT/'f2-config-v3.json'),'script_sha256':sha(Path(__file__)),'manifest_sha256':sha(ROOT/'candidate-manifest.json'),'core_sha256':sha(ROOT/'funnel_core_v2.py'),'f0_v4_sha256':sha(ROOT/'f0-receipt-v4.json'),'f1_v5_sha256':sha(ROOT/'f1-receipt-v5.json'),'generator_v2_sha256':sha(ROOT/'f2_common_v2.py'),'behavior_loaded':False,'numerical_F2_gate':False})
if __name__=='__main__':main()
