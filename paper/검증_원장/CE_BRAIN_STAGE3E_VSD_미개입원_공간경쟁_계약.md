# CE-BRAIN Stage 3E VSD 미개입원 공간경쟁 계약

> 상태: **사전등록 / raw VSD outcome 미개봉**  
> 자료: Borealis `10.5683/SP2/CCHOVV`, version 1.2,
> `Neurophotonics tutorial.zip`  
> ZIP MD5: `2dce551e8a0a258a69708b8f5e3ebe37`

## 1. 쉬운 말로 말한 목표

- **최종 목표:** 뇌의 자극-반응 간선을 거리로 설명할 수 있는지, 아니면 방향성 그래프나 일반
  전이규칙이 더 맞는지 구분한다.
- **이번 하위 목표:** 20개 피질 위치 중 한 위치의 자극반응을 숨겼을 때, 나머지 위치에서 배운
  공간규칙으로 그 전체 반응 지도를 맞힐 수 있는지 본다.
- **필요한 이유:** 처음 보는 자극원을 못 맞히면 training 연결행렬이 예뻐 보여도 일반화되는
  뇌 공간이라고 부를 수 없다.

## 2. 목표 정렬과 주장 상한

이 자료는 한 공개 예제 동물, 20개 거시적 피질 영역, 영역당 2회 반복으로 보인다. 따라서
통과해도 `한 동물의 mesoscale VSD에서 source-held-out 공간규칙이 development로 생존했다`까지만
말한다. 세포 수준 국소기하, 동물 일반화, Riemannian metric, Stage 4 구조 ground truth로
승격하지 않는다. 작은 독립 perturbation이 없어 local quadraticity의 직접 검사는 불가능하다.

## 3. 장치와 봉인 분할

- stimulation/receiver site는 공식 코드 순서의 20개다.
- 각 stimulation site에는 TIFF repeat 1·2가 있고, 두 stimulation site마다 대응하는 no-stim
  TIFF `NOA`부터 `NOJ`까지가 repeat별로 있다.
- source label을 `SHA256("CE-BRAIN-stage3-vsd-r1|" + label)`로 정렬한다.
- development 12개:
  `V2L, HLR, M2R, MFR, RSL, MBR, MFL, V1R, PTR, RSR, PTL, M2L`.
- calibration 4개: `V1L, V2R, HLL, BCR`.
- confirmation 4개: `MBL, FLL, BCL, FLR`.
- 이번 실행은 development 12개 source의 leave-one-source-out만 연다. calibration과 confirmation의
  source별 결과는 읽거나 보고하지 않는다.

## 4. 고정 전처리

공식 `NetworkAnalysis_VSD.m`의 수치 정의를 재현한다.

1. TIFF는 `128×128×108`, repeat 2개여야 한다.
2. source index `i`의 no-stim은 `A + floor(i/2)`이고 repeat 번호는 source repeat와 맞춘다.
   공식 주석의 “every two stims”와 파일구조를 따른다. MATLAB 예제의 `j` 기반 NOA 고정은
   명백한 indexing 불일치이므로 주 분석에 쓰지 않는다.
3. `stim/no-stim`, 원래 frame 3–28 baseline, `dF/F0×100`을 계산한다.
4. 공식 5×5, sigma 2.5 Gaussian kernel과 zero padding을 적용한다.
5. frame 32 stimulus artifact를 제거한다.
6. 20개 `pos.mat` 좌표의 5×5 ROI에서 신호를 평균한다.
7. 새 frame 20–28의 baseline, 새 frame 32–42의 최대값을 사용한다. 최대값이 baseline SD의
   2.5배를 넘을 때만 새 frame 33–35의 baseline 초과합을 response로 쓰고 음수는 0으로 둔다.
8. stimulation source와 같은 receiver의 diagonal은 0으로 둔다.

## 5. 경쟁 모델

각 development source를 한 번씩 숨기고, 한 repeat로 적합해 다른 repeat의 숨긴 response
20개를 예측한다. repeat 방향을 바꾼 두 MSE를 source 단위에서 평균한다.

- `M0 receiver mean`: source 정보 없이 receiver별 training 평균만 사용.
- `M1 isotropic Euclidean`: receiver intercept에 source-receiver Euclidean 거리와 거리제곱을
  더한 고정 공간 감쇠.
- `M2 directed quadratic`: receiver intercept에 `dx, dy, dx², dx·dy, dy²`를 더해 방향성과
  이방성을 허용한 공간모델.
- `M3 general source kernel`: receiver별로 training source 좌표에서 Gaussian kernel 보간한다.
  bandwidth는 training source 좌표 쌍거리의 중앙값으로 outcome을 보지 않고 고정한다.

M1/M2는 최소제곱, M3는 정규화 가중평균이다. hidden source·repeat의 값으로 파라미터나
bandwidth를 고르지 않는다.

## 6. 통계와 분기

source별 개선은 `(MSE_M0 - MSE_model) / MSE_M0`이다. 12개 development source를 독립
부호 단위로 삼아 `2^12=4096`개 exact sign-flip의 한쪽 p값을 계산한다.

- `SPATIAL_GEOMETRY_SURVIVES_DEVELOPMENT`: M1 또는 M2의 평균 개선 `>0`, exact `p<=0.01`,
  10,000회 source bootstrap 95% CI 하한 `>0`.
- `GENERAL_KERNEL_PREFERRED_DEVELOPMENT`: M3가 위 문턱을 통과하고, M3 개선에서 가장 좋은
 M1/M2 개선을 뺀 source별 차이도 exact `p<=0.01`, bootstrap 하한 `>0`.
- M3만 첫 문턱을 통과하지만 geometry 대비 우위 문턱까지는 못 넘으면
  `GENERAL_KERNEL_SURVIVES_DEVELOPMENT`로 제한한다.
- 어느 모델도 첫 문턱을 통과하지 못하면 `VSD_SOURCE_GENERALIZATION_NOT_ESTABLISHED`.

같은 directed response matrix에서 symmetry 오차와 probabilistic distance의 triangle violation은
descriptive diagnostic로만 기록한다. 해당 값만으로 metric을 채택하거나 폐기하지 않는다.
평가 MSE에서는 자극 artifact 때문에 정의상 0으로 만든 source=receiver diagonal 하나를 제외한다.

## 7. 실행 후 목표 이탈 검사

- 원래 질문에 답했는가: unseen source의 전체 response 예측에 답했는지 확인한다.
- 무엇이 반증되었는가: 실패한 고정 model family만 좁혀 기록한다.
- 무엇이 살아 있는가: calibration·confirmation source, 다른 동물, 세포수준 자료는 봉인한다.
- 다음 허용 행동: development 생존 모델이 있을 때만 calibration source를 별도 계약으로 연다.
  local quadraticity와 동물 확인 없이 Riemannian 또는 전역 manifold로 올라가지 않는다.
