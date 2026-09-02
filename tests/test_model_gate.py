"""`.claude/hooks/lib/model_gate.py` UserPromptSubmit 위임 지시 계약.

메인 세션은 사용자가 정한 모델(보통 Fable)로 둔다. 생물학 프롬프트가 오면 막는 대신
"메인은 위임만 하라"는 지시를 문맥에 넣는다. 항상 exit 0.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / ".claude" / "hooks" / "lib" / "model_gate.py"


def _load():
    spec = importlib.util.spec_from_file_location("model_gate", HOOK)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


gate = _load()

BIO = ["해마 CA1 자료를 보자", "spine turnover 를 확인", "Ottenheimer 2023 재분석", "시냅스 가소성 카드"]
NONBIO = ["sympy 로 항등식 검증", "ledger.py card-check 실행", "훅 테스트 추가"]


def transcript(tmp_path: Path, model: str) -> str:
    path = tmp_path / "t.jsonl"
    rows = [
        {"message": {"role": "user", "content": "x"}},
        {"message": {"role": "assistant", "model": model, "content": "y"}},
    ]
    path.write_text("\n".join(json.dumps(r) for r in rows), encoding="utf-8")
    return str(path)


@pytest.mark.parametrize("prompt", BIO)
def test_bio_prompt_on_non_opus_injects_delegation_without_blocking(prompt, tmp_path):
    code, message, context = gate.decide(prompt, transcript(tmp_path, "claude-fable-5-1"))
    assert code == 0
    assert message == ""
    assert "위임" in context and "bio-reader" in context and "claude-fable-5-1" in context


@pytest.mark.parametrize("prompt", BIO)
def test_bio_prompt_on_opus_is_silent(prompt, tmp_path):
    assert gate.decide(prompt, transcript(tmp_path, "claude-opus-5")) == (0, "", "")


@pytest.mark.parametrize("prompt", NONBIO)
def test_non_bio_prompt_is_silent(prompt, tmp_path):
    assert gate.decide(prompt, transcript(tmp_path, "claude-fable-5-1")) == (0, "", "")


def test_unknown_model_injects_delegation(tmp_path):
    code, message, context = gate.decide(BIO[0], str(tmp_path / "missing.jsonl"))
    assert code == 0 and message == ""
    assert "위임" in context and "미상" in context


def test_never_exits_two(tmp_path):
    for model in ("claude-fable-5-1", "claude-sonnet-5", "claude-haiku-4-5", "claude-opus-5"):
        for prompt in BIO + NONBIO:
            assert gate.decide(prompt, transcript(tmp_path, model))[0] == 0


def test_last_assistant_entry_wins(tmp_path):
    path = tmp_path / "t.jsonl"
    rows = [
        {"message": {"role": "assistant", "model": "claude-opus-5"}},
        {"message": {"role": "user", "content": "x"}},
        {"message": {"role": "assistant", "model": "claude-fable-5-1"}},
    ]
    path.write_text("\n".join(json.dumps(r) for r in rows), encoding="utf-8")
    assert gate.current_model(str(path)) == "claude-fable-5-1"


def test_malformed_lines_are_skipped(tmp_path):
    path = tmp_path / "t.jsonl"
    path.write_text(
        "not json\n" + json.dumps({"message": {"role": "assistant", "model": "claude-opus-5"}}) + "\n{",
        encoding="utf-8",
    )
    assert gate.current_model(str(path)) == "claude-opus-5"


def test_hook_process_exit_zero_and_context_on_stdout(tmp_path):
    payload = {"prompt": BIO[0], "transcript_path": transcript(tmp_path, "claude-fable-5-1")}
    proc = subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert proc.returncode == 0
    assert "model-gate" in proc.stdout and "위임" in proc.stdout
    assert proc.stderr.strip() == ""


def test_hook_is_registered_as_first_user_prompt_hook():
    settings = json.loads((ROOT / ".claude" / "settings.json").read_text(encoding="utf-8"))
    hooks = settings["hooks"]["UserPromptSubmit"][0]["hooks"]
    assert "model-gate" in hooks[0].get("command", "")


def test_wrapper_exists():
    assert (ROOT / ".claude" / "hooks" / "model-gate.cmd").is_file()
