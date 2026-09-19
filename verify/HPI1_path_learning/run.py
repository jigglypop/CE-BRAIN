"""Rebuild a baseline and its paired 160-EM refinements; never overwrite evidence."""
from pathlib import Path
import argparse, json, time
import numpy as np
from hpi1 import initialize, make_streams, expectation, maximize, metrics_fast, refine, crossing, evaluate, assess


def describe(T, curves):
    hits = [crossing(curves[:, i]) for i in (0, 4, 5)]
    complete = all(x is not None for x in hits[1:])
    transfer = assess(T, 'reward_protected', hold=.05, skip=.1, extra=5)
    return dict(complete=complete, first_crossing_off_r2_r1=hits,
                r2_first=bool(hits[1] < hits[2]) if complete else None,
                reward=evaluate(T),
                transfer={k: transfer.get(k) for k in ('valid', 'all_three', 'near_stay_mass', 'far_shift_mass', 'far_reanchor_entry_mass')})


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--seed', type=int, default=262)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--checkpoint', type=Path)
    a = p.parse_args()
    if a.output.exists():
        raise FileExistsError('Choose a new output directory.')
    a.output.mkdir(parents=True)
    start = time.perf_counter()
    if a.checkpoint:
        with np.load(a.checkpoint, allow_pickle=False) as d:
            T, streams, curves = d['transition'].copy(), d['streams'].copy(), d['curves'].copy()
        if T.shape != (8, 8, 100, 100) or curves.shape != (1001, 6) or streams.shape != (50, 520):
            raise ValueError('Expected a frozen 800-state, 1000-update baseline checkpoint.')
    else:
        T = initialize(a.seed)
        streams = make_streams(a.seed)
        history = [metrics_fast(T)]
        for stage, seq in enumerate(streams):
            for _ in range(20):
                counts, _ = expectation(T, seq)
                T = maximize(T, counts)
                history.append(metrics_fast(T))
            print('baseline stage', stage + 1, flush=True)
        curves = np.asarray(history)
    np.savez_compressed(a.output / 'baseline.npz', transition=T, streams=streams, curves=curves)
    result = dict(seed=a.seed, scope='Model phenotype; not neuronal accuracy or MaleCNS.', baseline=describe(T, curves))
    for name, paths in [('plain_continuation', False), ('path_repair', True)]:
        U, tail, events = refine(T.copy(), streams[-1], use_paths=paths)
        all_curves = np.vstack([curves, tail[1:]])
        np.savez_compressed(a.output / (name + '.npz'), transition=U, curves=all_curves)
        result[name] = dict(**describe(U, all_curves), events=events)
    result['elapsed_seconds'] = time.perf_counter() - start
    result['time_contract'] = 'Late refinement is accepted in 40-update blocks, not measured biological time.'
    (a.output / 'RESULT.json').write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    print(json.dumps({k: v['complete'] for k, v in result.items() if isinstance(v, dict) and 'complete' in v}))


if __name__ == '__main__':
    main()
