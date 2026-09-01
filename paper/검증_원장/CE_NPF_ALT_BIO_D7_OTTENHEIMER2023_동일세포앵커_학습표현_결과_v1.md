# CE-NPF 대체 생물자료 D7 Ottenheimer 2023 동일세포 앵커·학습표현 결과 v1

## 판정

- 계약: `ALT_BIO_D7_OTTENHEIMER_SAME_CELL_ANCHOR_PLASTICITY_v1+A1+A2`
- 일회성 실행 판정: `D7_COMPONENT_CONJUNCTION_NOT_SUPPORTED`
- 범위: 성체 mouse prelimbic cortex(PL), 8 mice, A1--A3 세션, 활동값과 무관하게
  등록된 동일세포 triplet 354개.
- 증거 지위: 범위고정 `L1` 음성 결과. 통합 미시변수--계량--행동 사슬은 계속
  `BIO_EVIDENCE_L0 / BIOLOGICAL_MEDIATION_UNTESTED`다.

안정 동일세포 cue-response 앵커 $A$와 최초 세션 내 재현 변화 $P_0$는 각각
통과했지만, 그 변화가 A2/A3보다 A1에 더 큰지를 묻는 사전고정
$P_{\mathrm{specific}}$이 실패했다. 따라서 안정 앵커와 **A1 세션 특이적** 기능
변화의 공동주요 conjunction은 지지되지 않는다.

## 입력·실행 영수증

- 공식 원자료: Figshare file `37918065`, DOI
  `10.6084/m9.figshare.21365598.v1`.
- 원자료 ZIP: 3,723,747,863 bytes, MD5
  `6085f775f1ea3a85505c55aafaf242bb`, SHA-256
  `47ffe1933713f53be720d85023f75c6f487faa8ee39a46ad0af63e3801bc4bd9`.
- source lock: 2,189 bytes, SHA-256
  `49d10952c71f0cc16b795b49b5b2992be19f7c3938dd3046139e93f7250a0b50`.
- 잠긴 artifact: base 계약, A1, A2, runner, 19-test 회귀파일, 공식 ZIP, 저자
  code ZIP, 최종 preflight, Python 3.11.9, NumPy 2.4.6, SciPy 1.17.1의 11개
  canonical role.
- 최종 preflight: `D7_PREFLIGHT_PASS / ENDPOINT_NOT_RUN`, SHA-256
  `1ed7e5513afcf5c816674f3947c39d547ae582fbea87f601f9d1480d37bf2ee1`.
- 회귀검사: 19/19 통과.
- 결과 JSON: 170,962 bytes, SHA-256
  `7e3596b56f1fc725dd26226a8f2d3cd1e65d392bb76a65d3b83129e49ac251ad`.
- 실행 횟수: 위 정본 결과 경로에 1회. 다른 출력 이름으로 재실행하지 않는다.

## 사전고정 공동주요 결과

모든 p값은 mouse를 독립단위로 한 256개 부호배치 전수열거의 one-sided exact
값이다. Type-I 해석은 귀무에서 mouse statistic의 부호대칭이라는 가정과 작은
$n=8$에 의존한다.

| 성분 | mean | median/보조량 | 양성 mouse | exact p | pass |
|---|---:|---:|---:|---:|---|
| 동일세포 앵커 $A$ | 0.079628 | median 0.094771; pooled same-cell cosine median 0.512368 | 8/8 | 0.00390625 | yes |
| A1 내 재현 변화 $P_0$ | 0.087506 | median 0.070912 | 7/8 | 0.01171875 | yes |
| A1 특이 변화 $P_{\mathrm{specific}}$ | 0.016365 | median 0.021478 | 4/8 | 0.31640625 | **no** |
| early--late 행동변화 $B$ | 1.796328 | -- | 8/8 | 0.00390625 | yes |
| late $CS^+-CS^-$, $D^{late}$ | 3.364282 | -- | 8/8 | 0.00390625 | yes |

공동주요 판정은

\[
\mathrm{PASS}_{\mathrm{joint}}
=\mathrm{PASS}_{A}\land\mathrm{PASS}_{P_0}
\land\mathrm{PASS}_{P_{\mathrm{specific}}}
=1\land1\land0=0
\]

이다. 행동 IUT는 통과했지만 실패한 신경 공동주요 성분을 구제하지 않는다.

## mouse별 고정 통계량

| mouse | $A_m$ | $P_{0,m}$ | $P_{\mathrm{specific},m}$ | $B_m$ | $D_m^{late}$ |
|---|---:|---:|---:|---:|---:|
| PL01 | 0.138365 | 0.161858 | 0.117418 | 2.486731 | 3.934783 |
| PL02 | 0.091503 | -0.023474 | -0.118333 | 0.026389 | 1.092885 |
| PL03 | 0.005208 | 0.058854 | -0.009298 | 1.744855 | 2.695513 |
| PL08 | 0.031250 | 0.008177 | -0.102998 | 1.587152 | 1.884211 |
| PL10 | 0.098039 | 0.057480 | 0.052253 | 2.335185 | 4.721739 |
| PL11 | 0.112022 | 0.168671 | 0.086338 | 0.846144 | 4.337321 |
| PL15 | 0.045045 | 0.082969 | -0.025392 | 1.963158 | 4.763158 |
| PL16 | 0.115591 | 0.185510 | 0.130933 | 3.381008 | 3.484649 |

## 고정 민감도

등록·local 대조의 앵커 평균 방향은 모두 양수였다.

| sensitivity | $A$ mean | exact p |
|---|---:|---:|
| author edge typo | 0.079628 | 0.00390625 |
| strict 5 px/2 px | 0.068116 | 0.03125 |
| no distance/margin | 0.076530 | 0.01171875 |
| author greedy | 0.076697 | 0.01171875 |
| local spatial null | 0.083333 | 0.00390625 |

그러나 $P_{\mathrm{specific}}$은 2.5 s 창에서도 mean 0.015432,
$p=0.3046875$, first/last one-third에서도 mean 0.037814,
$p=0.1953125$로 비지지였다. raw unsmoothed 자료에서는 $P_0$ 자체도
mean 0.029374, $p=0.1015625$로 통과하지 않았다. 이 민감도들은 primary를
구제하거나 다시 판정하는 데 쓰지 않는다.

## 생물학적 해석 경계

이 자료가 허용하는 관찰은 다음과 같다.

1. 성체 PL에서 등록된 같은 세포의 상대적 cue-response signature에는 수일간
   유지되는 anchor 성분이 있었다.
2. A1 안에서 시간순 홀짝 interleaved folds로 재현되는 early--late 변화 성분은
   있었지만, 그 변화가 후기 A2/A3 세션보다 A1에 특이적이라는 사전고정 증거는
   없었다.
3. 같은 cohort에서 differential licking의 증가와 late discrimination은
   관찰됐다. 그러나 신경변화와 행동의 mouse-level 공변이나 인과 매개를 검정한
   것은 아니다.

따라서 “학습이 이 신경변화를 만들었다”, “뉴런의 의미가 고정됐다”, “연결·가중치·
전도속도가 리만공간을 접었다”는 결론은 금지한다. 이 자료는 $W,v,\tau$,
출력 Fisher field $g$, 또는 \(\Delta(A,W,\tau)\to\Delta g\to\Delta behavior\)
중 어느 것도 측정하지 않았다.

## 원래 질문에 대한 결론

- 원래 강한 H2인 “의미를 가지고 태어나 청소년기에 고정”: `NOT_TESTED`.
  성체 3-session 자료에는 출생·청소년기 관측이 없다.
- 재구성 H2R인 “안정한 세포별 anchor + session/context-dependent expression”:
  anchor 단독은 지지됐지만 사전고정 adult-PL conjunction은
  `D7_COMPONENT_CONJUNCTION_NOT_SUPPORTED`다.
- 확인적 지지에 실패한 것: 이 preparation과 estimator에서
  $A\land P_0\land P_{\mathrm{specific}}$의 사전고정 conjunction. 이는 모든 세포
  정체성이나 모든 성체 가소성을 반증하지 않으며, $P$ 실패는 가소성 0의 동등성
  증거도 아니다.
- 살아 있는 것: 안정 세포형·회로 scaffold와 문맥·세션 의존 표현을 분리하는
  약한 재구성, 그리고 독립 cohort에서의 발달 연령·맹검 registration·구조/지연/
  활동/행동 공동측정.
- 다음 허용 행동: 같은 자료에서 창·등록·세포선택·검정을 바꿔 구제하지 않는다.
  독립 cohort의 발달기--청소년기--성체 종단자료 또는 미시 연결·지연과
  output-relative metric을 함께 측정하는 무작위 개입·구제 설계만 허용한다.

## 계보

- [기준 계약](CE_NPF_ALT_BIO_D7_OTTENHEIMER2023_동일세포앵커_학습표현_분석계약_v1.md)
- [A1 스키마 보정](CE_NPF_ALT_BIO_D7_OTTENHEIMER2023_분석계약_v1_사전스키마보정_A1.md)
- [A2 등록·시간축 보정](CE_NPF_ALT_BIO_D7_OTTENHEIMER2023_분석계약_v1_등록보정_A2.md)
- [자료획득·무결성](CE_NPF_ALT_BIO_D7_OTTENHEIMER2023_자료획득_무결성결과.md)
- [source lock](../6_뇌/국소회로_상태다양체_흐름_대응/repro/ottenheimer_same_cell_anchor_plasticity_v1_execution_source_lock.tsv)
- [최종 preflight](../6_뇌/국소회로_상태다양체_흐름_대응/repro/ottenheimer_same_cell_anchor_plasticity_v1A2_preflight_final.json)
- [일회성 결과 JSON](../6_뇌/국소회로_상태다양체_흐름_대응/repro/ottenheimer_same_cell_anchor_plasticity_v1_result.json)
