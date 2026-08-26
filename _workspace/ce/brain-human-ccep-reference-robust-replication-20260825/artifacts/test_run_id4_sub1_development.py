import importlib.util
import sys
from pathlib import Path


HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
spec = importlib.util.spec_from_file_location("subject_runner", HERE / "run_id4_sub1_development.py")
runner = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(runner)


def test_bounded_concurrency_cap_and_observation():
    assert runner.SIGNAL_WORKERS == 8
    assert runner.MAX_SITE_TRIALS == 23
    assert runner._observed_max_concurrency([(0, 10), (1, 4), (2, 8), (11, 12)]) == 3
    assert runner._observed_max_concurrency([(0, 1), (1, 2)]) == 1
    try:
        runner._run_site("X1-X2", [], [], {}, {}, workers=9)
        raise AssertionError("signal concurrency above the frozen cap accepted")
    except ValueError as exc:
        assert "bounded signal concurrency" in str(exc)
    too_many = [{"node": "X1-X2"}] * 24
    try:
        runner._run_site("X1-X2", too_many, [], {}, {}, workers=8)
        raise AssertionError("site above the frozen trial cap accepted")
    except RuntimeError as exc:
        assert "site events" in str(exc)


def test_resume_is_fail_closed_on_cleanup_or_contract_mismatch():
    rows = [{"channel": f"C{index}", "cleanup": True, "persistent_raw_bytes": 0} for index in range(2)]
    payload = {
        "status": "PASS_DEVELOPMENT_SITE_ENDPOINT", "subject": "sub-1", "stimulation_site": "X1-X2",
        "amendment_id": runner.AMENDMENT_ID, "plan_sha256": runner.PLAN_SHA256, "channels": 2,
        "channel_receipts": rows, "max_signal_concurrency": 8, "observed_max_concurrency": 2,
        "persistent_raw_bytes": 0, "raw_tile_disposed": True, "cross_site_signal_cache": False,
        "decoded_value_cache_after_copy": False,
    }
    assert runner._resumable_site_receipt(payload, site="X1-X2", channels=2)
    payload["channel_receipts"][0]["cleanup"] = False
    assert not runner._resumable_site_receipt(payload, site="X1-X2", channels=2)
