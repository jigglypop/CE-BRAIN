import json,sys,collections,re,os
def load(p):
    with open(p,'r',encoding='utf-8') as f: return json.load(f)

# 1) Hattori imaging cohort: sessions per mouse
cd=load(r"C:\dev\ce\ce-agi-runtime\data\external\hattori_2023_zenodo_10969434\remote_zip_central_directory.json")
def walk_names(o,acc):
    if isinstance(o,dict):
        for k,v in o.items():
            if k in ("name","filename","path") and isinstance(v,str): acc.append(v)
            else: walk_names(v,acc)
    elif isinstance(o,list):
        for v in o: walk_names(v,acc)
names=[]; walk_names(cd,names)
img=[n for n in names if "/Imaging/" in n]
print("HATTORI total members:",len(names),"imaging members:",len(img))
per=collections.Counter()
for n in img:
    m=re.search(r"/Imaging/(RH\d+)/",n)
    if m: per[m.group(1)]+=1
print("HATTORI imaging files per mouse:",dict(per))
# session-date tokens per mouse
sess=collections.defaultdict(set)
for n in img:
    m=re.search(r"/Imaging/(RH\d+)/([^/]+)/(\d{6})_",n)
    if m: sess[m.group(1)].add((m.group(2),m.group(3)))
print("HATTORI imaging (plane,date) sessions per mouse:",{k:len(v) for k,v in sorted(sess.items())})
for k in sorted(sess): print("   ",k,sorted(sess[k])[:12])
