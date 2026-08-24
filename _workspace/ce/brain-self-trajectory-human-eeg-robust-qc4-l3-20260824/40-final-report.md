# BA-SRM4-L3 최종 보고서 — R0 기준식 STOP

Status: COMPLETE

Final disposition: `APPARATUS_INVALID_OR_BASELINE_UNRESOLVED`

## 초록

이 실행은 공개 inner-speech scalp EEG에서 현재 관측 상태만 쓰는 고정 기준식 $M_0$가 persistence보다 미래 100 ms 변화를 예측할 수 있는지 먼저 검사하고, 그 조건이 충족될 때만 400 ms 순서 경로 feature를 더한 $M_1$을 열도록 설계했다. 전류 보존·막전류·history-dependent synaptic efficacy는 생물물리적 출발점으로 사용했지만, 무한 history 상태와 Riemann metric은 명시된 모델 공리로 남겼다. Signal-blind R0는 session마다 5 pair씩 총 10 pair와 20개 window를 정확한 byte range로 읽었고, range·provenance·finite/nonflat·conditioning·표본 guard를 통과했다. 그러나 task 기준식의 persistence 대비 gain은 held-out `ses-01`에서 $-3.6460501404125005$, `ses-02`에서 $0.0025103259988423846$, pooled에서 $-0.40260785355519274$였으며, 방향별 양수와 pooled 양수라는 사전 gate를 만족하지 못했다. 따라서 이 결과는 $M_0$ feasibility의 음성 판정이며, $M_1$ path area, shuffle, word 분석과 R1/R2/C1/C2/C3는 열지 않았다. 이 STOP은 무한차원 edge state, 실제 Riemann metric, 자아, 의식 또는 해마 주소 가설의 검증·반증이 아니다.

## 문제와 주장 경계

이 보고서가 다루는 질문은 "고정된 EEG 관측·전처리 아래에서 현재 상태 기준식이 persistence를 이긴 뒤, 과거 increment의 순서가 미래 EEG increment 예측에 추가 정보를 주는가"이다. 이 질문은 자아나 의식의 존재론을 직접 판정하지 않으며, EEG channel에서 neuron edge conductance나 뇌 전체의 metric을 역산하는 질문도 아니다. 따라서 본문에서 생물물리 출발식, 수학적 후보 공간, 측정식, 사전 고정 경험 비교를 구분한다.

**[정의: 생물물리 출발식]** 막전위 $V$에 대한 cable/current-conservation 출발식은 다음과 같다.

$$
c_m(x)\,\partial_t V
=
\nabla_\Gamma\!\cdot\!\bigl(\sigma(x)\nabla_\Gamma V\bigr)
-I_{\rm ion}(V,w)
-I_{\rm syn}(V,h_t)
+I_{\rm ext}.
$$

이 식은 compartment 모형의 출발점이며, chemical current $I^{\rm chem}_{j\to i}=g_{ji}[h_{ji,t}](V_i-E_{ji})$와 gap current $I^{\rm gap}_{ij}=g^{\rm gap}_{ij}(V_j-V_i)$를 포함할 수 있다. 여기서 history가 유효 coupling을 바꿀 수 있다는 사실은 출처가 뒷받침하지만, 아래의 함수공간과 metric을 실제 인간 뇌가 유일하게 따른다는 뜻은 아니다.

**[공리: 모델 선택]** 기준 전압·시간·conductance 척도로 무차원화한 상태를

$$
q_\tau=(v(\tau),w(\tau),h_\tau)
\in\mathcal M
=\mathbb R^{N_v+N_w}\times L^2_\rho(( -\infty,0],\mathbb R^m)
$$

로 둔다. Filtered spike, 전압, gate, 조절 trace를 담은 $h_\tau$ 때문에 이 후보 상태공간은 무한차원이다. $\mathcal G_{ij}[h_{ij,\tau}]>0$가 causal $C^\infty$ functional이고 계수와 kernel이 아래 조건을 만족한다고 가정할 때만, edge와 history가 tangent 거리로 기여하는 후보 metric $G_q$를 말할 수 있다.

**[정리: 조건부 metric]** $a_i(q)$가 양의 균일 상·하한을 갖고, $K_{ij}(q,\theta)$가 self-adjoint·smooth·균일 bounded/coercive이며 $\rho(\theta)>0$이면,

$$
\begin{aligned}
G_q(\xi,\eta)
={}&\sum_i a_i(q)\xi_{v_i}\eta_{v_i}
+\frac12\sum_{i,j}b_{ij}(q)
(\xi_{v_i}-\xi_{v_j})(\eta_{v_i}-\eta_{v_j})\\
&+\sum_{i,j}\int_{-\infty}^{0}
\xi_{h,ij}(\theta)^\top K_{ij}(q,\theta)
\eta_{h,ij}(\theta)\rho(\theta)\,d\theta
\end{aligned}
$$

는 양의 bounded bilinear form을 정의한다. 증명. 첫 항은 $a_i$의 양의 하한으로 finite-dimensional 전압 성분에 양의 하한을 제공하고, 마지막 항은 각 $K_{ij}$의 coercivity와 $\rho>0$로 history norm에 양의 하한을 제공한다. 균일 boundedness와 유한 edge 합 또는 수렴하는 edge 합을 쓰면 Cauchy--Schwarz 부등식으로 $|G_q(\xi,\eta)|\le C\|\xi\|\|\eta\|$를 얻는다. 대칭성은 $K_{ij}$의 self-adjointness 및 대칭 edge 항에서 따르고, 따라서 명시한 가정 아래의 결론만 성립한다. 이 정리는 데이터가 계수나 kernel을 추정했다는 주장이 아니므로, 이 실행의 EEG 결과를 ambient neural metric의 식별로 해석할 수 없다.

## EEG 관측과 사전 고정 비교

**[정의: 측정식]** EEG channel $c$는 잠재 상태 전체가 아니라 volume conduction과 기록 변형을 거친 관측 quotient로만 둔다.

$$
x_c(t)=a_c\,\mathcal O_c(q_t)+b_c+\varepsilon_c(t)+o_c(t).
$$

Training fold에서만 median $m_c$와 robust scale $s_c=1.4826\operatorname{MAD}_c$를 맞추고, $u_{tc}=(x_{tc}-m_c)/s_c$ 및 $\widetilde u_{tc}=4\tanh(u_{tc}/4)$를 사용했다. $u_{tc}/4$는 무차원이고 transform은 bounded이며, median/MAD estimator 자체를 물리 흐름의 $C^\infty$ 성질로 부르지 않는다. 전압·시간·conductance·current·capacitance, $\log p_k$, whitened area, ridge penalty의 핵심 인자는 별도 무차원 검사에서 정합성을 확인했다.

**[정의: 관측 기준식]** PCA/whitening으로 얻은 $d=2$ 관측 좌표 $z_t$에서 target은 $y_t=z_{t+\Delta}-z_t$, $\Delta=0.1\,{\rm s}$다. R0의 $M_0$는 intercept, endpoint의 두 좌표 및 마지막 causal velocity의 두 좌표만 쓰는 $p=5$ ridge 기준식이다. $M_1$은 여기에 $H=0.4\,{\rm s}$ 창의 antisymmetric level-2 area

$$
A_{12}(t;H)=\frac12\sum_{p<q}
\left(\Delta z_p^1\Delta z_q^2-\Delta z_p^2\Delta z_q^1\right)
$$

를 하나 추가하도록 고정했지만, R0 $M_0$ gate 실패 때문에 실행하지 않았다. $d=2$는 계산상 고정한 관측 좌표 차원일 뿐 의식, 자아 또는 실제 뇌 상태의 차원이 아니다.

**[정의: 사전 고정 gain]** persistence predictor $\widehat y=0$의 loss를 $L_P$, 기준식 loss를 $L_0$, path식 loss를 $L_1$로 두고,

$$
B=\frac{L_P-L_0}{L_P},\qquad
G=\frac{L_0-L_1}{L_0}.
$$

로 둔다. $B$는 $L_P>10^{-12}$일 때, $G$는 $L_0>10^{-12}$일 때만 정의한다. R0에서는 $B_{\rm task}$가 두 LOSO 방향과 pooled 모두 양수여야 했고, 이 baseline feasibility를 통과한 뒤에만 $G$와 $M_1$을 열 수 있었다.

## no-go와 대조군의 지위

**[정리: state/path no-go]** 임의의 유한 history feature $H_t$를 사용하는 예측기는 augmented state $S'_t=(S_t,H_t)$의 instantaneous function으로 다시 쓸 수 있다. 증명. $S'_t$의 정의에 $H_t$를 포함했으므로, 원래 predictor $f(S_t,H_t)$에 대해 $\widetilde f(S'_t)=f(S_t,H_t)$로 두면 된다. 그러므로 장래에 $M_1>M_0$이 성립하더라도, 그 결과는 선택한 관측 baseline에 비해 ordered-history 정보가 더 있었다는 뜻일 뿐 자아가 존재론적으로 state가 아니라 path임을 증명하지 않는다.

단순히 increment 순서를 뒤집으면 $A_{12}\mapsto-A_{12}$이지만, scalar area를 쓰는 선형 ridge는 $\beta\mapsto-\beta$로 재적합되어 fitted prediction과 penalty가 같다. 이 때문에 sign reversal은 유효한 matched null이 아니며 최종 gate에서 제외했다. 계약은 마지막 increment를 고정한 채 이전 increment만 trial-hash seed로 20회 순열화하여 start, endpoint, displacement, energy, 마지막 velocity와 increment multiset을 보존하고 area만 바꾸도록 했다. 이 shuffle은 향후 $M_1$이 열릴 때의 artificial order-destruction contrast이지 p-value나 인과적 null이 아니며, 이번 STOP에서는 실행하지 않았다.

## R0 실행과 수치 비교

Signal-blind allocation은 predecessor의 D2-M 100 pair를 session별 hash 순서로 R0/R1/R2의 10/20/70 pair로 배정했다. R0는 `ses-01`과 `ses-02`에서 각각 5 pair의 task/rest를 열어 20개 window를 읽었고, 모든 request는 HTTP `206` 및 정확히 768,256 byte를 반환했다. Manifest, parser, allocation, provenance, finite/nonflat, conditioning, loss denominator와 $n=p+5=10$ design guard는 통과했으며, 이 범위의 apparatus/range 실행 지위는 **[조건부 산출: apparatus/range execution]** `PASS`다.

그 뒤 사전 고정된 $M_0$를 persistence와 비교한 결과는 다음과 같다. `ses-01`의 task loss는 $L_0=1.587008161968733$, $L_P=0.3415822287763408$로 $B_{\rm task}=-3.6460501404125005$였고, `ses-02`에서는 $L_0=2.727897944886762$, $L_P=2.734763091776724$로 $B_{\rm task}=0.0025103259988423846$였다. Pooled task loss는 $L_0=2.157453053427748$, $L_P=1.5381726602765324$로 $B_{\rm task}=-0.40260785355519274$였으며, pooled rest도 $B_{\rm rest}=-0.9334834668020284$였다.

즉 `ses-02`의 미세한 양수만으로 `ses-01`의 큰 음수와 pooled 음수를 상쇄할 수 없으며, 사전 고정한 directional-plus-pooled gate는 거짓이다. 이 결과는 **[산출: preregistered negative comparison]** `M0_BASELINE_STOP`이며, 최종 상태는 `APPARATUS_INVALID_OR_BASELINE_UNRESOLVED`다. 명칭의 apparatus는 신호 byte range 자체가 실패했다는 뜻이 아니라, 이 run에서 path 비교를 정당화할 기준 예측 apparatus 또는 baseline이 해결되지 않았다는 fail-closed 분류다.

## 미개방 endpoint와 후속 경계

`path_area_opened=false`, `ordered_history_gain_opened=false`, `word_effect_opened=false`다. 따라서 $M_1$, level-2 area, constrained shuffle, word effect, ordered-history 경험 후보는 모두 **[미완성: 미검증]**이다. R1-MEDIUM, R2-LARGE 및 C1/C2/C3도 sealed 상태이며, 이번 R0의 실패를 이용해 같은 run에서 baseline, target, feature, threshold 또는 gate를 바꾸어 재실행할 수 없다.

이 결과는 neuron-level edge conductance, 실제 무한차원 Riemann metric, cortical curvature/holonomy, 자아, 의식, 해마의 sparse address 또는 cryptographic hash를 식별하지 못한다. Robust scaling과 bounded transform은 넓은 artifact를 숨길 수도 있고, B1과 D2-M은 같은 `sub-02` recording 계열이므로 설령 뒤 단계가 열렸더라도 독립 subject/recording 복제가 아니다. 후속 시험은 이 R0 material을 development evidence로 소진 처리하고, 새 계약에서 새 signal-blind split, 새 baseline falsifier, measurement/QC 경계 및 보존할 confirmation set을 결과 보기 전에 고정해야 한다.

## 재현 경로

이 보고서는 contract `04ea2bb2166916120bebf25c546646dd59f4bd20b4c97c4e9ba5de28f70a174d`, sources `207ccb209276ab85435b2b864571e4511306f1b966ff6d24b36aa2023120f6ff`, math `898960658ada3a181f2da1e9e87414135508e7e7a301ff609b0d98332c5acece`, routes `fb82f423ac8c928bcacad0d63deb073ad7668e2a55ceca1e51ba1054c31c5fa8`의 동결 내용에 근거한다. R0 receipt의 SHA-256은 `3bd9db6c2c2519075437bdd142c742f361a6efabc68376a7c786fd9d6f9dd61b`이고, 구현 및 focused test의 SHA-256은 각각 `6c8e3522c9b4a230196ee65f8eebc6dce58e2c030440cfa4a0c448ab7c3486ea`, `511a1aeeed669277a4df0bcd0cd048b42cb150a63a06498dc7b80275d4e0a5e5`다. 아래 첫 명령은 코드 경계 검증이며, 둘째 명령은 receipt를 읽는 경로 확인이다. 네트워크 실행 또는 `--execute`로 새 endpoint를 열어 이 동결 run을 재시도해서는 안 된다.

```powershell
.codex\hooks\python.cmd pytest _workspace\ce\brain-self-trajectory-human-eeg-robust-qc4-l3-20260824\artifacts\test_srm4_real_eeg.py -q
.codex\hooks\python.cmd python -m json.tool _workspace\ce\brain-self-trajectory-human-eeg-robust-qc4-l3-20260824\artifacts\r0-receipt.json
```

Focused validation은 Python 3.11.9에서 `12 passed in 1.03s`였고, 이는 allocation, fail-closed guard, training-only transform 및 synthetic identifiability fixture의 구현 속성만 확인한다. 실측 R0 결과의 원본 경로는 `artifacts/r0-receipt.json`, 고정 split은 `artifacts/srm4-allocation.json`, 실행 코드와 검증은 각각 `artifacts/srm4_real_eeg.py`, `artifacts/test_srm4_real_eeg.py`다.

## 1차 참고문헌

Rall, W. (1977). *Core Conductor Theory and Cable Properties of Neurons*. DOI: [10.1002/j.2040-4603.1977.tb00811.x](https://doi.org/10.1002/j.2040-4603.1977.tb00811.x). Hodgkin, A. L., & Huxley, A. F. (1952). *A quantitative description of membrane current and its application to conduction and excitation in nerve*. DOI: [10.1113/jphysiol.1952.sp004764](https://doi.org/10.1113/jphysiol.1952.sp004764). Ghanbari, A. et al. (2017). *Estimating short-term synaptic plasticity from pre- and postsynaptic spiking*. DOI: [10.1371/journal.pcbi.1005738](https://doi.org/10.1371/journal.pcbi.1005738).

Brunner, C. et al. (2016). *Volume Conduction Influences Scalp-Based Connectivity Estimates*. DOI: [10.3389/fncom.2016.00121](https://doi.org/10.3389/fncom.2016.00121). OpenNeuro dataset `ds006033` v1.0.1, DOI: [10.18112/openneuro.ds006033.v1.0.1](https://doi.org/10.18112/openneuro.ds006033.v1.0.1). Inner-speech EEG data article, DOI: [10.1016/j.dib.2025.112258](https://doi.org/10.1016/j.dib.2025.112258).
