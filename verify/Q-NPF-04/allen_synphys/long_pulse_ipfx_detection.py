"""고정 IPFX 판본과 기본 검출 조건으로 LP 발화 후보를 산출한다."""
import json
import platform
import sys
from pathlib import Path
import numpy as np
import scipy
from population_reciprocity import ROOT,sha
from superficial_ee_eligibility import save

HERE=Path(__file__).resolve().parent
wheel=ROOT/'data/external/analysis_tools/ipfx_download/ipfx-2.1.2-py3-none-any.whl'
source=HERE/'same_cell_long_pulse_result.json'
params={'start':0.05,'end':1.05,'filter':10.,'dv_cutoff':20.,'max_interval':0.005,
        'min_height':2.,'min_peak':-30.,'thresh_frac':0.05,'reject_at_stim_start_interval':0}
save('long_pulse_ipfx_detection_contract.json',{
    'question':'What spike candidates does fixed IPFX detect in the 24 saved long-pulse records?',
    'source':'IPFX2.1.2 wheel, not verified historical r2.1 environment; SpikeFeatureExtractor only, not full producer QC/intrinsic pipeline.',
    'parameters':params,'units':'t seconds, voltage mV, current pA; original relative time and recorded command preserved.',
    'selection':'All24 records; active steps and zero-command controls separate; clipped spikes retained and flagged.',
    'checks':'Array SHA and finite data; flat input gives zero events; translated time origin preserves peak count and timing.',
    'limits':'No independent spike truth, no cell-stability/full QC or calibrated rheobase; no fit to DB targets.',
    'wheel_sha256':sha(wheel),'input_sha256':sha(source),'code_sha256':sha(Path(__file__)),
    'runtime':{'python':platform.python_version(),'numpy':np.__version__,'scipy':scipy.__version__}})
sys.path.insert(0,str(wheel))
from ipfx.feature_extractor import SpikeFeatureExtractor
records=json.loads(source.read_text(encoding='utf-8'))['records'];out=[]
for row in records:
    path=ROOT/row['array_path'];assert sha(path)==row['array_sha256']
    with np.load(path,allow_pickle=False) as a:v=a['voltage']*1000;i=a['current']*1e12
    t=np.arange(len(v))/row['rate'];assert np.isfinite(v).all() and np.isfinite(i).all()
    peaks=SpikeFeatureExtractor(**params).process(t,v,i)
    if not out:
        assert len(SpikeFeatureExtractor(**params).process(t,np.full(len(t),-65.),np.zeros(len(t))))==0
    moved=SpikeFeatureExtractor(**{**params,'start':0.15,'end':1.15}).process(t+.1,v,i)
    assert len(peaks)==len(moved)
    if len(peaks):assert np.allclose(peaks['peak_t'].to_numpy()+.1,moved['peak_t'].to_numpy(),atol=1e-10)
    segments=row['analysis']['command_segments']
    out.append({'sweep':row['sweep'],'electrode':row['electrode'],'active_command':len(segments)>1,
                'step_pA':segments[1]['current_pA'] if len(segments)>1 else 0.,'spike_candidates':len(peaks),
                'clipped_candidates':int(peaks['clipped'].sum()) if len(peaks) else 0,
                'peak_times_s':peaks['peak_t'].tolist() if len(peaks) else [],
                'threshold_times_s':peaks['threshold_t'].tolist() if len(peaks) else [],
                'peak_voltage_mV':peaks['peak_v'].tolist() if len(peaks) else []})
result={'contract_sha256':sha(HERE/'long_pulse_ipfx_detection_contract.json'),'records':out,
        'verification':'PASS exact archive hashes, flat trace and all24 time-origin checks',
        'claim':'Fixed current-release algorithm candidates; not independent biological verification or full historical pipeline reproduction'}
save('long_pulse_ipfx_detection_result.json',result)
for r in out:print(r['sweep'],r['electrode'],round(r['step_pA']),r['spike_candidates'],r['clipped_candidates'])
print(result['verification'])
