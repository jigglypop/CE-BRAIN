"""같은 120블록 시작 상태에서 두 연결 교환과 혼합 교환의 민감도를 비교한다."""
import itertools
import json
from pathlib import Path
import numpy as np
import microns_constrained_swaps as base
from microns_swap_extension import validate

HERE = base.HERE
CONTRACT = HERE / 'microns_three_edge_contract.json'
OUTPUT = HERE / 'microns_three_edge_result.json'
STORE = base.DATA / 'three_edge_sensitivity'


def three(a, edges, indices, direction, categories):
    if len(set(map(int, indices))) != 3:
        return False
    old = [tuple(map(int, edges[i])) for i in indices]
    new = [(old[k][0], old[(k + direction) % 3][1]) for k in range(3)]
    if len(set(new)) != 3 or any(u == v for u, v in new):
        return False
    oldset = set(old)
    if set(new) == oldset or any(a[p] and p not in oldset for p in new):
        return False
    if sorted(int(categories[p]) for p in old) != sorted(int(categories[p]) for p in new):
        return False
    for p in old:
        a[p] = False
    for i, p in zip(indices, new):
        a[p] = True
        edges[i] = p
    return True


def fixtures():
    # Exhaust every ordered edge triple and both rotations for every 3-node graph.
    pairs = [(u, v) for u in range(3) for v in range(3) if u != v]
    accepted = 0
    for mask in range(64):
        a = np.zeros((3, 3), dtype=bool)
        for k, p in enumerate(pairs):
            a[p] = bool(mask & (1 << k))
        c = np.zeros_like(a, dtype=int)
        edges = np.argwhere(a)
        for ids in itertools.permutations(range(len(edges)), 3):
            for direction in (1, -1):
                b, e = a.copy(), edges.copy()
                if three(b, e, ids, direction, c):
                    accepted += 1
                    validate(b, e, a, c)
                    assert three(b, e, ids, -direction, c)
                    assert np.array_equal(a, b) and np.array_equal(edges, e)
    assert accepted > 0
    return accepted


def main():
    fixture_count = fixtures()
    prior_path = HERE / 'microns_swap_extension_result.json'
    prior = json.loads(prior_path.read_text())
    selected = [r for r in prior['chains'] if r['seed'] in base.SEEDS[:2]]
    spec = dict(source_result_sha256=base.sha(prior_path), code_sha256=base.sha(Path(__file__)),
                base_code_sha256=base.sha(Path(base.__file__)),
                validation_code_sha256=base.sha(HERE / 'microns_swap_extension.py'),
                raw_source_hashes=json.loads(base.CONTRACT.read_text())['source_sha256'],
                scope='same selected1348 cells, thresholds1 and3, first two original seeds, paired starts at block120',
                run='15 new blocks per branch; each E attempts; summarize all15, no burn-in selection',
                moves='control: original two-edge; mixed: independently choose two or three with probability1/2; uniform ordered edge indices with replacement; three rotates targets by +1 or -1 equiprobably; reject loops, duplicates, null moves, category mismatch',
                symmetry='indexed edges retained; inverse rotation with same indices has equal probability; rejection retained. Does not prove irreducibility or mixing.',
                seeds='old_seed+2000 for each branch; matched start, not identical effective random proposals',
                gate='every block exact in/out degrees and category counts; report actual acceptance and reciprocity sensitivity; no p-value or uniform expectation',
                claim_ceiling='observed-graph computational sensitivity, not new biological sample or causal result',
                starts=selected, numpy=np.__version__)
    if CONTRACT.exists():
        assert json.loads(CONTRACT.read_text()) == spec
    else:
        CONTRACT.write_text(json.dumps(spec, indent=2), encoding='utf-8')
    for name, digest in spec['raw_source_hashes'].items():
        p = HERE / name if (HERE / name).exists() else base.DATA / name
        assert base.sha(p) == digest
    counts, categories = base.load_graph()
    STORE.mkdir(exist_ok=True)
    summaries = []
    for start in selected:
        rp = base.ROOT / start['final_checkpoint']
        assert base.sha(rp) == start['final_checkpoint_sha256']
        gp = rp.with_suffix('.npz')
        assert base.sha(gp) == start['final_graph_sha256']
        threshold, seed = start['threshold'], start['seed']
        initial = counts >= threshold
        for branch in ('control', 'mixed'):
            out = STORE / f't{threshold}_seed{seed}_{branch}.json'
            graph = out.with_suffix('.npz')
            if out.exists():
                record = json.loads(out.read_text())
                assert record['contract_sha256'] == base.sha(CONTRACT)
                assert record['graph_sha256'] == base.sha(graph)
                with np.load(graph, allow_pickle=False) as saved:
                    validate(saved['adjacency'], saved['edges'], initial, categories)
                    assert record['trajectory'][-1]['reciprocal'] == int((saved['adjacency'] & saved['adjacency'].T).sum() // 2)
            else:
                with np.load(gp, allow_pickle=False) as saved:
                    a, edges = saved['adjacency'].copy(), saved['edges'].copy()
                rng = np.random.default_rng(seed + 2000)
                m = len(edges)
                accepted = [0, 0]
                attempts = [0, 0]
                trajectory = []
                for block in range(1, 16):
                    indices = rng.integers(0, m, size=(m, 3))
                    kinds = rng.integers(0, 2, size=m) if branch == 'mixed' else np.zeros(m, dtype=int)
                    directions = rng.integers(0, 2, size=m) * 2 - 1
                    for ids, kind, direction in zip(indices, kinds, directions):
                        attempts[kind] += 1
                        accepted[kind] += (three(a, edges, ids, int(direction), categories) if kind else base.propose(a, edges, ids[0], ids[1], categories))
                    validate(a, edges, initial, categories)
                    trajectory.append(dict(block=block, reciprocal=int((a & a.T).sum() // 2),
                                           original_overlap=float((a & initial).sum() / m)))
                    if block % 5 == 0:
                        print(threshold, seed, branch, block, trajectory[-1]['reciprocal'], flush=True)
                with graph.open('xb') as stream:
                    np.savez_compressed(stream, adjacency=a, edges=edges)
                record = dict(contract_sha256=base.sha(CONTRACT), graph_sha256=base.sha(graph),
                              trajectory=trajectory, accepted=list(map(int, accepted)), attempts=list(map(int, attempts)), rng_state=rng.bit_generator.state)
                with out.open('x') as stream:
                    json.dump(record, stream, indent=2)
            vals = [r['reciprocal'] for r in record['trajectory']]
            summaries.append(dict(threshold=threshold, seed=seed, branch=branch, mean=float(np.mean(vals)),
                                  range=[min(vals), max(vals)], last5_minus_first5=float(np.mean(vals[-5:]) - np.mean(vals[:5])),
                                  accepted=record['accepted'], attempts=record['attempts'],
                                  record=out.relative_to(base.ROOT).as_posix(), record_sha256=base.sha(out)))
    result = dict(contract_sha256=base.sha(CONTRACT), reversible_fixture_transitions=fixture_count,
                  chains=summaries, status='PAIRED_KERNEL_SENSITIVITY_NOT_UNIFORMITY_PROOF')
    if OUTPUT.exists():
        assert result == json.loads(OUTPUT.read_text())
    else:
        OUTPUT.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
