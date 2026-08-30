# CE-BRAIN Stage 3E VSD 미개입원 공간경쟁 결과

> 판정: `VSD_SOURCE_GENERALIZATION_NOT_ESTABLISHED`  
> 자료: Borealis `10.5683/SP2/CCHOVV`, version 1.2  
> 계약: `CE_BRAIN_STAGE3E_VSD_미개입원_공간경쟁_계약.md`

## 1. 한 문장 결과

두 반복에서 자극-반응 행렬은 안정적으로 재현됐지만, 12개 development 자극원을 하나씩 숨긴
예측에서 고정 유클리드·방향성 이차공간·일반 공간커널 어느 것도 receiver-mean 기준선을
사전등록 문턱만큼 이기지 못했다.

## 2. 결과표

| 항목 | 평균 개선 | exact sign-flip p | source bootstrap 95% CI | 판정 |
|---|---:|---:|---:|---|
| 반복 간 off-diagonal 상관 | `0.767629` | — | — | 신호 재현성 있음 |
| isotropic Euclidean | `+0.011736` | `0.402832` | `[-0.082287, 0.091079]` | 미통과 |
| directed quadratic | `-0.121727` | `0.809814` | `[-0.380853, 0.111213]` | 미통과 |
| general source kernel | `-0.016697` | `0.703125` | `[-0.072464, 0.034184]` | 미통과 |
| kernel - best geometry | `-0.028433` | `0.691162` | `[-0.124187, 0.078486]` | kernel 우위 없음 |

확률거리 진단의 symmetry median absolute difference는 `0.749873`, ordered triad triangle
violation fraction은 `0.084091`이었다. 이 값들은 descriptive이며 단독 판정 게이트가 아니다.

## 3. 문과 독자를 위한 해석

같은 도시의 교통지도를 두 번 측정했더니 비슷한 지도가 나왔다. 측정기가 망가진 것은 아니다.
하지만 11개 출발지의 교통흐름으로 열두 번째 출발지의 전체 흐름을 맞히려 하자, 단순히
각 목적지의 평균을 말하는 방법보다 거리 지도도, 방향을 허용한 지도도, 부드러운 보간법도
확실히 낫지 않았다.

따라서 지금 실패한 것은 `뇌에는 공간구조가 전혀 없다`가 아니다. 실패한 것은 더 좁고 강한
주장이다.

> 한 동물의 거시적 피질 자극에서, 다른 자극원에 그대로 옮겨 쓸 수 있는 고정 공간규칙이
> 현재 세 모델 중 하나로 존재한다.

유클리드 모델 평균이 `+1.17%`인 것은 작은 방향성 신호일 수 있지만, source별 변동이 커서
신뢰구간이 0을 넓게 가로지르고 exact p도 `0.403`이다. 이를 geometry 지지로 승격하지 않는다.

## 4. 목표 정렬 사후점검

- 원래 질문에 답했는가: 예. training reconstruction이 아니라 unseen stimulation source의
  전체 response를 맞히는지 검사했다.
- 무엇이 미확립되었는가: 현재 고정 Euclidean·directed quadratic·source-kernel family.
- 무엇이 살아 있는가: 상태에 따라 바뀌는 geometry, 비공간 graph/operator, 더 미세한 자극,
  다른 동물과 다른 endpoint.
- 다음 허용 행동: calibration `V1L,V2R,HLL,BCR`와 confirmation `MBL,FLL,BCL,FLR`는 열지
  않는다. 새 model family는 같은 development outcome에 사후 적합하지 말고 별도 자료 또는
  새 계약이 필요하다.
- 금지: 이 결과를 local quadraticity·Riemannian 부재의 증명이나 전 뇌 보편결론으로 읽지 않는다.

## 5. 재현 영수증

- ZIP MD5: `2dce551e8a0a258a69708b8f5e3ebe37`
- 실행:
  `py -3.11 examples/brain/ce_brain_stage3e_vsd_source_generalization.py <zip>`
- 결과 artifact: `data/external/ce_brain_stage3_vsd/development_result.json`
- calibration/confirmation stimulation TIFF는 실행 코드가 읽지 않았다.
