# CE-BRAIN Human Memory 양성대조 R1 결과

Status: `PREREGISTERED_SENSITIVITY_NOT_ESTABLISHED / OFFICIAL_METHOD_DIAGNOSTIC_REPRODUCED`

기준일: 2026-08-31

## 1. 사전등록 판정

outcome-blind development 순서에서 완전 200-trial, schema unit 10개 이상인 최초 13 subjects를 열었다. firing/coverage 문을 통과한 units는 251개였다.

사전등록한 category-preserving label permutation `[0.2, 1.2]`초 분석에서:

- memory-selective units: 12/251 = 4.78%
- selective unit이 있는 subjects: 9/13
- cohort-wide null count 95 percentile: 16 units
- 사전 비율 문턱: 7%

실제 12 units는 비율 문턱과 null-count 문턱을 모두 실패했다.

**[사전등록 판정]** `MEMORY_APPARATUS_SENSITIVITY_NOT_ESTABLISHED`.

이 결과만 보면 P19·P16의 관계복원 음성을 생물학적 부재로 강화할 수 없다.

## 2. 공개 원코드 감사

공식 OSF code archive `codeCopyGitHub_nwbsharing.tar.gz`를 SHA-256 `34e6c22b...a364d0`으로 고정해 MATLAB 구현을 확인했다.

공식 `NWB_singleCellAnalysis_release.m`은 논문 본문의 “200ms 뒤 1초” 요약과 달리 다음을 사용한다.

1. stimulus onset `+0.2`부터 `+1.7`초, 총 1.5초
2. 행동이 정답인 old/new trials만 사용
3. old와 new를 각 집단 평균에서 빼고 pooled mean을 더한 centered bootstrap
4. 1,000 resamples, `p<0.05`
5. summary에서는 별도 firing-rate filter 없이 처리된 모든 cells를 분모로 사용

또한 공식 코드 내부 주석은 실제 데이터와 맞게 `1=old, 0=new`라고 명시한다. NWB column description의 `0=old, 1=new`는 반대다. 우리의 pixel identity 의미 고정이 옳았음을 독립 확인한다.

공식 code archive: <https://osf.io/hv7ja/>

## 3. outcome-known 공식방법 진단

사전등록 결과를 본 뒤, 같은 13 subjects에 공식 MATLAB 방법을 Python으로 그대로 옮긴 진단을 실행했다.

- units: 263
- memory-selective: 23
- 비율: 8.75%
- 논문 전체자료 기준: 146/1,863 = 7.84%

공식방법 진단은 알려진 기억신호를 같은 크기로 재현했다.

**[진단 판정]** `OUTCOME_KNOWN_OFFICIAL_METHOD_DIAGNOSTIC_REPRODUCED`.

이 진단은 사전등록 결과를 대체하지 않는다. 다만 다음 두 사실을 분리한다.

- 데이터와 spike table 자체에는 old/new 기억신호가 있다.
- 우리의 더 짧고 category-stratified한 사전등록 양성대조는 그 신호를 충분히 검출하지 못했다.

## 4. 계보 영향

P19·P16 관계복원 미통과를 “기억신호가 없는 데이터였기 때문”이라고 설명할 수는 없다. 반면 관계복원 분석은 공식 신호가 강한 시간창과 정답 trial 제한을 사용하지 않았으므로, 현재 음성을 최종 반증으로 승격하는 것도 금지한다.

다음 정당한 행동은 이미 본 P19/P16/양성대조 13명에서 창을 바꾸는 것이 아니다. **아직 관계 endpoint를 열지 않은 새 development subjects**에서 공식 0.2–1.7초·correct-trial 조건을 포함한 R2 관계복원 계약을 먼저 고정하고 실행하는 것이다.

코드: `examples/brain/ce_brain_human_memory_positive_control.py`

검증: `tests/test_ce_brain_human_memory_positive_control.py`
