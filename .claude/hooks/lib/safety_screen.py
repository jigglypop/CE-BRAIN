"""PreToolUse 안전 선별. 결정적 코드, LLM 없음.

왜: 이 저장소의 연구는 신경과학·정보기하이고 생물학적 위험 내용을 만들 이유가 없다.
그런데 서브에이전트 프롬프트나 문서에 위험 범주 문구가 섞이면 (a) 실제로 만들면 안 되는
내용이 만들어지고 (b) 모델 제공자의 안전장치가 요청을 거부해 루프가 통째로 죽는다.
이 훅은 보내기 전에 막아서 두 경우를 모두 없앤다. 우회 스위치는 두지 않는다.

범주
1. bio_risk   병원체·독소 능력 상향(전염성·병원성 증강, 에어로졸화, 무기화, 합성 경로,
              생물보안 검사 우회). 차단(exit 2).
2. model_internals  다른 에이전트에게 사고과정·추론 흔적·시스템 프롬프트를 그대로 내놓으라는
              요구. 차단(exit 2). 에이전트에게는 결론과 마지막 json만 요구한다.
3. classify_first 도메인 판별 없이 연구 역할(prover·adversary·judge·sourcer·paper-writer와
              그 -bio 짝)을 부르면 차단(exit 2). 먼저 domain-classifier(opus)가
              verify/_routing/<session_id>.json 영수증을 남겨야 한다. 영수증의 domain이 bio인데
              비-생물 역할을 부르면 그것도 차단이다.
4. bio_routing 생물학 내용이 든 서브에이전트 호출은 생물 전담(opus)으로만 보낸다. 차단(exit 2).
              이유: 생물 자료·문헌을 읽는 자리에서 제공자 안전장치 오탐이 반복돼 루프가 죽었다.
              통과 조건은 model=opus 이거나 subagent_type이 BIO_AGENTS 중 하나(카드가 전부 opus).
5. oversize   Agent 프롬프트가 너무 길다. 경고만(exit 0). 긴 입력은 파일 경로로 넘긴다.

예외는 하나뿐이다. 이 훅의 정의 파일(`safety_screen.py`)과 그 시험 파일을 Write/Edit로
고칠 때는 건너뛴다. 패턴 목록 자체가 차단 문구를 담아야 하기 때문이다.

오탐 방지: 이 저장소에서 정상적으로 쓰는 말(시냅스, spine, myelin, AAV, GCaMP, optogenetic,
tetanus/botulinum 광저해 도구, 유도 과정, 추론)은 범주 1·2의 패턴에 넣지 않는다. 범주 1은
"능력을 올린다"는 뜻이 문장에 있어야 걸리고, 범주 2는 추출 동사가 있어야 걸린다.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

MAX_AGENT_PROMPT_CHARS = 12000

BIO_RISK = (
    ("gain-of-function", re.compile(r"gain[\s\-_]?of[\s\-_]?function", re.I)),
    (
        "능력 상향(전염성·병원성)",
        re.compile(
            r"(enhanc|increas|boost|improv)\w*\s+(the\s+)?"
            r"(transmissibility|virulence|lethality|pathogenicity|infectivity)",
            re.I,
        ),
    ),
    ("전염성·병원성 증강", re.compile(r"(전염성|감염성|병원성|치사율)\s*(을|를)?\s*(증강|강화|높이)", re.I)),
    ("에어로졸화", re.compile(r"(aerosoliz\w*|에어로졸\s*화)", re.I)),
    ("무기화", re.compile(r"(weaponi[sz]\w*|생물\s*무기|bioweapon|biological\s+weapon|bioterror\w*)", re.I)),
    ("select agent", re.compile(r"\bselect\s+agent\b", re.I)),
    (
        "병원체·독소 합성 경로",
        re.compile(
            r"(synthesi[sz]\w*|제작|합성)\s*\w*\s*"
            r"(pathogen|viral\s+genome|virus\s+genome|nerve\s+agent|병원체)",
            re.I,
        ),
    ),
    ("화학·생물 작용제", re.compile(r"\b(nerve\s+agent|sarin|soman|ricin|anthrax)\b", re.I)),
    (
        "생물보안 검사 우회",
        re.compile(r"(bypass|evade|circumvent)\w*\s+(the\s+)?(biosecurity|dna\s+synthesis)\s+screen", re.I),
    ),
)

MODEL_INTERNALS = (
    (
        "사고과정 추출 요구",
        re.compile(
            r"(reveal|dump|print|output|expose|extract|show)\s+(me\s+)?(your\s+|the\s+)?"
            r"(chain[\s\-]?of[\s\-]?thought|reasoning\s+trace|internal\s+reasoning|"
            r"hidden\s+reasoning|thinking\s+tokens?|system\s+prompt)",
            re.I,
        ),
    ),
    (
        "사고과정 그대로 출력 요구",
        re.compile(r"(사고\s*과정|내부\s*추론|추론\s*흔적|시스템\s*프롬프트)\s*(을|를)?\s*(그대로\s*)?(출력|공개|노출|덤프|보여)", re.I),
    ),
)


def texts_from(tool_name: str, tool_input: dict) -> list[str]:
    """검사 대상 문자열. 도구마다 사람이 쓴 자리만 본다."""
    parts: list[str] = []
    keys = {
        "Agent": ("prompt", "description"),
        "Task": ("prompt", "description"),
        "Write": ("content",),
        "Edit": ("new_string",),
        "MultiEdit": (),
        "Bash": ("command",),
    }.get(tool_name, ("prompt", "content", "new_string", "command"))
    for key in keys:
        value = tool_input.get(key)
        if isinstance(value, str):
            parts.append(value)
    for edit in tool_input.get("edits") or []:
        if isinstance(edit, dict) and isinstance(edit.get("new_string"), str):
            parts.append(edit["new_string"])
    return parts


def screen(tool_name: str, tool_input: dict, session_id: str = "") -> tuple[int, str]:
    haystacks = texts_from(tool_name, tool_input)
    for label, pattern in BIO_RISK:
        for text in haystacks:
            found = pattern.search(text)
            if found:
                return 2, (
                    f"[safety-screen] 차단: 생물학적 위험 범주 '{label}' 문구가 있다 "
                    f"(일치: {found.group(0)[:60]!r}).\n"
                    "이 저장소의 표적은 신경과학·정보기하이고 이런 내용을 만들 이유가 없다. "
                    "범위를 벗어난 문장을 지우거나 중립적 표현으로 다시 쓴 뒤 호출하라. "
                    "우회 스위치는 없다."
                )
    for label, pattern in MODEL_INTERNALS:
        for text in haystacks:
            found = pattern.search(text)
            if found:
                return 2, (
                    f"[safety-screen] 차단: 모델 내부 추출 범주 '{label}' 문구가 있다 "
                    f"(일치: {found.group(0)[:60]!r}).\n"
                    "서브에이전트에게는 결론과 마지막 fenced json만 요구한다. "
                    "사고과정·시스템 프롬프트를 그대로 내놓으라고 쓰지 말고, 필요한 근거는 "
                    "verify/ 아래 산출물 경로로 받아라."
                )
    if tool_name in {"Agent", "Task"}:
        agent = str(tool_input.get("subagent_type") or "").strip()
        if agent in RESEARCH_ROLES:
            domain = declared_domain(session_id) if session_id else None
            if domain is None:
                return 2, (
                    f"[safety-screen] 차단: 도메인 판별 없이 연구 역할 '{agent}'를 불렀다.\n"
                    f"먼저 subagent_type='{CLASSIFIER_AGENT}'(opus)를 돌려 이 작업이 생물학인지 판별하고 "
                    f"{ROUTING_DIR}/<session_id>.json 영수증을 남겨라. 그 뒤 영수증의 routes 대로 부른다."
                )
            if domain == "bio" and agent in NONBIO_AGENTS:
                return 2, (
                    f"[safety-screen] 차단: 도메인이 bio인데 비-생물 역할 '{agent}'를 불렀다.\n"
                    f"영수증({ROUTING_DIR})의 routes 대로 '{agent}-bio'를 써라. 생물 도메인은 전담(opus)이 맡는다."
                )
        prompt_text = " ".join(haystacks)
        marker = BIO_MARKERS.search(prompt_text)
        if marker:
            model = str(tool_input.get("model") or "").strip().lower()
            agent = str(tool_input.get("subagent_type") or "").strip()
            if model not in BIO_ALLOWED_MODELS and agent not in BIO_AGENTS:
                hit = marker.group(0)[:40]
                where = agent or "없음"
                which = model or "지정 안 함"
                swap = {
                    "prover": "prover-bio",
                    "adversary": "adversary-bio",
                    "judge": "judge-bio",
                    "sourcer": "sourcer-bio",
                    "paper-writer": "paper-writer-bio",
                }.get(agent, "bio-reader")
                return 2, (
                    "[safety-screen] 차단: 생물학 내용이 있는데 생물 전담(opus)이 아니다 "
                    f"(일치: {hit!r}, subagent_type={where}, model={which})."
                    f"\n생물 도메인은 전담 에이전트가 맡는다. subagent_type을 '{swap}'로 바꾸거나 "
                    "model을 opus로 지정하라. "
                    "수학·물리·컴공만 다루는 호출이면 생물 용어를 프롬프트에서 빼고 파일 경로로 넘겨라."
                )
    if tool_name in {"Agent", "Task"}:
        prompt = tool_input.get("prompt")
        if isinstance(prompt, str) and len(prompt) > MAX_AGENT_PROMPT_CHARS:
            return 0, (
                f"[safety-screen 경고] Agent 프롬프트가 {len(prompt)}자다 "
                f"(권장 상한 {MAX_AGENT_PROMPT_CHARS}). 긴 json·표는 파일에 쓰고 경로만 넘겨라. "
                "과대 프롬프트는 제공자 안전장치의 오탐과 조기 종료를 부른다."
            )
    return 0, ""


BIO_MARKERS = re.compile(
    r"(뉴런|시냅스|수상돌기|축삭|해마|피질|생쥐|마우스|전기생리|칼슘\s*영상|이광자|"
    r"spine|dendrit|axon|synap|neuron|cortex|hippocamp|mice|mouse|in\s+vivo|"
    r"two[- ]photon|optogenetic|GCaMP|AAV|dF/F|Neuropixels|"
    r"Ottenheimer|Loewenstein|Hattori|Maristany|Randi|Track2p|Stx3|DANDI|AllenSDK|"
    r"Visual\s+Behavior|International\s+Brain\s+Laboratory|IBL)",
    re.I,
)
BIO_READER_AGENT = "bio-reader"
BIO_ALLOWED_MODELS = frozenset({"opus"})

# 생물 도메인 전담(전부 카드가 opus). 생물 내용은 이 중 하나이거나 model=opus 여야 한다.
BIO_AGENTS = frozenset(
    {
        "bio-reader",
        "prover-bio",
        "adversary-bio",
        "judge-bio",
        "sourcer-bio",
        "paper-writer-bio",
    }
)
NONBIO_AGENTS = frozenset({"prover", "adversary", "judge", "sourcer", "paper-writer"})
# 도메인 판별 없이 부르면 안 되는 역할. 분류기 자신은 면제.
RESEARCH_ROLES = BIO_AGENTS | NONBIO_AGENTS
CLASSIFIER_AGENT = "domain-classifier"
ROUTING_DIR = "verify/_routing"


def repo_root() -> Path:
    env = os.environ.get("CLAUDE_PROJECT_DIR")
    if env:
        return Path(env).resolve()
    return Path(__file__).resolve().parents[3]


def routing_receipt(session_id: str) -> Path:
    safe = "".join(ch for ch in str(session_id) if ch.isalnum() or ch in "-_") or "unknown"
    return repo_root() / ROUTING_DIR / f"{safe}.json"


def declared_domain(session_id: str) -> str | None:
    """라우팅 영수증의 domain. 없거나 읽을 수 없으면 None."""
    path = routing_receipt(session_id)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    domain = data.get("domain")
    return str(domain).strip().lower() if domain else None


SELF_DEFINITION_PATHS = (
    ".claude/hooks/lib/safety_screen.py",
    "tests/test_safety_screen.py",
)


def is_self_definition(tool_name: str, tool_input: dict) -> bool:
    """이 훅 자신의 정의 파일을 고칠 때만 선별을 건너뛴다.

    이유: 패턴 목록과 그 시험 자료는 차단 문구를 그대로 담아야 하므로, 선별을 걸면
    훅이 자기 정의를 못 고치는 자기잠금이 된다. 예외는 Write/Edit의 두 경로뿐이고
    Agent 프롬프트와 Bash 명령에는 적용하지 않는다.
    """
    if tool_name not in {"Write", "Edit", "MultiEdit"}:
        return False
    raw = tool_input.get("file_path") or tool_input.get("path")
    if not raw:
        return False
    normalized = str(raw).replace("\\", "/")
    return any(normalized.endswith(suffix) for suffix in SELF_DEFINITION_PATHS)


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
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return 0
    tool_name = str(payload.get("tool_name", ""))
    if is_self_definition(tool_name, tool_input):
        return 0
    code, message = screen(tool_name, tool_input, str(payload.get("session_id", "")))
    if message:
        print(message, file=sys.stderr)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
