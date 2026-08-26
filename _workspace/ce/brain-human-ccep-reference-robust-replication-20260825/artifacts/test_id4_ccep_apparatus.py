import importlib.util
import struct
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
spec = importlib.util.spec_from_file_location("id4", HERE / "id4_ccep_apparatus.py")
id4 = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(id4)


CHANNELS = """name\ttype\tstatus
A\tseeg\tgood
B\tecog\tgood
C\tieeg\tgood
D\tseeg\tgood
E\tieeg\tbad
"""
ELECTRODES = """name\tx\ty\tz
A\t0\t0\t0
B\t2\t0\t0
C\t30\t0\t0
D\t32\t0\t0
E\t50\t0\t0
"""
EVENTS = """status\telectrical_stimulation_current\telectrical_stimulation_type\telectrical_stimulation_site\tpolarity
good\t6.0 mA\tbiphasic\tA-B\t+
good\t6.0 mA\tbiphasic\tA-B\t+
good\t6.0 mA\tbiphasic\tA-B\t+
good\t6.0 mA\tbiphasic\tA-B\t+
good\t6.0 mA\tbiphasic\tA-B\t+
good\t6.0 mA\tbiphasic\tA-B\t+
good\t6.0 mA\tbiphasic\tA-B\t+
good\t6.0 mA\tbiphasic\tA-B\t+
good\t6.0 mA\tbiphasic\tA-B\t+
good\t6.0 mA\tbiphasic\tA-B\t+
good\t6.0 mA\tbiphasic\tC-D\t-
good\t6.0 mA\tbiphasic\tC-D\t-
good\t6.0 mA\tbiphasic\tC-D\t-
good\t6.0 mA\tbiphasic\tC-D\t-
good\t6.0 mA\tbiphasic\tC-D\t-
good\t6.0 mA\tbiphasic\tC-D\t-
good\t6.0 mA\tbiphasic\tC-D\t-
good\t6.0 mA\tbiphasic\tC-D\t-
good\t6.0 mA\tbiphasic\tC-D\t-
good\t6.0 mA\tbiphasic\tC-D\t-
"""


def test_signal_blind_plan_metrics_controls_and_stop(tmp_path):
    plan = id4.canonical_metadata_plan(CHANNELS, ELECTRODES, EVENTS, snapshot="ds004457-v1.0.2", subject="sub-1")
    assert plan["signal_accessed"] is False
    assert plan["canonical_nodes"] == ["A-B", "C-D"]
    assert len(plan["pairs"]) == 1 and plan["pairs"][0]["midpoint_distance_mm"] == 30
    assert plan["orientation_labels"]["A-B"] == ["A->B"]
    reversed_events = EVENTS + ("good\t6.0 mA\tbiphasic\tB-A\t+\n" * 10)
    reversed_plan = id4.canonical_metadata_plan(
        CHANNELS, ELECTRODES, reversed_events, snapshot="ds004457-v1.0.2", subject="sub-1"
    )
    assert "A-B" in reversed_plan["excluded_mixed_polarity_nodes"]
    assert reversed_plan["canonical_nodes"] == ["C-D"]
    non_biphasic = EVENTS.replace("biphasic", "monophasic")
    assert id4.canonical_metadata_plan(
        CHANNELS, ELECTRODES, non_biphasic, snapshot="ds004457-v1.0.2", subject="sub-1"
    )["canonical_nodes"] == []
    labels = id4.patient_labels(["sub-1", "sub-2", "sub-3", "sub-4", "sub-5"], snapshot="ds004457-v1.0.2")
    assert sorted(labels.values()).count("development") == 2
    metric = id4.reciprocal_metrics([(2, 2, 1, 1), (4, 4, 2, 2)])
    assert metric["u"] == 0 and metric["R"] > 1.25
    fixed = id4.fixed_patient_label(1.6, 1.0, 1 / 8193, 0.5)
    assert fixed["phi_mean"] and not fixed["phi_bip"]
    assert id4.confirmation_label([fixed, fixed, fixed]) == "REFERENCE_SENSITIVE_PATTERN_REPLICATED"
    controls = id4.synthetic_adverse_controls(seeds=16)
    assert controls["status"] == "PASS"
    assert all(value <= 7 for value in controls["null"].values())
    assert all(value >= 13 for value in controls["power"].values())
    assert controls["common_reference"]["mean_R"] > 1.25
    assert controls["common_reference"]["bip_R"] == 1.0
    stop = id4.mef3_random_access_capability()
    assert stop["status"] == "APPARATUS_MEF3_RANDOM_ACCESS_STOP"
    assert stop["adapter"] == "mef3io" and stop["mef3io_version"] == "1.1.2"
    assert stop["reason"] == "executable fixture path and allowed channels required"
    adapter = id4.Mef3ioRandomAccessAdapter(allowed_channels=["LV1"])
    for channel, start, end in (("NOT_LV1", 0, 1), ("LV1", 0, id4.MEF3_MAX_WINDOW_UUTC + 1), ("LV1", True, 1)):
        try:
            adapter.random_window(channel, start, end)
            raise AssertionError("unbounded reader request accepted")
        except RuntimeError:
            pass
    fixture = id4.official_single_channel_transient_fixture_receipt()
    assert fixture["capability_evidence_only"] and not fixture["endpoint_evidence"]
    assert fixture["sample_index_capability_gate"] == "PASS_OFFICIAL_FIRST_BLOCK_SAMPLE_INDEX"
    assert fixture["sample_index_equivalence_established"] and not fixture["development_opened"]
    sample_gate = id4.mef3_sample_index_capability()
    assert sample_gate["status"] == "PASS_OFFICIAL_FIRST_BLOCK_SAMPLE_INDEX"
    assert sample_gate["scope"] == "official-first-block-capability-only"
    assert sample_gate["persistent_raw_bytes"] == 0 and not sample_gate["development_analysis_opened"]
    assert fixture["samples"] == fixture["finite_samples"] == 2048
    assert fixture["uUTC_half_open"] == [81209476921, 81210476921]
    header = bytes(id4.TIDX_HEADER_BYTES)
    row_a = struct.pack("<qqqIIii16s", 1024, 1000000, 0, 2048, 1936, 0, 0, bytes(16))
    row_b = struct.pack("<qqqIIii16s", 2960, 2000000, 2048, 2048, 100, 0, 0, bytes(16))
    index = id4.parse_tidx(header + row_a + row_b)
    assert index[0]["red_flags"] == 0 and index[0]["discontinuity"] is False
    flag_tail = bytearray(16); flag_tail[4] = 0x01
    other_tail = bytearray(16); other_tail[3] = 0x80; other_tail[4] = 0x02; other_tail[5] = 0x40
    parsed_flags = id4.parse_tidx(header + struct.pack("<qqqIIii16s", 1024, 1000000, 0, 2048, 1936, 0, 0, bytes(flag_tail))
                                  + struct.pack("<qqqIIii16s", 2960, 2000000, 2048, 2048, 100, 0, 0, bytes(other_tail)))
    assert parsed_flags[0]["red_flags"] == 0x01 and parsed_flags[0]["discontinuity"] is True
    assert parsed_flags[1]["red_flags"] == 0x02 and parsed_flags[1]["discontinuity"] is False
    assert id4.plan_tdat_ranges(index, start_uutc=1000000, end_uutc=2000000, fs_hz=2048, tdat_size=3060) == [(0, 2960)]
    assert id4.plan_tdat_ranges(index, start_uutc=2000000, end_uutc=3000000, fs_hz=2048, tdat_size=3060) == [(0, 1024), (2960, 3060)]
    for bad in (header + row_a[:-1], header + row_b + row_a):
        try:
            id4.parse_tidx(bad)
            raise AssertionError("invalid index accepted")
        except ValueError:
            pass
    try:
        id4.plan_tdat_ranges(index, start_uutc=1, end_uutc=2, fs_hz=0, tdat_size=3060)
        raise AssertionError("invalid sampling frequency accepted")
    except ValueError:
        pass
    overlap_bytes = id4.parse_tidx(header + row_a + struct.pack("<qqqIIii16s", 2000, 2000000, 2048, 2048, 100, 0, 0, bytes(16)))
    overlap_samples = id4.parse_tidx(header + row_a + struct.pack("<qqqIIii16s", 2960, 2000000, 1024, 2048, 100, 0, 0, bytes(16)))
    overlap_times = id4.parse_tidx(header + row_a + struct.pack("<qqqIIii16s", 2960, 1500000, 2048, 2048, 100, 0, 0, bytes(16)))
    for bad_rows, bad_size in ((overlap_bytes, 3060), (overlap_samples, 3060), (overlap_times, 3060), (index, 3000)):
        try:
            id4.plan_tdat_ranges(bad_rows, start_uutc=1000000, end_uutc=3000000, fs_hz=2048, tdat_size=bad_size)
            raise AssertionError("invalid block interval accepted")
        except ValueError:
            pass
    receipts = id4.write_small_receipts(tmp_path)
    assert receipts["capability"]["status"] == "APPARATUS_MEF3_RANDOM_ACCESS_STOP"
    assert receipts["capability"]["sample_index"]["status"] == "PASS_OFFICIAL_FIRST_BLOCK_SAMPLE_INDEX"
    assert receipts["fixture"]["cleanup"] is True
