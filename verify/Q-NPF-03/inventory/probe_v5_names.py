import re,os
# MATLAB v5: scan first N bytes for plausible ASCII variable/field names (no array values loaded)
targets=[
 r"C:\dev\ce\ce-agi-runtime\data\external\tsimring_adolescent_v1_2025\tracked_spines_properties_table.mat",
 r"C:\dev\ce\ce-agi-runtime\data\external\tsimring_adolescent_v1_2025\soma_properties_table.mat",
 r"C:\dev\ce\ce-agi-runtime\data\external\tan_v1_development_2021\data_CB21.mat",
]
pat=re.compile(rb"[A-Za-z][A-Za-z0-9_]{2,40}")
for p in targets:
    if not os.path.exists(p): print("MISSING",p); continue
    with open(p,'rb') as f: buf=f.read(3_000_000)
    seen=[]; s=set()
    for m in pat.finditer(buf[128:]):
        w=m.group().decode('latin-1')
        if w in s: continue
        s.add(w); seen.append(w)
    print(f"\n=== {os.path.basename(p)} ({os.path.getsize(p):,} B) first-3MB ASCII tokens ({len(seen)} uniq):")
    print("   ", ", ".join(seen[:120]))
