# BA-SRM4-L3 mathematics lane

Status: COMPLETE

Contract SHA-256: `04ea2bb2166916120bebf25c546646dd59f4bd20b4c97c4e9ba5de28f70a174d`

## 1. 무차원 감사

| 항 | 원래 단위 | 정규화 | core 상태 |
|---|---|---|---|
| $V,E$ | voltage | $(V-E_*)/V_*$ | 무차원 |
| $t$ | time | $t/t_*$ | 무차원 |
| $g$ | conductance | $g/g_*$ | 무차원 |
| $I$ | current | $I/(g_*V_*)$ | 무차원 |
| $C$ | charge/voltage | $C/(g_*t_*)$ | 무차원 |
| robust residual | voltage/voltage | $u=(x-m)/s$ | 무차원 |
| tanh 인자 | — | $u/4$ | 무차원 |
| PCA spectrum | variance ratio | $p_k=\lambda_k/\sum_j\lambda_j$ | 무차원 |
| entropy 인자 | — | $\log p_k$ | 무차원, $0\log0=0$ |
| path area | whitened coordinate squared | $A_{12}$ | 무차원 |
| ridge penalty | standardized design | $\lambda=1$ | 무차원 |

표준 CE dimensionless 검증은 `.codex\hooks\python.cmd pytest tests\test_dimensionless.py -q -p no:cacheprovider`에서 `19 passed in 0.37s`였고 checker는 exit code 0이었다. 이는 계약 식의 물리적 진실이 아니라 core 인자의 차원 정합성 증거다.

## 2. 전기식과 metric의 조건부 완결성

[정의] cable PDE에서 compartment 식으로 갈 때 $C_i=\int_{\Omega_i}c_m dx$와 $g^{\rm ax}_{ij}=\sigma A/\ell$를 사용한다. 이 공간 이산화 뒤 $C_i/(g_*t_*)$가 무차원이다.

[공리: 모델 선택] history는 ideal delta spike가 아니라 filtered trace를 포함한 $L^2_\rho$ 원소다. $\mathcal G:H_\rho\to\mathbb R_+$가 지정 topology에서 causal $C^\infty$라고 가정한다.

[정리: 조건부] $a_i$가 양의 균일 상·하한을 갖고, $K_{ij}$가 self-adjoint·smooth·균일 bounded/coercive이며 $\rho>0$이면 계약의 $G_q$는 양의 bounded bilinear form을 정의한다. 이 조건을 데이터가 추정한 것이 아니므로 ambient neural metric의 경험적 식별로 승격하지 않는다.

## 3. CAR와 affine 범위

물리적 channel별 gain $D$와 common-average matrix $C$는 일반적으로 교환하지 않는다. 두 channel에서 $x=(1,-1)$, $D=\operatorname{diag}(2,1)$이면 $C(Dx)=(1.5,-1.5)$지만 $D(Cx)=(2,-1)$다. 따라서 pre-CAR channel별 gain 불변성 주장은 거짓이며 계약에서 제거했다.

공통 nonzero gain과 시간불변 channel offset은 CAR, fold-local median/MAD와 odd tanh 뒤 예측 geometry가 동치다. post-CAR channel별 affine map은 부호 대각변환과 PCA subspace rotation을 만들 수 있으므로 raw PCA 좌표가 아니라 Gram matrix와 refit prediction loss의 orthogonal equivariance만 검사한다. degenerate eigenvalue에서는 좌표축 자체를 비교하지 않는다.

## 4. 경로 area와 대조군

[산출] increment 순서를 완전히 역전하면 $A_{12}\mapsto-A_{12}$다. 그러나 scalar area를 가진 linear ridge를 재적합하면 coefficient도 $\beta\mapsto-\beta$가 되어 fitted prediction과 penalty가 정확히 같다. 그러므로 단순 sign reversal은 matched orientation null이 아니다.

[예측] 고정된 마지막 increment를 제외한 이전 increment만 trial-hash seed로 순열화한다. 이때 start, endpoint, displacement, energy, 마지막 velocity와 increment multiset은 보존되고 area만 달라진다. 매 shuffle에서 training과 held-out area를 같이 만들고 $M_1$을 재적합하므로 $M_0$ 정보와 model capacity가 맞는다. 이는 artificial order-destruction contrast이며 교환가능성·인과검정이나 p-value가 아니다.

## 5. 표본과 design guard

한 pair는 task와 rest의 두 prediction row를 만든다. R0의 LOSO training은 session당 5 pair, 즉 10 row이고 $p=5$라서 $n=p+5$를 만족한다. R1은 누적 session당 15 pair, 즉 30 row이며 full $M_1$의 최대 raw parameter 수는 intercept를 포함해 19라서 guard를 만족할 수 있다. zero-variance non-intercept 열은 training fold에서 coefficient와 standardized value를 0으로 고정하고 active count에서 제외한다.

task/rest 두 row는 같은 pair에 속하므로 $2N$을 독립 표본 수나 유의확률 계산에 사용하지 않는다. row 수는 design-rank guard에만 쓰고 receipt는 pair-clustered loss도 함께 보고한다. $10^{-2}$ loss margin은 whitening 뒤 무차원인 사전 고정 effect-size threshold이며 significance threshold가 아니다.

$B$와 $G$는 각각 $L_P>10^{-12}$와 $L_0>10^{-12}$일 때만 정의한다. pooled gain은 방향별 gain의 산술평균이 아니라 두 방향 SSE와 scalar count를 합쳐 만든 pooled loss에서 계산한다.

## 6. state/path no-go

[정리] 임의의 유한 history feature $H_t$에 대해 augmented state $S'_t=(S_t,H_t)$를 정의하면 그 history predictor는 $S'_t$의 instantaneous function이다. 따라서 $M_1>M_0$은 선택한 관측 baseline에 상대적인 ordered-history gain만 보이며 self가 존재론적으로 path이고 state가 아니라는 것을 판정하지 못한다.

## Math verdict

원 계약 SHA `51c662ab...`에는 invalid reverse null, CAR 불변성 과장, small-stage design ambiguity와 zero denominator가 있었다. revision 1에서 이를 수정했고 최종 계약 SHA `04ea2bb...`는 독립 재감사에서 `Gate: PASS`를 받았다. 남은 P1은 pair correlation과 fixed effect-size 해석을 receipt에 공개하는 것이다. 실제 EEG 개방을 막는 P0 수학 결함은 없다.
