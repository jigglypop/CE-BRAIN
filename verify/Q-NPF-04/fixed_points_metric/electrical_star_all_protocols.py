"""Census all recording/command channel metadata in the same electrical-star NWB.

No acquisition or command data-array values are decoded. Protocol names and
instrument settings are exposed; previously extracted response summaries are
not copied into this census. A command label is not a calibrated intervention.
"""
import json
from collections import Counter, defaultdict
from pathlib import Path

import h5py
import numpy as np

from allen_joint_inventory import BASE, describe, raw, sha, text

HERE = Path(__file__).resolve().parent
OUTPUT = HERE / 'electrical_star_all_protocols_result.json'
TEXT_FIELDS = ['SweepNum', 'TimeStampSinceIgorEpochUTC', 'Stim Wave Name',
               'OperatingModeString', 'AD unit', 'DA unit', 'Electrode',
               'ScaledOutSignalString', 'RawOutSignalString',
               'High precision sweep start']
SETTING_FIELDS = ['SweepNum', 'TimeStampSinceIgorEpochUTC', 'EntrySourceType',
                  'Clamp Mode', 'Active Headstage', 'DAC', 'ADC',
                  'Stim Scale Factor', 'VC Holding Enable', 'VC Holding Level',
                  'IC Holding Enable', 'IC Holding Level', 'Sampling interval',
                  'RsComp Enable', 'Series Resistance', 'Whole Cell Comp Enable']


def scalar_metadata(node):
    result = {}
    for key in ['description', 'comments', 'source', 'stimulus_description']:
        if key in node and isinstance(node[key], h5py.Dataset) and node[key].size <= 16:
            result[key] = [text(v) for v in np.asarray(node[key]).ravel()]
    return result


def main():
    if OUTPUT.exists():
        raise FileExistsError(OUTPUT)
    code_hash = sha(Path(__file__))
    prior_path = HERE / 'electrical_star_protocol_result.json'
    prior = json.loads(prior_path.read_text(encoding='utf8'))
    nb_path = HERE / 'electrical_star_notebook_values_result.json'
    nb = json.loads(nb_path.read_text(encoding='utf8'))
    cache = BASE / 'raw_ranges' / prior['selection']['ext_id']
    initial_manifest = json.loads((cache / 'manifest.json').read_text())
    initial_bytes = sum(b['bytes'] for b in initial_manifest['blocks'].values())
    raw.URL, raw.CACHE, raw.LIMIT = prior['remote']['url'], cache, initial_bytes + 32 * 1024 * 1024
    with raw.CachedRanges() as reader:
        assert reader.remote == prior['remote']
        records, other_nodes, group_inventory = [], [], {}
        with h5py.File(reader, 'r') as f:
            for group_path in ['acquisition', 'stimulus', 'general', 'processing']:
                if group_path in f:
                    group_inventory[group_path] = list(f[group_path])
            for kind, group_path in [('acquisition', 'acquisition/timeseries'),
                                      ('command', 'stimulus/presentation')]:
                group = f[group_path]
                group_inventory[group_path] = list(group)
                for index, key in enumerate(sorted(group)):
                    node = group[key]
                    if not key.startswith('data_') or not isinstance(node, h5py.Group) or 'electrode_name' not in node:
                        other_nodes.append(dict(kind=kind, path=node.name, fields=list(node) if isinstance(node,h5py.Group) else [],
                                                shape=list(node.shape) if isinstance(node,h5py.Dataset) else None))
                        continue
                    rec = describe(node)
                    rec.update(kind=kind, fields=list(node), attributes={k:str(v) for k,v in node.attrs.items()},
                               **scalar_metadata(node))
                    records.append(rec)
                    if (index + 1) % 200 == 0:
                        print('CHANNEL_METADATA', kind, index + 1, 'new_bytes', reader.downloaded_this_session, flush=True)
            group = f[nb['group_path']]
            text_keys = [text(k) for k in group['textualKeys'][0]]
            indices = sorted(text_keys.index(k) for k in TEXT_FIELDS if k in text_keys)
            text_values = np.asarray(group['textualValues'][:, indices, :])
            text_records = []
            for index, row in enumerate(text_values):
                fields = {text_keys[k]:[text(v) for v in row[j]] for j,k in enumerate(indices)
                          if any(text(v) for v in row[j])}
                if fields:
                    text_records.append(dict(row=index, fields=fields))
        provenance = dict(remote=reader.remote, initial_cached_bytes=initial_bytes,
                          new_download_bytes=reader.downloaded_this_session, blocks=reader.manifest['blocks'])
    paired = defaultdict(lambda: defaultdict(list))
    for rec in records:
        paired[(rec['sweep'], rec['device'])][rec['kind']].append(rec)
    sweeps, anomalies = defaultdict(list), []
    for (sweep, device), kinds in sorted(paired.items()):
        if set(kinds) != {'acquisition', 'command'} or any(len(v) != 1 for v in kinds.values()):
            anomalies.append(dict(sweep=sweep, device=device, counts={k:len(v) for k,v in kinds.items()}))
            continue
        acq, cmd = kinds['acquisition'][0], kinds['command'][0]
        units = acq['unit'], cmd['unit']
        mode = 'ic' if units == ('V', 'A') else 'vc' if units == ('A', 'V') else 'unknown'
        sweeps[sweep].append(dict(device=device, mode=mode, acquisition_path=acq['path'], command_path=cmd['path'],
            clocks_match=all(acq[k] == cmd[k] for k in ['start', 'rate', 'samples']),
            start=acq['start'], rate=acq['rate'], samples=acq['samples'],
            description=acq.get('stimulus_description'), source=cmd.get('source')))
    settings = [dict(row=r['row'], fields={k:v for k,v in r['fields'].items() if k in SETTING_FIELDS})
                for r in nb['numerical_records'] if any(k in SETTING_FIELDS for k in r['fields'])]
    labels = Counter(v for r in text_records for v in r['fields'].get('Stim Wave Name', []) if v)
    summary = dict(sweep_count=len(sweeps), min_sweep=min(sweeps), max_sweep=max(sweeps),
        channel_records=dict(Counter(r['kind'] for r in records)),
        mode_channel_counts=dict(Counter(r['mode'] for rows in sweeps.values() for r in rows)),
        protocol_label_counts=dict(labels), unpaired_channel_groups=len(anomalies), other_nodes=len(other_nodes),
        all_paired_clocks_match=all(r['clocks_match'] for rows in sweeps.values() for r in rows),
        new_download_bytes=provenance['new_download_bytes'])
    assert sha(Path(__file__)) == code_hash
    result = dict(code_sha256=code_hash, prior_protocol_sha256=sha(prior_path), notebook_values_sha256=sha(nb_path),
        raw_reader_sha256=sha(Path(raw.__file__)), metadata_reader_sha256=sha(HERE/'allen_joint_inventory.py'),
        scope='Entire acquisition/timeseries and stimulus/presentation channel metadata plus selected protocol text and settings; no data-array values',
        summary=summary, records=records, sweeps=dict(sweeps), unpaired=anomalies, other_nodes=other_nodes,
        group_inventory=group_inventory, textual_fields_selected=[text_keys[k] for k in indices], textual_records=text_records,
        settings_fields_requested=SETTING_FIELDS, settings_records=settings, provenance=provenance,
        claim_ceiling='BIO_EVIDENCE_L0 input eligibility; labels do not establish actual command amplitude, calibrated membrane voltage, or current response')
    with OUTPUT.open('x', encoding='utf8') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')
    print('DONE', json.dumps(summary), 'sha256', sha(OUTPUT), flush=True)


if __name__ == '__main__':
    main()
