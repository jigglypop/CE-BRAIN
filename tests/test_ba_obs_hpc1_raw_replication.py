import importlib.util
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pytest


MODULE = Path("examples/brain/ba_obs_hpc1_raw_replication.py")
SPEC = importlib.util.spec_from_file_location("hpc1", MODULE)
hpc1 = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = hpc1
SPEC.loader.exec_module(hpc1)


def test_frozen_fixture_decoder_windows_processing_and_bootstrap():
    assert {name: values.tolist() for name, values in hpc1.WINDOWS.items()} == {
        "early": list(range(258, 275)), "late": list(range(275, 375)),
        "prestim": list(range(100, 200)), "baseline": list(range(225, 245)),
    }
    assert len(hpc1.FILES) == 18
    p20 = next(x for x in hpc1.FILES if x.subject == "p20" and x.phase == "pre")
    assert p20.clinical == "D9" and p20.bipolar_second == "D10"

    # BrainVision multiplex order is time-major little-endian float32.
    expected = np.arange(2 * 3 * hpc1.N_SAMPLES, dtype=np.float32).reshape(3, 2, hpc1.N_SAMPLES)
    payload = expected.transpose(1, 2, 0).reshape(-1).astype("<f4").tobytes()
    chunks = (payload[:17], payload[17:9001], payload[9001:])
    decoded = hpc1._extract_multiplexed_chunks(chunks, 3, (0, 2), 2*hpc1.N_SAMPLES)
    assert np.array_equal(decoded, expected[[0, 2]].reshape(2, -1))

    # A nontrivial trial set verifies DFT removal, p17 filter route, baseline, and aperture.
    t = np.arange(hpc1.N_SAMPLES) / hpc1.FS
    rng = np.random.default_rng(71)
    x = np.vstack([10 + 3*np.sin(2*np.pi*60*t) + rng.normal(scale=1.0, size=hpc1.N_SAMPLES)
                   + np.exp(-((hpc1.TIME_MS-120)/25)**2) for _ in range(24)])
    clean, keep = hpc1.process_trials(x, "p17")
    assert keep.all() and np.allclose(clean[:, hpc1.WINDOWS["baseline"]].mean(axis=1), 0, atol=1e-10)
    assert hpc1.p2p_mean(clean, keep, "late") > 0
    # Baseline precedes every artifact predicate: a constant 600-uV offset is zero
    # after baseline, and must not be rejected by an unbaselined amplitude check.
    offset_clean, offset_keep = hpc1.process_trials(600.0 + rng.normal(size=(24, hpc1.N_SAMPLES)), "p16")
    assert offset_keep.all() and np.abs(offset_clean[:, hpc1.WINDOWS["baseline"]].mean()).max() < 1e-10

    trial_p2p = np.ptp(clean[:, hpc1.WINDOWS["late"]], axis=1).mean()
    assert not np.isclose(hpc1.p2p_mean(clean, keep, "late"), trial_p2p)
    lo, hi, prob = hpc1.shared_bootstrap(np.array([1., 2., 3., 4.]), np.array([0., 1., 2., 3., 4.]), draws=512)
    assert lo <= hi and 0 <= prob <= 1
    assert set(hpc1._loo(np.array([1., 2., 3., 4.]), np.array([0., 1., 2., 3., 4.]))) == {
        "p16", "p17", "p18", "p19", "p20", "UC004", "UC005"}


def _synthetic_lock():
    records = []
    for spec in hpc1.FILES:
        channels = ([{"name": spec.clinical, "resolution": 1.0, "unit": "µV", "to_microvolts": 1.0},
                     {"name": spec.bipolar_second, "resolution": 1.0, "unit": "µV", "to_microvolts": 1.0}]
                    + [{"name": f"X{i}", "resolution": 1.0, "unit": "µV", "to_microvolts": 1.0}
                       for i in range(spec.n_channels - 2)])
        size = 4 * spec.n_channels * spec.blocks * hpc1.N_SAMPLES
        records.append({**hpc1.asdict(spec), "annex_sha256": "a" * 64, "annex_size": size,
                        "samples": spec.blocks*hpc1.N_SAMPLES, "clinical_index": 0, "bipolar_second_index": 1,
                        "clinical_to_microvolts": 1.0, "bipolar_second_to_microvolts": 1.0,
                        "eeg": {"version_id": "version", "etag": "etag", "content_length": str(size), "accept_ranges": "bytes"},
                        "vhdr": {"version_id": "version-h", "etag": "etag-h", "content_length": "1", "accept_ranges": "bytes",
                                 "sha256": "b"*64, "number_of_channels": spec.n_channels,
                                 "sampling_interval_us": 1_000_000/hpc1.FS, "data_file": Path(spec.rel_eeg).name,
                                 "little_endian": True, "channels": channels}})
    return {"status": "SOURCE_LOCK_PASS", "commit": hpc1.COMMIT, "fs_hz": hpc1.FS,
            "window_indices": {key: value.tolist() for key, value in hpc1.WINDOWS.items()}, "records": records}


def test_source_lock_validation_header_units_and_stream_receipt(monkeypatch):
    lock = _synthetic_lock()
    hpc1.validate_source_lock(lock)
    lock["records"][0]["clinical_index"] = 1
    with pytest.raises(ValueError, match="STOP_MEASUREMENT_APERTURE"):
        hpc1.validate_source_lock(lock)

    header = ("Brain Vision Data Exchange Header File Version 1.0\n[Common Infos]\n"
              "DataFile=x.eeg\nDataFormat=BINARY\nDataOrientation=MULTIPLEXED\nNumberOfChannels=2\n"
              "SamplingInterval=2002.002002\n[Binary Infos]\nBinaryFormat=IEEE_FLOAT_32\nUseBigEndianOrder=NO\n"
              "[Channel Infos]\nCh1=A1,,0.001,mV\nCh2=A2,,1,µV\n").encode()
    parsed = hpc1._parse_vhdr(header)
    assert parsed["little_endian"] and parsed["channels"][0]["to_microvolts"] == 1.0
    bad = header.replace(b"UseBigEndianOrder=NO", b"UseBigEndianOrder=YES")
    with pytest.raises(ValueError, match="big-endian"):
        hpc1._parse_vhdr(bad)

    spec = hpc1.EPFile("TS", "x", "pre", "task", 1, 2, "A1", "A2")
    raw = np.arange(2000, dtype="<f4").reshape(1000, 2).tobytes()
    record = {"eeg": {"version_id": "v", "etag": "e"}, "annex_size": len(raw),
              "annex_sha256": hashlib.sha256(raw).hexdigest(), "vhdr": {"sha256": "h"},
              "clinical_index": 0, "bipolar_second_index": 1,
              "clinical_to_microvolts": 2.0, "bipolar_second_to_microvolts": 1.0}
    class Response:
        headers = {"x-amz-version-id": "v", "etag": "e"}
        def __enter__(self): return self
        def __exit__(self, *args): return False
        def read(self, n):
            if not hasattr(self, "offset"): self.offset = 0
            out = raw[self.offset:self.offset+n]
            self.offset += len(out)
            return out
    monkeypatch.setattr(hpc1, "urlopen", lambda request, timeout: Response())
    observed, receipt = hpc1._stream_selected(spec, record)
    assert receipt["observed_sha256"] == record["annex_sha256"] and receipt["observed_size"] == len(raw)
    assert observed[0, 0, 1] == 4.0 and observed[1, 0, 1] == 3.0


def test_transaction_refusal_status_and_summary(tmp_path):
    progress, result, lock = tmp_path / "progress.json", tmp_path / "result.json", tmp_path / "lock.json"
    result.write_text("{}", encoding="utf-8")
    lock.write_text(json.dumps(_synthetic_lock()), encoding="utf-8")
    with pytest.raises(ValueError, match="existing one-shot transaction"):
        hpc1.main(["raw-one-shot", "--lock", str(lock), "--progress", str(progress), "--result", str(result)])
    result.unlink()
    with pytest.raises(ValueError, match="SHA-256 does not match"):
        hpc1.main(["raw-one-shot", "--lock", str(lock), "--progress", str(progress), "--result", str(result)])

    trials = np.vstack([np.linspace(0, 5, hpc1.N_SAMPLES) + i/100 for i in range(24)])
    summary = hpc1._clean_summary(trials, np.ones(24, dtype=bool))
    assert len(summary["clean_mean_waveform_microvolts"]) == hpc1.N_SAMPLES
    assert len(summary["clean_trial_p2p_microvolts"]["late"]) == 24

    def lane(d, low, loo):
        return {"D": d, "bootstrap": (low, 1.0, .9), "paired_p17_p19": 1.0,
                "leave_one_participant_out": loo}
    result_obj = {"clinical": {"late": lane(-.1, -.2, {"p16": -.1}), "early": lane(0, -.1, {"p16": 1}),
                               "prestim": lane(0, -.1, {"p16": 1})},
                  "bipolar": {"late": lane(1, .1, {"p16": 1})}}
    assert hpc1._status_lattice(result_obj)["same_data_status"] == "SAME_DATA_REANALYSIS_NOT_SUPPORTED"
    result_obj["clinical"]["late"] = lane(1, .1, {"p16": -.1})
    assert "PARTICIPANT_SENSITIVE" in hpc1._status_lattice(result_obj)["flags"]


def test_success_transaction_commits_result_before_terminal_progress(tmp_path, monkeypatch):
    progress, result = tmp_path / "progress.json", tmp_path / "result.json"
    hpc1._atomic_json(progress, {"status": "RAW_IN_PROGRESS", "attempt_id": "ATTEMPT1"})
    calls = []
    original = hpc1._atomic_json
    def traced(path, payload):
        calls.append(path)
        original(path, payload)
    monkeypatch.setattr(hpc1, "_atomic_json", traced)
    hpc1._commit_raw_success(result, progress, {"status": "RAW_COMPLETE", "attempt_id": "ATTEMPT1"})
    assert calls == [result, progress]
    terminal = json.loads(progress.read_text(encoding="utf-8"))
    assert result.exists() and terminal["status"] == "RAW_COMPLETE" and terminal["raw_result_sha256"]
