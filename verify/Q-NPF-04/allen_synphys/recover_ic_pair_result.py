"""저장 경로 NameError 뒤 남은 배열에서 결과만 복구한다. 네트워크 접근 없음."""
import json
from pathlib import Path
import numpy as np
import ic_pair_comparison as analysis


def main():
    spec = json.loads(analysis.CONTRACT.read_text(encoding='utf-8'))
    inventory_path = analysis.HERE / 'ic_recovery_inventory_result.json'
    assert analysis.sha(Path(analysis.__file__)) == spec['code_sha256']
    assert analysis.sha(inventory_path) == spec['inventory_sha256']
    inventory = json.loads(inventory_path.read_text(encoding='utf-8'))
    archive = analysis.CACHE / 'ic_positive_negative_windows.npz'
    TSeries, _, _ = analysis.reference()
    from neuroanalysis.spike_detection import detect_ic_evoked_spikes
    assert analysis.fixtures(TSeries, detect_ic_evoked_spikes) == spec['fixtures']
    with np.load(archive, allow_pickle=False) as arrays:
        assert len(arrays.files) == 240
        records, summaries = analysis.summarize(arrays, inventory, TSeries, detect_ic_evoked_spikes)
    manifest = json.loads((analysis.CACHE / 'manifest.json').read_text(encoding='utf-8'))
    result = {
        'contract_sha256': analysis.sha(analysis.CONTRACT),
        'arrays_sha256': analysis.sha(archive),
        'arrays_path': archive.relative_to(analysis.HERE.parents[2]).as_posix(),
        'new_bytes': None,
        'total_cached_bytes': sum(b['bytes'] for b in manifest['blocks'].values()),
        'recovery': {
            'reason': 'Original extraction and analysis finished; result construction failed with undefined ROOT. Frozen code and contract preserved.',
            'network_bytes': 0,
            'original_session_new_bytes': 'Unavailable after process exit; not reconstructed as a measured session count.',
            'code_sha256': analysis.sha(Path(__file__)),
        },
        'records': analysis.clean(records),
        'summaries': summaries,
    }
    with analysis.OUTPUT.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2, allow_nan=False)
    print(json.dumps(summaries, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
