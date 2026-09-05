"""중복 등록·손상·미완료 파일을 수집 완료로 오인하지 않는지 검사한다."""
import importlib.util
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location(
    "data_registry", Path(__file__).resolve().parents[1] / ".codex/hooks/data_registry.py"
)
registry = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(registry)


def add(ledger, path, **kwargs):
    return registry.register(ledger, "dataset", kwargs.pop("version", "v1"), "asset",
                             path, "https://example.org/source", "테스트", **kwargs)


def test_same_asset_reuses_record_and_preserves_alternate_location(tmp_path):
    ledger = tmp_path / "ledger.jsonl"
    first, second = tmp_path / "first.bin", tmp_path / "second.bin"
    first.write_bytes(b"same")
    second.write_bytes(b"same")
    assert add(ledger, first)[1]
    assert not add(ledger, first)[1]
    assert add(ledger, second)[1]
    assert len(registry.find(ledger, registry.digest(first))) == 2


def test_changed_content_requires_resolution_or_distinct_version(tmp_path):
    ledger, path = tmp_path / "ledger.jsonl", tmp_path / "data.bin"
    path.write_bytes(b"original")
    add(ledger, path)
    path.write_bytes(b"changed data")
    assert registry.find(ledger, "dataset")[0]["local_state"] == "changed"
    with pytest.raises(ValueError, match="다른 해시"):
        add(ledger, path)
    assert add(ledger, path, version="v2")[1]
    assert registry.find(ledger, "v2", verify=True)[0]["local_state"] == "hash_match"


def test_partial_directory_and_missing_are_not_verified(tmp_path):
    ledger, partial = tmp_path / "ledger.jsonl", tmp_path / "data.partial"
    partial.write_bytes(b"unfinished")
    with pytest.raises(ValueError, match="미완료"):
        add(ledger, partial)
    add(ledger, partial, location_only=True)
    assert registry.find(ledger, "dataset")[0]["local_state"] == "partial"
    partial.unlink()
    assert registry.find(ledger, "dataset")[0]["local_state"] == "missing"
    with pytest.raises(ValueError, match="없습니다"):
        add(ledger, partial)
    add(ledger, tmp_path, location_only=True)
    assert registry.find(ledger, tmp_path.name)[-1]["local_state"] == "location_only"


def test_default_lookup_does_not_hash_but_verify_detects_same_metadata_damage(tmp_path, monkeypatch):
    ledger, path = tmp_path / "ledger.jsonl", tmp_path / "data.bin"
    path.write_bytes(b"original")
    add(ledger, path)
    original_digest = registry.digest
    monkeypatch.setattr(registry, "digest", lambda path: pytest.fail("조회 중 불필요한 해시 계산"))
    assert registry.find(ledger, "dataset")[0]["local_state"] == "unchanged_metadata"
    monkeypatch.setattr(registry, "digest", original_digest)
    import os
    stat = path.stat()
    path.write_bytes(b"modified")
    os.utime(path, ns=(stat.st_atime_ns, stat.st_mtime_ns))
    assert registry.find(ledger, "dataset", verify=True)[0]["local_state"] == "changed"
