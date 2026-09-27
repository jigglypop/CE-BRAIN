import json

import pytest

from research import harness


@pytest.fixture
def ledger(tmp_path, monkeypatch):
    monkeypatch.setattr(harness, "LEDGER", tmp_path / "ledger.jsonl")
    monkeypatch.setattr(harness, "RESULTS", tmp_path / "results")
    data = tmp_path / "x.bin"
    data.write_bytes(b"real data")
    return harness.register("d", "v1", "x.bin", data, "https://source", "test")


def test_check_bounds_and_unevaluated():
    assert harness.check(0.5, 0, 1)["passed"] is True
    assert harness.check(1.5, 0, 1)["passed"] is False
    assert harness.check(None, 0, 1)["passed"] is None


def test_reverse_proof_needs_the_term():
    assert harness.reverse("G", 0.1, 0.9, 0.2)["passed"] is True
    assert harness.reverse("G", 0.1, 0.15, 0.2)["passed"] is False


def test_register_then_verify(ledger):
    (row,) = harness.registered("d", "x.bin")
    assert row["sha256"] == ledger["sha256"]
    harness.verify([row])
    harness.path(row).write_bytes(b"changed")
    with pytest.raises(ValueError):
        harness.verify([row])
    with pytest.raises(LookupError):
        harness.registered("missing")


def test_axiom_needs_ledger_data(ledger):
    ok = harness.check(1, 0, 2)
    adopted = harness.record("s", "C4", "c", "r", {"a": ok}, [ledger],
                             proof=harness.reverse("G", 0.1, 0.9, 0.2), extra=3)
    saved = json.loads((harness.RESULTS / "s.json").read_text(encoding="utf-8"))
    assert adopted["verdict"] == "지지됨" and saved["axiom_adopted"] and saved["measured"] == {"extra": 3}
    assert harness.record("t", "C4", "c", "r", {"a": ok}, [])["verdict"] == "미확립"
    assert harness.record("u", "C4", "c", "r", {"a": harness.check(3, 0, 2)}, [ledger])["verdict"] == "실패"
    assert harness.record("v", "C4", "c", "r", {"a": harness.check(None)}, [ledger])["verdict"] == "미확립"
    with pytest.raises(ValueError):
        harness.record("w", "C9", "c", "r", {}, [ledger])
