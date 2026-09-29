import re

from research.harness import PREMISES, ROOT
from tools import sync_readme

PAPER = ROOT / "paper/CE-BRAIN.md"


def paper_table():
    """Status cell of every premise row in chapter 1 of the paper."""
    section = PAPER.read_text(encoding="utf-8").split("\n## 1.", 1)[1].split("\n## ", 1)[0]
    rows = [[c.strip() for c in line.strip().strip("|").split("|")] for line in section.splitlines()]
    return {cells[0]: cells[2] for cells in rows if re.fullmatch(r"C\d", cells[0])}


def cited(cell):
    """Steps a status cell names with a verdict: '**채택** (C1-4, C1-6)' → 지지됨, 'C1-1·2·3 실패' → 실패."""
    named = {}
    adopted = re.match(r"\*\*채택\*\*[^(]*\(([^)]*)\)", cell)
    for premise, number in re.findall(r"(C\d)-(\d+)", adopted.group(1) if adopted else ""):
        named[f"{premise}-{number}"] = "지지됨"
    for premise, numbers, verdict in re.findall(r"(C\d)-(\d+(?:·\d+)*) ?(실패|미확립)", cell):
        named.update({f"{premise}-{n}": verdict for n in numbers.split("·")})
    return named


def test_readme_table_is_generated_from_results():
    text = sync_readme.README.read_text(encoding="utf-8")
    assert sync_readme.render(text, sync_readme.results()) == text, "python -m tools.sync_readme"


def test_paper_table_agrees_with_results():
    rows = sync_readme.results()
    status = sync_readme.status(rows)
    verdicts = {sync_readme.label(r["step"]): r["verdict"] for r in rows}
    paper = paper_table()
    assert sorted(paper) == sorted(PREMISES)
    wrong = [(p, "채택" if status[p]["adopted"] else "미채택") for p, cell in paper.items()
             if cell.startswith("**채택**") != status[p]["adopted"]]
    wrong += [(step, verdicts.get(step)) for cell in paper.values()
              for step, verdict in cited(cell).items() if verdicts.get(step) != verdict]
    assert wrong == []


def test_adoption_needs_a_supported_step():
    rows = [{"step": "c4_1_x", "premise": "C4", "verdict": "실패", "date": "2026-01-01"},
            {"step": "c5_2_x", "premise": "C5", "verdict": "미확립", "date": "2026-01-02"},
            {"step": "c5_10_x", "premise": "C5", "verdict": "지지됨", "date": "2026-01-03"}]
    status = sync_readme.status(rows)
    assert not status["C4"]["adopted"] and status["C5"]["adopted"]
    assert status["C5"]["미확립"] == ["C5-2"] and status["C5"]["지지됨"] == ["C5-10"]
    text = sync_readme.render(f"머리\n{sync_readme.BEGIN}\n옛 표\n{sync_readme.END}\n꼬리", rows)
    assert "옛 표" not in text and "| C5 " in text and "최근 판정 2026-01-03" in text and text.endswith("꼬리")
