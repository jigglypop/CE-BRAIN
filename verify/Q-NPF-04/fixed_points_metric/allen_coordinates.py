"""보유 Allen DB의 실제 좌표 열을 전량 집계한다. 반응값은 읽지 않는다."""
import hashlib
import json
import sqlite3
import sys
from collections import Counter, defaultdict
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
DB = ROOT/'data/external/allen_synphys_r21/synphys_r2.1_small.sqlite'
SCHEMA = HERE.parent/'allen_synphys/source_snapshots/aisynphys__database__schema__experiment.py'


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    prior = json.loads((HERE.parent/'allen_synphys/component_contract.json').read_text(encoding='utf-8'))
    database_sha = sha(DB)
    assert database_sha == prior['db_sha256']
    assert sha(SCHEMA) == prior['source_hashes'][SCHEMA.name]
    counts = Counter()
    groups = defaultdict(list)
    with sqlite3.connect(DB.resolve().as_uri()+'?mode=ro', uri=True) as con:
        for cell, experiment, raw in con.execute('SELECT id, experiment_id, position FROM cell ORDER BY id'):
            position = json.loads(raw) if isinstance(raw,str) else raw
            if position is None:
                counts['null'] += 1
                continue
            point = np.asarray(position,dtype=float)
            if point.shape != (3,):
                counts['other_shape'] += 1
                continue
            if not np.isfinite(point).all():
                counts['nonfinite_3d'] += 1
                continue
            counts['finite_3d'] += 1
            groups[experiment].append((cell,point))
    experiments = []
    for experiment, rows in sorted(groups.items()):
        if len(rows) < 4:
            continue
        points = np.vstack([p for _,p in rows])
        singular = np.linalg.svd(points-points.mean(axis=0),compute_uv=False)
        tolerance = singular[0]*max(points.shape)*np.finfo(points.dtype).eps
        experiments.append({'experiment_id':experiment,'cell_ids':[cell for cell,_ in rows],
                            'singular_values':singular.tolist(),'rank_tolerance':float(tolerance),
                            'affine_rank':int(np.sum(singular>tolerance))})
    result = {'database_sha256':database_sha,'schema_sha256':sha(SCHEMA),'code_sha256':sha(Path(__file__)),
              'runtime':{'executable':sys.executable,'python':sys.version,'numpy':np.__version__},
              'counts':dict(counts),'experiments_with_coordinates':len(groups),
              'rank_counts_at_least_four_cells':dict(Counter(r['affine_rank'] for r in experiments)),
              'rank_rule':'Centered SVD, tolerance=max(shape)*machine_epsilon*largest_singular_value; no ridge',
              'coordinate_definition':'cell.position: 3D location in arbitrary experiment coordinate system; unit not stated by this schema field',
              'limits':['Numerical coordinate rank is not calibration or noise-resolved identifiability',
                        'Voltage/current joins, units, affine stimulation, unobserved inputs and held-out prediction untested'],
              'claim_ceiling':'BIO_EVIDENCE_L0_INPUT_INVENTORY','experiments':experiments}
    with (HERE/'allen_coordinates_result.json').open('x',encoding='utf-8') as f:
        json.dump(result,f,ensure_ascii=False,indent=2,allow_nan=False)
    print(json.dumps({k:result[k] for k in ('counts','experiments_with_coordinates','rank_counts_at_least_four_cells','claim_ceiling')}))


if __name__ == '__main__':
    main()
