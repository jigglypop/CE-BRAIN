import json
p=r"C:\dev\ce\ce-agi-runtime\paper\6_뇌\국소회로_상태다양체_흐름_대응\repro\wang_propensity_content_split_v1_result_final.json"
d=json.load(open(p,encoding='utf-8'))
def brief(o,pre="",depth=0):
    if depth>2: return
    if isinstance(o,dict):
        for k,v in list(o.items())[:25]:
            if isinstance(v,(dict,list)):
                n=len(v)
                print(f"{pre}{k}: {type(v).__name__}({n})")
                if depth<2: brief(v if isinstance(v,dict) else (v[0] if v and isinstance(v[0],dict) else {}),pre+"  ",depth+1)
            else:
                print(f"{pre}{k}: {str(v)[:140]}")
brief(d)
