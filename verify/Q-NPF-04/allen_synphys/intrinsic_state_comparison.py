"""보유한 36기록의 초기·후기 test-pulse를 기술 비교한다. 추론 검정은 하지 않는다."""
import json
import hashlib
from pathlib import Path
from statistics import median
from datetime import datetime

HERE = Path(__file__).resolve().parent

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    contract_path = HERE / 'intrinsic_test_pulse_binding_contract.json'
    result_path = HERE / 'intrinsic_test_pulse_binding_result.json'
    contract = json.loads(contract_path.read_text(encoding='utf-8'))
    result = json.loads(result_path.read_text(encoding='utf-8'))
    assert result['contract_sha256'] == sha(contract_path)
    assert contract['code_sha256'] == sha(HERE / 'intrinsic_test_pulse_binding.py')
    assert contract['source_sha256'] == sha(HERE / 'medium_recording_lookup_result.json')
    prior = json.loads((HERE / 'medium_recording_lookup_result.json').read_text(encoding='utf-8'))
    records = {(r['sweep'], r['device']): r for r in prior['records']}
    assert len(records) == len(result['records']) == 36
    expected = {(s, d) for s in list(range(7, 13)) + list(range(90, 96)) for d in (2, 4, 5)}
    assert set(records) == {(r['sweep'], r['device']) for r in result['records']} == expected
    summaries = []
    for device in (2, 4, 5):
        groups = {}
        for name, sweeps in [('early_TargetV', range(7, 13)), ('late_If_Curve', range(90, 96))]:
            rows = [r for r in result['records'] if r['device'] == device and r['sweep'] in sweeps]
            assert len(rows) == 6
            for r in rows:
                rec = records[r['sweep'], device]['recording']
                assert r['test_pulse']['recording_id'] == rec['id'] == r['test_recording']['id']
                assert r['test_pulse']['electrode_id'] == rec['electrode_id']
                assert r['test_recording']['start_time'] == rec['start_time']
            values = {}
            for field in ('access_resistance', 'input_resistance'):
                x = [r['test_pulse'][field] / 1e6 for r in rows]
                assert all(v > 0 for v in x)
                values[field + '_Mohm'] = dict(min=min(x), median=median(x), max=max(x))
            times = sorted(r['test_recording']['start_time'] for r in rows)
            groups[name] = dict(n=6, first_start=times[0], last_start=times[-1], measurements=values)
        early, late = groups['early_TargetV'], groups['late_If_Curve']
        delta = {k: late['measurements'][k]['median'] - early['measurements'][k]['median'] for k in early['measurements']}
        summaries.append(dict(device=device, groups=groups, late_minus_early_median_Mohm=delta,
            between_block_start_gap_s=(datetime.fromisoformat(late['first_start']) - datetime.fromisoformat(early['last_start'])).total_seconds()))
    output = dict(source_sha256=sha(result_path), code_sha256=sha(Path(__file__)),
        status='DESCRIPTIVE_POSTHOC_COMPARISON',
        scope='One experiment, three electrodes; six records per protocol per electrode; no independent biological replicates or significance test.',
        limits='Protocol and time are confounded. Differences do not identify biological versus recording drift. No stability threshold or exclusions applied.',
        summaries=summaries)
    destination = HERE / 'intrinsic_state_comparison_result.json'
    if destination.exists():
        assert json.loads(destination.read_text(encoding='utf-8')) == output
    else:
        with destination.open('x', encoding='utf-8') as stream:
            json.dump(output, stream, ensure_ascii=False, indent=2)
    print(json.dumps(output, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
