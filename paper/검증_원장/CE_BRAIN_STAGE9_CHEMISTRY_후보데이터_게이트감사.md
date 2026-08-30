# CE-BRAIN Stage 9 chemistry 후보 데이터 게이트 감사

Status: `CHEMICAL_WRITE_GATE_NOT_IDENTIFIABLE_IN_AUDITED_CANDIDATES`

기준일: 2026-08-31

## 1. 직접 주장의 최소 장치

`화학은 쓰기 허가를 건다`를 직접 검사하려면 같은 개체·과제·비교 단위에 다음 네 축이 함께 있어야 한다.

1. 전기적 population trajectory
2. ACh·DA·NE 측정 또는 개입
3. 전기 trajectory를 맞추고 화학 상태를 비교할 조건
4. 이후에도 남는 시냅스·표현·행동 update endpoint

한 Dandiset 안에 ephys 파일과 photometry 파일이 따로 있다는 사실은 동시 측정이 아니다.

## 2. endpoint-blind 후보 감사

| Dandiset | 실제 asset 구조 | 직접 gate 판정 |
|---|---|---|
| `001176@0.260610.2204` | ACh 단독 또는 cholinergic axon+ACh+행동; ephys와 지속 update 없음 | 식별 불가 |
| `001950@draft` | 9개 Zarr의 `.zmetadata` 직접 검사: unit-bearing 5, FIP-bearing 3, 둘을 함께 가진 asset 0 | 식별 불가 |
| `001955@0.260828.0749` | ephys 34, photometry 32지만 공동 asset 0, 양 modality의 subject overlap 0 | 식별 불가 |
| `001084@0.241023.2011` | 180개가 ophys 계열; 빠른 dopamine·광학 조작 자료이나 ephys 없음 | 식별 불가 |
| `000251@0.230331.0255` | 한 Dandiset에 dopamine sensor와 single-unit가 있으나 sensor는 159·209–219 계열, unit는 30xx 계열로 subject/session이 분리됨 | 동시 gate 식별 불가 |
| `000559@0.260528.0858` | 폐루프 dopamine axon 광자극과 이후 행동은 있으나 ephys·내인성 화학 측정 없음 | 약한 인과지속성만 실행 가능 |
| `000298@draft` | 질문은 FSCV+ensemble에 가깝지만 buggy라고 명시된 invalid draft, asset 1 | 실행 불가 |
| `001434@draft` | ACh 학습·소거 질문은 가깝지만 현재 invalid draft, asset 0 | 실행 불가 |

001950은 계속 변하는 draft이므로 기준일 snapshot 판정이다. 001434·000298도 향후 유효 자료가 공개되면 다시 장치 감사를 할 수 있다.

## 3. 판정과 의미

**[장치 판정]** `CHEMICAL_WRITE_GATE_NOT_IDENTIFIABLE_IN_AUDITED_CANDIDATES`.

000559의 약한 하위분기는 결과를 열기 전에 cohort-confounding을 막는 계약을 고정해 실행했다.
같은 cohort 0·3·5의 14동물에서 방향은 양수였지만 primary exact `p=0.1333`, late-session
`p=0.2511`로 `DA_CAUSAL_PERSISTENCE_NOT_ESTABLISHED`였다. 이는 직접 gate 판정을 바꾸지
않으며 정본은 `CE_BRAIN_STAGE9_DA_R6_인과지속성_결과.md`다.

이것은 ACh·DA·NE가 기억 쓰기를 조절하지 않는다는 음성 결과가 아니다. 현재 감사한 공개 후보로는 CE의 더 강한 직접 주장을 같은 관측계에서 식별할 수 없다는 뜻이다.

**[금지]** 001176의 빠른 ACh dynamics, 001632의 dopamine 학습자료, 별도 ephys 결과를 사후에 연결해 하나의 직접 gate 증거로 만들지 않는다.

**[재개 조건]** 네 축이 같은 개체와 비교 단위에 있는 새 공개자료, 또는 화학 개입 전후의 전기 궤적과 장기 행동 변화가 함께 기록된 사전등록 실험이 필요하다.
