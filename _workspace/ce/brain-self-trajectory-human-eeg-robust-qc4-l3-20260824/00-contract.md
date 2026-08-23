# BA-SRM4-L3 연구 계약 — 무한기억 전기동역학의 상태 대 경로 EEG 검정

Status: COMPLETE

PREDECESSOR: `_workspace/ce/brain-self-trajectory-human-eeg-channel-qc3-l3-20260824`

CE_RUN: `_workspace/ce/brain-self-trajectory-human-eeg-robust-qc4-l3-20260824`

## 1. 질문과 이번 판본의 경계

이 실행은 “현재의 관측 상태만 알면 100 ms 뒤 EEG 변화가 충분히 예측되는가, 아니면 같은 현재 상태와 저차 통계를 조건화한 뒤에도 순서 있는 400 ms 경로가 추가 예측정보를 갖는가”를 검정한다. 순간의 자아를 예측 충분상태의 한 점으로, 이어지는 동일성을 그 점들의 경로로 보는 수학 후보에서 나온 제한된 관측 예측이다. scalp EEG 하나로 자아나 의식의 존재론을 판정하지 않는다.

선행 BA-SELF1/2/3은 과학 endpoint 전에 세 차례 멈췄다. 절대 전압 QC는 0/32 pair, 공통-scale QC는 13/32, 채널별 affine 불변 max-QC는 17/32만 남겼다. BA-SELF3의 필요조건은 24/32와 session별 12/16이었지만 실제로는 10/16과 7/16이었다. 거부 15 pair 중 14 pair에서 차분 최댓값이 관여했다. 이는 126×63 표준화 값 중 단 하나의 극단값으로 pair 전체를 버리는 측정 gate의 전이 실패이지, 전기동역학이나 상태-경로 식의 결과가 아니다.

이번 판본은 그 max-QC를 cutoff 조정으로 구제하지 않는다. finite·nonflat·range integrity만 hard gate로 남기고, 유한한 artifact는 고정된 smooth bounded transform으로 연속 완화한다. 그 뒤 알려진 전도성 막 방정식의 저차 관측 축약에 순서 있는 2차 경로항을 하나만 더해 matched baseline과 비교한다.

`docs/axium.md`와 `docs/참조/무차원_감사_수학.md`는 저장소에 존재하지 않는다. 따라서 이 계약은 그 파일의 공리나 기호를 추정해 사용하지 않으며, 아래 정의·공리·경험 후보만을 사용한다.

## 2. PREDECESSOR_EVIDENCE

| 항목 | 고정 증거 | 판정과 재사용 경계 |
|---|---|---|
| BA-SELF3 final | `40-final-report.md`, SHA-256 `78199331071369981cf54d18a863dab075e0a1a413ab127c0931ab8ef4a9e445` | `APPARATUS_INVALID_CHANNELWISE_QC_TRANSFER`; path/model endpoint 미개방 |
| BA-SELF3 ledger | `_workspace/ce/brain-algorithm-route-ledger.md`, SHA-256 `1265db747905b1c08f2bd12fe458d7fe8e264d3e6d73849203ed8e31416fe98b` | R2 max-QC는 killed; 자아·의식·경로 식은 미검증 |
| BA-SELF3 B1 | `artifacts/b1-channelwise-transfer-receipt.json`, SHA-256 `d3b7319804206b3ddcc6f35260706dfe4d4b961e0053db80c1c16c9569ead362` | 17/32, ses-01 10/16, ses-02 7/16; B1은 소진되어 feasibility 진단에만 사용 가능 |
| BA-SELF3 allocation | `artifacts/b1-allocation.json`, SHA-256 `91fff95baa5ff309d2dda23e4206da8f7f04fd6341c6b1012b2dbb82bb95f1c2` | 신호 미개방 `D2-M` 100 pair가 ses-01 57, ses-02 43으로 남음 |
| Source manifest | BA-SELF1 `artifacts/a0-trial-manifest.json`, SHA-256 `4ebc8efdca4e277a989c8e7aceb0f00911d84fd20e6b6980dc94cbce7062a061` | trial identity, anchor, word, session, 원래 C split 고정 |
| Range/parser | BA-SELF1 `artifacts/brainvision_range.py`, SHA-256 `b075b9deb34c6a5e93ab58eabeb378a38c2e69045b4155d219252154baa3d559` | exact byte range, BrainVision parse, causal filter만 상속 |

B1의 signal은 새 transform의 비봉인 smoke diagnostic에는 다시 사용할 수 있지만 후보 선택, cutoff 적합, 성공률 또는 과학 검증 표본으로 세지 않는다. `D2-M`, C1, C2, C3의 endpoint는 아직 보지 않았다.

## 3. BIO_STARTING_MECHANISM — 전압·전류·전도도

[정의] 수상돌기·축삭을 metric graph $\Gamma$로 보고 막전압을 $V(x,t)$, 막 정전용량 밀도를 $c_m(x)$, 축방향 전도도를 $\sigma(x)$로 쓴다. 알려진 출발 방정식의 형식은 다음 전류 보존식이다.

$$
c_m(x)\,\partial_t V
=
\nabla_\Gamma\!\cdot\!\bigl(\sigma(x)\nabla_\Gamma V\bigr)
-I_{\rm ion}(V,w)
-I_{\rm syn}(V,h_t)
+I_{\rm ext}.
$$

[정의] 이온 gate $w_r$와 화학·전기 시냅스 전류는 다음처럼 분리한다.

$$
\tau_r(V)\dot w_r=w_{r,\infty}(V)-w_r,
$$

$$
I^{\rm chem}_{j\to i}=g_{ji}[h_{ji,t}](V_i-E_{ji}),
\qquad
I^{\rm gap}_{ij}=g^{\rm gap}_{ij}(V_j-V_i).
$$

[공리: 모델 선택] $h_{ji,t}(\theta)$는 $\theta\le0$의 필터된 spike-rate trace, 전압, gate와 조절상태를 담는 $L^2_\rho$ history 함수이고, $g_{ji}=\mathcal G_{ji}[h_{ji,t}]>0$는 지정된 Hilbert topology에서 causal $C^\infty$ functional이라고 가정한다. 이상적 Dirac spike 자체를 $L^2$ 원소라고 하지 않는다. gap-current 식도 이 실행에서 검증된 인간 뇌 연결법칙이 아니라 선택한 electrical-coupling 모형이다. 이 가정들은 단일 scalar $W_{ij}$보다 넓은 synapse 모형을 정의하지만, 이 EEG 실행이 실제 $\mathcal G_{ji}$를 식별한다는 뜻은 아니다.

## 4. 무차원화와 무한차원 리만 상태공간

[정의] 기준 전압 $V_*>0$, 시간 $t_*>0$, 전도도 $g_*>0$를 두고

$$
v_i=\frac{V_i-E_*}{V_*},\qquad
\tau=\frac{t}{t_*},\qquad
\gamma=\frac{g}{g_*},\qquad
\iota=\frac{I}{g_*V_*},\qquad
\chi_i=\frac{C_i}{g_*t_*}
$$

로 정규화한다. 따라서 reduced 전류 보존식의 모든 항과 $\chi_i$는 무차원이다.

[정의] 연속 cable 식과 이산 node 식의 단위 다리는 compartment $\Omega_i$에서 $C_i=\int_{\Omega_i}c_m(x)\,dx$와 axial face conductance $g^{\rm ax}_{ij}=\sigma_{ij}A_{ij}/\ell_{ij}$를 만드는 유한체적 이산화로 둔다. 이 다리를 적용한 뒤에만 $C_i/(g_*t_*)$를 사용한다. 이는 cable/PDE를 유한 compartment 모델로 이산화하는 모델 정의이며, OpenNeuro scalp EEG가 실제 인간 뇌의 compartment 경계·축삭 전도도·edge conductance를 식별한다는 뜻은 아니다.

[정의] 전체 history-state는

$$
q_\tau=(v(\tau),w(\tau),h_\tau)
\in
\mathcal M
=
\mathbb R^{N_v+N_w}
\times
L^2_\rho(( -\infty,0],\mathbb R^m)
$$

에 놓는다. history 함수공간 때문에 $\mathcal M$은 무한차원이다.

[공리: 모델 선택] $a_i$는 양의 상·하한을 가지며 $q$에 smooth하고, $b_{ij}$는 비음이 아니며 $q$에 smooth하다고 가정한다. $\rho(\theta)>0$는 적분가능한 history weight다. $K_{ij}(q,\theta)$는 self-adjoint이고 $q$에 smooth하며 Hilbert norm에 대해 균일 bounded·coercive라고 가정해

$$
\begin{aligned}
G_q(\xi,\eta)
={}&\sum_i a_i(q)\xi_{v_i}\eta_{v_i}
+\frac12\sum_{i,j}b_{ij}(q)
(\xi_{v_i}-\xi_{v_j})(\eta_{v_i}-\eta_{v_j})\\
&+\sum_{i,j}\int_{-\infty}^{0}
\xi_{h,ij}(\theta)^\top
K_{ij}(q,\theta)
\eta_{h,ij}(\theta)\rho(\theta)\,d\theta
\end{aligned}
$$

를 후보 Riemannian metric으로 둔다. 이는 edge와 history가 tangent distance에 기여한다는 명시적 모델 공리다. scalp EEG에서 이 metric 전체를 복원한다는 주장은 금지한다.

## 5. CE_DELTA — 검정 가능한 저차 경로항

[정의] 관측은

$$
x_c(t)=a_c\,\mathcal O_c(q_t)+b_c+\varepsilon_c(t)+o_c(t)
$$

로 둔다. $\mathcal O$는 volume-conduction observation, $a_c,b_c$는 기록 gain·offset, $\varepsilon$는 연속 noise, $o$는 드문 artifact다. 유한 EEG는 $q_t$ 전체가 아니라 $\mathcal O$가 만드는 관측 quotient만 제약한다.

[정의] training fold 안에서만 각 channel의 중앙값 $m_c$와 robust scale $s_c=1.4826\operatorname{MAD}_c$를 적합하고

$$
u_{tc}=\frac{x_{tc}-m_c}{s_c},
\qquad
\widetilde u_{tc}=\kappa\tanh\!\left(\frac{u_{tc}}{\kappa}\right),
\qquad \kappa=4
$$

를 사용한다. $u_{tc}/\kappa$는 무차원이고 transform은 $C^\infty$이며 bounded다. median/MAD estimator 자체를 물리적 $C^\infty$ flow라고 부르지 않는다. nonfinite 또는 $s_c\le0$만 hard reject하고, 유한 극단값 하나로 pair 전체를 버리지 않는다.

[정의] training fold의 $\widetilde u$에 PCA와 whitening을 적합해 dimensionless 관측좌표 $z_t$를 만든다. 실제 계산 rank는 통계적 식별력을 위해 $d=2$로 고정하되, 이것을 의식이나 뇌의 본질적 차원이라고 해석하지 않는다. 별도로 covariance eigenvalue $\lambda_k$에서

$$
p_k=\frac{\lambda_k}{\sum_j\lambda_j},
\qquad
d_{\rm eff}=\exp\!\left(-\sum_k p_k\log p_k\right)
$$

를 보고해 비정수 유효차원을 측정한다. $p_k$와 $\log p_k$의 인자는 무차원이다.

$d_{\rm eff}$는 covariance trace와 $\lambda_1$이 양수일 때만 정의하고 $0\log0=0$ convention을 쓴다. 그렇지 않으면 해당 fold를 degenerate로 거부한다.

[정의] history 길이 $H=0.4\,{\rm s}$, 미래 간격 $\Delta=0.1\,{\rm s}$를 고정한다. $M_0$는 endpoint $z_t$, 마지막 causal velocity, 시작점, 전체 displacement, 경로 energy, word와 task/rest를 사용한다. $M_1$은 같은 항에 다음 antisymmetric level-2 area 하나만 더한다.

$$
A_{12}(t;H)
=
\frac12\sum_{p<q}
\left(
\Delta z_p^1\Delta z_q^2
-\Delta z_p^2\Delta z_q^1
\right).
$$

target은 $y_t=z_{t+\Delta}-z_t$다. $z$, $A_{12}$와 target은 whitening 뒤 무차원이다. 이 area는 선택된 관측 frame의 경로 특징이며 ambient 뇌 manifold의 곡률이나 holonomy 그 자체가 아니다.

[경험 후보] 같은 training-only transform과 controls 아래 $M_1$이 $M_0$보다 held-out future increment를 더 잘 예측하면, 관측된 현재점과 저차 요약만으로 제거되지 않는 ordered-history 정보가 있다는 제한된 증거로 삼는다.

## 6. MEASUREMENT_MODEL

OpenNeuro `ds006033` version `1.0.1`의 BrainVision EEG를 사용한다. 각 task/rest anchor에서 raw 5 kHz의 `anchor-2500`부터 `anchor+500`까지 3,001 sample만 exact HTTP Range로 읽는다. `206`, `Content-Range`, ETag, payload SHA-256를 receipt에 기록한다. little-endian multiplexed float32를 decode하고 ECG를 제거한 63 scalp channel에 common-average reference를 적용한다.

501-tap Hamming FIR, cutoff 45 Hz를 causal `lfilter`로 적용하고 첫 500 raw sample을 버린 뒤 20배 decimation하여 250 Hz, 126×63 window를 만든다. endpoint index 100, target index 125, history는 endpoint 직전 100 sample이다. zero-phase filtering, 미래 sample을 쓰는 filtering, per-dataset cutoff retune은 금지한다.

기존 absolute/R1/R2 max score는 matched diagnostic으로만 기록하고 gate나 weight에 사용하지 않는다. 새 transform의 $\kappa=4$도 적합하지 않는다.

## 7. DATA_PROVENANCE와 DATA_SPLIT

자료는 DOI `10.18112/openneuro.ds006033.v1.0.1`, 1차 자료 논문 DOI `10.1016/j.dib.2025.112258`, 고정 manifest와 predecessor range reader에서만 가져온다. raw EEG payload나 decoded window는 저장소에 저장하거나 commit하지 않는다.

P0에서 SELF3 allocation의 `new_split=D2-M` 100 pair만 추출한다. 각 session 안에서

$$
k_i=\operatorname{SHA256}\!\left(
\operatorname{UTF8}(``BA\text{-}SRM4\text{-}REAL\text{-}v1:''\Vert\mathrm{trial\_hash}_i)
\right)
$$

를 계산하고 $(k_i,\mathrm{trial\_hash}_i)$로 정렬한다. 각 session의 처음 5 pair는 `R0-SMALL`, 다음 10 pair는 `R1-MEDIUM`, 나머지는 `R2-LARGE`다.

| stage | ses-01 | ses-02 | 합계 | 역할 |
|---|---:|---:|---:|---|
| R0-SMALL | 5 | 5 | 10 | 약 10%; domain·conditioning·baseline feasibility |
| R1-MEDIUM | 10 | 10 | 20 | 추가 20%; SMALL과 합쳐 최초 path futility |
| R2-LARGE | 42 | 28 | 70 | 독립 development validation |
| C1/C2/C3 | predecessor 그대로 | predecessor 그대로 | 25/50/175 | R2 성공 전까지 완전 봉인 |

allocation receipt는 신호 접근 전에 모든 trial hash, key, session, word, old/new split과 word coverage를 기록한다. R0 실패 시 R1/R2/C를 열지 않고, R1 실패 시 R2/C를 열지 않는다. R2-LARGE는 R0/R1 outcome을 feature나 coefficient 적합에 사용하지 않는다.

## 8. 모델, observables와 matched controls

모든 median/MAD, PCA, whitening, feature standardization과 coefficient는 training session에서만 적합한다. 두 session 방향을 바꾼 leave-one-session-out 평가를 사용한다. ridge penalty는 standardized feature에 $\lambda=1$로 고정하고 intercept에는 penalty를 주지 않는다. normal equation 대신 SVD/lstsq를 사용한다.

R0의 baseline은 intercept, endpoint 두 좌표와 마지막 velocity 두 좌표만 쓰는 $p=5$ 저차 모델로 고정한다. R1/R2의 $M_0$는 section 5의 전체 feature를 사용한다. word는 고정된 여덟 수준 중 사전순 첫 수준을 reference로 한 일곱 indicator로 encoding한다. training fold에서 분산이 정확히 0인 non-intercept 열은 standardized value와 coefficient를 0으로 고정하고 active feature 수에서 제외한다. test-only word는 이 고정 encoding으로 표현한다. 한 pair의 task와 rest window를 서로 다른 두 prediction row로 세므로 $n_{train}=2N_{train,pair}$다. 각 fit은 이 row 수로 $n_{train}\ge p_{active}+5$를 만족해야 하며 아니면 fail-closed한다.

$M_0$와 $M_1$의 held-out loss는

$$
L_{m,c}=\frac1d\left\|y_c-\widehat y_{m,c}\right\|_2^2,
\qquad
G_c=\frac{L_{0,c}-L_{1,c}}{L_{0,c}}
$$

로 정의한다. persistence predictor $\widehat y=0$의 loss $L_P$와 baseline 재현율

$$
B_c=\frac{L_{P,c}-L_{0,c}}{L_{P,c}}
$$

도 먼저 기록한다. 각 분모에는 $L_P>10^{-12}$와 $L_0>10^{-12}$를 요구한다. 이를 만족하지 않으면 degenerate loss로 fail-closed하며, $B_c\le0$이면 path항을 해석하지 않는다. pooled gain은 sample별 squared error를 두 held-out 방향에서 합산해 만든 pooled $L_0,L_1$로 한 번만 계산한다.

matched controls는 task/rest pair, word indicator, 동일 endpoint·velocity·start·displacement·energy, trial hash로 고정한 20개 within-window increment-order shuffle, 기존 세 QC score다. shuffle은 마지막 increment를 고정하고 그 이전 increment들만 순열화한다. 따라서 increment multiset, start, endpoint, displacement, energy와 마지막 causal velocity를 모두 보존하고 area만 바꾼다. 매 control마다 training과 held-out area를 같은 hash 법칙으로 다시 만들고 $M_1$을 다시 적합한다. 이는 사전 고정된 artificial order-destruction contrast이지 교환가능성 검정이나 인과 null이 아니며 p-value로 해석하지 않는다. 단순 $A_{12}\mapsto-A_{12}$는 재적합하면 coefficient 부호도 바뀌어 같은 model이 되므로 matched null로 사용하지 않는다. oriented coefficient를 고정한 부호반전 loss는 stress diagnostic으로만 기록하고 성공 gate나 방향성 주장에 사용하지 않는다.

별도로 $d_{\rm eff}$, eigenvalue ratio $\lambda_2/\lambda_1$, finite/scale counts, transform saturation fraction $|u|>4$, condition별 loss와 gain을 보고한다.

## 9. 단계별 residual rule과 falsifier

P0 합성 검증은 known-state conductance 선형화 두 종류를 만든다. Markov control에는 endpoint·velocity만으로 충분한 dynamics를, history positive에는 고정 area coupling을 넣는다. 동일 observation mixing과 finite outlier를 가한 뒤 다음을 모두 만족해야 한다.

- CAR 이전의 공통 nonzero recording gain과 시간불변 channel offset에서 예측 loss가 허용오차 `1e-10` 안에 일치한다. 별도로 CAR 이후 인위적인 channel별 affine map은 PCA 좌표가 아니라 Gram matrix와 예측 loss의 orthogonal-equivariance만 검사한다. 물리적 channel별 gain과 CAR가 교환된다고 주장하지 않는다.
- Markov control에서 평균 $G_{task}\le0.01$이다.
- history positive에서 평균 $G_{task}\ge0.05$이고 oriented가 20개 순서 shuffle 각각보다 loss 0.01 이상 낮다.
- nonfinite와 zero-scale은 fail-closed다.

R0-SMALL은 hard-domain failure가 없어 10/10 pair, session별 5/5가 남아야 한다. section 8의 $p=5$ 저차 baseline만 사용하고 pair당 task/rest 두 prediction row를 쓰므로 각 LOSO training 방향의 $n_{train}=10$이다. 두 방향 모두 $n_{train}\ge p+5$, $\lambda_2/\lambda_1\ge10^{-6}$, finite $d_{\rm eff}$, $L_P,L_0>10^{-12}$이고 pooled $B_{task}>0$이어야 한다. path gain과 word effect는 열지 않는다. 하나라도 실패하면 `APPARATUS_INVALID_OR_BASELINE_UNRESOLVED`로 종료한다.

R1-MEDIUM은 SMALL+MEDIUM 30 pair를 development로 사용한다. active-feature guard와 양의 loss 분모를 먼저 통과해야 한다. 두 방향 모두 $B_{task}>0$이고 $G_{task}>0$, oriented $M_1$이 20개 refit shuffle의 median보다 낮은 loss를 가져야 한다. leave-one-word-out은 해당 word의 training과 held-out row를 함께 제외한 뒤 transform과 model을 다시 적합한다. 한 word만 제거하면 pooled $G_{task}$ 부호가 뒤집히는 결과도 실패다. 실패하면 `STOP_NO_ORDERED_HISTORY_FEASIBILITY`로 종료하고 LARGE를 열지 않는다.

R2-LARGE는 70 pair만으로 transform과 coefficient를 새로 적합한다. 성공 조건은 다음 모두다.

- hard-domain retained pair가 전체 53/70 이상, ses-01 32/42 이상, ses-02 21/28 이상이다.
- 두 방향 모두 $B_{task}>0$과 $G_{task}>0$이다.
- pooled $G_{task}\ge0.02$다.
- oriented $M_1$ loss가 20개 refit shuffle 각각보다 0.01 이상 낮다.
- leave-one-word-out 여덟 결과 중 최소 일곱에서 $G_{task}>0$이다.

성공하면 `PASS_L3_ORDERED_HISTORY_OBSERVATION_QUOTIENT`다. $G_{rest}$도 같은 방향이면 generic temporal-history pilot이고, 추가로 $G_{task}-G_{rest}\ge0.01$일 때만 inner-speech-specific 후보라고 기록한다. R2 성공 전에는 C1/C2/C3를 열지 않는다.

## 10. 형식 지위와 no-go

[정의] 막 전류식, history-state, 후보 metric, 관측 quotient, robust transform, baseline과 path feature는 이 계약의 모델 정의다.

[공리: 모델 선택] 필터된 $L^2_\rho$ history에서 $\mathcal G_{ij}$가 causal $C^\infty$ functional이라는 성질, metric 계수의 smooth·self-adjoint·균일 bounded/coercive 성질, $d=2$, $H=0.4$ s, $\Delta=0.1$ s, $\kappa=4$, $\lambda=1$은 채택한 모델·실험 공리다.

[경험 후보: 미검증] ordered level-2 area가 상태 baseline보다 held-out 미래 EEG를 더 잘 예측한다.

[미완성] scalp EEG에서 neuron별 edge conductance, 무한차원 metric, 실제 자아상태, 의식 순간 또는 hippocampal hash를 식별하는 다리는 없다.

[정리: state/path no-go] 유한 history feature는 augmented instantaneous state의 좌표로 다시 정의할 수 있다. 따라서 $M_1>M_0$이어도 자아가 존재론적으로 path이고 state가 아니라는 결론은 나오지 않는다. 결과는 선택한 관측 quotient와 baseline에 상대적인 추가 예측정보만 뜻한다.

## 11. 필수 계약 필드

`BIO_STARTING_MECHANISM`: section 3의 cable/current conservation, ion gate, chemical/gap current.

`CE_DELTA`: infinite-history conductance 후보에서 나온 관측 quotient의 antisymmetric level-2 area 한 항.

`MEASUREMENT_MODEL`: section 5–6의 affine observation, fold-local median/MAD, $4\tanh(u/4)$, causal FIR, exact range.

`DATA_PROVENANCE`: OpenNeuro DOI, primary-paper DOI, hash-fixed manifest/parser/receipts.

`DATA_SPLIT`: signal-blind 10/20/70 funnel과 sealed C1/C2/C3.

`OBSERVABLES`: finite/scale counts, saturation fraction, $d_{\rm eff}$, eigenvalue ratio, active-feature/sample guard, $L_P,L_0,L_1,B,G$, shuffle/word controls와 비판정용 fixed-sign stress diagnostic.

`RESIDUAL_RULE`: section 9의 단계별 hard gate와 predictive gain.

`FALSIFIER`: baseline이 persistence를 못 이김, ordered gain 비양수, refit shuffle 동등·우월, word 의존, LARGE 비복제.

`MATCHED_CONTROLS`: 동일 transform·features의 $M_0$, rest, 20 refit increment-order shuffle, leave-one-word-out, 세 predecessor QC diagnostic. 단순 area 부호반전은 matched control이 아니다.

`MODEL_SELECTION`: outcome 기반 선택 없음. $d,H,\Delta,\kappa,\lambda$, feature와 threshold 전부 고정.

`REVISION_TRIGGER`: parser/receipt 결함만 같은 판본에서 수정한다. 식·transform·split·threshold·target·feature 변경은 새 계약이며 열린 split을 재사용할 수 없다.

`CLAIM_CEILING`: `L3_REAL_HUMAN_SCALP_EEG / ORDERED_HISTORY_OBSERVATION_QUOTIENT_PILOT_ONLY / SELF_ONTOLOGY_CONSCIOUSNESS_DIMENSION_EDGE_CONDUCTANCE_HIPPOCAMPAL_HASH_UNIDENTIFIED / POPULATION_AND_CAUSAL_GENERALIZATION_PROHIBITED`.
