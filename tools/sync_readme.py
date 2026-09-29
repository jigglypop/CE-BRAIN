"""README의 공리 상태 표를 단계 결과(research/results/<단계>.json)에서 만든다.

전제는 지지됨 판정이 하나라도 있을 때만 채택이다(하네스 규칙). 재판정 단계(C3-1r처럼 번호 뒤 r)가 있으면 원래 단계 대신
그 판정을 센다. 전제가 없는 하네스 이전 결과는 표에 넣지 않는다.

    python -m tools.sync_readme          README를 고친다
    python -m tools.sync_readme --check  README가 결과와 다르면 1로 끝난다
"""

from __future__ import annotations

import json
import re
import sys

from research.harness import PREMISES, RESULTS, ROOT

README = ROOT / "README.md"
BEGIN = "<!-- 공리 상태: python -m tools.sync_readme 가 research/results에서 만든다 -->"
END = "<!-- /공리 상태 -->"
VERDICTS = ("지지됨", "실패", "미확립")


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


def status(rows):
    """{premise: {"adopted": bool, verdict: [labels]}}. A re-judged step is shown as 'C3-1(→C3-1r)' and not counted."""
    labels = {label(r["step"]) for r in rows}
    table = {p: {"adopted": False, **{v: [] for v in VERDICTS}} for p in PREMISES}
    for r in rows:
        name = label(r["step"])
        superseded = f"{name}r" in labels
        table[r["premise"]][r["verdict"]].append(f"{name}(→{name}r)" if superseded else name)
        table[r["premise"]]["adopted"] |= r["verdict"] == "지지됨" and not superseded
    return table


def block(rows):
    dates = [r.get("date") or r["run_at"][:10] for r in rows]
    lines = [BEGIN, "",
             f"단계 결과 {len(rows)}개, 최근 판정 {max(dates)}. 전제는 원장 실데이터로 낸 지지됨 판정이 있을 때만 채택하고, "
             "재판정(r)이 있으면 원래 단계 대신 그 판정을 센다. 전제가 없는 하네스 이전 결과(01·02·02b)는 넣지 않는다.", "",
             "| 전제 | 상태 | 지지됨 | 실패 | 미확립 |", "|---|---|---|---|---|"]
    for premise, s in status(rows).items():
        cells = [", ".join(s[v]) or "—" for v in VERDICTS]
        state = "**채택**" if s["adopted"] else "미채택"
        lines.append(f"| {premise} {PREMISES[premise]} | {state} | " + " | ".join(cells) + " |")
    return "\n".join(lines + ["", END])


def render(text, rows):
    """README text with the generated block replaced."""
    pattern = re.compile(re.escape(BEGIN) + ".*?" + re.escape(END), re.S)
    if not pattern.search(text):
        raise ValueError("README has no generated axiom block")
    return pattern.sub(lambda _: block(rows), text)


def main(argv):
    text = README.read_text(encoding="utf-8")
    synced = render(text, results())
    if "--check" in argv:
        return int(synced != text)
    README.write_text(synced, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
