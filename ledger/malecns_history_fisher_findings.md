# MaleCNS 끝점·직전 관측쌍·전체 경로의 효능 정보

문서 유형: 개발 분석 원장. 시작일: 2026-09-15. 현재 상태: 관련 검사 통과·전량 계산 중.
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
승인된 기본 Python 3.11.9 실행기로 관련 검사 **7개가 1.85초에 통과**했고 Sol의 독립
읽기 리뷰에서 차단 결함은 없었다. 전량 실행은 별도 승인 Python 3.11.15에서 진행 중이며,
프로세스 생존이나 부분 로그를 완료 결과로 세지 않는다.
전량 확률·미분 질량·양 축 marginal 재현의 허용오차는 `5e-9`다. 고유값 검사는
`min_eigenvalue/max(1,max_abs_eigenvalue) >= -5e-9`이며 clipping·ridge를 쓰지 않는다.
rank 기준은 이전과 같은 `eigenvalue > 1e-10*max(1,largest_eigenvalue)`다.

전량 독립 비선형 차분은 모든 54개 초기분포·3,600개 관측쌍·0..16 step에서 세 구조
좌표와 `h=1e-4,5e-5`를 비교한다. 최대 절대오차 `1e-6` 이하와 성분별
`error/(1e-8+1e-4*abs(analytic)) <= 1`을 함께 요구한다. 결과가 나오기 전에 기준을
바꾸지 않는다. full-path Fisher의 독립 검산은 작은 경로 완전 열거이며 거대한 전체 raw
경로를 모두 열거하거나 전량 full-path finite difference를 실행했다는 뜻이 아니다.

현재 source·초기화·관측을 고정한 접촉 기반 확률 모형의 `BIO_EVIDENCE_L0` 연구다.
이력 정보가 늘거나 rank가 커져도 생물학적 기억·학습·가소성·신경 시간·물리공간 계량을
확인한 것이 아니다. 모든 coarse history, 같은 예산 확률 보존 축약, 새 입력·대안 경계,
실제 ROI·기능 관측의 요구는 보존한다.
