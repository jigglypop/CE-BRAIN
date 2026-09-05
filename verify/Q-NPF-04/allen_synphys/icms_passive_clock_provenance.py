"""비과제군 절단·연결 시간축과 기록 범위 출처 감사."""
import hashlib,json
from pathlib import Path
import h5py
import numpy as np
from population_reciprocity import ROOT,sha
from superficial_ee_eligibility import save
HERE=Path(__file__).resolve().parent
def main():
    base=ROOT/'data/external/xie_icms_plasticity_2025';tree=json.loads((base/'author_repo_tree_20260905.json').read_text(encoding='utf-8'))
    entries={r['path']:r for r in tree['tree']};sources=[]
    for name in ['processing/control/stage1_sort.py','processing/util/load_control.py']:
        p=base/'code'/name;b=p.read_bytes();blob=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
        normalization='none'
        if blob!=entries[name]['sha']:
            normalized=b.replace(b'\r\n',b'\n')
            blob=hashlib.sha1(b'blob '+str(len(normalized)).encode()+b'\0'+normalized).hexdigest()
            normalization='CRLF to LF for Git comparison only'
        assert blob==entries[name]['sha']
        sources.append(dict(path=name,sha256=sha(p),git_blob=blob,normalization=normalization))
    c=json.loads((HERE/'icms_passive_first_sessions_contract.json').read_text(encoding='utf-8'));rows=[]
    for a in c['selected']:
        p=base/Path(a['path']).name
        with h5py.File(p,'r') as f:
            st=f['intervals/electrical_stimulation'];first=st['start_time'][:][st['burst_index_in_trial'][:]==0]
            names=[];f.visit(names.append)
            decode=lambda v:v.decode('utf-8') if isinstance(v,bytes) else str(v)
            rows.append(dict(path=a['path'],sha256=sha(p),first_burst_count=len(first),
                first_burst_spacing_quantiles=np.quantile(np.diff(first),[0,.5,1]).tolist(),
                acquisition_items=list(f['acquisition'].keys()),obs_intervals_present='units/obs_intervals' in f,
                invalid_times_present='intervals/invalid_times' in f,
                exact_condensed_trials_paths=[n for n in names if 'condensed_trials' in n],
                session_description=decode(f['session_description'][()]),experiment_description=decode(f['general/experiment_description'][()])))
    save('icms_passive_clock_provenance_result.json',dict(code_sha256=sha(Path(__file__)),author_tree_sha=tree['sha'],sources=sources,sessions=rows,
        source_findings=['stage1_sort slices around each stimulus start +/-5s, clips to original recording bounds, stitches and remaps timestamps, saves condensed_trials.csv',
                         'load_control drops zero-current rows in MAT-backed branch; fallback groups NEV pulses and assigns survey current'],
        interpretation='Public source verified against author tree. Actual NWB conversion and per-trial retained interval map not established. Regular spacing is compatible with condensed time, not proof of natural experimental spacing.',
        endpoint_status='POSTTRAIN_RESPONSE_NOT_EVALUATED_PENDING_OBSERVATION_SUPPORT'))
    for r in rows:print(r['path'],r['first_burst_spacing_quantiles'],'obs',r['obs_intervals_present'],'acq',r['acquisition_items'])
if __name__=='__main__':main()
