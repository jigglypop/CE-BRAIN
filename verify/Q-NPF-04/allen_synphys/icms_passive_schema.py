"""비과제 첫 세션의 자극·기록 시간 범위 감사."""
import json
from pathlib import Path
import h5py
import numpy as np
from population_reciprocity import ROOT,sha
from superficial_ee_eligibility import save
HERE=Path(__file__).resolve().parent
def main():
    cp=HERE/'icms_passive_first_sessions_contract.json';c=json.loads(cp.read_text(encoding='utf-8'));results=[]
    base=ROOT/'data/external/xie_icms_plasticity_2025'
    for a in c['selected']:
        p=base/Path(a['path']).name;m=json.loads((base/('passive_'+a['asset_id']+'_metadata.json')).read_text(encoding='utf-8'))
        assert p.stat().st_size==a['size'] and sha(p)==m['digest']['dandi:sha2-256']
        with h5py.File(p,'r') as f:
            datasets=[]
            def visit(n,o):
                if isinstance(o,h5py.Dataset):datasets.append(dict(path=n,shape=list(o.shape),dtype=str(o.dtype),description=str(o.attrs.get('description',''))))
            f.visititems(visit)
            st=f['intervals/electrical_stimulation'];tr=f['intervals/trials'];s=st['start_time'][:];e=st['stop_time'][:];sp=f['units/spike_times'][:]
            windows=[(-.7,-.2),(.8,1.3)]
            overlaps=[sum(bool(np.any((s<t+b)&(e>t+a))) for t in s) for a,b in windows]
            row=dict(path=a['path'],sha256=sha(p),units=len(f['units/id']),spikes=len(sp),trials=len(tr['id']),bursts=len(s),
                frequency_hz=np.unique(st['frequency_hz'][:]).tolist(),pulse_counts=np.unique(st['pulse_count'][:]).tolist(),
                duration_quantiles=np.quantile(e-s,[0,.5,1]).tolist(),burst_indices=np.unique(st['burst_index_in_trial'][:]).tolist(),
                start_first=s[:6].tolist(),stop_first=e[:6].tolist(),spike_range=[float(sp.min()),float(sp.max())],
                stim_range=[float(s.min()),float(e.max())],trial_range=[float(tr['start_time'][:].min()),float(tr['stop_time'][:].max())],
                task_window_train_overlap_counts=overlaps,catch_trials=int((tr['current_uA'][:]==0).sum()) if 'current_uA' in tr else None,
                session_description=str(f['session_description'][()]),datasets=datasets)
            results.append(row)
            print({k:v for k,v in row.items() if k not in ('datasets','sha256')})
    save('icms_passive_schema_result.json',dict(contract_sha256=sha(cp),code_sha256=sha(Path(__file__)),sessions=results))
if __name__=='__main__':main()
