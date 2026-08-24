# BA-OBS-NOGO1 연구 계약 — 유한 관측의 무한차원 metric 비식별성

Status: COMPLETE

Mode: light mathematics-only continuation

PREDECESSOR: `_workspace/ce/brain-synapse-functional-quotient-qc2-20260823`

CE_RUN: `_workspace/ce/brain-finite-observation-metric-nonidentifiability-20260824`

## 1. 질문

무한차원 neural history Hilbert 공간을 유한 수의 EEG·전극·feature로
수동 관측할 때, 관측 pullback이 전체 공간의 양의 정부호 Riemann metric을
결정할 수 있는가? 결정할 수 없다면 정확히 무엇까지만 식별되는가?

이 run은 새 생물학·의식·AGI 주장을 만들지 않는다. 선행 BA-SRM2/3의
“유한 관측은 quotient만 본다”는 정리를 명시적 비식별 witness까지
강화하고, 성립 범위와 반례 경계를 닫는 것이 목적이다.

## 2. 대상과 무차원 규약

**[정의]** $\mathcal H$는 무한차원 실 Hilbert 공간이고,
$m:U\subset\mathcal H\to\mathbb R^r$는 $C^1$ 유한 관측 map이다.
고정한 $x\in U$에서 $J=Dm_x$로 둔다. 모든 출력은 채널별 기준척도로
먼저 무차원화하며, $W\in\mathbb R^{r\times r}$는 무차원 대칭 양의
정부호 measurement precision이다.

**[정의]** 관측 pullback 형식은

$$
g_x^{\rm obs}(u,v)=\langle Ju,WJv\rangle_{\mathbb R^r}
$$

이다. $K=\ker J$, $X=K^\perp$, $R=\operatorname{ran}J$로 둔다.

## 3. 동결 명제

**[정리 후보 T1: 유한 pullback 퇴화]** $g_x^{\rm obs}$는 양의
준정부호이고

$$
\ker g_x^{\rm obs}=K,
\qquad
\operatorname{rank}g_x^{\rm obs}=\operatorname{rank}J\le r.
$$

$\mathcal H$가 무한차원이고 $r<\infty$이므로 $K$는 무한차원이다.
따라서 $g_x^{\rm obs}$는 $\mathcal H$에서 coercive한 strong Riemann
metric일 수 없고, $\mathcal H/K$에서만 양의 정부호 형식을 유도한다.

**[정리 후보 T2: 같은 quotient를 갖는 무한 ambient metric 족]**
$\operatorname{rank}J>0$일 때 $J_X=J|_X:X\to R$와

$$
B=J_X^*WJ_X
$$

를 둔다. 임의의 bounded, self-adjoint, coercive
$A:K\to K$에 대해

$$
G_A=A\oplus B
$$

는 $\mathcal H=K\oplus X$ 위의 strong metric operator다. 서로 다른
$A$들은 서로 다른 ambient metric을 만들지만, $K$를 따라 최소화해 얻는
quotient metric과 $m$의 1차 관측 geometry는 모두 동일하다. 특히
$A_\alpha=(1+\alpha)I_K$, $\alpha>0$는 연속 무한 witness 족이다.

**[따름정리 후보 C1]** 유한 수동 관측만으로는 무한차원 ambient metric,
hidden-direction 거리, ambient dimension 또는 “차원 4”를 유일하게
식별할 수 없다. 보고 가능한 것은 rank가 $r$ 이하인 pointwise observable
quotient geometry다.

ambient dimension 부분은 T1/T2의 고정 공간 결론으로 대신하지 않고
별도 witness로 증명한다. $q\le r$를 고정하고 모든
$n\in\mathbb N\cup\{\infty\}$에 대해

$$
\mathcal H_n=\mathbb R^q\oplus\mathbb R^n,
\qquad
m_n(a,b)=(a,0_{r-q}),
\qquad
W_n=I_r,
$$

로 두며 $\mathbb R^\infty=\ell^2$로 해석한다. 모든 $n$에서 같은 rank
$q$ 관측과 같은 quotient metric을 얻지만 ambient dimension은 임의다.

## 4. 증명 의무

1. $W\succ0$에서 $g_x^{\rm obs}(u,u)=0$과 $Ju=0$의 동치.
2. 제1동형정리로 $\mathcal H/K\simeq R$이며 $K$가 무한차원임을 증명.
3. $J_X$가 $X$와 $R$ 사이의 bounded isomorphism이고 $B$가 coercive임을
   증명.
4. $G_A$의 boundedness, self-adjointness, coercivity와 서로 다른
   $A$에 대한 비동일성을 증명.
5. quotient norm

   $$
   \|[u]\|_{G_A}^2=\inf_{k\in K}\langle u+k,G_A(u+k)\rangle
   $$

   이 $A$와 무관하고 $g_x^{\rm obs}$와 일치함을 증명.
6. 비선형 $m$에는 pointwise derivative 정리로만 적용하며, 매끄러운
   quotient manifold에는 constant-rank neighborhood와 smooth closed
   kernel subbundle이 추가로 필요함을 명시.
7. $J=0$이면 $X=R=\{0\}$이고 quotient가 영벡터공간인 퇴화 경계로
   별도 처리하며, bounded-inverse 논증을 억지로 적용하지 않음.
8. 서로 다른 $\mathcal H_n$ witness로 ambient dimension 비식별성을
   T1/T2와 별도로 증명.

## 5. 반례와 적용 경계

다음 경우에는 이 정리의 결론을 그대로 적용하지 않는다.

- $\mathcal H$가 유한차원이고 관측이 injective인 경우.
- 무한 센서 또는 별도 구조제약으로 $m$이 injective가 되는 경우.
- metric이 알려진 유한 매개변수 family에 제한되고, metric이 dynamics에
  들어가며 충분한 개입과 persistent excitation으로 매개변수를 식별하는
  경우.
- hidden block $A$를 observable block $B$에 묶는 독립적인 물리 공리가
  주어진 경우.

이 정리는 brain metric이 존재하지 않는다고 말하지 않는다. 또한
consciousness, self, hippocampal address, loop, 3+1 world model 또는 AGI
동형성을 증명하거나 반박하지 않는다.

## 6. 형식 상태와 claim ceiling

T1/T2/C1은 모든 전제와 증명 의무가 닫힐 때만 `[정리]`로 승격한다.
전제 누락이나 완전한 반례가 발견되면 부모 명제를 제거하거나 정확한
좁은 명제로 축소한다. empirical lane, implementation, EEG access와
simulation은 열지 않는다.

`CLAIM_CEILING`: `MATHEMATICAL_LOCAL_NO_GO_ONLY / FINITE_PASSIVE_OBSERVATION / OBSERVABLE_QUOTIENT_IDENTIFIABLE / AMBIENT_NEURAL_METRIC_DIMENSION_CONSCIOUSNESS_UNIDENTIFIED`.
