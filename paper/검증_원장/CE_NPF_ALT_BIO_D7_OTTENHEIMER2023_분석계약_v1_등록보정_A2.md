# D7 Ottenheimer 분석계약 v1 사전 등록·시간축 보정 A2

## 보정 지위와 안전 정지 영수증

- 기준: base contract + `사전스키마보정_A1`.
- 최종 결합 계약 ID:
  `ALT_BIO_D7_OTTENHEIMER_SAME_CELL_ANCHOR_PLASTICITY_v1+A1+A2`.
- 보정 시점: `spks` 값, cue 반응 서명, A/P/B mouse statistic, p-value를 계산하거나 보지
  않은 registration-only 단계.
- 발견: 원래 5 px/2 px/80% 규칙은 공개 수동좌표의 정상 분포와 맞지 않아 5 mice를
  endpoint 전에 탈락시켰고, PL08의 수동 mask 한 열에는 객관적인 panel-order 오류가
  있었다. 또 한 session의 `frameTimes`에는 장시간 단절이 있었다.
- 조치: 결과 해석을 중단한 채 아래 최소 보정을 먼저 고정한다. 신경 공동주요 endpoint
  A/P의 정의·방향·alpha는 바꾸지 않고, 행동 해석 자격은 A2-6의 late discrimination
  IUT gate로 강화한다.

이 문서는 base와 A1 위에 덧붙인다. 등록 hard gate, 등록 sensitivities, 시간축 연속성에
충돌이 있으면 A2가 우선한다.

## A2-1. 객관적 out-of-FOV mask 열

24개 session mask의 모든 열을 활동과 무관하게 검사했을 때, `[0,511]^2` 밖 좌표는
1-based `PL08 column 10` 하나의 triplet에만 있었다.

- `o1d1`: `(x,y)=(1400,50)`
- `o1d3`: `(x,y)=(-665,36)`

공식 base mask에서 이 열만 세 panel 순서가 `[2,1,0]`으로 뒤집혀 있고 나머지 모든 열은
`[0,1,2]`였다. primary는 값을 추측해 고치지 않고 이 한 triplet을 세 날짜 모두에서
제외한다. 다음 hard gate를 적용한다.

1. non-finite mask coordinate는 없어야 한다.
2. out-of-FOV set은 정확히 `{(PL08, zero-based k=9)}`여야 한다.
3. 다른 out-of-FOV 열이 생기거나 알려진 열이 달라지면 `D7_SCHEMA_BLOCKED`다.

## A2-2. 활동-독립 보수적 primary 등록

`processROIs`는 A1-3의 정확한 duplicate 규칙과 수정된 네-edge 식을 쓴다. 각 session에서
유효한 수동좌표와 모든 후보 `stat.med=(y,x)` 사이 거리행렬을 만들고 각 열의 최초
최근접 ROI를 고른다. 24개 session의 `ops.diameter`가 모두 12 px임을 확인했으므로,
사후 임의 픽셀값 대신 그 acquisition scale로 primary 거리문턱을 고정한다.

\[
d_1^2\le\frac{diameter^2}{2}=72
\quad(d_1\le 8.485281\ldots\ {\rm px}),
\qquad d_2-d_1\ge2\ {\rm px}.
\]

같은 session에서 둘 이상의 수동 열이 같은 최초 최근접 ROI를 가리키면 저자처럼 먼 열을
다음 후보로 강제 재배정하지 않고, 그 충돌에 참여한 열 모두를 triplet 전체에서 제외한다.
충돌군은 distance·margin 통과 여부를 적용하기 전 모든 구조적으로 유효한 수동 열의 최초
최근접으로 먼저 계산한다.
세 session 중 한 번이라도 충돌하면 세 날짜 모두 제외한다. 활동값은 어떤 단계에도 쓰지
않는다.

이 규칙의 사전 등록-only 예상 보존수는 다음과 같으며 exact shape lock으로 쓴다.

| mouse | 원래 열 | primary 보존 triplet |
|---|---:|---:|
| PL01 | 55 | 54 |
| PL02 | 55 | 52 |
| PL03 | 33 | 33 |
| PL08 | 20 | 17 |
| PL10 | 40 | 35 |
| PL11 | 64 | 62 |
| PL15 | 39 | 38 |
| PL16 | 65 | 63 |
| 합계 | 371 | 354 |

mouse별 80%와 최소 15 gate는 그대로 유지하며 모두 통과해야 한다. 실제 결과가 위 exact
count와 다르면 endpoint를 열지 않고 `D7_REGISTRATION_SCHEMA_BLOCKED`다.

임의의 5 px 문턱은 폐기한다. no-distance audit의 366 triplet·1,098개 session
mapping에서 최근접 거리의
`min/median/p90/p95/p99/max`가 약
`0/2.236/5.099/6.083/8.062/11.662 px`였기 때문에 5 px는 저자 수동좌표 분포의
상위 약 10%를 구조적 근거 없이 자른다. 최종 primary는 자료 안의 ROI diameter를
사용하고 모호한 최근접을 막기 위해 `d2-d1>=2 px`도 유지한다.

## A2-3. 등록 sensitivities

다음은 primary를 구제하지 않는 고정 sensitivity다.

1. `STRICT_5PX_2PX`: 알려진 OOB를 제외하고 `d1<=5 px`, `d2-d1>=2 px`, 최초 최근접
   충돌 참여 열 전부 제외를 적용한다. 각 mouse에 최소 6개가 남아야 계산하며, 그렇지
   않으면 unavailable로 기록한다.
2. `NO_DISTANCE_MARGIN`: 알려진 OOB만 제외하고 최초 최근접 충돌 참여 열을 전부 제외한다.
   예상 보존수는 `55,53,33,19,38,64,39,65`, 총 366이다.
3. `AUTHOR_GREEDY`: 알려진 OOB만 제외한 뒤 저자 `imagingAcquisition.m:975-1013`의
   order-dependent collision rerouting을 그대로 재현한다. 예상 총수는 370이며 reroute는
   PL02 d1 한 열과 PL10 d1/d2 두 열이다. 최대 reroute 거리는 56.73 px까지 갈 수 있어
   primary가 아니라 기술 sensitivity다.
4. `AUTHOR_EDGE_TYPO`: primary의 diameter/margin/collision 규칙을 유지하되 저자 원문의 x-right-edge
   오타를 사용한다. 이 archive에서는 24/24 session의 candidate와 최초 최근접 mapping이
   수정판과 동일해야 한다.

primary 공동주요가 통과해도 `STRICT_5PX_2PX`, `NO_DISTANCE_MARGIN`, `AUTHOR_GREEDY`,
`AUTHOR_EDGE_TYPO` 또는 기존 local-spatial A의 8-mouse mean 방향이 0 이하이거나
계산 불가능하면
`D7_REGISTRATION_OR_LOCAL_TUNING_SENSITIVE`로 강등한다. sensitivity로 primary 실패를
구제하지 않는다.

## A2-4. frame-time 단절과 causal smoothing

median interval만 보는 base gate를 다음으로 강화한다. 각 session의
`d_k=frameTimes[k+1]-frameTimes[k]`, median `d_tilde`에 대해

\[
0.5\tilde d\le d_k\le1.5\tilde d
\]

를 벗어나는 곳을 segment break로 정의한다. 공개 자료의 유일한 break는
`PL01/o1d2`, zero-based diff index `10149`, 약 `320.54020125 s`다.

causal half-normal은 전체 sample index에 한 번 적용하지 않고 각 연속 segment에서
분모를 다시 시작한다. 모든 cue에 대해 baseline `[u-1,u)`, sensitivity response
`[u,u+2.5)`, 그리고 baseline 첫 sample보다 앞선 최대 15-sample smoothing history가
하나의 segment 안에 있어야 한다. 그렇지 않으면 `D7_SCHEMA_BLOCKED`다. 공개 자료에서
단절 뒤 가장 가까운 cue도 약 19.07 s 떨어져 있어 이 gate는 endpoint를 선택하지 않는다.

## A2-5. 등록 후 표본수와 zero-norm 규칙

base의 `N_m`을 다음처럼 분리한다.

\[
N_m^{raw}=\text{원래 mask 열 수},\qquad
I_m=\text{세 날짜 primary 등록을 모두 통과한 열 집합},\qquad
n_m=|I_m|.
\]

80% gate의 분모는 `N_m^raw`다. population mean, rank 후보수, cell 평균·중앙값,
`C_ms`의 분모는 모두 `n_m`이다.

무반응은 접근 차단이 아니라 생물학적 0으로 처리한다.

- anchor의 날짜쌍에서 true cell signature의 두 norm 중 하나라도 정확히 0이면 그 cell-pair
  advantage `a_i^{st}=0`으로 둔다. zero signature와의 cosine은 0으로 저장하되 그 cell을
  양성 anchor로 만들지 않는다.
- plasticity의 두 interleaved fold 변화 중 하나 또는 둘의 norm이 정확히 0이면
  `c_is=0`으로 둔다.
- non-finite 값만 `D7_NUMERICAL_BLOCKED`다.

fold는 각 `(phase,cue)` 내부 시간순 `1,3,5,...`와 `2,4,6,...`의 서로 겹치지 않는
interleaved fold다. 무작위 독립표본이라는 뜻의 “독립 fold” 표현은 쓰지 않는다.

## A2-6. 행동 습득 자격과 exact 검정의 가정

base의 변화 contrast `B_m` 외에 A1 late phase의 절대 discrimination을

\[
D_m^{late}=(\bar L_{CS+}-\bar L_{CS-})_{late,A1}
\]

로 고정한다. `mean(B)>0`, `p_B<=0.05`와 함께 `mean(D^late)>0`,
`p_{late}<=0.05`가 모두 통과해야 “행동 습득이 관찰된 세션”이라는 자격을 준다. 각 성분이
모두 필요한 IUT gate이므로 각각 alpha 0.05를 쓴다. 양성이라도 신경 P와 행동 B의
mouse별 공변이나 인과를 검정한 것은 아니므로 최종 표현은 “같은 A1 cohort에서
differential licking 증가와 함께 관찰됐다”로 제한한다.

256개 mouse 부호를 전수 열거한 계산은 수치적으로 exact하지만, 관찰자료에서의 Type-I
해석은 mouse statistic의 영가설 분포가 부호대칭이라는 가정을 필요로 한다. 이 가정과
작은 `n=8`을 결과에 명시한다.

## A2-7. 저자 smoothing weight의 bit-level 정의

base의 연속 half-normal 식은 개념식으로 유지하되 실행 weight는 저자 MATLAB
`imagingAcquisition.m:177-184`의 선형보간을 정확히 따른다. 정규화상수는 분자·분모에서
상쇄되므로

\[
\tilde w_k=\exp[-\tfrac12(k/15)^2],\quad k=0,\ldots,50
\]

를 source grid `t_k=0.02k`에 놓고, `h=0,...,15`의 imaging grid `t_h=h/15`에서 1차
보간한 값을 `w_h`로 쓴다. direct continuous Gaussian 평가가 아니라 이 interpolated
weight를 source lock한다.

## 목표 복귀와 다음 게이트

- 원래 질문에 아직 답했는가: 아니다. 여기까지는 등록·시간축 준비다.
- 무엇이 반증됐는가: 5 px 절대거리를 생물학적 유효성 hard gate로 삼을 근거와, 모든 공개
  mask 열이 그대로 유효하다는 예상.
- 무엇이 살아 있는가: 354개 activity-blind, diameter-gated 동일세포 triplet에서 안정
  앵커와 학습 중 기능
  변화가 공존할 가능성.
- 다음 허용 행동: runner를 A2에 맞게 수정하고 synthetic test와 registration-only
  preflight에서 exact 354 count·유일 gap을 확인한 뒤, stable snapshot을 독립 감사한다.
  그 뒤에만 endpoint를 정확히 한 번 실행한다.
