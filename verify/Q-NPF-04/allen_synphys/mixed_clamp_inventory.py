"""Indexed observability inventory, not an AP/PSC or connectivity estimate.

Read every recording in three already nominated experiments. Reuse immutable
medium ranges; permit missing ranges only in a separate bounded overlay.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import platform

from vc20hz_source_inputs import HERE, ROOT, LayeredRanges, sha
from medium_recording_lookup import ReadVFS, apsw
from vc20hz_measurement_state import indexed_query

BASE = ROOT/'data/external/allen_synphys_r21/medium_ranges'
BASE_SHA = '8f7f88ae8b62f67312c9f34616bc2feb280cc7b24db62a59b5b8a7c44d057bab'
PRIOR = ROOT/'data/external/allen_synphys_r21/vc20hz_medium_ranges/1574292898.139'
PRIOR_SHA = 'f447289e24e4eccf2b33333ac7bbe0ec97a9c73f42c7b628df0587c390f53325'
OVERLAY = ROOT/'data/external/allen_synphys_r21/mixed_clamp_medium_ranges/v1'
EXPERIMENTS = {3338: '1574282818.996', 3340: '1574286231.385', 4863: '1630015960.701'}
MAX_NEW = 8*1024*1024
SELECTION = HERE/'next_donor_batch_result.json'
DEPENDENCIES = {
    'vc20hz_source_inputs.py': '2a10fbf34a3c15b0f33765baf6b335249ebb06647d47cda6429b4d6b123227cb',
    'vc20hz_measurement_state.py': '055db380bf1760661d96c95aa9ea479f1bba254952aa4d4dc4bf9cbf88810444',
    'medium_recording_lookup.py': '0d2ee2f4a52cc21bbcf940b8c5642ffcb66f458d72aaf78bc3d4b69a85b6edf9',
    'raw_metadata.py': '5aa32fce7a19372183cf304ecf70bcd1d168dc723ffcffbc74f0711d83db50ae',
}
JOIN = (
    'SELECT r.id, r.sync_rec_id, r.electrode_id, r.device_name, r.stim_name, '
    'r.sample_rate, p.id AS patch_id, p.clamp_mode, p.qc_pass, '
    'p.baseline_potential, p.baseline_current, p.nearest_test_pulse_id '
    'FROM recording r INDEXED BY ix_recording_sync_rec_id '
    'LEFT JOIN patch_clamp_recording p INDEXED BY ix_patch_clamp_recording_recording_id '
    'ON p.recording_id=r.id WHERE r.sync_rec_id=?'
)


class ReusingRanges(LayeredRanges):
    def __init__(self, base=BASE, overlay=OVERLAY, allow_download=False,
                 base_sha=BASE_SHA, prior=PRIOR, prior_sha=PRIOR_SHA, max_new=MAX_NEW):
        super().__init__(base, overlay, allow_download, base_sha, max_new)
        self.prior = Path(prior)
        if sha(self.prior/'manifest.json') != prior_sha:
            raise ValueError('Prior manifest changed')
        self.prior_manifest = json.loads((self.prior/'manifest.json').read_text(encoding='utf-8'))
        if any(self.prior_manifest.get(k) != self.manifest[k]
               for k in ('remote', 'block_size', 'base_manifest_sha256')):
            raise ValueError('Prior cache identity mismatch')
        self.used_prior = {}

    def block(self, start):
        if start in self.memo:
            return self.memo[start]
        key = str(start)
        if key not in self.base_manifest['blocks'] and key not in self.manifest['blocks']:
            entry = self.prior_manifest['blocks'].get(key)
            if entry is not None:
                value = (self.prior/f'{start:012d}.bin').read_bytes()
                if len(value) != entry['bytes'] or hashlib.sha256(value).hexdigest() != entry['sha256']:
                    raise ValueError('Corrupt prior block')
                self.used_prior[key] = entry
                self.memo[start] = value
                return value
        return super().block(start)


def classify(records):
    """Only same-sweep IC -> VC pairs; unknown metadata never becomes negative."""
    if len({r['id'] for r in records}) != len(records):
        raise ValueError('Duplicate recording join')
    if len({r['electrode_id'] for r in records}) != len(records):
        raise ValueError('Multiple recordings for one electrode in a sweep')
    if len({r['sync_rec_id'] for r in records}) > 1:
        raise ValueError('Mixed sweep identity')
    known = [r for r in records if r['patch_id'] is not None and r['clamp_mode'] in ('ic', 'vc')]
    modes = Counter(r['clamp_mode'] for r in known)
    candidates = [dict(source_recording=pre['id'], target_recording=post['id'],
        source_electrode=pre['electrode_id'], target_electrode=post['electrode_id'],
        both_recording_qc_passed=pre['qc_pass'] == post['qc_pass'] == 1)
        for pre in known if pre['clamp_mode'] == 'ic'
        for post in known if post['clamp_mode'] == 'vc']
    return dict(mode_counts=dict(sorted(modes.items())), recordings=len(records),
        unknown_mode_recordings=[r['id'] for r in records if r not in known],
        coverage_complete=bool(records) and len(known) == len(records),
        mixed_mode=bool(candidates), candidates=candidates)


def collect(db, experiments=EXPERIMENTS):
    plans, output = [], []
    lookup = lambda sql, args: indexed_query(db, sql, args, plans)
    for eid, ext_id in experiments.items():
        metadata = lookup('SELECT id,ext_id FROM experiment WHERE ext_id=?', (ext_id,))
        if len(metadata) != 1 or metadata[0]['id'] != eid:
            raise ValueError('Experiment identity mismatch')
        electrodes = lookup('SELECT id,device_id FROM electrode WHERE experiment_id=?', (eid,))
        device_map = {r['id']: r['device_id'] for r in electrodes}
        syncs = lookup('SELECT id,ext_id FROM sync_rec WHERE experiment_id=?', (eid,))
        if not syncs or len(syncs) > 2000:
            raise ValueError('Unexpected sweep count')
        if len({s['ext_id'] for s in syncs}) != len(syncs):
            raise ValueError('Duplicate sweep label')
        sweeps = []
        for sync in sorted(syncs, key=lambda s: int(s['ext_id'])):
            records = lookup(JOIN, (sync['id'],))
            if any(r['sync_rec_id'] != sync['id'] or r['electrode_id'] not in device_map for r in records):
                raise ValueError('Foreign recording identity')
            for record in records:
                record['device_id'] = device_map[record['electrode_id']]
            sweeps.append(dict(sync_rec_id=sync['id'], sweep=int(sync['ext_id']),
                               records=records, classification=classify(records)))
        counts = Counter(r['clamp_mode'] if r['patch_id'] is not None and r['clamp_mode'] in ('ic','vc')
                         else 'unknown' for s in sweeps for r in s['records'])
        mixed = [s['sweep'] for s in sweeps if s['classification']['mixed_mode']]
        incomplete = [s['sweep'] for s in sweeps if not s['classification']['coverage_complete']]
        output.append(dict(experiment=metadata[0], electrodes=electrodes, sweeps=sweeps,
            summary=dict(sweeps=len(sweeps), recording_modes=dict(sorted(counts.items())),
                mixed_mode_sweeps=mixed, incomplete_mode_sweeps=incomplete,
                candidate_pairs=sum(len(s['classification']['candidates']) for s in sweeps))))
        print(json.dumps(dict(experiment=eid, summary=output[-1]['summary'])), flush=True)
    return dict(experiments=output, query_plans=plans)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--allow-download', action='store_true')
    parser.add_argument('--output', type=Path, default=HERE/'mixed_clamp_inventory_result.json')
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError('Preserve previous output')
    for name, digest in DEPENDENCIES.items():
        if sha(HERE/name) != digest:
            raise ValueError('Dependency changed: '+name)
    selection = json.loads(SELECTION.read_text(encoding='utf-8'))
    selected = [r for r in selection['screening'] if r['experiment'] in EXPERIMENTS]
    if {r['experiment'] for r in selected} != set(EXPERIMENTS):
        raise ValueError('Prior candidate provenance missing')
    with ReusingRanges(allow_download=args.allow_download) as reader:
        vfs, db = ReadVFS(reader), None
        try:
            db = apsw.Connection('remote.sqlite', flags=apsw.SQLITE_OPEN_READONLY, vfs='ce_medium_readonly')
            db.execute('PRAGMA query_only=ON')
            db.execute('PRAGMA temp_store=MEMORY')
            out = collect(db)
        except Exception:
            print(json.dumps(dict(status='INCOMPLETE', missing_blocks=sorted(reader.missing),
                used_base=len(reader.used_base), used_prior=len(reader.used_prior),
                used_overlay=len(reader.used_overlay), downloaded=reader.downloaded)), flush=True)
            raise
        finally:
            if db is not None:
                db.close()
            vfs.unregister()
        provenance = dict(remote=reader.remote, base_manifest_sha256=BASE_SHA, prior_manifest_sha256=PRIOR_SHA,
            used_base=reader.used_base, used_prior=reader.used_prior, used_overlay=reader.used_overlay,
            overlay_manifest=reader.manifest_path.relative_to(ROOT).as_posix(),
            overlay_manifest_sha256=sha(reader.manifest_path) if reader.manifest_path.exists() else None,
            downloaded_this_session=reader.downloaded, max_overlay_bytes=MAX_NEW)
    if sha(BASE/'manifest.json') != BASE_SHA or sha(PRIOR/'manifest.json') != PRIOR_SHA:
        raise ValueError('Parent cache changed during inventory')
    out.update(schema='allen.mixed-clamp-inventory.v1', source_sha256=sha(__file__),
        test_sha256=sha(ROOT/'tests/test_mixed_clamp_inventory.py'), dependency_sha256=DEPENDENCIES,
        selection_source_sha256=sha(SELECTION), prior_candidates=selected, provenance=provenance,
        python=platform.python_version(), apsw=apsw.apswversion(),
        scope='All medium-DB sync recordings in nominated experiments3338/3340/4863; all electrodes, including unknown/QC-failed metadata.',
        interpretation='Mixed IC-source/VC-target mode is only an observability candidate, not proof of observed source AP, PSC, connection or plasticity. '
                       'Absence in these experiments does not establish absence in the Allen dataset.')
    serialized = json.dumps(out, ensure_ascii=False, indent=2, allow_nan=False)
    with args.output.open('x', encoding='utf-8') as stream:
        stream.write(serialized)
    print(json.dumps(dict(output=str(args.output), downloaded=provenance['downloaded_this_session'])))


if __name__ == '__main__':
    main()
