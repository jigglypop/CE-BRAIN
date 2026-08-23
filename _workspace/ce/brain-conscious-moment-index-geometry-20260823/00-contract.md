# BA-SRM5 연구 계약 — 무한차원 순환 기하, 순간 4차원 의식 후보, 해마 색인

Status: COMPLETE

Date: 2026-08-23

PREDECESSOR: `_workspace/ce/brain-synapse-edge-operator-geometry-20260823`

## 1. 질문과 판정 단위

사용자 가설을 서로 독립적으로 틀릴 수 있는 세 명제로 분리한다.

1. 신경계의 과거 의존 간선 상태는 무한차원 history space로 표현할 수 있고,
   대칭 양의 metric은 간선 결합 연산자의 합으로 정의할 수 있는가.
2. 반복 회로의 국소 return operator가 한 순간에 rank 4인 느린/중심 부분공간을
   선택하고, 그 좌표가 의식 내용의 공통 관측 quotient라는 가설을 만들 수 있는가.
3. 해마가 그 좌표와 맥락을 희소 주소로 바꾸어 분산된 피질 패턴을 빠르게
   재활성화하는 similarity-preserving index라는 가설을 만들 수 있는가.

이 세 명제의 결합은 현재 `[공리: 모델 선택][미완성]`이다. 특히 BA-SRM4에서
관측된 hard rank 4는 이번 의식 차원 4의 입력 증거로 사용하지 않는다. 같은 숫자가
나왔다는 사실은 가설 생성 동기일 뿐이며, 독립 자료에서 차원을 다시 선택해야 한다.

## 2. PREDECESSOR_EVIDENCE

| 선행 결과 | artifact / SHA-256 | 상태 | 보존 가능한 좁은 주장 | 재시도 금지·경계 |
|---|---|---|---|---|
| BA-SRM4 final | `40-final-report.md` / `3a0c42385ce1c328e872eccb8a2f5a848c532ef2d31ba3559b21a81e010115ff` | `DISCOVERY_CANDIDATE_FROZEN` | causal history를 가진 시냅스는 무한차원으로 표현할 수 있지만 finite output은 점별 관측 quotient만 식별한다 | IC→IC hard rank 4를 뇌 전체·의식·생물학적 상태 수로 승격하지 않는다 |
| BA-SRM4 equation | `artifacts/discovery-equation.v2.json` / `127489197d7fa7d5047e475ec2203dba354c2610873104f36515ab4c653fb1f1` | `DISCOVERY_ONLY` | 현재 pulse-response chart에서 ex/in sensitivity hard rank가 4인 후보 | validation/confirmation을 열지 않고 새 의식 가설의 양성 자료로 재사용하지 않는다 |
| BA-A6-P | route ledger / `feea6b9787de1edd47e66c66eaf983b791a9aa52663661cab319dc438f00f34c` | `MATH_PROPERTY_PASS / EMPIRICAL_UNTESTED` | full-rank flow derivative의 pullback은 조건부 Riemann metric이고 rank loss에서는 PSD만 남는다 | 실제 뇌 또는 의식 metric으로 동일시하지 않는다 |
| BA-TR11/13 | 같은 route ledger | `CURVATURE_MEMORY_IDENTITY_REJECTED / CURVATURE_SELECTOR_STOP` | metric·curvature는 표현의 진단량일 수 있으나 기억 정체나 일반 경로 선택자로 충분하지 않다 | `곡률=기억`, `곡률만으로 의식 경로 선택`을 되살리지 않는다 |
| BA-M0 | 같은 route ledger | `CONFIRMED_SIMULATOR / L0` | rank-4 recurrent write의 합성 capacity witness만 있다 | 획득 규칙·의식·해마 생물학 증거로 사용하지 않는다 |

## 3. BIO_STARTING_MECHANISM

출처 레인이 다음 생물학적 출발점을 1차 문헌에서 각각 검증한다.

- 피질과 시상-피질의 반복 처리 및 지연된 recurrent interaction;
- 해마가 분산된 신피질 기억 표상을 가리키는 index라는 이론과 그 개입 증거;
- 치아이랑(dentate gyrus)의 pattern separation과 CA3 recurrent circuit의
  pattern completion;
- 신경 집단 활동이 과제별 저차원 부분공간에 놓일 수 있다는 실기록 결과.

이 출발점들은 서로의 결합을 증명하지 않는다. 특히 `저차원`, `recurrent`,
`hippocampal index`가 각각 관측됐다는 사실만으로 `순간 의식=4차원`은 나오지 않는다.

## 4. CE_DELTA

### 4.1 무한차원 간선 history 공간

관측 영역 집합을 $V$, directed edge 집합을 $E$라 하고 다음 Hilbert 공간을 쓴다.

$$
\mathcal H
=\bigoplus_{v\in V}\mathbb R^{p_v}
\oplus
\bigoplus_{e\in E}
L^2\!\left(({-\infty},0],\rho(\theta)d\theta;\mathbb R^{q_e}\right),
\qquad \rho(\theta)>0.
$$

history 좌표는 $\xi_{e,t}(\theta)=s_e(t+\theta)$, $\theta\le0$이다. $\rho$는
weighted norm이 유한하고 time-shift가 유계가 되도록 별도로 고정한다. 이 정의만으로
Riemann metric이 생기지 않는다. `[공리: 모델 선택]`으로 smooth bounded
self-adjoint operator $A_x$와 edge incidence/contrast operator $D_e$를 둔다.

$$
A_x=A_{0,x}+\sum_{e\in E}D_e^*K_e(x)D_e,
\qquad
g_x(u,v)=\langle u,A_xv\rangle_{\mathcal H}.
$$

합은 quadratic-form 또는 operator norm에서 수렴해야 하며, 어떤
$0<m\le M<\infty$에 대해 $mI\preceq A_x\preceq MI$를 요구한다. directed edge는
동역학을 정하지만 metric 항 $D_e^*K_eD_e$는 대칭이다. 간선 자체를 metric으로
부르지 않는다.

### 4.2 반복 회로가 선택하는 순간 rank-4 부분공간

실제 생물 기준 동역학과 새 가설을 분리한다.

$$
d\xi_t
=F_{\rm bio}(\xi_t,u_t;\theta_{\rm bio})\,dt
+\Delta F_{\rm CE}(\xi_t;\phi)\,dt
+G(\xi_t)\,dW_t.
$$

짧은 무차원 분석 창 $\Delta/\tau_0$에서 recurrent flow의 bounded tangent return
operator를 $U_t^\Delta=D\Phi_{t,t+\Delta}(\xi_t)$라 한다. 이것은 그래프의 closed
walk, SCC membership, Levi-Civita holonomy와 같은 대상이 아니다. 이 셋을 연결하려면
별도의 edge transport와 적합성 조건이 필요하다. 네 개의 느린/준중립
mode와 나머지 안정 mode 사이에 닫힌 contour $\Gamma_4$가 존재할 때 Riesz
projection 후보를 정의한다.

$$
P_t^{(4)}
=\frac{1}{2\pi i}\oint_{\Gamma_4}
(zI-U_t^\Delta)^{-1}\,dz,
\qquad \operatorname{rank}P_t^{(4)}=4.
$$

복소화한 operator에서 contour 내부의 algebraic multiplicity를 세되, 실수 동역학에서는
복소켤레 쌍을 함께 세어 real rank가 4인지 확인한다. `[공리: 물리 사상]` 순간 의식
내용 후보는 전체 $\xi_t$가 아니라 local dimensionless chart displacement

$$
\zeta_t
=S_\xi^{-1}\!\left(\varphi_t(\xi_t)-\varphi_t(\bar\xi_t)\right),
\qquad
z_t=\chi_t(P_t^{(4)}\zeta_t)\in\mathbb R^4
$$

로 표현되는 metastable spectral-coordinate 후보이다. Riesz range는 자동으로 quotient가
아니다. 여기서 4는 물리적 시공간 차원이 아니고
좌표축의 의미도 사전 고정하지 않는다. spectral gap이 없거나 rank가 4가 아니면
이 후보는 그 시점에서 abstain한다.

### 4.3 부위별 다른 형상과 공통 index cell

영역 $r$의 상태공간 $\mathcal H_r$는 서로 다른 차원·위상·metric을 가질 수 있다.
각 영역에서 공통 moment space로 가는 many-to-one 관측 사상

$$
\pi_{r,t}:\mathcal H_r\longrightarrow\mathcal Z_t\cong\mathbb R^4
$$

만 요구한다. 서로 다른 영역의 합집합 $\bigsqcup_r\mathcal H_r$ 위에서

$$
x_r\sim_t x_s
\quad\Longleftrightarrow\quad
\pi_{r,t}(x_r)=\pi_{s,t}(x_s)
$$

를 정의할 때에만 공통 관측 equivalence class 또는 quotient라고 부른다. smooth quotient
manifold 주장은 constant-rank와 smooth closed-kernel 조건을 추가로 요구한다. 따라서
시각·청각·촉각의 세부 패턴이 서로 미분동형이라는 주장은 하지 않는다. 공통 좌표의
dimensionless quantization cell은

$$
q_t=Q_\varepsilon(\bar z_t),
\qquad \bar z_t=S_z^{-1}(z_t-z_0)
$$

로 정의한다. $q_t$가 같다는 것은 현재 관측 목적에서 같은 equivalence class라는
뜻이며 원래 감각 패턴이 동일하거나 손실 없이 복원된다는 뜻이 아니다.

### 4.4 해마의 candidate sparse address 가설

`hash`는 암호학적 hash가 아니라 희소하고 충돌 가능한 주소라는 뜻으로 제한한다.
무차원 moment 좌표 $\bar z_t$, 무차원 맥락 $\bar c_t$, 위상/시간 좌표 $\bar\tau_t$에서

$$
h_t
=\mathsf{Sparse}_{s}
\!\left(B_z\bar z_t+B_c\bar c_t+B_\tau\bar\tau_t-\vartheta\right)
\in\{0,1\}^{m_h}
$$

를 만들고, 저장된 episode 주소 $h_\nu$ 중

$$
\widehat\nu_t
=\underset{\nu}{\operatorname{argmax}}
\frac{\langle h_t,h_\nu\rangle}
{\lVert h_t\rVert_2\lVert h_\nu\rVert_2}
$$

를 찾는 후보를 둔다. 이 식만으로 similarity preservation은 나오지 않는다. latent
distance $d_Z$와 Hamming/cosine distance $d_H$의 triplet-order error

$$
\delta_{\rm ord}
=\Pr\!\left[
(d_Z(i,j)-d_Z(i,k))(d_H(i,j)-d_H(i,k))<0
\right]
$$

와 collision rate가 random sparse 및 semantic controls보다 낮을 때에만 제한된 의미의
similarity-preserving address라고 부른다. 실제 감각 세부는 피질 decoder
$D_r(\widehat\nu_t)$에서 재활성화되며 $h_t$ 자체에 모두 저장됐다고 주장하지 않는다.

## 5. MEASUREMENT_MODEL

미래 실기록 분석에서는 숨은 상태를 직접 관측했다고 쓰지 않는다.

$$
y_{r,k}=\mathcal H_r(\xi_{r,t_k};\psi_r)+\varepsilon_{r,k},
\qquad \varepsilon\sim\mathcal D(0,\Sigma_r).
$$

$y$는 spike count/rate, field potential, ECoG 또는 calcium fluorescence 중 실제
dataset의 단위를 유지한다. indicator kinetics, bin width, filtering, report latency,
motor response와 arousal은 $\mathcal H_r$ 또는 nuisance 변수로 분리한다. neural
state covariance inverse만으로 intrinsic Riemann metric을 선언하지 않는다. 의식 접근
label도 의식 자체가 아니라 objective discrimination, subjective visibility 또는 no-report
proxy 중 사전 고정한 측정값이다. primary label 하나와 report·motor·arousal 대조를 분리한다.

## 6. DATA_PROVENANCE와 DATA_SPLIT

이번 run은 식·가능성·반례를 고정하는 이론 run이며 사람/동물 outcome을 열지 않는다.
따라서 `DATA_PROVENANCE = NO_DATA_OPENED`이고 empirical evidence ceiling은 L0보다
낮은 `CONCEPTUAL_ONLY`다. `IMPLEMENTATION_DECISION = SKIP_NO_PINNED_DATA`이며,
아래 split·observable·selection 항목은 이번 run에서 수치를 선택하는 절차가 아니라
후속 empirical run을 열기 전에 새 계약으로 고정해야 할 admission checklist다.

후속 실증 run은 동시에 기록된 다영역 자료와 의식 접근 또는 자극 조건, 해마-피질
reinstatement를 가진 1차 공개 dataset을 DOI·판본·subject/session identity까지 고정해야
한다. subject 또는 session 단위로 train/development/confirmation을 분리하고 인접 시간
window가 split을 가로지르지 않게 한다. 같은 trial을 차원 선택과 confirmation에 함께
쓰지 않는다.

## 7. OBSERVABLES

후속 run에서 결과 전에 다음을 고정한다.

1. dimension 후보 $d\in\{1,2,3,4,5,6,8,10,12\}$의 held-out likelihood/ELPD;
2. 네 번째와 다섯 번째 normalized mode의 spectral gap;
3. $P_t^{(4)}$ subspace stability와 recurrent disruption 전후 변화;
4. modality-held-out cross-decoding, triplet-order distortion 및 collision rate;
5. hippocampal sparse-code distance가 예측하는 cortical reinstatement target과 latency;
6. cortical similarity, semantic embedding, arousal, motor report를 넣은 뒤의 incremental
   hippocampal index information.

## 8. RESIDUAL_RULE과 MODEL_SELECTION

- 이번 conceptual run에는 numerical residual, fitted parameter, seed, rank estimator,
  gap cutoff 또는 codebook이 없다. 아래 항목을 현재 판본의 동결 수치로 해석하지 않는다.
- 모든 시간·전압·발화율·지연은 $\tau_0,V_0,f_0$ 같은 source-locked scale로
  무차원화한 뒤 exp, resolvent threshold, probability core에 넣는다.
- $d=4$는 다른 $d$보다 paired held-out $\Delta\mathrm{ELPD}>2SE$일 때만 선택한다.
- 자유도에는 encoder, dynamics order, covariance, sparsity, quantizer와 nuisance
  regression을 모두 포함한다.
- raw high-dimensional state, unconstrained latent dimension, PCA/CCA, feedforward-only,
  recurrent non-rank-fixed model과 비교한다.
- hippocampal address는 random sparse projection, cortical-only similarity, semantic-only
  retrieval, time-shuffled code와 같은 split에서 비교한다.

## 9. FALSIFIER와 MATCHED_CONTROLS

다음 중 하나면 해당 좁은 주장을 기각한다.

1. 독립 자료에서 $d=4$가 차원 sweep의 우승자가 아니거나 mode 4/5 gap이 불안정하면
   `MOMENT_RANK4_NOT_SUPPORTED`;
2. recurrent perturbation·backward mask·time reversal이 feedforward control보다
   선택적으로 rank-4 안정성을 무너뜨리지 않으면 `LOOP_SELECTION_NOT_IDENTIFIED`;
3. shared 4D quotient가 modality-specific 또는 unrestricted model보다 held-out
   cross-modal 예측을 개선하지 못하면 `COMMON_INDEX_NOT_SUPPORTED`;
4. hippocampal code가 cortical similarity와 맥락을 넘어서 reinstatement 대상·속도를
   예측하지 못하거나 개입에서 선택적 효과가 없으면 `HIPPOCAMPAL_ADDRESS_NOT_IDENTIFIED`;
5. 4D 좌표만으로 원래 고차원 감각 세부를 lossless 복원한다고 주장하는 모델은
   별도 4D manifold/support 증명 없이는 정보·위상 no-go로 기각한다.

## 10. 후보 경로와 선택

| 경로 | 상태 | 이유 |
|---|---|---|
| A. infinite history + spectral rank-4 moment + hippocampal sparse address | `SELECTED_HYPOTHESIS` | 사용자 아이디어를 가장 적게 왜곡하며 각 연결고리를 독립 반증할 수 있다 |
| B. recurrent shared workspace, dimension free | `MANDATORY_CONTROL` | 반복 처리 효과와 숫자 4를 분리한다 |
| C. high-dimensional recurrent state without collapse | `MANDATORY_CONTROL` | 저차원 bottleneck 자체의 필요성을 시험한다 |
| D. curvature/holonomy equals memory or consciousness | `REJECTED_PREDECESSOR_CONFLICT` | BA-TR11/13 반례와 일반 선택 실패를 되살린다 |
| E. literal cryptographic hippocampal hash | `REJECTED_CATEGORY_ERROR` | 생물학적 희소 색인과 충돌하며 충돌·유사도·학습을 숨긴다 |

## 11. REVISION_TRIGGER

source lane에서 생물 출발점 또는 측정 가능성이 부정되면 수식에 맞춰 출처를 넓히지
않고 해당 연결고리를 제거한다. 후속 validation을 본 뒤 dimension menu, rank threshold,
window, encoder 또는 hash sparsity를 바꾸면 새 run-id와 새 confirmation 자료가 필요하다.

후속 data contract는 $\tau_0,V_0,f_0$, $\rho$의 단위·함수형, $S_\xi,S_z$, spectral
estimator와 gap cutoff, quantizer margin, $m_h,s$, address seed/codebook, collision/tie
policy, cue window와 decoder를 결과 전에 고정해야 한다. 어느 하나라도 없으면
`BLOCKED_EMPIRICAL_INSTANTIATION`이며 현재 이론 run의 식을 fit하지 않는다.

## 12. CLAIM_CEILING

허용 지위는 다음뿐이다.

- infinite-dimensional edge-history metric의 존재 조건: `[조건부 정리]` 후보;
- rank-4 spectral projection과 finite-dimensional slow manifold: 수학 가정 아래
  `[조건부 정리]` 후보;
- 순간 의식과의 동일시, 공통 감각 index, 해마 sparse address: `[공리: 물리 사상][미완성]`;
- 실제 뇌가 이 결합 메커니즘을 쓴다는 주장: 금지;
- BA-SRM4의 숫자 4를 독립 확인으로 사용하는 것: 금지.

이번 run에서는 구현·fit·validation dataset 개봉을 하지 않는다. source와 수학 감사를
통과한 뒤 식의 생존 범위와 가장 짧은 실증 경로만 최종 보고한다. 목표 종료 상태는
`CONCEPTUAL_FORMALIZATION_COMPLETE / EMPIRICAL_INSTANTIATION_BLOCKED`이며, 이는
생물학적 가설 통과가 아니다.
