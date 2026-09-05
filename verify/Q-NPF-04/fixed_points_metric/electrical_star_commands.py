"""Identify long-step current inputs and electrode settings without response data."""
import json
from pathlib import Path

import h5py
import numpy as np

from allen_joint_inventory import BASE, raw, sha, text

HERE = Path(__file__).resolve().parent


def segments(values, rate):
    cuts = np.r_[0,np.flatnonzero(np.abs(np.diff(values))>.05)+1,len(values)]
    return [dict(start_s=float(a/rate),end_s=float(b/rate),duration_s=float((b-a)/rate),
                 current_pA=float(np.mean(values[a:b])),sd_pA=float(np.std(values[a:b])))
            for a,b in zip(cuts[:-1],cuts[1:])]


def settings(comment, device):
    selected = {}
    prefix = f'HS#{device}:'
    for line in str(comment).split('\r'):
        if not line.startswith(prefix):
            continue
        key, separator, value = line[len(prefix):].partition(':')
        if separator and any(s in key for s in ['Holding','Bridge','Series Resistance','LPF','Pipette Offset','Clamp Mode']):
            selected[key] = value.strip()
    return selected


def main():
    output = HERE/'electrical_star_commands_result.json'
    if output.exists():
        raise FileExistsError(output)
    protocol_path = HERE/'electrical_star_protocol_result.json'
    protocol = json.loads(protocol_path.read_text(encoding='utf8'))
    raw.URL = protocol['remote']['url']
    raw.CACHE = BASE/'raw_ranges'/protocol['selection']['ext_id']
    manifest = json.loads((raw.CACHE/'manifest.json').read_text())
    raw.LIMIT = sum(b['bytes'] for b in manifest['blocks'].values())+32*1024*1024
    names, electrodes, commands = {}, [], []
    with raw.CachedRanges() as reader:
        assert reader.remote == protocol['remote']
        with h5py.File(reader,'r') as f:
            for row in protocol['records']:
                if row['kind']!='acquisition':
                    continue
                node = f[row['path']]
                d = node['stimulus_description'][()]
                label = text(d[0] if getattr(d,'shape',()) else d)
                names.setdefault(row['sweep'],{})[row['device']] = label
                if 'TargetV' in label:
                    electrodes.append(dict(sweep=row['sweep'],device=row['device'],
                        settings=settings(node.attrs.get('comment',''),row['device'])))
            target_sweeps = sorted(s for s,devices in names.items() if any('TargetV' in label for label in devices.values()))
            print('TARGET_SWEEPS',target_sweeps,flush=True)
            print('PROTOCOL_NAMES',sorted({name for ds in names.values() for name in ds.values()}),flush=True)
            for row in protocol['records']:
                if row['kind']!='command' or row['sweep'] not in target_sweeps:
                    continue
                if row['unit'] != 'A':
                    raise ValueError('TargetV command is not current clamp')
                values = (np.asarray(f[row['path']+'/data'][()],float)*row['conversion']+row['offset'])*1e12
                commands.append(dict(sweep=row['sweep'],device=row['device'],samples=len(values),rate=row['rate'],
                                     segments=segments(values,row['rate'])))
                print('COMMAND',row['sweep'],row['device'],flush=True)
        result = dict(code_sha256=sha(Path(__file__)),protocol_sha256=sha(protocol_path),
            remote=reader.remote,names=names,electrode_settings=electrodes,commands=commands,
            target_sweeps=target_sweeps,new_download_bytes=reader.downloaded_this_session,
            cached_bytes_total=sum(b['bytes'] for b in reader.manifest['blocks'].values()),
            scope='Command arrays and settings only; no acquisition waveform values opened',
            command_segment_threshold_pA=.05,
            limitations=['Settings are instrument metadata, not independent access-resistance estimates',
                         'Command arrays omit holding current, which remains a separate notebook setting'],
            claim_ceiling='BIO_EVIDENCE_L0 input eligibility')
    with output.open('x',encoding='utf8') as stream:
        json.dump(result,stream,ensure_ascii=False,indent=2,allow_nan=False)
        stream.write('\n')
    print('DONE',json.dumps(dict(target_sweeps=target_sweeps,new_bytes=result['new_download_bytes'],sha256=sha(output))),flush=True)


if __name__ == '__main__':
    main()
