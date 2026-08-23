from __future__ import annotations

import importlib.util
from pathlib import Path
import sqlite3
import sys

import numpy as np


MODULE_PATH = Path(__file__).with_name("prepare_discovery_dataset.py")
SPEC = importlib.util.spec_from_file_location("prepare_discovery_dataset", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
prepare = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = prepare
SPEC.loader.exec_module(prepare)


def fake_sequence(pre_mode: str = "ic", post_mode: str = "ic"):
    rows = []
    for pulse in range(12):
        row = {
            "pulse_number": pulse,
            "onset_time": 0.01 * pulse,
            "previous_pulse_dt": 0.01 if pulse else None,
            "stim_amplitude": 2e-12 if pre_mode == "ic" else 2e-3,
            "stim_duration": 1e-3,
            "n_spikes": 1,
            "first_spike_after_onset": 0.5e-3,
            "pre_clamp_mode": pre_mode,
            "post_clamp_mode": post_mode,
            "dec_fit_reconv_amp": 3e-4 if post_mode == "ic" else 3e-12,
            "baseline_dec_fit_reconv_amp": 0.0,
            "dec_fit_latency": 1e-3,
            "dec_fit_rise_time": 2e-3,
            "dec_fit_decay_tau": 4e-3,
            "dec_fit_nrmse": 0.1,
            "induction_frequency": 100.0,
            "recovery_delay": 0.25,
            "bath_temperature": 36.85,
            "baseline_potential": -60e-3,
            "baseline_current": 5e-12,
            "baseline_noise_stdev": 1e-4 if post_mode == "ic" else 1e-12,
            "pair_soma_distance": 50e-6,
            "post_input_resistance": 100e6,
            "post_capacitance": 20e-12,
            "post_time_constant": 10e-3,
            "ex_qc_pass": 1,
            "in_qc_pass": 0,
        }
        rows.append(row)
    return rows


def test_split_quarantines_every_predecessor_group():
    group = "slice-a"
    assert prepare.assigned_split(group, {group}) == "discovery-contaminated"
    assert prepare.split_bucket(group) in range(10)
    other = "slice-b"
    assert prepare.assigned_split(other, {group}) in {
        "discovery",
        "validation",
        "confirmation",
    }


def test_repeated_lims_slice_specimen_rows_never_cross_splits():
    con = sqlite3.connect(":memory:")
    con.execute(
        "CREATE TABLE slice(id INTEGER PRIMARY KEY, ext_id TEXT, lims_specimen_name TEXT)"
    )
    con.executemany(
        "INSERT INTO slice VALUES (?, ?, ?)",
        [(1, "row-a", "lims-slice"), (2, "row-b", "lims-slice"), (3, "row-c", "other")],
    )
    rows, ext_to_group, predecessor = prepare.split_rows(con, {"row-a"})
    con.close()
    repeated = [row for row in rows if row["group_id"] == "lims-slice"]
    assert ext_to_group["row-a"] == ext_to_group["row-b"] == "lims-slice"
    assert predecessor == {"lims-slice"}
    assert {row["assigned_split"] for row in repeated} == {"discovery-contaminated"}


def test_typed_commands_and_responses_never_share_numeric_channel():
    ic_current, ic_voltage = prepare.typed_command(2e-12, "ic")
    vc_current, vc_voltage = prepare.typed_command(2e-3, "vc")
    assert ic_current == 2.0 and np.isnan(ic_voltage)
    assert np.isnan(vc_current) and vc_voltage == 2.0

    ic_voltage_response, ic_current_response = prepare.typed_response(3e-4, "ic")
    vc_voltage_response, vc_current_response = prepare.typed_response(3e-12, "vc")
    assert ic_voltage_response == 0.3 and np.isnan(ic_current_response)
    assert np.isnan(vc_voltage_response) and vc_current_response == 3.0


def test_future_target_values_never_enter_features():
    rows = fake_sequence()
    features_before, target_before = prepare.feature_row(rows)
    for pulse in prepare.TARGET_PULSES:
        rows[pulse]["dec_fit_reconv_amp"] = 9999.0
        rows[pulse]["dec_fit_latency"] = 8888.0
        rows[pulse]["dec_fit_rise_time"] = 7777.0
        rows[pulse]["dec_fit_decay_tau"] = 6666.0
    features_after, target_after = prepare.feature_row(rows)
    assert np.array_equal(features_before, features_after, equal_nan=True)
    assert not np.array_equal(target_before, target_after)


def test_mode_specific_feature_channels_remain_structurally_missing():
    ic_features, _ = prepare.feature_row(fake_sequence("ic", "ic"))
    vc_features, _ = prepare.feature_row(fake_sequence("vc", "vc"))
    index = {name: idx for idx, name in enumerate(prepare.FEATURE_NAMES)}
    assert np.isfinite(ic_features[index["history_mean_stim_ic_over_I0"]])
    assert np.isnan(ic_features[index["history_mean_stim_vc_over_V0"]])
    assert np.isnan(vc_features[index["history_mean_stim_ic_over_I0"]])
    assert np.isfinite(vc_features[index["history_mean_stim_vc_over_V0"]])
    assert np.isfinite(ic_features[index["post_noise_ic_over_V0"]])
    assert np.isnan(ic_features[index["post_noise_vc_over_I0"]])
    assert np.isnan(vc_features[index["post_noise_ic_over_V0"]])
    assert np.isfinite(vc_features[index["post_noise_vc_over_I0"]])


def test_sql_is_discovery_scoped_and_blob_free():
    prepare.assert_discovery_sql(prepare.DISCOVERY_SQL)
    normalized = prepare.DISCOVERY_SQL.lower()
    assert "selected_discovery_sequence" in normalized
    assert "stim_pulse.data" not in normalized
    assert "pulse_response.data" not in normalized


def test_fixed_target_and_feature_schema():
    assert prepare.HISTORY_PULSES == tuple(range(8))
    assert prepare.TARGET_PULSES == tuple(range(8, 12))
    assert len(prepare.TARGET_NAMES) == 16
    assert len(prepare.FEATURE_NAMES) == 33
