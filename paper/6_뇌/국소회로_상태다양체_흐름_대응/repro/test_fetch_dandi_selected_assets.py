import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

import fetch_dandi_selected_assets as downloader
from fetch_dandi_selected_assets import load_selection, safe_target, verify_existing


def _selection(path: Path, payload: bytes) -> dict:
    asset = {
        "asset_id": "asset-1",
        "path": "sub-Ctrl-1/example.nwb",
        "size": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
        "url": "https://example.invalid/example.nwb",
    }
    path.write_text(
        json.dumps(
            {
                "status": "DANDI_ASSET_SELECTION_AUDIT_PASS",
                "selected_assets": [asset],
            }
        ),
        encoding="utf-8",
    )
    return asset


def test_safe_target_rejects_traversal(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="unsafe"):
        safe_target(tmp_path, "../escape.nwb")


def test_safe_target_stays_below_resolved_root(tmp_path: Path) -> None:
    target = safe_target(tmp_path, "sub-Ctrl-1/example.nwb")
    assert target == tmp_path.resolve() / "sub-Ctrl-1" / "example.nwb"


def test_load_selection_requires_passing_receipt(tmp_path: Path) -> None:
    path = tmp_path / "selection.json"
    path.write_text(json.dumps({"status": "FAIL", "selected_assets": []}), encoding="utf-8")
    with pytest.raises(ValueError, match="not a passing"):
        load_selection(path)


def test_existing_asset_is_verified_without_network(tmp_path: Path) -> None:
    selection_path = tmp_path / "selection.json"
    payload = b"source-locked biological bytes"
    asset = _selection(selection_path, payload)
    root = tmp_path / "data"
    target = safe_target(root, asset["path"])
    target.parent.mkdir(parents=True)
    target.write_bytes(payload)
    result = verify_existing(target, asset)
    assert result is not None
    assert result["transfer"] == "already_verified"
    assert result["sha256"] == asset["sha256"]


def test_existing_mismatch_stops(tmp_path: Path) -> None:
    selection_path = tmp_path / "selection.json"
    payload = b"expected"
    asset = _selection(selection_path, payload)
    root = tmp_path / "data"
    target = safe_target(root, asset["path"])
    target.parent.mkdir(parents=True)
    target.write_bytes(b"wrong___")
    with pytest.raises(ValueError, match="SHA-256 mismatch"):
        verify_existing(target, asset)


def test_curl_backend_uses_safe_argument_list_and_resume(tmp_path: Path, monkeypatch) -> None:
    partial = tmp_path / "asset.part"
    partial.write_bytes(b"1234")
    asset = {
        "path": "sub-Ctrl-1/example.nwb",
        "url": "https://example.invalid/a",
        "size": 10,
    }
    observed = {}

    monkeypatch.setattr(downloader.shutil, "which", lambda name: "C:/Windows/curl.exe")

    def fake_run(command, **kwargs):
        observed["command"] = command
        observed["kwargs"] = kwargs
        range_start, range_end = (
            int(value) for value in command[command.index("--range") + 1].split("-")
        )
        output = Path(command[command.index("--output") + 1])
        output.write_bytes(b"x" * (range_end - range_start + 1))
        return SimpleNamespace(returncode=0, stdout="206", stderr="")

    monkeypatch.setattr(downloader.subprocess, "run", fake_run)
    transfer = downloader._curl_transfer(partial, asset, 33.0, 4)
    assert transfer == "resumed_curl"
    assert observed["command"][0] == "C:/Windows/curl.exe"
    assert observed["command"][observed["command"].index("--range") + 1] == "4-9"
    assert observed["command"][-1] == asset["url"]
    assert observed["kwargs"] == {"capture_output": True, "text": True, "check": False}
    assert partial.read_bytes() == b"1234" + b"x" * 6
