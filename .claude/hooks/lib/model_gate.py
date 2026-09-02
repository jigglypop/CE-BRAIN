"""UserPromptSubmit 위임 지시. 결정적 코드, LLM 없음. 프롬프트를 막지 않는다(항상 exit 0).

왜: 사용자는 메인 세션을 Fable로 둔다. 그런데 생물학 내용을 Fable이 직접 읽으면 제공자
안전장치 오탐으로 턴이 죽어 왔다. 해법은 모델 전환이 아니라 **위임**이다. 메인은
오케스트레이터로만 움직이고, 생물 자료·문헌·카드 본문은 생물 전담 opus 에이전트가 읽는다.
이 훅은 생물 프롬프트가 들어올 때 그 지시를 메인 문맥의 맨 앞에 넣는다.

판정
1. 프롬프트에 생물 표지(`safety_screen.BIO_MARKERS`, 정본 하나)가 없으면 아무것도 안 한다.
2. 있고 현재 메인 모델이 opus면 아무것도 안 한다(직접 읽어도 죽지 않는다).
3. 있고 opus가 아니거나 모델을 알 수 없으면 stdout으로 위임 지시를 문맥에 넣는다.
   차단은 하지 않는다. 사용자가 메인 모델을 고르는 권한을 훅이 빼앗지 않기 위해서다.

현재 모델은 `transcript_path`(JSONL)의 마지막 assistant 항목 `message.model`에서 읽는다.
파일이 크므로 꼬리 256KB만 본다.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from safety_screen import BIO_MARKERS  # noqa: E402  표지 정본은 하나

TAIL_BYTES = 256 * 1024
OPUS_TOKEN = "opus"

DELEGATE_TEMPLATE = (
    "[model-gate] 이 프롬프트는 생물학 도메인이다(일치: {hit!r}). 현재 메인 모델은 {model}이고 "
    "opus가 아니다.\n"
    "메인은 오케스트레이터로만 움직여라. 생물 자료·문헌·카드 본문을 메인 문맥으로 끌어오지 말고, "
    "0단계 domain-classifier로 `verify/_routing/<session_id>.json` 영수증을 남긴 뒤 "
    "생물 전담(prover-bio·adversary-bio·judge-bio·sourcer-bio·paper-writer-bio·bio-reader, 전부 opus)에 "
    "위임한다. 서브에이전트에는 파일 경로만 넘기고 돌려받는 것은 마지막 fenced json 하나다. "
    "생물 원문을 직접 읽어야 하면 bio-reader에 시켜라."
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


def current_model(transcript_path: str) -> str | None:
    """마지막 assistant 항목의 model. 없으면 None."""
    if not transcript_path:
        return None
    for line in reversed(read_tail(transcript_path)):
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        message = row.get("message")
        if isinstance(message, dict) and message.get("role") == "assistant":
            model = message.get("model")
            if model:
                return str(model)
    return None


def decide(prompt: str, transcript_path: str) -> tuple[int, str, str]:
    """(exit code, stderr 메시지, stdout 문맥)."""
    found = BIO_MARKERS.search(prompt or "")
    if not found:
        return 0, "", ""
    hit = found.group(0)[:40]
    model = current_model(transcript_path)
    if model is not None and OPUS_TOKEN in model.lower():
        return 0, "", ""
    return 0, "", DELEGATE_TEMPLATE.format(model=model or "미상", hit=hit)


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
    code, message, context = decide(
        str(payload.get("prompt", "")), str(payload.get("transcript_path", ""))
    )
    if context:
        print(context)
    if message:
        print(message, file=sys.stderr)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
