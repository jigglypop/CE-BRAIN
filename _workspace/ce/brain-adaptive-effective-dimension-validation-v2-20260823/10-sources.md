# BA-SRM7 출처 레인 — Hallinen 측정모형과 missingness rule

Status: COMPLETE

Date: 2026-08-23

## 1. 판정

BA-SRM7의 public dataㆍcode provenance와 원저자 prediction input은 1차 출처에서
확인됐다. BA-SRM6의 `Ratio2` neuron별 finite fraction 0.75는 archived producer code의
규칙이 아니다. 원저자 Python prediction pipeline은 raw red/green에서 만든
motion-corrected $I$를 평활ㆍ보간한 `I_smooth_interp_crop_noncontig`를 사용하고,
timepoint에서 NaN neuron 비율이 0.5 미만일 때만 그 timepoint를 보존한다.

다만 BA-SRM7의 train-prefix fit, causal one-sided filter, reliability weight $D_r$는
논문이 입증한 생물 기전이 아니라 미래 예측 leakage를 막기 위한 분석자 revision이다.
따라서 `SOURCE_VERIFIED_MEASUREMENT_START / CAUSAL_ANALYST_EXTENSION`으로 판정한다.

## 2. 1차 출처 잠금

| 항목 | 잠근 식별자 | 지지 범위 |
|---|---|---|
| publication | Hallinen et al., *eLife* 2021, DOI `10.7554/eLife.66135` | moving *C. elegans*의 동시 population calcium과 locomotion |
| data | OSF DOI `10.17605/OSF.IO/DPR3H`, node `dpr3h` | AML310/AML32 GCaMP, AML18 GFP archive |
| code | `leiferlab/PredictionCode`, revision `ca59416112a9c10a8d6a3179092a7d3c888bcd4e` | published preprocessingㆍprediction input |
| archival code | Software Heritage revision `ca59416112a9c10a8d6a3179092a7d3c888bcd4e` | immutable revision receipt |
| code license | GPL-2.0; `LICENSE` SHA-256 `189b1af95d661151e054cea10c91b3d754e4de4d3fecfb074c1fb29476f7167b` | local source audit; upstream code를 제품 코드로 복사하지 않음 |
| OSF license | API field `null` | rawㆍderived data commit/redistribution 금지, local analysis와 인용만 |

기계 판본 영수증은 `artifacts/source-lock.json`이다.

## 3. archived code에서 확인한 측정 사슬

`utility/data_handler.py`의 SHA-256은
`69c2ff90f1aa98a04e5b4b89c7e2319b176db0dfd1a012c9b6eff54c5d6b89bd`다.
이 파일에서 확인되는 순서는 다음과 같다.

1. `heatDataMS.mat`를 읽고 `rRaw`, `gRaw`, `rPhotoCorr`, `gPhotoCorr`를
   `hasPointsTime` 길이로 자른다.
2. raw red/green에 exponential photobleaching correction을 적용한다.
3. `rPhotoCorr`/`gPhotoCorr`가 NaN인 위치를 raw-corrected channel에서도 NaN으로
   만들고 `close_nan_holes`와 flagged-volume mask를 적용한다.
4. neuron별로 green을 red+intercept에 least squares fit해 common motion component를
   빼고 $I$를 만든다.
5. NaN-weighted Gaussian filter `gauss_filterNaN`으로 평활ㆍ보간하고, 긴 NaN 구간에
   남은 nonfinite는 `np.interp`로 채운다.
6. $I$에서 NaN neuron 비율이 0.5 미만인 timepoint만 `valid_map`에 둔다.
7. `I_smooth_interp_crop_noncontig`와 실제 `I_Time_crop_noncontig`를 함께 저장한다.

`utility/get_all_recordings.py` SHA-256
`b26d0d0d9c05c2ebc3123cbdde23429225fa0d20265977ef6e09dacee488a863`는 prediction
recording을 만들 때 `Neurons.I_smooth_interp_crop_noncontig`를 읽고 같은 valid map의
velocity와 curvature를 붙인다. `Ratio2`는 별도 MATLAB correlation script에 남지만
published Python locomotion predictor의 neural input이 아니다.

실제 MAT schema에서도 `behavior`는 `ethogram`, `x_pos`, `y_pos`, `v`, `pc1_2`,
`pc_3`를 포함하며, `v`와 `pc1_2` 길이는 `hasPointsTime`과 맞는다. BA-SRM7은
centerline-derived 새 label을 만들지 않고 이 embedded fields만 쓴다.

## 4. source와 BA-SRM7 revision의 분리

| 연산 | archived source | BA-SRM7 primary | 지위 |
|---|---|---|---|
| photobleach fit | full retained trace | recording first-60% prefix only | `[공리: 모델 선택]` leakage 방지 |
| red→green decorrelation fit | full trace | first-60% finite pair only | `[공리: 모델 선택]` leakage 방지 |
| filter | centered Gaussian, $\sigma=5$ | one-sided truncated Gaussian, $\sigma=5,L=20$ | `[공리: 모델 선택]` causalization |
| frame viability | NaN neuron fraction $<0.5$ | 동일 | `[공리: 외부 입력]` source rule |
| neuron viability | effective bad-neuron list empty; no 0.75 rule | prefix finite count $\ge W$ and nonconstant scale | `[공리: 모델 선택]` estimator existence |
| covariance | publication의 핵심 대상 아님 | fixed reliability-weighted PSD $G_t$ | `[공리: 모델 선택]` CE 관측 operator |

원저자의 centered Gaussian filter는 $t$ 뒤 값을 읽는다. 같은-time behavior decoding에는
upstream preprocessing이지만 BA-SRM7의 $t+h$ causal prediction에서는 leakage 위험이
있다. 그래서 source-symmetric output은 parity diagnostic으로만 남기고 score하지 않는다.
이는 source code가 틀렸다는 판정이 아니라 질문이 달라 생기는 경계다.

## 5. 데이터가 지지할 수 있는 범위

Hallinen corpus는 source-rooted calcium summary와 locomotion 사이의 temporal held-out
prediction, 그리고 GFP/red/mask artifact control을 시험하기에 적합하다. 다음은 이
자료와 분석으로 식별되지 않는다.

- spike, membrane voltage, synaptic current;
- structural 또는 directed synaptic edge;
- recurrent loop의 causal return operator;
- hippocampal sparse index 또는 hash;
- conscious report, conscious moment, 인간 의식;
- AGI capability 또는 구현 원리.

실제 score가 통과하더라도 최대 문장은 다음과 같다.

> source-rooted causal fluorescence quotient의 soft spectral features가 이 개발 corpus의
> calibration-prefix 이후 future locomotion에서 matched observed controls보다 증분
> 예측값을 보였다.

## 6. 후속 독립 경로

독립 confirmation은 이번 corpus로 measurement rule을 제안했다는 사실을 피할 수 있는
새 source-locked recording을 요구한다. whole-brain worm replication에는 WormID/DANDI,
mammalian multi-area predictive transfer에는 IBL, hippocampal index에는 별도의 human
iEEG reinstatement 자료가 후보지만, 어느 것도 BA-SRM7의 현재 입력으로 대체하지 않는다.

## 7. 참조

- Hallinen KM et al. (2021), DOI `10.7554/eLife.66135`, accessed 2026-08-23.
- OSF project, DOI `10.17605/OSF.IO/DPR3H`, accessed 2026-08-23.
- `https://github.com/leiferlab/PredictionCode/tree/ca59416112a9c10a8d6a3179092a7d3c888bcd4e`, accessed 2026-08-23.
- `https://archive.softwareheritage.org/browse/revision/ca59416112a9c10a8d6a3179092a7d3c888bcd4e/`, accessed 2026-08-23.
