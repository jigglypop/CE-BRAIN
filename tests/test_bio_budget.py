"""`.claude/hooks/lib/bio_budget.py` Stop 훅 계약.

메인이 쓴 마지막 답변의 도메인 용어 예산을 강제한다. 넘치면 턴 종료를 막고 환원을 요구한다.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / ".claude" / "hooks" / "lib" / "bio_budget.py"


def _load():
    spec = importlib.util.spec_from_file_location("bio_budget", HOOK)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


budget = _load()


def transcript(tmp_path: Path, text: str, name: str = "t.jsonl") -> str:
    path = tmp_path / name
    rows = [
        {"message": {"role": "user", "content": "x"}},
        {"message": {"role": "assistant", "content": [{"type": "text", "text": text}]}},
    ]
    path.write_text("\n".join(json.dumps(r) for r in rows), encoding="utf-8")
    return str(path)


NEUTRAL = (
    "판정이 왔습니다. 구조 입력으로는 쓸 수 있고 계량 endpoint로는 부적격입니다. "
    "전체 보고는 verify/Q-NPF-04 아래 파일에 있습니다. 적격성 0/4, 표본 상한 85MB입니다. "
    "다음은 별도 질문 등록입니다."
)

HEAVY = (
    "해마 뉴런의 시냅스 가소성을 보면 수상돌기 spine 이 축삭 axon 과 만나고, "
    "이광자 칼슘 영상에서 dendrite 와 cortex, hippocampus 의 mouse 자료를 "
    "Ottenheimer 2023 과 DANDI 에서 확인했습니다. Neuropixels 기록도 있습니다."
)


def test_neutral_reply_passes(tmp_path):
    assert budget.decide(transcript(tmp_path, NEUTRAL)) == (0, "")


def test_marker_heavy_reply_blocks(tmp_path):
    code, message = budget.decide(transcript(tmp_path, HEAVY))
    assert code == 2
    assert "bio-budget" in message and "환원" in message


def test_counts_distinct_and_total():
    distinct, total, kinds = budget.count_markers("뉴런 뉴런 시냅스 axon")
    assert total == 4
    assert distinct == 3
    assert kinds[0] == "뉴런"


def test_budget_boundary_passes(tmp_path):
    text = " ".join(["뉴런"] * budget.TOTAL_BUDGET)
    code, _ = budget.decide(transcript(tmp_path, text))
    assert code == 0
    over = " ".join(["뉴런"] * (budget.TOTAL_BUDGET + 1))
    assert budget.decide(transcript(tmp_path, over, "u.jsonl"))[0] == 2


def test_distinct_budget_triggers_even_when_total_small(tmp_path):
    kinds = ["뉴런", "시냅스", "축삭", "해마", "피질", "spine", "axon"]
    assert len(kinds) > budget.DISTINCT_BUDGET
    assert budget.decide(transcript(tmp_path, " ".join(kinds)))[0] == 2


def test_missing_transcript_fails_open(tmp_path):
    assert budget.decide(str(tmp_path / "missing.jsonl")) == (0, "")
    assert budget.decide("") == (0, "")


def test_plain_string_content_is_read(tmp_path):
    path = tmp_path / "s.jsonl"
    path.write_text(
        json.dumps({"message": {"role": "assistant", "content": HEAVY}}), encoding="utf-8"
    )
    assert budget.decide(str(path))[0] == 2


def test_only_last_assistant_counts(tmp_path):
    path = tmp_path / "m.jsonl"
    rows = [
        {"message": {"role": "assistant", "content": [{"type": "text", "text": HEAVY}]}},
        {"message": {"role": "user", "content": "x"}},
        {"message": {"role": "assistant", "content": [{"type": "text", "text": NEUTRAL}]}},
    ]
    path.write_text("\n".join(json.dumps(r) for r in rows), encoding="utf-8")
    assert budget.decide(str(path)) == (0, "")


def test_hook_process_blocks_and_passes(tmp_path):
    for text, expected in ((HEAVY, 2), (NEUTRAL, 0)):
        payload = {
            "hook_event_name": "Stop",
            "transcript_path": transcript(tmp_path, text, f"{expected}.jsonl"),
        }
        proc = subprocess.run(
            [sys.executable, str(HOOK)],
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        assert proc.returncode == expected
        if expected == 2:
            assert "bio-budget" in proc.stderr


def test_non_stop_event_is_ignored(tmp_path):
    payload = {
        "hook_event_name": "SubagentStop",
        "transcript_path": transcript(tmp_path, HEAVY),
    }
    proc = subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert proc.returncode == 0


def test_hook_registered_before_ledger_gate():
    settings = json.loads((ROOT / ".claude" / "settings.json").read_text(encoding="utf-8"))
    commands = [h.get("command", "") for h in settings["hooks"]["Stop"][0]["hooks"]]
    assert "bio-budget" in commands[0]
    assert any("ledger-or-block" in c for c in commands)


def test_bio_cards_require_json_only_final_message():
    for name in (
        "bio-reader",
        "prover-bio",
        "adversary-bio",
        "judge-bio",
        "sourcer-bio",
        "paper-writer-bio",
    ):
        card = (ROOT / ".claude" / "agents" / f"{name}.md").read_text(encoding="utf-8")
        assert "마지막 메시지는 그 json 하나뿐이다" in card
