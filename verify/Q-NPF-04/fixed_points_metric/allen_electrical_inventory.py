"""Metadata-only census of electrical edges and within-experiment spatial rank.

Selection follows annotation topology and geometry, not response amplitude.
Directional pair rows are merged only for geometry, not to infer rectification.
"""
import hashlib
import json
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
DB = ROOT/'data/external/allen_synphys_r21/synphys_r2.1_small.sqlite'
DB_SHA = '7372499fdd874f057565080d5769baaf2659ef39d9f3bc3c7147dd1e1c280a53'


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def geometry(vectors):
    if not vectors:
        return dict(rank=0, singular_values=[], condition_number=None)
    array = np.asarray(vectors, float)
    singular = np.linalg.svd(array, compute_uv=False)
    tolerance = singular[0]*max(array.shape)*np.finfo(float).eps
    rank = int(np.sum(singular > tolerance))
    return dict(rank=rank, singular_values=singular.tolist(), tolerance=tolerance,
                condition_number=float(singular[0]/singular[-1]) if rank == 3 else None)


def components(edges):
    remaining = {n for edge in edges for n in edge}
    groups = []
    while remaining:
        group, frontier = set(), {min(remaining)}
        while frontier:
            group |= frontier
            frontier = {n for edge in edges if set(edge) & frontier for n in edge}-group
        remaining -= group
        groups.append(sorted(group))
    return groups


def main():
    output = HERE/'allen_electrical_inventory_result.json'
    if output.exists():
        raise FileExistsError(output)
    assert sha(DB) == DB_SHA
    with sqlite3.connect(DB.resolve().as_uri()+'?mode=ro', uri=True) as con:
        con.row_factory = sqlite3.Row
        rows = [dict(r) for r in con.execute('SELECT * FROM pair WHERE has_electrical=1 ORDER BY id')]
        cells = {}
        for row in con.execute('SELECT c.id,c.experiment_id,c.ext_id,c.position,c.cre_type,c.cell_class,'
                               'c.electrode_id,e.device_id FROM cell c JOIN electrode e ON e.id=c.electrode_id'):
            c = dict(row)
            c['position'] = json.loads(c['position']) if c['position'] else None
            cells[c['id']] = c
        by = defaultdict(list)
        for row in rows:
            by[row['experiment_id']].append(row)
        experiments = []
        for ex, positive in sorted(by.items()):
            record = dict(con.execute('SELECT id,ext_id,slice_id,project_name,target_region,ephys_file '
                                      'FROM experiment WHERE id=?', (ex,)).fetchone())
            keys = sorted({tuple(sorted((r['pre_cell_id'],r['post_cell_id']))) for r in positive})
            edges, directions = [], []
            for pre, post in keys:
                a, b = cells[pre]['position'], cells[post]['position']
                vector = None
                if a is not None and b is not None:
                    delta = np.asarray(b, float)-np.asarray(a, float)
                    if delta.shape == (3,) and np.isfinite(delta).all() and np.linalg.norm(delta) > 0:
                        vector = (delta/np.linalg.norm(delta)).tolist()
                        directions.append(vector)
                paired = [dict(r) for r in con.execute('SELECT id,pre_cell_id,post_cell_id,has_electrical,'
                    'has_synapse,crosstalk_artifact FROM pair WHERE experiment_id=? AND '
                    '((pre_cell_id=? AND post_cell_id=?) OR (pre_cell_id=? AND post_cell_id=?))',
                    (ex,pre,post,post,pre))]
                edges.append(dict(cells=[pre,post], unit_direction=vector, annotation_rows=paired))
            groups = []
            for group in components(keys):
                vectors = [e['unit_direction'] for e in edges if e['cells'][0] in group and e['unit_direction'] is not None]
                groups.append(dict(cells=group, geometry=geometry(vectors)))
            record.update(positive_ordered_rows=len(positive), undirected_edges=edges,
                edge_direction_geometry=geometry(directions), connected_components=groups,
                cells=[c for c in cells.values() if c['experiment_id']==ex])
            experiments.append(record)
    candidates = [e for e in experiments if any(c['geometry']['rank']==3 for c in e['connected_components'])]
    selected = min(candidates,key=lambda e:e['id']) if candidates else None
    result = dict(code_sha256=sha(__file__), database_path=DB.relative_to(ROOT).as_posix(), database_sha256=DB_SHA,
        observation_scope='Previously held annotation and position census; no electrical waveform opened',
        counts=dict(positive_ordered_rows=len(rows), undirected_positive_edges=sum(len(e['undirected_edges']) for e in experiments),
            experiments=len(experiments), direction_rank=dict(Counter(e['edge_direction_geometry']['rank'] for e in experiments)),
            experiments_with_rank3_connected_component=len(candidates)),
        selection='Exploratory metadata selection: connected positive-edge component spans 3D, then lowest experiment ID; not a response-based confirmation sample',
        selected_experiment_id=selected['id'] if selected else None,
        selected_external_id=selected['ext_id'] if selected else None,
        experiments=experiments,
        limitations=['Binary electrical annotation is not a measured conductance',
            'Ordered-row disagreement or absence is retained and is not physical rectification evidence',
            'Numerical coordinate rank does not establish metrological resolution or simultaneous good recordings',
            'No eigenvalue flooring or cross-animal spatial pooling is used',
            'Conditioned selection does not estimate prevalence in the brain'],
        claim_ceiling='BIO_EVIDENCE_L0 data eligibility; no identified spatial metric')
    with output.open('x', encoding='utf8') as stream:
        json.dump(result,stream,ensure_ascii=False,indent=2,allow_nan=False)
        stream.write('\n')
    print(json.dumps(dict(counts=result['counts'],selected_experiment=selected,
                         result_sha256=sha(output)),ensure_ascii=True))


if __name__ == '__main__':
    main()
