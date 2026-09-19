"""Complete seven VC input records using an immutable base and bounded overlay.

Default is offline. --allow-download admits only missing byte ranges from the
same remote ETag. This extracts measurements; it does not identify synaptic PSCs.
"""
import argparse
import hashlib
import io
import json
import platform
import urllib.request
from pathlib import Path

import h5py
import numpy as np

import raw_metadata as raw

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BASE = ROOT/'data/external/allen_synphys_r21/raw_ranges/1574292898.139'
OVERLAY = ROOT/'data/external/allen_synphys_r21/vc20hz_ranges/1574292898.139'
BASE_SHA = 'dfea65157ac4bfc8af5aae0c08964b6c4258e631655d9cd17a3c4140ff06b15d'
MAX_NEW = 16*1024*1024


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


class LayeredRanges(raw.CachedRanges):
    def __init__(self, base=BASE, overlay=OVERLAY, allow_download=False,
                 expected_base_sha=BASE_SHA, max_new=MAX_NEW):
        io.RawIOBase.__init__(self)
        self.base, self.overlay = Path(base), Path(overlay)
        self.base_sha = sha(self.base/'manifest.json')
        if self.base_sha != expected_base_sha:
            raise ValueError('Base manifest changed')
        self.base_manifest = json.loads((self.base/'manifest.json').read_text(encoding='utf-8'))
        self.remote = self.base_manifest['remote']
        if self.base_manifest['block_size'] != raw.BLOCK:
            raise ValueError('Unexpected block size')
        self.manifest_path = self.overlay/'manifest.json'
        self.manifest = dict(remote=self.remote, block_size=raw.BLOCK,
                             base_manifest_sha256=self.base_sha, blocks={})
        if self.manifest_path.exists():
            saved = json.loads(self.manifest_path.read_text(encoding='utf-8'))
            if any(saved.get(k)!=self.manifest[k] for k in ('remote','block_size','base_manifest_sha256')):
                raise ValueError('Overlay identity mismatch')
            self.manifest = saved
        self.pos, self.downloaded = 0, 0
        self.allow_download, self.max_new = allow_download, max_new
        self.remote_verified = False
        self.used_base, self.used_overlay, self.missing = {}, {}, set()
        self.memo = {}

    def verify_remote(self):
        request = urllib.request.Request(self.remote['url'],method='HEAD')
        with urllib.request.urlopen(request,timeout=30) as response:
            if (response.headers.get('ETag')!=self.remote['etag'] or
                    int(response.headers['Content-Length'])!=self.remote['bytes']):
                raise ValueError('Remote version changed')
        self.remote_verified = True

    def block(self,start):
        if start in self.memo:
            return self.memo[start]
        for folder, manifest, used in ((self.base,self.base_manifest,self.used_base),
                                       (self.overlay,self.manifest,self.used_overlay)):
            record = manifest['blocks'].get(str(start))
            if record is not None:
                value = (folder/f'{start:012d}.bin').read_bytes()
                if len(value)!=record['bytes'] or hashlib.sha256(value).hexdigest()!=record['sha256']:
                    raise ValueError(f'Corrupt cached block {start}')
                used[str(start)] = record
                self.memo[start] = value
                return value
        self.missing.add(start)
        if not self.allow_download:
            raise OSError(f'Offline missing block {start}')
        end = min(start+raw.BLOCK,self.remote['bytes'])-1
        if sum(v['bytes'] for v in self.manifest['blocks'].values())+end-start+1>self.max_new:
            raise RuntimeError('Overlay byte limit reached')
        if not self.remote_verified:
            self.verify_remote()
        request = urllib.request.Request(self.remote['url'],headers={
            'Range':f'bytes={start}-{end}','If-Match':self.remote['etag']})
        with urllib.request.urlopen(request,timeout=30) as response:
            if (response.status!=206 or response.headers.get('Content-Range')!=f'bytes {start}-{end}/{self.remote["bytes"]}'
                    or response.headers.get('ETag')!=self.remote['etag']):
                raise ValueError('Unexpected ranged response')
            value = response.read(end-start+2)
        if len(value)!=end-start+1:
            raise ValueError('Truncated or oversized range')
        self.overlay.mkdir(parents=True,exist_ok=True)
        path = self.overlay/f'{start:012d}.bin'
        # An interrupted write is never silently accepted as a valid block.
        with path.open('xb') as stream:
            stream.write(value)
        record = dict(bytes=len(value),sha256=hashlib.sha256(value).hexdigest())
        self.manifest['blocks'][str(start)] = record
        temp = self.manifest_path.with_suffix('.tmp')
        temp.write_text(json.dumps(self.manifest,indent=2),encoding='utf-8')
        temp.replace(self.manifest_path)
        self.used_overlay[str(start)] = record
        self.memo[start] = value
        self.downloaded += len(value)
        return value


def text(value):
    return value.decode() if isinstance(value,bytes) else str(value)


def command_intervals(values,rate,threshold=.0001):
    """All excursions from initial command, including any test pulses."""
    values = np.asarray(values,float)
    if values.ndim!=1 or not len(values) or not np.isfinite(values).all() or rate<=0:
        raise ValueError('Invalid command')
    baseline = float(values[0])
    active = np.abs(values-baseline)>threshold
    boundaries = np.diff(np.r_[False,active,False].astype(np.int8))
    starts,stops = np.flatnonzero(boundaries==1),np.flatnonzero(boundaries==-1)
    return [dict(start_index=int(a),stop_index=int(b),start_s=float(a/rate),
                 duration_s=float((b-a)/rate),delta_min_V=float(np.min(values[a:b])-baseline),
                 delta_max_V=float(np.max(values[a:b])-baseline)) for a,b in zip(starts,stops)]


def extract(reader):
    arrays,rows = {},[]
    with h5py.File(reader,'r') as handle:
        for sweep in range(7):
            for group,channels,unit in (('acquisition/timeseries',('AD9','AD8','AD2'),'A'),
                                         ('stimulus/presentation',('DA5','DA4','DA2'),'V')):
                for channel in channels:
                    node = handle[f'{group}/data_{sweep:05d}_{channel}']
                    dataset = node['data']
                    actual_unit = text(dataset.attrs['unit'])
                    conversion = float(dataset.attrs['conversion'])
                    offset = float(dataset.attrs.get('offset',0))
                    rate = float(node['starting_time'].attrs['rate'])
                    start = float(np.asarray(node['starting_time'][()]).ravel()[0])
                    if actual_unit!=unit or dataset.shape!=(505902,) or rate!=100000:
                        raise ValueError('Unexpected measurement schema')
                    if not np.isfinite([conversion,offset,start]).all() or conversion<=0:
                        raise ValueError('Invalid clock or conversion')
                    values = np.asarray(dataset[()],dtype=np.float64)*conversion+offset
                    if not np.isfinite(values).all():
                        raise ValueError('Nonfinite recording')
                    key = f's{sweep}_{channel}_{unit}'
                    arrays[key] = values
                    row = dict(sweep=sweep,channel=channel,path=node.name,array_key=key,
                               unit=unit,conversion=conversion,offset=offset,rate=rate,start=start,
                               samples=len(values),dtype=str(dataset.dtype),
                               electrode=text(np.asarray(node['electrode_name'][()]).ravel()[0]))
                    for name in ('comments','description','neurodata_type'):
                        if name in node.attrs:
                            row[name] = text(node.attrs[name])
                        elif name in node:
                            row[name] = text(node[name][()])
                    if unit=='V':
                        row['initial_command_V'] = float(values[0])
                        row['all_command_intervals'] = command_intervals(values,rate)
                    rows.append(row)
            clocks = {(r['start'],r['rate'],r['samples']) for r in rows if r['sweep']==sweep}
            if len(clocks)!=1:
                raise ValueError('Channel clock mismatch')
            print(f'Completed sweep {sweep}: six full channels',flush=True)
    return arrays,rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--allow-download',action='store_true')
    parser.add_argument('--output',type=Path,default=HERE/'vc20hz_source_inputs_result.json')
    parser.add_argument('--array-output',type=Path,default=ROOT/'data/local/allen-synphys-analysis/vc20hz-inputs-v1/full_inputs.npz')
    args = parser.parse_args()
    if args.output.exists() or args.array_output.exists():
        raise FileExistsError('Preserve existing extraction outputs')
    with LayeredRanges(allow_download=args.allow_download) as reader:
        arrays,rows = extract(reader)
        provenance = dict(remote=reader.remote,base_manifest=str((BASE/'manifest.json').relative_to(ROOT)),
            base_manifest_sha256=reader.base_sha,used_base=reader.used_base,used_overlay=reader.used_overlay,
            downloaded_this_session=reader.downloaded,overlay_bytes=sum(r['bytes'] for r in reader.manifest['blocks'].values()),
            overlay_manifest=str(reader.manifest_path.relative_to(ROOT)),overlay_manifest_sha256=sha(reader.manifest_path))
    if sha(BASE/'manifest.json')!=BASE_SHA:
        raise ValueError('Base cache changed during extraction')
    args.array_output.parent.mkdir(parents=True,exist_ok=True)
    with args.array_output.open('xb') as stream:
        np.savez_compressed(stream,**arrays)
    result = dict(schema='allen.vc20hz.source-inputs.v1',source_sha256=sha(__file__),
        test_sha256=sha(ROOT/'tests/test_vc20hz_source_inputs.py'),python=platform.python_version(),
        numpy=np.__version__,h5py=h5py.__version__,provenance=provenance,records=rows,
        arrays=dict(path=args.array_output.relative_to(ROOT).as_posix(),bytes=args.array_output.stat().st_size,sha256=sha(args.array_output)),
        interpretation='Command-locked clamp currents; no independent source Vm/AP channel; not identified PSCs or plasticity.')
    with args.output.open('x',encoding='utf-8') as stream:
        json.dump(result,stream,ensure_ascii=False,indent=2)
    print(json.dumps(dict(records=len(rows),arrays=len(arrays),new_bytes=provenance['downloaded_this_session'],
                         array_bytes=args.array_output.stat().st_size,output=str(args.output)),ensure_ascii=True))


if __name__=='__main__':
    main()
