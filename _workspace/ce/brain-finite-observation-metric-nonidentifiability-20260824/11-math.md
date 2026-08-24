# BA-OBS-NOGO1 mathematics lane

Status: COMPLETE

Contract SHA-256: `dba35c1704f9730e9e0660a02be2a2a0ee313ae9786bf90bd139b6840bf0b12f`

## 1. 전제와 무차원성

$\mathcal H$는 무한차원 실 Hilbert 공간이고,
$m:U\subset\mathcal H\to\mathbb R^r$는 $C^1$이다. 고정한 $x$에서
$J=Dm_x$, $K=\ker J$, $X=K^\perp$, $R=\operatorname{ran}J$로 둔다.
$J$는 bounded이므로 $K$는 닫혀 있고, $R$는 유한차원이므로 닫혀 있다.
관측 좌표는 기준척도로 먼저 무차원화하며 $W=W^{\mathsf T}\succ0$도
무차원 measurement precision으로 둔다. 따라서

$$
g_x^{\rm obs}(u,v)=\langle Ju,WJv\rangle
$$

의 두 인자는 같은 무차원 좌표에 놓인다. exp, log 또는 차원 있는
고정점 인자는 이 정리에 들어가지 않는다.

## 2. 정리 1 — 유한 pullback의 퇴화

**[정리]** $g_x^{\rm obs}$는 양의 준정부호이고

$$
\ker g_x^{\rm obs}=\ker J,
\qquad
\operatorname{rank}g_x^{\rm obs}=\operatorname{rank}J\le r.
$$

또한 $K$는 무한차원이다. 따라서 $g_x^{\rm obs}$는 $\mathcal H$의
coercive strong Riemann metric일 수 없지만 $\mathcal H/K$에는 양의
정부호 pointwise quotient inner product를 유도한다.

증명. $W$의 양의 정부호 제곱근을 사용하면

$$
g_x^{\rm obs}(u,u)=\|W^{1/2}Ju\|^2\ge0.
$$

$W\succ0$이므로 이 값이 영일 필요충분조건은 $Ju=0$이다. 따라서
kernel이 같고, 유한 rank 연산자 $W^{1/2}J$와
$J^*WJ=(W^{1/2}J)^*(W^{1/2}J)$의 rank는 $J$의 rank와 같다.

$J_X=J|_X$는 $X$에서 $R$로 가는 전단사다. injectivity는
$X\cap K=\{0\}$에서 오고, 임의의 $Jh\in R$에 대해
$h=k+x\in K\oplus X$로 쓰면 $Jh=Jx$이므로 surjectivity가 따른다.
따라서 $X\simeq R$는 유한차원이다. 만약 $K$도 유한차원이면
$\mathcal H=K\oplus X$가 유한차원이 되어 모순이므로 $K$는
무한차원이다. 무한차원 nullspace가 있으므로 coercivity는 불가능하다.

마지막으로

$$
\bar g_x([u],[v])=g_x^{\rm obs}(u,v)
$$

로 두면 $Jk=0$ 때문에 대표원 선택과 무관하고, $[u]\ne0$이면
$Ju\ne0$이므로 양의 정부호다. 이는 한 점의 quotient inner product다.
global quotient manifold라는 결론은 아직 포함하지 않는다. 증명 끝.

## 3. 정리 2 — 같은 quotient를 갖는 무한 ambient metric 족

**[정리]** $\operatorname{rank}J>0$이라 하자. $J_X=J|_X$와

$$
B=J_X^*WJ_X
$$

를 둔다. 임의의 bounded, self-adjoint, coercive $A:K\to K$에 대해
$G_A=A\oplus B$는 $\mathcal H=K\oplus X$ 위의 strong metric
operator다. 서로 다른 $A$들은 서로 다른 ambient metric을 만들지만,
그 quotient metric은 모두 $g_x^{\rm obs}$와 같고 $A$와 무관하다.

증명. $J_X$는 Banach 공간 사이의 bounded bijection이므로 bounded
inverse theorem에 따라 어떤 $c_J>0$에 대해

$$
\|J_Xx\|\ge c_J\|x\|
$$

가 성립한다. $W$의 최소 고윳값을 $\lambda_{\min}(W)>0$라 하면

$$
\langle x,Bx\rangle
=\langle J_Xx,WJ_Xx\rangle
\ge\lambda_{\min}(W)c_J^2\|x\|^2.
$$

따라서 $B$는 bounded, self-adjoint, coercive다. $A$의 coercivity
상수를 $a>0$, $B$의 상수를 $b>0$라 하면 $h=k+x$에 대해

$$
\langle h,G_Ah\rangle
=\langle k,Ak\rangle+\langle x,Bx\rangle
\ge\min(a,b)\|h\|^2.
$$

그러므로 $G_A$는 bounded inverse를 갖는 strong metric operator다.

이제 $u=k_0+x$로 쓰면

$$
\begin{aligned}
\|[u]\|_{G_A}^2
&=\inf_{k\in K}\langle u+k,G_A(u+k)\rangle\\
&=\inf_{k\in K}
\left(\langle k_0+k,A(k_0+k)\rangle+\langle x,Bx\rangle\right)\\
&=\langle x,Bx\rangle\\
&=\langle Ju,WJu\rangle.
\end{aligned}
$$

infimum은 $k=-k_0$에서 달성된다. polarization을 적용하면 norm뿐 아니라
전체 quotient bilinear form이 $g_x^{\rm obs}$와 같다는 결론을 얻는다.
한편 $A_\alpha=(1+\alpha)I_K$, $\alpha>0$로 두면 영이 아닌
$k\in K$에서

$$
\langle k,G_{A_\alpha}k\rangle=(1+\alpha)\|k\|^2
$$

이므로 ambient metric들은 서로 다르다. 관측 map $m$, derivative $J$와
quotient geometry는 전혀 바뀌지 않는다. 증명 끝.

$J=0$이면 $X=R=\{0\}$이고 observable quotient는 영벡터공간이다.
이 경우에도 모든 bounded coercive ambient metric이 같은 영 관측을
만드므로 비식별성은 더 강하지만, $J_X^{-1}$ 논증은 사용하지 않는다.

## 4. 따름정리 — ambient dimension과 숫자 4의 비식별성

**[따름정리]** finite passive output은 관측 rank와 quotient metric이
같은 모델들 사이에서 ambient dimension을 선택하지 못한다.

증명. $q\le r$를 고정하고 모든 $n\in\mathbb N$과 $n=\infty$에 대해

$$
\mathcal H_n=\mathbb R^q\oplus\mathbb R^n,
\qquad
m_n(a,b)=(a,0_{r-q}),
\qquad
W_n=I_r,
\qquad
G_n=I
$$

로 둔다. 여기서 $\mathbb R^\infty=\ell^2$다. 모든 $n$에서 관측
derivative의 rank는 $q$이고 quotient metric은 $\|a\|^2$로 동일하지만
ambient dimension은 $q+n$으로 임의이며 무한대도 포함한다. 따라서
유한 관측만으로 ambient dimension이 4인지, 다른 정수인지, 무한인지
선택할 수 없다. 증명 끝.

이 결론은 manifold dimension과 entropy·participation ratio 같은 연속
effective dimension을 동일시하지 않는다. 후자는 관측 quotient에서
선택한 스펙트럼 요약량이다.

## 5. 비선형·전역 경계와 반례

비선형 $m$에 대한 위 정리는 각 점의 $Dm_x$에 적용되는 local first-order
결론이다. constant-rank neighborhood와 smooth closed complemented kernel
subbundle이 있어야 quotient bundle 또는 local quotient manifold를
말할 수 있다. 이 전제 없이 curvature, holonomy, global geodesic 또는
의식의 현재 manifold를 결론내릴 수 없다.

다음 조건에서는 no-go의 적용 범위가 줄어든다.

- finite-dimensional restricted family에서 관측이 injective인 경우
- 무한 센서나 독립 구조제약으로 hidden kernel이 사라지는 경우
- metric이 dynamics에 들어가고 개입·persistent excitation이 hidden
  parameter를 식별하는 경우
- 독립 물리 공리가 hidden block을 observable block에 유일하게 묶는 경우

따라서 이 정리는 brain metric의 부재를 말하지 않는다. finite passive
observation만으로 그것을 유일하게 복원할 수 없다는 정리다. self,
consciousness, hippocampal address, loop, 3+1 world model과 AGI 동형성은
모두 미식별 상태로 남는다.

## Math verdict

P0: none. 최초 C1 문구는 고정 $\mathcal H$의 T1/T2만으로 ambient
dimension 비식별성을 말해 P1이었으나, section 4의 cross-model witness로
보완했다. $J=0$ 경계와 pointwise/global quotient 구분도 명시했다.
T1, T2와 따름정리는 계약의 claim ceiling 안에서 완결된다.
