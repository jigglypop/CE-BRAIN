"""원좌표·저장 그래프에서 교정 통계를 복원하고 선택·새 seed 결과를 검증한다."""
import copy
import hashlib
import json
from pathlib import Path
import numpy as np
from scipy.spatial.distance import cdist
import sgsg_calibration_grid as run


def main():
    selection = json.loads((run.HERE / 'sgsg_grid_selection.json').read_text())
    result = json.loads((run.HERE / 'sgsg_grid_result.json').read_text())
    contract = json.loads(run.CONTRACT.read_text())
    assert selection['contract_sha256'] == run.source.base.sha(run.CONTRACT)
    assert result['selection_sha256'] == run.source.base.sha(run.HERE / 'sgsg_grid_selection.json')
    roots, xyz, observed, _ = run.source.data()
    bins = np.digitize(cdist(xyz, xyz), [50, 100, 200, 400, 800])
    valid = 0
    failed = 0
    for name, digest in result['receipt_sha256'].items():
        receipt = run.STORE / name
        assert run.source.base.sha(receipt) == digest
        r = json.loads(receipt.read_text())
        if r['status'] != 'PASS':
            failed += 1
            continue
        path = receipt.with_suffix('.npz')
        assert run.source.base.sha(path) == r['file_sha256']
        with np.load(path, allow_pickle=False) as f:
            a = f['adjacency']
            assert f['roots'].tolist() == roots
        assert a.dtype == bool and not np.diag(a).any()
        assert hashlib.sha256(a.tobytes()).hexdigest() == r['graph_sha256']
        u, v = np.nonzero(a)
        out = np.bincount(u, minlength=len(roots))
        inc = np.bincount(v, minlength=len(roots))
        assert len(u) == r['features']['edges']
        assert np.bincount(bins[u, v], minlength=6).tolist() == r['features']['distance_counts']
        assert np.isclose(np.std(out), r['features']['out_degree_sd'], atol=1e-12)
        assert np.isclose(np.std(inc), r['features']['in_degree_sd'], atol=1e-12)
        assert int(np.sum((out + inc) == 0)) == r['features']['zero_degree_cells']
        valid += 1
    assessments = []
    for candidate in selection['candidates']:
        records = [json.loads((run.STORE / p).read_text()) for p in candidate['receipts']]
        assessment = run.assess(records, selection['observed_features'])
        assert assessment == candidate['assessment']
        if assessment['eligible']:
            assert np.isclose(assessment['score'], np.dot(list(assessment['scaled_errors'].values()), list(assessment['scaled_errors'].values())))
            assessments.append(candidate)
    chosen = min(assessments, key=lambda r: (r['assessment']['score'], r['index']))
    assert chosen == selection['selected']
    assert not set(contract['calibration_seeds']) & set(contract['evaluation_seeds'])
    evaluation = result['evaluation']
    records = [json.loads((run.STORE / p).read_text()) for p in evaluation['receipts']]
    assert run.assess(records, selection['observed_features']) == {k: v for k, v in evaluation.items() if k != 'receipts'}
    replayed = []
    config, geometry, spread = run.source.load_modules()
    config = copy.deepcopy(config)
    params = chosen['parameters']
    config['nngraph'].update({k: params[k] for k in ('dist_neighbors', 'p_pick')})
    config['instance']['step_tgt'] = params['step_tgt']
    for name in [chosen['receipts'][0], evaluation['receipts'][0]]:
        r = json.loads((run.STORE / name).read_text())
        a, diagnostic = run.generate(config, geometry, spread, xyz, r['seed'])
        with np.load((run.STORE / name).with_suffix('.npz'), allow_pickle=False) as f:
            assert np.array_equal(a, f['adjacency'])
        assert diagnostic == r['diagnostic']
        replayed.append(name)
    if not (chosen['assessment']['pass_all'] and evaluation['pass_all']):
        assert result['reciprocal_endpoint'] is None
    output = dict(result_sha256=run.source.base.sha(run.HERE / 'sgsg_grid_result.json'),
                  verifier_sha256=run.source.base.sha(Path(__file__)),
                  verified_graphs=valid, failed_receipts=failed, replayed=replayed,
                  selection_score_verified=True, separate_simulation_seeds=True,
                  biological_holdout=False)
    run.source.write_once(run.HERE / 'sgsg_grid_verification.json', output)
    print(json.dumps(output))


if __name__ == '__main__':
    main()
