# Reality Stone 라이브러리 전환

활성 CE 코드는 PyPI의 `reality_stone[llm]==0.3.0`을 사용한다. 라이브러리 소스는
독립 [Reality Stone 저장소](https://github.com/jigglypop/reality_stone)에서 관리하고, 이 저장소에는
복사하거나 `PYTHONPATH`로 주입하지 않는다.

```powershell
python -m pip install .
python tools/verify_library.py
python -m pytest tests/test_unified_example.py -q -p no:cacheprovider
```

`verify_library.py`는 설치된 0.3.0의 위치, 두 Rust 확장, gradient와 CPU BrainRuntime을
검사한다. 네이티브 확장을 다시 빌드하려면 독립 라이브러리 저장소의 README를 따른다.
CUDA는 이번 배포의 지원 범위에 포함하지 않는다.

## 원본 연구 재현

분리 전 commit은 `fffd356ee4f1f7bf5079f3379cd06e4dc56a444c`다. 추적 파일 2,590개의
원래 바이트와 디렉터리 구조를 `C:\dev\ce\ce-agi-runtime-repro-fffd356`에 보존했다.
원본을 직접 바꾸는 대신 과거 연구는 이 환경에서 실행한다. 실행 파일, Python
3.11.9, 설치 패키지 목록과 파일 해시는
`C:\dev\build\reality-stone-extraction-20260919\reproduction-environment.json`에 기록했다.
외부 데이터와 `CE_RUNS_PATH` 자료는 계속 읽기 전용 입력이다.
CE 작업 트리에서 뺀 소스와 약 1.83 GB의 빌드 산출물은 같은 작업 폴더의
`retired-active-files`에 별도로 보존했다. 이 이동은 디스크 전체 사용량이나 Git 과거 이력을 줄이지 않는다.

```powershell
python tools/historical.py pytest tests/test_reality_bridge.py -q
```

다른 위치에 원본 복제본이 있으면 `CE_REPRO_SOURCE_ROOT`를 지정한다. historical
실행기는 원본 HEAD와 선택한 파일의 SHA-256을 확인한다. 이 실행은 자동으로 전체
연구를 재실행하지 않는다. 이관 경로와 원본 해시는
[분리 원장](ledger/reality_stone_extraction.json)에 기록한다.

해시 또는 옛 파일 경로에 묶인 26개 검사·스크립트는 원본 환경으로 이관했다.
일반 검사는 설치된 패키지의 파일 위치를 조회하도록 바꿨다. 과거 영수증의 경로와
해시는 수정하지 않았다. 설치 위치가 달라진 새 검증 결과를 옛 영수증과 동일한
기록으로 취급하지 않는다.

`ood_length_repro.py`와 `recursion_probe.py`의 학습 말뭉치는 원래 라이브러리의
소스·예제·테스트 전체이므로 보존된 원본을 읽는다. wheel 안의 코드만 사용해
데이터가 달라지는 것을 막기 위한 선택이다. 기존 말뭉치가 필요하지 않은 새 연구는
별도의 입력을 명시해야 한다.

## 검증 범위

0.3.0은 [PyPI](https://pypi.org/project/reality-stone/0.3.0/)에 배포했다.
[배포 작업](https://github.com/jigglypop/reality_stone/actions/runs/35435176257)은
Windows AMD64·Linux x86_64·macOS arm64와 Python 3.10–3.12 조합의 wheel 9개를 검사했다.
각 wheel의 네이티브·fallback 실행과 gradient 검사 4개가 통과했다.
실제 공개 wheel을 설치한 CE 작업 트리에서 전환 대상 테스트 1,793개가 통과했고,
보존한 원본 환경의 선택 검사 4개도 통과했다.

배포 검사는 두 Rust 확장, 기본 연산·gradient, CPU BrainRuntime, Python fallback을
확인한다. 소프트웨어 배포 성공은 생물학적 결과나 기존 연구의 재현 성공을 뜻하지
않는다. 일반 전체 수집에는 이미 삭제된 `.claude` hook을 찾는 세 테스트가 남아
있으며, 이 문제는 이번 라이브러리 분리와 별개다.
작업 중 별도로 변경된 `AGENTS.md`와 삭제된 `.codex/`, `CE_BRAIN_RESEARCH.md`는 보존했다.
이 상태에서 문서 정책 검사는 기존 오류 38개를 보고하며, 이번 분리로 추가된 오류는 없다.

독립 라이브러리의 `main`과 `v0.3.0`은 `cf8f47884a7b17a4a1d8e75f0bc9b7499c4706fd`다.
CE 저장소는 `main`, upstream `origin/main`, HEAD와 확인한 원격 tip 모두
`fffd356ee4f1f7bf5079f3379cd06e4dc56a444c`이며, 소비자 전환 변경은 커밋하지 않은 작업 트리에 있다.
바뀐 파일 목록과 전체 검증 로그는 외부 작업 폴더의 `final-consumer-change-list.json`과
[분리 원장](ledger/reality_stone_extraction.json)에 기록했다.
