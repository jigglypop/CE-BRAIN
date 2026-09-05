"""같은 세포 위치와 NWB 전압/전류 채널을 보유 바이트만으로 결합한다."""
import hashlib
import io
import json
import sqlite3
import sys
from collections import Counter, defaultdict
from pathlib import Path
import h5py
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BASE = ROOT/'data/external/allen_synphys_r21'
sys.path.insert(0,str(HERE.parent/'allen_synphys'))
import raw_metadata as raw


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


class MissingBlock(OSError):
    pass


class OfflineRanges(raw.CachedRanges):
    def __init__(self, cache):
        io.RawIOBase.__init__(self)
        self.cache = cache
        self.manifest = json.loads((cache/'manifest.json').read_text(encoding='utf-8'))
        self.remote = self.manifest['remote']
        assert self.manifest['block_size'] == raw.BLOCK
        self.pos = 0
        self.used = {}
        self.missing = set()

    def block(self, start):
        path = self.cache/f'{start:012d}.bin'
        expected = self.manifest['blocks'].get(str(start))
        if expected is None or not path.exists():
            self.missing.add(start)
            raise MissingBlock(f'Uncached block {start}')
        data = path.read_bytes()
        assert len(data) == expected['bytes']
        assert hashlib.sha256(data).hexdigest() == expected['sha256']
        self.used[str(start)] = expected
        return data


def text(value):
    return value.decode() if isinstance(value,bytes) else str(value)


def describe(node):
    electrode = text(node['electrode_name'][()][0])
    data = node['data']
    return {'path':node.name,'sweep':int(node.name.split('/')[-1].split('_')[1]),
            'device':int(electrode.rsplit('_',1)[1]),'unit':text(data.attrs['unit']),
            'conversion':float(data.attrs['conversion']),'offset':float(data.attrs.get('offset',0.)),
            'rate':float(node['starting_time'].attrs['rate']),
            'start':float(node['starting_time'][()][0]),'samples':int(data.shape[0])}


def main():
    coordinate_result = json.loads((HERE/'allen_coordinates_result.json').read_text(encoding='utf-8'))
    database = BASE/'synphys_r2.1_small.sqlite'
    assert sha(database) == coordinate_result['database_sha256']
    results = []
    with sqlite3.connect(database.resolve().as_uri()+'?mode=ro',uri=True) as con:
        for cache in sorted((BASE/'raw_ranges').iterdir()):
            if not cache.is_dir() or not (cache/'manifest.json').exists():
                continue
            cells = []
            for row in con.execute('SELECT e.id,c.id,c.ext_id,c.electrode_id,el.device_id,c.position '
                                   'FROM experiment e JOIN cell c ON c.experiment_id=e.id '
                                   'JOIN electrode el ON el.id=c.electrode_id WHERE e.ext_id=? ORDER BY c.id',(cache.name,)):
                position = json.loads(row[5]) if row[5] is not None else None
                cells.append(dict(zip(('experiment','cell','cell_external','electrode','device','position'),row[:5]+(position,))))
            devices = {c['device']:c for c in cells}
            assert len(devices) == len(cells)
            channels = {'acquisition':[],'command':[]}
            failures = []
            with OfflineRanges(cache) as reader:
                with h5py.File(reader,'r') as f:
                    for label,group in [('acquisition','acquisition/timeseries'),('command','stimulus/presentation')]:
                        try:
                            for key in sorted(f[group]):
                                if key.startswith('data_') and 'electrode_name' in f[group][key]:
                                    channels[label].append(describe(f[group][key]))
                        except MissingBlock as error:
                            failures.append({'section':label,'reason':str(error)})
                provenance = {'remote':reader.remote,'used_blocks':reader.used,'missing_blocks':sorted(reader.missing)}
            commands = defaultdict(list)
            for row in channels['command']:
                commands[(row['sweep'],row['device'])].append(row)
            joined = []
            unpaired = []
            for row in channels['acquisition']:
                candidates = commands[(row['sweep'],row['device'])]
                if row['device'] not in devices or len(candidates) != 1:
                    unpaired.append({'acquisition':row,'command_candidates':len(candidates),'cell_found':row['device'] in devices})
                    continue
                command = candidates[0]
                clocks = all(row[k] == command[k] for k in ('start','rate','samples'))
                units = (row['unit'],command['unit'])
                joined.append({'cell':devices[row['device']],'acquisition':row,'command':command,
                               'clocks_match':clocks,'mode':'ic' if units==('V','A') else ('vc' if units==('A','V') else 'unknown')})
            sweeps = defaultdict(list)
            for row in joined:
                p = row['cell']['position']
                if row['clocks_match'] and row['mode'] != 'unknown' and p is not None and np.isfinite(p).all():
                    a = row['acquisition']
                    sweeps[(a['sweep'],a['start'],a['rate'],a['samples'])].append(row)
            geometry = []
            for key,rows in sorted(sweeps.items()):
                points = np.array([r['cell']['position'] for r in rows])
                singular = np.linalg.svd(points-points.mean(axis=0),compute_uv=False)
                tol = singular[0]*max(points.shape)*np.finfo(float).eps
                geometry.append({'sweep':key[0],'start':key[1],'rate':key[2],'samples':key[3],
                                 'cell_ids':[r['cell']['cell'] for r in rows],
                                 'modes':[r['mode'] for r in rows],
                                 'affine_rank':int(np.sum(singular>tol)),'singular_values':singular.tolist()})
            summary = {'external':cache.name,'db_cells':len(cells),'acquisition_metadata':len(channels['acquisition']),
                       'command_metadata':len(channels['command']),'joined_channels':len(joined),
                       'unpaired_channels':len(unpaired),'metadata_complete':not failures,
                       'synchronous_groups':len(geometry),
                       'rank_counts':dict(Counter(g['affine_rank'] for g in geometry)),
                       'max_cells_in_synchronous_group':max((len(g['cell_ids']) for g in geometry),default=0)}
            results.append({'summary':summary,'cells':cells,'joined':joined,'unpaired':unpaired,
                            'geometry':geometry,'cache_failures':failures,'provenance':provenance})
            print(json.dumps(summary),flush=True)
    result = {'code_sha256':sha(Path(__file__)),'reader_sha256':sha(Path(raw.__file__)),
              'database_sha256':coordinate_result['database_sha256'],'results':results,
              'scope':'All three existing raw cache directories; no signal values or network reads',
              'limitations':['Partial cache failure is not absent source data',
                             'Clock agreement and V/A labels do not establish membrane voltage correction or injection calibration',
                             'No spatial stimulation rank, balanced current, linearity or biological metric established'],
              'claim_ceiling':'BIO_EVIDENCE_L0_INPUT_JOIN'}
    with (HERE/'allen_joint_inventory_result.json').open('x',encoding='utf-8') as f:
        json.dump(result,f,ensure_ascii=False,indent=2,allow_nan=False)


if __name__ == '__main__':
    main()
