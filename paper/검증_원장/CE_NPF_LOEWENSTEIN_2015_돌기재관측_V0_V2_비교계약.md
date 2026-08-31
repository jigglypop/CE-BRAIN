# CE-NPF Loewenstein 2015 돌기 재관측 V0–V2 비교계약

Status: **OUTCOME_COUNTS_SEEN / MODEL_FIT_UNSEEN / CONTRACT_SPEC_FROZEN /
IMPLEMENTATION_LOCK_PENDING / REAL_DATA_FIT_NOT_AUTHORIZED**

Claim ceiling: **WITHIN_PIPELINE_DESCRIPTIVE_PREDICTION_ONLY /
BIO_EVIDENCE_L0**

판본일: 2026-08-31

## 0. 최종 목표, 이번 단계, 이탈 방지

**최종 목표.** 발달 prior 위에서 연결·가중치·전도 지연의 변화가 국소
출력-상대 Riemann 계량을 어떻게 바꾸고 기능적 공간을 접는지, 생물학 자료가
허용하는 범위까지 세부식으로 닫는다.

**이번 하위 목표.** Loewenstein 2015 공개 종단표의 동일한 2,723개 관측구간에서
상수 baseline \(V_0\), first-catalog 경과시간 \(V_1\), z 관측과정 nuisance
\(V_{1Z}\), 현재 morphology \(V_2\)의 다음-session 재카탈로그 예측을
whole-cell holdout으로 비교한다.

**왜 필요한가.** 접촉 turnover 식을 실제 생물학 행자료에 연결하되, 검출과
진짜 소실을 분리하지 못하는 표에서 birth–death contact process나 Riemann
folding을 성급히 주장하지 않기 위해서다.

**목표 명료성과 이탈.** 목표는 명확하다. 이 계약은 구조 관측과정의 제한된
예측 비교일 뿐 \(\Delta\Theta\to\Delta g\), 전도속도, synaptic efficacy,
행동 매개를 판정하지 않는다. 양성 결과도 Stage 10이나
**BIO_EVIDENCE_L0**를 승격하지 않는다.

**다음 gate.** 실제 결과를 열기 전에 단일 Rust 수치코어, 얇은 PowerShell
wrapper와 strict execution lock을 구현하고 합성 fixture만으로 감사한다.
그 세 파일과 compiler·source·선행 receipt hash가 안정화되고 독립 감사에서
blocker와 major가 0일 때에만 별도 lock이
**real_data_fit_authorized=true**를 열 수 있다. 현재는 실제 fit을 금지한다.

## 1. 사전지식과 정본 입력

### 1.1 이 계약은 완전 blind preregistration이 아니다

원 논문의 결론, 전체·cell별 사건 수와 age별 사건 수는 이미 공개되어 있고
입력 사전검사에서 확인했다. 그러나 이 계약을 고정할 때 \(V_0\)–\(V_2\)의
계수, frailty, LOCO predictive score, model delta와 판정은 계산하거나 보지
않았다. 따라서 정확한 명칭은 **outcome-count-aware, model-fit-unseen locked
reanalysis**다. 확인적 독립복제나 endpoint-blind 시험으로 부르지 않는다.

### 1.2 content와 선행 gate

- [원 논문](https://doi.org/10.1523/JNEUROSCI.2917-14.2015)
- [저자 data dictionary](https://decision-making-lab.com/data/spines/spines.html)
- [입력 사전검사 결과](CE_NPF_LOEWENSTEIN_2015_SPINE_생존입력_사전검사_결과.md)
- [source-lock manifest](../6_뇌/국소회로_상태다양체_흐름_대응/repro/loewenstein_2015_spine_source_lock.tsv)

| 대상 | bytes | SHA-256 |
|---|---:|---|
| 저자 headerless CSV | 569,938 | \(2f6343606f62abb07b82491a71f0e4a4a898923d2bcf86aa4be8d596276d0062\) |
| 저자 HTML data dictionary | 4,850 | \(995bdb601f6ff71cd5877486dfdd0576db576c15effcc8c52db560eb523d9657\) |
| source-lock manifest | 921 | \(8209a09886b9322a02308f1dceff8d3805462c715135f79e28e1ab1e166b0630\) |
| source preflight auditor | — | \(a1b68ad6820055ba305058d7b5f646626df2842dd628a2401a95f785b4f600cc\) |
| source preflight receipt | — | \(2ce71a85cd25c5da3d26c74f14aeb6c2d23daafa7fe3485b77567ddce619f517\) |

선행 receipt의 판정은 **PARTIAL_MODEL_ELIGIBILITY**, source 의미는
**live_unversioned_host_content_identity_only**다. 장기 가용성과 명시적
license는 잠기지 않았다. source-column schema의 upstream 용어와 아래
생물학적 endpoint는 서로 다른 잠금이다.

### 1.3 생물학적 endpoint 상한

자료는 약 6개월령 성체 수컷 GFP-M 마우스 6마리의 청각피질 L5 pyramidal
neuron 8개, apical tuft에서 얻었다. 축방향 해상도 한계 때문에 측방 돌기를
선별했고 filopodia를 spine과 분리하지 않았다. 따라서 endpoint는 정확히

> 같은 표본·영상·저자 추적 pipeline에서 저자가 catalog한 측방 돌기가
> 4일 뒤 다음 session에 다시 catalog되는가

이다. 성숙 흥분성 spine, 기능성 synapse, 생물학적 birth/death, true age 또는
모든 contact slot의 endpoint가 아니다.

## 2. 공통 rowset과 사건 정의

복합 ID를 \(q=(c,d,s)\), session을 \(\ell\in\{1,\ldots,6\}\), 저자표에 행이
있음을 \(O_{q\ell}=1\)로 둔다. 첫 catalog session은

\[
f_q=\min\{\ell:O_{q\ell}=1\}
\]

이다. 공통 비교 row는

\[
\mathcal R
=\{(q,\ell):f_q\in\{2,3,4,5\},\
O_{q\ell}=1,\ \ell<6\}
\tag{C2015.1}
\]

로 고정한다. 사건은

\[
Y_{q\ell}=1-O_{q,\ell+1}
\tag{C2015.2}
\]

이며 \(Y=1\)은 다음-session **비카탈로그**다. first catalog는 biological
birth의 interval bound가 아니고 true-age 하한·상한도 주지 않는다.

Rust 코어는 preflight receipt의 집계를 입력으로 신뢰하지 않고 raw 13열에서
다음을 직접 재구축해야 한다.

- 정확히 8,699행 × 13열, cell 8, dendrite 48, 복합 ID 3,688
- 중복 \((c,d,s,\ell)\) 0, 내부 \(1\to0\to1\) gap 0
- \(\mathcal R\) 2,723구간, \(Y=1\) 1,459건
- 정렬 \((cell,dendrite,spine,session)\)
- canonical line \(cell|dendrite|spine|session|Y\)와 마지막 LF
- rowset SHA-256
  \(127bf184fe88cd04c727f39c719e7ee0931c6bd1264338bb1b9b30dfff38fcd4\)

모든 후보는 정확히 같은 \(\mathcal R\)와 8개 LOCO fold를 사용한다. 결측 제거,
imputation, winsorization, clipping, 사후 bin 병합은 금지한다.

알려진 support는 다음과 같다.

| first-catalog 뒤 경과 | 구간 | 비카탈로그 |
|---:|---:|---:|
| 0일 | 1,861 | 1,122 |
| 4일 | 557 | 249 |
| 8일 | 219 | 66 |
| 12일 | 86 | 22 |

| cell | 구간 | 비카탈로그 |
|---:|---:|---:|
| 1 | 529 | 321 |
| 2 | 151 | 72 |
| 3 | 404 | 201 |
| 4 | 433 | 231 |
| 5 | 419 | 229 |
| 6 | 401 | 202 |
| 7 | 353 | 185 |
| 8 | 33 | 18 |

어느 outer training fold에서든 네 age level, 각 level의 event와 non-event,
모든 설계열의 full rank가 없으면 bin을 바꾸지 않고
**STOP_DESIGN_OR_SEPARATION_FAIL**로 멈춘다.

## 3. 조건부 관측모형

일일 log hazard를

\[
\eta_i=x_i^\top\beta+u_c+v_{cd}
\]

로 두고 4일 exposure를 명시하면

\[
\xi_i=\log4+\eta_i,\qquad
\Lambda_i=e^{\xi_i}=4e^{\eta_i},\qquad
p_i=\Pr(Y_i=1\mid u_c,v_{cd},x_i)
=1-e^{-e^{\xi_i}}.
\tag{C2015.3}
\]

안정적인 조건부 log likelihood는

\[
\ell_i(\eta_i)
=Y_i\log\{-\operatorname{expm1}[-e^{\xi_i}]\}
-(1-Y_i)e^{\xi_i}.
\tag{C2015.4}
\]

사건을 midpoint나 exact jump로 만들지 않는다. 식 (C2015.4)는 4일 interval
event의 absorbing catalogued-state working likelihood다.

## 4. 고정 설계 \(V_0,V_1,V_{1Z},V_2\)

first-catalog 뒤 경과 bin을 \(a_i=\ell-f_q\in\{0,1,2,3\}\)으로 두고

\[
A_{ik}=\mathbf1\{a_i=k\},\qquad k=1,2,3
\tag{C2015.5}
\]

을 쓴다. 0일이 기준이다. 연속·단조 age curve, spline, interaction,
random slope와 feature selection은 금지한다.

형태·관측 열은

\[
r_i=\log I_i,\qquad
s_i=\frac{\lambda_{1i}-\lambda_{2i}}
{\lambda_{1i}+\lambda_{2i}},\qquad
d_i=\log D_i,\qquad z_i
\tag{C2015.6}
\]

다. \(I,D>0\)이어야 한다. 각 outer fold의 training rows에서만
\(r,s,d,z\)의 평균과 \(n-1\) sample SD를 계산하고

\[
x_i^*=\frac{x_i-\bar x_{\mathrm{train}}}
{s_{\mathrm{train}}}
\tag{C2015.7}
\]

를 heldout rows에 그대로 적용한다. SD가 \(10^{-12}\) 이하이거나 비유한 값이
있으면 멈춘다. heldout covariate도 scaler에 참여하지 않는다.

네 고정모형은

\[
\begin{aligned}
V_0:\quad \eta_i
&=\beta_0+u_c+v_{cd},\\
V_1:\quad \eta_i
&=\beta_0+\sum_{k=1}^3\gamma_kA_{ik}+u_c+v_{cd},\\
V_{1Z}:\quad \eta_i
&=\beta_0+\sum_{k=1}^3\gamma_kA_{ik}
+\beta_Zz_i^*+u_c+v_{cd},\\
V_2:\quad \eta_i
&=\beta_0+\sum_{k=1}^3\gamma_kA_{ik}
+\beta_Zz_i^*
+\beta_Ir_i^*+\beta_Ss_i^*+\beta_Dd_i^*
+u_c+v_{cd}.
\end{aligned}
\tag{C2015.8}
\]

\(V_{1Z}\)는 네 번째 생물가설이 아니라 z orientation/detection nuisance를
형태 increment에서 분리하는 감사 대조다. penalty, REML과 결과를 본
hyperparameter 선택은 쓰지 않는다.

## 5. nested frailty와 정확한 주변우도

\[
u_c\sim N(0,\sigma_u^2),\qquad
v_{cd}\stackrel{\mathrm{iid}}{\sim}N(0,\sigma_v^2),
\qquad u\perp v
\tag{C2015.9}
\]

로 둔다. cell \(c\), dendrite \(d\)의 row 집합을 \(I_{cd}\)라 하면

\[
A_{cd}(u;\theta)
=\int\phi_{\sigma_v}(v)
\exp\left\{\sum_{i\in I_{cd}}\ell_i(u,v)\right\}\,dv,
\tag{C2015.10}
\]

\[
L_c(\theta)
=\int\phi_{\sigma_u}(u)
\prod_{d\in D_c}A_{cd}(u;\theta)\,du.
\tag{C2015.11}
\]

heldout cell \(h\)의 training ML과 점수는

\[
\widehat\theta_{m,-h}
=\arg\max_\theta\sum_{c\ne h}\log L_c(\theta),
\qquad
\operatorname{NLPD}_{m,h}
=-\log L_h(\widehat\theta_{m,-h}).
\tag{C2015.12}
\]

heldout cell의 새 \(u_h\)는 cell 전체에서 한 번, 그 cell의 모든 새
\(v_{hd}\)는 dendrite별로 한 번씩 **공동 적분**한다. heldout outcome으로
BLUP/empirical Bayes update를 하거나 random effect를 0으로 plug-in하거나
행별 주변확률을 따로 적분해 log score를 더하지 않는다. 식 (C2015.12)는
모수 불확실성을 적분하지 않은 whole-cell joint **plug-in predictive score**다.
Bayesian posterior predictive라고 부르지 않는다.

### 5.1 분산의 정확한 경계 face

매 fold·모형에서

\[
(\sigma_u,\sigma_v)\in
\{(0,0),(+,0),(0,+),(+,+)\}
\tag{C2015.13}
\]

네 face를 모두 평가한다. 0인 차원은 quadrature에서 제거한다. 양의 성분은
\(\log\sigma\)로 최적화하고 \(10^{-6}\le\sigma\le10\)을 계산 guard로 둔다.
lower guard에 닿은 active face는 대응 0-face로 환원한다.

복잡 face의 training log-likelihood 이득이 가장 가까운 nested 0-face보다
\(10^{-8}\) nat/train-row 이하이면 더 단순한 face를 선택한다. 같은 복잡도의
비중첩 face가 그 tolerance 안에서 묶이면 결정 순서는
\((0,0),(+,0),(0,+),(+,+)\)다. \(\sigma=10\)에서 바깥 방향 score가 양수이면
cap 값을 보고하지 않고 **STOP_FRAILTY_UNIDENTIFIED**로 멈춘다. 분산 경계에
보통 \(\chi^2\) LRT나 Wald 해석을 적용하지 않는다.

## 6. deterministic nested adaptive Gauss–Hermite

inner log integrand를

\[
g_{cd}(v;u)
=\log\phi_{\sigma_v}(v)
+\sum_{i\in I_{cd}}\ell_i(u,v)
\]

라 한다. 유일 mode \(m\)와
\(s=[-g''_{cd}(m;u)]^{-1/2}\)를 찾으면 order \(Q\)의 AGHQ는

\[
\log A_{cd,Q}(u)
=\log(\sqrt2s)+
\operatorname{LSE}_{k=1}^Q
\left[
\log w_k+g_{cd}(m+\sqrt2sx_k;u)+x_k^2
\right].
\tag{C2015.14}
\]

outer

\[
G_c(u)=\log\phi_{\sigma_u}(u)
+\sum_{d\in D_c}\log A_{cd,Q}(u)
\tag{C2015.15}
\]

에도 같은 adaptive 공식을 적용한다.

필수 구현규칙은 다음과 같다.

- Gaussian 정규화상수를 포함한다.
- 모든 outer node에서 모든 inner mode와 integral을 다시 계산한다.
- outer mode는 joint conditional mode가 아니라 inner-marginal \(G_c\)에서 찾는다.
- 모든 합은 log-sum-exp, 사건항은 안정적인 expm1/log1p를 쓴다.
- heldout \(Y\)에 따른 adaptive centering은 적분좌표 선택이지 BLUP가 아니다.
- mode score와 relative step은 각각 \(10^{-10}\) 이하, 최대 50회다.
- mode의 second derivative는 유한한 음수이고, 그 음의 부호를 취한 curvature와
  반환 scale은 유한한 양수여야 한다.

수치 순서는 다음처럼 고정한다.

1. \(Q=15\): 모든 face를 고정 multistart로 최적화한다.
2. \(Q=25\): 각 \(Q=15\) 해에서 모든 face를 재최적화하고 최종 face를 고른다.
3. \(Q=35\): \(Q=25\) 최종모수의 training/heldout 적분을 고정모수 감사한다.
4. 25→35 감사가 실패할 때만 한 번 \(Q=35\) 재최적화, \(Q=45\) 고정모수
   감사를 허용한다. 다시 실패하면 전체 비교를 닫는다.

필수 수치 gate는

\[
\max_c\frac{
|\log L_{c,Q_2}(\widehat\theta)-\log L_{c,Q_1}(\widehat\theta)|
}{\max(1,n_c)}
\le10^{-6},
\tag{C2015.16}
\]

- 15→25 재최적화 pooled CV-NLPD 차이 \(\le10^{-5}\) nat/interval,
- scaled active-parameter 최대차
  \(\max_j|\theta_{25,j}-\theta_{15,j}|/(1+|\theta_{25,j}|)\le10^{-3}\),
- normalized training objective **score-quadrature gradient** infinity norm
  \(\le10^{-6}\),
- best three converged starts의 objective 차이 \(\le10^{-8}\) nat/train-row,
- active finite-difference Hessian condition number \(\le10^{10}\)

다. \(Q=15\)과 \(Q=25\)가 다른 variance face를 고르면, 추가 variance 이득이
식 (C2015.13)의 boundary tolerance 안이라 \(Q=25\)가 더 단순한 face를 고른
경우만 허용한다. 그 밖의 face 변경은 quadrature nonconvergence다. 한 항이라도
실패하면 winner나 delta를 내지 않는다.

### 6.1 optimizer 고정

full BFGS, score-quadrature gradient, Armijo \(c_1=10^{-4}\), step shrink
\(1/2\), 최대 400 iteration·5,000 objective evaluation을 쓴다. optimizer의
내부 projected-gradient 종료 문턱은 \(10^{-8}\)로 두되, 공개 수치 gate는
모든 선택해에 대해 더 느슨한 상한 \(10^{-6}\)을 별도로 적용한다.
fixed-effect guard는 \([-20,20]\)이며 닿으면 separation으로 정지한다.

내부 종료량과 공개량은 섞지 않는다. \(J_Q=-\ell_Q/n_{\rm train}\),
\(g_{\rm raw}=\nabla J_Q\), \(g_{\rm proj}=P_{\rm KKT}(g_{\rm raw})\)로 두고,
내부 종료에는 \(\lVert g_{\rm proj}\rVert_\infty\), 공개 gate에는
\(\lVert g_{\rm raw}\rVert_\infty\)를 쓴다. active \(\log\sigma\)가 상한에
있을 때 바깥쪽 likelihood score가 양수, 즉 \(g_{{\rm raw},j}<0\)이면 별도
tolerance로 덮지 않고 **STOP_FRAILTY_UNIDENTIFIED**로 닫는다.

여기서 score-quadrature gradient는 연속 적분의 Fisher/Louis score identity를
같은 \(Q\) posterior node·weight로 평가한 값이다. adaptive mode·scale에
의존하는 **유한-\(Q\) 근사식 자체의 정확한 미분**이라고 부르지 않는다.
따라서 BFGS 방향으로 쓰려면 항목 5의 사전 고정 finite-difference gate와
Q15→25 objective·모수 수렴 gate를 함께 통과해야 한다. 이 구분을 숨긴
exact finite-Q analytic gradient 표기는 금지한다.

training 사건비 \(\bar Y\)로

\[
\beta_0^{(0)}
=\log\{-\log(1-\bar Y)/4\}
\tag{C2015.17}
\]

를 만들고 네 start를 고정한다.

1. \(\beta_0^{(0)}\), 나머지 fixed effect 0, active \(\sigma=(0.1,0.1)\)
2. \(\beta_0^{(0)}-0.5\), 나머지 0, active \(\sigma=(0.5,0.5)\)
3. \(\beta_0^{(0)}+0.5\), 나머지 0, active \(\sigma=(1.5,0.25)\)
4. \(\beta_0^{(0)}\), nonintercept에 \(+0.05,-0.05,\ldots\), active
   \(\sigma=(0.25,1.5)\)

한 active variance face에서는 첫 active 값을 사용하고 없는 값은 제거한다.
최소 세 start가 수렴하고 best three가 위 tolerance로 합의해야 한다.

Q25 optimum에서 이 score-quadrature gradient의 5-point finite difference
Hessian을 대칭화하고 condition number를 계산한다. coefficient
SE·p-value·CI는 계산하지 않는다.

## 7. LOCO 점수와 비추론적 판정

primary와 secondary는

\[
S_m^{\mathrm{pooled}}
=\frac{\sum_{h=1}^8\operatorname{NLPD}_{m,h}}{2723},
\qquad
S_m^{\mathrm{macro}}
=\frac18\sum_{h=1}^8
\frac{\operatorname{NLPD}_{m,h}}{n_h}
\tag{C2015.18}
\]

다. cell별 \(S_{m,h}=\operatorname{NLPD}_{m,h}/n_h\)도 모두 기록한다.

직접 비교는 세 개뿐이다.

1. \(V_1-V_0\): first-catalog elapsed-level 예측
2. \(V_{1Z}-V_1\): z orientation/detection sensitivity
3. \(V_2-V_{1Z}\): morphology의 z-adjusted incremental prediction

\(V_2-V_0\)은 총 descriptive lift로 보조 보고할 수 있지만 귀속하지 않는다.
\(V_2-V_1\)은 morphology와 z가 섞이므로 morphology 근거로 금지한다.

reduced \(B\), augmented \(A\)에 대해

\[
\Delta_h=S_{B,h}-S_{A,h},\quad
\Delta_{\mathrm{pool}}=S_B^{\mathrm{pooled}}-S_A^{\mathrm{pooled}},\quad
\Delta_{\mathrm{macro}}=S_B^{\mathrm{macro}}-S_A^{\mathrm{macro}}
\tag{C2015.19}
\]

로 두어 양수가 augmented 개선이 되게 한다. exact zero와
\(|\Delta_h|\le10^{-12}\)는 sign count에서 0으로 센다.

\[
\epsilon=\log(1.01)=0.009950330853168092,\qquad
\kappa=\log(1.05)=0.04879016416943205.
\tag{C2015.20}
\]

**ROBUST_DESCRIPTIVE_GAIN**은 다음 AND다.

- \(\Delta_{\mathrm{pool}}\ge\epsilon\)
- \(\Delta_{\mathrm{macro}}\ge\epsilon/2\)
- \(\Delta_h>10^{-12}\)인 cell이 6/8 이상
- \(\min_h\Delta_h\ge-\kappa\)

**ROBUST_DESCRIPTIVE_LOSS**는 완전 대칭이다.

- \(\Delta_{\mathrm{pool}}\le-\epsilon\)
- \(\Delta_{\mathrm{macro}}\le-\epsilon/2\)
- \(\Delta_h<-10^{-12}\)인 cell이 6/8 이상
- \(\max_h\Delta_h\le\kappa\)

그 밖은 **DESCRIPTIVE_TIE_OR_MIXED**다. 이는 equivalence가 아니다. 각 비교는
방향을 섞지 않고 `gain_gate_vector`와 `loss_gate_vector`를 모두 남긴다. 각
vector는 **CELL_GUARD_FAIL**, **POOLED_MARGIN_FAIL**, **MACRO_MARGIN_FAIL**,
**SIGN_COUNT_FAIL** Boolean 네 개이며, 각각 위 gain·loss 네 조건의 부정이다.
gain vector가 모두 false면 gain, loss vector가 모두 false면 loss, 그 밖은
tie/mixed다. 선택되지 않은 방향의 vector도 삭제하지 않는다. 한 fold라도
support, finite score, optimizer 또는 quadrature gate를 실패하면 7개 fold만
평균내지 않고 **ESTIMATION_OR_SUPPORT_STOP / COMPARISON_NOT_EVALUABLE**로 닫는다.

문턱의 뜻은 효과크기 percent point가 아니다.

- pooled \(\log1.01\): 관측된 call에 부여한 interval별 확률의 기하평균비
  \(1.01\) 이상
- macro \(\tfrac12\log1.01\): cell 동일가중 기하평균비
  \(\sqrt{1.01}\) 이상
- 6/8: 8개 cell ID의 기술적 안정성 규칙이지 6 animals 또는 p-value가 아님
- worst-cell \(-\log1.05\): 어떤 cell도 기하평균 확률비가 \(1/1.05\)보다
  더 나빠지지 않는다는 pipeline guard

## 8. p-value와 CI를 만들지 않는 이유

8 cell이 6 mice에 어떻게 대응하는지 없어 독립 생물학 표본 단위를 복원할 수
없다. interval은 돌기–dendrite–cell–mouse에 중첩되고, 8 LOCO training set은
크게 겹친다. row/spine bootstrap, Wilks iid, exact sign/binomial
exchangeability와 cluster asymptotic을 정당화할 수 없다.

따라서 허용 보고는 pooled·macro·cell별 point score, 각 denominator와 네
decision Boolean뿐이다. coefficient/score p-value·CI, significant,
equivalent, independent replication이라는 표현은 금지한다.

## 9. 결과별 허용 문장과 금지 승격

- \(V_1>V_0\) gain: first-catalog elapsed level이 within-pipeline
  재카탈로그 예측을 개선했다. biological age·true birth·continuous
  stabilization은 말하지 않는다.
- \(V_{1Z}>V_1\) gain: z로 포착되는 orientation/detection process에
  민감하다. 생물학적 gain이 아니며 **OBSERVATION_PROCESS_SENSITIVE**를 붙인다.
- \(V_{1Z}\) tie/loss: z confounding 부재 증명이 아니다. z는 불완전 proxy이므로
  \(V_2\)에서 계속 nuisance로 둔다.
- \(V_2>V_{1Z}\) gain: current image morphology가 elapsed level과 measured-z
  이후 다음-session author recatalog call에 추가 prognostic information을
  준다. morphology가 persistence를 일으키거나 intensity가 weight/conductance라는
  뜻이 아니다.
- tie/loss: age/morphology biology의 반증이 아니라 이 pipeline의 사전고정
  robust gain 미확립 또는 descriptive predictive loss다.

세 비교가 모두 gain이어도
**WITHIN_PIPELINE_DESCRIPTIVE_PREDICTION_ONLY /
BIOLOGICAL_MECHANISM_UNTESTED**다. animal 일반화, mature-spine survival,
birth/death CTMC, true-age semi-Markov, mark PDMP, presynaptic parent,
conducting transition, efficacy/weight, myelin/speed, neural Riemann metric,
folding, 의미·행동·인과는 모두 닫힌다. 성체-only 표는 청소년기 고정이나
발달 prior를 판정하지 않는다.

## 10. 구현 전 합성 gate

실자료 path를 받을 수 없는 **self-test only** mode가 다음을 모두 통과해야 한다.

1. SHA-256 known vectors와 strict lock parser
2. GH node·weight 양성, 대칭, 합 1과 표준정규 moments
3. Gaussian-only integral 1
4. extreme \(\eta\) grid의 cloglog log1mexp와 analytic score
5. 전체 objective score-quadrature gradient 대 5-point finite difference
6. inner/outer score-quadrature score와 Louis-identity curvature finite difference
7. 한 dendrite nested 2D 대 \(N(0,\sigma_u^2+\sigma_v^2)\) 1D
8. 두 dendrite production factorization 대 brute-force 3D GH
9. 잘못된 row-wise frailty 적분이 fixture에서 분리됨
10. heldout outcome·covariate poison 뒤 training scaler·fit bitwise 불변
11. 네 variance boundary face
12. quadratic optimizer, multistart와 Hessian eigenvalue oracle
13. row·dendrite 순열 뒤 canonical design과 fitted result 불변
14. synthetic core receipt 두 번 byte-identical
15. fixed-key-order JSON golden string
16. 네 variance face의 Q15·Q25 자연 무-fallback 경로, 강제 Q35 재최적화·Q45
    감사 경로, 32-fold LOCO orchestration·집계, 비교 판정과 자연·강제
    production core renderer의 end-to-end 실행

이 목록의 “통과”를 구현 뒤에 임의로 정하지 않도록 다음 수치 계약을 먼저
고정한다. 두 값 \(a,b\)의 scaled error는
\[
E_{\mathrm{sc}}(a,b)
=\frac{|a-b|}{1+|a|+|b|}
\tag{C2015.21}
\]
이다. 모든 로그우도 차이는 natural-log 단위다.

- 항목 2: 네 quadrature order에서 raw weight-sum 최대 절대오차
  \(\le2\times10^{-13}\), 표준정규 moment 최대 절대오차
  \(\le5\times10^{-11}\), node·weight 대칭 최대 절대오차
  \(\le2\times10^{-13}\)이다. 모든 node·weight의 finite와 weight 양성은
  exact Boolean gate다.
- 항목 3: Gaussian-only 적분의 \(|\log \widehat I_{25}|\le2\times10^{-12}\).
- 항목 4: event \(0,1\), \(\eta=(-30,-12,-4,-1,0,2,5)\), 중앙차분
  \(h=10^{-5}\)에서 score와 second derivative 각각의 최대 절대오차
  \(\le2\times10^{-8}\).
- 항목 5: \(Q=35\), 각 모수의
  \(h_j=2\times10^{-4}(1+|\theta_j|)\)인 5-point stencil에서
  score-quadrature gradient 대 finite-difference gradient의
  \(\max_jE_{\mathrm{sc}}\le2\times10^{-6}\).
- 항목 6: 알려진 concave quadratic의 mode와 scale 절대오차
  \(\le2\times10^{-12}\). 별도로 production inner와 outer log-integrand의
  score-quadrature score와 Louis-identity curvature를 유한-\(Q\) 중앙차분
  \(h=10^{-5}(1+|z|)\)과 비교하여 score 최대 scaled error
  \(\le2\times10^{-7}\), curvature 최대 scaled error
  \(\le2\times10^{-6}\).
- 항목 7: \(Q=35\)에서 두 log integral 차이
  \(\le2\times10^{-9}\).
- 항목 8: production \(Q=25\)와 normalized fixed-node brute-force
  \(Q=25\) 3D GH의 log integral 차이 \(\le2\times10^{-8}\).
- 항목 9: 같은 fixture에서 잘못된 row-wise 값과 production 값의 차이
  \(\ge10^{-4}\).
- 항목 10과 13: 비교 대상 training scaler, training-only design hash,
  fitted parameter·objective·score-quadrature gradient와 canonical row/design
  bytes 또는 hash가 bitwise 동일해야 한다. gradient는 infinity norm만이 아니라
  fitted parameter에서 다시 평가한 전체 vector를 비교한다.
- 항목 11: 네 face의 값·gradient가 모두 finite여야 하며 lower guard의
  active face는 exact zero face로 환원되어야 한다.
- 항목 12: quadratic target의 모수 최대 절대오차
  \(\le2\times10^{-6}\), 네 start objective spread
  \(\le10^{-10}\), \(2\times2\) Hessian 고유값 oracle 최대 절대오차
  \(\le2\times10^{-12}\).
- 항목 14와 15는 UTF-8 bytes exact equality로 판정한다.
- 항목 16: 자연 경로는 Q25 최종모수의 Q35 cell delta가 \(10^{-6}\) 이하라
  재최적화 없이 닫혀야 한다. 강제 fixture는 같은 Q15·Q25 해에서 Q35를
  재최적화하고 Q45 cell delta \(\le10^{-6}\), Q25→Q35 active-parameter delta
  \(\le10^{-3}\), 최종 score-quadrature gradient infinity norm
  \(\le10^{-6}\)을 만족해야 한다. 선택해의 raw score-quadrature gradient
  infinity norm은 적합점에서 다시 계산해 \(\le10^{-6}\), 탐색한 모든 face의
  내부 projected-gradient infinity norm은 \(\le10^{-8}\)이어야 하며, 저장한 전체
  gradient vector·두 norm과 bitwise로 일치해야 한다. 별도의 8-cell
  비균등-denominator fixture는
  production과 같은 32-fold 생성·완전성·pooled/macro/per-cell 집계·Q15→Q25
  전역 gate·세 비교를 통과해야 한다. 양성 fixture의 최대 Q15→Q25 pooled
  score 차이는 \(\le10^{-5}\), 음성 fixture의 차이는 \(>10^{-5}\)여야 하고 후자는
  limit와 observed를 보존한 정확한 stop으로 닫혀야 한다. 이 네 수치량은 모두
  observed·limit·comparison·pass로 self-test receipt에 기록한다.
  수치 kernel은 앞의 실제 자연·강제 fit이, 32-fold orchestration은 결정론적
  injected fitter가 담당하되 둘은 같은 production orchestration 함수를 공유한다.
  자연 renderer는 fallback optional 값 `null`과 빈 진단 배열을, 강제 renderer는
  Q35 payload를 내며 각 경로를 두 번 그린 bytes가 각각 동일해야 한다. 두 renderer
  fixture는 실제 8-cell·104-row 비균등 synthetic dataset에서 각각 완전한 32-fold
  report를 새로 만들며, 다른 report의 fold를 끼워 넣거나 production row count를
  하드코딩하지 않는다. dataset summary와 report의 row·cell·fold 수가 다르면
  renderer가 정지한다.

각 최대 관측오차와 row-wise 분리량은 synthetic core receipt에 기록한다.
하나라도 비유한 값이면 tolerance 비교 전 즉시 실패한다. 이 문턱은
실자료 결과나 생물학적 효과 문턱이 아니라 구현·수치 감사 문턱이다.

실자료 path를 self-test mode에 주면 오히려
**STOP_REAL_DATA_FORBIDDEN_IN_SELF_TEST**로 닫는다.

## 11. 실행 잠금과 영수증 계약

구현은 한 개의 dependency-free Rust source와 통계 계산을 하지 않는 얇은
PowerShell wrapper로 제한한다. runtime은 single-thread로 고정한다. compiler는
Rust 1.95.0이며 정확한 flag는
**--edition=2021 -C opt-level=3 -C debuginfo=0 -C overflow-checks=yes
-C target-feature=-fma -C codegen-units=1**이다. fast-math와 native
target-cpu는 쓰지 않는다.

strict TSV execution lock은 다음의 bytes·SHA와 의미를 고정한다.

- 이 계약
- Rust source와 wrapper
- source manifest, preflight auditor와 receipt
- CSV와 dictionary
- rustc -Vv, compiler executable SHA와 host target
- rowset hash·counts, model 열 순서, tolerance
- deterministic self-test core receipt SHA
- **real_data_fit_authorized**

키 순서는 다음 29개로 고정한다.

```text
schema_version
real_data_fit_authorized
comparison_contract_sha256
rust_source_sha256
wrapper_sha256
source_manifest_sha256
preflight_auditor_sha256
preflight_receipt_sha256
preflight_decision
raw_csv_sha256
raw_csv_bytes
dictionary_sha256
dictionary_bytes
rowset_sha256
comparison_rows
comparison_events
age_rows
age_events
cell_rows
cell_events
model_feature_order
numerical_tolerance_profile
self_test_core_sha256
rustc_version
rustc_verbose_sha256
rustc_host
rustc_executable_sha256
compile_flags
runtime_threads
```

`rustc -Vv`는 각 출력 줄을 UTF-8 no-BOM LF로 잇고 final LF를 정확히 하나
붙인 bytes를 hash한다. `host:` 줄은 정확히 하나여야 한다. dictionary와 CSV는
네트워크에서 실행 중 다시 받지 않고, 사용자가 제공한 local exact bytes만 쓴다.

hash 순환을 피하기 위해 계약→코드·wrapper 안정화→execution lock 순으로 만든다.
코드와 wrapper는 lock hash를 하드코딩하지 않는다. 실제 실행자는 외부에서
예상 lock SHA-256을 명시하고 wrapper가 exact bytes를 검사해야 한다.

wrapper는 lock과 Rust source를 각각 한 번 읽은 byte array 자체로 hash·parse한다.
검증한 두 byte array를 fresh 임시 snapshot에 쓰고 read-only 공유 handle을
compiler와 Rust runner가 끝날 때까지 유지한다. compiler와 runner에는 원본 경로가
아니라 이 snapshot 경로만 전달한다. 따라서 hash한 bytes와 parse·compile·재검사한
bytes 사이에 경로 재열기나 replace race가 들어갈 수 없다.

발견한 rustc executable도 regular-file·non-reparse임을 확인한 read-only
`FileShare.Read` handle의 같은 bytes로 hash하고, 그 handle을 `-V`, `-Vv`, compile이
끝날 때까지 유지한다. compile된 binary 역시 같은 방식으로 hash한 handle을 모든
self-test·fit 실행이 끝날 때까지 유지한다. 따라서 compiler와 runner executable도
식별 뒤 교체되는 경로 race를 허용하지 않는다.

실자료 경로의 순서는 fail-closed로 고정한다. wrapper와 같은 production binary는
source·wrapper를 읽기 전에 lock exact hash·schema를 검사한 뒤
`real_data_fit_authorized=false`이면 dictionary와
CSV의 존재 여부조차 조회하지 않고 **STOP_REAL_DATA_NOT_AUTHORIZED**로 닫는다.
true일 때만 구현·선행 receipt·toolchain을 검사하고 binary를 만든 뒤, 임시 경로에서
같은 `run_self_test_suite`를 실행한다. 그 deterministic receipt bytes의 SHA-256이
lock의 `self_test_core_sha256`와 exact match하고 `status=PASS`,
`real_data_opened=false`일 때만 dictionary, CSV 순으로 exact bytes를 검증하고
적합을 허용한다. 불일치는 **STOP_SELF_TEST_CORE_HASH_MISMATCH**이며
`fit_started=false`다. Rust fit mode도 lock 직후 같은 결합을 독립적으로 반복한다.
dictionary·CSV parse와 dataset 검증까지 성공한 뒤, 첫 production fit 호출 직전에
Rust가 `ce_npf_loewenstein_2015_fit_started_v1\n` exact bytes를 `create_new` pending
파일에 쓰고 `sync_all`한 다음 최종 marker 경로로 원자적 rename한다. wrapper는 이
exact marker만 인정해 `fit_started`를 정한다. 따라서 실행 파일 launch나 입력 검증
단계의 실패는 false이고, marker commit 뒤 적합 도중 실패는 core receipt가 없어도
true다. 성공했는데 marker가 없거나 bytes가 다르면 **STOP_RUNNER_EXIT**로 닫는다.

출력은 분리한다.

- **core_receipt.json** (`ce_npf_loewenstein_2015_v0_v2_core_receipt_v3`):
  fixed key order, UTF-8 no BOM, LF, final LF 1개,
  finite float의 고정 scientific format, timestamp·절대/임시 path 없음
- **self_test_core.json** (`ce_npf_loewenstein_2015_v0_v2_self_test_v3`):
  같은 byte 규율과 고정된 수치·exact gate 구조
- **environment_receipt.json**: 실행시각, OS, rustc/binary/core hash와
  임시파일 정리 상태

core receipt는 source/contract/code hash, expected·observed self-test hash와 exact
match, 모든 self-test limit·observed·comparison·pass, rowset·fold/design hash,
counts·support, scaler, model feature 열 순서, likelihood·frailty face·AGHQ 정의,
fold/model parameter·normalized objective·raw score-quadrature gradient vector와 norm,
내부 projected-gradient norm·Hessian·quadrature delta,
heldout joint score와 세 비교의 gain/loss gate vector를 모두 담는다. model별
pooled Q15·Q25·final score와 두 전역 delta를 분리한다. Q15→Q25 delta만
사전 고정 수렴 gate이며 Q25→final delta는 재최적화 예측 변화와 quadrature
변화를 섞는 `record_only_fallback_path_shift`로 기록하고 limit/pass나 stop으로
쓰지 않는다. 각 fold는 네 face의
Q15·Q25 진단과, fallback이면 Q35 네 face 진단을 모두 남긴다. 최초 Q25→Q35
cell delta, fallback parameter delta, 최종 Q35→Q45 cell delta를 섞지 않는다.
fallback 미사용 optional 값은 0이 아니라 JSON `null`이고 진단 배열은 `[]`다.

또한 다음을 분리해 기록한다.

- catalogued_protrusion_predictive_comparison_executed
- latent_contact_hypothesis_tested=false
- conducting_state_tested=false
- riemannian_folding_tested=false
- heldout_random_effect_conditioning=false
- animal_heldout=false

## 12. fail-closed 코드

최소 stop code는 다음이다.

- STOP_EXECUTION_CONTRACT_HASH_MISMATCH
- STOP_CONTRACT_SCHEMA_MISMATCH
- STOP_IMPLEMENTATION_HASH_MISMATCH
- STOP_TOOLCHAIN_MISMATCH
- STOP_SOURCE_CONTENT_MISMATCH
- STOP_PREREQUISITE_RECEIPT_MISMATCH
- STOP_SOURCE_SCHEMA_OR_COUNT_MISMATCH
- STOP_ROWSET_MISMATCH
- STOP_FOLD_PARTITION_MISMATCH
- STOP_MODEL_ROWSET_MISMATCH
- STOP_FEATURE_DOMAIN_OR_RANK
- STOP_GH_SELF_TEST
- STOP_SELF_TEST_CORE_HASH_MISMATCH
- STOP_AGHQ_MODE_FAILURE
- STOP_NONFINITE_LIKELIHOOD_OR_GRADIENT
- STOP_OPTIMIZER_NONCONVERGENCE
- STOP_MULTISTART_DISAGREEMENT
- STOP_FRAILTY_UNIDENTIFIED
- STOP_HESSIAN_ILL_CONDITIONED
- STOP_QUADRATURE_NONCONVERGENCE
- STOP_HELDOUT_LEAKAGE
- STOP_RECEIPT_NONDETERMINISTIC
- STOP_OUTPUT_EXISTS
- STOP_REAL_DATA_FORBIDDEN_IN_SELF_TEST
- STOP_REAL_DATA_NOT_AUTHORIZED
- STOP_RUNNER_EXIT
- STOP_TEMP_CLEANUP_SCOPE
- STOP_WRAPPER_FAILURE

실패 receipt는 첫 stop code, expected·observed, fit_started까지만 deterministic하게
쓰고 nonzero exit한다. wrapper 선행검사 실패도 같은 core stop receipt를 쓰며,
runner가 이미 쓴 첫 receipt를 덮지 않는다. 단, **STOP_OUTPUT_EXISTS**는 기존
파일을 덮을 수 없으므로 새 receipt를 쓰지 않는 명시적 예외다. 한 fold 실패를
loss나 tie로 바꾸지 않는다. OS error text·절대 path 같은 비결정적 세부는 core의
`observed`에 넣지 않고 environment receipt의 `stop_detail`에만 둔다.
오류가 결정론적 `expected=...:observed=...` 값을 이미 갖고 있으면 core는 그 두
실제 값을 보존한다. generic fallback은 그런 typed 값이 없는 오류에만 허용한다.
임시 snapshot/runner 정리가 실패하면 environment status도 반드시 `STOP`이다.

## 13. 생물학적 승격 gate

1. **animal inference:** cell↔mouse crosswalk, 충분한 독립 mouse, 모든 cell의
   mouse nesting, animal-heldout 또는 독립복제
2. **observation truth:** registered raw image·branch mask, branch
   length-time exposure, 실제 timestamp, visit/censor reason, blinded 반복
   annotation, detection/re-ID false-positive·negative calibration
3. **object·age·birth:** filopodia/nascent/mature 분리, baseline 이전 관측과
   initial-age law, candidate-slot/branch denominator, terminal EM·PSD/active-zone
4. **contact·conducting:** pre+post parent identity, repeated same-contact
   functional assay, efficacy/conductance calibration
5. **발달:** juvenile→adolescent→adult 종단 동물과 age-specific intervention
6. **Riemann folding:** 같은 animal/cell의 독립 population output likelihood,
   common-support SPD metric, pre/post transport, structural/weight/delay
   intervention·rescue, animal/intervention holdout
7. **governance:** 명시적 license와 versioned archive; 생물 식별과 별도

이 가운데 하나도 Loewenstein 재카탈로그 score만으로 자동 개방하지 않는다.
