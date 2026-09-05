"""합성곱 대신 가능한 블록 통계량 조합을 직접 열거하여 정확한 분포를 검증한다."""
import itertools
import json
import math
from collections import Counter
from pathlib import Path
from reference_spike_audit import sha

HERE = Path(__file__).resolve().parent
rp = HERE / 'microns_disjoint_result.json'
dp = HERE / 'microns_disjoint_rows.json'
result, detail = json.loads(rp.read_text()), json.loads(dp.read_text())
assert result['detail_sha256'] == sha(dp)
checked, combinations = 0, 0
for partition in detail['partitions']:
    cells = [i for r in partition['rows'] for i in r['indices']]
    assert sorted(cells) == list(range(1348))
    for kind in ('degrees', 'joint'):
        fixed_sum, fixed_weight, choices = 0, 1, []
        for r in partition['rows']:
            h = [(int(k), v) for k, v in r[kind]['histogram'].items()]
            assert sum(v for k, v in h) == len(r[kind]['admissible_states'])
            if len(h) == 1:
                fixed_sum += h[0][0]
                fixed_weight *= h[0][1]
            else:
                choices.append(h)
        actual = Counter()
        for choice in itertools.product(*choices):
            actual[fixed_sum + sum(k for k, v in choice)] += fixed_weight * math.prod(v for k, v in choice)
            combinations += 1
        expected = next(r for r in result['results'] if all(r[k] == partition[k] for k in ('arm', 'seed', 'threshold')) and r['constraints'] == kind)
        assert actual == Counter({int(k): int(v) for k, v in expected['histogram'].items()})
        checked += 1
receipt = dict(result_sha256=sha(rp), detail_sha256=sha(dp), verifier_sha256=sha(Path(__file__)),
               distributions_verified=checked, directly_enumerated_statistic_combinations=combinations,
               scope='partition uniqueness and weighted statistic-product distribution; not independent re-enumeration of every local graph',
               status='DIRECT_WEIGHTED_PRODUCT_MATCH')
out = HERE / 'microns_disjoint_verification.json'
if out.exists():
    assert json.loads(out.read_text()) == receipt
else:
    out.write_text(json.dumps(receipt, indent=2), encoding='utf-8')
print(json.dumps(receipt, indent=2))
