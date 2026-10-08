"""연구 단계 하네스.

한 단계는 핵심 전제 하나(C1–C8)의 명제 하나를 판정한다. 기준은 실행 전에 단계 파일에서 `check`로
고정하고, 결과는 `record`로 남긴다. 역증명은 전제 항을 뺀 식의 오차를 함께 적어, 그 항 없이는 생물
기준값을 맞추지 못함을 보인다.

기준이 실행 전에 고정되었음은 git이 보인다. `record`는 단계 파일과 그 단계가 읽은 연구 코드가 커밋된 그대로일
때만 결과를 쓰고, 단계 파일의 커밋 해시·커밋 시각과 실행 시각을 남긴다. 실행은 덮어쓰지 않고
`research/results/<단계>/<UTC시각>.json`으로 쌓으며, `research/results/<단계>.json`은 최신 실행과 같다.

단계 판정: 자료 원장(`ledger/data_registry.jsonl`)에 등록된 실데이터로 계산해야 지지됨이 될 수 있다. 원장 자료 없이 낸
판정은 미확립이다. 전제 상태(채택·잠정·미채택)는 단계 판정을 모아 `tools/sync_readme.py`가 정한다.
"""

from __future__ import annotations

import datetime
import hashlib
import json
import shutil
import subprocess
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
    """Write one step's verdict with its criteria, reverse proof, ledger data, code hashes and commit."""
    if premise not in PREMISES:
        raise ValueError(f"unknown premise: {premise}")
    commit = sealed(step)
    for row in data:
        if not path(row).is_file() or path(row).stat().st_size != row["bytes"]:
            raise ValueError(f"{row['asset']} is missing or differs from its ledger record")
    judged = verdict(list(checks.values()) + ([proof] if proof else []), data)
    run_at = now()
    result = {
        "step": step, "premise": premise, "premise_text": PREMISES[premise], "claim": claim,
        "reference": reference, "checks": checks, "reverse_proof": proof,
        "verdict": judged, "axiom_adopted": judged == "지지됨", "measured": measured,
        "data": [{k: row[k] for k in ("dataset", "version", "asset", "sha256")} for row in data],
        "code_sha256": {p.relative_to(HERE).as_posix(): sha256(p) for p in code()},
        "git": commit, "date": run_at.astimezone().date().isoformat(),
        "run_at": run_at.isoformat(timespec="seconds"), "run": f"{step}/{run_at:%Y%m%dT%H%M%SZ}.json",
    }
    save(step, result)
    return result


def now():
    return datetime.datetime.now(datetime.timezone.utc)


def git(*args):
    return subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, text=True,
                          encoding="utf-8", check=True).stdout.strip()


def sealed(step):
    """The step file's last commit; refuse unless it and the research code it loaded are committed as they are."""
    file = (HERE / f"{step}.py").relative_to(ROOT).as_posix()
    loaded = {p.relative_to(ROOT).as_posix() for p in code()}
    changed = git("status", "--porcelain", "--", file, *loaded)
    last = git("log", "-1", "--format=%H %cI", "--", file).split()
    if changed or not last or not (ROOT / file).is_file():
        raise RuntimeError(f"commit {file} and the code it loads before recording: {changed or file}")
    return {"step_commit": last[0], "step_committed_at": last[1], "head": git("rev-parse", "HEAD")}


def save(step, result):
    """Add the run under results/<step>/ and make results/<step>.json that latest run. Nothing is overwritten."""
    runs, latest = RESULTS / step, RESULTS / f"{step}.json"
    runs.mkdir(parents=True, exist_ok=True)
    if latest.is_file() and not any(runs.iterdir()):  # 누적 전 결과도 남긴다
        date = json.loads(latest.read_text(encoding="utf-8"))["date"].replace("-", "")
        shutil.copy2(latest, runs / f"{date}-legacy.json")
    text = json.dumps(result, ensure_ascii=False, indent=1)
    with open(RESULTS / result["run"], "x", encoding="utf-8") as stream:
        stream.write(text)
    latest.write_text(text, encoding="utf-8")


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
