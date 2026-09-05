"""상호연결을 쓰지 않는 SGSG 교정과 별도 난수 표본의 적합성 평가."""
import copy
import hashlib
import itertools
import json
from pathlib import Path
import warnings

import numpy as np
import sgsg_fixed_transfer_seed32 as source

HERE = source.HERE
STORE = source.base.ROOT / 'data/external/sgsg_calibration_grid'
CONTRACT = HERE / 'sgsg_calibration_grid_contract.json'


def features(a, bins):
    """No reciprocal-pair counts, products with transpose, or motif statistics."""
    edges = int(a.sum())
    return dict(edges=edges, distance_counts=np.bincount(bins[a], minlength=6).tolist(),
                out_degree_sd=float(a.sum(1).std()), in_degree_sd=float(a.sum(0).std()),
                zero_degree_cells=int(np.sum((a.sum(0) + a.sum(1)) == 0)))


def assess(records, target):
    if not all(r['status'] == 'PASS' for r in records):
        return dict(eligible=False, score=None, pass_all=False)
    means = {key: float(np.mean([r['features'][key] for r in records]))
             for key in ('edges', 'out_degree_sd', 'in_degree_sd', 'zero_degree_cells')}
    # Mean within-graph distance fractions, not a count-weighted pooled graph.
    fractions = np.mean([np.array(r['features']['distance_counts']) / r['features']['edges'] for r in records], axis=0)
    means['distance_fractions'] = fractions.tolist()
    tv = float(abs(fractions - np.array(target['distance_counts']) / target['edges']).sum() / 2)
    errors = dict(edges=abs(means['edges'] / target['edges'] - 1) / .20,
                  distance_tv=tv / .10,
                  out_degree_sd=abs(means['out_degree_sd'] / target['out_degree_sd'] - 1) / .25,
                  in_degree_sd=abs(means['in_degree_sd'] / target['in_degree_sd'] - 1) / .25,
                  zero_degree_cells=abs(means['zero_degree_cells'] - target['zero_degree_cells']) / 1.0)
    return dict(eligible=True, score=sum(v * v for v in errors.values()),
                pass_all=all(v <= 1 for v in errors.values()), mean_features=means,
                scaled_errors=errors, distance_total_variation=tv)


def generate(config, geometry, spread, xyz, seed):
    np.random.seed(seed)
    original = spread._evaluate_probs_less_random
    diagnostic = {'zero_sum_rows': 0}

    def checked(p_mat, adjust=None):
        m = p_mat.tocsr()
        assert np.isfinite(m.data).all() and (m.data >= 0).all()
        sums = np.asarray(m.sum(axis=1)).ravel()
        scaled = sums if adjust is None else sums * adjust
        assert np.isfinite(scaled).all()
        picks = np.round(scaled).astype(int)
        assert (picks[sums == 0] == 0).all() and (sums[picks > 0] > 0).all()
        diagnostic['zero_sum_rows'] += int(np.sum(sums == 0))
        return original(p_mat, adjust=adjust)

    spread._evaluate_probs_less_random = checked
    try:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter('always')
            m = geometry.cand2_point_nn_matrix(xyz, **config['nngraph'])
            g, history, _ = spread.build_instance(xyz, m, **config['instance'])
        assert all(str(w.message) == 'invalid value encountered in divide' for w in caught)
        assert np.isfinite(g.data).all() and np.isfinite(history).all()
        assert np.isfinite(m.data).all()
        a = g.toarray()
        assert np.isin(a, [0, 1]).all() and not np.diag(a).any()
        assert a.shape == (len(xyz), len(xyz)) and a.sum() > 0
        diagnostic['warning_events'] = len(caught)
        return a.astype(bool), diagnostic
    finally:
        spread._evaluate_probs_less_random = original


def sample(config, geometry, spread, roots, xyz, bins, label, seed):
    receipt = STORE / f'{label}_{seed}.json'
    path = STORE / f'{label}_{seed}.npz'
    if receipt.exists():
        r = json.loads(receipt.read_text())
        assert r['contract_sha256'] == source.base.sha(CONTRACT)
        if r['status'] == 'PASS':
            assert source.base.sha(path) == r['file_sha256']
            with np.load(path, allow_pickle=False) as f:
                assert f['roots'].tolist() == roots
                assert features(f['adjacency'], bins) == r['features']
        return r
    try:
        a, diagnostic = generate(config, geometry, spread, xyz, seed)
        with path.open('xb') as stream:
            np.savez_compressed(stream, adjacency=a, roots=np.array(roots, dtype=np.int64))
        r = dict(status='PASS', features=features(a, bins), diagnostic=diagnostic,
                 graph_sha256=hashlib.sha256(a.tobytes()).hexdigest(), file_sha256=source.base.sha(path))
    except Exception as exc:
        r = dict(status='FAILED', error_type=type(exc).__name__, error=str(exc))
    r.update(contract_sha256=source.base.sha(CONTRACT), seed=seed, label=label)
    source.write_once(receipt, r)
    return r


def main():
    config, geometry, spread = source.load_modules()
    grid = [dict(dist_neighbors=d, p_pick=p, step_tgt=q)
            for d, p, q in itertools.product([35., 47., 65.], [.03, .10, .30], [1.5, 2.325, 3.0])]
    spec = dict(question='Does a bounded SGSG calibration without reciprocity match density, distance and degree variability on the observed 347-cell subvolume?',
                design='Exploratory fit to already inspected biological data; simulation calibration/evaluation seeds are separate, not independent biological holdout',
                grid=grid, calibration_seeds=list(range(2026091700, 2026091708)),
                evaluation_seeds=list(range(2026091800, 2026091832)),
                base_config=config, adaptation='Same as fixed transfer: actual347 coordinates, homogeneous23P, no outside paths or per-subclass biases',
                score='Sum of squared scaled errors of mean features: edges relative/0.20, distance-fraction TV/0.10, out-SD relative/0.25, in-SD relative/0.25, isolated-cell mean absolute/1.0. No reciprocity in score. Lexicographic grid order tie-break.',
                gate='All draws succeed and each scaled error <=1, calibration and evaluation separately; engineering tolerances, not significance tests. Any failed draw disqualifies its candidate; no replacement.',
                selection='Lowest score among executable candidates, even if no candidate passes. Save selection before evaluating32newseeds. No further search in this contract.',
                endpoint='Only if selected candidate passes both adequacy gates, record reciprocal count distribution and observed-minus-mean descriptively; otherwise do not evaluate reciprocal endpoint.',
                code_sha256=source.base.sha(Path(__file__)), loader_sha256=source.base.sha(Path(source.__file__)),
                archive_sha256=source.base.sha(source.ARCHIVE), prior_contract_sha256=source.base.sha(HERE / 'sgsg_fixed_transfer_seed32_contract.json'),
                prior_verification_sha256=source.base.sha(HERE / 'sgsg_transfer_verification.json'),
                environment=json.loads((HERE / 'sgsg_fixed_transfer_seed32_contract.json').read_text())['python'])
    source.write_once(CONTRACT, spec)
    roots, xyz, observed, bins = source.data()
    target = features(observed, bins)
    STORE.mkdir(exist_ok=True)
    candidates = []
    for index, params in enumerate(grid):
        cfg = copy.deepcopy(config)
        cfg['nngraph'].update({k: params[k] for k in ('dist_neighbors', 'p_pick')})
        cfg['instance']['step_tgt'] = params['step_tgt']
        records = [sample(cfg, geometry, spread, roots, xyz, bins, f'c{index:02}', seed) for seed in spec['calibration_seeds']]
        r = dict(index=index, parameters=params, assessment=assess(records, target),
                 receipts=[f'{x["label"]}_{x["seed"]}.json' for x in records])
        candidates.append(r)
        print(json.dumps({k: v for k, v in r.items() if k != 'receipts'}), flush=True)
    eligible = [r for r in candidates if r['assessment']['eligible']]
    best = min(eligible, key=lambda r: (r['assessment']['score'], r['index'])) if eligible else None
    selection = dict(contract_sha256=source.base.sha(CONTRACT), observed_features=target, candidates=candidates, selected=best)
    source.write_once(HERE / 'sgsg_grid_selection.json', selection)
    evaluation = None
    endpoint = None
    if best is not None:
        cfg = copy.deepcopy(config)
        cfg['nngraph'].update({k: best['parameters'][k] for k in ('dist_neighbors', 'p_pick')})
        cfg['instance']['step_tgt'] = best['parameters']['step_tgt']
        records = [sample(cfg, geometry, spread, roots, xyz, bins, 'evaluation', seed) for seed in spec['evaluation_seeds']]
        evaluation = assess(records, target)
        evaluation['receipts'] = [f'{x["label"]}_{x["seed"]}.json' for x in records]
        if best['assessment']['pass_all'] and evaluation['pass_all']:
            mutual = []
            for r in records:
                with np.load(STORE / f'{r["label"]}_{r["seed"]}.npz', allow_pickle=False) as f:
                    a = f['adjacency']
                mutual.append(int((a & a.T).sum() // 2))
            endpoint = dict(observed=int((observed & observed.T).sum() // 2), simulated=mutual,
                            mean=float(np.mean(mutual)), claim='Descriptive fitted-model check only; no confirmatory p-value')
    result = dict(selection_sha256=source.base.sha(HERE / 'sgsg_grid_selection.json'), evaluation=evaluation,
                  reciprocal_endpoint=endpoint,
                  status='ADEQUACY_PASS_DESCRIPTIVE_ONLY' if endpoint is not None else 'RECIPROCITY_NOT_EVALUATED_ADEQUACY_FAILED',
                  receipt_sha256={p.name: source.base.sha(p) for p in sorted(STORE.glob('*.json'))})
    source.write_once(HERE / 'sgsg_grid_result.json', result)
    print(json.dumps({k: v for k, v in result.items() if k != 'receipt_sha256'}), flush=True)


if __name__ == '__main__':
    main()
