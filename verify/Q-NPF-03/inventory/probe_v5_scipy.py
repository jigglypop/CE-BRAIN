import scipy.io as sio, os, sys
p=r"C:\dev\ce\ce-agi-runtime\data\external\tsimring_adolescent_v1_2025\soma_properties_table.mat"
try:
    d=sio.loadmat(p, struct_as_record=False, squeeze_me=True)
    ks=[k for k in d if not k.startswith('__')]
    print("top vars:",ks)
    for k in ks:
        v=d[k]
        print("  ",k,type(v).__name__,getattr(v,'shape',None),getattr(v,'dtype',None))
        if hasattr(v,'_fieldnames'): print("     fields:",v._fieldnames[:40])
except Exception as e:
    print("FAIL",type(e).__name__,str(e)[:300])
