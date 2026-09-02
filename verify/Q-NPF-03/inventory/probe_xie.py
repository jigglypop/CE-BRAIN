import h5py,numpy as np
p=r"C:\dev\ce\ce-agi-runtime\data\external\xie_icms_plasticity_2025\fig3_final_results_zenodo_v1.mat"
with h5py.File(p,'r') as h:
    for k in h.keys():
        if k=='#refs#': continue
        o=h[k]
        if isinstance(o,h5py.Dataset):
            print(f"{k:28s} shape={o.shape} dtype={o.dtype}")
        else:
            print(f"{k:28s} GROUP keys={list(o.keys())[:12]}")
    # peek small numeric datasets
    for k in ['allDays','allSubset','allROI2Comp','invalidCurr']:
        if k in h and isinstance(h[k],h5py.Dataset):
            d=h[k]
            print(f"\n--- {k} shape={d.shape} dtype={d.dtype}")
            if d.dtype!=object and d.size<200:
                print(np.array(d).ravel()[:60])
