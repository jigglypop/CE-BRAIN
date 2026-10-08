import re

from research.harness import PREMISES, ROOT
from tools import sync_readme

PAPER = ROOT / "paper/CE-BRAIN.md"


def paper_table():
    """Status cell of every premise row in chapter 1 of the paper."""
    section = PAPER.read_text(encoding="utf-8").split("\n## 1.", 1)[1].split("\n## ", 1)[0]
    rows = [[c.strip() for c in line.strip().strip("|").split("|")] for line in section.splitlines()]
    return {cells[0]: cells[2] for cells in rows if re.fullmatch(r"C\d", cells[0])}


def state(cell):
    """'**채택** …' → 채택, '**잠정** …' → 잠정, otherwise 미채택."""
    found = re.match(r"\*\*(채택|잠정)\*\*", cell)
    return found.group(1) if found else "미채택"


def cited(cell):
    """Steps a status cell names with a verdict: '**잠정** (C1-4, C1-6)' → 지지됨, 'C1-1·2·3 실패' → 실패."""
    named = {}
    adopted = re.match(r"\*\*(?:채택|잠정)\*\*[^(]*\(([^)]*)\)", cell)
    for premise, number in re.findall(r"(C\d)-(\d+r?)", adopted.group(1) if adopted else ""):
        named[f"{premise}-{number}"] = "지지됨"
    for premise, numbers, verdict in re.findall(r"(C\d)-(\d+r?(?:·\d+r?)*) ?(실패|미확립)", cell):
        named.update({f"{premise}-{n}": verdict for n in numbers.split("·")})
    return named


def test_readme_and_state_tables_are_generated_from_results():
    rows = sync_readme.results()
    for file in (sync_readme.README, sync_readme.STATE):
        text = file.read_text(encoding="utf-8")
        assert sync_readme.render(text, rows, sync_readme.pending(rows)) == text, "python -m tools.sync_readme"


def test_paper_table_agrees_with_results():
    rows = sync_readme.results()
    status = sync_readme.status(rows, sync_readme.pending(rows))
    verdicts = {sync_readme.label(r["step"]): r["verdict"] for r in rows}
    paper = paper_table()
    assert sorted(paper) == sorted(PREMISES)
    wrong = [(p, status[p]["state"]) for p, cell in paper.items() if state(cell) != status[p]["state"]]
    wrong += [(step, verdicts.get(step)) for cell in paper.values()
              for step, verdict in cited(cell).items() if verdicts.get(step) != verdict]
    assert wrong == []


def test_adoption_needs_a_supported_step():
    rows = [{"step": "c4_1_x", "premise": "C4", "verdict": "실패", "date": "2026-01-01"},
            {"step": "c5_2_x", "premise": "C5", "verdict": "미확립", "date": "2026-01-02"},
            {"step": "c5_10_x", "premise": "C5", "verdict": "지지됨", "date": "2026-01-03"}]
    status = sync_readme.status(rows)
    assert not status["C4"]["adopted"] and status["C5"]["adopted"] and status["C5"]["state"] == "채택"
    assert status["C5"]["미확립"] == ["C5-2"] and status["C5"]["지지됨"] == ["C5-10"]
    text = sync_readme.render(f"머리\n{sync_readme.BEGIN}\n옛 표\n{sync_readme.END}\n꼬리", rows)
    assert "옛 표" not in text and "| C5 " in text and "최근 판정 2026-01-03" in text and text.endswith("꼬리")


def test_a_rejudged_step_replaces_the_original_for_adoption():
    rows = [{"step": "c3_1_x", "premise": "C3", "verdict": "지지됨", "date": "2026-01-01"},
            {"step": "c3_1r_x", "premise": "C3", "verdict": "실패", "date": "2026-01-02"},
            {"step": "c3_2_x", "premise": "C3", "verdict": "실패", "date": "2026-01-01"}]
    status = sync_readme.status(sorted(rows, key=lambda r: sync_readme.order(r["step"])))
    assert not status["C3"]["adopted"]
    assert status["C3"]["지지됨"] == ["C3-1(→C3-1r)"] and status["C3"]["실패"] == ["C3-1r", "C3-2"]
    assert sync_readme.status(rows[:1] + rows[2:])["C3"]["state"] == "잠정"
    assert sync_readme.status(rows[:1])["C3"]["adopted"]


def test_a_failure_or_a_waiting_rejudgement_makes_adoption_provisional():
    rows = [{"step": "c1_1_x", "premise": "C1", "verdict": "실패", "date": "2026-01-01"},
            {"step": "c1_2_x", "premise": "C1", "verdict": "지지됨", "date": "2026-01-02"},
            {"step": "c2_1_x", "premise": "C2", "verdict": "지지됨", "date": "2026-01-02"},
            {"step": "c6_1_x", "premise": "C6", "verdict": "지지됨", "date": "2026-01-02"}]
    status = sync_readme.status(rows, ["C2-1r"])
    assert status["C1"]["state"] == "잠정" and not status["C1"]["adopted"]
    assert status["C2"]["state"] == "잠정" and status["C2"]["pending"] == ["C2-1r"]
    assert status["C6"]["state"] == "채택" and status["C6"]["adopted"]
    assert "**잠정**" in sync_readme.block(rows, ["C2-1r"]) and "| C2-1r |" in sync_readme.block(rows, ["C2-1r"])


def test_waiting_rejudgements_are_found_from_step_files():
    rows = sync_readme.results()
    waiting = sync_readme.pending(rows)
    done = {sync_readme.label(r["step"]) for r in rows}
    assert all(name.endswith("r") and name not in done for name in waiting)


def test_paper_table_names_every_step():
    """Chapter 1 of the paper mentions every step of its premise, failures included (D19)."""
    rows = sync_readme.results()
    paper = paper_table()
    unnamed = []
    for premise, cell in paper.items():
        named = {f"{p}-{n}" for p, numbers in re.findall(r"(C\d)-(\d+r?(?:·\d+r?)*)", cell) for n in numbers.split("·")}
        unnamed += [label for r in rows if r["premise"] == premise
                    and (label := sync_readme.label(r["step"])) not in named]
    assert unnamed == []
