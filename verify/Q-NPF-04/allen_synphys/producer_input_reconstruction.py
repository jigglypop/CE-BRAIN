"""20kHz 후보 입력을 보유 NWB 파형에서 복원한다. 역사적 동일성은 미검증."""
import json
from pathlib import Path
import numpy as np
from reference_spike_audit import reference,sha
from superficial_ee_eligibility import save

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
OUT=ROOT/'data/external/allen_synphys_r21/raw_ranges/1574292898.139/producer_input_candidates.npz'

def main():
    TSeries,_,manifest=reference()
    sources={n:HERE/f for n,f in dict(alignment='producer_alignment_audit_result.json',fits='producer_pulse_fits_result.json',
        targets='ic_full_recording_qc_result.json',inventory='ic_extended_inventory_result.json').items()}
    save('producer_input_reconstruction_contract.json',dict(
        question='Can source-informed20kHz response and baseline candidates be reconstructed from existing target archives?',
        response='DB start, stop at start+50ms or next actual pulse onset, whichever earlier; use inspected code rule.',
        baseline='DB baseline start plus20ms from Allen baseline distributor9711704; historical dependency not established.',
        resampling='Pinned campagnola bbe61 TSeries time_slice and resample20000;2nd-order Bessel cutoff20000Hz then interpolation.',
        limits='Explicit cross-version reconstruction candidate; no DB blobs for direct equality, no claim of historical fit reproduction.',
        checks='Original archive hashes, in-bounds windows, finite output, expected20kHz metadata, constant-signal preservation.',
        source_sha256={n:sha(p) for n,p in sources.items()},dependency_manifest=manifest,
        baseline_source_sha256=sha(HERE/'source_snapshots/neuroanalysis_allen__baseline_distributor.py'),code_sha256=sha(Path(__file__))))
    data={n:json.loads(p.read_text(encoding='utf-8')) for n,p in sources.items()}
    inv={r['sweep']:r for r in data['inventory']['selected']}
    fits={(r['sweep'],r['pulse']):r for r in data['fits']['records']}
    receipts={(r['sweep'],r['target']):r for r in data['targets']['analysis']['records']}
    fixture=TSeries(np.full(5000,-.065),sample_rate=100000,t0=0).resample(20000)
    assert np.max(np.abs(fixture.data+.065))<1e-10
    arrays={};rows=[];cache={}
    for r in data['alignment']['records']:
        sw,pulse=r['sweep'],r['pulse'];fit=fits[sw,pulse]
        if sw not in cache:
            receipt=receipts[sw,'positive'];path=ROOT/receipt['array_path'];assert sha(path)==receipt['array_sha256']
            with np.load(path,allow_pickle=False) as z:v=z['voltage']
            cache[sw]=TSeries(v,sample_rate=inv[sw]['nodes']['positive']['rate'],t0=0)
        trace=cache[sw]
        start=fit['pulse_response']['data_start_time']
        windows={'response':(start,start+r['inferred_response_duration_s']),
                 'baseline':(r['baseline']['start_s'],r['baseline']['start_s']+.02)}
        entries={}
        for label,(a,b) in windows.items():
            assert 0<=a<b<=len(trace)/trace.sample_rate
            raw=trace.time_slice(a,b);down=raw.resample(20000)
            assert down.sample_rate==20000 and np.isfinite(down.data).all()
            key=f'{sw}_{pulse}_{label}';arrays[key]=down.data
            entries[label]=dict(key=key,requested_start_s=a,requested_stop_s=b,actual_start_s=float(down.t0),
                samples=len(down),sample_rate=float(down.sample_rate),raw_samples=len(raw))
        rows.append(dict(sweep=sw,pulse=pulse,spike_time_s=fit['stim_pulse']['first_spike_time'],arrays=entries))
    assert len(arrays)==480
    if OUT.exists():
        with np.load(OUT,allow_pickle=False) as saved:
            assert set(saved.files)==set(arrays)
            for key,val in arrays.items():assert np.array_equal(saved[key],val)
    else:
        with OUT.open('xb') as stream:np.savez_compressed(stream,**arrays)
    result=dict(contract_sha256=sha(HERE/'producer_input_reconstruction_contract.json'),array_path=OUT.relative_to(ROOT).as_posix(),array_sha256=sha(OUT),records=rows,
        status='RECONSTRUCTION_CANDIDATE_NOT_HISTORICAL_EQUALITY',new_download_bytes=0)
    save('producer_input_reconstruction_result.json',result)
    print('CANDIDATE_ARRAYS',len(arrays),'BYTES',OUT.stat().st_size)
    print('RESPONSE_SIZES',sorted({r['arrays']['response']['samples'] for r in rows}))
    print('BASELINE_SIZES',sorted({r['arrays']['baseline']['samples'] for r in rows}))

if __name__=='__main__':main()
