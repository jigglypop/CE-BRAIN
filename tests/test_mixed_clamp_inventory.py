import hashlib
import json
from pathlib import Path
import sys

import pytest

HERE = Path(__file__).resolve().parents[1]/'verify/Q-NPF-04/allen_synphys'
sys.path.insert(0, str(HERE))
import mixed_clamp_inventory as m


def rec(rid, mode, sync=10, qc=1, patch=True):
    return dict(id=rid, electrode_id=rid+100, sync_rec_id=sync, patch_id=rid if patch else None,
                clamp_mode=mode, qc_pass=qc)


def test_direction_qc_and_missingness_are_distinct():
    result = m.classify([rec(1,'ic'),rec(2,'vc',qc=0),rec(3,None,patch=False)])
    assert result['mixed_mode'] and not result['coverage_complete']
    assert result['unknown_mode_recordings']==[3]
    assert result['candidates']==[dict(source_recording=1,target_recording=2,source_electrode=101,
        target_electrode=102,both_recording_qc_passed=False)]
    assert m.classify([rec(1,'ic'),rec(2,'ic')])['candidates']==[]
    assert not m.classify([])['coverage_complete']


@pytest.mark.parametrize('records', [[rec(1,'ic'),rec(2,'vc',sync=11)],
    [rec(1,'ic'),rec(1,'vc')], [rec(1,'ic'),dict(rec(2,'vc'),electrode_id=101)]])
def test_no_cross_sweep_or_duplicate_pairing(records):
    with pytest.raises(ValueError):
        m.classify(records)


def test_indexed_inventory_keeps_mode_unknown_and_joins_all_electrodes():
    db = m.apsw.Connection(':memory:')
    db.execute('CREATE TABLE experiment(id INTEGER PRIMARY KEY,ext_id TEXT); '
        'CREATE UNIQUE INDEX ix_experiment_ext_id ON experiment(ext_id); '
        'CREATE TABLE electrode(id INTEGER PRIMARY KEY,experiment_id INTEGER,device_id INTEGER); '
        'CREATE INDEX ix_electrode_experiment_id ON electrode(experiment_id); '
        'CREATE TABLE sync_rec(id INTEGER PRIMARY KEY,experiment_id INTEGER,ext_id TEXT); '
        'CREATE INDEX ix_sync_rec_experiment_id ON sync_rec(experiment_id); '
        'CREATE TABLE recording(id INTEGER PRIMARY KEY,sync_rec_id INTEGER,electrode_id INTEGER,device_name TEXT,stim_name TEXT,sample_rate REAL); '
        'CREATE INDEX ix_recording_sync_rec_id ON recording(sync_rec_id); '
        'CREATE TABLE patch_clamp_recording(id INTEGER PRIMARY KEY,recording_id INTEGER,clamp_mode TEXT,qc_pass INTEGER,baseline_potential REAL,baseline_current REAL,nearest_test_pulse_id INTEGER); '
        'CREATE INDEX ix_patch_clamp_recording_recording_id ON patch_clamp_recording(recording_id); '
        "INSERT INTO experiment VALUES(1,'test'); INSERT INTO electrode VALUES(101,1,1),(102,1,2); "
        "INSERT INTO sync_rec VALUES(10,1,'0'),(11,1,'1'); "
        "INSERT INTO recording VALUES(1,10,101,'1','test',20000),(2,10,102,'2','test',20000),"
        "(3,11,101,'1','test',20000),(4,11,102,'2','test',20000); "
        "INSERT INTO patch_clamp_recording VALUES(1,1,'ic',1,NULL,0,NULL),(2,2,'vc',1,-0.07,NULL,NULL),"
        "(3,3,'ic',1,NULL,0,NULL)")
    result = m.collect(db, {1: 'test'})
    assert result['experiments'][0]['summary']==dict(sweeps=2,recording_modes={'ic':2,'unknown':1,'vc':1},
        mixed_mode_sweeps=[0],incomplete_mode_sweeps=[1],candidate_pairs=1)
    assert len(result['query_plans'])==5
    with pytest.raises(ValueError,match='scan'):
        m.indexed_query(db,'SELECT * FROM recording',(),[])
    with pytest.raises(ValueError,match='identity'):
        m.collect(db, {2: 'test'})
    db.close()


def test_prior_range_reused_without_download_and_corruption_rejected(tmp_path):
    base,prior,overlay = [tmp_path/name for name in ('base','prior','new')]
    base.mkdir();prior.mkdir()
    payload = b'abc'
    manifest = dict(remote=dict(url='https://example.invalid/db',bytes=3,etag='fixed'),block_size=65536,blocks={})
    (base/'manifest.json').write_text(json.dumps(manifest),encoding='utf-8')
    parent_sha = m.sha(base/'manifest.json')
    prior_manifest = dict(manifest,base_manifest_sha256=parent_sha,
        blocks={'0':dict(bytes=3,sha256=hashlib.sha256(payload).hexdigest())})
    (prior/'manifest.json').write_text(json.dumps(prior_manifest),encoding='utf-8')
    path = prior/'000000000000.bin'
    path.write_bytes(payload)
    kwargs = dict(base=base,overlay=overlay,base_sha=parent_sha,prior=prior,prior_sha=m.sha(prior/'manifest.json'))
    with m.ReusingRanges(**kwargs) as reader:
        assert reader.block(0)==payload and reader.downloaded==0
        assert list(reader.used_prior)==['0'] and not overlay.exists()
    path.write_bytes(b'bad')
    with m.ReusingRanges(**kwargs) as reader:
        with pytest.raises(ValueError,match='Corrupt'):
            reader.block(0)
