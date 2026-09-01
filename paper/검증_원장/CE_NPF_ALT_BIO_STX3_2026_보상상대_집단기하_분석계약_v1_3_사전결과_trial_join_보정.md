# Stx3 보상상대 집단기하 분석계약 v1.3 사전결과 trial-join 보정

Status: `ANALYSIS_CONTRACT_FROZEN_PRE_OUTCOME / BIOLOGICAL_ENDPOINT_NOT_YET_EVALUATED`

보정 계약 ID: `CE_NPF_ALT_BIO_STX3_REWARD_ALIGNMENT_XN_v1_3`

고정일: 2026-09-02

선행 계약 SHA-256:

- v1: `13bf98597f63fbb397cf86b0aa29404999eeb509a3f3a09e17fb7603d6eb576a`
- v1.1: `f7bf144585e19207a1289c85128c6b428a97433d3e355b7e389af0958911aa95`
- v1.2: `6a096227441ce8bb2a562953870524d35973be260b38b3adb5a9f95055cffa09`

이 문서는 v1.2의 첫 32-file 구조 preflight가 생물학 endpoint 계산 전에 멈춘 뒤 작성한
사전결과 보정이다. 기존 preflight receipt는
`data/external/plitt_kaganovsky_stx3_2026/stx3_reward_alignment_v1_2_full_preflight.json`,
상태는 `STX3_TRIAL_JOIN_BLOCKED`, SHA-256은
`d7913685d98457d91783bfa88a0891a7ab4dabcb4214e6dbf8117308f9e3036c`이다.
receipt의 `biological_endpoint_evaluated`는 `false`이고, `G`, `ΔG`, `B`, `ΔB`, 집단검정,
결합검정은 계산되지 않았으며 attempt marker와 endpoint 결과 파일도 생성되지 않았다.
따라서 이 보정은 결과에 맞춘 분석 변경이 아니며 v1.2 one-shot을 소비하지 않는다.
기존 실패 receipt는 삭제하거나 덮어쓰지 않는다.

## 1. 발견된 계약 오류와 자료 의미론

v1.1은 annotation의 global block 번호와 full-resolution 행동 stream의 session-local block
번호가 숫자까지 같아야 한다고 과잉 제약했다. 전수 구조 감사에서 다음이 확인되었다.

- annotation `trial_info.block_number`와 2P-aligned `block/data`는 32/32 exact였다.
- annotation `vr_trial_info.block_number`와 full-resolution `block/data`는 32/32 exact였다.
- full trial start/end 및 position timestamp에 공식 `session.py::_get_block_number`의
  `round(ITI) >= 59` 규칙을 독립 적용한 값도 32/32에서 `vr_trial_info.block_number`와
  exact였다.
- LR, trial number, trial 순서 및 경계는 32/32 exact였다.
- `trial_info.block_number - vr_trial_info.block_number`는 각 세션 안에서 하나의 정수
  상수였으며, `Cre_1/day0=1`, `Ctrl_4/day0=2`, 나머지 30세션은 0이었다.

두 stream은 서로 다른 sampling clock을 쓰므로 cross-family timestamp의 숫자 동일성은 join
조건이 아니다. 감사에서 trial-start 차이는 모두 -27.918--+58.312 ms였고, 대부분의 end
차이도 sampling quantization 범위였다. 마지막 trial의 큰 세 예외는 `Cre_1/day5`
442.142 ms, `Ctrl_7/day5` 97.103 ms, `Ctrl_8/day5` 79.471 ms였으나, 해당 trial의
number/LR/block partition과 start identity 및 신경 reward-window 위치 coverage는 유지됐다.
v1.3 preflight는 이 cross-family boundary 시간차를 세션별 진단값으로 기록하되, 이를
숫자-offset join이나 trial 삭제에 사용하지 않는다.

공식 loader는 annotation의 `trial_info`를 신경 프레임에 정렬된 trial 정본으로 읽고,
full-resolution 행동 stream은 별도로 읽는다. 공식 same-day concatenation 코드도 후속
session의 local block이 0에서 시작하면 이전 session의 마지막 global block에 1을 더해
global block 번호를 만든다. 따라서 위 두 nonzero 차이는 trial 불일치가 아니라 잘린
session fragment의 global/local 좌표 원점 차이이다.

## 2. 동결된 global-minus-local offset 표

아래 32행은 `subject<TAB>day<TAB>offset`을 사전식으로 정렬하고 LF로 결합하되 마지막
LF를 붙이지 않은 canonical text다. SHA-256은
`399b783760b50e33d93206066a841ab0ce53773fe13b955593f83b727ff2c92c`이다.

```text
Cre_1	0	1
Cre_1	5	0
Cre_2	0	0
Cre_2	5	0
Cre_3	0	0
Cre_3	5	0
Cre_4	0	0
Cre_4	5	0
Cre_5	0	0
Cre_5	5	0
Cre_6	0	0
Cre_6	5	0
Cre_7	0	0
Cre_7	5	0
Ctrl_1	0	0
Ctrl_1	5	0
Ctrl_2	0	0
Ctrl_2	5	0
Ctrl_3	0	0
Ctrl_3	5	0
Ctrl_4	0	2
Ctrl_4	5	0
Ctrl_5	0	0
Ctrl_5	5	0
Ctrl_6	0	0
Ctrl_6	5	0
Ctrl_7	0	0
Ctrl_7	5	0
Ctrl_8	0	0
Ctrl_8	5	0
Ctrl_9	0	0
Ctrl_9	5	0
```

## 3. 교정된 fail-closed trial join

각 선택 세션에서 다음을 모두 만족해야 한다.

1. annotation `trial_info.block_number`와 `trial_info.LR`을 neural/global trial 정본으로
   사용한다. aligned block/LR의 각 trial 구간은 이 정본과 exact여야 한다.
2. annotation `vr_trial_info.block_number`와 `vr_trial_info.LR`을 full/local trial 정본으로
   사용한다. full block/LR의 각 trial 구간은 이 정본과 exact여야 한다.
3. 두 annotation trial 벡터, aligned/full start·end marker, aligned/full trial-number 벡터의
   길이와 순서는 exact여야 한다. trial number는 두 stream에서 같고 세션 안에서 정확히
   1씩 증가해야 한다. aligned start/end는 기존대로 annotation index와 exact여야 한다.
4. 모든 trial ordinal에서
   `global block - local block = k_session`이어야 하며, 차이는 세션 안에서 상수여야 한다.
   그 상수는 제2절의 동결된 `(subject, day, offset)` 표와도 exact여야 한다.
5. endpoint의 block 0--4 학습행 및 block 5 평가행 선택은 오직 global
   `trial_info.block_number`를 사용한다. full/local block 번호를 endpoint 선택에 사용하지
   않는다.

한 trial만 다른 offset, transition 위치 불일치, 알려지지 않은 nonzero offset, LR 또는 trial
number 불일치, fuzzy time join, trial 삭제, trial별 offset, 결과값을 이용한 보정은 모두
`STX3_TRIAL_JOIN_BLOCKED`다.

## 4. 구현·검증·실행 게이트

- runner는 v1, v1.1, v1.2, v1.3 네 실파일의 SHA-256을 모두 검증한다.
- focused test는 +1/+2 동결 offset 통과, 상수지만 동결표와 다른 offset 차단, 한 trial만
  변한 offset 차단, `vr_trial_info`와 full stream 불일치 차단, 기존 LR/trial-number 차단을
  포함한다.
- v1.3 preflight는 기존 v1.2 실패 receipt와 다른 O_EXCL 경로에 쓰며 32/32 세션의
  `full_block_offset`을 보고한다.
- 새 runner, preflight, test, 전체 test count, v1.3 preflight receipt, 기존 7개 공식 source,
  selection/download/ROI receipt, 실행 환경을 새 execution lock에 결박한다.
- 위 잠금과 독립 감사 전에는 attempt marker를 만들거나 endpoint를 계산하지 않는다.

## 5. 해석 상한은 바뀌지 않는다

이 보정은 trial identity만 교정한다. estimator는 여전히 A/B crossvalidated bilinear
reward-alignment proxy이며 Fisher tensor, 리만 metric field 또는 물리적 시공간 metric의
직접 추정치가 아니다. Stx3 자료에는 직접적인 synaptic weight/STP/contact/delay 측정과
mediator-specific intervention/rescue가 없다. 따라서 양성 결과라도 상한은 비무작위 기전
연관을 포함한 동일동물 triad의 `BIO_EVIDENCE_L2`이고, 통합 연결→기하→행동 인과사슬은
`BIO_EVIDENCE_L0`을 넘지 않는다.
