# CE-NPF 대체 생물학자료 D1 동일뉴런 기능결합 분석계약

## 목표와 지위

- 계보: `ALT_BIO_D1_SAME_CELL_COUPLING_v1`
- 자료: Majnik et al. Track2p, Zenodo record `17091226`.
- 상위 가설 2의 재구성: “뉴런이 의미를 가진 채 태어나 청소년기에 고정된다”가 아니라, **공급자가 같은 행으로 추적한 동일 신경세포의 활동–운동 결합이 생후 초기 발달 1주 동안 측정 불안정성보다 크게 변하는가**만 묻는다.
- 이 분석은 데이터 설명에 이미 예고된 arousal modulation 발달을 고정식으로 재분석하는 재현이지, 맹검 발견이 아니다.

## 고정 입력과 추론 단위

- 마우스: `jm031`, `jm032`, `jm038`, `jm039`, `jm040`, `jm046` 전부.
- 주효과 세션: 각 마우스의 정렬된 첫 날 (F)과 마지막 날 (L). QC 실패 시 인접 날로 교체하지 않는다.
- 추론 단위는 뉴런이 아니라 마우스 6마리다.
- `spks.npy`는 공급자가 처리한 활동 proxy, `motion_energy_glob.npy`는 움직임/각성 proxy로 제한한다.

## 시간축 복원 게이트

행동 프레임 시간 (t_j)와 간격 (q_j=t_{j+1}-t_j)에 대해

\[
\tilde q=\operatorname{median}_j q_j,\qquad
r_j=\operatorname{round}(q_j/\tilde q)
\]

로 고정한다. 다음을 모두 만족해야 한다.

1. `interframe_int == diff(tstamps)` (배열의 정확 일치), (q_j>0).
2. 모든 (r_j\in\{1,2\}), 최대 반올림 잔차 ≤ `0.20 frame`.
3. 추론 누락수 ∑((r_j-1))가 `neural_frames - behavior_frames`와 정확히 같다.
4. 누적 복원 위치가 0에서 시작해 `neural_frames - 1`에 정확히 끝난다.
5. 누락률 ≤ 5%.

누락 위치에는 `NaN`만 넣고 보간하지 않는다. 12개 첫날·마지막날 세션 중 하나라도 실패하면 `D1_ALIGNMENT_BLOCKED`로 중단한다.

## 고정 전처리

1. 신경활동과 복원한 motion을 10프레임 비중첩 bin으로 나눈다.
2. 각 bin에서 `spks`는 평균, motion은 중앙값을 쓴다. motion이 10개 중 8개 미만이면 그 bin을 결측으로 한다.
3. 60 bins(600 원프레임)을 한 block으로 한다. 앞에서부터 완전한 짝수 개 block만 유지하고 나머지 꼬리는 버린다.
4. 0, 2, 4, ... block은 half (A), 1, 3, 5, ... block은 half (B)로 고정한다. 각 half에 최소 20 blocks와 할당 bin의 95% 이상 유효 motion을 요구한다.
5. 세포 집합은 마우스의 **모든 날**에서 `iscell[:,0] == 1`인 동일 행의 교집합으로 고정한다.
6. 네 endpoint half (F_A,F_B,L_A,L_B)에서 활동이 상수이거나 비유한값인 세포만 모든 endpoint에서 제외한다. 상관크기나 reliability로 선별하지 않는다. 마우스당 최소 20세포를 요구한다.

## 세포별 결합과 마우스별 효과

세포 (i), 날 (d\in\{F,L\}), half (h\in\{A,B\})에서 lag 탐색·로그변환 없이

\[
\beta_{i,d,h}=\rho_{\mathrm{Spearman}}
(\overline{spks}_{i,d,h},\widetilde{motion}_{d,h})
\]

를 계산한다. 마우스 (m)의 날 간 변화량과 같은 날 분할 잡음은

\[
D_m={1\over4}\sum_{h,k\in\{A,B\}}
\operatorname{median}_i
|\beta_{i,F,h}-\beta_{i,L,k}|,
\]

\[
N_m={1\over2}\left[
\operatorname{median}_i|\beta_{i,F,A}-\beta_{i,F,B}|+
\operatorname{median}_i|\beta_{i,L,A}-\beta_{i,L,B}|
\right],
\]

\[
E_m=D_m-N_m
\]

로 고정한다. (E_m>0)은 날 간 결합 변화가 같은 날의 분할-반복 불일치보다 크다는 운영적 뜻만 가진다.

## 통계와 판정

\[
T_+=\sum_{m=1}^{6}\mathbf 1(E_m>0)
\]

에 대해 귀무가설 (P(E_m>0)=1/2)의 단측 exact binomial sign test를 쓴다. 6/6 양성일 때만 (p=1/64=0.015625)로 주효과를 지지한다. 5/6은 (p=7/64=0.109375)로 지지가 아니다.

- `D1_SAME_CELL_COUPLING_CHANGE_SUPPORTED`: 전체 6마리 QC 통과 및 (T_+=6).
- `D1_SAME_CELL_COUPLING_CHANGE_NOT_SUPPORTED`: 전체 QC는 통과했지만 (T_+<6).
- `D1_BLOCKED_QUALITY`: 한 마리라도 정렬·block·유효 bin·세포수 게이트 실패. (n<6)으로 축소해 구제하지 않는다.

보조 강건성은 동일 pipeline의 Kendall (\tau_b), 공급자 세포행 홀수/짝수 분할, leave-one-mouse-out 방향으로 제한하며 주판정을 뒤집지 않는다.

## 해석 상한

- Track2p의 동일 행은 공급자의 추적 정의이며, `ground_truth.csv`는 3마리에만 있어 모든 세포의 물리 동일성을 독립 확인하지 못한다.
- 개별 마우스의 정확한 생후 일령이 현재 선택 파일에 고정되지 않아 “P7→P14”라고 부르지 않고 “첫날→마지막날의 생후 초기 발달 주간”으로 제한한다.
- motion energy는 뉴런의 “의미”가 아니다.
- 이 실험은 청소년기 고정, 시냅스 연결·가중치, 전도속도, 리만기하, 공간 접힘을 판정하지 못한다. 강한 선천적 기능 불변 가설만 좁힌다.
