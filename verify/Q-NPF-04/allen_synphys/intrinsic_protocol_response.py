"""36파형에서 프로토콜별 발화 후보와 음전류 전압 반응을 계산한다."""
import json
import platform
import sys
from pathlib import Path
import numpy as np
import scipy
from population_reciprocity import ROOT, sha
from superficial_ee_eligibility import save

HERE=Path(__file__).resolve().parent
SOURCE=HERE/'intrinsic_waveforms_result.json'
WHEEL=ROOT/'data/external/analysis_tools/ipfx_download/ipfx-2.1.2-py3-none-any.whl'

def main():
    legacy=json.loads((HERE/'long_pulse_ipfx_detection_contract.json').read_text(encoding='utf-8'))
    assert sha(WHEEL)==legacy['wheel_sha256']
    parameters={k:v for k,v in legacy['parameters'].items() if k not in ('start','end')}
    save('intrinsic_protocol_response_contract.json',dict(
        question='What spike candidates and negative-current voltage responses occur within each intrinsic protocol?',
        population='All36 saved records, one experiment, devices2/4/5. No pooled early-late fitting or independent-replicate inference.',
        input='Recorded relative command in pA, voltage in mV, time in seconds; holding not added.',
        pulse='Require exact recorded nonzero plateau boundaries at DB rounded Epoch1 indices, then detect over that actual interval.',
        parameters=parameters, endpoint='Per-record spike count, clipping, latency, peak times; negative-current zero-candidate deltaV/deltaI descriptive chord response.',
        voltage_windows='Median over50ms before main pulse and final100ms of main pulse. No access/bridge correction or tau fit.',
        checks='Input/archive hashes; exact command segment; flat fixture; translated time-origin invariance for all36.',
        limits='No calibrated rheobase, independent spike truth, historical pipeline reproduction or causal identification. Zero candidates does not prove no spikes.',
        source_sha256=sha(SOURCE),wheel_sha256=sha(WHEEL),code_sha256=sha(Path(__file__)),
        runtime=dict(python=platform.python_version(),numpy=np.__version__,scipy=scipy.__version__)))
    sys.path.insert(0,str(WHEEL))
    from ipfx.feature_extractor import SpikeFeatureExtractor
    result=json.loads(SOURCE.read_text(encoding='utf-8'));out=[]
    assert len(result['records'])==36
    for r in result['records']:
        path=ROOT/r['array_path'];assert sha(path)==r['array_sha256']
        with np.load(path,allow_pickle=False) as archive:
            v=archive['voltage']*1000;i=archive['current']*1e12
        assert np.isfinite(v).all() and np.isfinite(i).all()
        a,b=r['comparison']['start_index'],r['comparison']['stop_index'];fs=r['rate']
        assert 0<a<b<len(i) and i[a]!=i[a-1] and i[b]!=i[b-1]
        assert np.all(i[a:b]==i[a]) and i[a]!=0
        t=np.arange(len(v))/fs
        params={**parameters,'start':a/fs,'end':b/fs}
        spikes=SpikeFeatureExtractor(**params).process(t,v,i)
        shifted=SpikeFeatureExtractor(**{**params,'start':a/fs+.125,'end':b/fs+.125}).process(t+.125,v,i)
        assert len(spikes)==len(shifted)
        if len(spikes):assert np.allclose(spikes['peak_t'].to_numpy()+.125,shifted['peak_t'].to_numpy(),atol=1e-10)
        if not out:assert len(SpikeFeatureExtractor(**params).process(t,np.full(len(t),-65.),np.zeros(len(t))))==0
        delta=float(np.median(v[b-round(.1*fs):b])-np.median(v[a-round(.05*fs):a]))
        step=float(i[a]-np.median(i[a-round(.05*fs):a]))
        out.append(dict(sweep=r['sweep'],device=r['device'],protocol=r['stimulus'],step_pA=step,
            start_s=a/fs,end_s=b/fs,spike_candidates=len(spikes),
            clipped_candidates=int(spikes['clipped'].sum()) if len(spikes) else 0,
            first_threshold_latency_s=float(spikes.iloc[0]['threshold_t']-a/fs) if len(spikes) else None,
            peak_times_s=spikes['peak_t'].tolist() if len(spikes) else [],delta_voltage_mV=delta,
            negative_zero_candidate_chord_Mohm=delta/step*1000 if step<0 and len(spikes)==0 else None))
    save('intrinsic_protocol_response_result.json',dict(contract_sha256=sha(HERE/'intrinsic_protocol_response_contract.json'),
        records=out,verification='PASS36 archive, actual plateau and time-origin checks; flat fixture zero',
        claim='Protocol-specific observational candidates and voltage responses, not validated rheobase or mechanism'))
    for r in out:print(r['sweep'],r['device'],round(r['step_pA'],3),r['spike_candidates'],r['clipped_candidates'],r['negative_zero_candidate_chord_Mohm'])

if __name__=='__main__':main()
