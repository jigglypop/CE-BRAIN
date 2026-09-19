"""Run an explicitly selected historical test/script in its original checkout."""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]

def main(arguments: list[str]) -> int:
    if len(arguments) < 2 or arguments[0] not in {"pytest", "python"}:
        raise SystemExit("Usage: python tools/historical.py pytest|python ORIGINAL_PATH [arguments...]")
    manifest = json.loads((ROOT / "ledger/reality_stone_extraction.json").read_text(encoding="utf-8"))
    archive = Path(os.environ.get("CE_REPRO_SOURCE_ROOT", str(ROOT.parent / "ce-agi-runtime-repro-fffd356"))).resolve()
    if archive == ROOT or not (archive / ".git").is_dir():
        raise SystemExit(f"Preserved checkout not found: {archive}; see LIBRARY.md")
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=archive, text=True).strip()
    if head != manifest["source_commit"]:
        raise SystemExit("Historical checkout HEAD differs from preserved source commit")
    relative = arguments[1].split("::", 1)[0].replace("\\", "/")
    expected = manifest["relocated_paths"].get(relative)
    if expected is None:
        raise SystemExit(f"Path is not registered for historical execution: {relative}")
    source = (archive / relative).resolve()
    if not source.is_relative_to(archive) or hashlib.sha256(source.read_bytes()).hexdigest() != expected:
        raise SystemExit("Historical source hash differs from preserved original")
    return subprocess.run([str(archive / ".codex/hooks/python.cmd"), *arguments], cwd=archive, check=False).returncode

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
