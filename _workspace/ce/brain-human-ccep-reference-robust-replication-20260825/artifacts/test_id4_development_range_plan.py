import importlib.util
import struct
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
spec = importlib.util.spec_from_file_location("planner", HERE / "id4_development_range_plan.py")
planner = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(planner)

CHANNELS = """name\ttype\tstatus
A\tseeg\tgood
B\tecog\tgood
C\tieeg\tgood
"""
ELECTRODES = """name\tx\ty\tz
A\t0\t0\t0
B\t2\t0\t0
C\t30\t0\t0
"""
EVENT_HEADER = "status\telectrical_stimulation_current\telectrical_stimulation_type\telectrical_stimulation_site\tonset\n"


def _events(onsets):
    return EVENT_HEADER + "".join(f"good\t6.0 mA\tbiphasic\tA-B\t{onset}\n" for onset in onsets)


EVENTS = _events(str((2048 + index) / 2048) for index in range(10))


def _index(second_start=10, second_sample=0, rows=3):
    header = bytes(1024)
    packed = [struct.pack("<qqqIIii16s", 1024 + 1936 * i, (second_start + i) * 1_000_000,
                          second_sample + 2048 * i, 2048, 1936, 0, 0, bytes(16)) for i in range(rows)]
    return header + b"".join(packed)


def _plan(**changes):
    args = dict(snapshot="ds004457-v1.0.2", subject="sub-1", events_tsv=EVENTS, channels_tsv=CHANNELS,
                electrodes_tsv=ELECTRODES, tidx_by_channel={channel: _index() for channel in ("A", "B", "C")},
                tdat_size_by_channel={channel: 6832 for channel in ("A", "B", "C")}, fs_hz=2048)
    args.update(changes)
    return planner.plan_development_ranges(**args)


def _labeled_events(dataset, subject):
    lines = EVENTS.strip().splitlines()
    return lines[0] + "\tdataset\tsubject\n" + "\n".join(line + f"\t{dataset}\t{subject}" for line in lines[1:]) + "\n"


def test_offline_development_range_manifest_is_source_locked_and_fail_closed():
    manifest = _plan()
    row = manifest["channels"][0]
    assert manifest["signal_accessed"] is False and manifest["aggregate"]["planned_persistent_raw_bytes"] == 0
    assert manifest["precision_convention"] == "decimal-onset-lexical-ulp-sample-grid-v4" and manifest["precision_convention_version"] == 4
    assert manifest["windows_samples"] == [[1024, 2160]]
    assert manifest["epoch_windows_samples"] == {"acquisition": [-1024, 103], "baseline": [-1024, -10], "early": [21, 103], "prestim": [-512, -430]}
    table = planner.development_event_table(snapshot="ds004457-v1.0.2", subject="sub-1", events_tsv=EVENTS,
                                            channels_tsv=CHANNELS, electrodes_tsv=ELECTRODES, fs_hz=2048)
    assert [row["half"] for row in table] == ["A", "B"] * 5
    assert [row["trial_index"] for row in table] == list(range(10))
    assert all(row["acquisition"] == [row["center_sample"] - 1024, row["center_sample"] + 103] for row in table)
    assert manifest["index_cardinality"] == {"universal_header_bytes": 1024, "entry_bytes": 56}
    assert 1024 + 56 * 3482 == 196016
    assert row["ranges"] == [[0, 4896]] and row["bytes"] == 4896 and row["block_count"] == 2
    assert _plan()["channels"][0]["tidx_sha256"] == row["tidx_sha256"]
    assert manifest["aggregate"]["planned_tdat_bytes"] == 3 * 4896
    assert _plan(events_tsv=_labeled_events("ds004457-v1.0.2", "sub-1"))["subject"] == "sub-1"
    one_block = _index()[:1024 + 56]
    for changes in ({"subject": "sub-2"}, {"events_tsv": EVENTS.replace("A-B", "A-X")},
                    {"tidx_by_channel": {"A": _index(), "B": _index(), "C": _index(second_start=11)}, "tdat_size_by_channel": {"A": 6832, "B": 6832, "C": 6832}},
                    {"tidx_by_channel": {channel: one_block for channel in ("A", "B", "C")}},
                    {"tidx_by_channel": {channel: _index(second_sample=1) for channel in ("A", "B", "C")}},
                    {"tdat_size_by_channel": {channel: 3000 for channel in ("A", "B", "C")}},
                    {"events_tsv": _labeled_events("ds004457-v9.9.9", "sub-1")},
                    {"events_tsv": _labeled_events("ds004457-v1.0.2", "sub-2")}):
        try:
            _plan(**changes)
            raise AssertionError("fail-closed planner accepted invalid input")
        except ValueError:
            pass
    sparse_events = _events([*(str((2048 + index) / 2048) for index in range(5)),
                             *(str((8192 + index) / 2048) for index in range(5))])
    sparse = _plan(events_tsv=sparse_events, tidx_by_channel={channel: _index(rows=5) for channel in ("A", "B", "C")},
                   tdat_size_by_channel={channel: 10704 for channel in ("A", "B", "C")})
    assert sparse["channels"][0]["ranges"] == [[0, 4896], [6832, 10704]]
    assert sparse["channels"][0]["block_count"] == 4
    long_block = bytes(1024) + struct.pack("<qqqIIii16s", 1024, 10_000_000, 0, 10240, 1936, 0, 0, bytes(16))
    long = _plan(events_tsv=sparse_events, tidx_by_channel={channel: long_block for channel in ("A", "B", "C")},
                 tdat_size_by_channel={channel: 2960 for channel in ("A", "B", "C")})
    assert long["channels"][0]["ranges"] == [[0, 2960]]
    assert long["channels"][0]["block_count"] == 1
    exact = planner._event_windows(_events(["82.52587890625"]), CHANNELS, {"A-B"},
                                   snapshot="ds004457-v1.0.2", subject="sub-1", fs_hz=2048)
    assert exact == [(167989, 169116)]
    rounded = planner._event_windows(_events(["415.5825195"]), CHANNELS, {"A-B"},
                                     snapshot="ds004457-v1.0.2", subject="sub-1", fs_hz=2048)
    assert rounded == [(850089, 851216)]
    try:
        planner._event_windows(_events(["1.0001"]), CHANNELS, {"A-B"},
                               snapshot="ds004457-v1.0.2", subject="sub-1", fs_hz=2048)
        raise AssertionError("onset outside its lexical half-ULP accepted")
    except ValueError:
        pass
    for ambiguous in ("0.1", "0.000244140625"):
        try:
            planner._onset_sample(ambiguous, 2048)
            raise AssertionError("ambiguous/tied onset sample accepted")
        except ValueError:
            pass
    assert planner._onset_sample("432.75", 2048)[0] == 886272
    cross_index = bytes(1024) + b"".join(struct.pack("<qqqIIii16s", 1024 + 1936 * i, 10_000_000 + 500_000 * i,
                                                       1024 * i, 1024, 1936, 0, 0, bytes(16)) for i in range(3))
    cross = _plan(tidx_by_channel={channel: cross_index for channel in ("A", "B", "C")},
                  tdat_size_by_channel={channel: 6832 for channel in ("A", "B", "C")})
    assert cross["channels"][0]["ranges"] == [[0, 1024], [2960, 6832]]
    assert cross["channels"][0]["block_count"] == 2
    la1_index = bytes(1024) + struct.pack("<qqqIIii16s", 1024, 10_000_000, 0, 2049, 1936, 0, 0, bytes(16)) + struct.pack("<qqqIIii16s", 2960, 10_999_999, 2049, 2047, 1936, 0, 0, bytes(16))
    la1 = _plan(tidx_by_channel={channel: la1_index for channel in ("A", "B", "C")},
                tdat_size_by_channel={channel: 4896 for channel in ("A", "B", "C")})
    assert la1["channels"][0]["ranges"] == [[0, 4896]] and la1["channels"][0]["block_count"] == 2
    discontinuity_tail = bytearray(16); discontinuity_tail[4] = 0x01
    for second_sample, tail in ((2050, bytes(16)), (2048, bytes(16)), (2049, bytes(discontinuity_tail))):
        bad = bytes(1024) + struct.pack("<qqqIIii16s", 1024, 10_000_000, 0, 2049, 1936, 0, 0, bytes(16)) + struct.pack("<qqqIIii16s", 2960, 10_999_999, second_sample, 2047, 1936, 0, 0, tail)
        try:
            _plan(tidx_by_channel={channel: bad for channel in ("A", "B", "C")},
                  tdat_size_by_channel={channel: 4896 for channel in ("A", "B", "C")})
            raise AssertionError("selected sample-index discontinuity accepted")
        except ValueError:
            pass
    source = (HERE / "id4_development_range_plan.py").read_text()
    assert "float(" not in source and "math." not in source
