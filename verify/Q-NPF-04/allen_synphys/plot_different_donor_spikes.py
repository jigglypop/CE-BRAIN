"""수집된 24개 원파형을 명령 시작 기준으로 표시한다. 판정값은 수정하지 않는다."""
import json
from pathlib import Path
import xml.etree.ElementTree as ET
import numpy as np
from reference_spike_audit import sha

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def main():
    result = json.loads((HERE/'different_donor_raw_spikes_result.json').read_text(encoding='utf-8'))
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="620" viewBox="0 0 1000 620">',
             '<rect width="1000" height="620" fill="white"/>',
             '<style>text {font:14px sans-serif; fill:#222}</style>',
             '<text x="50" y="25">24? ???: ??? ?? ??, ??? ?? ??</text>',
             '<text x="50" y="48">? ??? ?? ??? ??. ?? ?? ???? ?? ?? ?? ??.</text>']
    for col, asset in enumerate(result['assets']):
        path = ROOT/asset['path']
        assert sha(path) == asset['sha256']
        with np.load(path, allow_pickle=False) as z:
            voltage, current = z['voltage'], z['current']
        fs = asset['rate_hz']
        sweep = int(asset['binding']['sweep'])
        rows = [r for r in result['records'] if r['sweep'] == sweep]
        for panel, values, scale, lo, hi, unit in [(0, voltage, 1000, -90, 70, 'mV'), (1, current, 1e9, -.2, 3, 'nA')]:
            x0, y0, w, h = 70+col*490, 105+panel*235, 405, 175
            parts.append(f'<text x="{x0}" y="{y0-20}">?? {sweep} ? {unit}</text>')
            for tick in (lo, (lo+hi)/2, hi):
                y = y0+h-(tick-lo)/(hi-lo)*h
                parts.append(f'<path d="M{x0},{y} h{w}" stroke="#ddd"/><text x="{x0-48}" y="{y+5}">{tick:g}</text>')
            for tick in (0, 1, 2, 3):
                x = x0+(tick+.5)/3.5*w
                parts.append(f'<text x="{x}" y="{y0+h+20}">{tick}</text>')
            for row in rows:
                center = round(row['actual_onset_s']*fs)
                offsets = np.arange(-round(.0005*fs), round(.003*fs))
                yy = values[center+offsets]*scale
                assert np.min(yy) >= lo and np.max(yy) <= hi, '? ?? ? ??'
                xx = x0+(offsets/fs*1000+.5)/3.5*w
                yy = y0+h-(yy-lo)/(hi-lo)*h
                coordinates = ' '.join(f'{x:.2f},{y:.2f}' for x,y in zip(xx,yy))
                color = '#be432d' if not row['aligned'] else '#406eab'
                alpha = .9 if not row['aligned'] else .35
                parts.append(f'<polyline points="{coordinates}" fill="none" stroke="{color}" stroke-opacity="{alpha}" stroke-width="1"/>')
            parts.append(f'<text x="{x0+80}" y="{y0+h+43}">?? ?? ? ?? (ms)</text>')
    parts.append('</svg>')
    svg = '\n'.join(parts)
    ET.fromstring(svg)
    (HERE/'different_donor_spikes.svg').write_text(svg, encoding='utf-8')
    print('PLOT_PASS: 24 pulses; verified archive hashes')


if __name__ == '__main__':
    main()
