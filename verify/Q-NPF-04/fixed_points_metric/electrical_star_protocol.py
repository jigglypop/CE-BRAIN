"""Read NWB channel metadata for the spatially spanning electrical-star candidate.

No acquisition waveform values are opened. Missing byte ranges are reusable.
"""
import json
from collections import Counter, defaultdict
from pathlib import Path

import h5py

from allen_joint_inventory import BASE, describe, raw, sha, text

HERE = Path(__file__).resolve().parent
EXT = '1552517188.758'


def main():
    output = HERE/'electrical_star_protocol_result.json'
    if output.exists():
        raise FileExistsError(output)
    inventory_path = HERE/'allen_electrical_inventory_result.json'
    inventory = json.loads(inventory_path.read_text(encoding='utf8'))
    assert inventory['selected_external_id'] == EXT
    selection = next(e for e in inventory['experiments'] if e['ext_id']==EXT)
    raw.URL = f'https://allen-synphys.s3-us-west-2.amazonaws.com/synphys-{EXT}.nwb'
    raw.CACHE = BASE/'raw_ranges'/EXT
    manifest_path = raw.CACHE/'manifest.json'
    existing_bytes = (sum(b['bytes'] for b in json.loads(manifest_path.read_text())['blocks'].values())
                      if manifest_path.exists() else 0)
    raw.LIMIT = existing_bytes+32*1024*1024
    with raw.CachedRanges() as reader:
        with h5py.File(reader, 'r') as f:
            records, examples = [], {}
            for kind, group_name in [('acquisition','acquisition/timeseries'),('command','stimulus/presentation')]:
                group = f[group_name]
                keys = sorted(k for k in group if k.startswith('data_') and 0<=int(k.split('_')[1])<=15)
                print('METADATA_CHANNELS',kind,len(keys),flush=True)
                for index,key in enumerate(keys):
                    node = group[key]
                    if 'electrode_name' not in node:
                        continue
                    record = describe(node)
                    record['kind'] = kind
                    for field in ['description','comments','source','stimulus_description']:
                        if field in node and isinstance(node[field],h5py.Dataset) and node[field].size<=16:
                            values = node[field][()]
                            record[field] = text(values[0] if getattr(values,'shape',()) else values)
                    records.append(record)
                    if kind not in examples:
                        examples[kind] = dict(fields=list(node), attributes={k:str(v) for k,v in node.attrs.items()},
                                              first_metadata=record)
                        print('FIRST_METADATA',kind,'fields',list(node),'device',record['device'],flush=True)
                    if (index+1)%200==0:
                        print('METADATA_PROGRESS',kind,index+1,'new_bytes',reader.downloaded_this_session,flush=True)
        channels = defaultdict(dict)
        for row in records:
            key = (row['sweep'],row['device'])
            assert row['kind'] not in channels[key]
            channels[key][row['kind']] = row
        summaries = defaultdict(list)
        devices = {c['device_id']:c['id'] for c in selection['cells']}
        for (sweep,device), paired in sorted(channels.items()):
            if set(paired)!= {'acquisition','command'}:
                raise ValueError('Missing channel pair')
            acq,cmd = paired['acquisition'],paired['command']
            units = (acq['unit'],cmd['unit'])
            summaries[sweep].append(dict(device=device,cell=devices.get(device),
                mode='ic' if units==('V','A') else 'vc' if units==('A','V') else 'unknown',
                clocks_match=all(acq[k]==cmd[k] for k in ['start','rate','samples']),
                samples=acq['samples'],rate=acq['rate'],description=acq.get('stimulus_description'),
                comments=cmd.get('comments'),source=cmd.get('source')))
        result = dict(code_sha256=sha(Path(__file__)),inventory_sha256=sha(inventory_path),
            raw_reader_sha256=sha(Path(raw.__file__)),metadata_reader_sha256=sha(HERE/'allen_joint_inventory.py'),
            scope='Metadata for sweeps 0..15 only: acquired voltage/current array values not inspected',selection=selection,
            metadata_sweep_scope=[0,15],
            scope_reason='Command labels identified initial TargetV 10..15 before response access; wider metadata-only scan stopped as unnecessary and all cached bytes reused',
            previously_cached_bytes=existing_bytes,
            remote=reader.remote,examples=examples,records=records,sweeps=dict(summaries),
            sweep_count=len(summaries),new_download_bytes=reader.downloaded_this_session,
            cached_bytes_total=sum(b['bytes'] for b in reader.manifest['blocks'].values()),
            claim_ceiling='BIO_EVIDENCE_L0 recording eligibility')
    with output.open('x',encoding='utf8') as stream:
        json.dump(result,stream,ensure_ascii=False,indent=2)
        stream.write('\n')
    print('DONE',json.dumps(dict(sweeps=result['sweep_count'],records=len(records),
        new_bytes=result['new_download_bytes'],sha256=sha(output))),flush=True)


if __name__ == '__main__':
    main()
