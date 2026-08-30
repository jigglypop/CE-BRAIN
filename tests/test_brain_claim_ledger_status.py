from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "paper" / "검증_원장" / "리만부분공간_의식순간_주장원장.md"
NARRATIVE = ROOT / "paper" / "6_뇌" / "12_리만부분공간_의식순간_강화.md"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _claim_rows(text: str) -> dict[str, str]:
    rows: dict[str, str] = {}
    for line in text.splitlines():
        match = re.match(r"^\| (CE-[A-Z0-9-]+) \|", line)
        if match is None:
            continue
        claim_id = match.group(1)
        assert claim_id not in rows, f"duplicate claim row: {claim_id}"
        rows[claim_id] = line
    return rows


def test_canonical_brain_documents_have_no_c0_control_characters() -> None:
    for path in (LEDGER, NARRATIVE):
        text = _read(path)
        bad = [
            (index, ord(char))
            for index, char in enumerate(text)
            if ord(char) < 32 and char not in "\t\n\r"
        ]
        assert bad == [], f"{path}: unexpected C0 controls {bad[:10]}"


def test_successor_closed_claims_are_not_left_open() -> None:
    text = _read(LEDGER)
    rows = _claim_rows(text)

    assert "후속 정리로 폐쇄" in rows["CE-SUBSPACE-003"]
    assert "프로토콜 폐쇄" in rows["CE-E1-003"]
    assert "후속 정리로 부분 폐쇄" in rows["CE-TIGHTINT-004"]
    assert "후속 정리로 폐쇄" in rows["CE-GRAPH-004"]
    assert "후속 정리로 부분 폐쇄" in rows["CE-RMESH-005"]
    assert "후속 정리로 부분 폐쇄" in rows["CE-RPOLY-005"]
    assert "후속 정리로 부분 폐쇄" in rows["CE-PQUAD-006"]
    assert "후속 정리로 부분 폐쇄" in rows["CE-RAD-005"]
    assert "후속 정리로 부분 폐쇄" in rows["CE-RBRIDGE-005"]
    assert "후속 정리로 부분 폐쇄" in rows["CE-PRAD-005"]
    assert "후속 정리로 부분 폐쇄" in rows["CE-SPLRAD-005"]
    assert "후속 정리로 부분 폐쇄" in rows["CE-RSPLRAD-005"]
    assert "후속 정리로 부분 폐쇄" in rows["CE-ARP-005"]
    assert "후속 정리로 부분 폐쇄" in rows["CE-PSPEC-005"]

    residual = rows["CE-RESINT-004"]
    assert "finite predeclared diagonal/dense menus" in residual
    assert "arbitrary finite rational circle meshes" in residual
    assert "simple polygonal Jordan contour" in rows["CE-RPOLY-001"]


def test_retired_open_phrases_do_not_reappear() -> None:
    text = _read(LEDGER)
    retired = (
        "joint local composition remains open",
        "composition with this local domain gate remains open",
        "No E1 scoring implementation",
        "Residual/Krawczyk and empirical coverage parts remain open",
        "General noncircular contour, arbitrary-mesh projector quadrature",
        "General smooth Jordan geometry, verified quadrature of the nominal projector",
        "Smooth-contour parameterization, adaptive verified refinement",
        "General smooth nonpolygonal contour/quadrature",
        "verified smooth quadrature/rank extraction",
    )
    for phrase in retired:
        assert phrase not in text


def test_genuine_empirical_and_execution_ceilings_remain_explicit() -> None:
    rows = _claim_rows(_read(LEDGER))

    assert "[미완성]" in rows["CE-E1META-004"]
    assert "[미완성]" in rows["CE-NMB-007"]
    assert "[미완성: narrowed]" in rows["CE-B64-005"]
    assert "미완성: narrowed" in rows["CE-RPOLY-005"]
    assert "미완성: narrowed" in rows["CE-PQUAD-006"]
    assert "[미완성: narrowed]" in rows["CE-APREF-005"]
    assert "미완성: narrowed" in rows["CE-ELL-005"]
    assert "[미완성: narrowed]" in rows["CE-EBRIDGE-005"]
    assert "미완성: narrowed" in rows["CE-CSEL-005"]
    assert "미완성: narrowed" in rows["CE-PSPEC-005"]
    assert "미완성: narrowed" in rows["CE-CHSPEC-005"]
    assert "[미완성: narrowed]" in rows["CE-QFACT-005"]
    assert "미완성: narrowed" in rows["CE-CXSPEC-005"]
    assert "미완성: narrowed" in rows["CE-IVSPEC-005"]
    assert "미완성: narrowed" in rows["CE-COPT-005"]
    assert "[미완성: narrowed]" in rows["CE-CAOPT-005"]
    assert "미완성: narrowed" in rows["CE-EOPT-005"]
    assert "미완성: narrowed" in rows["CE-SEOPT-005"]
    assert "미완성: narrowed" in rows["CE-GAOPT-005"]
    assert "미완성: narrowed" in rows["CE-KOPT-005"]
    assert "미완성: narrowed" in rows["CE-MKSPEC-005"]
    assert "미완성: narrowed" in rows["CE-MKRES-004"]
    assert "[미완성: narrowed]" in rows["CE-MKINT-004"]
    assert "[미완성: narrowed]" in rows["CE-DEFCON-004"]
    assert "[미완성: narrowed]" in rows["CE-DEFINT-004"]
    assert "[미완성: narrowed]" in rows["CE-AUTODEF-004"]
    assert "[미완성: narrowed]" in rows["CE-GADEF-004"]
    assert "[미완성: narrowed]" in rows["CE-AIGADEF-004"]
    assert "미완성: narrowed" in rows["CE-AOPT-004"]
    assert "미완성: narrowed" in rows["CE-SAOPT-004"]
    assert "미완성: narrowed" in rows["CE-DAOPT-004"]
    assert "[미완성: narrowed]" in rows["CE-DIFACT-004"]
    assert "[미완성: narrowed]" in rows["CE-CFOPT-004"]
    assert "[미완성: narrowed]" in rows["CE-CCOV-004"]
    assert "미완성: narrowed" in rows["CE-DSTAB-004"]
    assert "미완성: narrowed" in rows["CE-DEXEC-004"]
    assert "미완성: narrowed" in rows["CE-DPCA-004"]
    assert "미완성: narrowed" in rows["CE-DPREP-004"]
    assert "미완성: narrowed" in rows["CE-DMAN-004"]
    assert "미완성: narrowed" in rows["CE-DBYTE-004"]
    assert "[미완성: narrowed]" in rows["CE-DSIGN-005"]
    assert "[미완성: narrowed]" in rows["CE-EDIM-005"]
    assert "[미완성: narrowed]" in rows["CE-ENOISE-005"]
    assert "미완성: narrowed" in rows["CE-EDISC-005"]
    assert "미완성: narrowed" in rows["CE-NDISC-005"]
    assert "미완성: narrowed" in rows["CE-DDISC-005"]
    assert "미완성: narrowed" in rows["CE-IDISC-005"]
    assert "미완성: narrowed" in rows["CE-CIDISC-005"]
    assert "미완성: narrowed" in rows["CE-SCIDISC-005"]
    assert "[미완성: narrowed]" in rows["CE-TCIDISC-005"]
    assert "remote" in rows["CE-E1META-004"]
    assert "empirical" in rows["CE-B64-005"]
