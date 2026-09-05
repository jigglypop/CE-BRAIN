"""보유 IC 창에서 관측 가능한 품질 항목만 점검한다. 원 QC 통과를 대체하지 않는다."""
import json
from pathlib import Path
import numpy as np
from reference_spike_audit import sha
from raw_metadata import CACHE

HERE = Path(__file__).resolve().parent
OUTPUT = HERE / 'ic_local_quality_result.json'
SOURCE = HERE / 'qc_sources/pulse_qc.py'


def analyze():
    assert sha(SOURCE) == '27cdf2753740d860ccd5e94b0f8745b7bce7288a914c0be43575280c14da887a'
    previous = json.loads((HERE / 'ic_pair_comparison_result.json').read_text(encoding='utf-8'))
    archive = CACHE / 'ic_positive_negative_windows.npz'
    assert sha(archive) == previous['arrays_sha256']
    rows = []
    with np.load(archive, allow_pickle=False) as arrays:
        for old in previous['records']:
            for target in ('positive', 'negative'):
                v = arrays[f"sweep{old['sweep']}_pulse{old['pulse']}_{target}"]
                # Local extraction begins at command -10ms; its first 5ms is baseline.
                base = v[:500]
                median = float(np.median(base))
                sd = float(base.std())
                maximum = float(v.max())
                excursion = float(np.max(np.abs(v-median)))
                failures = []
                if sd > .0015: failures.append('baseline_sd')
                if maximum > -.040: failures.append('peak_voltage')
                if excursion > .010: failures.append('excursion')
                if not -.085 < median < -.050: failures.append('ex_baseline_range')
                rows.append(dict(sweep=old['sweep'], pulse=old['pulse'], target=target,
                    baseline_mV=median*1000, baseline_sd_uV=sd*1e6,
                    peak_mV=maximum*1000, excursion_mV=excursion*1000,
                    local_failures=failures))
    summaries = {}
    for target in ('positive', 'negative'):
        selected = [r for r in rows if r['target']==target]
        summaries[target] = {'windows':len(selected),
            'local_failure_count':sum(bool(r['local_failures']) for r in selected),
            **{field:[min(r[field] for r in selected),max(r[field] for r in selected)]
               for field in ('baseline_mV','baseline_sd_uV','peak_mV','excursion_mV')}}
    return dict(status='PARTIAL_QC_ONLY', timing='Post-result diagnostic; no exclusions or revised response estimates',
        upstream_commit='b187927abf1e8df46d11b47eeb88c8e2c76aee3c',
        source_sha256=sha(SOURCE), arrays_sha256=sha(archive), code_sha256=sha(Path(__file__)),
        window='command[-10,+12)ms; first5ms local baseline; not verified original producer response window',
        missing=['full-recording baseline current/potential/noise', 'whole-sweep zero fraction',
                 'producer pulse windows and original QC outcomes', 'complete adjacent-stimulus context',
                 'independent biological spike truth and access-resistance assessment'],
        summaries=summaries, records=rows)


if __name__ == '__main__':
    result = analyze()
    if OUTPUT.exists():
        assert result == json.loads(OUTPUT.read_text(encoding='utf-8'))
        print('LOCAL_QUALITY_REPRODUCED')
    else:
        with OUTPUT.open('x', encoding='utf-8') as stream:
            json.dump(result, stream, ensure_ascii=False, indent=2, allow_nan=False)
    print(json.dumps(result['summaries'], indent=2))
