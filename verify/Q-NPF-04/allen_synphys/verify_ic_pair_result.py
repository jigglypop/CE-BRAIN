"""봉인 소스를 유지하며 JSON의 tuple→list 변환을 반영해 재현을 검사한다."""
import json
from pathlib import Path
import numpy as np
import ic_pair_comparison as a

spec = json.loads(a.CONTRACT.read_text(encoding='utf-8'))
result = json.loads(a.OUTPUT.read_text(encoding='utf-8'))
ipath = a.HERE / 'ic_recovery_inventory_result.json'
archive = a.CACHE / 'ic_positive_negative_windows.npz'
assert a.sha(Path(a.__file__)) == spec['code_sha256']
assert a.sha(ipath) == spec['inventory_sha256']
assert a.sha(a.CONTRACT) == result['contract_sha256']
assert a.sha(archive) == result['arrays_sha256']
assert a.sha(a.HERE / 'recover_ic_pair_result.py') == result['recovery']['code_sha256']
TSeries, _, _ = a.reference()
from neuroanalysis.spike_detection import detect_ic_evoked_spikes
assert a.fixtures(TSeries, detect_ic_evoked_spikes) == spec['fixtures']
with np.load(archive, allow_pickle=False) as arrays:
    assert len(arrays.files) == 240
    rows, summaries = a.summarize(arrays, json.loads(ipath.read_text(encoding='utf-8')), TSeries, detect_ic_evoked_spikes)
# JSON has arrays, not Python tuples. No rounding or numeric tolerance is applied.
assert json.loads(json.dumps(a.clean(rows), allow_nan=False)) == result['records']
assert summaries == result['summaries']
print('IC_PAIR_REPRODUCED: 240 local arrays, 60 pulses, exact numeric equality')
for target in ('positive', 'negative'):
    print(target, 'first_mean_uV', np.mean([s['first_pulse'][target]['voltage_change_uV'] for s in summaries]),
          'all_mean_uV', np.mean([s['all_pulse_'+target+'_uV'] for s in summaries]))
