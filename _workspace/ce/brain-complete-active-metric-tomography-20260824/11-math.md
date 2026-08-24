# BA-OBS-ID2 mathematics lane — 무한차원 강한 계량의 완전 능동 tomography

Status: COMPLETE

Verdict: PASS after math-verifier revision 1

P0: none.  
P1: none after independent-reset, symmetric-clipping, identity-tail, and stable-tail corrections.

## 1. 범위와 가정

$\mathcal H$는 **실** separable Hilbert 공간이고 $(e_n)_{n\ge1}$은 고정된 complete
orthonormal basis다. 복소 Hilbert 공간의 sesquilinear polarization은 이번 정리의
범위가 아니다. 미지 metric과 mobility는 bounded self-adjoint operator이며

$$
g_-I\preceq G\preceq g_+I,
\qquad
M=G^{-1},
\qquad
m_-I\preceq M\preceq m_+I,
$$

$$
m_-=g_+^{-1},
\qquad
m_+=g_-^{-1}.
$$

각 query $f$는 다른 query의 이력이 남지 않는 동일한 reset state에서 시행한다.
합성 측정 공리 A1은 알려진 linear potential $V_f(q)=-\langle f,q\rangle$ 아래

$$
q'(0+)=Mf,
\qquad
Q_G(f)=\langle f,q'(0+)\rangle=\langle f,Mf\rangle
$$

를 exact하게 읽는다고 가정한다. 이는 실제 신경계에 대해 확립된 측정식이 아니라
이번 수학적 식별 정리의 이상적 oracle이다.

## 2. [정리 T4] uniform strong monotonicity가 주는 전역 안정 단사성

**명제.** $\mathcal X,\mathcal Y$가 실 Hilbert 공간이고
$\Theta\subset\mathcal X$가 열린 convex 집합이라고 하자.
$\Phi:\Theta\to\mathcal Y$는 $C^1$, $L:\mathcal Y\to\mathcal X$는 bounded
linear map이라 하자. 어떤 $\mu>0$에 대해 모든 $\vartheta\in\Theta$와
$h\in\mathcal X$에서

$$
\left\langle D(L\circ\Phi)_\vartheta h,h\right\rangle
\ge \mu\|h\|_{\mathcal X}^2
$$

이면 모든 $\vartheta_1,\vartheta_2\in\Theta$에 대해

$$
\boxed{
\|\Phi(\vartheta_1)-\Phi(\vartheta_2)\|_{\mathcal Y}
\ge \frac{\mu}{\|L\|}
\|\vartheta_1-\vartheta_2\|_{\mathcal X}}
$$

가 성립한다. 따라서 $\Phi$는 전역 단사이고 $\Phi(\Theta)$ 위 inverse는
$\|L\|/\mu$-Lipschitz다.

**증명.** $h=\vartheta_1-\vartheta_2$와
$\gamma(s)=\vartheta_2+sh$ $(0\le s\le1)$를 둔다. Convexity 때문에 선분 전체가
$\Theta$에 들어간다. $F=L\circ\Phi$에 Banach-space fundamental theorem of
calculus를 적용하면 Bochner integral로

$$
F(\vartheta_1)-F(\vartheta_2)
=\int_0^1DF_{\gamma(s)}h\,ds.
$$

양변과 $h$의 내적을 취하면

$$
\begin{aligned}
\left\langle F(\vartheta_1)-F(\vartheta_2),h\right\rangle
&=\int_0^1\left\langle DF_{\gamma(s)}h,h\right\rangle ds\\
&\ge\mu\|h\|^2.
\end{aligned}
$$

한편 Cauchy--Schwarz와 $L$의 boundedness로

$$
\left\langle F(\vartheta_1)-F(\vartheta_2),h\right\rangle
\le
\|L\|\,\|\Phi(\vartheta_1)-\Phi(\vartheta_2)\|\,\|h\|.
$$

$h\ne0$이면 $\|h\|$를 약분하여 표시된 하한을 얻고, $h=0$이면 자명하다.
$\mu>0$인 가정은 $L=0$과 양립하지 않는다. 이 결론은 image 위 inverse에 관한
것이며 $\Phi$의 surjectivity는 주장하지 않는다. 증명은 $\dim\mathcal X<\infty$를
쓰지 않으므로 무한차원에서도 그대로 성립한다. $\square$

이 정리는 “모든 점에서 derivative가 injective”보다 강하다. 단순 immersion은
self-intersection을 허용하지만, 여기서는 하나의 fixed readout $L$이 전 구간에서
같은 방향의 강한 단조성을 제공하므로 멀리 떨어진 두 점도 합쳐질 수 없다.

## 3. [정리 T5] 임의 bounded strong metric의 가산 완전 식별

**명제.** Query 집합을

$$
\mathscr D=
\{e_i:i\ge1\}
\cup
\{e_i+e_j,e_i-e_j:1\le i<j<\infty\}
$$

로 둔다. A1의 exact response $Q_G(f)$를 모든 $f\in\mathscr D$에서 알면
arbitrary bounded self-adjoint coercive metric $G$가 유일하게 정해진다.

**증명.** 먼저 diagonal coefficient는

$$
m_{ii}:=\langle e_i,Me_i\rangle=Q_G(e_i)
$$

다. 실 Hilbert 공간의 polarization을 쓰면 $i<j$에서

$$
\begin{aligned}
Q_G(e_i+e_j)-Q_G(e_i-e_j)
&=\langle e_i+e_j,M(e_i+e_j)\rangle\\
&\quad-\langle e_i-e_j,M(e_i-e_j)\rangle\\
&=4\langle e_i,Me_j\rangle,
\end{aligned}
$$

따라서

$$
m_{ij}=m_{ji}
=\frac{Q_G(e_i+e_j)-Q_G(e_i-e_j)}4
$$

다. 이제 두 mobility $M_1,M_2$가 모든 query에서 같은 값을 준다고 하자.
$A=M_1-M_2$의 모든 matrix coefficient $\langle e_i,Ae_j\rangle$가 0이다.
유한 지지 벡터 $x,y$에 대해 bilinearity로 $\langle y,Ax\rangle=0$이므로
$Ax=0$이다. 유한 지지 벡터들은 $\mathcal H$에 조밀하고 $A$는 bounded이므로
연속성에 의해 $A=0$이다. 따라서 $M_1=M_2$이고, bounded coercive operator의
inverse가 유일하므로 $G_1=G_2$다. $\square$

$\mathscr D$는 가산 집합이다. 첫 $N$ basis direction만 쓰면 필요한 scalar query는

$$
N+2\binom N2=N^2
$$

개다. 그러므로 이 결과는 유한 매개변수 prior가 없는 전역 유일성 정리지만, 유한
실험으로 무한 operator를 완성했다는 정리는 아니다. 가산히 무한한 모든 response가
exact하게 주어진다는 정보 완전성이 no-go를 제거한다.

## 4. [따름정리 C3] 유한 section의 strong recovery

$P_N$을 $\operatorname{span}\{e_1,\ldots,e_N\}$으로의 orthogonal projection,
$R_N=I-P_N$이라 하고

$$
M_N=P_NMP_N+R_N,
\qquad
G_N=M_N^{-1}
$$

로 둔다.

**균일 spectral bound.** $x=P_Nx+R_Nx$의 직교분해를 쓰면

$$
\langle x,M_Nx\rangle
=\langle P_Nx,MP_Nx\rangle+\|R_Nx\|^2.
$$

따라서

$$
\min(1,m_-)I\preceq M_N\preceq\max(1,m_+)I,
$$

$$
\|M_N^{-1}\|\le \frac1{\min(1,m_-)}=\max(1,g_+).
$$

**Strong convergence.** 고정된 $x\in\mathcal H$에 대해 $P_Nx\to x$이고,
$M$이 bounded이므로 $MP_Nx\to Mx$다. 다시 $P_N\to I$ strongly이므로

$$
P_NMP_Nx\to Mx,
\qquad
R_Nx\to0,
$$

즉 $M_Nx\to Mx$다. Resolvent identity

$$
G_N-G=M_N^{-1}(M-M_N)G
$$

에서 $Gx$를 고정 벡터로 보고 위 strong convergence와 $\sup_N\|M_N^{-1}\|<\infty$를
쓰면 $G_Nx\to Gx$도 따른다. 따라서

$$
\boxed{M_N\xrightarrow{\rm strong}M,
\qquad G_N\xrightarrow{\rm strong}G.}
$$

추가 decay 없이 operator norm으로 강화할 수는 없다. 예를 들어 $M=2I$이면
$M_N=2P_N+R_N$이고 모든 $N$에서

$$
\|M_N-M\|_{\rm op}=1,
\qquad
\|G_N-G\|_{\rm op}=\frac12.
$$

이는 strong convergence와 모순되지 않는다.

## 5. [따름정리 C4] 유한 noisy reconstruction 경계

$A_N=P_NMP_N|_{P_N\mathcal H}$를 진짜 $N\times N$ block이라 하자. 각 scalar
response의 오차가 $|\widehat Q(f)-Q_G(f)|\le\varepsilon$이면 diagonal 추정 오차는
$\varepsilon$ 이하이고 polarization으로 얻은 off-diagonal 오차는

$$
\left|\frac{\delta Q(e_i+e_j)-\delta Q(e_i-e_j)}4\right|
\le\frac\varepsilon2
$$

다. 이 값을 $(i,j)$와 $(j,i)$에 똑같이 넣어 대칭 raw block $\widehat A_N$을
만들면

$$
\begin{aligned}
\|\widehat A_N-A_N\|_{\rm HS}^2
&\le N\varepsilon^2
+2\binom N2\left(\frac\varepsilon2\right)^2\\
&=\varepsilon^2\left[N+\frac{N(N-1)}4\right]
=:\eta_N^2.
\end{aligned}
$$

Self-adjoint $N\times N$ matrices에서 spectrum이 $[m_-,m_+]$에 놓이는 closed convex
set으로의 Frobenius projection은 eigenvalue clipping이다. $A_N$ 자체가 이 set에
속하므로 metric projection의 비팽창성에 의해

$$
\|\operatorname{clip}(\widehat A_N)-A_N\|_{\rm HS}
\le\|\widehat A_N-A_N\|_{\rm HS}\le\eta_N.
$$

$B=M-I$와 $b_{ij}=\langle e_i,Be_j\rangle$가

$$
\sum_{i,j\ge1}(1+\max\{i,j\})^{2s}|b_{ij}|^2\le C_s^2
$$

를 만족한다고 하자. $M_N=I+P_NBP_N$이므로

$$
\begin{aligned}
\|M-M_N\|_{\rm op}
&\le\|B-P_NBP_N\|_{\rm HS}\\
&=\left(\sum_{\max(i,j)>N}|b_{ij}|^2\right)^{1/2}\\
&\le\frac{C_s}{(N+2)^s}
\le\frac{C_s}{(N+1)^s}.
\end{aligned}
$$

Clipped block을 identity tail로 연장한 것을 $\widetilde M_N$이라 하면 triangle
inequality로

$$
\boxed{
\|\widetilde M_N-M\|_{\rm op}
\le\eta_N+\frac{C_s}{(N+1)^s}.}
$$

Clipping은 측정 block에만 적용되므로 전체 completion은
$[\min(1,m_-),\max(1,m_+)]$에 놓이고

$$
\|\widetilde M_N^{-1}\|\le\max(1,g_+),
\qquad
\|M^{-1}\|\le g_+.
$$

Inverse perturbation identity를 적용하면

$$
\begin{aligned}
\|\widetilde G_N-G\|_{\rm op}
&=\|\widetilde M_N^{-1}(M-\widetilde M_N)M^{-1}\|_{\rm op}\\
&\le g_+\max(1,g_+)\|\widetilde M_N-M\|_{\rm op},
\end{aligned}
$$

즉

$$
\boxed{
\|\widetilde G_N-G\|_{\rm op}
\le g_+\max(1,g_+)
\left[\eta_N+\frac{C_s}{(N+1)^s}\right].}
$$

고정된 $\varepsilon>0$에서는 $\eta_N\asymp\varepsilon N/2$이므로 이 상계가 0으로
가지 않는다. Exact query이거나 반복측정으로 $\eta_N\to0$일 때만 decay 가정과 함께
operator-norm consistency가 따른다.

## 6. [산출] infinite-support rank-one witness

$\mathcal H=\ell^2$, $r=0.60$, $\beta=0.50$이고

$$
v_n=\sqrt{1-r^2}\,r^{n-1}
$$

라 하자. 기하급수 합으로 $\|v\|=1$이다. 따라서

$$
M=I+\beta v\otimes v,
\qquad
G=I-cv\otimes v,
\qquad
c=\frac\beta{1+\beta}
$$

이고, $M$의 spectrum은 $\{1,1+\beta\}$, $G$의 spectrum은
$\{1,(1+\beta)^{-1}\}$다. 특히

$$
I\preceq M\preceq1.5I,
\qquad
\frac23I\preceq G\preceq I.
$$

$u_N=P_Nv$, $z_N=(I-P_N)v$,

$$
a_N=\|u_N\|^2=1-b_N,
\qquad
b_N=\|z_N\|^2=r^{2N}
$$

라 하면

$$
M_N=I+\beta u_N\otimes u_N,
\qquad
G_N=I-c_Nu_N\otimes u_N,
\qquad
c_N=\frac\beta{1+\beta a_N}.
$$

$u_N\perp z_N$이고 rank-one operator의 HS 내적을 전개하면

$$
\begin{aligned}
\|M-M_N\|_{\rm HS}^2
&=\beta^2(2a_Nb_N+b_N^2)\\
&=\beta^2(2b_N-b_N^2),
\end{aligned}
$$

$$
\|G-G_N\|_{\rm HS}^2
=c^2\left[
2a_Nb_N+b_N^2+
\frac{\beta^2a_N^2b_N^2}{(1+\beta a_N)^2}
\right].
$$

두 식은 작은 수 $b_N$을 직접 사용하므로 $1-a_N^2$ 또는 $c_N-c$의 subtraction
cancellation을 피한다. 동결된 $N$ menu의 안정 계산값은 다음과 같다.

| $N$ | $N^2$ queries | $\|M-M_N\|_{\rm HS}$ | $\|G-G_N\|_{\rm HS}$ | $\eta_N$ at $\varepsilon=10^{-8}$ |
|---:|---:|---:|---:|---:|
| 4 | 16 | $9.12554231391954\times10^{-2}$ | $6.08649257826294\times10^{-2}$ | $2.64575131106459\times10^{-8}$ |
| 8 | 64 | $1.18758409689598\times10^{-2}$ | $7.91728934049912\times10^{-3}$ | $4.69041575982343\times10^{-8}$ |
| 16 | 256 | $1.99482590634433\times10^{-4}$ | $1.32988394050291\times10^{-4}$ | $8.71779788708135\times10^{-8}$ |
| 32 | 1024 | $5.62762324000874\times10^{-8}$ | $3.75174882667249\times10^{-8}$ | $1.67332005306815\times10^{-7}$ |

## 7. [정리] 모든 유한 query 집합의 남는 blind tail

유한 query $f_1,\ldots,f_K\in\mathcal H$의 span은 유한차원이다. 무한차원
$\mathcal H$에서는 그 orthogonal complement에 unit vector $w$가 존재한다. 따라서

$$
M^{\rm alt}=M+\delta w\otimes w
$$

가 허용 spectral class 안에 남도록 $\delta>0$을 고르면 모든 기존 query에서

$$
Q_{G^{\rm alt}}(f_k)-Q_G(f_k)
=\delta|\langle w,f_k\rangle|^2=0
$$

이지만 held-out $w$에서는 차이가 $\delta$다. 즉 finite exact active query도 임의의
무한 operator 전체를 유일하게 정하지 못한다.

동결 witness에서는 더 강하게

$$
w_N=\frac{re_{N+1}-e_{N+2}}{\sqrt{1+r^2}}
$$

를 택한다. $v_{N+2}=rv_{N+1}$이므로 $w_N\perp v$이고 $\|w_N\|=1$이다.

$$
M^{\rm alt,N}=M+0.10w_N\otimes w_N
$$

의 eigenvalues는 $1.5$, $1.1$, $1$이므로 원래 $[1,1.5]$ class 안에 있다. 첫
$N$ basis directions에 지지된 $N^2$ query에는 완전히 보이지 않지만

$$
Q_{G^{\rm alt,N}}(w_N)-Q_G(w_N)=0.10
$$

이다. 이것은 유한 no-go를 보존하는 adverse control인 동시에, 가산 완전 query가
왜 필요한지를 보여 준다.

## 8. 무차원성 감사

| 대상 | 판정 |
|---|---|
| $\bar q=q_{\rm phys}/q_*$, $\tau=t/t_*$, $\bar f=f_{\rm phys}/f_*$ | 기준 스케일의 비이므로 무차원이다. |
| $M=(t_*f_*/q_*)M_{\rm phys}$, $G=M^{-1}$ | gradient-flow onset 식에서 정규화된 operator다. |
| $Q_G(f)=\langle f,Mf\rangle$ | 정규화 좌표와 operator를 쓰므로 무차원이다. |
| $\varepsilon$, $\eta_N$, $C_s$ | dimensionless response/operator coefficient의 오차와 norm이다. Basis index의 weight도 무차원이다. |
| $r,\beta,a_N,b_N,c,c_N$ 및 spectral bounds | 모두 순수 수 또는 dimensionless operator ratio다. |
| T4의 $\mu/\|L\|$ | 정규화된 domain/output norm 사이의 inverse-Lipschitz 비율이다. |

Dimensionless verdict: PASS.

## 9. no-go의 정확한 경계와 형식 지위

증명 결과는 다음 세 층을 구분한다.

1. **유한 passive 또는 유한 active:** 무한차원 orthogonal tail이 남으므로 arbitrary
   metric의 exact full recovery는 불가능하다.
2. **가산 완전 exact active:** 모든 matrix coefficient가 polarization으로 정해지므로
   arbitrary bounded strong metric은 전역적으로 유일하다.
3. **유한 noisy approximation:** strong convergence는 일반적이고, operator-norm
   error는 weighted HS decay와 감소하는 aggregate noise 아래 정량 제어된다.

따라서 “no-go가 사라진다”는 말은 두 번째 regime에 한정해 엄밀히 참이다. 정보가
유한한 첫 번째 regime의 반례를 삭제하거나 성공으로 고쳐 쓰지 않는다.

- **[정리]** T4 global stable identifiability: 증명 완료.
- **[정리]** T5 countably complete arbitrary-metric tomography: 증명 완료.
- **[따름정리]** C3 strong finite-section recovery: 증명 완료.
- **[따름정리]** C4 weighted-HS finite/noisy bound: 증명 완료.
- **[산출]** Infinite-support rank-one tail 및 same-class adverse control: analytic derivation 완료.
- **[예측]** 동결된 validator가 exact/noisy/tail/adverse gates를 재현하는지는 구현 전이다.
- **[미완성]** A1의 실제 뇌 실현 가능성, 생물학적 canonical basis, neural metric,
  의식·자아·해마 hash·AGI와의 연결은 검증되지 않았다.

Claim ceiling:
`GLOBAL_IDENTIFICATION_OF_AN_ARBITRARY_STRONG_METRIC_UNDER_COUNTABLY_COMPLETE_ACTIVE_QUADRATIC_RESPONSE / GLOBAL_STABLE_IDENTIFIABILITY_UNDER_UNIFORM_STRONG_MONOTONICITY / STRONG_OPERATOR_RECOVERY_AND_HS_FINITE_NOISY_BOUND / FINITE_PASSIVE_AND_FINITE_EXACT_FULL_RECOVERY_STILL_IMPOSSIBLE / SYNTHETIC_ONLY / NO_EMPIRICAL_BRAIN_CONSCIOUSNESS_SELF_OR_AGI_VALIDATION`.
