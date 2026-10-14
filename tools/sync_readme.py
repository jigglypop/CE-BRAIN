"""README와 상태 원장(ledger/STATE.md)의 공리 상태 표를 단계 결과(research/results/<단계>.json)에서 만든다.

전제 상태는 세 단계다(2026-10-08부터, 옛 규칙은 "지지됨 하나면 채택"이라 실패가 상태에 아무 영향이 없었다):
- 채택: 지지됨이 있고, 실패가 없고, 그 전제에 실행 안 된 재판정 단계 파일이 없다.
- 잠정: 지지됨이 있으나 실패가 있거나 재판정이 실행 전이다.
- 미채택: 지지됨이 없다.
재판정 단계(C3-1r처럼 번호 뒤 r)의 결과가 있으면 원래 단계 대신 그 판정을 센다. 전제가 없는 하네스 이전 결과는 넣지 않는다.

    python -m tools.sync_readme          README와 STATE.md를 고친다
    python -m tools.sync_readme --check  둘 중 하나라도 결과와 다르면 1로 끝난다
"""

from __future__ import annotations

import json
import re
import sys

from research.harness import HERE, PREMISES, RESULTS, ROOT

README = ROOT / "README.md"
STATE = ROOT / "ledger/STATE.md"
BEGIN = "<!-- 공리 상태: python -m tools.sync_readme 가 research/results에서 만든다 -->"
END = "<!-- /공리 상태 -->"
VERDICTS = ("지지됨", "실패", "미확립")
STATES = {"채택": "**채택**", "잠정": "**잠정**", "미채택": "미채택"}


def results():
    """Latest result of every harness step, in step order."""
    rows = [json.loads(p.read_text(encoding="utf-8")) for p in RESULTS.glob("*.json")]
    return sorted((r for r in rows if r.get("premise") in PREMISES), key=lambda r: order(r["step"]))


def order(step):
    premise, number = step.split("_")[:2]
    digits = number.rstrip("r")
    return premise, int(digits), number[len(digits):]


def label(step):
    """c1_10_split_half → C1-10, c3_1r_sleep_trace → C3-1r."""
    premise, number, again = order(step)
    return f"{premise.upper()}-{number}{again}"


def pending(rows):
    """Labels of re-judgement step files (research/c<n>_<m>r_*.py) that have no result yet."""
    done = {label(r["step"]) for r in rows}
    files = (label(p.stem) for p in HERE.glob("c*_*r_*.py") if p.stem.split("_")[1].endswith("r"))
    return sorted((f for f in files if f not in done), key=lambda name: order(name.lower().replace("-", "_")))


def status(rows, waiting=()):
    """{premise: {"state": 채택|잠정|미채택, "adopted": bool, "pending": [labels], verdict: [labels]}}.

    A re-judged step is shown as 'C3-1(→C3-1r)' and not counted. `waiting` names re-judgements not yet run."""
    labels = {label(r["step"]) for r in rows}
    table = {p: {"state": "미채택", "adopted": False, "pending": [], **{v: [] for v in VERDICTS}} for p in PREMISES}
    counted = {p: {v: 0 for v in VERDICTS} for p in PREMISES}
    for r in rows:
        name = label(r["step"])
        superseded = f"{name}r" in labels
        table[r["premise"]][r["verdict"]].append(f"{name}(→{name}r)" if superseded else name)
        counted[r["premise"]][r["verdict"]] += not superseded
    for name in waiting:
        table[name.split("-")[0]]["pending"].append(name)
    for p, s in table.items():
        if counted[p]["지지됨"]:
            s["state"] = "채택" if not counted[p]["실패"] and not s["pending"] else "잠정"
        s["adopted"] = s["state"] == "채택"
    return table


def block(rows, waiting=()):
    dates = [r.get("date") or r["run_at"][:10] for r in rows]
    lines = [BEGIN, "",
             f"단계 결과 {len(rows)}개, 최근 판정 {max(dates)}. 채택은 지지됨이 있고 실패가 없고 재판정이 남지 않은 전제, "
             "잠정은 지지됨이 있으나 실패가 있거나 재판정이 실행 전인 전제다. 재판정(r)의 결과가 있으면 원래 단계 대신 그 판정을 센다. "
             "전제가 없는 하네스 이전 결과(01·02·02b)는 넣지 않는다.", "",
             "| 전제 | 상태 | 지지됨 | 실패 | 미확립 | 재판정 대기 |", "|---|---|---|---|---|---|"]
    for premise, s in status(rows, waiting).items():
        cells = [", ".join(s[v]) or "—" for v in VERDICTS] + [", ".join(s["pending"]) or "—"]
        lines.append(f"| {premise} {PREMISES[premise]} | {STATES[s['state']]} | " + " | ".join(cells) + " |")
    return "\n".join(lines + ["", END])


def render(text, rows, waiting=()):
    """Text with the generated block replaced."""
    pattern = re.compile(re.escape(BEGIN) + ".*?" + re.escape(END), re.S)
    if not pattern.search(text):
        raise ValueError("no generated axiom block")
    return pattern.sub(lambda _: block(rows, waiting), text)


def main(argv):
    rows = results()
    waiting = pending(rows)
    stale = 0
    for file in (README, STATE):
        text = file.read_text(encoding="utf-8")
        synced = render(text, rows, waiting)
        stale |= synced != text
        if "--check" not in argv:
            file.write_text(synced, encoding="utf-8")
    return int(stale) if "--check" in argv else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
