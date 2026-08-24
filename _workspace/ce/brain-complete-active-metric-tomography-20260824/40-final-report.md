# BA-OBS-ID2 최종 보고서 — 무한차원 강한 계량의 완전 능동 tomography

Status: COMPLETE

Decision: PASS

Evidence level: MATHEMATICAL THEOREM + L0 DETERMINISTIC SYNTHETIC VALIDATION

## 1. 결론

이번 판본은 이전 finite-family/local 식별성 제한을 두 방향에서 제거했다.

첫째, 고정 readout 뒤의 derivative가 uniform strong monotonicity를 만족하면
parameter 공간이 무한차원이어도 forward map은 전역 lower-Lipschitz이며 단사다.

둘째, 실 separable Hilbert 공간에서 임의의 bounded self-adjoint coercive metric
$G$에 대해, mobility $M=G^{-1}$의 quadratic onset response

$$
Q_G(f)=\langle f,Mf\rangle
$$

를 complete basis의 diagonal 및 pair directions에서 모두 exact하게 읽으면

$$
\{Q_G(f):f\in\mathscr D\}
\Longrightarrow
\{\langle e_i,Me_j\rangle:i,j\ge1\}
\Longrightarrow M\Longrightarrow G
$$

가 성립한다. 따라서 **가산 완전 exact active-response regime에서는 arbitrary strong
metric의 전역 유일 식별 no-go가 제거된다.**

다만 유한 passive 또는 유한 exact active query에는 orthogonal blind tail이 남는다.
이 유한-data no-go는 참이므로 삭제하지 않았고, $w_N$ adverse control로 수치 재현했다.

## 2. 닫힌 수학 결과

- **[정리 T4]** Uniform strong monotonicity 아래 global stable identifiability.
- **[정리 T5]** Countably complete exact quadratic response 아래 arbitrary bounded
  strong metric의 global unique tomography.
- **[따름정리 C3]** $N^2$ query finite section의 mobility와 metric은 strong operator
  topology에서 참 operator로 수렴한다.
- **[따름정리 C4]** Weighted Hilbert--Schmidt decay와 aggregate noise 감소 아래
  finite/noisy operator-norm error가 명시적 상계로 제어된다.
- **[정리]** 모든 유한 query 집합에는 같은 response를 내는 same-class tail
  perturbation이 존재한다.

수학 stable-snapshot 감사와 구현 stable-snapshot 감사 모두 `P0: none`, `P1: none`으로
끝났다. 전체 증명은 `11-math.md`, 독립 수학 감사는 `20-audit.md`에 있다.

## 3. 합성 수치 검증

동결 witness는

$$
M=I+0.5,v\otimes v,
\qquad
v_n=\sqrt{1-0.6^2}\,(0.6)^{n-1}
$$

인 genuine infinite-support rank-one operator다. Query 식, 순서, noise, $N$ menu,
clipping interval과 gate를 결과 전에 고정했다.

| $N$ | queries | exact block error | noisy raw error | clipped error | mobility HS tail | metric HS tail |
|---:|---:|---:|---:|---:|---:|---:|
| 4 | 16 | $1.862\times10^{-16}$ | $2.646\times10^{-8}$ | $2.098\times10^{-8}$ | $9.126\times10^{-2}$ | $6.086\times10^{-2}$ |
| 8 | 64 | $3.713\times10^{-16}$ | $4.690\times10^{-8}$ | $3.966\times10^{-8}$ | $1.188\times10^{-2}$ | $7.917\times10^{-3}$ |
| 16 | 256 | $6.401\times10^{-16}$ | $8.718\times10^{-8}$ | $7.817\times10^{-8}$ | $1.995\times10^{-4}$ | $1.330\times10^{-4}$ |
| 32 | 1024 | $1.383\times10^{-15}$ | $1.673\times10^{-7}$ | $1.560\times10^{-7}$ | $5.628\times10^{-8}$ | $3.752\times10^{-8}$ |

모든 frozen gate가 통과했다. Exact block 오차는 $10^{-12}$보다 작고, noisy block
오차는 사전 상계 $\eta_N+10^{-12}$ 안에 있다. 두 analytic tail은 고정 grid에서
엄격히 감소했고 $N=32$에서 $10^{-7}$ 아래로 내려갔다. Clipped eigenvalues는
$[1,1.5]$에 남았다.

Adverse mobility

$$
M^{\rm alt,N}=M+0.10,w_N\otimes w_N,
\qquad
w_N=\frac{0.6e_{N+1}-e_{N+2}}{\sqrt{1+0.6^2}}
$$

는 동일 spectral class에 있으면서 첫 $N^2$ query에서 response 차이가 0이었다.
Held-out $w_N$ response 차이는 `0.10000000000000005`였다. 이는 유한 stage의 성공을
무한 operator 완전 복원으로 오독하지 못하게 하는 matched adverse control이다.

## 4. 재현 증거

| artifact | SHA-256 |
|---|---|
| contract | `2d4fa1a6010137a599984413cf1305479e776b7b5ea5a34a9d0a0b6aa1bbff0d` |
| mathematics | `2ed549a01d11ad4c209f766a329085bbf1065fcc64aaf460029e46eb113ddbab` |
| stable audit | `dde2f5bbf9d61be430adcfb7710f68eef369bed0f699af10528c4e3e6c36f32f` |
| validator | `e9f2e70775c4200a2ad8f46bd2b6c740f70a875d8b45f46135ab883e5f1b8572` |
| receipt | `080f22c9f2c4e03e31f95db73a0f8d1dfd72927ddb3254bd7a2ccaaddbad3743` |
| implementation note | `8af0dae01ce44094211ee76eda0887d8544dcbd0cf2b4a7cddc11878160434c0` |
| validation note | `6ffdbfa67d2795d918214ed8f07cdc9fd9a9e7f0b3f73d62244e4c256ef77b0b` |

Windows hook는 Python 3.11.9와 NumPy 2.4.6을 기록했다. Validator source compile과
focused execution이 PASS했다. 별도의 기존 무차원 회귀는 `19 passed in 0.33s`였다.
전체 test suite는 이 독립 artifact와 무관하므로 실행하지 않았다.

## 5. 뇌·의식 이론과의 현재 거리

이번 결과가 없앤 것은 **수학적 정보 완전성 아래의 arbitrary-metric 식별 장벽**이다.
실제 뇌에서는 A1의 독립 reset, arbitrary basis force, exact onset response와 countably
complete experiment를 아직 확보하지 못했다. 따라서 이 결과만으로 neuron edge가
metric coordinate인지, 의식이 저차원 present-world manifold인지, 자아가 상태 궤적의
연속성인지, 해마가 hash 역할을 하는지 판정할 수 없다.

다음 실제-뇌 단계는 정리를 다시 바꾸는 일이 아니다. 생물학적으로 허용되는 자극과
측정 연산자가 어느 query subspace를 실제로 span하는지 밝히고, 그 restricted
observability에서 유한 차수의 metric coefficient 또는 spectral summary를 held-out
개입 자료로 검증해야 한다.

## 6. 형식 지위와 claim ceiling

- **[공리]** A1: 독립 reset, known force, exact/noisy scalar onset response.
- **[정리]** T4, T5 및 finite-query blind-tail theorem.
- **[따름정리]** C3, C4.
- **[산출]** Rank-one analytic tails와 same-class adverse witness.
- **[예측]** 없음. 실제 뇌 데이터에 대한 사전 고정 예측은 이번 run에 포함하지 않았다.
- **[미완성]** A1의 생물학적 realization, canonical neural basis, measurement-model
  parity, real-brain intervention, consciousness/self/hippocampus/AGI bridge.

Claim ceiling:
`GLOBAL_IDENTIFICATION_OF_AN_ARBITRARY_STRONG_METRIC_UNDER_COUNTABLY_COMPLETE_ACTIVE_QUADRATIC_RESPONSE / GLOBAL_STABLE_IDENTIFIABILITY_UNDER_UNIFORM_STRONG_MONOTONICITY / STRONG_OPERATOR_RECOVERY_AND_HS_FINITE_NOISY_BOUND / FINITE_PASSIVE_AND_FINITE_EXACT_FULL_RECOVERY_STILL_IMPOSSIBLE / SYNTHETIC_ONLY / NO_EMPIRICAL_BRAIN_CONSCIOUSNESS_SELF_OR_AGI_VALIDATION`.
