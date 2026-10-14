"""재판정 실행기: 원자료가 있는 컴퓨터에서 명령 하나로 대기 중인 재판정을 돌리고 상태 표를 다시 만든다.

    python -m tools.rejudge             점검 → 재판정 → 상태 표(README·STATE.md) 갱신 → 요약
    python -m tools.rejudge --check     자료와 커밋 상태만 점검하고 아무것도 실행하지 않는다
    python -m tools.rejudge --fetch     원장에 없거나 디스크에 없는 자료를 research.fetch로 먼저 가져온다(DANDI 접속 필요)
    python -m tools.rejudge --commit    끝나면 결과·README·STATE.md를 한 커밋으로 남긴다(push는 하지 않는다)
    python -m tools.rejudge c3_1r_sleep_trace ...   고른 단계만

대기 단계는 `tools.sync_readme.pending`이 정한다(결과 없는 c<n>_<m>r_*.py). 단계마다 `harness.record`가 봉인(단계 파일과 읽은
연구 코드가 커밋된 그대로인지)을 확인하므로, 작업 트리에 고친 연구 코드가 있으면 시작하지 않는다.
"""

from __future__ import annotations

import json
import subprocess
import sys
import time

from research import harness
from tools import sync_readme

NEEDS = {  # 단계 → 읽는 원장 자료(단계 파일 main에서 읽는 것과 같다). 적은 순서가 실행 순서다
    "c3_1r_sleep_trace": ("dandi-000939-extract",),
    "c1_4r_common_trace_time": ("dandi-000056", "dandi-000939-extract", "dandi-001699"),
    "c1_6r_common_equation_precise": ("dandi-000056", "dandi-000939-extract", "dandi-001699"),
    "c1_8r_joint_v3": ("dandi-000056", "dandi-000939-extract", "dandi-001699"),
}
FETCHABLE = {"dandi-000056", "dandi-000044", "dandi-001699"}  # research.fetch.SOURCES


def waiting():
    """Step module names of re-judgements with no result yet, in step order."""
    labels = set(sync_readme.pending(sync_readme.results()))
    steps = [p.stem for p in harness.HERE.glob("c*_*r_*.py") if sync_readme.label(p.stem) in labels]
    known = list(NEEDS)  # 가벼운 것부터: C3-1r이 C3 상태를 가장 크게 바꾸고 가장 빠르다
    return sorted(steps, key=lambda s: (known.index(s) if s in known else len(known), sync_readme.order(s)))


def missing(dataset):
    """Ledger rows of a dataset whose file is absent or has the wrong size (sha256 is checked by the step itself)."""
    try:
        rows = harness.registered(dataset)
    except LookupError:
        return None
    rows = [r for r in rows if r.get("status") == "verified_file"]
    return [r["path"] for r in rows if not harness.path(r).is_file() or harness.path(r).stat().st_size != r["bytes"]]


def dirty():
    """Uncommitted changes under research/ (sealing would refuse them)."""
    return harness.git("status", "--porcelain", "--", "research").splitlines()


def check(steps):
    problems, datasets = [], sorted({d for s in steps for d in NEEDS.get(s, ())})
    for s in steps:
        if s not in NEEDS:
            problems.append(f"{s}: 읽는 자료를 NEEDS에 적지 않았다")
    for d in datasets:
        gone = missing(d)
        if gone is None:
            problems.append(f"{d}: 원장에 없다" + (" (--fetch로 가져올 수 있다)" if d in FETCHABLE else ""))
        elif gone:
            problems.append(f"{d}: 파일 {len(gone)}개가 없거나 크기가 다르다, 예 {gone[0]}"
                            + (" (--fetch)" if d in FETCHABLE else " (이 자료는 fetch 항목이 없다: 원래 컴퓨터의 data/에서 복사)"))
        else:
            print(f"자료 {d}: 원장 {len(harness.registered(d))}줄, 디스크 일치", flush=True)
    if dirty():
        problems.append("research/에 커밋 안 된 변경이 있다: " + "; ".join(dirty()[:3]))
    return problems


def run(step):
    start = time.time()
    done = subprocess.run([sys.executable, "-m", f"research.{step}"], cwd=harness.ROOT)
    latest = harness.RESULTS / f"{step}.json"
    if done.returncode or not latest.is_file():
        return {"step": step, "verdict": "실행 실패", "seconds": round(time.time() - start)}
    result = json.loads(latest.read_text(encoding="utf-8"))
    return {"step": step, "verdict": result["verdict"], "seconds": round(time.time() - start),
            "failed_checks": [k for k, v in result["checks"].items() if v.get("passed") is False]}


def main(argv):
    steps = [a for a in argv if not a.startswith("--")] or waiting()
    if not steps:
        print("대기 중인 재판정이 없다")
        return 0
    print("대기 재판정:", ", ".join(sync_readme.label(s) for s in steps), flush=True)
    if "--fetch" in argv:
        from research import fetch
        for d in sorted({d for s in steps for d in NEEDS.get(s, ())} & FETCHABLE):
            if missing(d) != []:
                print(f"가져오기 {d}", flush=True)
                fetch.fetch(d)
    problems = check(steps)
    if problems:
        print("시작하지 않는다:\n  " + "\n  ".join(problems))
        return 2
    if "--check" in argv:
        print("점검 통과")
        return 0
    summary = [run(s) for s in steps]
    sync_readme.main([])
    print("\n| 단계 | 판정 | 실패한 기준 | 초 |\n|---|---|---|---|")
    for r in summary:
        print(f"| {sync_readme.label(r['step'])} | {r['verdict']} | {', '.join(r.get('failed_checks', [])) or '—'} | {r['seconds']} |")
    table = sync_readme.status(sync_readme.results(), sync_readme.pending(sync_readme.results()))
    print("\n상태: " + ", ".join(f"{p} {s['state']}" for p, s in table.items()))
    if "--commit" in argv:
        files = ["README.md", "ledger/STATE.md", "research/results"]
        harness.git("add", *files)
        verdicts = ", ".join(f"{sync_readme.label(r['step'])} {r['verdict']}" for r in summary)
        harness.git("commit", "-m", f"재판정 실행: {verdicts}")
        print("커밋했다(push는 직접):", harness.git("log", "-1", "--format=%h %s"))
    return int(any(r["verdict"] == "실행 실패" for r in summary))


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
