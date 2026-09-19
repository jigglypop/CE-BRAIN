"""Bind all mixed-mode candidates to released cell, pulse, response and QC IDs.

This inventory reads metadata, not raw waveforms or fitted response amplitudes.
Reported AP detection remains to be checked against the actual source trace.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import platform

import mixed_clamp_inventory as inv
from vc20hz_measurement_state import indexed_query

HERE, ROOT, sha = inv.HERE, inv.ROOT, inv.sha
INPUT = HERE/'mixed_clamp_inventory_result.json'
INPUT_SHA = '0852aaa1ea1270965d25e2315d9d05a8d1b69e8340ba848196fad11854370cee'
SMALL = ROOT/'data/external/allen_synphys_r21/synphys_r2.1_small.sqlite'
SMALL_SHA = '7372499fdd874f057565080d5769baaf2659ef39d9f3bc3c7147dd1e1c280a53'
MODE_OVERLAY_SHA = '37e856069f55083c5489f705405bd7f5aa9d012391a27328e250dc003cc3abbf'
SOURCE_SHA = '31c37d3afdfa49e55c76c301e798eab843ae63763d52969cc28a3403b94f4870'
OVERLAY = ROOT/'data/external/allen_synphys_r21/mixed_clamp_pulse_ranges/v1'
PULSE_SQL = ('SELECT id,recording_id,cell_id,pulse_number,onset_time,amplitude,duration,'
    'n_spikes,first_spike_time,qc_pass,previous_pulse_dt '
    'FROM stim_pulse INDEXED BY ix_stim_pulse_recording_id WHERE recording_id=?')
RESPONSE_SQL = ('SELECT pr.id,pr.recording_id,pr.pair_id,pr.stim_pulse_id,pr.baseline_id,'
    'pr.ex_qc_pass,pr.in_qc_pass FROM pulse_response pr '
    'INDEXED BY ix_pulse_response_recording_id WHERE pr.recording_id=?')


class StageRanges(inv.ReusingRanges):
    def __init__(self, allow_download=False):
        super().__init__(overlay=OVERLAY, allow_download=allow_download,
                         prior=inv.OVERLAY, prior_sha=MODE_OVERLAY_SHA)
        if sha(inv.PRIOR/'manifest.json') != inv.PRIOR_SHA:
            raise ValueError('Earlier VC cache changed')
        self.older = json.loads((inv.PRIOR/'manifest.json').read_text(encoding='utf-8'))
        self.used_older = {}

    def block(self, start):
        key = str(start)
        if start not in self.memo and all(key not in m['blocks']
                for m in (self.base_manifest, self.prior_manifest, self.manifest)):
            entry = self.older['blocks'].get(key)
            if entry is not None:
                data = (inv.PRIOR/f'{start:012d}.bin').read_bytes()
                if len(data) != entry['bytes'] or hashlib.sha256(data).hexdigest() != entry['sha256']:
                    raise ValueError('Corrupt earlier VC block')
                self.memo[start], self.used_older[key] = data, entry
                return data
        return super().block(start)


def detected_single(pulse):
    t = pulse['first_spike_time']
    return pulse['n_spikes'] == 1 and t is not None and math.isfinite(t)


def summarize(pre, post, pulses, responses, pair):
    if pre['sync_rec_id'] != post['sync_rec_id'] or (pre['clamp_mode'], post['clamp_mode']) != ('ic','vc'):
        raise ValueError('Candidate timing or clamp mismatch')
    by_id = {p['id']: p for p in pulses}
    if len(by_id) != len(pulses) or any(p['recording_id'] != pre['id'] or
            (p['cell_id'] is not None and p['cell_id'] != pair['pre_cell_id']) for p in pulses):
        raise ValueError('Source pulse identity mismatch')
    if any(r['recording_id'] != post['id'] or r['pair_id'] != pair['id'] or r['stim_pulse_id'] not in by_id for r in responses):
        raise ValueError('Response identity mismatch')
    ids = [r['stim_pulse_id'] for r in responses]
    if len(set(ids)) != len(ids):
        raise ValueError('Duplicate response to a source pulse')
    both = pre['qc_pass'] == post['qc_pass'] == 1
    single = [p for p in pulses if detected_single(p)]
    return dict(source_pulses=len(pulses), response_rows=len(responses),
        pulse_cell_id_missing=sum(p['cell_id'] is None for p in pulses),
        pulse_qc_missing=sum(p['qc_pass'] is None for p in pulses),
        detected_single_spike_pulses=len(single),
        single_spike_source_qc_pulses=sum(p['qc_pass'] == 1 for p in single),
        response_ex_qc_passed=sum(r['ex_qc_pass'] == 1 for r in responses),
        response_in_qc_passed=sum(r['in_qc_pass'] == 1 for r in responses),
        both_recording_qc_passed=both,
        recording_response_qc_single_spikes=sum(both and r['ex_qc_pass'] == 1
            and detected_single(by_id[r['stim_pulse_id']]) for r in responses),
        single_spike_ex_qc_responses=sum(both and r['ex_qc_pass'] == 1 and by_id[r['stim_pulse_id']]['qc_pass'] == 1
            and detected_single(by_id[r['stim_pulse_id']]) for r in responses),
        pulses_without_response=sorted(set(by_id)-set(ids)))


def annotations(candidates, plans):
    ids = sorted({e for c in candidates for e in (c['source_electrode'],c['target_electrode'])})
    with inv.apsw.Connection(str(SMALL), flags=inv.apsw.SQLITE_OPEN_READONLY) as db:
        lookup = lambda sql,args: indexed_query(db,sql,args,plans)
        cells = lookup('SELECT id,experiment_id,ext_id,electrode_id,cre_type,target_layer,cell_class,cell_class_nonsynaptic '
            'FROM cell INDEXED BY ix_cell_electrode_id WHERE electrode_id IN ('+','.join('?' for _ in ids)+')', tuple(ids))
        cell_map = {c['electrode_id']:c for c in cells}
        if len(cells) != len(ids) or set(cell_map) != set(ids) or any(c['experiment_id'] != 4863 for c in cells):
            raise ValueError('Cell annotation identity mismatch')
        pairs = []
        for a,b in sorted({(c['source_electrode'],c['target_electrode']) for c in candidates}):
            rows = lookup('SELECT p.id,p.experiment_id,p.pre_cell_id,p.post_cell_id,p.has_synapse,p.has_polysynapse,p.has_electrical,'
                's.id AS synapse_id,s.synapse_type,d.id AS dynamics_id,d.qc_pass AS dynamics_qc_pass '
                'FROM pair p INDEXED BY ix_pair_pre_cell_id '
                'LEFT JOIN synapse s INDEXED BY ix_synapse_pair_id ON s.pair_id=p.id '
                'LEFT JOIN dynamics d INDEXED BY ix_dynamics_pair_id ON d.pair_id=p.id '
                'WHERE p.pre_cell_id=? AND p.post_cell_id=?',(cell_map[a]['id'],cell_map[b]['id']))
            if len(rows) != 1 or rows[0]['experiment_id'] != 4863:
                raise ValueError('Pair annotation identity mismatch')
            pairs.append(dict(rows[0],source_electrode=a,target_electrode=b))
    db.close()
    return dict(cells=cells,pairs=pairs)


def collect(db, mode, annotation, plans):
    lookup = lambda sql,args: indexed_query(db,sql,args,plans)
    by_electrode = {(p['source_electrode'],p['target_electrode']):p for p in annotation['pairs']}
    for p in annotation['pairs']:
        rows = lookup('SELECT id,experiment_id,pre_cell_id,post_cell_id FROM pair WHERE id=?',(p['id'],))
        if len(rows) != 1 or any(rows[0][k] != p[k] for k in rows[0]):
            raise ValueError('Small/medium pair mapping mismatch')
    output = []
    for sweep in mode['sweeps']:
        candidates = sweep['classification']['candidates']
        if not candidates:
            continue
        records = {r['id']:r for r in sweep['records']}
        source = {rid:lookup(PULSE_SQL,(rid,)) for rid in sorted({c['source_recording'] for c in candidates})}
        responses = {rid:lookup(RESPONSE_SQL,(rid,)) for rid in sorted({c['target_recording'] for c in candidates})}
        wanted = {p['id'] for p in annotation['pairs']}
        if any(r['pair_id'] not in wanted for rr in responses.values() for r in rr):
            raise ValueError('Unmapped target response pair')
        candidate_rows = []
        for c in candidates:
            pre,post = records[c['source_recording']],records[c['target_recording']]
            pair = by_electrode[c['source_electrode'],c['target_electrode']]
            rr = [r for r in responses[post['id']] if r['pair_id'] == pair['id']]
            candidate_rows.append(dict(c,pair_id=pair['id'],summary=summarize(pre,post,source[pre['id']],rr,pair)))
        output.append(dict(sweep=sweep['sweep'],sync_rec_id=sweep['sync_rec_id'],records=sweep['records'],
            source_pulses=source,target_responses=responses,candidates=candidate_rows))
    totals = []
    for pair in annotation['pairs']:
        rows = [c for s in output for c in s['candidates'] if c['pair_id'] == pair['id']]
        summed = {k:sum(c['summary'][k] for c in rows) for k in ('source_pulses','response_rows',
            'pulse_cell_id_missing','pulse_qc_missing','detected_single_spike_pulses','single_spike_source_qc_pulses','response_ex_qc_passed',
            'response_in_qc_passed','recording_response_qc_single_spikes','single_spike_ex_qc_responses')}
        totals.append(dict(pair_id=pair['id'],has_synapse=pair['has_synapse'],candidate_recordings=len(rows),
                           both_recording_qc_passed=sum(c['summary']['both_recording_qc_passed'] for c in rows),**summed))
    return dict(sweeps=output,totals=totals)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--allow-download',action='store_true')
    parser.add_argument('--output',type=Path,default=HERE/'mixed_clamp_pulses_result.json')
    args=parser.parse_args()
    if args.output.exists():
        raise FileExistsError('Preserve prior result')
    if sha(INPUT) != INPUT_SHA or sha(Path(inv.__file__)) != SOURCE_SHA or sha(SMALL) != SMALL_SHA:
        raise ValueError('Frozen input/source changed')
    for name,digest in inv.DEPENDENCIES.items():
        if sha(HERE/name) != digest:
            raise ValueError('Dependency changed: '+name)
    mode=next(e for e in json.loads(INPUT.read_text(encoding='utf-8'))['experiments'] if e['experiment']['id']==4863)
    candidates=[c for s in mode['sweeps'] for c in s['classification']['candidates']]
    plans=[]
    annotation=annotations(candidates,plans)
    with StageRanges(args.allow_download) as reader:
        vfs,db=inv.ReadVFS(reader),None
        try:
            db=inv.apsw.Connection('remote.sqlite',flags=inv.apsw.SQLITE_OPEN_READONLY,vfs='ce_medium_readonly')
            db.execute('PRAGMA query_only=ON');db.execute('PRAGMA temp_store=MEMORY')
            result=collect(db,mode,annotation,plans)
        except Exception:
            print(json.dumps(dict(status='INCOMPLETE',missing_blocks=sorted(reader.missing),downloaded=reader.downloaded)),flush=True)
            raise
        finally:
            if db is not None:db.close()
            vfs.unregister()
        provenance=dict(remote=reader.remote,base_manifest_sha256=inv.BASE_SHA,mode_overlay_sha256=MODE_OVERLAY_SHA,
            earlier_vc_overlay_sha256=inv.PRIOR_SHA,used_base=reader.used_base,used_mode_overlay=reader.used_prior,
            used_earlier_vc_overlay=reader.used_older,used_new_overlay=reader.used_overlay,
            overlay_manifest=reader.manifest_path.relative_to(ROOT).as_posix(),
            overlay_manifest_sha256=sha(reader.manifest_path) if reader.manifest_path.exists() else None,
            downloaded_this_session=reader.downloaded,max_overlay_bytes=inv.MAX_NEW)
    for path,digest in ((SMALL,SMALL_SHA),(inv.BASE/'manifest.json',inv.BASE_SHA),
            (inv.PRIOR/'manifest.json',inv.PRIOR_SHA),(inv.OVERLAY/'manifest.json',MODE_OVERLAY_SHA)):
        if sha(path) != digest:raise ValueError('Parent changed during read')
    result.update(schema='allen.mixed-clamp-pulses.v1',source_sha256=sha(__file__),
        test_sha256=sha(ROOT/'tests/test_mixed_clamp_pulses.py'),mode_inventory_sha256=INPUT_SHA,
        small_database_sha256=SMALL_SHA,dependency_sha256=dict(inv.DEPENDENCIES,**{'mixed_clamp_inventory.py':SOURCE_SHA}),
        annotation=annotation,query_plans=plans,provenance=provenance,python=platform.python_version(),apsw=inv.apsw.apswversion(),
        interpretation='All four directed mixed-mode pairs retained, including no-reported-synapse and QC-failed rows. '
        'Null pulse cell/QC metadata retained; identity instead follows verified recording/electrode/cell and pair mappings. '
        'Recording/response QC plus detected single AP and the stricter all-present pulse-QC count are separately reported. '
        'Released single-spike and response-QC metadata only; no raw source AP or target-current waveform inspected, no response fitting.')
    serialized=json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)
    with args.output.open('x',encoding='utf-8') as stream:stream.write(serialized)
    print(json.dumps(dict(totals=result['totals'],new_bytes=provenance['downloaded_this_session'])))


if __name__=='__main__':main()
