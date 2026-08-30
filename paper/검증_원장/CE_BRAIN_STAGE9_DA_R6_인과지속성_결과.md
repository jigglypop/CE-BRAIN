# CE-BRAIN Stage 9 DA-R6 도파민 개입 뒤 행동 지속성 결과

> 판정: `DA_CAUSAL_PERSISTENCE_NOT_ESTABLISHED`  
> 계약: `CE_BRAIN_STAGE9_DA_R6_인과지속성_계약.md`  
> 실행일: 2026-08-31

## 1. 한 문장 결과

폐루프 도파민 축삭 광자극군은 무자극 post 세션에서 표적 행동 사용 변화가 대조군보다
양의 방향이었지만, 동일 cohort 안 정확 순열검정의 사전 문턱을 통과하지 못했다.

## 2. 고정 분석 결과

| 항목 | 결과 | 문턱 | 판정 |
|---|---:|---:|---|
| 독립 동물 | chr2 8, ctrl 6 | 계약 장치와 일치 | 통과 |
| post 3·4 cohort-adjusted 효과 | `+0.0292049` | `> 0` | 방향 통과 |
| primary exact p | `0.133333` / 450 permutations | `<= 0.01` | 실패 |
| leave-one-animal-out 최소효과 | `+0.0135521` | 모든 값 `> 0` | 통과 |
| session 4 효과 | `+0.0246765` | `> 0` | 방향 통과 |
| session 4 exact p | `0.251111` / 450 permutations | `<= 0.05` | 실패 |

최종 상태는 계약의 AND 게이트에 따라 `DA_CAUSAL_PERSISTENCE_NOT_ESTABLISHED`다.

## 3. 문과 독자를 위한 해석

실험 동물마다 특정 행동이 나오면 도파민 축삭을 자극했고, 나중에는 자극을 끈 채 그 행동을
계속 더 쓰는지 보았다. 평균만 보면 자극군이 더 오래 그 행동을 썼다. 그러나 실험 배치 안에서
`자극군` 표찰을 가능한 모든 방식으로 다시 붙여 보니, 지금 정도 차이는 우연한 배치에서도
13.3% 정도 나왔다. 미리 정한 허용치는 1%였으므로 증거로 채택하지 않았다. 더 늦은 세션은
우연 가능성이 25.1%였다.

이 결과는 `도파민이 지속 행동변화를 만들지 않는다`는 증명이 아니다. 표본이 작고 cohort 3에는
처치 동물이 한 마리뿐이다. 정확한 결론은 **이 고정 자료·endpoint·배치대조로는 CE가 요구한
지속 쓰기 하위증거가 확립되지 않았다**이다.

## 4. 목표 정렬 사후점검

- 원래 질문에 답했는가: 직접 화학×전기 gate가 아니라 그보다 약한 지속 행동 하위질문에만 답했다.
- 무엇이 미확립되었는가: `change_usage` 마지막 30초를 동물 단위로 합친 현재 family.
- 무엇이 살아 있는가: 다른 지속 endpoint, 더 큰 균형 표본, 내인성 화학 측정, 동시 전기생리.
- 다음 허용 행동: 이 결과를 Stage 10 통합의 생존자로 사용하지 않는다. 직접자료 탐색 또는 새
  사전등록 실험 설계만 허용한다.

## 5. 재현 영수증

- 원본 processed parquet SHA-256:
  `3b139a1f46c750181616930d753dd1d804e01a75686e5c0cb34904932e401344`
- 잠금 CSV SHA-256:
  `89b18227486e4d29c842e11e0372093e63bf9e7ff7b7d58cfec76add34e19ec5`
- 실행:
  `py -3.11 examples/brain/ce_brain_stage9_da_r6_causal_persistence.py data/external/ce_brain_stage9_dandi000559/learning_timecourse_locked.csv`
- 결과 artifact:
  `data/external/ce_brain_stage9_dandi000559/result.json`
