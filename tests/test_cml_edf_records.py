import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / 'verify/Q-NPF-04/hippocampal_reinstatement/cml_edf_records.py'
spec = importlib.util.spec_from_file_location('cml_edf_records', PATH)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


@pytest.fixture
def held():
    base = ROOT / 'data/external/hippocampal_reinstatement/cml_catfr1_edf_probe_v1'
    if not base.exists():
        pytest.skip('bounded public EDF probe not held')
    fixed = (base / 'header_fixed_0_255.bin').read_bytes()
    rest = (base / 'header_rest.bin').read_bytes()
    raw = (base / 'data_record_250.bin').read_bytes()
    assert hashlib.sha256(fixed).hexdigest() == '28f16a01465f0ef4bfae1da9fd6bdec5b691cd394fa8b70decd5645025818a83'
    assert hashlib.sha256(rest).hexdigest() == '216cd632bc6fdaf28556a9974e39fabd4502ad277bb6e1b0d1d0b505a197b459'
    assert hashlib.sha256(raw).hexdigest() == '763e1b17010f05f1d1257b1544f5e2797cf99ebf3a0b1b81aac0968aba8bcca1'
    return fixed + rest, raw, json.loads((base / 'edf_probe_result.json').read_text(encoding='utf-8'))


def test_real_record_clock_labels_units_and_independent_voltage_extrema(held):
    header, raw, prior = held
    h = m.parse_header(header)
    assert h['file_bytes'] == 2074246832
    decoded = m.decode_records(h, raw, 250)
    assert decoded['record_onsets_s'] == [250.0]
    assert decoded['values'].shape == (120, 1600)
    assert set(decoded['units']) == {'uV'}
    reference = [s for s in prior['edf']['signals_metadata'] if s['label'] != 'EDF Annotations']
    assert decoded['labels'] == [s['label'] for s in reference]
    np.testing.assert_allclose(decoded['values'].min(axis=1), [s['physical_observed_min'] for s in reference], rtol=0, atol=1e-10)
    np.testing.assert_allclose(decoded['values'].max(axis=1), [s['physical_observed_max'] for s in reference], rtol=0, atol=1e-10)


def test_real_payload_rejects_wrong_record_identity_truncation_and_discontinuous_header(held):
    header, raw, _ = held
    h = m.parse_header(header)
    with pytest.raises(ValueError, match='TAL disagrees'):
        m.decode_records(h, raw, 251)
    with pytest.raises(ValueError, match='incomplete'):
        m.decode_records(h, raw[:-2], 250)
    altered = bytearray(header)
    altered[192:197] = b'EDF+D'
    with pytest.raises(ValueError, match='continuous'):
        m.parse_header(bytes(altered))


def test_exact_record_edge_and_sample_selection_does_not_read_an_extra_record(held):
    header, raw, _ = held
    h = m.parse_header(header)
    label = h['signals'][0]['label']
    span = m.record_span(h, label, 400000, 401600)
    assert (span['first_record'], span['record_count']) == (250, 1)
    assert (span['byte_start'], span['byte_end_inclusive']) == (96059732, 96443845)
    d = m.decode_records(h, raw, 250, [label])
    x = m.sample_interval(d, 400001, 401599)
    np.testing.assert_array_equal(x, d['values'][:, 1:-1])
    with pytest.raises(ValueError, match='not all held'):
        m.sample_interval(d, 399999, 400001)
    with pytest.raises(ValueError, match='integer'):
        m.record_span(h, label, 400000.0, 401600)


def test_timekeeping_uses_all_original_bytes_and_decimal_clock():
    assert m._record_onset(b'+250\x14\x14\x00') == 250
    assert str(m._record_onset(b'+0.125\x14\x14\x00')) == '0.125'
    for invalid in (b'+250\x14\x14', b'+250\x14WORD\x14\x00', b'nan\x14\x14\x00', b'+5\x14\x00'):
        with pytest.raises(ValueError):
            m._record_onset(invalid)
