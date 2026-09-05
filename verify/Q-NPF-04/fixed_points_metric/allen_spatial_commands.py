"""고정된 첫 시행에서 다섯 자극의 실제 명령 방향이 독립인지 검사한다."""
import json
from pathlib import Path
import h5py
import numpy as np
from allen_joint_inventory import HERE, BASE, raw, sha
from allen_spatial_recordings import geometry
from raw_sweep_map import fields


def main():
    inventory = HERE/'allen_spatial_recordings_result.json'
    prior = json.loads(inventory.read_text(encoding='utf-8'))
    rows = sorted(prior['joined'],key=lambda r:r['cell']['device'])
    assert len(rows)==5 and all(r['mode']=='vc' and r['acquisition']['sweep']==0 for r in rows)
    cache = BASE/'raw_ranges/1630015960.701'
    manifest = json.loads((cache/'manifest.json').read_text(encoding='utf-8'))
    raw.URL = manifest['remote']['url']; raw.CACHE = cache
    raw.LIMIT = sum(b['bytes'] for b in manifest['blocks'].values())+4*1024*1024
    before = [-.002,-.001]; during = [.0004,.0008]
    onsets = []
    segments = []
    with raw.CachedRanges() as reader:
        assert reader.remote == prior['provenance']['remote']
        with h5py.File(reader,'r') as f:
            for row in rows:
                device = row['cell']['device']
                node = f[row['command']['path']]
                meta = fields(node.attrs['comment'],device)
                candidates = [part.split(',') for part in meta['Epochs'].split(':')
                              if 'Epoch=1;' in part and 'Pulse=0;' in part and ';Active' in part]
                assert len(candidates)==1
                onsets.append(float(candidates[0][0]))
            delta = np.zeros((5,5))
            for column,onset in enumerate(onsets):
                for row_index,row in enumerate(rows):
                    info = row['command']; fs = info['rate']; node = f[info['path']+'/data']
                    averages = []
                    for window in (before,during):
                        start,stop = [round((onset+t)*fs) for t in window]
                        values = np.asarray(node[start:stop],dtype=float)*info['conversion']+info['offset']
                        assert values.size==stop-start and np.isfinite(values).all()
                        averages.append(float(values.mean()))
                        segments.append({'source_device':rows[column]['cell']['device'],'target_device':row['cell']['device'],
                                         'window_s':window,'sample_range':[start,stop],'mean_command_V':averages[-1]})
                    delta[row_index,column] = averages[1]-averages[0]
                print('COMMAND_DIRECTION',rows[column]['cell']['device'],flush=True)
        provenance = {'remote':reader.remote,'manifest':reader.manifest,'new_bytes':reader.downloaded_this_session}
    points = np.array([r['cell']['position'] for r in rows]); centered = points-points.mean(axis=0)
    design = np.column_stack([np.ones(5),centered])
    coefficients = np.linalg.lstsq(design,delta,rcond=None)[0]
    residual = delta-design@coefficients
    singular = np.linalg.svd(delta,compute_uv=False)
    rank = int(np.linalg.matrix_rank(delta))
    result = {'code_sha256':sha(Path(__file__)),'inventory_sha256':sha(inventory),
              'raw_reader_sha256':sha(Path(raw.__file__)),'devices':[r['cell']['device'] for r in rows],
              'cell_ids':[r['cell']['cell'] for r in rows],'onsets_s':onsets,'baseline_window_s':before,'pulse_window_s':during,
              'delta_command_V':delta.tolist(),'singular_values_V':singular.tolist(),'command_rank':rank,
              'position_difference_geometry':geometry(points),'affine_voltage_residual_relative':float(np.linalg.norm(residual)/np.linalg.norm(delta)),
              'affine_voltage_residuals_by_pulse':(np.linalg.norm(residual,axis=0)/np.linalg.norm(delta,axis=0)).tolist(),
              'projected_gradient_rank':int(np.linalg.matrix_rank(coefficients[1:])),
              'segments':segments,'provenance':provenance,
              'interpretation':'Actual voltage command differences, not corrected membrane voltages or neural response. One-cell pulses need not be spatial affine fields; combining responses requires verified linear superposition.',
              'limits':['Command full rank alone does not identify the biological connection operator',
                        'Large depolarizing pulses are not assumed to be subthreshold or linear',
                        'Membrane/electrode correction, neural current, balanced closure and held-out superposition remain untested'],
              'claim_ceiling':'BIO_EVIDENCE_L0_INPUT_DESIGN'}
    with (HERE/'allen_spatial_commands_result.json').open('x',encoding='utf-8') as f:
        json.dump(result,f,ensure_ascii=False,indent=2,allow_nan=False)
    print(json.dumps({k:result[k] for k in ('devices','onsets_s','command_rank','singular_values_V','projected_gradient_rank','affine_voltage_residual_relative')}),flush=True)


if __name__=='__main__':
    main()
