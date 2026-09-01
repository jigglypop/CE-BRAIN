# CE-NPF 대체 생물자료 D3 NDNF 복잡규칙 재학습 분석계약 v1

## 목표·이유·계보

- 계보: `ALT_BIO_D3_NDNF_COMPLEX_RELEARNING_v1`
- 최종 목표: 연결·가중치·지연의 가소성이 유효 표현기하를 바꾼다는 세부식을
  실제 생물자료로 제약한다.
- 이번 하위 목표: ALM layer 1 NDNF interneuron을 활성화해 apical dendritic
  integration을 억제했을 때, 같은 마우스의 rule-switch 오류 증가가 단순
  `A -> B`보다 복잡한 `B -> A'` 재학습에서 더 큰지만 시험한다.
- 필요한 이유: 이 결과는 `delta W`나 `delta g`를 직접 측정하지 않지만,
  plasticity update에 곱해지는 dendritic gate가 복잡한 재학습 행동에 필요한지
  판별해 세부식의 intervention-to-behavior 화살표를 제약한다.
- 논문이 이미 같은 방향을 보고했으므로 맹검 발견이나 독립 예측이 아니라,
  공개 raw per-mouse 자료에 완전히 적힌 새 source-locked 재분석이다.

## 입력 잠금과 분석 단위

- G-Node DOI: `10.12751/g-node.etlk5k`
- archive bytes: 483,324,456
- archive SHA-256:
  `b9962e7760ac7299cc968fa4a23d2c965342d78abdded4f937a4081588f09ba3`
- 독립 단위: mouse 10마리.
- mouse ID:
  `NWO1, NWO3, NWO4, NWO5, NWO6, NWO9, NWO10, NWO11, NWO12, NWO13`.
- 각 mouse의 `Control/<mouse>.mat`와 `Opto/<mouse>.mat`를 ID로 직접 pair한다.
- session 2는 `A -> B`, session 4는 `B -> A'`로 고정한다.
- 논문은 각 동물이 두 조건의 전체 paradigm을 무작위 순서로 수행했다고
  기술한다. 공개 파일에는 실제 condition order가 없으므로 period/carryover를
  조정하지 못하며 해석 상한으로 남긴다.

## 전체 선행 게이트

어떤 error endpoint도 계산하기 전에 다음을 전부 검사한다.

1. archive byte 수와 SHA-256가 잠금값과 같고 ZIP CRC가 전부 통과한다.
2. 두 condition에 정확히 위 10 mouse ID가 하나씩 있고 누락·추가가 없다.
3. 각 파일의 `cont_data`가 정확히 5 sessions이고 transition session에
   `Relearn`, `TrialTypes`, `Outcomes`, `DirOut`가 존재한다. `Relearn`과
   `DirOut`은 길이 `n`, `TrialTypes`와 `Outcomes`는 적어도 2열이고 행 수
   `n`으로 서로 맞아야 한다. `Outcomes[:,0]`은 outcome code이고 두 번째
   열은 시간이므로 endpoint에 쓰지 않는다.
4. `Relearn`의 unique set은 정확히 `A -> B`에서 old=`0`, new=`2`;
   `B -> A'`에서 old=`2`, new=`0`이다.
5. 아래 terminal-run switch를 포함한 뒤에 primary eligible trial과 고정
   민감도 eligible trial이 각각 20개 이상이다.
6. `TrialTypes[:,0]`은 0/1, `Outcomes[:,0]`은 -1/0/1/3,
   `DirOut`은 0/1/3 이외 값을 갖지 않는다. 공급자 코딩에서 `Outcomes`의
   -1은 impulsive, 0은 incorrect, 1은 correct, 3은 omission이다.

- archive·member 실패: `D3_SOURCE_BLOCKED`
- 구조·코딩·switch 실패: `D3_SCHEMA_BLOCKED`
- 20-trial 창 실패: `D3_BLOCKED_QUALITY`

게이트 실패는 생물학적 음성이 아니며 어떤 mouse endpoint도 출력하지 않는다.

## switch와 trial 선택

mouse `m`, condition `c`, transition `t`의 `Relearn` 값을 `r_q`라 하고 기대한
new-rule 값을 `r_t^new`라 한다. switch trial은

\[
s^*_{mct}=1+\max\{q:r_q\ne r_t^{new}\}
\]

로 정의한다. 즉, new rule 값이 시작된 뒤 session 끝까지 유지되는 terminal
run의 첫 trial이며 `s^*` 자체를 post-switch 창에 포함한다. 위 식의 trial
번호는 1부터 센다. switch 전에는 기대한 old-rule 값이 적어도 한 번 있어야
한다. 이 규칙은 `NWO12/Control/A->B`의 짧은 `0->2->0` 표지 예외에도 다른
strata와 동일하게 적용한다. 공급자 정렬자료의 “switch moment 다음부터
post-switch” 표기와 raw `Relearn` 상태값을 혼합하지 않고, 이 분석은 raw
상태값의 terminal new-rule run만 정본으로 쓴다.

주분석 후보는 시간순으로

\[
\mathcal R_{mct}=\{q\ge s^*_{mct}:TrialTypes_{q,0}=0,
\ Outcomes_{q,0}\in\{0,1\}\}
\]

이고 첫 20개만 쓴다. `TrialTypes[:,0]=0`은 right instruction이며, 논문상 두
rule switch에서 association이 바뀌는 쪽이다. `Outcomes[:,0]=-1` impulsive와
`3` omission을 제외하고, 완전 코딩된 `Outcomes[:,0]` 자체를 오류 정본으로
쓴다. 공개 README는 `DirOut`을 binary performance라고 설명하지만 실제 raw에는
0/1/3이 있고 valid `Outcomes` 행에서도 두 필드가 드물게 불일치한다. 더구나
relearning 파생치 생성 helper가 공개되지 않아 `DirOut`의 의미를 재현할 수
없으므로 주 endpoint에는 쓰지 않는다. 20은 공급자 Figure 1의
20-trial moving-average block에서 길이만 빌려 사전 고정한 값이며, 이 endpoint는
공급자의 moving-average나 공개되지 않은 `Relearn_ErrorPerTrials` 구현과 같다고
주장하지 않는다.

## mouse별 endpoint와 주효과

wrong-direction error rate를

\[
e_{mct}=\frac1{20}\sum_{q\in first20(\mathcal R_{mct})}
(1-Outcomes_{q,0})
\]

로 둔다. 각 transition의 paired optogenetic effect와 복잡도 interaction은

\[
d_{m,t}=e_{m,Opto,t}-e_{m,Control,t},
\]

\[
D_m=d_{m,BA}-d_{m,AB}
\]

이다. `D_m>0`은 NDNF activation에 따른 오류 증가가 simple `A -> B`보다
complex `B -> A'`에서 더 큼을 뜻한다. 주통계량은

\[
T_{obs}=\frac1{10}\sum_{m=1}^{10}D_m
\]

이다.

## exact null과 판정

논문이 보고한 mouse별 condition random order와 sharp no-treatment-effect
귀무 아래에서 10개 paired interaction의 부호를 전부 뒤집는 `2^10=1024`
경우를 열거한다.

\[
p_{exact}=2^{-10}\sum_{s\in\{-1,+1\}^{10}}
\mathbf 1\left[\frac1{10}\sum_m s_mD_m\ge T_{obs}\right].
\]

이는 평균 interaction의 sharp-null randomization statistic이다. 실제 order
변수가 없고 반복 paradigm의 carryover가 배제되지 않았으므로 모집단 평균의
무조건적 인과검정으로 확대하지 않는다.

검정은 `H_1:T_{obs}>0`인 단측, `alpha=0.05`로 고정한다. 결측 mouse가 하나라도
생기면 검정하지 않고 게이트 실패로 처리한다. `D_m=0`도 제거하지 않으며 완전열거
안에서 `+0`과 `-0` 두 부호 배정이 각각 한 경우로 세어진다. 평균 이외의 통계량,
다른 창 또는 양측 p값으로 판정을 다시 맞추지 않는다.

- `D3_NDNF_COMPLEX_RELEARNING_SPECIFIC_IMPAIRMENT_SUPPORTED`:
  모든 게이트 통과, `T_obs>0`, `p_exact<0.05`,
  `mean_m(d_{m,BA})>0`, 아래 omission-inclusive interaction도 양수.
- `D3_NDNF_COMPLEX_RELEARNING_SPECIFIC_IMPAIRMENT_NOT_SUPPORTED`:
  게이트는 통과했지만 위 결합조건 중 하나 이상 실패.

mouse별 `e`, `d`, `D`, `median(D)`, 양성 mouse 수를 전부 보고한다. 다른 창,
trial 수, rank test 또는 outlier 제외로 주판정을 바꾸지 않는다.

## 고정 민감도와 기술 대조

omission-inclusive 민감도에서는 impulsive만 제외한 switch 뒤 첫 20개
right-instruction trial을 고르고 `Outcomes[:,0]!=1`을 error로 센다.

\[
\tilde e_{mct}=\frac1{20}\sum_{q\in first20(\tilde{\mathcal R}_{mct})}
\mathbf1(Outcomes_{q,0}\ne1),
\]
\[
\tilde{\mathcal R}_{mct}=\{q\ge s^*:TrialTypes_{q,0}=0,
\ Outcomes_{q,0}\ne-1\}.
\]

같은 식으로 `tilde D_m`와 `mean(tilde D)`를 계산한다. 그 방향이 양수인 것은
주판정 필요조건이지만 별도 p값으로 판정을 구제하지 않는다. `d_AB`, `d_BA`,
condition-transition별 post-switch right-trial omission 비율과 impulsive 비율은
단순 운동·참여 저하 가능성을 보는 기술 대조다. primary는 valid trial 20개를
채우고 민감도는 non-impulsive trial 20개를 채우므로, 두 창이 달라질 수 있음을
명시하고 서로 같은 trial-position window라고 부르지 않는다. 모든 transition
session의 `(Outcomes[:,0], DirOut)` 교차표도 source QC로 출력하되, `DirOut` 기반
재판정이나 결과 구제에는 쓰지 않는다.

## 세부식에 주는 제약

학습 오차 신호를 `delta_t`, presynaptic eligibility를 `x_j(t)`, postsynaptic
state를 `y_i(t)`, NDNF activity를 `n_i(t)`라 할 때 시험할 수 있는 최소
plasticity-gate 모형은

\[
\dot W_{ij}(t)=\eta\,G_i(t)\,\delta_t\,x_j(t)y_i(t)-\lambda W_{ij}(t),
\qquad
G_i(t)=\sigma(a_i(t)-\beta n_i(t)),\quad\beta>0
\]

이다. NDNF activation은 `n_i`를 올려 `G_i`를 낮추는 intervention으로
해석한다. 양성 행동 interaction은 complex relearning에서
`partial(error)/partial n_NDNF>0`인 좁은 제약과 양립하지만 `dot W`를 직접
관측한 것은 아니다.

기존 유효계량 식

\[
g_\eta(z)=J_{F_\eta}(z)^\top\Sigma_\eta^{-1}J_{F_\eta}(z),
\qquad \eta=(A,W,\tau)
\]

과 연결하려면 같은 동물에서 `delta W` 또는 `delta tau`, 독립 population
output과 행동을 공동 측정해야 한다. 이번 자료의 행동 cohort를 별도 Figure
2--5 cohort와 합쳐 `NDNF -> delta W -> delta g -> behavior` 매개로 만들지
않는다.

## 해석 상한과 실행 잠금

- 이 endpoint는 청소년기 의미 고정, synaptic weight 변화, 전도속도, 물리적
  공간 접힘이나 리만계량을 직접 판정하지 않는다.
- 논문의 selective NDNF intervention·paired control은 기전 해석을 강화하지만,
  공개 source에는 mouse별 order, trial laser flag, 같은 동물의 dendritic
  manipulation check, rescue, 독립 holdout이 없다.
- `B -> A'`는 항상 session 4이고 `A -> B`는 항상 session 2이므로, 이 자료만으로
  규칙 복잡도와 transition 순서·재학습 시점을 분리하지 못한다.
- 따라서 이 재분석의 증거 상한은 범위고정 source-locked 구성요소 결과이며,
  통합 CE-NPF 사슬은 `BIO_EVIDENCE_L0 / BIOLOGICAL_MEDIATION_UNTESTED`다.
- 실행환경은
  `C:\Users\dongh\AppData\Local\Programs\Python\Python311\python.exe`,
  Python 3.11.9, NumPy 2.4.6, SciPy 1.17.1로 잠근다.
- 계약·runner·test hash, archive hash, interpreter·dependency 판본을 source
  lock에 기록하고 합성 test와 독립 감사 PASS 뒤 실제 endpoint를 정확히 한
  번 실행한다.
