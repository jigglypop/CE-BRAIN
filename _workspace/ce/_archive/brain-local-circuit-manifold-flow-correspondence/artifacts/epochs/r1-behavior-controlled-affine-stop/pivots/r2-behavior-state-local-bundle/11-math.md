# R2 수학·통계 사전검산

Status: COMPLETE

이 검산은 R2 결과를 열기 전에 계약 식과 판정 규칙만 대상으로 했다. R0/R1의
수치 실패는 predecessor witness로만 사용했으며 DANDI `001695`는 열지 않았다.

## 정의역과 분해

train-only 표준화 뒤 $x_t\in\mathbb R^N$, $\phi_t\in\mathbb R^6$는
무차원이다. 행동-only 함수 $c$가 $s_t=c(\phi_t)$를 정하고, chart $i$의
orthonormal $U_i\in\mathbb R^{N\times d}$에 대해

$$
P_i^\perp=I-U_iU_i^\top,
\qquad
z_t=U_i^\top(x_t-\mu_i),
\qquad
y_t=P_i^\perp(x_t-\mu_i)
$$

로 분해한다. $U_i^\top U_i=I_d$이므로 $P_i^\perp$는 대칭 직교 projector이고
$x_t-\mu_i=U_iz_t+y_t$가 정확하다. 후보의 출력도 마지막 normal projection
뒤 같은 ambient $\mathbb R^N$에 있으므로 target과 차원이 일치한다.

## 수축 certificate

chart $i$ 안에서 $x_t$의 normal 성분에 대한 도함수는

$$
L_i=P_i^\perp\operatorname{diag}(a_i)P_i^\perp
$$

이다. 따라서

$$
\|L_i\|_2
\le \|P_i^\perp\|_2^2\|\operatorname{diag}(a_i)\|_2
=\max_j|a_{ij}|=q_i^{\rm ub}.
$$

clipping 없이 $q_i^{\rm ub}<1$이면 선언한 chart 내부 normal map의 충분 수축
조건이다. 이는 switching 경계의 연속성, bunching, invariant graph 또는 biological
attraction을 보이지 않는다.

## 자유도와 support

| 모형 | chart당 penalized coefficient와 intercept 수 | 최소 scalar constraint | gate |
|---|---:|---:|---|
| local full-VAR+input | $(N+7)N$ | $n_iN$ | $n_i>N+7$ |
| R2 dynamics | $d(d+7)+N(d+8)$ | $n_iN$ | 위 full-VAR gate가 더 강함 |
| local tangent/mean nuisance | $Nd-d(d+1)/2+N$ | train chart의 $n_iN$ 값 | train-only SVD/mean, $d<n_i$ |

$N=295$이면 full-VAR는 output당 302개 계수·intercept를 가지며 최소 허용 row는
303개다. 이 gate는 scalar constraint 수가 자유계수 수보다 많게 하지만 condition
number가 좋다는 보장은 아니다. 모든 ridge $\lambda>0$는 finite design에서 유일한
penalized 해를 주며, rank와 condition diagnostic은 결과에 기록하되 생물량으로
해석하지 않는다.

## 판정 규칙

동일 row와 양의 공통 분모를 쓰므로 squared-error 차이의 부호와 NMSE 차이의
부호는 같다. 세 comparator 각각에 대해

$$
1-\frac{\operatorname{NMSE}_{\rm R2}}
        {\operatorname{NMSE}_{\rm control}}\ge0.01
$$

이고 paired block-bootstrap error-improvement 하한이 양수여야 한다. 세 조건의
교집합을 gate로 쓰므로 유리한 comparator 선택은 없다. 각 95% 구간을 joint 95%
confidence statement로 해석하지 않는다.

100-bin shift는 chart label만 이동하고 $\phi_t$, $x_t$, target은 보존한다. 따라서
이는 행동 입력 전체가 아니라 **동시 chart assignment**의 adverse control이다.
shifted model도 다시 train/development fit하고 동일 support gate를 지나므로 real
model의 parameter selection 이점을 그대로 두지 않는다.

## 누출·경계 검산

- chart 중심, neural mean, tangent, scaling과 unit retention은 train-only다.
- $d$와 $\lambda$만 development에서 고른다. $K=4$, feature, 문턱과 분모는 고정이다.
- chronological evaluation은 R2 계수 선택에 들어가지 않지만 R0/R1에서 asset이
  이미 열렸으므로 independent holdout이 아니다.
- DANDI `001695`는 R2에 사용하지 않는다고 계약과 portfolio가 함께 고정한다.
- tangent projector 거리와 principal angle은 descriptive이며 PASS gate가 아니다.

## 우선순위 발견과 수리

초안에는 Lloyd 100회 뒤 비수렴 처리, NMSE 분모, shifted support, transition 방향
합산이 모호한 P1 네 건이 있었다. 결과 접근 전에 계약을 각각
`CHART_NOT_CONVERGED`, 명시적 $D$, 동일 support gate, 양방향 합산 unordered pair로
고쳤다. 수정 뒤 P0/P1은 없다.

P2 경계는 두 가지다. full VAR은 통계 baseline이지 세포 기전식이 아니며,
세 개의 개별 95% interval을 joint coverage로 부를 수 없다. 계약의 claim ceiling이
두 해석을 금지한다.

## 재현

```text
PYTHONDONTWRITEBYTECODE=1 python3 artifacts/epochs/r1-behavior-controlled-affine-stop/pivots/r2-behavior-state-local-bundle/verify_contract_math.py
```

결과는 `PASS_CONTRACT_IDENTITIES_ONLY`; 고정 fixture에서 exact projected norm
`0.8386198201`은 upper bound `0.91` 이하였고, $N=295$ support 계산은 output당
302 parameters와 최소 303 rows를 재현했다. 이 fixture는 계약 항등식 검사일 뿐
신경 자료 증거가 아니다.
