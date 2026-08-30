# CE-BRAIN Stage 3H R1 — opto-fMRI 구조 전파연산자 계약

## 목표와 이탈 점검

- **목표:** 단순 직선거리보다 방향성 structural-connectome 전파 profile이 여섯 source의 whole-brain 반응관계를 더 잘 나타내는지 검사한다.
- **가설 사다리상의 위치:** Stage 3의 `metric 실패 → graph/operator 후보` 분기에 직접 대응한다.
- **현재 단계가 필요한 이유:** Stage 3G R2에서 Euclidean 후보가 실패했으므로, 같은 반응 RDM을 바꾸지 않고 구조 후보만 교체해야 원인을 분리할 수 있다.
- **이탈 여부:** 정렬됨. 이 검정은 graph shortest-path나 리만 거리를 주장하지 않고, 방향성 전파연산자의 source-profile 표현만 검사한다.
- **다음 게이트:** 구조 후보도 실패하면 고정·개체공통 공간표현은 미확립으로 두고 state/history-conditioned operator 또는 새로운 다중-source 장치로 이동한다.

## 고정 원자료와 재현 장치

- Coletta voxelwise connectome v2, DOI `10.17632/dxtzpvv83k.2`.
- 원 ZIP SHA-256: `8b481aebca120d41532c7fd5ab1845c6eb9c043c939b6e3eddd2c937b611a09f`.
- `full_connectome_no_thr.mat` SHA-256: `87bd852da4c72499dbc788bd911154789cfe4bd374a79b956cbc2995bb0d86bf`.
- `final_tesselation.nii.gz` SHA-256: `8f2760fff6d0fe4654e377f7956392a470d50446cbc182bfab56495971c52eca`.
- Moon 저자 코드 ZIP SHA-256: `183e458904d00a265450f9b2ec1956b774cc8c314699f58cbe7b4b757cfa672e`.
- `Allen_idx_proc.mat` SHA-256: `1e8b88c2628f2fcfd464c8ec2c8d090448c6e4cc9e3fe22bbca97469dd5f3a83`.

저자 `Polysynaptic_Moon_et_al.m`을 따라 왼쪽 `MOp, MOs, SSp-bfd, VISp, RSP, VISarl`을 15,314 parcel에 voxel-count 가중하고, 방향성 행렬을 1·2·3회 적용한다. 매 차수에서 source 자체 parcel은 0으로 만든다. 136개 양측 ROI로 가중 평균한 뒤, 2차 이상은 이전 차수들과 상수항을 회귀해 잔차만 남기고 target 축으로 표준화한다. 여섯 source profile의 `1-Pearson correlation` 15개가 각 차수의 고정 구조 RDM이다.

반응을 보기 전에 구조 RDM 생성이 완료됐고 상태는 `STRUCTURAL_OPERATOR_BUILT`다.

## 외부 사전정보로 잠근 1차 후보

동일 논문은 excitatory activation의 evoked connectivity는 주로 monosynaptic, inhibitory-neuron activation으로 얻은 spontaneous/silencing connectivity는 trisynaptic 구조와 맞는다고 보고했다. 따라서 현재 개발 반응을 보지 않고 다음을 고정한다.

- Thy1-ChR2: `incremental_order_1`.
- VGAT-ChR2: `incremental_order_3`.

`incremental_order_2` 및 서로 바꾼 차수는 1차 선택에 쓰지 않고 차수 특이성 음성대조에만 쓴다.

## 반응과 1차 검정

Stage 3G R2에서 생성한 등록-atlas foreground cross-half 반응 RDM을 그대로 재사용한다. 각 동물에서 고정 구조 RDM과 15개 반응거리의 Spearman `rho`를 구한다.

유전자형별 통과 조건:

1. 반복 신뢰도 중앙값 `>=0.30`, exact one-sided sign-flip `p<=0.05`.
2. 구조 연관 rho 중앙값 `>=0.30`.
3. rho exact one-sided sign-flip `p<=0.05`.
4. 여섯 source 이름 720개 완전 순열 `p<=0.05`.

두 유전자형은 별도 조건부 주장이다. 한 유전자형만 통과하면 그 조건에 한해서만 후보로 둔다.

## 2차 차수 특이성

잠근 차수 rho에서 각 대안 차수 rho를 뺀 개체별 차이를 계산한다. 두 대안 모두에 대해 중앙값 차이 `>=0.10` 및 paired exact one-sided sign-flip `p<=0.05`일 때만 `order-specific`이라고 부른다. 1차 구조 연관은 통과하지만 이 경쟁이 실패하면 “구조 profile 후보”까지만 허용하고 “1시냅스/3시냅스 특이성”은 주장하지 않는다.

## 판정과 주장 상한

- 둘 다 통과: `STRUCTURAL_OPERATOR_RELATION_CANDIDATE`.
- 하나만 통과: `CONDITION_LIMITED_STRUCTURAL_OPERATOR_CANDIDATE`.
- 둘 다 실패 또는 반복 신뢰도 실패: `STRUCTURAL_OPERATOR_RELATION_NOT_ESTABLISHED`.

통과해도 이는 6-source×136-target의 개체공통 구조 전파 profile과 반응관계의 연관이다. 최단경로 metric, 국소 리만성, 개체별 실제 축삭 연결, causal propagation time을 뜻하지 않는다. calibration/confirmation 각 6마리는 계속 봉인한다.
