import hashlib
import json
import importlib.util
import struct
import sys
import urllib.error
import shutil
from types import SimpleNamespace
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
spec = importlib.util.spec_from_file_location("acquire", HERE / "id4_development_index_acquire.py")
acquire = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(acquire)

CHANNELS = b"name\ttype\tunits\tsampling_frequency\tstatus\nA\tseeg\tuV\t2048\tgood\nB\tecog\tuV\t2048\tgood\nC\tieeg\tuV\t2048\tgood\nD\tieeg\tuV\t2048\tgood2\n"
ELECTRODES = b"name\tx\ty\tz\nA\t0\t0\t0\nB\t2\t0\t0\nC\t30\t0\t0\n"
EVENTS = ("status\telectrical_stimulation_current\telectrical_stimulation_type\telectrical_stimulation_site\tonset\n" +
          "".join(f"good\t6.0 mA\tbiphasic\tA-B\t{(2048 + index) / 2048}\n" for index in range(10))).encode()
PATHS = acquire._tsv_paths("sub-1")


def _index():
    return bytes(1024) + b"".join(struct.pack("<qqqIIii16s", 1024 + 1936 * i, (10 + i) * 1_000_000, 2048 * i, 2048, 1936, 0, 0, bytes(16)) for i in range(3))


class Fake:
    def __init__(self, bodies, heads): self.bodies, self.heads, self.calls = bodies, heads, []
    def get(self, url, **kwargs):
        self.calls.append(("GET", url));
        if url.startswith(acquire.S3_PREFIX) and url.endswith(".tdat"): raise AssertionError("tdat body requested")
        return self.bodies[url]
    def head(self, url, **kwargs): self.calls.append(("HEAD", url)); return self.heads[url]


class Response:
    headers = {}
    def __init__(self, url, body=b"ok"): self.url, self.body = url, body
    def __enter__(self): return self
    def __exit__(self, *args): return False
    def geturl(self): return self.url
    def read(self, _size): return self.body


def _fixture():
    bodies = {acquire._url(acquire.RAW_PREFIX, PATHS[name]): body for name, body in (("events", EVENTS), ("channels", CHANNELS), ("electrodes", ELECTRODES))}
    cpaths = {channel: acquire._channel_paths("sub-1", channel) for channel in ("A", "B", "C")}
    heads = {}
    for channel, paths in cpaths.items():
        index = _index(); sha = hashlib.sha256(index).hexdigest(); pointer = f"/annex/objects/SHA256E-s{len(index)}--{sha}.tidx\n".encode()
        tdat_sha = "a" * 64; tdat_size = 6832; tdat_pointer = f"/annex/objects/SHA256E-s{tdat_size}--{tdat_sha}.tdat\n".encode()
        bodies[acquire._url(acquire.RAW_PREFIX, paths["tidx"])] = pointer; bodies[acquire._url(acquire.RAW_PREFIX, paths["tdat"])] = tdat_pointer; bodies[acquire._url(acquire.S3_PREFIX, paths["tidx"])] = index
        heads[acquire._url(acquire.S3_PREFIX, paths["tdat"])] = {"Content-Length": str(tdat_size), "ETag": "etag", "x-amz-version-id": "version"}
    return Fake(bodies, heads), cpaths


def test_injected_metadata_index_acquire_is_compact_and_never_gets_tdat(tmp_path):
    assert acquire._channel_paths("sub-1", "LV1") == {
        "tidx": "sub-1/ses-ieeg01/ieeg/sub-1_ses-ieeg01_task-ccep_run-01_ieeg.mefd/LV1.timd/LV1-000000.segd/LV1-000000.tidx",
        "tdat": "sub-1/ses-ieeg01/ieeg/sub-1_ses-ieeg01_task-ccep_run-01_ieeg.mefd/LV1.timd/LV1-000000.segd/LV1-000000.tdat",
    }
    assert acquire._channel_paths("sub-5", "RK1") == {
        "tidx": "sub-5/ses-ieeg01/ieeg/sub-5_ses-ieeg01_task-ccep_run-01_ieeg.mefd/RK1.timd/RK1-000000.segd/RK1-000000.tidx",
        "tdat": "sub-5/ses-ieeg01/ieeg/sub-5_ses-ieeg01_task-ccep_run-01_ieeg.mefd/RK1.timd/RK1-000000.segd/RK1-000000.tdat",
    }
    fake, cpaths = _fixture(); expected = {name: hashlib.sha256(body).hexdigest() for name, body in (("events", EVENTS), ("channels", CHANNELS), ("electrodes", ELECTRODES))}
    progress = []
    receipt = acquire.acquire_development_index(snapshot="ds004457-v1.0.2", subject="sub-1", tsv_paths=PATHS, channel_paths=cpaths, expected_tsv_sha256=expected, transport=fake, progress=lambda *args: progress.append(args))
    assert receipt["signal_accessed"] is False and receipt["development_index_opened"] and not receipt["development_signal_opened"]
    assert receipt["precision_convention"] == "decimal-onset-lexical-ulp-sample-grid-v4" and receipt["precision_convention_version"] == 4 and receipt["shared_start_sample"] == 0
    assert len(receipt["planned_ranges"]) == 3 and receipt["concurrency"] == 1 and receipt["retry_policy"]["max_attempts"] == 3
    assert progress == [(1, 3, "A"), (2, 3, "B"), (3, 3, "C")]
    assert receipt == acquire.acquire_development_index(snapshot="ds004457-v1.0.2", subject="sub-1", tsv_paths=PATHS, channel_paths=cpaths, expected_tsv_sha256=expected, transport=_fixture()[0])
    assert all(not (method == "GET" and url.startswith(acquire.S3_PREFIX) and url.endswith(".tdat")) for method, url in fake.calls)
    for subject, mutate in (("sub-2", None), ("sub-1", "hash"), ("sub-1", "head")):
        bad, paths = _fixture(); bad_expected = dict(expected)
        if mutate == "hash": bad_expected["events"] = "0" * 64
        if mutate == "head": next(iter(bad.heads.values()))["x-amz-version-id"] = ""
        try:
            acquire.acquire_development_index(snapshot="ds004457-v1.0.2", subject=subject, tsv_paths=PATHS, channel_paths=paths, expected_tsv_sha256=bad_expected, transport=bad)
            raise AssertionError("source check accepted")
        except (ValueError, RuntimeError):
            pass
    bad, paths = _fixture(); next(iter(bad.heads.values()))["Content-Length"] = "1"
    try:
        acquire.acquire_development_index(snapshot="ds004457-v1.0.2", subject="sub-1", tsv_paths=PATHS, channel_paths=paths, expected_tsv_sha256=expected, transport=bad)
        raise AssertionError("tdat size mismatch accepted")
    except (ValueError, RuntimeError):
        pass
    calls, sleeps = [], []
    def transient(url, **kwargs):
        calls.append(url)
        if len(calls) == 1: raise TimeoutError("temporary")
        return Response(url)
    assert acquire.UrllibTransport(opener=transient, sleeper=sleeps.append).get(acquire.RAW_PREFIX + "x", timeout=1, max_bytes=10) == b"ok"
    assert len(calls) == 2 and sleeps == [0.05]
    permanent_calls = []
    def permanent(url, **kwargs):
        permanent_calls.append(url)
        raise urllib.error.HTTPError(str(url), 404, "not found", {}, None)
    try:
        acquire.UrllibTransport(opener=permanent, sleeper=lambda _: (_ for _ in ()).throw(AssertionError("retried permanent"))).get(acquire.RAW_PREFIX + "x", timeout=1, max_bytes=10)
        raise AssertionError("permanent HTTP failure accepted")
    except urllib.error.HTTPError:
        pass
    assert len(permanent_calls) == 1
    checkpoint = tmp_path / "resume.json"
    interrupted, paths = _fixture(); original_head = interrupted.head
    def stop_after_a(url, **kwargs):
        if url.endswith("B-000000.tdat"): raise TimeoutError("stop B")
        return original_head(url, **kwargs)
    interrupted.head = stop_after_a
    try:
        acquire.acquire_development_index(snapshot="ds004457-v1.0.2", subject="sub-1", tsv_paths=PATHS, channel_paths=paths, expected_tsv_sha256=expected, transport=interrupted, checkpoint_path=checkpoint)
        raise AssertionError("interruption accepted")
    except RuntimeError:
        pass
    state = json.loads(checkpoint.read_text())
    assert state["status"] == "IN_PROGRESS" and [entry["channel"] for entry in state["completed"]] == ["A"]
    assert state["precision_convention"] == "decimal-onset-lexical-ulp-sample-grid-v4" and state["precision_convention_version"] == 4 and state["shared_start_sample"] == 0
    assert "tidx_payload" not in json.dumps(state) and '"ranges"' not in json.dumps(state)
    def write_tampered(name, mutate, *, recompute=True):
        payload = json.loads(checkpoint.read_text()); mutate(payload)
        if recompute:
            payload.pop("checkpoint_sha256", None)
            payload["checkpoint_sha256"] = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        target = tmp_path / name; target.write_text(json.dumps(payload)); return target
    for target in (
        write_tampered("planned.json", lambda p: p["completed"][0].__setitem__("planned_tdat_bytes", 1)),
        write_tampered("hash.json", lambda p: p["completed"][0].__setitem__("range_sha256", "0" * 64), recompute=False),
        write_tampered("provenance.json", lambda p: p["completed"][0]["provenance"].__setitem__("etag", "")),
        write_tampered("extra.json", lambda p: p["completed"][0].__setitem__("extra", 1)),
        write_tampered("top-extra.json", lambda p: p.__setitem__("extra", 1)),
        write_tampered("old-precision.json", lambda p: p.pop("precision_convention")),
        write_tampered("stale.json", lambda p: p.__setitem__("subject", "sub-5"), recompute=False),
    ):
        try:
            acquire.acquire_development_index(snapshot="ds004457-v1.0.2", subject="sub-1", tsv_paths=PATHS, channel_paths=paths, expected_tsv_sha256=expected, transport=_fixture()[0], checkpoint_path=target)
            raise AssertionError("tampered completed checkpoint accepted")
        except ValueError:
            pass
    resumed, paths = _fixture()
    for url in list(resumed.bodies):
        if "/A.timd/" in url: del resumed.bodies[url]
    for url in list(resumed.heads):
        if "/A.timd/" in url: del resumed.heads[url]
    resumed_receipt = acquire.acquire_development_index(snapshot="ds004457-v1.0.2", subject="sub-1", tsv_paths=PATHS, channel_paths=paths, expected_tsv_sha256=expected, transport=resumed, checkpoint_path=checkpoint)
    assert resumed_receipt == receipt
    tampered = tmp_path / "tampered.json"; tampered.write_text(json.dumps({**state, "subject": "sub-5"}))
    try:
        acquire.acquire_development_index(snapshot="ds004457-v1.0.2", subject="sub-1", tsv_paths=PATHS, channel_paths=paths, expected_tsv_sha256=expected, transport=_fixture()[0], checkpoint_path=tampered)
        raise AssertionError("tampered checkpoint accepted")
    except ValueError:
        pass
    curl_exe = shutil.which("curl.exe")
    assert curl_exe is not None
    curl_calls = []
    def curl_runner(argv):
        curl_calls.append(argv)
        if "-I" in argv:
            return SimpleNamespace(returncode=0, stdout=b"HTTP/1.1 200 OK\r\nContent-Length: 7\r\nETag: tag\r\n\r\n", stderr=b"https://s3.amazonaws.com/openneuro.org/ds004457/x")
        return SimpleNamespace(returncode=0, stdout=b"payload", stderr=b"https://raw.githubusercontent.com/OpenNeuroDatasets/ds004457/1bbd3a0696c56b7dfd87020bc61092644a702d0a/x")
    curl = acquire.CurlTransport(runner=curl_runner, sleeper=lambda _: None, curl_path=curl_exe)
    assert curl.get(acquire.RAW_PREFIX + "x", timeout=1, max_bytes=10) == b"payload"
    assert curl.head(acquire.S3_PREFIX + "x", timeout=1) == {"Content-Length": "7", "ETag": "tag"}
    assert all(isinstance(argv, list) and not any("shell" in arg for arg in argv) for argv in curl_calls)
    get_argv, head_argv = curl_calls
    assert get_argv[get_argv.index("--max-filesize") + 1] == "10"
    assert "--max-filesize" not in head_argv
    range_calls = []
    def range_runner(argv):
        range_calls.append(argv)
        return SimpleNamespace(returncode=0, stdout=b"pay", stderr=b"https://s3.amazonaws.com/openneuro.org/ds004457/x\nbytes 2-4/7")
    ranged = acquire.CurlTransport(runner=range_runner, sleeper=lambda _: None, curl_path=curl_exe)
    assert ranged.get_range(acquire.S3_PREFIX + "x", start=2, end=4, timeout=1, max_bytes=3) == b"pay"
    assert range_calls[0][range_calls[0].index("--range") + 1] == "2-4"
    for bad in ((-1, 1, 3), (2, 1, 3), (0, 3, 3)):
        try:
            ranged.get_range(acquire.S3_PREFIX + "x", start=bad[0], end=bad[1], timeout=1, max_bytes=bad[2])
            raise AssertionError("invalid range accepted")
        except ValueError:
            pass
    escaped = acquire.CurlTransport(runner=lambda argv: SimpleNamespace(returncode=0, stdout=b"ok", stderr=b"https://example.invalid/"), sleeper=lambda _: None, curl_path=curl_exe)
    try:
        escaped.get(acquire.RAW_PREFIX + "x", timeout=1, max_bytes=10)
        raise AssertionError("effective host escape accepted")
    except ValueError:
        pass
    capped = acquire.CurlTransport(runner=lambda argv: SimpleNamespace(returncode=0, stdout=b"012345", stderr=b"https://raw.githubusercontent.com/OpenNeuroDatasets/ds004457/1bbd3a0696c56b7dfd87020bc61092644a702d0a/x"), sleeper=lambda _: None, curl_path=curl_exe)
    try:
        capped.get(acquire.RAW_PREFIX + "x", timeout=1, max_bytes=5)
        raise AssertionError("curl response cap accepted")
    except ValueError:
        pass
    retry_calls, retry_sleeps = [], []
    def curl_transient(argv):
        retry_calls.append(argv)
        if len(retry_calls) == 1:
            return SimpleNamespace(returncode=28, stdout=b"", stderr=b"timeout")
        return SimpleNamespace(returncode=0, stdout=b"ok", stderr=b"https://raw.githubusercontent.com/OpenNeuroDatasets/ds004457/1bbd3a0696c56b7dfd87020bc61092644a702d0a/x")
    assert acquire.CurlTransport(runner=curl_transient, sleeper=retry_sleeps.append, curl_path=curl_exe).get(acquire.RAW_PREFIX + "x", timeout=1, max_bytes=10) == b"ok"
    assert len(retry_calls) == 2 and retry_sleeps == [0.05]
    try:
        acquire._url(acquire.RAW_PREFIX, "../unlocked")
        raise AssertionError("unsafe host path accepted")
    except ValueError:
        pass
    bad, paths = _fixture(); wrong_paths = dict(PATHS); wrong_paths["events"] = "sub-2/ses-ieeg01/ieeg/x.tsv"
    try:
        acquire.acquire_development_index(snapshot="ds004457-v1.0.2", subject="sub-1", tsv_paths=wrong_paths, channel_paths=paths, expected_tsv_sha256=expected, transport=bad)
        raise AssertionError("cross-subject TSV path accepted")
    except ValueError:
        pass
    bad, paths = _fixture(); wrong_channels = dict(paths); wrong_channels["A"] = acquire._channel_paths("sub-1", "B")
    try:
        acquire.acquire_development_index(snapshot="ds004457-v1.0.2", subject="sub-1", tsv_paths=PATHS, channel_paths=wrong_channels, expected_tsv_sha256=expected, transport=bad)
        raise AssertionError("wrong channel path accepted")
    except ValueError:
        pass
    try:
        acquire._channel_paths("sub-1", "../unsafe")
        raise AssertionError("unsafe channel accepted")
    except ValueError:
        pass
