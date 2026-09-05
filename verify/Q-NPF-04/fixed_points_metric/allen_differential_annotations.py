"""Post-result context: same-cell published pair labels, not a new holdout."""
import json
import sqlite3
from pathlib import Path

from allen_joint_inventory import HERE, BASE, sha


def main():
    output=HERE/'allen_differential_annotations_result.json'
    if output.exists():raise FileExistsError('Preserve annotation snapshot')
    source=HERE/'allen_spatial_recordings_result.json'
    prior=json.loads(source.read_text(encoding='utf-8'))
    database=BASE/'synphys_r2.1_small.sqlite'
    assert sha(database)==prior['database_sha256']
    cells=sorted([r['cell'] for r in prior['joined']],key=lambda r:r['cell'])
    ids=[r['cell'] for r in cells]
    marks=','.join('?' for _ in ids)
    sql=(f'SELECT p.id AS pair_id,p.pre_cell_id,p.post_cell_id,p.has_synapse,p.has_electrical,'
         f's.id AS synapse_id,s.synapse_type,s.psp_amplitude,s.psc_amplitude '
         f'FROM pair p LEFT JOIN synapse s ON s.pair_id=p.id '
         f'WHERE p.pre_cell_id IN ({marks}) AND p.post_cell_id IN ({marks}) ORDER BY p.pre_cell_id,p.post_cell_id')
    with sqlite3.connect(database.resolve().as_uri()+'?mode=ro',uri=True) as connection:
        cursor=connection.execute(sql,ids+ids)
        columns=[x[0] for x in cursor.description]
        pairs=[dict(zip(columns,row)) for row in cursor]
    assert len(pairs)==20 and len({(p['pre_cell_id'],p['post_cell_id']) for p in pairs})==20
    out={'code_sha256':sha(Path(__file__)),'database_sha256':prior['database_sha256'],'identity_sha256':sha(source),
         'schema_sha256':sha(HERE.parent/'allen_synphys/source_snapshots/aisynphys__database__schema__synapse.py'),
         'cells':cells,'pairs':pairs,'units':{'position':'m, internal convention verified previously','psp_amplitude':'V','psc_amplitude':'A'},
         'context':'Post-result annotation lookup. Labels are prior database assessments, not independently revalidated here or used to select the transfer model.',
         'interpretation':'Known chemical-synapse labels can coexist with unidentifiable subthreshold transfer. Neither pair-negative labels nor test-negative response prove anatomical absence.',
         'metric_verdict':'NOT_EVALUATED'}
    with output.open('x',encoding='utf-8') as stream:json.dump(out,stream,ensure_ascii=False,indent=2,allow_nan=False)
    print(json.dumps({'pairs':len(pairs),'positive_chemical':[p for p in pairs if p['has_synapse']],
                      'electrical_labels_positive':sum(bool(p['has_electrical']) for p in pairs)}))


if __name__=='__main__':main()
