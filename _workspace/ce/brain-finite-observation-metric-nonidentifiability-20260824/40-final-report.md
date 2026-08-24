# BA-OBS-NOGO1 최종 보고서 — 유한 수동 관측의 ambient metric 비식별성

Status: COMPLETE

Final claim ceiling: `MATHEMATICAL_LOCAL_NO_GO_ONLY / FINITE_PASSIVE_OBSERVATION / OBSERVABLE_QUOTIENT_IDENTIFIABLE / AMBIENT_NEURAL_METRIC_DIMENSION_CONSCIOUSNESS_UNIDENTIFIED`

## 초록

이 보고서는 무한차원 Hilbert 상태공간을 유한 개 EEG·전극·feature로 수동 관측할 때 관측 pullback이 전체 Riemann metric을 유일하게 정할 수 없음을 증명한다. T1은 유한 관측의 pullback이 관측 kernel에서 퇴화하고 pointwise quotient에만 양의 정부호 형식을 준다는 정리다. T2는 hidden kernel 위의 metric을 연속적으로 바꿔도 동일한 quotient geometry가 남는 무한 witness 족을 구성한다. C1은 서로 다른 유한·무한 ambient 차원이 동일한 관측 rank와 quotient norm을 만들 수 있음을 별도 cross-model witness로 보인다. 결과는 local first-order, finite passive observation의 비식별성에 한정되며, EEG가 뇌 metric·edge·의식·자아·4차원성·AGI를 판정한다는 결론을 주지 않는다. 데이터, EEG 접근, simulator, 개입 또는 수치 검정은 열지 않았다.

## 그림자 비유와 정확한 질문

한 대의 카메라가 물체를 촬영할 때, 사진은 카메라가 보는 방향의 모양만 기록하고 카메라 뒤쪽으로 얼마나 두꺼운지 또는 내부가 어떻게 채워졌는지는 결정하지 못한다. 여기서 물체는 잠재 neural history 상태, 사진의 좌표는 유한 채널 관측, 카메라가 보지 못하는 방향은 관측 kernel에 해당한다. 서로 다른 내부 구조가 같은 사진을 만들 수 있다는 비유는 T2의 핵심, 즉 hidden block metric을 바꾸어도 관측 quotient가 달라지지 않는다는 점을 설명한다.

그러나 이 비유는 한계가 있다. 실제 카메라는 비선형 projection, 가림, 조명, 여러 시점, 움직임을 가질 수 있고, 뇌의 관측도 dynamics와 개입을 가질 수 있다. 따라서 본문이 증명하는 것은 고정한 점에서의 $C^1$ 유한 관측 derivative에 관한 local 결과뿐이며, 비선형 전역 manifold나 모든 가능한 실험을 하나의 사진처럼 처리하지 않는다.

**[정의]** $\mathcal H$를 무한차원 실 Hilbert 공간, $m:U\subset\mathcal H\to\mathbb R^r$를 $C^1$ 유한 관측 map이라 하자. 고정점 $x\in U$에서 $J=Dm_x$, $K=\ker J$, $X=K^\perp$, $R=\operatorname{ran}J$로 둔다. 관측 출력은 채널별 기준척도로 무차원화하고 $W=W^{\mathsf T}\succ0$는 무차원 measurement precision으로 둔다. 이때 관측 pullback은

$$
g_x^{\rm obs}(u,v)=\langle Ju,WJv\rangle_{\mathbb R^r}
$$

이다. 이 형식은 관측 좌표에서만 정의된 거리 정보를 잠재공간 쪽으로 당겨 온 것이며, 아직 ambient strong metric이라는 뜻은 아니다.

## T1 — 유한 pullback이 남기는 quotient

**[정리 T1: 유한 pullback 퇴화]** $g_x^{\rm obs}$는 양의 준정부호이고

$$
\ker g_x^{\rm obs}=K,
\qquad
\operatorname{rank}g_x^{\rm obs}=\operatorname{rank}J\le r.
$$

또한 $\mathcal H$가 무한차원이고 $r$이 유한이면 $K$는 무한차원이다. 따라서 $g_x^{\rm obs}$는 $\mathcal H$의 coercive strong Riemann metric일 수 없지만, $\mathcal H/K$에는 pointwise positive-definite quotient inner product를 유도한다.

증명. $W\succ0$의 양의 정부호 제곱근을 쓰면

$$
g_x^{\rm obs}(u,u)=\|W^{1/2}Ju\|^2\ge0.
$$

이 값이 영인 필요충분조건은 $Ju=0$이므로 kernel은 정확히 $K$다. 또한 $J^*WJ=(W^{1/2}J)^*(W^{1/2}J)$의 rank는 $J$의 rank와 같고, 출력공간이 $r$차원이므로 rank는 $r$ 이하이다. $J_X=J|_X$는 $X$에서 $R$로 가는 전단사다. 실제로 $X\cap K=\{0\}$이므로 injective이고, $Jh\in R$에 대해 $h=k+x\in K\oplus X$로 분해하면 $Jh=Jx$이므로 surjective다. 따라서 $X\simeq R$는 유한차원이고, $K$까지 유한차원이라면 $\mathcal H=K\oplus X$가 유한차원이 되어 모순이다.

마지막으로 $\bar g_x([u],[v])=g_x^{\rm obs}(u,v)$로 두면 $Jk=0$이므로 대표원 선택과 무관하다. $[u]\ne0$이면 $u\notin K$이어서 $Ju\ne0$이고, $W\succ0$로부터 $\bar g_x([u],[u])>0$이다. 이로써 관측이 식별하는 대상은 한 점에서의 quotient inner product라는 결론을 얻는다. 이는 전역 quotient manifold의 존재를 말하지 않는다.

## T2 — 같은 quotient를 갖는 무한 ambient metric 족

**[정리 T2: constructive non-identifiability]** $\operatorname{rank}J>0$이라고 하자. $J_X=J|_X:X\to R$와

$$
B=J_X^*WJ_X
$$

를 둔다. 임의의 bounded, self-adjoint, coercive operator $A:K\to K$에 대해 $G_A=A\oplus B$는 $\mathcal H=K\oplus X$ 위 strong metric operator다. 서로 다른 $A$는 서로 다른 ambient metric을 만들지만, $K$를 따라 최소화한 quotient metric은 모두 $g_x^{\rm obs}$와 같다.

증명. T1의 전단사성 및 bounded inverse theorem으로 $J_X^{-1}$는 bounded이고, 어떤 $c_J>0$에 대해 $\|J_Xx\|\ge c_J\|x\|$가 성립한다. $W$의 최소 고윳값을 $\lambda_{\min}(W)>0$라 하면

$$
\langle x,Bx\rangle
=\langle J_Xx,WJ_Xx\rangle
\ge\lambda_{\min}(W)c_J^2\|x\|^2.
$$

따라서 $B$는 bounded, self-adjoint, coercive다. $A$도 같은 성질을 가지므로 $h=k+x$에 대해 $\langle h,G_Ah\rangle$는 $K$와 $X$ 성분의 coercivity 상수 중 작은 값으로부터 아래로 제한된다. 즉 $G_A$는 strong metric operator다.

이제 $u=k_0+x$로 분해하면 quotient norm은

$$
\begin{aligned}
\|[u]\|_{G_A}^2
&=\inf_{k\in K}\langle u+k,G_A(u+k)\rangle\\
&=\inf_{k\in K}\left(
\langle k_0+k,A(k_0+k)\rangle+\langle x,Bx\rangle
\right)\\
&=\langle x,Bx\rangle
=\langle Ju,WJu\rangle.
\end{aligned}
$$

이다. infimum은 $k=-k_0$에서 달성되므로 hidden block $A$가 정확히 소거되고, polarization으로 quotient bilinear form 전체가 $g_x^{\rm obs}$와 같음을 얻는다. 한편 $A_\alpha=(1+\alpha)I_K$ ($\alpha>0$)로 두면 영이 아닌 $k\in K$에서 $\langle k,G_{A_\alpha}k\rangle=(1+\alpha)\|k\|^2$이므로 서로 다른 $\alpha$는 서로 다른 ambient metric이다. 그러므로 finite passive observation은 hidden-direction 거리를 유일하게 정하지 못한다.

$J=0$은 별도 경계다. 이때 $X=R=\{0\}$이고 observable quotient는 영벡터공간이며, 모든 bounded coercive ambient metric이 같은 영 관측을 만든다. 이 경우에는 $J_X^{-1}$를 쓰는 T2의 논증을 적용하지 않지만 비식별성 자체는 더 강하다.

## C1 — 숫자 4와 ambient 차원의 비식별성

**[따름정리 C1]** finite passive output은 같은 관측 rank와 quotient metric을 가진 모델들 사이에서 ambient dimension을 선택하지 못한다.

증명. $q\le r$를 고정하고, 모든 $n\in\mathbb N\cup\{\infty\}$에 대해

$$
\mathcal H_n=\mathbb R^q\oplus\mathbb R^n,
\qquad
m_n(a,b)=(a,0_{r-q}),
\qquad
W_n=I_r,
\qquad
G_n=I
$$

로 둔다. $n=\infty$에서는 $\mathbb R^\infty=\ell^2$로 해석한다. 모든 모델의 관측 derivative rank는 $q$이고 quotient norm은 $\|a\|^2$로 같지만 ambient dimension은 $q+n$이며 임의의 유한값과 무한값을 모두 취한다. 따라서 유한 수동 관측만으로 차원이 4인지, 다른 정수인지, 무한인지 판정할 수 없다. 이는 T1/T2가 고정한 하나의 $\mathcal H$ 안에서 보인 hidden metric 비식별성과 별개의 cross-model witness다.

이 따름정리는 manifold dimension을 entropy나 participation ratio 같은 effective dimension과 동일시하지 않는다. 후자는 선택한 관측 quotient의 스펙트럼 요약량이며, ambient dimension의 식별 증거가 아니다.

## 비선형·전역·반례 경계

비선형 관측 $m$에는 위 결과를 각 점의 derivative $Dm_x$에 적용한다. Local quotient manifold 또는 quotient bundle을 말하려면 constant-rank neighborhood와 smooth closed complemented kernel subbundle이 추가로 필요하다. 이 전제 없이 curvature, holonomy, global geodesic, memory 또는 의식의 current-world manifold에 관한 결론을 더할 수 없다.

다음 조건에서는 no-go의 적용 범위가 줄거나 사라질 수 있다. Ambient 공간이 유한차원이고 관측이 injective일 수 있으며, 무한 센서나 독립 구조제약으로 kernel이 사라질 수도 있다. 또한 metric이 알려진 유한 매개변수 family에 제한되고 dynamics에 들어가며, 충분한 개입과 persistent excitation으로 hidden parameter를 식별할 수 있다. Hidden block을 observable block에 유일하게 묶는 독립 물리 공리가 주어진 경우에도 T2의 자유도는 그대로 남지 않는다.

그러므로 본 정리는 brain metric이 존재하지 않는다는 명제가 아니다. finite passive observation만으로 무한차원 ambient metric과 hidden-direction 거리·차원을 유일하게 복원할 수 없다는 local 식별성 경계다. EEG의 유한 sensor, finite feature, 또는 low-rank latent coordinate를 이 정리의 전제에 맞게 모델링할 수 있더라도, 실제 measurement model과 전제 충족은 별도 계약에서 검증해야 한다.

## 뇌·의식·AGI에 대한 함의와 금지된 승격

EEG에서 어떤 낮은 rank, 관측 차원 또는 예측 feature가 유용하게 보이더라도 그것은 observable quotient의 성질일 수 있다. 그것만으로 neuron edge strength, infinite-dimensional synaptic state, ambient Riemann metric, cortical curvature 또는 hidden direction의 거리를 복원할 수 없다. 특히 숫자 4가 관측 chart에서 등장해도 의식이 4차원이라는 결론, 3+1 세계모델의 실증, 뇌 전체 차원의 확정으로 바꿀 수 없다.

동일한 이유로 이 정리는 self가 path인지 state인지, hippocampal sparse address가 존재하는지, loop이 기억·의식과 같은지, 또는 AGI가 뇌와 동형인지 증명하거나 반박하지 않는다. 이 문서의 유일한 양성 결론은 finite passive observation이 pointwise observable quotient geometry를 제공한다는 것이고, 유일한 음성 결론은 그 정보만으로 ambient metric과 dimension을 유일하게 식별할 수 없다는 것이다.

## 근거 경로와 재현

수학적 전제·증명·경계는 [계약](00-contract.md), [수학 lane](11-math.md), [route 결정](12-routes.md), [동결 감사](20-audit.md)에 고정되어 있다. Source lane은 이 math-only continuation이 새 empirical claim이나 외부 사실을 열지 않았음을 기록하며, implementation 및 numerical validation은 각각 `SKIPPED`다: [10-sources.md](10-sources.md), [30-implementation.md](30-implementation.md), [31-validation.md](31-validation.md). 이 run의 closure 근거는 수치 예시가 아니라 위 Hilbert-space 증명과 stable-snapshot audit이며, 유한 행렬 예시는 universal infinite-dimensional 명제를 검증하지 못한다.

동결 contract SHA-256은 `dba35c1704f9730e9e0660a02be2a2a0ee313ae9786bf90bd139b6840bf0b12f`이고, math SHA-256은 `9b191659ae6b81a496371b670348e5ceaa3087820aeb8cf634a2b87eecc76699`다. 문서 구조와 final-stage 무결성은 다음 명령으로 확인할 수 있으며, numerical simulation을 추가하는 것은 이 mathematics-only run의 재현이 아니라 별도 연구가 된다.

```powershell
.codex\hooks\run.ps1 check _workspace\ce\brain-finite-observation-metric-nonidentifiability-20260824 final
Get-FileHash _workspace\ce\brain-finite-observation-metric-nonidentifiability-20260824\40-final-report.md -Algorithm SHA256
```
