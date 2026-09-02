import json,collections
p=r"C:\dev\ce\ce-agi-runtime\data\external\hattori_2023_zenodo_10969434\selected_npz_schema_headers.json"
d=json.load(open(p,encoding='utf-8'))
print("status:",d.get("status"),"file_count:",d.get("file_count"),"distinct_schema:",d.get("distinct_schema_count"))
keys=collections.Counter(); shapes=collections.defaultdict(set)
for f in d.get("files",[]):
    for a in f.get("arrays",[]):
        keys[a["key"]]+=1; shapes[a["key"]].add(tuple(a["shape"]))
for k,c in keys.most_common(40):
    s=list(shapes[k])[:3]
    print(f"  {k:28s} n={c:4d} shapes~{s}")
paths=[f["path"] for f in d.get("files",[])]
print("sample paths:",paths[:5]); print("n paths:",len(paths))
