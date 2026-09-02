import os,sys,struct
paths=[
 r"C:\dev\ce\ce-agi-runtime\data\external\xie_icms_plasticity_2025\fig3_final_results_zenodo_v1.mat",
 r"C:\dev\ce\ce-agi-runtime\data\external\tsimring_adolescent_v1_2025\tracked_spines_properties_table.mat",
 r"C:\dev\ce\ce-agi-runtime\data\external\tsimring_adolescent_v1_2025\soma_properties_table.mat",
 r"C:\dev\ce\ce-agi-runtime\data\external\tan_v1_development_2021\data_CB21.mat",
 r"C:\dev\ce\ce-agi-runtime\data\external\hedrick2024_synapse_elimination\selected\Elim_Paper_Repository\Data\GluSnFR3_RCaMP2\JW083_SpineDynamicsSummary.mat",
 r"C:\dev\ce\ce-agi-runtime\data\external\hedrick2024_synapse_elimination\selected\Elim_Paper_Repository\Data\GluSnFR3_RCaMP2\JW083_ElimSpineSummary.mat",
]
for p in paths:
    if not os.path.exists(p):
        print("MISSING",p); continue
    sz=os.path.getsize(p)
    with open(p,'rb') as f: head=f.read(128)
    txt=head[:116].decode('latin-1','replace').strip('\x00').strip()
    ish5 = head[:8]==b'\x89HDF\r\n\x1a\n' or b'MATLAB 7.3' in head
    print(f"\n=== {os.path.basename(p)}  {sz:,} bytes")
    print("   header:",txt[:100])
    print("   hdf5(v7.3):",ish5)
    if ish5:
        try:
            import h5py
            with h5py.File(p,'r') as h:
                def show(name,obj):
                    import h5py as _h
                    if isinstance(obj,_h.Dataset):
                        print(f"     {name}  shape={obj.shape} dtype={obj.dtype}")
                n=[0]
                def cb(name,obj):
                    if n[0]<45: show(name,obj); n[0]+=1
                h.visititems(cb)
                print("     top keys:",list(h.keys())[:30])
        except Exception as e:
            print("   h5py fail:",e)
    else:
        try:
            import scipy.io as sio
            d=sio.whosmat(p)
            for name,shape,cls in d[:40]: print(f"     {name}  shape={shape} class={cls}")
        except Exception as e:
            print("   scipy whosmat fail:",type(e).__name__,e)
