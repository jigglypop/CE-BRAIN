"""네 노드 전체 그래프로 기존 교환 규칙의 도달성과 통계량을 정확히 감사한다."""
import itertools
import json
from collections import defaultdict
from fractions import Fraction
from pathlib import Path

import numpy as np
import microns_constrained_swaps as base
from reference_spike_audit import sha

HERE = Path(__file__).resolve().parent
PAIRS = [(u, v) for u in range(4) for v in range(4) if u != v]
BITS = {p: 1 << i for i, p in enumerate(PAIRS)}


def encode(a):
    return sum(BITS[p] for p in PAIRS if a[p])


def components(states, links):
    unseen = set(states)
    result = []
    while unseen:
        first = min(unseen)
        unseen.remove(first)
        stack, component = [first], [first]
        while stack:
            for target in links[stack.pop()]:
                if target in unseen:
                    unseen.remove(target)
                    component.append(target)
                    stack.append(target)
        result.append(sorted(component))
    return result


def audit(categories):
    fibers, links, triangles, reciprocal = defaultdict(list), {}, {}, {}
    signatures = {}
    for state in range(4096):
        a = np.zeros((4, 4), dtype=bool)
        for p, bit in BITS.items():
            a[p] = bool(state & bit)
        signature = tuple(tuple(map(int, x)) for x in base.signature(a, categories))
        signatures[state] = signature
        fibers[signature].append(state)
        reciprocal[state] = int((a & a.T).sum() // 2)
        edges = np.argwhere(a)
        neighbors = set()
        for i, j in itertools.combinations(range(len(edges)), 2):
            changed, ordered = a.copy(), edges.copy()
            if base.propose(changed, ordered, i, j, categories):
                neighbors.add(encode(changed))
        links[state] = neighbors
        # Alternate move audited exhaustively, not yet used on biological data.
        extra = set()
        for u, v, w in itertools.combinations(range(4), 3):
            for cycle in [[(u, v), (v, w), (w, u)], [(v, u), (w, v), (u, w)]]:
                reverse = [(y, x) for x, y in cycle]
                if all(a[p] for p in cycle) and not any(a[p] for p in reverse):
                    if sorted(int(categories[p]) for p in cycle) == sorted(int(categories[p]) for p in reverse):
                        changed = a.copy()
                        for p in cycle:
                            changed[p] = False
                        for p in reverse:
                            changed[p] = True
                        extra.add(encode(changed))
        triangles[state] = neighbors | extra
    for graph in (links, triangles):
        for state, targets in graph.items():
            for target in targets:
                assert signatures[state] == signatures[target]
                assert state in graph[target], 'reverse transition missing'
    output = {}
    for name, graph in [('original_two_edge', links), ('plus_triangle_reversal', triangles)]:
        disconnected, biased, witness = 0, 0, None
        for states in fibers.values():
            groups = components(states, graph)
            if len(groups) == 1:
                continue
            disconnected += 1
            means = [Fraction(sum(reciprocal[s] for s in group), len(group)) for group in groups]
            if len(set(means)) > 1:
                biased += 1
                if witness is None:
                    witness = dict(states=states, components=groups, component_means=list(map(str, means)),
                                   reciprocal_by_state={str(s): reciprocal[s] for s in states},
                                   edges_by_state={str(s): [list(p) for p, bit in BITS.items() if s & bit] for s in states})
        output[name] = dict(disconnected_fibers=disconnected, fibers_with_component_dependent_mean=biased,
                            first_mean_witness=witness)
    return dict(states=4096, constraint_fibers=len(fibers), **output)


def main():
    contract_path = HERE / 'swap_reachability_contract.json'
    contract = dict(question='Does the frozen swap kernel reach all constrained graphs, and can components have different reciprocal means?',
                    scope='Exhaustive 4096 loop-free directed labelled four-node graphs; synthetic only, BIO_EVIDENCE_L0',
                    cases=['one category', 'two broad types', 'two broad types and fixed line-distance bins'],
                    coordinates=[0, 40, 110, 250], types=[0, 0, 1, 1], distance_bins=[50, 100, 200, 400, 800],
                    endpoints='constraint fibers, connected components, exact rational reciprocal means; first witness in deterministic enumeration',
                    gate='any unequal component means refute universal unbiased expectation from a single reachable component; no inference that actual MICrONS fiber is disconnected',
                    source_sha256=sha(Path(base.__file__)), code_sha256=sha(Path(__file__)))
    if contract_path.exists():
        assert json.loads(contract_path.read_text()) == contract
    else:
        contract_path.write_text(json.dumps(contract, indent=2), encoding='utf-8')
    types = np.array(contract['types'])
    xy = np.array(contract['coordinates'])
    ordered = types[:, None] * 2 + types[None, :]
    cases = {'one_category': np.zeros((4, 4), dtype=int), 'broad_types': ordered * 6,
             'broad_types_and_distance': ordered * 6 + np.digitize(abs(xy[:, None] - xy[None, :]), contract['distance_bins'])}
    result = dict(contract_sha256=sha(contract_path), cases={k: audit(c) for k, c in cases.items()})
    target = HERE / 'swap_reachability_result.json'
    if target.exists():
        assert json.loads(target.read_text()) == result
    else:
        target.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps({k: {n: v for n, v in case.items() if n in ('states', 'constraint_fibers')} |
                     {n: {a: b for a, b in v.items() if a != 'first_mean_witness'} for n, v in case.items() if isinstance(v, dict)}
                     for k, case in result['cases'].items()}, indent=2))


if __name__ == '__main__':
    main()
