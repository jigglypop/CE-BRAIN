"""같은 전극의 LP82..89 명령과 전압을 보존하고 입력 변이를 검사한다."""
import argparse
import json
from pathlib import Path
import h5py
import numpy as np
import raw_metadata as raw
from population_reciprocity import sha
from superficial_ee_eligibility import save

HERE=Path(__file__).resolve().parent
INV=HERE/'same_cell_intrinsic_inventory_result.json'
OUT=raw.CACHE/'same_cell_long_pulse'
def txt(v):return v.decode('utf-8') if isinstance(v,bytes) else str(v)
def analyze(v,i,fs):
    assert len(v)==len(i) and np.isfinite(v).all() and np.isfinite(i).all()
    # Preserve exact command segments; avoid an outcome-selected onset threshold.
    bounds=np.r_[0,np.flatnonzero(np.diff(i)!=0)+1,len(i)]
    segments=[{'start_s':float(a/fs),'end_s':float(b/fs),'current_pA':float(i[a]*1e12)} for a,b in zip(bounds[:-1],bounds[1:])]
    return {'command_segments':segments,'voltage_range_mV':[float(v.min()*1000),float(v.max()*1000)],
            'zero_voltage_samples':int(np.sum(v==0)),'samples':len(v)}
def main():
    p=argparse.ArgumentParser();p.add_argument('--verify',action='store_true');args=p.parse_args()
    save('same_cell_long_pulse_contract.json',{
        'question':'Do LP sweeps82..89 contain actual varying current steps on each of the three paired-recording electrodes?',
        'scope':'All24 LP records on electrodes2,4,5; arrays in SI units; no spike detector, rheobase estimate or quality-based postselection.',
        'checks':'record/command electrode, unit, sample rate/start, shape, finite arrays; source conversion including offset; exact command run lengths.',
        'limits':'Electrode continuity is not verified cell stability; baseline holding/current context and full QC required before mechanism fitting.',
        'cache_limit_bytes':128*1024*1024,'inventory_sha256':sha(INV),'reader_sha256':sha(Path(raw.__file__)),'code_sha256':sha(Path(__file__))})
    result_path=HERE/'same_cell_long_pulse_result.json'
    if args.verify:
        result=json.loads(result_path.read_text(encoding='utf-8'))
        assert result['contract_sha256']==sha(HERE/'same_cell_long_pulse_contract.json')
        for row in result['records']:
            path=raw.ROOT/row['array_path'];assert sha(path)==row['array_sha256']
            with np.load(path,allow_pickle=False) as a:assert analyze(a['voltage'],a['current'],row['rate'])==row['analysis']
        print('LONG_PULSE_LOCAL_REPRODUCTION_PASS');return
    if result_path.exists():raise RuntimeError('Preserve completed result; use --verify')
    selected=[r for r in json.loads(INV.read_text(encoding='utf-8'))['records'] if 82<=r['sweep']<=89]
    assert len(selected)==24 and all(r['stimulus']=='Y10_LP_FastRheo_DA_0' for r in selected)
    OUT.mkdir(exist_ok=True);rows=[];raw.LIMIT=128*1024*1024
    with raw.CachedRanges() as reader:
        with h5py.File(reader,'r') as f:
            for r in selected:
                hs=int(r['electrode'].split('_')[-1]);cmdpath=f"/stimulus/presentation/data_{r['sweep']:05d}_DA{hs}"
                target=OUT/f"{r['sweep']}_{hs}.npz";sidecar=target.with_suffix('.json')
                if target.exists() and sidecar.exists():
                    row=json.loads(sidecar.read_text());assert sha(target)==row['array_sha256']
                else:
                    assert not target.exists() and not sidecar.exists(),'Partial asset requires explicit audit'
                    node=f[r['path']];cmd=f[cmdpath]
                    assert txt(node['electrode_name'][()][0])==txt(cmd['electrode_name'][()][0])==r['electrode']
                    assert txt(node['data'].attrs['unit'])=='V' and txt(cmd['data'].attrs['unit'])=='A'
                    assert float(node['starting_time'][()][0])==float(cmd['starting_time'][()][0])==r['start_s']
                    assert float(node['starting_time'].attrs['rate'])==float(cmd['starting_time'].attrs['rate'])==r['rate']
                    def values(ds):return np.asarray(ds[:],dtype=float)*float(ds.attrs['conversion'])+float(ds.attrs.get('offset',0))
                    v,i=values(node['data']),values(cmd['data']);analysis=analyze(v,i,r['rate'])
                    with target.open('xb') as stream:np.savez_compressed(stream,voltage=v,current=i)
                    row={**r,'command_path':cmdpath,'array_path':target.relative_to(raw.ROOT).as_posix(),'array_sha256':sha(target),'analysis':analysis}
                    with sidecar.open('x',encoding='utf-8') as stream:json.dump(row,stream,indent=2)
                rows.append(row);print('cached LP',r['sweep'],hs,flush=True)
        new_bytes=reader.downloaded_this_session
    out={'contract_sha256':sha(HERE/'same_cell_long_pulse_contract.json'),'new_bytes':new_bytes,'records':rows,
         'status':'PASS_ARRAY_BINDING_AND_COMMAND_INVENTORY_NOT_CELL_STABILITY_OR_QC'}
    save('same_cell_long_pulse_result.json',out)
    print('COMPLETE',len(rows),'new_bytes',new_bytes)
if __name__=='__main__':main()
