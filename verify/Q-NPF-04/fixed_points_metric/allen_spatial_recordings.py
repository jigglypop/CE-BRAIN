"""세 번째 NWB 첫 시행의 공간 기록 후보를 결합하고 rank 오판을 교정한다."""
import json
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path
import h5py
import numpy as np
from allen_joint_inventory import HERE, BASE, OfflineRanges, describe, sha, raw

EXT = '1630015960.701'


def geometry(points):
    points = np.asarray(points,dtype=float)
    differences = points[1:]-points[0]
    singular = np.linalg.svd(differences,compute_uv=False)
    tol = max(differences.shape)*np.finfo(float).eps*(singular[0] if len(singular) else 0.)
    rank = int(np.sum(singular>tol))
    assert rank <= min(len(points)-1,3)
    return {'rank':rank,'singular_values':singular.tolist(),'tolerance':float(tol)}


def main():
    old_path = HERE/'allen_joint_inventory_result.json'
    old = json.loads(old_path.read_text(encoding='utf-8'))
    selected = next(r for r in old['results'] if r['summary']['external']==EXT)
    cells = {c['device']:c for c in selected['cells']}
    corrections = []
    for experiment in old['results']:
        byid = {c['cell']:c for c in experiment['cells']}
        for group in experiment['geometry']:
            corrected = geometry([byid[c]['position'] for c in group['cell_ids']])
            if corrected['rank'] != group['affine_rank']:
                corrections.append({'external':experiment['summary']['external'],'sweep':group['sweep'],
                                    'cell_ids':group['cell_ids'],'old_rank':group['affine_rank'],**corrected})
    all_points = defaultdict(list)
    database = BASE/'synphys_r2.1_small.sqlite'
    assert sha(database) == old['database_sha256']
    with sqlite3.connect(database.resolve().as_uri()+'?mode=ro',uri=True) as con:
        for experiment,encoded in con.execute('SELECT experiment_id,position FROM cell ORDER BY id'):
            p = json.loads(encoded) if encoded is not None else None
            if p is not None and np.asarray(p).shape==(3,) and np.isfinite(p).all():
                all_points[experiment].append(p)
    database_ranks = Counter(geometry(p)['rank'] for p in all_points.values() if len(p)>=4)
    cache = BASE/'raw_ranges'/EXT
    channels = {'acquisition':[],'command':[]}
    with OfflineRanges(cache) as reader:
        with h5py.File(reader,'r') as f:
            for label,path in [('acquisition','acquisition/timeseries'),('command','stimulus/presentation')]:
                for key in sorted(f[path]):
                    if key.startswith('data_00000_') and 'electrode_name' in f[path][key]:
                        row = describe(f[path][key])
                        row['stimulus'] = str(f[path][key]['stimulus_description'][()][0]) if 'stimulus_description' in f[path][key] else None
                        channels[label].append(row)
                print('METADATA',label,len(channels[label]),flush=True)
        provenance = {'remote':reader.remote,'used_blocks':reader.used,'new_bytes':0}
    commands = {(r['sweep'],r['device']):r for r in channels['command']}
    assert len(commands) == len(channels['command'])
    joined = []
    unmatched = []
    for row in channels['acquisition']:
        command = commands.get((row['sweep'],row['device']))
        if command is None or row['device'] not in cells:
            unmatched.append({'acquisition':row,'command_found':command is not None,'cell_found':row['device'] in cells})
            continue
        units = (row['unit'],command['unit'])
        mode = 'ic' if units==('V','A') else ('vc' if units==('A','V') else 'unknown')
        joined.append({'cell':cells[row['device']],'acquisition':row,'command':command,'mode':mode,
                       'clock_match':all(row[k]==command[k] for k in ('start','rate','samples'))})
    groups = defaultdict(list)
    for row in joined:
        if row['clock_match'] and row['mode']!='unknown':
            a = row['acquisition']
            groups[(a['sweep'],a['start'],a['rate'],a['samples'])].append(row)
    spatial = []
    for key,rows in sorted(groups.items()):
        p = [r['cell']['position'] for r in rows]
        if any(v is None for v in p):
            continue
        spatial.append({'sweep':key[0],'start':key[1],'rate':key[2],'samples':key[3],
                        'cells':[r['cell']['cell'] for r in rows],'devices':[r['cell']['device'] for r in rows],
                        'modes':[r['mode'] for r in rows],'stimuli':[r['acquisition']['stimulus'] for r in rows],**geometry(p)})
    summary = {'external':EXT,'acquisition_channels':len(channels['acquisition']),
               'command_channels':len(channels['command']),'joined_channels':len(joined),
               'unmatched_channels':len(unmatched),'synchronous_groups':len(spatial),
               'rank_counts':dict(Counter(s['rank'] for s in spatial)),
               'rank3_sweeps':[s['sweep'] for s in spatial if s['rank']==3],
               'database_rank_counts_anchor':dict(database_ranks),'corrected_prior_groups':len(corrections),
               'new_bytes':provenance['new_bytes']}
    result = {'code_sha256':sha(Path(__file__)),'prior_inventory_sha256':sha(old_path),
              'helper_sha256':sha(HERE/'allen_joint_inventory.py'),'reader_sha256':sha(Path(raw.__file__)),
              'database_sha256':old['database_sha256'],'summary':summary,'rank_corrections':corrections,
              'joined':joined,'unmatched':unmatched,'spatial':spatial,'provenance':provenance,
              'scope':'Metadata only; first sweep 0 of pre-existing third raw recording, before signal results; no cohort-wide eligibility claim',
              'preparation':'An initial full-metadata scan stopped at its 16 MiB additional-cache budget. Downloaded blocks were retained. This bounded first-sweep join reuses cached blocks only.',
              'rank_rule':'Subtract first point; matrix has n-1 rows, so rank cannot exceed n-1; no ridge',
              'limits':['Machine-precision geometry rank is not noise-resolved biological identifiability',
                        'Mixed IC/VC commands require mode-specific interpretation and access/holding correction',
                        'Stimulus labels do not prove spatially independent or subthreshold inputs',
                        'Cell.position physical unit and historical mosaic calibration remain unverified'],
              'claim_ceiling':'BIO_EVIDENCE_L0_INPUT_JOIN'}
    with (HERE/'allen_spatial_recordings_result.json').open('x',encoding='utf-8') as f:
        json.dump(result,f,ensure_ascii=False,indent=2,allow_nan=False)
    print(json.dumps(summary),flush=True)


if __name__ == '__main__':
    main()
