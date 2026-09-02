"""Repository layout and document-policy checker (canonical harness entry).

``check_repository(root)`` returns a list of violation strings; an empty list is
the only passing result. ``tests/test_canonical_document_policy.py`` asserts it.
The checks are layout and policy rules only. A green result says nothing about
the scientific status of any document.

Rules (see ``.codex/harnesses/document_policy.md``):

1. ``paper/`` is the canonical document root and required harness entry points exist.
2. The retired document root literal never reappears on active surfaces.
3. Instruction files stay inside their byte budget.
4. No relative markdown link on an active surface points at a missing file, and
   no link targets the run workspace that lives outside this repository.
5. No zero-byte file is left under ``paper/``.
6. Narrative (non-ledger) markdown under ``paper/`` stays below the size ceiling;
   larger hand-accumulated files must be converted into a ``00_논문목차.md`` folder.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

# The retired root is spelled from parts so this file never contains the literal.
RETIRED_DOC_ROOT_LITERAL = "doc" + "s/"
EXTERNAL_RUN_ROOT = "_workspace/"

ACTIVE_SURFACES = (
    "AGENTS.md",
    "README.md",
    "paper",
    ".codex",
    ".claude",
    "tests",
    "examples",
    "experiments",
    "benchmarks/reports",
)
REQUIRED_PATHS = (
    "paper/README.md",
    ".codex/README.md",
    ".codex/harnesses/brain_evidence_ladder.md",
    ".codex/harnesses/document_policy.md",
    ".codex/hooks/python.cmd",
    ".codex/hooks/python_harness.py",
    ".codex/hooks/check-large-data.cmd",
    ".codex/hooks/check_large_data.py",
    ".codex/hooks/repository_harness.py",
)
INSTRUCTION_BUDGET_BYTES = {
    "AGENTS.md": 16_000,
    ".claude/CLAUDE.md": 8_000,
}
NARRATIVE_DOC_MAX_BYTES = 200_000
LEDGER_DIRS = ("paper/검증_원장",)
SKIP_DIR_NAMES = {".git", "__pycache__", "target", "node_modules", "data", ".pytest_cache"}
PATH_SUFFIXES = (
    ".md", ".py", ".rs", ".json", ".jsonl", ".tsv", ".csv", ".ps1", ".cmd",
    ".txt", ".toml", ".cu", ".sh", ".yaml", ".yml",
)
LINK_RE = re.compile(r"\[([^\]]*)\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")


def _rel(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def _iter_files(root: Path, suffixes: tuple[str, ...]) -> list[Path]:
    found: list[Path] = []
    for surface in ACTIVE_SURFACES:
        base = root / surface
        if base.is_file():
            if base.suffix in suffixes:
                found.append(base)
            continue
        if not base.is_dir():
            continue
        for path in base.rglob("*"):
            if any(part in SKIP_DIR_NAMES for part in path.relative_to(root).parts):
                continue
            if path.is_file() and path.suffix in suffixes:
                found.append(path)
    return sorted(set(found))


def _looks_like_path(target: str) -> bool:
    if target.startswith(("http://", "https://", "mailto:", "#", "$")):
        return False
    if "\\" in target or "{" in target or "}" in target:
        return False
    if target.startswith(("./", "../", "/")):
        return True
    if "/" in target:
        return True
    return target.lower().endswith(PATH_SUFFIXES)


def check_required_paths(root: Path) -> list[str]:
    return [f"missing required path: {rel}" for rel in REQUIRED_PATHS if not (root / rel).exists()]


def check_retired_root(root: Path) -> list[str]:
    violations: list[str] = []
    for path in _iter_files(root, (".md", ".py", ".cmd", ".ps1", ".sh", ".toml")):
        if path.resolve() == Path(__file__).resolve():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for number, line in enumerate(text.splitlines(), start=1):
            if RETIRED_DOC_ROOT_LITERAL in line and "http" not in line:
                violations.append(f"retired document root literal: {_rel(root, path)}:{number}")
    return violations


def check_instruction_budget(root: Path) -> list[str]:
    violations: list[str] = []
    for rel, budget in INSTRUCTION_BUDGET_BYTES.items():
        path = root / rel
        if path.exists() and path.stat().st_size > budget:
            violations.append(f"instruction budget exceeded: {rel} {path.stat().st_size} > {budget} bytes")
    return violations


def check_links(root: Path) -> list[str]:
    violations: list[str] = []
    for path in _iter_files(root, (".md",)):
        text = path.read_text(encoding="utf-8")
        for match in LINK_RE.finditer(text):
            target = match.group(2)
            if not _looks_like_path(target):
                continue
            line = text.count("\n", 0, match.start()) + 1
            location = f"{_rel(root, path)}:{line}"
            if target.startswith(EXTERNAL_RUN_ROOT) or f"/{EXTERNAL_RUN_ROOT}" in target:
                violations.append(f"link into external run workspace: {location} -> {target}")
                continue
            file_part = target.split("#", 1)[0]
            if not file_part:
                continue
            resolved = (path.parent / file_part).resolve()
            if not resolved.exists():
                violations.append(f"broken link: {location} -> {target}")
    return violations


def check_zero_byte_files(root: Path) -> list[str]:
    violations: list[str] = []
    paper = root / "paper"
    if not paper.is_dir():
        return violations
    for path in paper.rglob("*"):
        if any(part in SKIP_DIR_NAMES for part in path.relative_to(root).parts):
            continue
        if path.is_file() and path.name != ".gitkeep" and path.stat().st_size == 0:
            violations.append(f"zero-byte file under paper/: {_rel(root, path)}")
    return violations


def check_narrative_size(root: Path) -> list[str]:
    violations: list[str] = []
    paper = root / "paper"
    if not paper.is_dir():
        return violations
    for path in paper.rglob("*.md"):
        rel = _rel(root, path)
        if any(rel.startswith(ledger + "/") for ledger in LEDGER_DIRS):
            continue
        size = path.stat().st_size
        if size > NARRATIVE_DOC_MAX_BYTES:
            violations.append(
                f"narrative document over {NARRATIVE_DOC_MAX_BYTES} bytes ({size}); "
                f"convert to a 00_논문목차.md folder: {rel}"
            )
    return violations


def check_repository(root: Path | str) -> list[str]:
    root = Path(root).resolve()
    violations: list[str] = []
    violations.extend(check_required_paths(root))
    violations.extend(check_retired_root(root))
    violations.extend(check_instruction_budget(root))
    violations.extend(check_links(root))
    violations.extend(check_zero_byte_files(root))
    violations.extend(check_narrative_size(root))
    return violations


def main(arguments: list[str]) -> int:
    root = Path(arguments[0]) if arguments else Path(__file__).resolve().parents[2]
    violations = check_repository(root)
    if violations:
        print(f"REPOSITORY_HARNESS_FAIL ({len(violations)} violations)")
        for violation in violations:
            print(f"  - {violation}")
        return 1
    print("REPOSITORY_HARNESS_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
