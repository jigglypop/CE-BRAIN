"""Offline instrument settings from the 21 original VC acquisition groups."""
import argparse
import json
from pathlib import Path

import h5py
import numpy as np

from vc20hz_source_inputs import HERE, ROOT, LayeredRanges, sha

FIELDS = ('resistance_comp_bandwidth', 'resistance_comp_correction', 'resistance_comp_prediction',
          'whole_cell_capacitance_comp', 'whole_cell_series_resistance_comp', 'capacitance_fast', 'capacitance_slow')
NOTE_FIELDS = ('Fast compensation capacitance', 'Slow compensation capacitance', 'Fast compensation time',
               'Slow compensation time', 'RsComp Bandwidth', 'RsComp Correction', 'RsComp Enable',
               'RsComp Prediction', 'Whole Cell Comp Enable', 'Whole Cell Comp Cap',
               'Whole Cell Comp Resist', 'Series Resistance', 'V-Clamp Holding Enable', 'V-Clamp Holding Level')


def plain(value):
    if isinstance(value, bytes):
        return value.decode('utf-8')
    if isinstance(value, np.ndarray):
        return plain(value.tolist())
    if isinstance(value, np.generic):
        return plain(value.item())
    if isinstance(value, list):
        return [plain(v) for v in value]
    return value


def comment_settings(comment, device):
    selected = {}
    prefix = 'HS#'+str(device)+':'
    for line in comment.replace('\r', '\n').splitlines():
        if line.startswith(prefix):
            key, separator, value = line[len(prefix):].partition(':')
            if separator and key.startswith(('RsComp ', 'Whole Cell Comp ', 'Series Resistance',
                                             'Fast compensation', 'Slow compensation')):
                if key in selected and selected[key] != value.strip():
                    raise ValueError('Conflicting instrument comment')
                selected[key] = value.strip()
    return selected


def numeric_settings(keys, values, sweep, device, requested=NOTE_FIELDS):
    """Use explicitly classified acquisition rows; reject ambiguous setting changes."""
    fields = {k: i for i, k in enumerate(keys)}
    candidate = np.flatnonzero(values[:, fields['SweepNum'], 0] == sweep)
    types = values[candidate, fields['EntrySourceType'], 0]
    if not len(candidate) or not np.isfinite(types).all():
        raise ValueError('Explicit EntrySourceType required for this extractor')
    selected = candidate[types == 0]
    if not len(selected):
        raise ValueError('No acquisition notebook rows')
    result = {}
    for name in requested:
        if name not in fields:
            result[name] = dict(value=None, raw_row_indices=[])
            continue
        field = fields[name]
        local = values[selected, field, device].copy()
        global_values = values[selected, field, 8]
        global_mask = np.isfinite(global_values)
        local[global_mask] = global_values[global_mask]
        finite = np.isfinite(local)
        unique = np.unique(local[finite])
        if len(unique) > 1:
            raise ValueError('Conflicting acquisition settings: '+name)
        result[name] = dict(value=float(unique[0]) if len(unique) else None,
                            raw_row_indices=selected[finite].tolist())
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=HERE/'vc20hz_compensation_result.json')
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError('Preserve prior output')
    if sha(HERE/'vc20hz_source_inputs.py') != '2a10fbf34a3c15b0f33765baf6b335249ebb06647d47cda6429b4d6b123227cb':
        raise ValueError('Frozen reader changed')
    records = []
    with LayeredRanges(allow_download=False) as reader:
        with h5py.File(reader, 'r') as nwb:
            notebook = nwb['general/labnotebook/ITC1600_Dev_0']
            keys = plain(notebook['numericalKeys'][0])
            values = np.asarray(notebook['numericalValues'])
            for sweep in range(7):
                for device, channel in ((2, 'AD2'), (4, 'AD8'), (5, 'AD9')):
                    group = nwb[f'acquisition/timeseries/data_{sweep:05d}_{channel}']
                    settings = comment_settings(plain(group.attrs['comment']), device)
                    numeric = numeric_settings(keys, values, sweep, device)
                    rs = {0.: False, 1.: True}.get(numeric['RsComp Enable']['value'])
                    whole = {0.: False, 1.: True}.get(numeric['Whole Cell Comp Enable']['value'])
                    comment_rs = {'On': True, 'Off': False}.get(settings.get('RsComp Enable'))
                    comment_whole = {'On': True, 'Off': False}.get(settings.get('Whole Cell Comp Enable'))
                    if any(c is not None and c != n for c, n in ((comment_rs, rs), (comment_whole, whole))):
                        raise ValueError('Comment and numeric enable settings disagree')
                    records.append(dict(sweep=sweep, device=device, channel=channel, path=group.name,
                        missing_fields=plain(group.attrs.get('missing_fields', [])),
                        datasets={name: plain(group[name][()]) if name in group else None for name in FIELDS},
                        instrument_comment=settings,
                        notebook_numeric=numeric, enable_source='labnotebook EntrySourceType=0 numeric settings',
                        comment_rs_enabled=comment_rs, comment_whole_cell_enabled=comment_whole,
                        rs_compensation_enabled=rs, whole_cell_compensation_enabled=whole,
                        fast_slow_enable='No separate enable field established; numerical capacitances are settings.'))
        provenance = dict(remote=reader.remote, base_manifest_sha256=reader.base_sha,
            used_base=reader.used_base, used_overlay=reader.used_overlay, downloaded_this_session=reader.downloaded,
            overlay_manifest_sha256=sha(reader.manifest_path))
    out = dict(schema='allen.vc20hz.compensation.v1', source_sha256=sha(__file__),
        test_sha256=sha(ROOT/'tests/test_vc20hz_compensation.py'),
        records=records, provenance=provenance,
        units=dict(capacitance_fast='F', capacitance_slow='F', comments='Units retained verbatim; rounded display.'),
        interpretation='Instrument settings, not membrane capacitance estimates. Missing datasets are not zeros; disabled circuits are not applied compensation.',
        definitions=['https://alleninstitute.github.io/MIES/labnotebook-descriptions.html',
                     'https://alleninstitute.github.io/MIES/IPNWB/doc/nwb1.html'])
    serialized = json.dumps(out, indent=2, allow_nan=False)
    with args.output.open('x', encoding='utf-8') as stream:
        stream.write(serialized)
    print(json.dumps(dict(records=len(records), new_bytes=provenance['downloaded_this_session'], output=str(args.output))))


if __name__ == '__main__':
    main()
