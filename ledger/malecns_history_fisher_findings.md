# MaleCNS 끝점·직전 관측쌍·전체 경로의 효능 정보

문서 유형: 개발 분석 원장. 시작일: 2026-09-15. 재개일: 2026-09-19.
현재 상태: 2026-09-19 같은 범위의 전량 계산·독립 차분·companion 실행 완료, 산출물 등록 완료.
질문은 [연결 효능 분석](malecns_connection_fisher_findings.md)의 같은 세 좌표에서
현재만 보는 관측과 이력을 더 보는 관측이 얼마나 다른 정보를 보존하는가다.
전체 raw 그래프와 초기분포를 유지하며, 시점별 endpoint Fisher를 독립 표본처럼 더하지 않는다.
새 다운로드·사전등록·실제 뇌 활동 실험은 아니다. 파일 무결성은 [데이터 원장](data_registry.md)에 별도로 둔다.

## 고정 입력과 관측 범위

`connection-fisher-v1`의 결과·NPZ·소스·검사와 부모 입력 5개를 재사용한다.
현재 파일 크기·SHA가 봉인값과 일치함을 확인했다. 전체 연결 151,856,684개,
active raw source 1,834,661개, terminal category 흡수, 세 공유 log-efficacy feature와
source-common gauge를 바꾸지 않는다. 27개 assigned superclass의 균등/out-weight
초기분포 54개를 같은 기준값에 고정한다. 기간은 0..16 model step이다.

현재 관측 $Y_t$는 active category 30개와 terminal category 30개를 구별하는 60출력이다.
이번 이력 관측은 정확히 $(Y_{t-1},Y_t)$의 **인접 두 시점 결합 관측**이다. 이를
모든 과거의 coarse-history likelihood나 자율적인 60상태 Markov 축약이라고 하지 않는다.
30출력 대조에서는 두 시점 각각의 active/terminal flag를 버린다. 가장 많은 정보를
보존하는 상한 비교는 $X_0,\ldots,X_t$의 full path이며, 매 시점의 active raw ID와
terminal category를 관측한다. 더 많은 정보와 관측·저장 비용이 함께 들어가므로
동일 예산 모형의 우월성 비교가 아니다.

## 실제 결합확률의 구성

active 상태를 $a$, 흡수된 terminal category 확률을 $b$, 전체 active/terminal 전달을
$A,B$, active category 합산을 $O$라 둔다. source $j$의 category를 $c(j)$라 하고
한 step의 60출력 전달을 $S=[OA;B]$라 하면, 직전 상태가 active인 부분은

$$
q_t(c,d)=\sum_{j:c(j)=c} a_{t-1,j}S_{dj}
$$

다. 직전부터 terminal category $c$에 있던 질량은
$q_t(30+c,30+c)=b_{t-1,c}$에 더한다. 다른 terminal 출발 칸은 0이다.
source별 희소 readout을 $W_{60c(j)+d,j}=S_{dj}$로 옮기면 3,600×N 희소 연산자와
$a$의 곱으로 active 부분을 정확히 계산한다. $N$은 active raw source 수다.
이 행렬의 nnz는 source × 관측쌍 압축 셀 수이며 raw dyad 수가 아니다.

feature를 곱한 raw 행렬을 $F_k^A,F_k^B$, source 평균을 $\mu_k$라 둔다. $W_k$는
$[OF_k^A;F_k^B]$를 같은 방법으로 옮긴 행렬이다. 특히 reciprocity는 관측 category만
보고 곱할 수 없으므로 먼저 raw edge에 feature를 적용한다. 이전 단계의 미분
$u_k=\partial_k a$, $v_k=\partial_k b$로 결합 미분의 active 부분은
$W(u_k-\mu_k\odot a)+W_ka$이며 terminal 대각에는 $v_k$를 더한다.
결합확률을 각 축으로 합한 값과 그 미분은 봉인된 이전·현재 endpoint 값과 각각 같아야 한다.

현재 endpoint의 확률을 $p_d=\sum_cq_t(c,d)$, 양의 support에서 직전 관측의 조건부
확률을 $r_{c|d}=q_t(c,d)/p_d$라 두면 결합 score는
$\partial_\theta\log p_d+\partial_\theta\log r_{c|d}$로 분해된다.
조건부 score의 평균은 0이므로 교차항이 소거되어

$$
G_{pair60}-G_{endpoint60}=\sum_d p_d G_\theta(Y_{t-1}\mid Y_t=d)
$$

를 얻는다. 우변은 현재를 안 뒤 직전 관측이 더하는 효능 좌표의 조건부 Fisher이며
양의 준정부호다. 이는 상호정보량이나 생물학적 기억량이 아니고, 확률변수 사이의
통계적 의존 자체를 측정한 것도 아니다. 조건부 분포가 선택한 효능 방향에 따라 달라지는지를 본다.

## Full-path 정보와 비교 가능한 순서

같은 고정 feature와 양의 support에서, source $j$를 지난 한 전이의 score는
$f-\mu_j$다. 주어진 source에서 조건부 평균이 0이므로 서로 다른 시점 score의 교차
기댓값은 0이다. source별 feature 공분산을 $C_j$라 하면 full-path Fisher는

$$
G_{path}(t)=\sum_{r=0}^{t-1}\sum_j a_{r,j}C_j,
\qquad C_j=E[f f^\top\mid j]-\mu_j\mu_j^\top
$$

다. 이 합은 **조건부 전이 score 공분산의 합**이지 endpoint Fisher의 합이 아니다.
초기분포는 좌표에 무관하므로 초기 score는 0이고 흡수 후 결정론적 반복도 score 0이다.
feature의 겹침을 포함한 모든 교차 공분산을 계산하며, 관측으로 집계한 W만으로 source
공분산을 대신하지 않는다. 배경은 [Arampatzis 등, Pathwise Sensitivity Analysis in Transient Regimes](https://arxiv.org/abs/1502.05430)이며
이 유한 모형의 결과는 작은 raw 경로의 직접 열거로 독립 검산한다.

같은 기간에 다음 포함 관계만 강제한다.

- 이전·현재 endpoint30 각각의 Fisher ≤ pair30 Fisher ≤ pair60 Fisher.
- 이전·현재 endpoint60 각각의 Fisher ≤ pair60 Fisher ≤ full-path Fisher.
- 현재 refined endpoint Fisher ≤ full-path Fisher.
- full-path Fisher의 step 증가분은 양의 준정부호.

부등식은 행렬 Loewner 순서다. pair60과 현재 refined endpoint는 서로 포함되지 않으므로
차이 행렬의 양·음 고유값을 그대로 보고한다. 인접 쌍은 관측 window가 이동하므로
pair Fisher의 시간 단조도 요구하지 않는다. 작은 동일 feature 그래프의 반례를 검사에 둔다.

각 source와 terminal category를 고정하면 같은 압축 셀의 underlying terminal ID에서
feature가 일정하다. 따라서 **이전 raw source ID까지 본 full path**에 terminal ID를
추가해도 이번 세 좌표의 score 정보는 늘지 않는다. 이 결론을 이전 source가 category로만
보이는 pair60이나 terminal endpoint 관측으로 일반화하지 않는다.

## 구현과 진행 조건

[소스](../verify/MaleCNS/history_fisher.py)와 [관련 검사](../tests/test_malecns_history_fisher.py)를
추가했다. 작은 raw graph의 경로 완전 열거, 결합 미분의 독립 지수 tilt, raw source 공분산,
terminal ID의 full-path/endpoint 차이, nonnested 관측, 이동 window 비단조와 영방향을 검사한다.
2026-09-15에는 기본 Python 3.11.9 실행기로 관련 검사 **7개가 1.85초에 통과**했고 Sol의 독립
읽기 리뷰에서 차단 결함은 없었다. 당시 원장은 별도 Python 3.11.15에서 ‘전량 실행 중’으로
기록했지만, 2026-09-19 재개 점검에서는 결과·summary·캐시 출력과 실행 프로세스가 모두 없었다.
따라서 과거 실행을 완료 결과로 취급하지 않는다. 기존 소스와 입력을 바꾸지 않고 관련 검사
**7개를 1.33초에 다시 통과**한 뒤 같은 기본 범위의 전량 계산을 한 번 시작했다.
프로세스 생존이나 부분 로그를 완료 결과로 세지 않는다.
전량 확률·미분 질량·양 축 marginal 재현의 허용오차는 `5e-9`다. 고유값 검사는
`min_eigenvalue/max(1,max_abs_eigenvalue) >= -5e-9`이며 clipping·ridge를 쓰지 않는다.
rank 기준은 이전과 같은 `eigenvalue > 1e-10*max(1,largest_eigenvalue)`다.

현재 저장소에서 사용자가 삭제한 `.codex`를 복원하지 않고, 바이트가 보존된 형제 checkout의
실행기를 사용했다. 실행 명령은 저장소 루트에서 다음과 같다.

```powershell
$env:CE_PYTHON = 'C:\Users\dongh\AppData\Local\uv\cache\archive-v0\Sp2cxzBGA63aECqn\Scripts\python.exe'
C:\dev\ce\ce-agi-runtime-repro-fffd356\.codex\hooks\python.cmd python verify/MaleCNS/history_fisher.py --parent-result verify/MaleCNS/connection_fisher_result.json --cache-dir data/local/malecns-analysis/history-fisher-v1 --result verify/MaleCNS/history_fisher_result.json
```

시작 시각은 2026-09-19 19:22 KST, 실행 세션은 `58179`, launcher PID는 `6480`이다.
로그는 `C:\Users\dongh\AppData\Local\Temp\ce-history-fisher-20260919T192208376.out.log`와
동명 `.err.log`다. 이 식별자는 재개 당시 추적용이며 이후의 생존 증거를 대신하지 않는다.
이 실행은 종료 코드 0과 `HISTORY_FISHER_COMPLETE`를 남기고 끝났다. 전체 시간은
1,100.0919502초, 해석적 계산은 337.2561193초다. 실제 환경은 Python 3.11.15,
NumPy 2.4.6, SciPy 1.17.1이다. 입력·소스·검사·부모 결과와 출력 NPZ의 해시 12개를
완료 뒤 다시 대조했다. 작업 메모리 추정 8,439,638,464 bytes는 실측 최고 메모리가 아니다.

전량 독립 비선형 차분은 모든 54개 초기분포·3,600개 관측쌍·0..16 step에서 세 구조
좌표와 `h=1e-4,5e-5`를 비교한다. 최대 절대오차 `1e-6` 이하와 성분별
`error/(1e-8+1e-4*abs(analytic)) <= 1`을 함께 요구한다. 결과가 나오기 전에 기준을
바꾸지 않는다. full-path Fisher의 독립 검산은 작은 경로 완전 열거이며 거대한 전체 raw
경로를 모두 열거하거나 전량 full-path finite difference를 실행했다는 뜻이 아니다.

## 전량 검증과 결과

[완료 결과](../verify/MaleCNS/history_fisher_result.json)의 관측쌍 배열은
`(17,60,60,54)`, Jacobian은 `(17,60,60,54,4)`, Fisher는 `(17,54,6,4,4)`다.
모든 값은 유한하며 source별 결합 읽기 연산자의 비영 압축 셀은 5,014,620개다.

| 검사 | 전량 결과 | 판정 기준 |
|---|---:|---|
| 저장 NPZ 전체 step 0..16의 결합 확률 질량 최대오차 | `1.184385922670117e-12` | `5e-9` 이하 |
| 실행 중 diagnostics, step 1..16의 같은 오차 | `1.8407497748285095e-13` | `5e-9` 이하 |
| 두 주변분포의 부모 endpoint 대비 최대오차 | `1.1900480600957053e-12` | `5e-9` 이하 |
| 결합 미분 질량 최대오차 | 약 `1.027e-14` | `5e-9` 이하 |
| 공통 배수 gauge의 Jacobian·Fisher | 정확히 0 | 0 |
| 강제한 Loewner 관계의 최소 scaled 고유값 | 약 `-2.521e-14` | `-5e-9` 이상 |
| 세 좌표·두 간격의 차분 최대 절대오차 | `3.1474500783446047e-10` | `1e-6` 이하 |
| 같은 차분의 최대 scaled 오차 | `0.01836184489316089` | 1 이하 |

두 주변분포와 그 미분도 부모 endpoint 결과를 허용오차 안에서 재현했다. 더 작은
차분 간격이 항상 더 작은 오차를 만들지는 않았으므로 두 간격만으로 수렴 차수를
주장하지 않는다. 전량 차분은 결합확률의 Jacobian을 검산하며, full-path 식의 독립
검산 범위는 위에 명시한 작은 경로 완전 열거다.
질량 오차의 두 값은 합산 순서 때문이 아니다. 코드의 diagnostics 루프는 step 1에서
시작하고, 전체 NPZ의 최대오차는 초기 diagonal joint인 step 0의 probe 24에 있다.
초기 step을 포함한 검사도 통과했으며 결과 파일 자체는 수정하지 않았다.

1. **과거 관측의 추가 정보:** step 1에서는 초기 범주가 알려져 있으므로 pair60과
   endpoint60이 수치 허용오차 안에서 같다. Step 2..16의 매 시점에서는 54/54 probe에서
   `trace(G_pair60 - G_endpoint60) > 5e-9`다. 이 양성 기준과 행렬의 양의 준정부호
   판정은 구별한다. Trace 양성은 모든 효능 방향에서 엄격한 증가를 뜻하지 않는다.
2. **현재 해상도와 이력의 비교:** step 1에서는 refined endpoint가 54/54에서 우세하고,
   step 2에서는 54/54에서 차이 행렬이 indefinite다. Step 16에서는 pair60 우위가
   1/54, 양·음 방향이 함께 있는 경우가 53/54다. 보편적인 관측 순서는 없다.
3. **기록 창의 시간 변화:** 모든 54개 probe에서 pair60 Fisher가 시간에 따라 감소하는
   방향이 한 번 이상 있다. 같은 시점에 직전 관측을 추가하는 이득과 이동 창의 시간
   단조성은 서로 다른 명제다. 누적 full path의 증가 조건과 혼동하지 않는다.
4. **Rank와 양:** 세 구조 좌표의 미래 rank가 2인 셀 36개는 모두 step 1의 세 TBC
   범주 × 두 초기분포 × 여섯 관측이다. Step 2..16은 모든 관측에서 rank 3이다.
   이는 선택한 세 좌표의 수치 rank이며 정보의 크기·모든 연결의 식별성을 뜻하지 않는다.

초기분포별 수치와 범주별 값은 [기계 판독 summary](../verify/MaleCNS/history_fisher_summary.json)에
있다. Trace와 그 비는 현재 세 log-efficacy 좌표와 좌표 스케일에서만 해석한다.
매개변수 재표현에 불변인 기억량·정보 비율이나 독립 개체의 신뢰구간으로 읽지 않는다.

Step 16에서 각 초기분포의 27개 범주를 요약하면 다음과 같다. 표의 비는 범주별로
먼저 계산한 뒤 요약했으며, trace 중앙값끼리 나눈 비가 아니다.

| 초기분포 | endpoint60 / pair60 trace 비: 최소·중앙·최대 | pair60 / full-path trace 비: 최소·중앙·최대 | 추가 정보 양성 |
|---|---|---|---|
| 균등 | `0.596790 / 0.718947 / 0.893312` | `0.000571586 / 0.002081487 / 0.018249154` | 27/27 |
| outgoing 접촉수 가중 | `0.605891 / 0.689637 / 0.906102` | `0.000320110 / 0.002227502 / 0.009751653` | 27/27 |

전체 54개 probe의 추가 trace 최소·중앙·최대는
`0.00010085320875610063 / 0.0003399783454543683 / 0.004419442124809608`이다.
인접 관측쌍의 trace가 full path에 비해 작다는 관측은 과거의 raw 경로 전체를 저장하는
비교 상한과 현재 두 범주만 저장하는 관측의 차이다. 같은 저장 예산의 압축률은 아니다.

## 산출물과 재현 범위

자료 ID `malecns-analysis`의 `history-fisher-v1`에 결과·배열·소스·검사 4개,
`history-fisher-companion-v1`에 생성기·notebook·HTML·summary·PNG 4개, 합계 12개를
[파일 원장](data_registry.jsonl)에 등록했다. 원자료는 재다운로드하지 않았다.

| 산출물 | SHA-256 |
|---|---|
| `history_fisher_result.json` | `a825d15ee161145dda6fa6d7b40f5e9eaca2e128be977333d1486cc3541ab58e` |
| `history_fisher_arrays.npz` | `2408e1b1bf23ae35f0dbde33f7647953e70440b6f1b4f63dceeaa58e1372fc65` |
| `history_fisher_summary.json` | `afd7671789b61cfb00543da38b6744c59ce2472e8499a95f43a71f9ff18479dd` |
| `history_fisher_companion.ipynb` | `fc812e53ca5ecf6d289fdf5b6864e7a88f34f4b9fdf919649ea5ee04959b6a29` |
| `history_fisher_companion.html` | `d281c1522be3167c7a6d7aa1c8336ba882b59b3ef221f456f593c056e8bf2f75` |

배열은 `data/local/malecns-analysis/history-fisher-v1/`에 있다.
[실행 notebook](../verify/MaleCNS/history_fisher_companion.ipynb)은 총 11셀 중 코드 5셀을
위에서 아래로 실행해 오류 0, 실행 번호 1..5, nbformat 검증 통과다.
[HTML 읽기본](../verify/MaleCNS/history_fisher_companion.html)의 내장 PNG 4개와 notebook의
내장 PNG, 외부 그림의 바이트가 대응한다. 외부 그림 4개의 축·범주·범례·잘림은 실제
이미지로 검수했다. 전체 HTML의 브라우저 레이아웃은 검수하지 않았다.

생성기는 기존 출력 덮어쓰기를 거부한다. 아래는 최초 생성 명령의 기록이며, 현재
완료 파일을 지우고 반복 실행하라는 지시가 아니다. 별도 재현은 입력 정체성과 새 출력
위치를 명시한 뒤 수행한다.

```powershell
$env:CE_PYTHON_WRAPPER = 'C:\dev\ce\ce-agi-runtime-repro-fffd356\.codex\hooks\python.cmd'
& $env:CE_PYTHON_WRAPPER python verify/MaleCNS/build_history_fisher_notebook.py
```

## 해석과 다음 진행 조건

현재 source·초기화·관측을 고정한 접촉 기반 확률 모형의 `BIO_EVIDENCE_L0` 연구다.
이력 정보가 늘거나 rank가 커져도 생물학적 기억·학습·가소성·신경 시간·물리공간 계량을
확인한 것이 아니다. 모든 coarse history, 같은 예산 확률 보존 축약, 새 입력·대안 경계,
실제 ROI·기능 관측의 요구는 보존한다.

특히 분석가가 두 시점을 보관해서 얻는 정보는 신경계 내부에 학습된 흔적이 있다는
증거가 아니다. 다음 기능 자료는 같은 단위의 활동 순서와 이후 반응을 결합하고,
정적 효능·현재 입력만의 모형과 이력 의존 효능 모형을 보류 자료에서 구별해야 한다.
정규화된 경로만으로 source별 절대 효능을 복구할 수 없으므로, 전기적 해석에는 반응의
절대 크기·물리 시간·입출력 측정모형이 추가로 필요하다. 수학적 확률 보존 축약과
생물 측정 교정은 이 두 질문을 각각 충족해야 하며 어느 하나로 나머지를 대신하지 않는다.

### 보유 생물 자료와 연결할 때의 선행 조건

2026-09-19에 데이터 원장과 관련 코드·계약·결과를 읽어 다음 경로를 재확인했다.
이 검토는 기존 결과를 재해석하는 연결 작업이며 새 적합·다운로드가 아니다. MaleCNS와
Allen/Xie는 같은 개체나 준비가 아니므로 샘플을 합치거나 동일 기전의 증거로 더하지 않는다.

| 보유 경로 | 이미 확인된 범위 | 다음 계산 전에 해결할 점 |
|---|---|---|
| Allen 실험 `1630015960.701`, [발화이력 보류예측 원장](../paper/검증_원장/고정뉴런_발화이력_보류예측.md), [mode별 결과](../verify/Q-NPF-04/fixed_points_metric/allen_ap_history_modes_result.json) | pair 121538의 유효 train/시간/주파수 보류는 16/17/5. 50Hz 시간 보류의 depression RMSE 0.106537 mV는 zero 0.107699, constant 0.106665보다 조금 낮음 | 20Hz에서는 depression 0.207586, facilitation 0.207568 mV가 zero 0.204951보다 나빠 전이 필요조건 실패. pair 121566은 9/2/0으로 부족. 일반적인 이력 법칙·STP 기전·전도도 확인으로 승격하지 않음 |
| Allen 실험 `1574292898.139`, [회복반응 원장](../paper/검증_원장/Q_NPF_04_Allen_반복자극_회복반응.md), [기존 대응 결과](../verify/Q-NPF-04/allen_synphys/recovery_train_responses_result.json) | 같은 paired connection의 12-pulse, 240 command-response 대응과 기술값. 원자료 재사용 가능 | 보류 적합은 아직 없음. 126.51ms 회복 간격 하나, 앞 반응의 기준창 혼입과 두 표적 대비의 비독립성 때문에 개별 파형·자극 전 잔여 성분부터 교정해야 함 |
| Xie ICMS93, [기존 post-train 결과](../verify/Q-NPF-04/allen_synphys/icms93_posttrain_v2_result.json) | 자극 train 전후 unit firing과 catch 비교 | 개별 시냅스 효능 측정이 아니며 단일 탐색 session. 원장에는 폴더 위치만 등록돼 있어 NWB 개별 파일의 정체성 확인도 선행해야 함 |

이번에 확인한 후보 중에는 같은 식별 시냅스의 활동 이력과 장기 가소성 유도 전후
효능을 함께 판별할 자료가 없었다. 그렇다고 보유 자료가 모든 질문에 부적격한 것은
아니다. Allen의 짧은 이력 반응에서는 **측정모형을 먼저 교정한 뒤 시간·주파수 보류를
분리하는 질문**이 남는다. 직접 주입·clamp mode·작동점·숨은 입력을 확인하고, 같은
현재 입력에서 과거에 따라 달라지는 새 반응과 단순 파형 중첩을 구별해야 한다.
그 후에도 장기 학습, 출력 Fisher의 변화와 독립 전류 비용의 변화는 별도 관측이 필요하다.

2026-09-19 후속 [Allen 파형 비교](allen_recovery_waveform_findings.md)는 위 표의
`1574292898.139`에 대한 적합 제외 예측을 실제로 수행했다. 공통 오프셋을 허용한
양성 표적의 약화 후보는 개선됐지만, 오프셋을 0으로 고정하면 회복 우위가 사라졌다.
고정 커널의 위상도 작은 학습 오차 차이 안에서 넓게 달랐다. 기존 표는 당시의
입구 재고이며 후속 완료·한계는 새 원장을 따른다. 이 결과는 MaleCNS의 관측 이력을
실제 내부 가소성으로 연결하는 근거를 확정하지 않는다.
