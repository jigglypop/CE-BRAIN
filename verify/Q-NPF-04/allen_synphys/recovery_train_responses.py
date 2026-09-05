"""20시행의12개 실제 자극과 발화 후보, 두 표적 반응을 같은 창으로 계산한다."""
import argparse
import json
from pathlib import Path
import h5py
import numpy as np
import raw_metadata as raw
from reference_spike_audit import reference, sha, clean
from superficial_ee_eligibility import save
from same_cell_long_pulse import txt

HERE=Path(__file__).resolve().parent
INV=HERE/'ic_extended_inventory_result.json'
QC=HERE/'ic_full_recording_qc_result.json'
OUT=raw.CACHE/'recovery_train_sources'

def main():
    p=argparse.ArgumentParser();p.add_argument('--verify',action='store_true');args=p.parse_args()
    TSeries,_,manifest=reference()
    from neuroanalysis.spike_detection import detect_ic_evoked_spikes
    save('recovery_train_responses_contract.json',dict(
        question='Do fixed-window contrasts evolve across all12 pulses, separating initial8 and recovery4?',
        selection='All sweeps37..56 and all12 pulses; no outcome selection; one experiment.',
        command='Positive command intervals above half global positive maximum; require12 contiguous pulses and onset matches inventory within1 sample.',
        response='Same prior windows relative to unique finite max-slope spike: [2,8)ms minus[-8,-3)ms; retain both targets and their difference.',
        detector='Pinned neuroanalysis IC detector defaults; local[-10,+12)ms trace around each actual command onset; report missing/multiple.',
        endpoint='Pulse-index counts, mean/median contrasts; recovery onset interval per sweep. No division by noisy first response, STP fit or causal claim.',
        limits='Later-pulse baseline can contain residual prior responses; no deconvolution. Recovery intervals not randomized. Independent spike truth absent.',
        inventory_sha256=sha(INV),target_receipt_sha256=sha(QC),
        source_manifest=manifest,code_sha256=sha(Path(__file__)),reader_sha256=sha(Path(raw.__file__))))
    inventory=[r for r in json.loads(INV.read_text(encoding='utf-8'))['selected'] if 37<=r['sweep']<=56]
    targets={(r['sweep'],r['target']):r for r in json.loads(QC.read_text(encoding='utf-8'))['analysis']['records']}
    assert len(inventory)==20
    OUT.mkdir(exist_ok=True);new_bytes=0
    if not args.verify:
        raw.LIMIT=160*1024*1024
        with raw.CachedRanges() as reader:
            with h5py.File(reader,'r') as f:
                for sw in inventory:
                    dest=OUT/f"{sw['sweep']}.npz";receipt=dest.with_suffix('.json')
                    if dest.exists() and receipt.exists():
                        assert sha(dest)==json.loads(receipt.read_text())['sha256'];continue
                    assert not dest.exists() and not receipt.exists(),'Partial asset requires audit'
                    nodes=[f[sw['nodes']['pre']['path']],f[sw['command']['path']]]
                    arrays=[]
                    for node,unit in zip(nodes,('V','A')):
                        assert txt(node['electrode_name'][()][0])=='electrode_5'
                        assert txt(node['data'].attrs['unit'])==unit
                        assert float(node['starting_time'].attrs['rate'])==sw['nodes']['pre']['rate']
                        assert float(node['starting_time'][()][0])==sw['nodes']['pre']['start_s']
                        ds=node['data'];arrays.append(np.asarray(ds[:],dtype=float)*float(ds.attrs['conversion'])+float(ds.attrs.get('offset',0)))
                    assert arrays[0].shape==arrays[1].shape and all(np.isfinite(x).all() for x in arrays)
                    with dest.open('xb') as stream:np.savez_compressed(stream,voltage=arrays[0],current=arrays[1])
                    with receipt.open('x',encoding='utf-8') as stream:json.dump(dict(sha256=sha(dest),sweep=sw['sweep']),stream)
                    print('cached train',sw['sweep'],flush=True)
            new_bytes=reader.downloaded_this_session
    rows=[];assets=[]
    for sw in inventory:
        sid=sw['sweep'];fs=sw['nodes']['pre']['rate'];dest=OUT/f'{sid}.npz'
        digest=json.loads(dest.with_suffix('.json').read_text())['sha256'];assert sha(dest)==digest
        assets.append(dict(path=dest.relative_to(raw.ROOT).as_posix(),sha256=digest))
        with np.load(dest,allow_pickle=False) as z:pre=z['voltage'];command=z['current']
        active=command>command.max()/2
        starts=np.flatnonzero(np.diff(active.astype(int),prepend=0)==1)
        stops=np.flatnonzero(np.diff(active.astype(int),append=0)==-1)+1
        assert len(starts)==len(stops)==12
        assert np.all(np.abs(starts/fs-np.array(sw['onset_times_s']))<=1/fs+1e-9)
        voltages={}
        for target in ('positive','negative'):
            entry=targets[sid,target];path=raw.ROOT/entry['array_path'];assert sha(path)==entry['array_sha256']
            with np.load(path,allow_pickle=False) as z:voltages[target]=z['voltage']
            assert len(voltages[target])==len(pre)
        for index,(a,b) in enumerate(zip(starts,stops)):
            left=a-round(.01*fs);right=a+round(.012*fs);assert left>=0 and right<len(pre)
            spikes=detect_ic_evoked_spikes(TSeries(pre[left:right],dt=1/fs,t0=-.01,units='V'),(0,(b-a)/fs))
            row=dict(sweep=sid,pulse=index+1,command_start_s=float(a/fs),duration_ms=float((b-a)/fs*1000),
                command_pA=float(command[a]*1e12),recovery_onset_gap_s=float((starts[8]-starts[7])/fs),spikes=clean(spikes),responses={})
            if len(spikes)==1 and spikes[0]['max_slope_time'] is not None and np.isfinite(spikes[0]['max_slope_time']):
                center=a/fs+spikes[0]['max_slope_time']
                assert center-.008>=0 and center+.008<(len(pre)-1)/fs
                for target,v in voltages.items():
                    def mean(lo,hi):return float(np.interp((center+np.arange(lo,hi,1/fs))*fs,np.arange(len(v)),v).mean())
                    row['responses'][target]=(mean(.002,.008)-mean(-.008,-.003))*1e6
                row['difference_uV']=row['responses']['positive']-row['responses']['negative']
            rows.append(row)
    first=json.loads((HERE/'ic_extension_first_result.json').read_text(encoding='utf-8'))['analysis']['records']
    for old in first:
        now=next(r for r in rows if r['sweep']==old['sweep'] and r['pulse']==1)
        assert abs(now['difference_uV']-old['difference_uV'])<1e-5
    summary=[]
    for pulse in range(1,13):
        rr=[r for r in rows if r['pulse']==pulse];values=[r['difference_uV'] for r in rr if 'difference_uV' in r]
        summary.append(dict(pulse=pulse,total=len(rr),usable=len(values),mean_uV=float(np.mean(values)) if values else None,
            median_uV=float(np.median(values)) if values else None,positive=sum(x>0 for x in values)))
    result=dict(contract_sha256=sha(HERE/'recovery_train_responses_contract.json'),assets=assets,records=rows,summary=summary,
        verification='PASS240 command joins and20 prior first-pulse reproductions')
    save('recovery_train_responses_result.json',result)
    print(json.dumps(dict(summary=summary,new_bytes=new_bytes,recovery_gaps_s=sorted({r['recovery_onset_gap_s'] for r in rows})),indent=2))

if __name__=='__main__':main()
