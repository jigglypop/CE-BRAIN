"""저자 L2/3 파라미터를 Minnie 23P 좌표에 고정 적용하는 탐색 검사."""
import csv
import hashlib
import json
import sys
import types
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
import scipy
from scipy.spatial.distance import cdist
import microns_constrained_swaps as base

HERE = base.HERE
STORE = base.ROOT / 'data/external/sgsg_fixed_transfer'
ARCHIVE = base.ROOT / 'data/external/sgsg_v1/local_connectivity_model-v1.0.0.zip'
PREFIX = 'MWolfR-local_connectivity_model-b9f18bb/'


def write_once(path, value):
    if path.exists():
        assert json.loads(path.read_text(encoding='utf-8')) == value, path
    else:
        path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def load_modules():
    assert base.sha(ARCHIVE) == '540f98689798a06de97c7424c80710fe8d5b02082a4a9bae7b10766fe999c039'
    with zipfile.ZipFile(ARCHIVE) as z:
        config = json.loads(z.read(PREFIX + 'configs/pnagm_L23E_microns_yscale_experimental_v1p5.json'))
        modules = []
        for name in ('nngraph', 'instance'):
            member = PREFIX + 'src/pnagm/' + name + '.py'
            module = types.ModuleType('sgsg_' + name)
            exec(compile(z.read(member), member, 'exec'), module.__dict__)
            modules.append(module)
    return config, modules[0], modules[1]


def data():
    for name, digest in json.loads(base.CONTRACT.read_text())['source_sha256'].items():
        path = HERE / name if (HERE / name).exists() else base.DATA / name
        assert base.sha(path) == digest
    counts, categories = base.load_graph()
    roots = json.loads(base.SELECTED.read_text())['selected_roots']
    with (base.DATA / 'v1718_cell_info.csv').open(encoding='utf-8', newline='') as stream:
        cells = {int(r['pt_root_id']): r for r in csv.DictReader(stream)}
    ids = [i for i, r in enumerate(roots) if cells[r]['broad_type'] == 'excitatory' and cells[r]['cell_type'] == '23P']
    chosen = [roots[i] for i in ids]
    xyz = np.array([[float(cells[r]['pt_position_' + axis + '_tform']) for axis in 'xyz'] for r in chosen])
    a = counts[np.ix_(ids, ids)] >= 1
    assert len(chosen) == 347 and a.sum() == 5995 and not np.diag(a).any()
    assert np.isfinite(xyz).all() and len(np.unique(xyz, axis=0)) == len(xyz)
    return chosen, xyz, a, categories[np.ix_(ids, ids)] % 6


def summary(a, xyz, bins):
    edges = int(a.sum())
    d = cdist(xyz, xyz)
    return dict(edges=edges, reciprocal_pairs=int((a & a.T).sum() // 2),
                distance_counts=np.bincount(bins[a], minlength=6).tolist(),
                mean_edge_distance_um=float(d[a].mean()) if edges else None,
                out_degree_sd=float(a.sum(1).std()), in_degree_sd=float(a.sum(0).std()),
                zero_degree_cells=int(np.sum((a.sum(0) + a.sum(1)) == 0)))


def main():
    config, geometry, spread = load_modules()
    spec = dict(
        question='Can published L23 SGSG parameters transfer to the existing 347-cell Minnie 23P subvolume?',
        design='Exploratory fixed-parameter transfer, not fitted comparison or independent confirmation',
        population='existing v1718 selected 23P excitatory cells; threshold1; transformed soma coordinates in um',
        parameters=config,
        adaptation='Use existing 347 actual coordinates, omit example crop/resampling and per-subclass biases because all selected cells share 23P; other classes and outside-column paths absent',
        calibration='None; no parameter selected using observed reciprocity or density',
        seeds=list(range(2026091600, 2026091616)),
        gate='All 16 runs finite binary loop-free. Mean edge count must differ by <=20% of observed count for provisional density compatibility only. Otherwise no reciprocal-excess interpretation. Not a statistical acceptance test.',
        limitations='Same specimen as source MICrONS, version/population mismatch, boundary truncation, no exact degree/distance constraints, no error correction',
        predecessor_sha256=base.sha(HERE / 'sgsg_fixed_transfer_contract.json'), correction='Legacy numpy.random.seed requires uint32; failed before first graph. Fixed seed range before any output.', archive_sha256=base.sha(ARCHIVE), code_sha256=base.sha(Path(__file__)),
        loader_sha256=base.sha(Path(base.__file__)),
        source_sha256=json.loads(base.CONTRACT.read_text())['source_sha256'],
        interpreter=sys.executable, python=sys.version, numpy=np.__version__, pandas=pd.__version__, scipy=scipy.__version__)
    cp = HERE / 'sgsg_fixed_transfer_seed32_contract.json'
    write_once(cp, spec)
    roots, xyz, observed, bins = data()
    STORE.mkdir(exist_ok=True)
    records = []
    for seed in spec['seeds']:
        path = STORE / f'{seed}.npz'
        receipt = STORE / f'{seed}.json'
        if receipt.exists():
            record = json.loads(receipt.read_text())
            assert record['contract_sha256'] == base.sha(cp)
            if record['status'] == 'PASS':
                assert base.sha(path) == record['file_sha256']
                with np.load(path, allow_pickle=False) as f:
                    a = f['adjacency']
                    assert f['roots'].tolist() == roots
                assert record['summary'] == summary(a, xyz, bins)
        else:
            np.random.seed(seed)
            try:
                m = geometry.cand2_point_nn_matrix(xyz, **config['nngraph'])
                generated, history, degrees = spread.build_instance(xyz, m, **config['instance'])
                a = generated.toarray().astype(bool)
                assert a.shape == observed.shape and not np.diag(a).any()
                assert np.isfinite(history).all() and np.isfinite(m.data).all()
                with path.open('xb') as stream:
                    np.savez_compressed(stream, adjacency=a, roots=np.array(roots, dtype=np.int64), xyz=xyz)
                record = dict(status='PASS', seed=seed, summary=summary(a, xyz, bins),
                              file_sha256=base.sha(path), geometry_nonzeros=int(m.nnz),
                              graph_sha256=hashlib.sha256(a.tobytes()).hexdigest(), history=[float(v) for v in history])
            except Exception as exc:
                record = dict(status='FAILED', seed=seed, error_type=type(exc).__name__, error=str(exc))
            record['contract_sha256'] = base.sha(cp)
            write_once(receipt, record)
        records.append(record)
        print(json.dumps({k: v for k, v in record.items() if k in ('seed', 'status', 'summary', 'error')}), flush=True)
    valid = [r for r in records if r['status'] == 'PASS']
    all_pass = len(valid) == len(records)
    mean_edges = float(np.mean([r['summary']['edges'] for r in valid])) if all_pass else None
    density_ok = all_pass and abs(mean_edges / observed.sum() - 1) <= .2
    result = dict(contract_sha256=base.sha(cp), observed=summary(observed, xyz, bins),
                  selected_roots=roots, all_runs_pass=all_pass,
                  mean_generated_edges=mean_edges, provisional_density_compatible=bool(density_ok),
                  reciprocal_interpretation='NOT_ASSESSED; fixed parameter transport only' if density_ok else 'NOT_ELIGIBLE_DENSITY_OR_EXECUTION_MISMATCH',
                  receipt_sha256={f'{r["seed"]}.json': base.sha(STORE / f'{r["seed"]}.json') for r in records},
                  records=records)
    write_once(HERE / 'sgsg_fixed_transfer_seed32_result.json', result)
    print(json.dumps({k: v for k, v in result.items() if k not in ('records', 'selected_roots', 'receipt_sha256')}), flush=True)


if __name__ == '__main__':
    main()
