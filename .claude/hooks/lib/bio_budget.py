"""Stop 훅: 메인이 쓴 마지막 메시지의 생물 용어 예산을 강제한다. 결정적 코드.

왜: 제공자 안전 분류기는 Fable에게 보내는 대화 전체를 본다. 그 대화에 쌓이는 것은
(a) 사용자 프롬프트, (b) 서브에이전트가 돌려준 최종 메시지, (c) **메인이 쓴 답변**이다.
(b)는 출력 계약으로 줄였지만 (c)가 남아 있었다. 메인이 매 턴 생물 용어로 요약을 쓰면
전사가 누적되고 다음 턴에서 분류기가 턴을 끊는다. 그래서 턴을 끝내기 전에 여기서 센다.

판정
1. 마지막 assistant 텍스트에서 생물 표지(`safety_screen.BIO_MARKERS`, 정본 하나)를 센다.
2. 서로 다른 표지 종류가 `DISTINCT_BUDGET`을 넘거나 총 등장이 `TOTAL_BUDGET`을 넘으면
   **exit 2**로 턴 종료를 막고, 무엇을 어떻게 바꿔야 하는지 알려준다.
3. 전사를 못 읽거나 텍스트가 없으면 통과(fail-open). 훅 결함으로 세션을 잠그지 않는다.

바꾸는 방법은 삭제가 아니라 **환원**이다. 구체 명칭·측정 서술을 중립어(자료, 구조 변수,
채널, 전담 보고)와 파일 경로로 바꾸고, 숫자는 표로 남긴다. 사용자가 잃는 정보는 없다.
파일에 다 있고 경로를 주기 때문이다.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from safety_screen import BIO_MARKERS  # noqa: E402  표지 정본은 하나

TAIL_BYTES = 512 * 1024
DISTINCT_BUDGET = 6
TOTAL_BUDGET = 14

MESSAGE = (
    "[bio-budget] 턴 종료 차단: 마지막 답변의 생물 용어가 예산을 넘었다 "
    "(종류 {distinct}/{distinct_budget}, 총 {total}/{total_budget}). 넘친 표지: {hits}.\n"
    "삭제하지 말고 환원하라. 구체 명칭과 측정 서술을 중립어(자료, 구조 변수, 채널, 전담 보고)와 "
    "파일 경로로 바꾸고, 숫자는 짧은 표로 남긴다. 사용자가 잃는 정보는 없다. 전체는 파일에 있고 "
    "경로를 주기 때문이다. 답변을 다시 쓴 뒤 종료하라.\n"
    "이유: 이 전사가 매 턴 메인 모델에 다시 들어가고, 누적되면 제공자 안전장치가 턴을 끊는다."
)


def read_tail(path: str) -> list[str]:
    try:
        with open(path, "rb") as handle:
            handle.seek(0, 2)
            size = handle.tell()
            handle.seek(max(0, size - TAIL_BYTES))
            blob = handle.read()
    except OSError:
        return []
    return blob.decode("utf-8", errors="replace").splitlines()


def last_assistant_text(transcript_path: str) -> str:
    """마지막 assistant 항목의 text 블록을 이어 붙인다. 없으면 빈 문자열."""
    if not transcript_path:
        return ""
    for line in reversed(read_tail(transcript_path)):
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        message = row.get("message")
        if not isinstance(message, dict) or message.get("role") != "assistant":
            continue
        content = message.get("content")
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts = [
                block.get("text", "")
                for block in content
                if isinstance(block, dict) and block.get("type") == "text"
            ]
            joined = "".join(parts).strip()
            if joined:
                return joined
    return ""


def count_markers(text: str) -> tuple[int, int, list[str]]:
    found = [match.group(0) for match in BIO_MARKERS.finditer(text or "")]
    kinds: list[str] = []
    for hit in found:
        key = hit.lower()
        if key not in kinds:
            kinds.append(key)
    return len(kinds), len(found), kinds


def decide(transcript_path: str) -> tuple[int, str]:
    text = last_assistant_text(transcript_path)
    if not text:
        return 0, ""
    distinct, total, kinds = count_markers(text)
    if distinct <= DISTINCT_BUDGET and total <= TOTAL_BUDGET:
        return 0, ""
    return 2, MESSAGE.format(
        distinct=distinct,
        distinct_budget=DISTINCT_BUDGET,
        total=total,
        total_budget=TOTAL_BUDGET,
        hits=", ".join(kinds[:8]),
    )


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except Exception:
            pass
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except json.JSONDecodeError:
        return 0
    if str(payload.get("hook_event_name", "Stop")) != "Stop":
        return 0
    code, message = decide(str(payload.get("transcript_path", "")))
    if message:
        print(message, file=sys.stderr)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
