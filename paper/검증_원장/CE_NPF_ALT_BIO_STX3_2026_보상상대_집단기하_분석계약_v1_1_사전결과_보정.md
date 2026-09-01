# Stx3 보상상대 집단기하 분석계약 v1.1 사전결과 보정

Status: `ANALYSIS_CONTRACT_FROZEN_PRE_OUTCOME / BIOLOGICAL_ENDPOINT_NOT_YET_EVALUATED`

보정 계약 ID: `CE_NPF_ALT_BIO_STX3_REWARD_ALIGNMENT_XN_v1_1`

기준 계약: `CE_NPF_ALT_BIO_STX3_REWARD_ALIGNMENT_XN_v1`

기준 계약 SHA-256: `13bf98597f63fbb397cf86b0aa29404999eeb509a3f3a09e17fb7603d6eb576a`

고정일: 2026-09-01

이 문서는 결과값을 열기 전에 수행한 독립 구현감사에서 발견된 모호성만 닫는다. 아래 항목은 기준 계약의 해당 문구를 대체하며, 나머지 항목은 v1을 그대로 유지한다. 이 보정 시점까지 신경·핥기·속도·보상 endpoint 값이나 군 통계는 계산하지 않았다.

## 1. 출처와 ravel identity

- NWB annotation에는 일반적으로 `ravel_ind`가 없으므로 그 부재는 실패가 아니다.
- `subject × code day × scan`에서 day0/day5 ravel index로 가는 정본은 공식 코드 commit `f2ab24db8709a321d38576a1fa674f95035a2fec`의 `mouse_metadata.py`이며, 파일 SHA-256은 `2a52a5561de9ea61c379b4e6997aa51429403dd75be58ed3fd99d7c56f58d68a`이다.
- NWB에서는 `mouse`, `day`, `mux`, `novel_arm`을 독립 대조한다. annotation에 `ravel_ind`가 실제로 있으면 공식 metadata와 정확히 같아야 한다.
- 실행기는 공식 `mouse_metadata.py` 파일 자체의 SHA-256과 ROI-audit의 고정 pair hash를 모두 확인해야 한다.

## 2. schema와 trial ordinal join

- 각 신경 파일에서 `F_dff`, fluorescence, neuropil은 모두 `(frames, ROI)`이고 shape가 같아야 한다.
- 2P-aligned 신호와 full-resolution 신호는 각 family 안에서 data 길이와 timestamp 길이가 같아야 한다. 각 timestamp는 유한·엄격 증가이고, 같은 family의 필수 신호 timestamp는 position timestamp와 정확히 같아야 한다.
- full-resolution 필수 신호에 `manual rewards`를 추가한다.
- neural trial 정본은 annotation의 `trial_start_inds`, `teleport_inds`, `trial_info.LR`, `trial_info.block_number`이다. aligned `trial start/end` marker index는 annotation start/stop과 정확히 같아야 한다.
- behavior trial 정본은 full-resolution `trial start/end` marker에서 독립적으로 재구성한 시간순 `[start, stop)` 구간이다. 각 구간에서 `LR`과 `block`은 하나의 유한 정수로 일정해야 한다.
- neural과 behavior는 completed-trial ordinal의 개수·순서·LR·block이 모두 정확히 같아야 한다. offset 보정, fuzzy join, trial 삭제는 금지한다.
- 유효 경계는 각 trial에서 `start < stop`이고 이웃 trial 사이에 `stop <= next_start`이다. stop marker sample은 그 trial의 계산에 포함하지 않는다.

## 3. 위치 bin과 동일-trial 가중

- 공식 TwoPUtils commit `be01b1778a2e13d0b30e94ffb6ad18266efb1370`의 규칙을 고정한다. `spatial_analyses.py` SHA-256은 `da82bcec7813fcae838c3f4a892d282d87543120dc93533a76d504ee8a04199b`, `sess.py` SHA-256은 `888693b5652ad155384dd0654a4d5c98740e9fa9dc3b15bc1062ecab4514f919`이다.
- trial slice는 `[start, stop)`, 위치 bin은 `(left_edge, right_edge]`이다. 따라서 위치 13은 제외되고 14는 첫 bin, 43은 마지막 bin에 들어간다.
- 먼저 각 trial×bin의 frame 평균을 구하고, fold ratemap은 관측값이 있는 trial들의 bin 평균을 동일 가중 `nanmean`한다. frame 수로 trial을 재가중하지 않는다.
- `W`, `S_rate`, `S_motor`의 관측단위는 모두 completed `trial × position-bin` population vector이다. blocks 0–4만 training, block 5만 endpoint에 쓴다.

## 4. ROI를 한 번만 고정하는 규칙

- aligner가 대응시킨 ROI 중 raw primary에서 A/B fold의 left reward window와 right shift가 요구하는 모든 bin, 그리고 blocks 0–4의 공통 training row에서 필요한 값과 양의 유한 residual variance를 갖는 ROI를 한 번 선택한다.
- training row는 speed·lick과 그 시점의 후보 population vector가 모두 유한한 trial×bin만 사용한다. 이 row mask를 고정한다.
- 선택된 ROI 수가 20 미만이면 `STX3_REGISTRATION_BLOCKED`이다.
- primary, `S_rate`, `S_motor`는 동일한 ROI 순서와 동일한 training row를 사용한다. sensitivity에서 비유한 값이 생기더라도 cell을 추가로 버리지 않으며 `STX3_NUMERICAL_BLOCKED`로 중지한다.
- day0 ref index를 오름차순 정렬하고 그 pair에 대응하는 day5 target 순서를 유지한다. h5py 입력을 위해 day5 column을 임시 정렬해 읽은 경우 반드시 inverse permutation으로 pair 순서를 복원한다.

## 5. crossnobis 수식의 완전한 정의

interior index에서 left full index `14..18`은 `13..17`, right full index `21..25`는 `20..24`이며 두 window는 같은 오름차순 reward-offset 순서로 대응한다. fold `f`, day `d`, offset `k`, shift `s`에 대해

\[
\delta^{f}_{d,k,s}
=\mu^{f}_{d,left,L_k}
-\mu^{f}_{d,right,(R_k+s)\bmod 28}.
\]

이 \(\delta\)를 v1 §7.2의 \(d_{d,s}\), \(G_{i,d}\), \(\Delta G_i\)에 넣는다. shift 0은 true alignment이고 confirmatory wrong shift는 계속 `5..23`이다.

## 6. 행동 endpoint와 reward censor

- H trial에서 full-resolution `non-consummatory licks`만 센다.
- 각 trial은 첫 `reward > 0` 또는 첫 `manual rewards > 0` sample 직전까지만 eligible하다. 둘 다 전 trial에서 0일 때만 omission이다. reward sample과 그 뒤 sample은 제외한다.
- eligible 구간 안에서 whole track은 `[13,43)`, pre-reward window는 `[tfront-3,tfront)`이다.
- arm별 행동값은 trial별 비율의 평균이 아니라 H trial 전체의 pooled event ratio이다.

\[
B_{arm}=\frac{\sum_H N_{pre}}{\sum_H N_{whole}}.
\]

- arm 전체 whole-track lick 수가 0이면 `B_arm=0`이다. 이후 left/right arm을 동일 가중해 v1의 \(B_{i,d}\)와 \(\Delta B_i\)를 구한다.
- speed는 각 H trial의 eligible `[13,43)` finite sample mean을 먼저 구하고, arm 안에서 trial 동일 가중 평균, 마지막으로 left/right arm 동일 가중 평균한다. 이 day 값의 day5-day0 차이가 `Δspeed`이다.
- primary H trial 하나라도 eligible speed sample이 없으면 `STX3_NUMERICAL_BLOCKED`이다.

## 7. motor FWL, precision, 순열

- `S_motor`의 lick predictor는 2P-aligned `processing/behavior/2P-aligned behavior/licks/data`이다.
- blocks 0–4의 고정 training row에서 speed와 lick를 각각 `ddof=0` 평균/SD로 z-score한다. 두 SD는 모두 양의 유한값이어야 한다.
- category는 `day × LR × position_bin`이다. category-demean한 두 predictor의 design rank가 2가 아니면 `STX3_NUMERICAL_BLOCKED`이다. cell별 OLS 뒤 block5에는 speed/lick 항만 제거하고, 이어 cell-axis mean을 제거한다.
- precision residual variance는 sample variance `ddof=1`로 계산한다. positive finite variance의 median이 없거나 floor가 비유한이면 `STX3_NUMERICAL_BLOCKED`이다.
- 9 Ctrl/7 Cre 전수 label 검정은 관측 배치를 포함한 11,440개 모두를 분모로 하며 `count(T_perm >= T_obs) / 11440`이다. add-one 보정은 쓰지 않는다.
- association의 primary/`S_rate`/`S_motor`는 seed `20260901`로 미리 생성한 같은 99,999개 군내 behavior-rank permutation index를 재사용한다. Monte Carlo p는 v1의 add-one 정의를 유지한다.

## 8. 보고용 sensitivity의 지위

non-wrapping shift, omission-only behavior, 980-nm-only subset은 confirmatory PASS나 구조적 실패를 바꾸지 않는 `DESCRIPTIVE_ONLY`이다. 사전 정의가 부족한 별도 p-value를 만들지 않는다.

- non-wrapping: 고정 shift `8..23`의 mouse별 `ΔG`, 군 평균과 `mean_Ctrl-mean_Cre`만 기록한다.
- omission-only: 각 mouse×day×arm에서 omission H trial이 2개 이상인 경우에만 같은 pooled 행동값을 기록하고, mouse별 `ΔB`, 가용 mouse 수, 군 평균만 기록한다.
- 980-nm-only: `Ctrl_1..5`, `Cre_1..7`의 primary mouse별 `ΔG`, 군 평균과 차이만 기록한다.

## 9. 실행 허가 게이트

v1과 이 보정문서의 SHA-256, runner SHA-256, 정확한 Python 실행파일·버전, NumPy·SciPy·h5py 버전, selection/download/ROI/code source hash를 execution lock에 기록한 뒤에만 one-shot을 허용한다. 합성시험 또는 32-file preflight가 하나라도 실패하면 endpoint를 계산하지 않는다.

