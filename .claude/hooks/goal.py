"""UserPromptSubmit hook: 요청마다 전제 정렬 규칙과 prd/의 진행 중인 단계를 짧게 붙인다."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def active_steps(limit=3):
    """First table rows in prd/*.md whose status is 진행 or 다음, as 'label (status)'."""
    steps = []
    for plan in sorted((ROOT / "prd").glob("*.md")):
        for line in plan.read_text(encoding="utf-8").splitlines():
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if line.startswith("|") and len(cells) > 2 and cells[-1].startswith(("진행", "다음")):
                steps.append(f"{cells[0]} {cells[1][:40]} ({cells[-1][:20]})")
    return steps[:limit]


def main():
    lines = ["[하네스] 이 요청이 판정하는 핵심 전제(C1–C8)를 먼저 밝힌다. 어느 전제와도 닿지 않으면 멈추고 묻는다."]
    steps = active_steps()
    lines.append("[진행] " + " / ".join(steps) if steps else "[계획 없음] 작업 전에 prd/에 계획을 적는다.")
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "UserPromptSubmit",
                                             "additionalContext": "\n".join(lines)}}))


if __name__ == "__main__":
    main()
