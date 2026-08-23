# BA-SELF2-L3 대안 경로 결정 — 무차원 QC apparatus 판본

Status: COMPLETE

Contract SHA-256: `8eb85e4ce7218112c082b84e0f754ae3fa0afb1995374a9675c581164880517f`

Source-lane SHA-256: `54c318e3d42af474c253e97c2a9b56f83fe906959239b380c81365027defe55f`

Math-lane SHA-256: `403c7d73d01d8d736aff2db220d74f985cbcf9b4ff3d6aeb1c7173c1e8d7f827`

## 결정 범위

BA-SELF1은 `sub-01`에서 고정한 절대 전압 QC가 `sub-02`의 모든 D1
창을 탈락시켜 모델 outcome을 계산하지 못했다. 이 판본의 유일한
질문은, 공통 gain 및 채널별 상수 offset에 불변인 사전 고정
`Q_A,Q_D` gate가 D1에서 다음 개발 단계로 넘어갈 만큼 전이되는가이다.
이는 신경 품질의 충분조건도, 상태·경로 식의 검증도 아니다.

모든 경로는 관측된 scalp-EEG quotient에 한정한다. 현재 관측 상태와
국소 변화율 및 순서를 버린 요약량을 조건화한 뒤, 순서 있는 과거가
100 ms 뒤 quotient를 추가 예측하는지만 이후에 검사할 수 있다. 따라서
어느 경로도 자아, 의식, 무한 차원, 해마 hash, 단일 뉴런 전압, 또는
인구 일반화를 식별하지 않는다.

## 경로 비교와 사전 중단 규칙

| 경로 | 이번 판본의 상태 | 검증 대상 | 주요 교란/한계 | 사전 kill 또는 재개 규칙 |
|---|---|---|---|---|
| R1 | **SELECTED — OPEN** | A2에서 동결한 scale-free `Q_A,Q_D`가 D1의 32 paired trial에 전이되는지, 그리고 그 뒤에만 고정 상태/경로 모델의 held-out 예측 이득 | channel-specific gain, 다채널 동시 artifact, 이미 참조/필터를 통과한 체계오류는 `Q_A,Q_D`를 통과할 수 있다. A2 창은 독립 표본이 아니다. | D1에서 총 24/32 또는 어느 session에서 12/16 미만이면 `APPARATUS_INVALID_CROSS_SUBJECT_SCALE_FREE_QC`로 종료한다. 통과 뒤 D2 양방향 이득이 없으면 `STOP_NO_ROBUST_DEVELOPMENT_GAIN`; C3 fixed gate 실패면 해당 claim을 종료한다. parser/receipt 결함만 같은 계약에서 보수할 수 있다. |
| R2 | NOT SELECTED — separate new contract | 각 채널을 자체 robust scale로 정규화한 뒤 품질 gate를 두어 channel-specific gain 영향까지 줄이는 QC | 채널별 정규화는 넓은 공간적 진폭 구조와 실제 artifact를 함께 평탄화할 수 있다. 현재 A2 cutoff, `Q_A,Q_D`, D1 전이 문턱과 다른 측정 모델이다. | 이번 R1이 apparatus-invalid이거나, 별도 source/math audit가 R2의 artifact 검출력과 새 A-split calibration rule을 고정할 때만 새 판본에서 재개한다. D1 값을 보고 R2 기준이나 cutoff를 추가하는 것은 금지한다. |
| R3 | NOT SELECTED — separate new contract | low-frequency drift, line/scanner residual, spectral shape 또는 band-power를 추가한 QC | band 경계·window·threshold 선택이 자유도를 늘리고, spectral abnormality가 곧 biological artifact라는 보장은 없다. 이미 R1 failure를 보고 고르면 target-aware measurement tuning이 된다. | 독립된 apparatus split에서 band/window/threshold와 adverse synthetic control을 먼저 동결할 때만 재개한다. D1 수치, D2 loss 또는 confirmation을 본 뒤 spectral gate를 덧붙이면 즉시 무효다. |
| R4 | NOT SELECTED — dataset/modality replacement | `ds004196` 같은 별도 EEG 자료에서 QC/경로식 재현, 또는 `ds001618`의 self-reference fMRI에서 별도 질문 검증 | 과제, 센서, 전처리, time scale, participant 구조가 달라 직접적인 실패 회피가 될 수 있다. fMRI의 BOLD/motion/physiology와 EEG의 scalp quotient는 같은 관측량이 아니다. | 현 dataset의 R1은 고정된 규칙으로 완결한다. 새 dataset은 source provenance, mechanism, split, measurement model, matched controls, endpoint를 처음부터 계약하고 독립 confirmation을 둘 때만 새 run으로 시작한다. 현 run의 D1/D2 결과로 dataset을 고르는 것은 금지한다. |
| R5 | NOT SELECTED — ontology is not an empirical route here | “자아가 현재 상태인가, 이어지는 경로인가”라는 존재론적 판별 | 유한 history는 확장 상태로 재매개변수화할 수 있고, EEG는 전체 뇌상태가 아닌 관측 kernel의 quotient다. 같은 관측 상태에 서로 다른 hidden history가 가능하다. | R1의 예측 이득 또는 실패 어느 쪽도 R5를 통과/기각하지 못한다. 새 관측 개입이 이 no-go를 깨는 식별 조건을 제공할 때만 별도 철학·실험 계약으로 재개한다. 이 run에서는 `UNIDENTIFIED`를 유지한다. |

## 선택: R1만 실행

R1은 선행 실패의 원인과 직접 맞닿은 가장 작은 수정이다. 신호 변환,
관측 quotient, path-area 식, target, feature menu, D2 선택 절차, C1/C2/C3
confirmation, 그리고 claim ceiling은 BA-SELF1에서 그대로 상속한다. 바뀌는
것은 절대 전압 QC를 `Q_A,Q_D`의 scale-free apparatus gate로 교체한 것과,
이미 QC 목적으로 열린 D1을 향후 모델 자료에서 영구 제외한 것뿐이다.

R1의 A1/A2는 endpoint·target·feature·loss에 접근하지 않고 cutoff를 한 번
동결한다. D1도 `Q_A,Q_D`, pair/session acceptance, 그리고 matched absolute
diagnostic만 기록한다. `z`, 미래 target, path feature, loss, `M_0/M_1`은
D1에서 계산하지 않는다. 그러므로 D1-QC 통과는 과학적 성공이 아니라 D2
실행 가능성 gate다. D2는 오직 잔여 `sub-02` 132 pair에서 menu를 고르고,
`sub-03` confirmation은 그 전까지 봉인한다.

R1의 75% D1 gate가 실패하면 이 run은 음성 apparatus 산출로 완결한다.
그 결과는 path equation의 반증이 아니며, cutoff·정규화·band·dataset을
같은 run 안에서 바꿔 재시도할 권한을 주지 않는다. 반대로 D1 gate 통과도
QC의 일반화 또는 생물학적 동일성을 보장하지 않는다. 이후 D2 및 C3의
고정 adverse-control 조건까지 만족할 때에만 제한된 within-dataset
temporal-history pilot 결과를 보고할 수 있다.

## 동결 및 재개 경계

이 파일을 포함한 lanes와 audit gate가 고정된 뒤, D1의 `Q_A,Q_D` 값이나
acceptance를 본 다음에는 R2--R5를 추가하거나 R1의 QC 식, cutoff 법칙,
75% 문턱을 바꿀 수 없다. 그러한 변경은 이번 판본의 실패를 사후 흡수하는
새 측정 모델이므로 새 `00-contract.md`, 독립 apparatus calibration, source
및 math audit를 갖는 후속 run을 요구한다.

R4와 R5는 이번 run의 fallback이 아니다. R4는 다른 measurement contract이고,
R5는 현재 관측으로 식별 불가능하다는 no-go다. 이 구분은 R1의 양성 또는
음성 결과를 자아·의식·무한 차원에 대한 증거로 확대하지 못하게 하는
claim ceiling의 일부다.
