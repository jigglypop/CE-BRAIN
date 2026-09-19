"""Read bounded zero-origin EDF+C records without interpreting behavioral clocks.

Only completed, continuous EDF+ with exactly one annotation channel is supported.
Physical values retain each header's unit. Annotations are consecutive raw bytes,
never calibrated voltage or the low byte of each int16. No network or filtering.
Specification: https://www.edfplus.info/specs/edfplus.html
"""
from __future__ import annotations

from decimal import Decimal
import math
import re

import numpy as np


def _integer(value, name):
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, (int, np.integer)):
        raise ValueError(f'{name} must be an integer')
    return int(value)


def parse_header(raw: bytes) -> dict:
    if len(raw) < 256:
        raise ValueError('short fixed header')
    def field(start, end):
        return raw[start:end].decode('ascii', errors='strict').strip()
    if field(0, 8) != '0' or not field(192, 236).startswith('EDF+C'):
        raise ValueError('only continuous EDF+C is supported')
    ns = int(field(252, 256))
    size = int(field(184, 192))
    if ns < 2 or size != 256 + 256 * ns or len(raw) != size:
        raise ValueError('header size mismatch')
    records = int(field(236, 244))
    duration_text = field(244, 252)
    duration = float(duration_text)
    if records <= 0 or not math.isfinite(duration) or duration <= 0:
        raise ValueError('completed positive-duration records required')
    pos, columns = 256, []
    for width in (16, 80, 8, 8, 8, 8, 8, 80, 8, 32):
        columns.append([field(pos + i * width, pos + (i + 1) * width) for i in range(ns)])
        pos += width * ns
    signals, offset = [], 0
    for i in range(ns):
        label = columns[0][i]
        samples = int(columns[8][i])
        if not label or samples <= 0:
            raise ValueError('empty label or invalid samples per record')
        sig = dict(label=label, unit=columns[2][i], samples_per_record=samples,
                   byte_offset=offset, annotation=label == 'EDF Annotations')
        if not sig['annotation']:
            lo, hi = float(columns[3][i]), float(columns[4][i])
            dlo, dhi = int(columns[5][i]), int(columns[6][i])
            if not all(map(math.isfinite, (lo, hi))) or hi == lo or not -32768 <= dlo < dhi <= 32767:
                raise ValueError('invalid physical/digital calibration')
            sig.update(physical_min=lo, physical_max=hi, digital_min=dlo, digital_max=dhi,
                       sample_rate_hz=samples / duration, prefilter=columns[7][i])
        signals.append(sig)
        offset += 2 * samples
    labels = [s['label'] for s in signals]
    if len(set(labels)) != len(labels) or sum(s['annotation'] for s in signals) != 1:
        raise ValueError('unique labels and one annotation channel required')
    return dict(header_bytes=size, record_count=records, record_duration_s=duration,
                record_duration_decimal=duration_text, record_bytes=offset, signals=signals,
                file_bytes=size + records * offset)


def _signal(header, label):
    matches = [s for s in header['signals'] if s['label'] == label and not s['annotation']]
    if len(matches) != 1:
        raise ValueError(f'unknown neural channel: {label}')
    return matches[0]


def record_span(header: dict, label: str, start_sample: int, stop_sample: int) -> dict:
    """Plan the full records covering a half-open native sample interval."""
    start = _integer(start_sample, 'start_sample')
    stop = _integer(stop_sample, 'stop_sample')
    sig = _signal(header, label)
    n = sig['samples_per_record']
    if not 0 <= start < stop <= header['record_count'] * n:
        raise ValueError('sample interval outside recording')
    first, last = start // n, (stop - 1) // n
    return dict(first_record=first, record_count=last - first + 1,
                byte_start=header['header_bytes'] + first * header['record_bytes'],
                byte_end_inclusive=header['header_bytes'] + (last + 1) * header['record_bytes'] - 1,
                start_sample=start, stop_sample=stop, sample_rate_hz=sig['sample_rate_hz'])


def _record_onset(raw: bytes) -> Decimal:
    if b'\x00' not in raw:
        raise ValueError('unterminated timekeeping TAL')
    first = raw.split(b'\x00', 1)[0]
    parts = first.split(b'\x14')
    if len(parts) < 3 or parts[1] != b'' or parts[-1] != b'':
        raise ValueError('missing empty timekeeping annotation')
    if re.fullmatch(rb'[+-](?:\d+(?:\.\d*)?|\.\d+)', parts[0]) is None:
        raise ValueError('invalid timekeeping onset')
    return Decimal(parts[0].decode('ascii'))


def decode_records(header: dict, raw: bytes, first_record: int, labels=None) -> dict:
    """Decode same-rate channels and validate every record's raw TAL.

    The supported CML export uses record onset = index * duration. A different
    origin or discontinuity is rejected instead of silently retiming samples.
    """
    first = _integer(first_record, 'first_record')
    size = header['record_bytes']
    count, remainder = divmod(len(raw), size)
    if remainder or count == 0 or not 0 <= first < first + count <= header['record_count']:
        raise ValueError('incomplete or out-of-range records')
    if labels is None:
        labels = [s['label'] for s in header['signals'] if not s['annotation']]
    labels = list(labels)
    if not labels or len(set(labels)) != len(labels):
        raise ValueError('nonempty unique channel selection required')
    signals = [_signal(header, label) for label in labels]
    if len({s['samples_per_record'] for s in signals}) != 1:
        raise ValueError('selected channels must have the same sample rate')
    ann = next(s for s in header['signals'] if s['annotation'])
    n = signals[0]['samples_per_record']
    values = np.empty((len(signals), count * n), dtype=np.float64)
    onsets, rails = [], [0] * len(signals)
    duration = Decimal(header['record_duration_decimal'])
    for j in range(count):
        record_start = j * size
        a = record_start + ann['byte_offset']
        onset = _record_onset(raw[a:a + 2 * ann['samples_per_record']])
        if onset != (first + j) * duration:
            raise ValueError('record TAL disagrees with zero-origin continuous clock')
        onsets.append(float(onset))
        for k, sig in enumerate(signals):
            digital = np.frombuffer(raw, dtype='<i2', count=n,
                                    offset=record_start + sig['byte_offset'])
            if np.any(digital < sig['digital_min']) or np.any(digital > sig['digital_max']):
                raise ValueError(f'digital values outside calibration: {sig["label"]}')
            rails[k] += int(np.count_nonzero((digital == sig['digital_min']) | (digital == sig['digital_max'])))
            gain = (sig['physical_max'] - sig['physical_min']) / (sig['digital_max'] - sig['digital_min'])
            values[k, j * n:(j + 1) * n] = (digital.astype(np.float64) - sig['digital_min']) * gain + sig['physical_min']
    if not np.isfinite(values).all():
        raise ValueError('nonfinite calibrated values')
    return dict(labels=labels, units=[s['unit'] for s in signals], values=values,
                first_sample=first * n, stop_sample=(first + count) * n,
                sample_rate_hz=signals[0]['sample_rate_hz'], record_onsets_s=onsets,
                digital_rail_counts=rails)


def sample_interval(decoded: dict, start_sample: int, stop_sample: int) -> np.ndarray:
    """Return physical values for an exact half-open interval; never pad gaps."""
    start = _integer(start_sample, 'start_sample')
    stop = _integer(stop_sample, 'stop_sample')
    if not decoded['first_sample'] <= start < stop <= decoded['stop_sample']:
        raise ValueError('requested samples are not all held')
    return decoded['values'][:, start - decoded['first_sample']:stop - decoded['first_sample']].copy()
