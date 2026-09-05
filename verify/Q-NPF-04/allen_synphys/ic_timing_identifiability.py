"""기존 20시행의 입력 변이와 spike 상대시각을 재검토한다."""
import json
from pathlib import Path
import numpy as np
from population_reciprocity import sha
from superficial_ee_eligibility import save

HERE=Path(__file__).resolve().parent
command=HERE/'ic_command_context_result.json'
response=HERE/'ic_extension_first_result.json'
save('ic_timing_identifiability_contract.json',{
    'question':'Do existing sweeps37..56 provide distinct input doses, spike failures, and command-to-spike timing variation for a three-channel mechanism analysis?',
    'scope':'Reuse saved command/spike measurements only; no postsynaptic amplitude fitting or window selection.',
    'metrics':'Command height and duration range; spike count distribution; command-to-max-slope lag range/SD; least-squares linear sweep-order trend and residual SD.',
    'interpretation':'Timing variation is not timing precision or causal identification; constant suprathreshold input with one spike each does not estimate an excitability dose-response.',
    'checks':'Exact sweep37..56 correspondence; delay equals max_slope minus command onset; sum of onset lag and offset lag equals pulse duration.',
    'command_sha256':sha(command),'response_sha256':sha(response),'code_sha256':sha(Path(__file__))})
c=json.loads(command.read_text(encoding='utf-8'));r=json.loads(response.read_text(encoding='utf-8'))
edges=c['analysis']['edges'];responses={v['sweep']:v for v in r['analysis']['records']}
assert sorted(responses)==list(range(37,57))==sorted(v['sweep'] for v in edges)
assert len(edges)==20
lags=[];durations=[];heights=[];counts=[];sweeps=[]
for e in edges:
    row=responses[e['sweep']];counts.append(len(row['spikes']))
    assert len(row['spikes'])==1
    lag=(row['spikes'][0]['max_slope_time']-e['command_start_s'])*1000
    duration=(e['command_end_s']-e['command_start_s'])*1000
    assert np.isclose(lag,e['max_slope_after_command_ms'],atol=1e-12)
    assert np.isclose(lag+e['command_end_relative_spike_ms'],duration,atol=1e-12)
    lags.append(lag);durations.append(duration);heights.append(row['command_pA']);sweeps.append(e['sweep'])
lag=np.array(lags);x=np.column_stack([np.ones(20),np.array(sweeps)-np.mean(sweeps)])
beta=np.linalg.lstsq(x,lag,rcond=None)[0];residual=lag-x@beta
assert np.max(np.abs(x.T@residual))<1e-10
out={'contract_sha256':sha(HERE/'ic_timing_identifiability_contract.json'),'sweeps':sweeps,
     'command_height_pA_range':[min(heights),max(heights)],'pulse_duration_ms_range':[min(durations),max(durations)],
     'spike_counts':counts,'lag_ms':lags,'lag_range_ms':[min(lags),max(lags)],
     'lag_sample_sd_ms':float(lag.std(ddof=1)), 'linear_trend_ms_per_sweep':float(beta[1]),
     'detrended_residual_rms_ms':float(np.sqrt(np.mean(residual**2))),
     'sampling_interval_ms':sorted({1000/v['rate'] for v in c['metadata']}),
     'verification':'PASS exact source-event joins, timestamp identities and trend normal equations',
     'claim':'No postsynaptic mechanism separation established; repeated fixed-dose suprathreshold responses and descriptive timing only.'}
save('ic_timing_identifiability_result.json',out)
print(json.dumps(out,indent=2))
