"""연구 단계 하네스.

한 단계는 핵심 전제 하나(C1–C8)의 명제 하나를 판정한다. 기준은 실행 전에 단계 파일에서 `check`로
고정하고, 결과는 `record`로 `research/results/<단계>.json` 한 곳에 남긴다. 역증명은 전제 항을 뺀 식의
오차를 함께 적어, 그 항 없이는 생물 기준값을 맞추지 못함을 보인다.

공리 채택: 자료 원장(`ledger/data_registry.jsonl`)에 등록된 실데이터로 계산한 판정이 지지됨일 때만
전제를 공리로 채택한다. 원장 자료 없이 낸 판정은 미확립이다.
"""

from __future__ import annotations

import datetime
import hashlib
import json
import sys
import threading
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
RESULTS = HERE / "results"
LEDGER = ROOT / "ledger/data_registry.jsonl"
WRITING = threading.Lock()  # 병렬 추출이 원장 줄을 섞지 않게
PREMISES = {
    "C1": "하나의 공통 구조",
    "C2": "고정된 뉴런, 변하는 상태와 관계",
    "C3": "현재 상태에 남는 과거 흔적",
    "C4": "기능적 거리와 변화 비용 = 리만 계량",
    "C5": "지형(유지)과 방향의 분리",  # 09-29 개명: C5-1이 가른 것은 대칭(E)과 반대칭(F) 결합이다
    "C6": "학습·기억 = 이력에 따른 관계·계량 변화",
    "C7": "해마 = 기억의 주소 지정·검색",
    "C8": "여러 표현 중 하나가 지금 여기의 세계로 선택",
}


def registered(dataset, asset=None):
    """Latest ledger records of a dataset, or of one of its assets."""
    latest = {}
    with open(LEDGER, encoding="utf-8") as stream:
        for line in stream:
            row = json.loads(line) if line.strip() else {}
            if row.get("dataset") == dataset and asset in (None, row.get("asset")):
                latest[(row.get("version"), row.get("asset"))] = row
    if not latest:
        raise LookupError(f"not in the ledger: {dataset} {asset or ''}".strip())
    return list(latest.values())


def path(row):
    return ROOT / row["path"]


def verify(rows):
    """Raise unless every registered file is on disk with its ledger sha256."""
    for row in rows:
        if sha256(path(row)) != row["sha256"]:
            raise ValueError(f"{row['asset']} differs from its ledger record")


def register(dataset, version, asset, file, source, reason):
    """Append a verified file to the ledger. Earlier records are never rewritten."""
    file = Path(file).resolve()
    stat = file.stat()
    row = {"dataset": dataset, "version": version, "asset": asset,
           "path": file.relative_to(ROOT).as_posix() if file.is_relative_to(ROOT) else str(file),
           "source": source, "reason": reason, "sha256": sha256(file), "status": "verified_file",
           "bytes": stat.st_size, "mtime_ns": stat.st_mtime_ns,
           "recorded_at": datetime.datetime.now(datetime.timezone.utc).isoformat()}
    with WRITING, open(LEDGER, "a", encoding="utf-8") as stream:
        stream.write(json.dumps(row, ensure_ascii=False) + "\n")
    return row


def check(value, low=None, high=None):
    """One criterion fixed before the run: low ≤ value ≤ high. A None value is not evaluated."""
    value = None if value is None else float(value)
    passed = None if value is None else (low is None or value >= low) and (high is None or value <= high)
    return {"value": value, "low": low, "high": high, "passed": passed}


def reverse(term, error_with, error_without, tolerance):
    """역증명: the error is within tolerance with the premise term and outside it without."""
    return {"term": term, "error_with": float(error_with), "error_without": float(error_without),
            "tolerance": tolerance, "passed": bool(error_with <= tolerance < error_without)}


def verdict(judged, data):
    passed = [item["passed"] for item in judged]
    if not data or any(p is None for p in passed):
        return "미확립"
    return "지지됨" if all(passed) else "실패"


def record(step, premise, claim, reference, checks, data, proof=None, **measured):
    """Write one step's verdict with its criteria, reverse proof, ledger data and code hashes."""
    if premise not in PREMISES:
        raise ValueError(f"unknown premise: {premise}")
    for row in data:
        if not path(row).is_file() or path(row).stat().st_size != row["bytes"]:
            raise ValueError(f"{row['asset']} is missing or differs from its ledger record")
    judged = verdict(list(checks.values()) + ([proof] if proof else []), data)
    result = {
        "step": step, "premise": premise, "premise_text": PREMISES[premise], "claim": claim,
        "reference": reference, "checks": checks, "reverse_proof": proof,
        "verdict": judged, "axiom_adopted": judged == "지지됨", "measured": measured,
        "data": [{k: row[k] for k in ("dataset", "version", "asset", "sha256")} for row in data],
        "code_sha256": {p.relative_to(HERE).as_posix(): sha256(p) for p in code()},
        "date": datetime.date.today().isoformat(),
    }
    RESULTS.mkdir(exist_ok=True)
    (RESULTS / f"{step}.json").write_text(json.dumps(result, ensure_ascii=False, indent=1),
                                          encoding="utf-8")
    return result


def code():
    """Source files the running step has loaded: its research modules, and the Rust kernels when cefast is loaded."""
    files = {Path(m.__file__).resolve() for name, m in list(sys.modules.items())
             if (name.startswith("research.") or name == "__main__") and getattr(m, "__file__", None)}
    files = {f for f in files if f.is_relative_to(HERE) and f.suffix == ".py"}
    if "cefast" in sys.modules:
        files |= {HERE / "fast/Cargo.toml", *HERE.glob("fast/src/*.rs")}
    return sorted(files)


def sha256(file):
    with open(file, "rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()
