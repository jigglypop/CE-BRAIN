# BA-OBS-DISC1 mathematics lane — 무차원 전기·기하 kernel과 식별 경계

Status: COMPLETE

## 1. 조건부 전기 semigroup

**[조건부 정리]** 유한 관측 절단에서 $C=C^\top\succ0$이고
$A=L_g+J_{\rm ion}$가 고정이며 $C^{-1}A$가 안정하면, impulse 뒤의 선형 반응은

$$
v(t)=e^{-C^{-1}At}C^{-1}Bq
$$

이다. 이는 선형 ODE의 해이며 실제 뇌가 시간불변 선형계라는 정리가 아니다. 관측은
$y=C_{\rm ref}Rv+a+\eta$이므로 finite CCEP만으로 $A$, $R$, $C_{\rm ref}$을 분리할 수 없다.

## 2. Heat-kernel 후보의 유도와 차원 해석

smooth $q$-dimensional Riemannian manifold의 short-time heat kernel은 조건부로

$$
K(t,r)\sim(4\pi Dt)^{-q/2}
\exp\!\left[-\frac{\ell_g^2}{4Dt}-\frac{t}{\tau}\right]
\sum_{j\ge0}a_jt^j
$$

꼴이다. leading log-amplitude를 취하고 $t_0=50$ ms, $\ell_0=50$ mm로 정규화하면

$$
x=t/t_0,\quad r=\ell/\ell_0,
$$

$$
\log K\approx\beta_0-\frac q2\log x-\kappa\frac{r^2}{x}-\lambda x.
$$

여기서 $\kappa=\ell_0^2/(4Dt_0)$, $\lambda=t_0/\tau$는 무차원이다. 실제 target은
signed Green function이 아니라 montage를 거친 bin RMS energy이므로 fitted $q$는
`effective kernel-shape exponent`다. $q$가 연속으로 적합되는 것은 유효 지수를 허용한다는
뜻이지 topological dimension이 연속이라는 증명이 아니다.

## 3. 무차원 감사

| 식의 core 인자 | 원래 차원 | 정규화 | 차원 벡터 $(M,L,T,\Theta)$ |
|---|---|---|---|
| $\log x$ | $t:T$ | $x=t/(50\,\mathrm{ms})$ | $(0,0,0,0)$ |
| $r, r^p$ | $\ell:L$ | $r=\ell/(50\,\mathrm{mm})$ | $(0,0,0,0)$ |
| $r^2/x$, $r^p/x$ | $L^2/T$ 또는 $L^p/T$ before scale | $r,x$ 사용 | $(0,0,0,0)$ |
| $x'=x-\delta r$ | mixed before scale | $\delta$ dimensionless; physical report가 ms/mm | $(0,0,0,0)$ |
| $e^{-x'/\theta}$ | $t/\tau$ | $x',\theta=\tau/t_0$ | $(0,0,0,0)$ |
| $e^{g_x},e^{g_y}$ | none | $g_x,g_y$ dimensionless | $(0,0,0,0)$ |
| $u_1^\top\Delta X/\ell_0$ | $L$ | $/50$ mm | $(0,0,0,0)$ |
| $\log(E+10^{-6})$ | voltage/scale | $E$와 floor 모두 dimensionless | $(0,0,0,0)$ |

차원 상태: **무차원**. 이는 차원 정합 판정이지 물리적 참 판정이 아니다.

코드 검증:

```text
.codex/hooks/python.cmd pytest tests/test_dimensionless.py -q
19 passed in 0.38s
.codex/hooks/python.cmd python reality_stone/python/reality_stone/clarus/dimensionless.py
exit 0
```

## 4. Split의 독립성 수준

151 unordered pairs의 endpoint를 보지 않고 MNI-distance strata와 salted pair hash만으로
24/48/39/40을 만든다. 이 분할은 response-signal independent다. 그러나 같은 stimulation
site의 trial average가 여러 receiver pair에 재사용되므로 pair들이 iid는 아니다.

**[산출]** 따라서 primary uncertainty unit은 pair가 아니라 stage에 실제 등장한 stimulation
source다. Source별 평균 loss difference를 equal-weight source-cluster bootstrap하며 pair와
half를 다시 iid resample하지 않는다. 이것은 shared-source dependence를 보수적으로 반영하지만
한 환자 안의 source cluster가 population subject uncertainty를 대신하지는 않는다.

## 5. 작은 표본의 식별성 no-go와 제한

D0에는 24 unordered pairs, 48 directed edges가 있다. 자유 source gain 24개와 receiver gain
24개를 적합하면 intercept까지 사실상 포화하므로 geometry 식이 아니라 pair lookup이 된다.
같은 이유로 24-node low-rank directed factor와 pair별 delay/gain을 금지한다.

허용 후보는 최대 7 parameters이며 directionality는 endpoint-blind MNI principal axis 하나,
anisotropy는 determinant-one diagonal $G$의 두 parameters로 제한한다. 비선형 후보는 12
multi-start 수렴, full-rank numerical Jacobian, condition number와 boundary gate를 통과해야
한다. $x'\le0$ delay cell을 floor로 숨기는 fit은 infeasible이다.

이 gate가 통과해도 full system identification은 아니다. 서로 다른 $(C,A,R)$가 같은 finite
readout을 만들 수 있으므로 ambient/infinite-dimensional metric은 여전히 비식별이다.

## 6. Prediction comparison과 falsifier

Geometry-free B0와 후보 winner의 paired Huber loss 차이를

$$
\Delta_s=\mathcal L_{B0,s}-\mathcal L_{W,s}
$$

로 둔다. Held-out geometry tuple $(r,\Delta X,u_1^\top\Delta X)$를 joint-permute하면 time
profile과 response 값은 유지한 채 geometry association만 끊는다. 고정 train fit에 대해
source-cluster lower confidence bound가 양수이고 permutation $p\le0.05$일 때만 bipolar
prediction gate를 통과한다.

이 결과가 지지하는 명제는 다음보다 강할 수 없다.

> 제한된 single-subject observed CCEP energy에서 해당 MNI geometry descriptor를 사용하는
> winner가 geometry-free temporal baseline보다 그 stage의 held-out prediction을 개선했다.

Heat equation, Riemannian metric, axonal path 또는 상태공간 차원의 증명은 아니다.

## 7. Mathematics-lane disposition

`CONDITIONALLY_WELL_FORMED / DIMENSIONLESS / FINITE_OBSERVATION_ONLY`.
실제 데이터 전의 수학 blocker는 없다. 경험식 선택과 순차 gate 결과가 필요하다.
