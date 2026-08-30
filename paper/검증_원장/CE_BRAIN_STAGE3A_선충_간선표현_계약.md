# CE-BRAIN Stage 3A 선충 신호전파 간선표현 경쟁 계약

Status: `SEALED_PRE_RESULT`

봉인 전 schema receipt SHA-256은 `be74b966fbe664d00afd84486336fd5b3f0d08cfbc70c322f77f7f71be7e03fd`이다. 이 영수증은 confirmation 반응값을 열지 않았음을 기록한다. 봉인 직전 합성·규칙 단위검사는 `python -m pytest -p no:cacheprovider --basetemp %TEMP%\ce-stage3a-pytest-20260831-final tests/test_ce_brain_stage3a_worm_metric.py`로 10개 모두 통과했다.

## 1. 목표와 주장 상한

- **질문:** 직접 자극으로 측정한 방향성 source→receiver 전달을 대칭 거리, 방향성 거리, switching geometry, directed graph, 일반 비선형 operator 중 무엇이 가장 잘 예측하는가?
- **자료 역할:** DANDI `001075@0.240930.1859`는 다중 자극원 Stage 3 분석법의 실제 신경계 교정·후보 제거 자료다.
- **주장 상한:** C. elegans 신경계의 간선 표현 판정이다. mouse Phase 2E의 개체 상태축과 같은 종·같은 측정공간이 아니므로 이 결과만으로 포유류 국소 뇌 기하를 확정하지 않는다.
- **목표 정렬:** 현재 DANDI 000458의 MOs 단일 source로 불가능했던 대칭성·삼각부등식·held-out intervention 검사를 실제 다중 source 자료에서 수행한다.

## 2. 자산과 무결성

- 공개 판본의 `desc-segmentation_ophys+ogen.nwb` 110개만 사용한다.
- 총 bytes `1700529616`.
- 파일별 asset UUID·bytes·SHA-256 정본은 `data/external/ce_brain_stage3_worm/download-inventory.json`이며 그 SHA-256은 `31c9501592dc10b9a176f12124a77e7bbdfc06d2bf43fab97874526af5d7fcfc`이다.
- 원시 영상 4.1 TB는 사용하지 않는다. segmentation NWB에 기록된 stimulus table, target ROI, green/red trace, receiver centroid, canonical NeuroPAL label만 쓴다.

endpoint를 열지 않은 schema 감사에서 110개 동물, 5,614개 자극, 14,039개 receiver instance, canonical source 250종, directed canonical pair 35,876개, 양방향 쌍 13,004개가 확인됐다.

## 3. 고정 분할

subject id `s`를

```text
bucket = int(SHA256("CE-BRAIN-STAGE3A-20260905|s")[0:8], 16) mod 10
```

으로 나눈다.

- bucket 0–6: development 77개 동물.
- bucket 7–9: confirmation 33개 동물.

완전 미관측 source 시험은 canonical source label `n`에 대해

```text
int(SHA256("CE-BRAIN-STAGE3A-SOURCE-20260905|n")[0:8],16) mod 5 == 0
```

인 source의 모든 development endpoint를 fit에서 제외하고 confirmation에서만 채점한다.

## 4. canonical node와 좌표

- PumpProbe receiver id → `neuropal_ids` → NeuroPAL `labels`가 단일 정수 참조이고 최종 label에 영문자가 있는 경우만 canonical node로 쓴다.
- 자극 source는 `target_pumpprobe_id`가 finite이고 같은 receiver id의 canonical label이 있는 경우만 쓴다.
- source와 receiver가 같은 self-edge는 모델 점수에서 제외하고 source 품질 게이트에만 쓴다.
- development 동물의 receiver centroid를 축별 median/IQR로 정규화한 뒤 공통 label 중첩으로 similarity Procrustes 정렬한다. canonical template 좌표는 정렬된 development 좌표의 label별 median이다. confirmation 좌표나 반응값은 template 작성에 쓰지 않는다.

## 5. 반응 endpoint와 품질 게이트

각 동물·receiver에서 stimulus로부터 10초 이전~20초 이후가 아닌 frame으로 green 대 red OLS `g=a+br`를 fit한다. residual을 non-stimulus median과 `1.4826×MAD`로 z-score하며 MAD 바닥은 그 동물의 양수 MAD 10th percentile이다.

- baseline: stimulus start 기준 `[-10,-2]`초.
- response: stimulus stop 뒤 `[1,10]`초.
- response detection: `|z|≥3`이 연속 두 frame 이상.
- delivered-intervention gate: source self-response에서 `z≥4`가 연속 두 frame 이상. 이를 못 넘은 자극 사건 전체는 제외한다.
- pair endpoint `y∈{0,1}`은 receiver response detection이다. 부호·peak latency·10-point waveform은 진단으로 보존한다.

## 6. 후보 모델

모든 확률 모델은 development만으로 fit하고 confirmation binary log loss를 주 점수로 쓴다.

- `N` null: development 전체 propagation rate.
- `R` symmetric quadratic: `logit p=β0-ΔxᵀGΔx`, `G=L Lᵀ`인 PSD metric.
- `F` directional: R에 signed displacement `bᵀΔx`를 더한다.
- `S` switching: development template의 첫 두 PCA 축 사분면별 PSD metric 네 개와 shrinkage 공통 metric.
- `G` directed graph: canonical ordered pair의 Jeffreys-smoothed development rate; 미관측 pair는 source·receiver marginal의 logit 평균으로 backoff한다.
- `O` general coordinate operator: source/receiver template 좌표 6차원에 `PCG64(20260905)`로 고정한 64개 random Fourier feature와 ridge-logistic readout.

연속모델 R/F/S/O는 같은 ridge 후보 `10^-4,10^-3,10^-2,10^-1,1`을 development subject 5-fold hash CV로 선택한다. G의 smoothing과 모든 feature 수는 고정한다.

교차검증 행이 180,000개를 넘으면 모델별로 `PCG64(20260905 + len(model_name))`를 사용해 정확히 180,000개 행을 비복원 추출한다. 이 상한은 ridge 선택에만 적용하며, 선택 뒤 최종 development 적합과 confirmation 채점에는 모든 적격 행을 사용한다.

봉인 실행환경은 CPython 3.11.9, NumPy 2.4.6, SciPy 1.17.1, h5py 3.16.0이다. 실행 파일의 절대 경로를 manifest에 함께 기록하며, 재계산 때 구현·버전·경로가 manifest와 다르면 apparatus stop으로 처리한다.

## 7. 주 평가와 불확실성

1. **held-out animal/common pair:** development에 한 번 이상 존재한 ordered pair의 confirmation log loss. N/R/F/S/G/O 모두 비교한다.
2. **held-out source:** 사전 hash로 development에서 완전히 제거한 source의 confirmation log loss. N/R/F/S/O를 비교하고 G는 `NOT_IDENTIFIABLE_FOR_UNSEEN_SOURCE`로 별도 보고한다.
3. confirmation subject cluster bootstrap 1,999회, `PCG64(20260905)`.
4. A가 B보다 나은 상대 개선은 `(loss_B-loss_A)/loss_B`다.

후보 지지는 두 평가에서 N보다 `≥0.05` 개선하고 bootstrap 95% 하한 `>0`이어야 한다. 승자는 두 평가에서 다음 후보보다 평균 `≥0.03`, bootstrap 하한 `>0`이어야 한다. 한 평가만 이기거나 후보 간 문턱이 안 벌어지면 tension이다.

## 8. metric 공리 진단

- **방향성:** F의 R 대비 개선이 `≥0.03`, bootstrap 하한 `>0`이면 대칭 metric을 약화한다.
- **경험적 대칭성:** confirmation에서 양방향 모두 3개 동물 이상인 pair의 Jeffreys rate 차이 `|p_ij-p_ji|` 분포를 보고한다.
- **삼각부등식:** confirmation에서 각 directed edge가 3개 동물 이상인 triad에 `d_ij=-log p_ij`를 적용한다. 10% 상대 slack을 넘는 위반율을 deterministic 최대 50,000 triad에서 계산한다. bootstrap 위반율 하한이 0.10보다 크면 일반 probabilistic metric을 약화한다.
- **local quadraticity:** R이 N을 지지 문턱으로 이기고 최선 후보보다 3% 이상 열세가 아니어야 유지한다.

## 9. 판정

1. R 승리 + 방향성/삼각/local gate 통과: `RIEMANNIAN_LIKE_LOCAL_RETAINED`.
2. F 승리 또는 방향성 gate 통과, O가 F를 이기지 않음: `DIRECTIONAL_FINSLER_RETAINED`.
3. S 승리: `SWITCHING_STRATIFIED_RETAINED`.
4. G가 common-pair에서 승리하나 unseen-source를 예측할 수 없음: `DIRECTED_GRAPH_SEEN_SOURCE_ONLY`.
5. O 승리: `GENERAL_TRANSITION_OPERATOR_RETAINED`.
6. N만 지지되거나 후보가 갈림: `REPRESENTATION_TENSION`.
7. provenance/schema/preprocessing/manifest/recompute 실패: `STAGE3A_APPARATUS_STOP`.

어떤 결과도 anatomy-blind MICrONS Stage 4를 즉시 허가하지 않는다. 이 결과는 먼저 포유류 다중 source replication 후보와 full time-kernel Stage 3B 계약을 선택하는 데 쓴다.
