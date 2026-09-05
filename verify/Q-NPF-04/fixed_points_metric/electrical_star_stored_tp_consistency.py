"""Posthoc numeric association of stored TP, TPStorage, and lab notebook.

The peak window is discovered on the first stored waveform, then reused on
the remaining nine. This is a file/estimator consistency check, not a new
independent biological validation or historical MIES source reconstruction.
"""
import hashlib
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
INPUT = HERE / 'electrical_star_stored_tp_waveforms_result.json'
EXPECTED_INPUT_SHA = '192c6275adaa6e4c904af19d71130ce8fa43e286769346eb7e774ef18dfa0c30'
OUTPUT = HERE / 'electrical_star_stored_tp_consistency_result.json'
FIELDS = (('Baseline_VC', 'baseline_pA'),
          ('PeakResistance', 'peak_resistance_MOhm'),
          ('SteadyStateResistance', 'steady_resistance_MOhm'))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def baseline_mapping(wave, valid_heads, property_baselines):
    """Match each packed waveform column by its exact 76-sample mean."""
    observed = np.asarray(wave, float)[295:371].mean(axis=0)
    matrix = np.abs(observed[:, None] - np.asarray(property_baselines)[None, :])
    matches = matrix == 0
    if not ((matches.sum(0) == 1).all() and (matches.sum(1) == 1).all()):
        raise ValueError('Baseline identity does not define a unique permutation')
    return [int(valid_heads[j]) for j in matches.argmax(1)]


def discover_peak_window(wave, implied_peak, tolerance=1e-8):
    """Search a stated finite family; no claim about all possible estimators."""
    candidates = []
    for start in range(374, 410):
        for stop in range(start + 1, 426):
            error = float(np.max(np.abs(wave[start:stop].mean(0) - implied_peak)))
            candidates.append((error, start, stop))
    candidates.sort()
    hits = [v for v in candidates if v[0] <= tolerance]
    if len(hits) != 1:
        raise ValueError('Peak averaging window not unique in the search family')
    return dict(start=hits[0][1], stop_exclusive=hits[0][2],
                max_error=hits[0][0], next_best_max_error=candidates[1][0],
                candidates=len(candidates), tolerance=tolerance)


def property_vector(record, name, heads):
    return np.array([record['property_fields'][name][h] for h in heads], float)


def main():
    if OUTPUT.exists():
        raise FileExistsError(OUTPUT)
    assert sha(INPUT) == EXPECTED_INPUT_SHA
    code_hash = sha(__file__)
    source = json.loads(INPUT.read_text(encoding='utf8'))
    first = source['records'][0]
    heads = first['sorted_valid_headstage_mapping_hypothesis']
    implied = property_vector(first, 'Baseline_VC', heads) - 10000 / property_vector(first, 'PeakResistance', heads)
    peak_window = discover_peak_window(np.array(first['waveform_raw']), implied)
    rows = []
    for record in source['records']:
        wave = np.array(record['waveform_raw'])
        valid = record['sorted_valid_headstage_mapping_hypothesis']
        mapping = baseline_mapping(wave, valid, property_vector(record, 'Baseline_VC', valid))
        baseline = wave[295:371].mean(0)
        peak = wave[peak_window['start']:peak_window['stop_exclusive']].mean(0)
        late = wave[795:871].mean(0)
        for column, head in enumerate(mapping):
            nb = next(v for v in record['notebook_cells'] if v['device'] == head)
            properties = record['property_fields']
            prop_b = properties['Baseline_VC'][head]
            prop_p = properties['PeakResistance'][head]
            prop_s = properties['SteadyStateResistance'][head]
            identities = {p: float(np.float32(properties[p][head])) == nb[n] for p, n in FIELDS}
            original = record['features_by_waveform_column'][column]
            # Both estimates use the same previously fixed 75/3/75-sample rule.
            stored_peak_R = -10000 / original['peak_delta_raw']
            stored_late_R = -10000 / original['late_delta_raw']
            rows.append(dict(sweep=record['sweep'], property_row=record['property_row'],
                waveform_column=column, headstage=head, notebook_float32_identity=identities,
                baseline_error_pA=float(baseline[column] - prop_b),
                implied_peak_current_error_pA=float(peak[column] - (prop_b - 10000 / prop_p)),
                implied_late_current_error_pA=float(late[column] - (prop_b - 10000 / prop_s)),
                reconstructed_peak_R_MOhm=float(-10000 / (peak[column] - baseline[column])),
                reconstructed_late_R_MOhm=float(-10000 / (late[column] - baseline[column])),
                peak_R_error_MOhm=float(-10000 / (peak[column] - baseline[column]) - prop_p),
                late_R_error_MOhm=float(-10000 / (late[column] - baseline[column]) - prop_s),
                stored_same_estimator_peak_R_MOhm=stored_peak_R,
                stored_same_estimator_late_R_MOhm=stored_late_R,
                inserted_to_stored_same_estimator_peak_R_ratio=nb['inserted']['defined_peak_resistance_MOhm'] / stored_peak_R,
                inserted_to_stored_same_estimator_late_R_ratio=nb['inserted']['defined_late_resistance_MOhm'] / stored_late_R))
    primary = [r for r in rows if r['headstage'] in (1, 2, 4, 5)]
    ratios = {}
    for kind in ('peak', 'late'):
        values = [r['inserted_to_stored_same_estimator_' + kind + '_R_ratio'] for r in primary]
        ratios[kind] = dict(min=float(min(values)), max=float(max(values)), median=float(np.median(values)))
    summary = dict(waveforms=10, channels=70, first_waveform_discovery_channels=7,
        remaining_waveform_verification_channels=63,
        notebook_float32_exact_matches=sum(sum(r['notebook_float32_identity'].values()) for r in rows),
        notebook_comparisons=210, all_mapping_orders_equal_expected=all(r['headstage'] == heads[r['waveform_column']] for r in rows),
        max_abs_errors={name: max(abs(r[name]) for r in rows) for name in
                       ('baseline_error_pA', 'implied_peak_current_error_pA', 'implied_late_current_error_pA', 'peak_R_error_MOhm', 'late_R_error_MOhm')},
        primary_four_inserted_to_stored_same_estimator_ratios=ratios,
        property_minus_waveform_time_s_range=[min(r['property_time_minus_waveform_note_s'] for r in source['records']), max(r['property_time_minus_waveform_note_s'] for r in source['records'])],
        waveform_minus_notebook_time_s_range=[min(r['waveform_time_minus_notebook_tp_s'] for r in source['records']), max(r['waveform_time_minus_notebook_tp_s'] for r in source['records'])])
    result = dict(code_sha256=code_hash, input_sha256=sha(INPUT), numpy_version=np.__version__,
        stage='Posthoc data-format and estimator consistency; no new biological holdout',
        baseline_window_zero_based_inclusive=[295, 370], late_window_zero_based_inclusive=[795, 870],
        peak_window_discovered_on_first_waveform=peak_window,
        voltage_step_for_numeric_reconstruction_mV=-10,
        summary=summary, records=rows,
        interpretation='The ten stored waveform columns reproduce TPStorage baseline and resistances; float32-rounded properties exactly reproduce the selected notebook cells. This supports these specific associations and the notebook pA/MOhm numerical scales.',
        limitations=['The actual historical implementation was not obtained; numeric equivalence here is not source-code provenance',
                     'The discovery/verification split is an internal consistency check after waveform exposure, not independent biological evaluation',
                     'Current units are anchored to recorded notebook units, not an independent physical calibration',
                     'HoldingCmd_VC physical meaning/update time remains unverified',
                     'Finite-window peak is not instantaneous i(0+), true Rs, or an intrinsic membrane/junction parameter',
                     'The same-estimator inserted/stored ratios still compare different acquisitions and do not prove identical conditions'])
    assert sha(__file__) == code_hash
    with OUTPUT.open('x', encoding='utf8') as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write('\n')
    print(json.dumps(summary, indent=2))
    print('SHA256', sha(OUTPUT))


if __name__ == '__main__':
    main()
