"""원 CSV와 전체 설계행렬로 봉인된 ER 강도 계산을 독립 대조한다."""
import csv
import hashlib
import io
import json
import zipfile
from pathlib import Path

import numpy as np
from scipy.linalg import block_diag

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

contract_path = HERE / 'peng2024_er_strength_contract.json'
contract = json.loads(contract_path.read_text(encoding='utf-8'))
result = json.loads((HERE / 'peng2024_er_strength_result.json').read_text(encoding='utf-8'))
archive = ROOT / 'data/external/peng2024_human/data.zip'
assert sha(archive) == contract['archive_sha256']
assert sha(HERE / 'peng2024_er_strength.py') == contract['code_sha256']
assert sha(contract_path) == result['contract_sha256']
with zipfile.ZipFile(archive) as z:
    rows = list(csv.DictReader(io.StringIO(z.read('data/tconnection_er.csv').decode('utf-8-sig'))))
lookup = {(r['cellid_pre'], r['cellid_post']): r for r in rows}
assert len(lookup) == len(rows)
published = result['branches']['author_published']
blocks, flags, values = [], [], []
for record in published['records']:
    selected = [r for r in rows if r['clusterid'] == record['cluster']
                and r['connected'] == '1' and np.isfinite(float(r['avg_psp_amplitude']))
                and float(r['avg_psp_amplitude']) > 0]
    assert len(selected) == record['directions']
    assert {r['patientid'] for r in selected} == {record['patient']}
    senders = sorted({r['cellid_pre'] for r in selected})
    receivers = sorted({r['cellid_post'] for r in selected})
    blocks.append(np.array([[int(r['cellid_pre'] == n) for n in senders]
                           + [int(r['cellid_post'] == n) for n in receivers] for r in selected], float))
    flags.extend(int(lookup[r['cellid_post'], r['cellid_pre']]['connected']) for r in selected)
    values.extend(np.log(float(r['avg_psp_amplitude'])) for r in selected)
x = np.column_stack((block_diag(*blocks), flags))
y = np.array(values)
coef, _, rank, _ = np.linalg.lstsq(x, y, rcond=1e-10)
assert np.isclose(coef[-1], published['beta'], atol=1e-10, rtol=0)
normal_error = float(np.max(np.abs(x.T @ (y - x @ coef))))
assert normal_error < 1e-9
v = published['patients']
num = sum(p[0] for p in v.values())
den = sum(p[1] for p in v.values())
leave = [(num-p[0])/(den-p[1]) for p in v.values()]
assert np.allclose([min(leave), max(leave)], published['leave_one_patient_beta_range'])
out = {'verification': 'PASS', 'method': 'original CSV; block diagonal sender/receiver plus reciprocal column; joint least squares',
       'source_sha256': sha(archive), 'result_sha256': sha(HERE/'peng2024_er_strength_result.json'),
       'verifier_sha256': sha(Path(__file__)), 'informative_directions': len(y),
       'design_shape': list(x.shape), 'rank': int(rank), 'joint_beta': float(coef[-1]),
       'normal_equation_max_error': normal_error,
       'leave_one_patient_ratio_range': [float(np.exp(min(leave))), float(np.exp(max(leave)))],
       'scope': 'Arithmetic verification of published branch; not a new biological replication or missing-data audit'}
target = HERE/'peng2024_er_strength_verification.json'
if target.exists():
    assert json.loads(target.read_text(encoding='utf-8')) == out
else:
    target.write_text(json.dumps(out, indent=2)+'\n', encoding='utf-8')
print(json.dumps(out, indent=2))
