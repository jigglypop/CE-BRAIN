"""거친 격자의 실패를 보존하고 선택된 d,p에서 q만 한 번 세분한다."""
import copy
import json
from pathlib import Path
import numpy as np
import sgsg_calibration_grid as grid

HERE = grid.HERE


def main():
    prior_path = HERE / 'sgsg_grid_selection.json'
    prior_result = HERE / 'sgsg_grid_result.json'
    prior = json.loads(prior_path.read_text())
    assert not prior['selected']['assessment']['pass_all']
    assert json.loads(prior_result.read_text())['reciprocal_endpoint'] is None
    chosen = prior['selected']['parameters']
    assert chosen == dict(dist_neighbors=65., p_pick=.1, step_tgt=1.5)
    config, geometry, spread = grid.source.load_modules()
    grid.STORE = grid.source.base.ROOT / 'data/external/sgsg_local_calibration'
    grid.CONTRACT = HERE / 'sgsg_local_calibration_contract.json'
    spec = dict(question='Can one predeclared local q refinement repair density without losing the other four adequacy conditions?',
                design='Adaptive exploratory followup after coarse grid; all observed data already inspected; new simulation seeds, no biological holdout',
                fixed=dict(dist_neighbors=65., p_pick=.1), q_values=[1.55,1.60,1.65,1.70,1.75,1.80,1.85,1.90,1.95],
                calibration_seeds=list(range(2026091900, 2026091916)), evaluation_seeds=list(range(2026092000, 2026092064)),
                score_and_gate='Exactly reuse coarse-grid assess: E20%, distanceTV0.10, in/out SD25%, mean isolated count1; all five required in calibration and evaluation. No reciprocal information in calibration.',
                selection='Lowest score among fully executed candidates; tie by ascendingq; evaluate only selected candidate. No further refinement within this contract.',
                endpoint='Only after both adequacy gates pass: descriptive reciprocal count mean/range and observed-minus-mean; no tail p-value or hypothesis confirmation',
                prior_selection_sha256=grid.source.base.sha(prior_path), prior_result_sha256=grid.source.base.sha(prior_result),
                prior_contract_sha256=grid.source.base.sha(HERE / 'sgsg_calibration_grid_contract.json'),
                code_sha256=grid.source.base.sha(Path(__file__)), shared_code_sha256=grid.source.base.sha(Path(grid.__file__)),
                archive_sha256=grid.source.base.sha(grid.source.ARCHIVE))
    grid.source.write_once(grid.CONTRACT, spec)
    roots, xyz, a, bins = grid.source.data()
    target = grid.features(a, bins)
    grid.STORE.mkdir(exist_ok=True)
    candidates = []
    for i, q in enumerate(spec['q_values']):
        cfg = copy.deepcopy(config)
        cfg['nngraph'].update(spec['fixed'])
        cfg['instance']['step_tgt'] = q
        records = [grid.sample(cfg, geometry, spread, roots, xyz, bins, f'q{i:02}', seed) for seed in spec['calibration_seeds']]
        candidate = dict(index=i, parameters=dict(**spec['fixed'], step_tgt=q), assessment=grid.assess(records,target),
                         receipts=[f'{r["label"]}_{r["seed"]}.json' for r in records])
        candidates.append(candidate)
        print(json.dumps({k:v for k,v in candidate.items() if k != 'receipts'}), flush=True)
    eligible = [r for r in candidates if r['assessment']['eligible']]
    best = min(eligible, key=lambda r:(r['assessment']['score'],r['index'])) if eligible else None
    selection = dict(contract_sha256=grid.source.base.sha(grid.CONTRACT), observed_features=target, candidates=candidates, selected=best)
    grid.source.write_once(HERE / 'sgsg_local_selection.json', selection)
    evaluation = None
    endpoint = None
    if best is not None:
        cfg = copy.deepcopy(config)
        cfg['nngraph'].update(spec['fixed'])
        cfg['instance']['step_tgt'] = best['parameters']['step_tgt']
        records = [grid.sample(cfg, geometry, spread, roots, xyz, bins, 'evaluation', seed) for seed in spec['evaluation_seeds']]
        evaluation = grid.assess(records,target)
        evaluation['receipts'] = [f'{r["label"]}_{r["seed"]}.json' for r in records]
        if best['assessment']['pass_all'] and evaluation['pass_all']:
            values=[]
            for r in records:
                with np.load(grid.STORE / f'{r["label"]}_{r["seed"]}.npz',allow_pickle=False) as f:
                    g=f['adjacency']
                values.append(int((g & g.T).sum()//2))
            obs=int((a & a.T).sum()//2)
            endpoint=dict(observed=obs,simulated=values,mean=float(np.mean(values)),
                          observed_minus_mean=obs-float(np.mean(values)),
                          range=[min(values),max(values)],
                          interpretation='Descriptive adaptive-model comparison, not a conditional null or biological validation')
    result=dict(selection_sha256=grid.source.base.sha(HERE / 'sgsg_local_selection.json'),evaluation=evaluation,
                reciprocal_endpoint=endpoint,status='ADEQUACY_PASS_DESCRIPTIVE_ONLY' if endpoint is not None else 'RECIPROCITY_NOT_EVALUATED_ADEQUACY_FAILED',
                receipt_sha256={p.name:grid.source.base.sha(p) for p in sorted(grid.STORE.glob('*.json'))})
    grid.source.write_once(HERE / 'sgsg_local_result.json',result)
    print(json.dumps({k:v for k,v in result.items() if k!='receipt_sha256'}),flush=True)


if __name__ == '__main__':
    main()
