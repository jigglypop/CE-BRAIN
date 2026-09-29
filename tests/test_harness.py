import datetime
import json
import subprocess
import sys

import pytest

from research import harness

STEPS = ("s", "t", "u", "v")


def git(root, *args):
    return subprocess.run(["git", "-C", str(root), "-c", "user.name=t", "-c", "user.email=t@t", *args],
                          capture_output=True, text=True, check=True).stdout.strip()


def at(monkeypatch, *parts):
    monkeypatch.setattr(harness, "now", lambda: datetime.datetime(*parts, tzinfo=datetime.timezone.utc))


@pytest.fixture
def repo(tmp_path, monkeypatch):
    """A git repo whose research/ holds committed step files s, t, u, v."""
    monkeypatch.setattr(harness, "ROOT", tmp_path)
    monkeypatch.setattr(harness, "HERE", tmp_path / "research")
    monkeypatch.setattr(harness, "RESULTS", tmp_path / "research/results")
    monkeypatch.setattr(harness, "LEDGER", tmp_path / "ledger.jsonl")
    monkeypatch.delitem(sys.modules, "cefast", raising=False)
    (tmp_path / "research").mkdir()
    for step in STEPS:
        (tmp_path / f"research/{step}.py").write_text('"""판정 기준."""\n', encoding="utf-8")
    git(tmp_path, "init", "-q")
    git(tmp_path, "add", "research")
    git(tmp_path, "commit", "-q", "-m", "steps")
    return tmp_path


@pytest.fixture
def ledger(repo):
    data = repo / "x.bin"
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
        harness.record("s", "C9", "c", "r", {}, [ledger])


def test_record_refuses_a_step_file_not_committed_as_is(repo, ledger, monkeypatch):
    ok = {"a": harness.check(1, 0, 2)}
    (repo / "research/new.py").write_text("", encoding="utf-8")
    (repo / "research/s.py").write_text('"""판정 기준을 바꿈."""\n', encoding="utf-8")
    for name in ("new", "s", "missing"):  # untracked, changed after its commit, absent
        with pytest.raises(RuntimeError):
            harness.record(name, "C4", "c", "r", ok, [ledger])
    git(repo, "add", "research/s.py")  # staged is not committed
    with pytest.raises(RuntimeError):
        harness.record("s", "C4", "c", "r", ok, [ledger])
    assert not harness.RESULTS.exists()
    git(repo, "commit", "-q", "-m", "criteria")
    at(monkeypatch, 2026, 9, 29, 3, 4, 5)
    result = harness.record("s", "C4", "c", "r", ok, [ledger])
    assert result["git"]["step_commit"] == result["git"]["head"] == git(repo, "rev-parse", "HEAD")
    assert result["git"]["step_committed_at"] == git(repo, "log", "-1", "--format=%cI", "--", "research/s.py")
    assert result["run_at"] == "2026-09-29T03:04:05+00:00"


def test_record_refuses_changed_code_the_step_loaded(repo, ledger, monkeypatch):
    helper = repo / "research/t.py"
    monkeypatch.setattr(harness, "code", lambda: [helper])
    helper.write_text('"""바뀐 도우미."""\n', encoding="utf-8")
    with pytest.raises(RuntimeError):
        harness.record("s", "C4", "c", "r", {"a": harness.check(1, 0, 2)}, [ledger])


def test_runs_accumulate_and_the_step_file_names_the_latest(repo, ledger, monkeypatch):
    ok = {"a": harness.check(1, 0, 2)}
    at(monkeypatch, 2026, 9, 29, 1, 0, 0)
    harness.record("s", "C4", "c", "r", ok, [ledger])
    at(monkeypatch, 2026, 9, 29, 2, 0, 0)
    harness.record("s", "C4", "c", "r", {"a": harness.check(3, 0, 2)}, [ledger])
    runs = sorted(p.name for p in (harness.RESULTS / "s").iterdir())
    assert runs == ["20260929T010000Z.json", "20260929T020000Z.json"]
    first = json.loads((harness.RESULTS / "s" / runs[0]).read_text(encoding="utf-8"))
    latest = (harness.RESULTS / "s.json").read_text(encoding="utf-8")
    assert first["verdict"] == "지지됨"
    assert latest == (harness.RESULTS / "s" / runs[1]).read_text(encoding="utf-8")
    assert json.loads(latest)["run"] == "s/20260929T020000Z.json" and json.loads(latest)["verdict"] == "실패"
    with pytest.raises(FileExistsError):  # a run is never overwritten, even in the same second
        harness.record("s", "C4", "c", "r", ok, [ledger])
    assert (harness.RESULTS / "s.json").read_text(encoding="utf-8") == latest


def test_a_result_from_before_accumulation_is_kept(repo, ledger, monkeypatch):
    harness.RESULTS.mkdir()
    (harness.RESULTS / "t.json").write_text(json.dumps({"step": "t", "date": "2026-09-28"}), encoding="utf-8")
    at(monkeypatch, 2026, 9, 29, 1, 0, 0)
    harness.record("t", "C4", "c", "r", {"a": harness.check(1, 0, 2)}, [ledger])
    kept = json.loads((harness.RESULTS / "t/20260928-legacy.json").read_text(encoding="utf-8"))
    assert kept == {"step": "t", "date": "2026-09-28"}
    assert json.loads((harness.RESULTS / "t.json").read_text(encoding="utf-8"))["run"] == "t/20260929T010000Z.json"
