# 05. 거대 역사공간 속의 순간 부분공간: Riesz 부분공간의 생성 조건

## 5. 거대 역사공간 속의 순간 부분공간

### 5.1 Riesz 부분공간은 언제 생기는가

전체 $\mathcal H$가 크다는 사실은 어느 순간의 유효한 분석 좌표가 반드시 크다는 뜻이 아니다. 짧은 시간창 $\Delta$의 흐름 $\Phi_{t,t+\Delta}$를 접공간에서 미분한 연산자 $U_t^\Delta=D\Phi_{t,t+\Delta}(x_t)$를 보자. 복소화한 공간에서 스펙트럼의 한 묶음만 분리할 수 있다면 그 묶음이 순간 부분공간을 정의한다.

**[정의]** 닫힌 곡선 $\Gamma$가 $U$의 스펙트럼 중 유한한 대수적 중복도 $d$를 가진 묶음만 둘러싼다고 하자. 이때

$$
P=\frac{1}{2\pi i}\oint_\Gamma(zI-U)^{-1}\,dz
\tag{13}
$$

를 Riesz 사영이라 한다. $P$의 상은 그 순간 선택된 스펙트럼 부분공간이다. Riesz 사영은 일반적으로 직교사영이 아님을 기억해야 한다.

**[정리: Riesz rank와 섭동 안정성]** (13)의 조건에서 $P^2=P$, $PU=UP$, $\operatorname{rank}P=d$다. $R=\sup_{z\in\Gamma}\|(zI-U)^{-1}\|$라 하고 $R\|E\|<1$이면 같은 곡선은 $U+E$에서도 같은 수의 고유값을 분리하며

$$
\|P(U+E)-P(U)\|
\le\frac{\operatorname{len}(\Gamma)}{2\pi}
\frac{R^2\|E\|}{1-R\|E\|}.
\tag{14}
$$

증명. resolvent 항등식과 Neumann 급수로 $(zI-U-E)^{-1}$를 $(zI-U)^{-1}$의 수렴 급수로 쓴다. 이를 (13)에 적분하면 사영 차이에 대한 (14)가 나온다. 곡선 위에 스펙트럼이 지나지 않으므로 그 안의 대수적 중복도, 곧 사영의 rank는 보존된다. □

이 정리는 선형화된 짧은 시간창의 정리다. Riesz 분리만으로 비선형 흐름의 느린 다양체가 나오지는 않는다. 비선형 결론에는 아래의 균일 dichotomy 또는 normal hyperbolicity 가설과 graph-transform 수축이 별도로 필요하다. **[미완성: 경험적 적용]** 실제 뇌 흐름이 그 균일 가설을 만족하는지는 아직 확인하지 않았다.

실수 기록에서 복소 스펙트럼을 세는 관례도 먼저 고정해야 한다. **[정의: 실수 rank 관례]** 실수 선형 return operator $U$를 복소화했을 때, 실수 고유값 $\lambda$의 대수적 중복도는 그대로 실수 차원에 더한다. 비실수 고유값은 $\lambda,\bar\lambda$를 함께 묶어야 하므로, 상반평면 대표의 중복도 $m_{\rm alg}(\lambda)$는 실수 차원에 두 배로 기여한다. 따라서

$$
d_{\mathbb R}
=\sum_{\lambda\in\mathbb R}m_{\rm alg}(\lambda)
+2\sum_{\operatorname{Im}\lambda>0}m_{\rm alg}(\lambda).
\tag{15}
$$

켤레변환이 $\lambda$의 일반화 고유공간을 $\bar\lambda$의 일반화 고유공간으로 보내므로 이 규칙이 나온다. 이 식은 복소 계산의 bookkeeping 규칙이며, 관측 hard rank나 의식 차원을 정하는 식이 아니다. 후보 menu를 비교하기 전에 실수 rank 관례를 고정하지 않으면 같은 회전 모드를 한 차원 또는 두 차원으로 세는 오류가 생긴다.

**[정리: 조건부 국소 느린 다양체 후보]** $r\ge2$이고 기준 궤적 근처의 흐름이 $C^r$라고 하자. 변분 cocycle이 균일하게 유계인 사영과 $C^{r-1}$ 불변 분해 $E_t^s\oplus E_t^c\oplus E_t^u$를 가지며, stable·unstable 수축/팽창률이 center율을 양의 여유만큼 지배한다고 가정한다. 또한 고정한 관형 이웃에서 선형부를 뺀 비선형 도함수가 충분히 작다고 하자. 그러면 $E_t^c$에 접하고 실수 차원 $d_{\mathbb R}$를 갖는 국소 불변 $C^{r-1}$ graph가 존재한다.

증명 개요. 근방의 좌표를 $(\xi_c,\xi_{su})$로 나누고, 하나의 무차원 시간창을 따라 Lipschitz graph $\xi_{su}=h_t(\xi_c)$를 보낸다. 지수 gap과 작은 비선형 Lipschitz 상수가 graph transform을 수축으로 만들므로 고정 graph가 존재하고 불변이다. 표준 bootstrap이 $C^{r-1}$ 정칙성을 준다. gap이 닫히거나 사영이 유계가 아니거나 비선형 remainder가 크면 이 논증은 성립하지 않는다. 이 가설들은 실제 뇌 기록에서 확인된 적이 없으며, Riesz 분리만으로 이 정리를 적용할 수는 없다.

#### 정량적 triangular subcase: “충분히 작다”를 부등식으로 쓰기

일반 정상쌍곡성 정리를 대체하지 않으면서 실행 가능한 한 하위 경우를 정확히 닫을 수 있다. 무차원 시간창마다

$$
x_{t+1}=\phi_t(x_t),\qquad
y_{t+1}=B_ty_t+g_t(x_t,y_t)
\tag{15a}
$$

인 triangular chart를 생각하자. 즉 base $x$의 다음 값은 fiber $y$에 의존하지 않는다. $\operatorname{Lip}(\phi_t^{-1})\le\mu$, $\|B_t\|\le b$이고

$$
\|g_t(x,0)\|\le G,\qquad
\|g_t(x,y)-g_t(x',y')\|
\le L_x\|x-x'\|+L_y\|y-y'\|
\tag{15b}
$$

라 하자. base·fiber 기준척도 $X_*,Y_*$를 먼저 정해 $R=R_{\rm raw}/Y_*$, $G=G_{\rm raw}/Y_*$,
$L_x=L_{x,\rm raw}X_*/Y_*$, $\kappa=\kappa_{\rm raw}X_*/Y_*$로 만든다. 모두 무차원이다.

**[정리: 정량 triangular graph transform]** $q=b+L_y$라 두고

$$
q<1,\qquad qR+G\le R,\qquad
\mu(q\kappa+L_x)\le\kappa
\tag{15c}
$$

라고 하자. 그러면 $\|h_t\|_\infty\le R$, $\operatorname{Lip}(h_t)\le\kappa$인 graph family 공간에

$$
(\mathcal Th)_{t+1}(x')=
B_th_t(\phi_t^{-1}x')+
g_t(\phi_t^{-1}x',h_t(\phi_t^{-1}x'))
\tag{15d}
$$

가 자기수축으로 작용한다. 따라서 선언한 base 실수차원 $d$를 갖는 유일한 불변 Lipschitz graph family가 존재하고, 같은 base orbit 위의 fiber는

$$
\|y_{t+n}-h_{t+n}(x_{t+n})\|
\le q^n\|y_t-h_t(x_t)\|
\tag{15e}
$$

로 graph를 추적한다.

증명. (15c)의 둘째 식은 (15d)의 sup norm을 $R$ 안에 남긴다. 두 base 점의 역상을 비교하면 graph 기울기는 $\mu(q\kappa+L_x)$ 이하이므로 셋째 식이 slope class를 보존한다. 같은 base 역상에서 두 graph의 차이는 $B_t$와 $g_t$의 fiber Lipschitz 항만 남아 $q$배 이하가 된다. 완비 graph 공간에 Banach 고정점 정리를 적용하면 유일성이 나오고, 같은 계산을 fiber 궤적에 반복하면 (15e)가 나온다. □

세 margin

$$
m_q=1-q,\qquad
m_R=R-(qR+G),\qquad
m_\kappa=\kappa-\mu(q\kappa+L_x)
\tag{15f}
$$

를 따로 기록한다. $m_q$는 엄격히 양수여야 한다. $m_R$ 또는 $m_\kappa$가 $0$이면 정리는 성립하지만 작은 오차에도 깨질 수 있으므로 robust interior가 아니다. $q=1$의 identity fiber에서는 모든 constant graph가 불변이어서 유일성과 흡인이 실패한다. 이는 수축 등호를 허용할 수 없다는 완전한 반례다.

`quantitative_graph_transform.py`는 raw/base/fiber 척도를 exact rational로 정규화하고 세 margin, 실패 원인, robust-interior 표지, graph 차원과 $q^n$ tracking을 반환한다. focused test는 26/26, 유한 부분공간 코드와의 인접 검증은 43/43을 통과했다. 같은 상수로 $d=1,4,5,6,100$이 모두 통과하므로 이 정리는 공급한 차원을 보존할 뿐 4–6을 선택하지 않는다.

#### 정량적 coupled-base subcase

triangular 가정도 affine base의 전역 Lipschitz 부분경우에서는 제거할 수 있다. 무차원 chart를

$$
x'=A_tx+a_t+f_t(x,y),
\qquad y'=B_ty+g_t(x,y)
\tag{15g}
$$

로 두고 $\|A_t^{-1}\|\le\mu$, $\|B_t\|\le b$라 하자. $f_t$의 base·fiber Lipschitz 상계를 $L_{fx},L_{fy}$, $g_t$의 것을 $L_{gx},L_{gy}$라 쓰고, cross-unit 상수와 graph slope는 $X_*,Y_*$로 먼저 무차원화한다. $q=b+L_{gy}$와

$$
\alpha=\mu^{-1}-L_{fx}-L_{fy}\kappa
\tag{15h}
$$

를 정의한다. $\alpha>0$이면 graph $h$ 위의 base 역상을 찾는 식

$$
x=A_t^{-1}\{x'-a_t-f_t(x,h(x))\}
\tag{15i}
$$

의 우변은 수축률 $\mu(L_{fx}+L_{fy}\kappa)<1$을 갖는다. 따라서 graph마다 base 재매개화가 유일하고, 그 lower Lipschitz 상계는 $\alpha$다.

**[정리: affine coupled-base Lipschitz graph transform]** 다음 네 조건을 가정하자.

$$
\alpha>0,
\qquad qR+G\le R,
\qquad q\kappa+L_{gx}\le\kappa\alpha,
\tag{15j}
$$

$$
Q:=q+(q\kappa+L_{gx})\frac{L_{fy}}{\alpha}<1.
\tag{15k}
$$

그러면 반지름 $R$, slope $\kappa$인 graph family 공간에서 coupled graph transform은 $Q$-수축이고, 공급한 base 차원을 갖는 유일한 불변 Lipschitz graph family가 존재한다.

증명. 첫 조건은 (15i)의 존재·유일성을 준다. 둘째는 fiber image를 tube 안에 남긴다. 한 graph 위에서 fiber 출력 차이는 $(q\kappa+L_{gx})\|x_1-x_2\|$ 이하이고 base 출력 차이는 $\alpha\|x_1-x_2\|$ 이상이므로 셋째 조건이 slope를 보존한다. 같은 출력 base 점에 대한 두 graph의 역상 차이는 $(L_{fy}/\alpha)\|h_1-h_2\|_\infty$ 이하이다. 이를 fiber 출력 차이에 넣으면 정확히 (15k)의 $Q$가 나온다. Banach 고정점 정리가 존재와 유일성을 준다. □

기록할 margin은

$$
m_\alpha=\alpha,
\quad m_R=R-(qR+G),
\quad m_\kappa=\kappa\alpha-(q\kappa+L_{gx}),
\quad m_Q=1-Q.
\tag{15l}
$$

$m_\alpha,m_Q$는 엄격히 양수여야 한다. $\alpha=0$에서는 $A=I$, $f(x,y)=-x$가 base map을 상수로 만들어 역상 자체를 없애고, $Q=1$의 identity fiber에서는 constant invariant graph가 유일하지 않다. $L_{fx}=L_{fy}=0$이면 $\alpha=1/\mu$, $Q=q$가 되어 (15c)의 triangular slope 식을 정확히 회복한다.

`quantitative_coupled_graph_transform.py`는 이 네 margin과 실패 원인을 exact rational로 계산한다. focused 26/26, triangular 회귀 52/52를 통과했다. 같은 조건이 $d=1,4,5,6,100$을 모두 받아들이므로 이 확장도 4–6을 선택하지 않는다.

#### 정량적 $C^1$ triangular subcase

“표준 bootstrap으로 매끄럽다”는 문장을 첫 미분 단계에서는 명시적 부등식으로 바꿀 수 있다. base가 graph와 독립인 $C^1$ diffeomorphism이고 triangular인

$$
x'=\phi_t(x),
\qquad y'=B_ty+g_t(x,y)
\tag{15m}
$$

를 두고, 앞의 Lipschitz certificate가 이미 통과했다고 하자. $g_t$가 $C^1$이고 fiber 방향으로 편미분이

$$
\|D_xg_t(x,y)-D_xg_t(x,y')\|
\le H_x\|y-y'\|,
$$

$$
\|D_yg_t(x,y)-D_yg_t(x,y')\|
\le H_y\|y-y'\|
\tag{15n}
$$

을 만족한다고 하자. raw 상수는 $H_x=X_*H_{x,raw}$, $H_y=Y_*H_{y,raw}$로 무차원화한다.

graph transform의 도함수는 동일한 base 역상 $x=\phi_t^{-1}(x')$에서

$$
D(\mathcal Th)(x')=
\{B_tDh+D_xg_t+D_yg_tDh\}D\phi_t^{-1}(x')
\tag{15o}
$$

다. 두 $C^1$ graph 반복의 함수거리와 도함수거리를 각각 $\delta_n,d_n$이라 하고

$$
\beta=q\mu,
\qquad c_D=\mu(H_y\kappa+H_x)
\tag{15p}
$$

로 두면 다음 정량 승격이 성립한다.

**[정리: nonaffine triangular $C^1$ 승격]** $\sup_{t,x'}\|D\phi_t^{-1}(x')\|\le\mu$이고 기존 Lipschitz gate와 함께 $\beta<1$이면 유일한 불변 Lipschitz graph는 $C^1$이고

$$
\delta_n\le q^n\delta_0,
\qquad
d_{n+1}\le\beta d_n+c_D\delta_n,
\tag{15q}
$$

$$
d_n\le
\beta^n d_0+c_D\delta_0
\sum_{j=0}^{n-1}\beta^{n-1-j}q^j
\tag{15r}
$$

가 성립한다.

증명. triangular 구조 때문에 두 graph는 같은 $x=\phi_t^{-1}(x')$와 같은 오른쪽 인자 $D\phi_t^{-1}(x')$를 쓴다. 따라서 (15o)를 빼면 $Dh-D\widehat h$에 곱해지는 항은 $q\mu=\beta$ 이하이다. $D_yg$의 변화는 $H_y\delta_n$ 이하이고 slope $\kappa$와 곱해지며, $D_xg$의 변화는 $H_x\delta_n$ 이하이다. 이것이 (15q)를 준다. 반복하면 (15r)가 나오고, $q,\beta<1$이면 합성곱 항도 0으로 간다. 함수와 도함수의 균일수렴 정리를 적용하면 Lipschitz 고정 graph가 $C^1$이다. affine constancy는 어느 단계에도 쓰이지 않는다. □

정확한 nonaffine witness도 있다.

$$
\phi_a(x)=x+a\sin x,
\qquad 0\le a<1
\tag{15s}
$$

이면 $1-a\le\phi_a'(x)\le1+a$이고 $\phi_a$는 strictly increasing이며 proper이므로 global $C^1$ diffeomorphism이다. 따라서

$$
\|D\phi_a^{-1}\|_\infty\le\frac1{1-a}.
\tag{15t}
$$

$a=1$에서는 $\phi_1'(\pi)=0$이라 유한한 uniform inverse-derivative bound가 없다. `sine_perturbed_base_inverse_lipschitz`는 exact $a\in[0,1)$에서 (15t)를 반환하고 경계를 거절한다.

엄격성은 실제 내용이다. 국소 선형 map $(x,y)\mapsto(qx,qy)$에서 $\mu=1/q$라 $q\mu=1$이고, $h_c(x)=c|x|$는 $h_c(qx)=qh_c(x)$를 만족하는 불변 Lipschitz graph지만 $c\ne0$이면 원점에서 미분 불가능하다. 따라서 등호에서 $C^1$을 강제할 수 없다.

`quantitative_c1_graph_transform.py`는 predecessor 실패를 그대로 보존하면서 $\beta$, margin, $c_D$와 (15q)의 exact 반복 상계를 반환한다. C1 본체 20/20, nonaffine fixture 10/10, 합동 회귀 30/30을 통과했다. 같은 조건은 $d=1,4,5,6,100$을 모두 받지만 그 차원을 선택하지는 않는다.

#### 정량적 affine coupled-base $C^1$ 승격

coupled map (15g)에서는 두 graph가 같은 출력 base 점을 만들더라도 역상 $x=F_h^{-1}(x')$와 역 Jacobian이 달라진다. 따라서 triangular 증명의 공통 오른쪽 인자 논법을 그대로 쓸 수 없다. 이를 닫기 위해 $C^1$ graph만이 아니라 다음의 정규화된 $C^{1,1}$ class를 고정한다.

$$
\|Dh\|\le\kappa,
\qquad \operatorname{Lip}(Dh)\le\Lambda,
\qquad
\operatorname{Lip}(Df_t)\le H_f,
\quad \operatorname{Lip}(Dg_t)\le H_g.
\tag{15u}
$$

여기서 Jacobian의 Lipschitz 상수도 $X_*,Y_*$로 정규화한 product chart의 무차원 수이다. $s=q\kappa+L_{gx}$라 두고 한 graph 위의 base·fiber Jacobian 변화 상계를

$$
C_F=H_f(1+\kappa)^2+L_{fy}\Lambda,
\qquad
C_Y=q\Lambda+H_g(1+\kappa)^2
\tag{15v}
$$

로 둔다. $\|DF_h^{-1}\|\le\alpha^{-1}$와 inverse 차이 항등식 $J_1-J_2=J_1(DF_2-DF_1)J_2$를 쓰면 출력 graph 도함수의 Lipschitz 상계는

$$
\Lambda_{\rm out}
=\frac{C_Y}{\alpha^2}+\frac{sC_F}{\alpha^3}.
\tag{15w}
$$

따라서 $\Lambda_{\rm out}\le\Lambda$가 바로 $C^{1,1}$ graph class 불변 조건이다. 이제 두 graph의 함수거리와 도함수거리를 $\delta,d$라 하자. 같은 출력 base 점에서 predecessor의 역상 추정은

$$
r_x=\frac{L_{fy}}{\alpha},
\qquad
\|x_1-x_2\|\le r_x\delta,
\qquad
Z=1+(1+\kappa)r_x
\tag{15x}
$$

를 준다. 상태점 이동과 $Dh$의 위치 이동을 각각 분리하면

$$
A_\delta=H_fZ(1+\kappa)+L_{fy}\Lambda r_x,
\qquad
Y_\delta=q\Lambda r_x+H_gZ(1+\kappa)
\tag{15y}
$$

이고, $\|DF_1-DF_2\|\le L_{fy}d+A_\delta\delta$, $\|DY_1-DY_2\|\le qd+Y_\delta\delta$가 된다.

**[정리: affine coupled-base $C^1$ graph transform]** 기존 coupled Lipschitz gate, (15u), $\Lambda_{\rm out}\le\Lambda$가 성립하고

$$
\beta_c=\frac{q}{\alpha}+\frac{sL_{fy}}{\alpha^2}
=\frac{Q}{\alpha}<1,
\qquad
c_c=\frac{Y_\delta}{\alpha}+\frac{sA_\delta}{\alpha^2}
\tag{15z}
$$

이면 유일한 불변 Lipschitz graph는 $C^1$이고

$$
\delta_{n+1}\le Q\delta_n,
\qquad
d_{n+1}\le\beta_cd_n+c_c\delta_n
\tag{15aa}
$$

가 성립한다.

증명. $D(\mathcal Th)=DY_h(DF_h)^{-1}$에서 한 graph의 위치 두 개를 비교하면 (15v)의 두 항과 inverse 차이 항등식이 (15w)를 준다. 서로 다른 graph 두 개를 같은 $x'$에서 비교하면 (15x)가 역상의 이동을, $C^{1,1}$ class가 $\|Dh_1(x_1)-Dh_2(x_2)\|\le d+\Lambda r_x\delta$를 준다. 이를 $DF,DY$의 block 전개에 넣으면 (15y)를 얻는다. 마지막으로 $DY_1J_1-DY_2J_2=(DY_1-DY_2)J_1+DY_2(J_1-J_2)$와 $\|J_i\|\le\alpha^{-1}$를 쓰면 (15aa)가 나온다. $Q,\beta_c<1$인 상삼각 반복의 유한 합성곱이 0으로 가므로 함수와 도함수가 함께 균일수렴하고 고정 graph는 $C^1$이다. □

$L_{fx}=L_{fy}=H_f=0$이면 $\alpha=1/\mu$, $Q=q$, $\beta_c=q\mu$가 되어 triangular 정리로 정확히 환원된다. 따라서 앞의 $q\mu=1$, $h_c(x)=c|x|$ 반례는 coupled 정리의 strict 경계도 막는다. `quantitative_coupled_c1_graph_transform.py`는 $C_F,C_Y,\Lambda_{\rm out},\beta_c,c_c$와 모든 margin을 exact rational로 반환한다. focused 21/21, coupled·무차원 인접 회귀 77/77을 통과했다. 다음 단계에서는 다시 affine triangular 범위로 좁혀 두 번째 미분을 완전히 전개한다.

#### 정량적 affine triangular $C^2$ 승격

첫 미분에서 graph-independent base는 두 graph의 역상을 같게 만들었다. 두 번째 미분에서는 여기에 base 역함수의 두 번째 미분이 없어야 가장 좁은 완결식이 된다. 따라서 이 절에서는 $x'=A_tx+a_t$인 affine triangular base만 다룬다. $P_t=A_t^{-1}$, $S_h(x)=B_th(x)+g_t(x,h(x))$, $J_h=(I,Dh)$로 두면 $\mathcal Th=S_h\circ F_t^{-1}$이고

$$
D^2(\mathcal Th)(x')[u,v]
=\left\{(B_t+D_yg_t)D^2h
+D^2g_t[J_h,J_h]\right\}[P_tu,P_tv].
\tag{15ab}
$$

이 식의 첫 항은 기존 fiber 수축이 graph의 Hessian에 작용하는 부분이고, 둘째 항은 비선형 map 자체의 굽음이 graph로 유입되는 부분이다. 이를 정량화하려고 정규화된 product chart에서

$$
\|D^2h\|\le\Lambda_2,
\qquad
\|D^2g_t\|\le K_2,
\qquad
\|D^2g_t(x,y_1)-D^2g_t(x,y_2)\|
\le K_3\|y_1-y_2\|
\tag{15ac}
$$

를 가정한다. $K_3$는 반드시 고전적 3차 미분 자체일 필요는 없고, fiber 방향에서 map Hessian의 Lipschitz modulus면 충분하다. 그러나 이 modulus를 완전히 생략할 수는 없다. 서로 다른 두 graph에서는 $h_1(x)$와 $h_2(x)$가 다르므로 $D^2g_t(x,h_1(x))-D^2g_t(x,h_2(x))$를 제어할 수단이 사라지기 때문이다.

$\|J_h\|\le1+\kappa$, $\|P_t\|\le\mu$, $\|B_t+D_yg_t\|\le q$를 (15ab)에 대입하면 출력 graph의 Hessian 상계는

$$
\Lambda_{2,\mathrm{out}}
=\mu^2\left\{q\Lambda_2+K_2(1+\kappa)^2\right\}.
\tag{15ad}
$$

따라서 $\Lambda_{2,\mathrm{out}}\le\Lambda_2$가 Hessian-bounded graph class의 불변 조건이다. 이제 두 반복의 함수·도함수·Hessian 거리를 각각 $\delta_n,d_n,e_n$이라 두고

$$
\beta_2=q\mu^2,
\qquad
c_{21}=2\mu^2K_2(1+\kappa),
\qquad
c_{20}=\mu^2\left\{K_2\Lambda_2+K_3(1+\kappa)^2\right\}
\tag{15ae}
$$

로 정의한다.

**[정리: affine triangular $C^2$ graph transform]** 기존 triangular $C^1$ certificate가 통과하고, (15ac), $\Lambda_{2,\mathrm{out}}\le\Lambda_2$, $\beta_2<1$이 성립하면 유일한 불변 graph는 $C^2$이며

$$
\delta_{n+1}\le q\delta_n,
\qquad
d_{n+1}\le\beta_1d_n+c_{10}\delta_n,
\qquad
e_{n+1}\le\beta_2e_n+c_{21}d_n+c_{20}\delta_n
\tag{15af}
$$

가 성립한다. 특히 Hessian 오차에는

$$
e_n\le\beta_2^ne_0+
\sum_{j=0}^{n-1}\beta_2^{n-1-j}
\left(c_{21}d_j+c_{20}\delta_j\right)
\tag{15ag}
$$

라는 유한 합성곱 상계가 있다.

증명. triangular base이므로 같은 출력 base 점에 대한 두 graph의 역상 $x=P_t(x'-a_t)$는 같다. (15ab)의 첫 항을 두 graph 사이에서 빼면 $(B+D_yg_1)(D^2h_1-D^2h_2)$가 $qe_n$을 준다. 남은 $(D_yg_1-D_yg_2)D^2h_2$는 $K_2\Lambda_2\delta_n$ 이하이다. 둘째 항에서는 한 번에 하나씩 bilinear 인자 $J_h$를 바꾸면 $2K_2(1+\kappa)d_n$이 나오고, map Hessian의 평가점을 바꾸면 $K_3(1+\kappa)^2\delta_n$이 나온다. 두 base 방향에 각각 $P_t$가 곱해지므로 전체에 $\mu^2$이 붙어 (15af)의 셋째 부등식이 된다. 앞의 두 recurrence와 합치면 대각 계수가 $q,\beta_1,\beta_2$인 비음수 상삼각 반복이다. 세 계수가 모두 1보다 작으므로 (15ag)와 그 아래 단계의 합성곱이 0으로 간다. 함수, 도함수, Hessian의 균일수렴 정리를 두 번 적용하면 고정 graph는 $C^2$이다. □

엄격 경계도 정확히 드러난다. $K_2=K_3=0$이면 $e_{n+1}\le q\mu^2e_n$으로 분리된다. 반면

$$
x'=\frac12x,
\qquad
y'=\frac14y,
\qquad
h_c(x)=c\,x|x|
\tag{15ah}
$$

에서는 $q\mu=1/2<1$이지만 $q\mu^2=1$이고 $h_c(x/2)=h_c(x)/4$이다. 이 graph는 $C^1$이지만 $c\ne0$이면 원점에서 $C^2$가 아니다. 그러므로 second-order bunching의 등호를 통과시킬 수 없다.

`quantitative_c2_graph_transform.py`는 $\Lambda_{2,\mathrm{out}},\beta_2,c_{21},c_{20}$, class와 bunching margin, (15af)의 exact 동시 반복을 반환한다. focused 22/22, C1·C2·무차원 인접 회귀 73/73을 통과했다. 같은 상수로 $d=1,4,5,6,100$을 모두 보존하지만 차원을 선택하지 않는다. 이제 base가 graph에 의존할 때 생기는 inverse-map Hessian 항을 복원한다.

#### 정량적 affine coupled-base $C^2$ 승격

coupled base에서는 graph가 달라지면 역상뿐 아니라 역함수의 두 번째 미분도 달라진다. 이 차이를 빠뜨리지 않으려고

$$
L_h=DF_h,
\quad J_h=L_h^{-1},
\quad K_h=DY_h,
\quad T_h=K_hJ_h,
\quad P_h=D^2F_h,
\quad R_h=D^2Y_h
\tag{15ai}
$$

로 둔다. 여기서 $T_h=D(\mathcal Th)$이다. inverse-function Hessian 항등식을 합성함수의 두 번째 미분에 넣으면

$$
D^2(\mathcal Th)(x')[u,v]
=N_h(x)[J_hu,J_hv],
\qquad
N_h=R_h-T_hP_h,
\qquad
x=F_h^{-1}(x').
\tag{15aj}
$$

앞 절의 coupled $C^1$ certificate는 $\|J_h\|\le\alpha^{-1}$, $\|T_h\|\le\rho:=s/\alpha$, $\|P_h\|\le C_F$, $\|R_h\|\le C_Y$를 이미 준다. 따라서

$$
N_0:=C_Y+\rho C_F,
\qquad
\|D^2(\mathcal Th)\|\le\frac{N_0}{\alpha^2}le\Lambda
\tag{15ak}
$$

이고, 마지막 부등식은 앞서 쓴 $C^{1,1}$ class 조건과 같은 식이다. 그러나 두 graph의 Hessian을 비교할 때는 새로운 문제가 생긴다. 역상이 $x_1\ne x_2$이므로 $D^2h_1(x_1)-D^2h_2(x_2)$를 같은 점의 Hessian 거리만으로 제어할 수 없다. $L_{fy}>0$인 경우에는

$$
\operatorname{Lip}(D^2h)\le\Xi,
\qquad
\operatorname{Lip}(D^2f_t)\le T_f,
\qquad
\operatorname{Lip}(D^2g_t)\le T_g
\tag{15al}
$$

를 추가해야 한다. 이들은 모두 normalized product chart의 무차원 상수다. 한 graph 안에서 product rule을 전개하면

$$
C_P=T_f(1+\kappa)^3+3H_f(1+\kappa)\Lambda+L_{fy}\Xi,
$$

$$
C_R=q\Xi+3H_g(1+\kappa)\Lambda+T_g(1+\kappa)^3,
$$

$$
C_T=\frac{C_Y}{\alpha}+\frac{sC_F}{\alpha^2},
\qquad
C_N=C_R+C_TC_F+\rho C_P
\tag{15am}
$$

를 얻는다. $N_h[J_h,J_h]$에서 $N_h$와 두 $J_h$를 차례로 바꾸고, 마지막에 $F_h^{-1}$로 재매개화하면 출력 graph-Hessian modulus는

$$
\Xi_{\mathrm{out}}
=\frac{C_N}{\alpha^3}
+\frac{2N_0C_F}{\alpha^4}.
\tag{15an}
$$

따라서 $L_{fy}>0$에서는 $\Xi_{\mathrm{out}}\le\Xi$가 $C^{2,1}$ class 불변 조건이다. 반대로 $L_{fy}=0$이면 base가 graph와 독립이고 두 graph의 역상이 같으므로 이 추가 gate는 필요하지 않다. 이는 단순한 편의 분기가 아니라 triangular 정리로의 정확한 환원을 보존하는 조건이다.

이제 두 graph의 같은 출력 base 점에서 $r_x=L_{fy}/\alpha$, $Z=1+(1+\kappa)r_x$를 다시 쓴다. 값·도함수·Hessian 거리를 $\delta,d,e$라 하면

$$
\|x_1-x_2\|\le r_x\delta,
\quad
\|z_1-z_2\|_\oplus\le Z\delta,
\quad
\|Dh_1(x_1)-Dh_2(x_2)\|
\le d+\Lambda r_x\delta,
$$

$$
\|D^2h_1(x_1)-D^2h_2(x_2)\|
\le e+\Xi r_x\delta.
\tag{15ao}
$$

$P_h$와 $R_h$를 각각 전개하면

$$
\|P_1-P_2\|
\le L_{fy}e+P_dd+P_\delta\delta,
\qquad
P_d=2H_f(1+\kappa),
$$

$$
P_\delta=L_{fy}\Xi r_x+H_fZ\Lambda
+2H_f(1+\kappa)\Lambda r_x
+T_fZ(1+\kappa)^2,
\tag{15ap}
$$

$$
\|R_1-R_2\|
\le qe+R_dd+R_\delta\delta,
\qquad
R_d=2H_g(1+\kappa),
$$

$$
R_\delta=q\Xi r_x+H_gZ\Lambda
+2H_g(1+\kappa)\Lambda r_x
+T_gZ(1+\kappa)^2.
\tag{15aq}
$$

앞의 $C^1$ recurrence에서 $\|T_1-T_2\|\le\beta_1d+c_1\delta$이므로 $N_h=R_h-T_hP_h$에 대해

$$
\|N_1-N_2\|
\le Qe+N_dd+N_\delta\delta,
$$

$$
N_d=R_d+C_F\beta_1+\rho P_d,
\qquad
N_\delta=R_\delta+C_Fc_1+\rho P_\delta.
\tag{15ar}
$$

**[정리: affine coupled-base $C^2$ graph transform]** 기존 coupled $C^1$ certificate, 필요한 경우의 $\Xi_{\mathrm{out}}\le\Xi$, 그리고

$$
\beta_{2,c}=\frac{Q}{\alpha^2}<1
\tag{15as}
$$

이 성립하면 유일한 불변 graph는 $C^2$이고

$$
e_{n+1}le\beta_{2,c}e_n+c_{21,c}d_n+c_{20,c}\delta_n,
$$

$$
c_{21,c}=\frac{N_d}{\alpha^2}
+\frac{2N_0L_{fy}}{\alpha^3},
\qquad
c_{20,c}=\frac{N_\delta}{\alpha^2}
+\frac{2N_0A_\delta}{\alpha^3}
\tag{15at}
$$

가 성립한다.

증명. (15ap)과 (15aq)는 $P_h,R_h$의 차이를 각각 $e,d,\delta$ 층으로 분해한다. 이를 $N_h=R_h-T_hP_h$에 넣으면 (15ar)가 나온다. inverse-Jacobian 항등식은 $\|J_1-J_2\|\le\alpha^{-2}(L_{fy}d+A_\delta\delta)$를 준다. 이제 (15aj)에서 먼저 $N_1$을 $N_2$로 바꾸고, 다음 두 outer argument $J_1$을 하나씩 $J_2$로 바꾸면 (15at)의 세 계수를 얻는다. 기존 value·derivative recurrence와 합친 전체 반복은 대각이 $Q,\beta_1,\beta_{2,c}$인 비음수 상삼각계다. 세 값이 모두 1보다 작으므로 함수·도함수·Hessian 차이가 0으로 가고 고정 graph는 $C^2$이다. □

$L_{fx}=L_{fy}=L_{gx}=H_f=T_f=0$이면 $\alpha=1/\mu$, $Q=q$, $r_x=0$이다. $H_g=K_2$, $T_g=K_3$로 놓으면 (15as)와 (15at)는 (15ae)의 triangular $\beta_2,c_{21},c_{20}$으로 정확히 환원된다. 따라서 (15ah)의 $q\mu^2=1$ 반례는 coupled 정리의 strict 경계도 막는다.

`quantitative_coupled_c2_graph_transform.py`는 $C_P,C_R,C_T,N_0,C_N,\Xi_{\mathrm{out}}$, 모든 $P,R,N$ 차이 계수와 (15at)의 exact 반복을 반환한다. focused 22/22, coupled C1/C2·triangular C2·무차원 인접 회귀 97/97, 전체 graph·C1·C2·scalar/tensor scale·무차원 연동 223/223을 통과했다. $d=1,4,5,6,100$을 모두 보존하지만 선택하지 않는다. 남은 smooth 공백은 nonaffine/local $C^2$, $C^3$ 이상 Faà di Bruno 계층, 실제 뇌에서의 chart와 균일 고차 도함수 상수 추정이다.

affine이라는 제한을 풀면, 기저 좌표 자체의 굽음이 graph의 Hessian으로 들어온다. graph와 무관한 전역 $C^2$ diffeomorphism $x'=\phi_t(x)$와 그 역함수 $\psi_t=\phi_t^{-1}$에 대해

$$
\|D\psi_t\|\le\mu,\qquad \|D^2\psi_t\|\le\nu
\tag{15au}
$$

를 가정하자. $S_h(x)=B_th(x)+g_t(x,h(x))$이면 $\mathcal Th=S_h\circ\psi_t$이고, 빠뜨리면 안 되는 정확한 항은

$$
D^2(\mathcal Th)
=D^2S_h[D\psi_t,D\psi_t]+DS_hD^2\psi_t
\tag{15av}
$$

이다. 앞의 affine 식에는 둘째 항이 0이었다. $s=q\kappa+L_x$라 놓으면 (15ac)는 이제

$$
\Lambda_{2,\mathrm{out}}^{\mathrm{na}}
=\mu^2\{q\Lambda_2+K_2(1+\kappa)^2\}+s\nu
\le\Lambda_2
\tag{15aw}
$$

로 바뀐다. 즉 연결로 정의한 좌표공간 자체가 휘면 그 굽음 $\nu$가 현재 graph의 일차 기울기 $s$와 곱해져 이차 구조로 유입된다.

두 graph는 같은 출력 기저점에서 같은 $\psi_t,D\psi_t,D^2\psi_t$를 사용한다. 따라서 별도의 $D^2\psi_t$ Lipschitz modulus 없이도 차이를 닫을 수 있고,

$$
e_{n+1}\le q\mu^2e_n
+\{2\mu^2K_2(1+\kappa)+q\nu\}d_n
+\left[\mu^2\{K_2\Lambda_2+K_3(1+\kappa)^2\}
+\nu(H_y\kappa+H_x)\right]\delta_n
\tag{15ax}
$$

을 얻는다. **[정리: global nonaffine triangular $C^2$ 승격]** 기존 nonaffine $C^1$ certificate가 통과하고 (15aw)와 strict $q\mu^2<1$이 성립하면 유일한 불변 graph는 $C^2$이다. 이 정리는 기저가 graph에 의존하지 않는 경우에 한정된다. coupled nonaffine 기저에서는 두 graph의 역함수가 달라지므로 추가 비교항이 필요하다.

굽은 기저의 정확한 예시는

$$
\phi_a(x)=x+a\sin x,\qquad
\mu_a=\frac1{1-a},\qquad
\nu_a=\frac{a}{(1-a)^3},\qquad 0\le a<1
\tag{15ay}
$$

이다. $a=1/4$와 계약에 고정한 상수에서는

$$
\Lambda_{2,\mathrm{out}}^{\mathrm{na}}=\frac{214}{27}<8,
\quad \beta_2=\frac89,
\quad c_{21}^{\mathrm{na}}=\frac{20}{27},
\quad c_{20}^{\mathrm{na}}=\frac{38}{27}.
\tag{15az}
$$

$a=0$이면 affine $C^2$ 식으로 정확히 환원되고, $a=1$이면 $\phi_1'(\pi)=0$이어서 유한 inverse certificate가 깨진다. 구현은 focused 26/26, triangular C1/C2·무차원 인접 101/101, graph/C1/C2·무차원 연동 196/196을 통과했다. 이 결과는 전역 graph-independent nonaffine triangular $C^2$를 닫지만, nonaffine coupled $C^2$, $C^3$ 이상, 실제 뇌 chart와 4–6차원 선택은 여전히 열어 둔다.

전역 공간 전체가 아니라 한 순간의 국소 chart만 사용할 때에는 “미분식이 맞다”는 사실 외에 정의역 검사가 하나 더 필요하다. $U_t=\overline B(c_t,r_t)$를 순간 기저영역이라 하고, $\phi_t,\psi_t=\phi_t^{-1}$가 이 compact 집합들의 열린 근방에서 $C^2$라고 하자. 필요한 최소 조건은

$$
\psi_t(U_{t+1})\subseteq U_t,
\qquad
\sup_{x'\in U_{t+1}}\|\psi_t(x')-c_t\|
\le r_{\mathrm{pre},t}\le r_t
\tag{15ba}
$$

이다. 그러면 모든 $x'\in U_{t+1}$에서

$$
(\mathcal T_th_t)(x')
=B_th_t(\psi_t(x'))
+g_t(\psi_t(x'),h_t(\psi_t(x')))
\tag{15bb}
$$

가 선언한 영역 안의 $h_t$만 읽는다. 따라서 앞의 value·derivative·Hessian 수축 증명은 국소 convex 영역에서도 그대로 작동한다.

그러나 이 조건의 불변성 의미는 정확히 제한해야 한다. 얻는 것은

$$
F_t(\operatorname{graph}h_t)
\cap(U_{t+1}\times Y)
=\operatorname{graph}h_{t+1}
\tag{15bc}
$$

라는 **backward-covered overflow invariance**다. 입력 graph의 모든 점이 다음 영역 안에 남는다는 뜻은 아니다. 그 더 강한 결론에는 별도로 $\phi_t(U_t)\subseteq U_{t+1}$가 필요하다. 특히 같은 compact 영역을 diffeomorphism이 양방향으로 정확히 덮으면 경계가 경계에 닿으므로, 양방향 포함을 모두 ‘엄격한 내부 margin’으로 바꾸는 식은 일반적으로 모순이다.

**[정리: local nonaffine triangular $C^2$ 승격]** (15ba), 열린 근방에서의 균일 $C^2$ 상계, 기존 nonaffine C1 gate, (15aw), strict $q\mu^2<1$이 성립하면 (15bc)의 의미에서 유일한 국소 불변 graph는 $C^2$이다. coverage equality $r_{\mathrm{pre}}=r_t$는 통과하지만 perturbation에 robust하지 않다.

국소 굽은 expanding witness는

$$
\phi_{\lambda,a}(x)=\lambda x+a\sin x,
\quad
\mu=(\lambda-a)^{-1},
\quad
\nu=a(\lambda-a)^{-3},
\quad
r_{\mathrm{pre}}\le\mu r_t,
\qquad \lambda>a\ge0
\tag{15bd}
$$

이다. $(\lambda,a,r_t)=(2,1/4,1)$이면

$$
m_{\mathrm{cov}}=\frac37,
\quad
\Lambda_{2,\mathrm{out}}^{\mathrm{loc}}=\frac{94}{343},
\quad
\beta_2=\frac8{49},
\quad
c_{21}=\frac{36}{343},
\quad
c_{20}=\frac{37}{343}.
\tag{15be}
$$

두 반례가 지위를 고정한다. $U=[-1,1]$과 $\phi(x)=x/2$에서는 $x'=3/4$가 $h(3/2)$를 요구하므로 coverage 없는 국소식은 정의되지 않는다. 반대로 $\phi(x)=2x$는 inverse coverage를 만족하지만 $x=3/4$를 $3/2$로 보내므로 전체 전진 보존은 나오지 않는다. 구현은 focused 31/31, 인접 133/133, graph/C1/C2/local·무차원 연동 228/228을 통과했다.

전체 전진 보존까지 요구하려면 두 방향을 독립적으로 검사해야 한다. 즉

$$
\phi_t(U_t)\subseteq U_{t+1},
\qquad
\psi_t(U_{t+1})\subseteq U_t
\quad\Longrightarrow\quad
\phi_t(U_t)=U_{t+1}.
\tag{15bf}
$$

둘째 포함에 $\phi_t$를 적용하면 $U_{t+1}\subseteq\phi_t(U_t)$가 되므로 등호가 나온다. 따라서 overflow 교집합 식 (15bc)는

$$
F_t(\operatorname{graph}h_t)
=\operatorname{graph}h_{t+1}
\tag{15bg}
$$

로 강화된다.

여기에는 직관과 반대되는 경계 규율이 있다. 닫힌 ball의 정확한 forward·inverse image 반지름을

$$
R_{\mathrm{fwd}}
=\sup_{x\in U_t}\|\phi_t(x)-c_{t+1}\|,
\qquad
R_{\mathrm{pre}}
=\sup_{x'\in U_{t+1}}\|\psi_t(x')-c_t\|
\tag{15bh}
$$

라 하면 matched-domain에서는 반드시
$R_{\mathrm{fwd}}=r_{t+1}$, $R_{\mathrm{pre}}=r_t$이다. 두 값이 반지름보다 크면 포함을 인증하지 못하고, 정확한 supremum이 반지름보다 작다는 주장은 full ball image가 경계에 닿는다는 사실과 모순이다. 그러므로 domain contact margin은 0이어야 한다. 이는 미분 수축 margin이 strict일 수 없다는 뜻이 아니라, compact matched-domain의 구조적 접촉을 수치적 robust interior로 잘못 부르면 안 된다는 뜻이다.

**[정리: exact matched-domain local nonaffine triangular $C^2$]** (15ba)의 모든 미분·inverse coverage 조건과 forward inclusion이 함께 성립하면, 유일한 국소 $C^2$ graph는 (15bg)의 의미에서 전체 전진·역방향 불변이다. 미분 계층의 recurrence는 (15ax)와 같고, 새 결론은 집합의 정의역 지위다.

실제로 굽으면서 경계를 고정하는 예시는

$$
\phi_a(x)=x+a x(1-x^2),
\qquad 0\le a<\frac12,
\qquad U=[-1,1]
\tag{15bi}
$$

이다. $\phi_a(\pm1)=\pm1$이고 $\phi_a'(x)=1+a-3ax^2\ge1-2a>0$이므로 열린 collar에서 diffeomorphism이며 $U$를 정확히 $U$로 보낸다. 또한

$$
\mu=(1-2a)^{-1},
\qquad
\nu=6a(1-2a)^{-3}.
\tag{15bj}
$$

$a=1/4$의 exact fixture에서는

$$
\Lambda_{2,\mathrm{out}}=\frac78,
\quad
\beta_2=\frac12,
\quad
c_{21}=\frac32,
\quad
c_{20}=0.
\tag{15bk}
$$

Hessian-class margin $1/8$과 bunching margin $1/2$은 strict하지만 두 domain-contact residual은 0이다. 구현은 focused 32/32, 인접 166/166, graph/C1/C2/local/matched·무차원 연동 261/261을 통과했다. 이제 graph-independent nonaffine C2의 global, overflow-local, exact matched-domain full-forward 경로가 모두 닫혔다.

다음 공백은 기저가 휘는 동시에 fiber graph 값에도 의존하는 경우다. 먼저 $C^1$ 층을 분리해야 한다. 기저를

$$
F_h(x)=\phi_t(x)+f_t(x,h(x)),
\qquad
\|\phi_t(x_1)-\phi_t(x_2)\|
\ge\mu^{-1}\|x_1-x_2\|,
\qquad
\|D^2\phi_t\|\le H_\phi
\tag{15bl}
$$

로 놓는다. coupled Lipschitz 단계의 $\alpha,Q,r_x,Z$는 변하지 않는다. 그러나 $DF_h$ 자체가 입력점에 따라 휘므로 one-graph Jacobian modulus는

$$
C_F^{\mathrm{na}}
=H_\phi+H_f(1+\kappa)^2+L_{fy}\Lambda
\tag{15bm}
$$

가 되고,

$$
\Lambda_{\mathrm{out}}^{\mathrm{na}}
=\frac{C_Y}{\alpha^2}
+\frac{sC_F^{\mathrm{na}}}{\alpha^3}
\le\Lambda
\tag{15bn}
$$

가 C1,1 class gate다.

두 graph는 같은 출력점에서도 서로 다른 역상 $x_1,x_2$를 사용한다. 따라서

$$
\|D\phi_t(x_1)-D\phi_t(x_2)\|
\le H_\phi r_x\delta
\tag{15bo}
$$

가 추가되고, base-Jacobian의 value coefficient는

$$
A_\delta^{\mathrm{na}}
=H_\phi r_x+H_fZ(1+\kappa)+L_{fy}\Lambda r_x
\tag{15bp}
$$

가 된다. **[정리: global nonaffine coupled $C^1$ 승격]** (15bn)과 기존 coupled Lipschitz gate, strict $Q/\alpha<1$이 성립하면 유일한 불변 graph는 $C^1$이고

$$
d_{n+1}
\le\frac Q\alpha d_n
+\left(\frac{Y_\delta}{\alpha}
+\frac{sA_\delta^{\mathrm{na}}}{\alpha^2}\right)\delta_n.
\tag{15bq}
$$

여기서 중요한 점은 대각 수축계수 $Q/\alpha$는 그대로지만, class 상계와 value-to-derivative 교차항은 모두 커진다는 것이다. 둘 중 하나에서 $H_\phi$를 빼면 nonaffine 식이 아니다.

정확한 witness $\phi_{\lambda,a}(x)=\lambda x+a\sin x$에서는 $\mu=(\lambda-a)^{-1}$, $H_\phi=a$다. $(\lambda,a)=(1001/1000,1/1000)$와 기존 strict coupled fixture를 넣으면

$$
C_F^{\mathrm{na}}=\frac{147}{2000},
\quad
\Lambda_{\mathrm{out}}^{\mathrm{na}}=\frac{69388}{253265},
\quad
A_\delta^{\mathrm{na}}=\frac{351}{18500},
\tag{15br}
$$

$$
\beta_1=\frac{308}{1369},
\qquad
c_{10}^{\mathrm{na}}=\frac{41212}{1266325}.
\tag{15bs}
$$

$H_\phi=0$이면 네 신규 증가분이 모두 사라져 affine coupled C1 계수로 정확히 환원된다. 구현은 focused 30/30, 인접 113/113, 전체 graph/C1/C2/local/matched·무차원 연동 292/292를 통과했다. 이로써 nonaffine coupled C2가 사용할 정당한 C1 predecessor가 생겼다. 다음 $C^2$ 층에는 $D^2\phi_t$의 위치 변화 modulus가 추가로 필요하다.

이제 같은 비아핀 결합 기저에서 2차 미분까지 닫을 수 있다. 앞 절의
$H_\phi$에 더해

$$
\|D^2\phi_t(x_1)-D^2\phi_t(x_2)\|
\le T_\phi\|x_1-x_2\|
\tag{15bt}
$$

를 둔다. 이는 “공간이 휜다”는 말을 단지 곡률이 유한하다는 조건과,
그 곡률이 위치에 따라 얼마나 빨리 바뀌는가라는 서로 다른 두 조건으로
분리한다. $P_h=D^2F_h$, $R_h=D^2Y_h$,
$N_h=R_h-(DY_hDF_h^{-1})P_h$라 쓰면 역함수 항등식은

$$
D^2(\mathcal Th)(x')[u,v]
=N_h(x)[DF_h(x)^{-1}u,DF_h(x)^{-1}v]
\tag{15bu}
$$

이다. 따라서 $H_\phi$는 $P_h$의 크기에, $T_\phi$는 $P_h$의 위치별
변화율에 들어간다. 한 그래프 위의 정확한 상계는

$$
C_P^{\mathrm{na}}
=T_\phi+T_f(1+\kappa)^3
+3H_f(1+\kappa)\Lambda+L_{fy}\Xi,
\tag{15bv}
$$

$$
C_N^{\mathrm{na}}=C_R+C_TC_F^{\mathrm{na}}+\rho C_P^{\mathrm{na}},
\qquad
\Xi_{\mathrm{out}}^{\mathrm{na}}
=\frac{C_N^{\mathrm{na}}}{\alpha^3}
+\frac{2NC_F^{\mathrm{na}}}{\alpha^4}.
\tag{15bw}
$$

**[정리: global nonaffine coupled $C^2$ 조건부 폐쇄]** 기존 비아핀 결합
$C^1$ 게이트, 조건부 $C^{2,1}$ class 게이트
$\Xi_{\mathrm{out}}^{\mathrm{na}}\le\Xi$, 그리고
$Q/\alpha^2<1$이 성립하면 유일한 불변 그래프는 $C^2$이다.
$L_{fy}=0$이면 두 그래프의 기저 선행점이 같으므로 $\Xi$ 게이트는
필요하지 않다. 즉 기저가 휘었다는 이유만으로 불필요한 정칙성을
강제하지 않는다.

두 그래프를 비교할 때 새로 생기는 항은

$$
P_\delta^{\mathrm{na}}
=T_\phi r_x+L_{fy}\Xi r_x+H_fZ\Lambda
+2H_f(1+\kappa)\Lambda r_x+T_fZ(1+\kappa)^2.
\tag{15bx}
$$

이에 따라 Hessian 거리 $e_n$, 미분 거리 $d_n$, 값 거리 $\delta_n$은

$$
e_{n+1}\le\frac Q{\alpha^2}e_n
+\left(\frac{N_d^{\mathrm{na}}}{\alpha^2}
+\frac{2NL_{fy}}{\alpha^3}\right)d_n
+\left(\frac{N_\delta^{\mathrm{na}}}{\alpha^2}
+\frac{2NA_\delta^{\mathrm{na}}}{\alpha^3}\right)\delta_n
\tag{15by}
$$

을 만족한다. 이는 값·기울기·곡률 오차가 위에서 아래로 전달되는
상삼각 수렴식이다. 따라서 여기서 “순간적으로 집중된 저차원 의식”에
대해 실제로 얻은 것은 차원 4--6의 선택이 아니라, **주어진 저차원
그래프가 주변 고차원 상태공간과 결합되고 기저 공간 자체가 휘어도
곡률까지 보존되는 충분조건**이다.

정확한 sine witness에서
$\phi_{\lambda,a}(x)=\lambda x+a\sin x$,
$(\lambda,a)=(1001/1000,1/1000)$로 두면
$\mu=1$, $H_\phi=T_\phi=1/1000$이고

$$
\Xi_{\mathrm{out}}^{\mathrm{na}}
=\frac{701739032}{1733598925},
\quad
\beta_{2,c}=\frac{12320}{50653},
\quad
c_{21,c}^{\mathrm{na}}=\frac{840496}{9370805},
\quad
c_{20,c}^{\mathrm{na}}=\frac{410712208}{8667994625}.
\tag{15bz}
$$

$H_\phi=T_\phi=0$에서는 모든 층이 affine coupled $C^2$로 정확히
환원되고, $f\equiv0$에서는 $\nu=H_\phi\mu^3$인 graph-independent
nonaffine triangular $C^2$로 정확히 환원된다. 반대로
$Q/\alpha^2=1$에서는 포함된 $C^1$/비-$C^2$ 반례 때문에 실패한다.
구현은 focused 29/29, 인접 139/139, 전체 graph/C1/C2/local/matched·무차원
연동 322/322를 통과했다. 남은 것은 local-domain 게이트와의 결합,
$C^3$ 이상, 실제 뇌장의 동정, 그리고 의식·차원 선택의 경험적 다리다.

전역 정리를 실제 순간 chart에 쓰려면 한 가지 정의역 문제가 더 남는다.
입력 기저영역을 $U_t=\overline B(c_t,R_t)$, 다음 순간의 기저영역을
$U_{t+1}$이라 하자. 결합 모형에서 역으로 따라가는 사상은
$\phi_t^{-1}$가 아니라 그래프 $h$에 의존하는

$$
F_{t,h}^{-1},
\qquad
F_{t,h}(x)=\phi_t(x)+f_t(x,h(x))
\tag{15ca}
$$

이다. 따라서 $\phi_t^{-1}(U_{t+1})\subseteq U_t$만 확인하면 충분하지
않다. 직관적으로는 같은 길의 지도라도 실린 짐 $h(x)$이 조향에
영향을 주면 실제 되돌아가는 길이 달라지는 것과 같다. 이 비유는
$f$가 0일 때 깨지며, 그때에만 두 역상이 다시 일치한다.

**[공리: 수학적 정의역 입력]** 모든 허용 그래프가 쓰는 역함수 가지가
$U_{t+1}$의 열린 근방에 존재하고, 다음 균일 상계가 주어졌다고 하자.

$$
\sup_h\sup_{x'\in U_{t+1}}
\|F_{t,h}^{-1}(x')-c_t\|
\le R_{\mathrm{pre}}\le R_t.
\tag{15cb}
$$

기준 기저 길이 $X_0$로 나눈 정의역 여유는

$$
m_{\mathrm{dom}}
=\frac{R_t-R_{\mathrm{pre}}}{X_0}.
\tag{15cc}
$$

이렇게 정규화해야 서로 다른 좌표 단위에서도 같은 조건을 비교할 수
있다. 등호 $m_{\mathrm{dom}}=0$은 허용되지만 작은 오차에 견디는 내부점은
아니다.

**[정리: backward-covered local nonaffine coupled $C^2$]** 식 (15cb)와
전역 비아핀 결합 $C^2$ 정리의 모든 조건이 각 열린 collar에서 균일하게
성립하면, 국소 graph transform은 잘 정의되고 기존 값·기울기·Hessian
수렴식을 그대로 보존한다. 따라서 유일한 국소 불변 그래프는 $C^2$이며

$$
\operatorname{graph}(h_{t+1})
=\Phi_t(\operatorname{graph}(h_t))
\cap(U_{t+1}\times Y)
\tag{15cd}
$$

를 만족한다.

증명. 식 (15cb)는 모든 $x'\in U_{t+1}$와 모든 허용 그래프에서
$F_{t,h}^{-1}(x')\in U_t$를 보장한다. 그러므로 전역 증명에 나타나는
$Y_h,P_h,R_h,N_h,J_h$를 모두 같은 collar 안에서 평가할 수 있다.
정의역을 제한해도 연쇄법칙과 각 균일 상계는 바뀌지 않으므로 앞 절의
상삼각 $C^0/C^1/C^2$ 수렴식이 그대로 적용된다. 완비인 제한 graph
class에서 수축 고정점은 유일하고, 출력 영역에 남는 상만 취하면 식
(15cd)를 얻는다. □

여기서 식 (15cd)는 **overflow 불변성**이다. 입력 영역의 모든 점이 다음
영역 안으로 간다는 full-forward 명제가 아니다. 실제로
$\phi(x)=2x$이면 $[-1,1]$의 역상은 안쪽에 들어오지만 $x=3/4$의 전진상은
$3/2$라서 영역을 벗어난다.

결합이 실제로 0이 아닌 정확한 예도 있다. 한 기저차원에서

$$
F_h(x)=\lambda x+a\sin x+\varepsilon h(x),
\qquad |h(x)|\le R_y
\tag{15ce}
$$

라 두면, $\lambda>a\ge0$에서

$$
R_{\mathrm{pre}}
=\frac{R_{t+1}+\varepsilon R_y}{\lambda-a}.
\tag{15cf}
$$

이는 $(\lambda-a)|x|\le|F_h(x)|+\varepsilon|h(x)|$에서 한 단계씩
따라온다. $\lambda=2$, $a=1/4$, $\varepsilon=1/20$이고 모든 반경이
1이면 기저 역함수 상계는 $\mu=4/7$, 실제 결합 역함수 상계는
$40/69$, $R_{\mathrm{pre}}=3/5$,
$m_{\mathrm{dom}}=2/5$이다. 같은 fixture의 2차 bunching은
$7520/109503$이다. 결합을 끄면 식 (15cf)는 graph-independent 상계
$\mu R_{t+1}$로 정확히 환원된다.

$\phi^{-1}$만 검사하는 더 넓은 부모 주장은 반례로 제거된다.
$\phi(x)=2x$, $f(x,y)=y$, $h=-2$이면 $\phi^{-1}(1)=1/2$는 단위영역
안이지만 실제 $F_h^{-1}(1)=3/2$는 밖이다. 따라서 현재 닫힌 것은 실제
$F_h^{-1}$를 균일하게 검사하는 backward-covered 국소 정리다. 정확한
matched full-forward 결합 정리는 모든 허용 그래프에서 경계를 보존하는
별도 graph class가 필요하므로 아직 미완성이다. 구현 검증은 집중 35개,
인접 133개, 관련 통합 358개를 통과했으며, 이는 수치 구현의 일관성이지
실제 뇌 chart나 의식의 증거가 아니다.

앞의 overflow 정리는 출력영역에서 필요한 역상을 모두 제공하지만,
입력영역의 모든 점이 다음 영역에 남는다고 말하지는 않는다. 이 마지막
간극을 닫으려면 기저영역의 양방향 접촉뿐 아니라 그래프 자체의 경계도
보존해야 한다. compact 기저 ball $U_t$에서 경계고정 그래프 class를

$$
\mathcal H_0
=\{h:h|_{\partial U_t}=0\}
\tag{15cg}
$$

로 정의하자. 여기서 $\partial U_t$는 ball의 전체 경계다. 한 차원에서는
두 끝점 $-1,1$이지만, 높은 차원에서는 경계 sphere 전체이므로 끝점
두 개만 검사하는 식으로 바꾸어서는 안 된다.

**[공리: 수학적 matched-domain 입력]** 실제 graph-dependent 사상에 대한
uniform exact contact와 fiber 경계조건을 각각 독립적으로 둔다.

$$
R_{\mathrm{pre}}^{\mathrm{exact}}=R_t,
\qquad
R_{\mathrm{fwd}}^{\mathrm{exact}}=R_{t+1},
\tag{15ch}
$$

$$
\sup_{h\in\mathcal H_0}
\sup_{x\in\partial U_t}\|h(x)\|=0,
\qquad
\sup_{x\in\partial U_t}\|g_t(x,0)\|=0.
\tag{15ci}
$$

식 (15ch)는 역상과 전진상의 영역 포함을 따로 검사한다. 식 (15ci)는
기저영역이 맞더라도 변환된 fiber graph가 경계에서 들뜨는 경우를
차단한다. 네 조건을 하나의 `matched=true` 표지로 합치지 않는 이유는
어느 경계가 실패했는지 각각 반증할 수 있어야 하기 때문이다.

**[정리: exact matched local nonaffine coupled $C^2$]** 식 (15ch)--(15ci)와
앞 절의 overflow-local 비아핀 결합 $C^2$ 정리가 성립하면, 모든 허용
그래프에 대해

$$
F_{t,h}(U_t)=U_{t+1}
\tag{15cj}
$$

이고 graph transform은 $\mathcal H_0$를 보존한다. 따라서 유일한 국소
$C^2$ 불변 그래프는 선언한 compact 영역에서 전진·후진 모두 정확히
불변이다.

증명. 전진 접촉은 $F_h(U_t)\subseteq U_{t+1}$을 준다. 역상 접촉에
$F_h$를 적용하면 반대 포함을 얻으므로 식 (15cj)가 성립한다. compact
ball 사이의 diffeomorphism은 경계를 경계로 보낸다. 따라서
$x'\in\partial U_{t+1}$의 선행점 $x=F_h^{-1}(x')$는
$\partial U_t$에 있고, 식 (15ci)에서

$$
(\mathcal Th)(x')
=B_t h(x)+g_t(x,h(x))=0
\tag{15ck}
$$

이다. 그러므로 경계고정 graph class가 보존된다. 정의역 조건은 앞 절의
미분계수와 상삼각 수렴식을 바꾸지 않으므로 같은 수축 고정점이 유일한
$C^2$ graph를 준다. □

정확한 image equality는 compact ball의 경계에 닿는다. 따라서 domain
contact margin은 양수가 아니라 정확히 0이다. 이는 미분 bunching margin도
0이라는 뜻이 아니다. 정의역 접촉은 구조적으로 비강건하지만, 내부의
미분 수축은 엄격할 수 있다.

결합이 0이 아닌 경계고정 예시는 다음과 같다.

$$
F_h(x)=x+a x(1-x^2)+\varepsilon h(x),
\qquad h(-1)=h(1)=0.
\tag{15cl}
$$

$\|h'\|\le\kappa$이면

$$
F_h'(x)
=1+a-3ax^2+\varepsilon h'(x)
\ge1-2a-\varepsilon\kappa.
\tag{15cm}
$$

$a=1/100$, $\varepsilon=1/100$, $\kappa=1/2$에서는 오른쪽이 $39/40$이고
$F_h(\pm1)=\pm1$이다. 그러므로 모든 허용 $F_h$는 단조증가하며 단위구간을
정확히 자기 자신으로 보낸다. 이때 기저 역함수 상계는 $50/49$, 실제
결합 역함수 상계는 $40/39$이고

$$
H_\phi=T_\phi=\frac3{50},
\quad
\Xi_{\mathrm{out}}=\frac{4085248}{30074733},
\quad
\beta_{2,c}=\frac{6272}{59319},
\tag{15cn}
$$

$$
c_{21,c}=\frac{37888}{3855735},
\qquad
c_{20,c}=\frac{1021312}{751868325}.
\tag{15co}
$$

$Y_h=h/10$으로 두면 fiber 경계도 0으로 보존된다. 반대로 graph 경계가
0이 아니면 비영 $\varepsilon h$가 기저 끝점을 이동시키고, fiber boundary
forcing이 0이 아니면 변환 graph가 $\mathcal H_0$를 벗어난다. 결합을
끄면 graph-independent matched cubic으로 정확히 환원된다.

구현 검증은 집중 38개, 인접 173개, 관련 통합 397개를 통과했다. 이로써
명시한 균일 전제 아래의 미분·정의역 계층은 matched local nonaffine
coupled $C^2$까지 닫혔다. 다음 수학 공백은 $C^3$ 이상이며, 실제 뇌장과
의식·4--6차원 동일시는 여전히 별도의 경험적 미완성 다리다.

### 5.1.1 유한 비정규 Riesz 계산에서 무엇을 인증하는가

실험 또는 시뮬레이션에서는 무한 연산자 대신 유한 실수 행렬 $U$를 얻는 경우가 많다. 이때 원형 contour $\Gamma=\{c+re^{i\theta}\}$가 스펙트럼 묶음을 피해서 둘러싸면, **[정리: 조건부 유한 contour-Riesz]** 정확한 대상은

$$
P=\frac{1}{2\pi i}\oint_\Gamma(zI-U)^{-1}dz
\tag{16}
$$

인 일반적으로 **비직교인** Riesz 사영이다. 계산기가 만드는 것은 $P$가 아니라, $z_k=c+re^{2\pi ik/N}$에서의 사다리꼴 근사

$$
P_N=\frac1N\sum_{k=0}^{N-1}re^{2\pi ik/N}(z_kI-U)^{-1}
\tag{17}
$$

와 더 촘촘한 $P_{2N}$이다. 정확한 $P$만 $P^2=P$ 및 $PU=UP$를 보장한다. $P_N$과 $P_{2N}$는 수렴을 탐색하는 근사이며, 두 값이 가깝다는 사실만으로 정확한 오차 상계가 생기지는 않는다. 한편 $Q$는 $P$ 또는 수치적으로 realify한 $\operatorname{Ran}P_N$의 상 위에 만든 **직교** 사영이다. 따라서 $P$는 동역학적 spectral identity에, $Q$는 (22)의 집중도에 쓰고 둘을 바꾸어 쓰지 않는다.

**[정의: 유한 certificate의 단위]** `finite_riesz.py`는 $U,c,r$와 같은 spectral 단위를 갖는 양의 `spectral_reference_scale` $s_{\rm ref}$를 요구한다. 실제 정규화 척도는

$$
s_{\rm spec}=\max(s_{\rm ref},\|U\|_2,|c|,r,\max_j|\lambda_j|).
\tag{18}
$$

이다. 원시 sampled separation은 spectral 단위, 원시 sampled resolvent norm은 그 역단위를 갖는다. 그러나 refinement, imaginary content, idempotence, commutator, realified rank 판정은 모두 $s_{\rm spec}$와 projector 크기로 나눈 무차원 residual로만 strict decision을 내린다. 이렇게 해야 단위를 바꾸었을 때 certificate의 통과·실패가 임의로 바뀌지 않는다.

**[산출: a-posteriori ceiling]** `FiniteRieszCertificate`는 sampled separation·sampled resolvent 최대값·$\|P_{2N}-P_N\|$·idempotence·commutator·realification singular value/rank·imaginary residual을 보고한다. 이는 유한 계산의 사후 진단이다. sampling point가 contour 전체를 덮었다는 증명도, $P_N-P$의 엄밀한 bound도 아니다. analytic strip 폭 $a$와 그 안의 적분함수 상계 $M$를 별도로 인증한 경우에만

$$
\|P_N-P\|\le\frac{2M}{e^{aN}-1}
\tag{19}
$$

같은 quadrature bound를 쓸 수 있다. 그렇지 않으면 certificate의 `quadrature_error_bound`는 비어 있어야 한다.

여기서 “contour 전체”를 실제로 인증하는 데 필요한 조건을 더 정확히 쓸 수 있다. 원 $\Gamma$의 표본점을 $z_k=c+re^{2\pi ik/N}$로 놓고, 각 점의 최소특이값에 대한 **엄밀한 하한 enclosure**와 인접 표본점에서 원 위 임의 점까지의 거리의 **엄밀한 상한**을 갖췄다고 하자. 원의 최대 chord 길이는 $2r\sin(\pi/(2N))$이므로, 이들을 뺀 값

$$
\widehat\delta_N=
\min_k\underline{\sigma}_{\min}(z_kI-U)
-\overline{2r\sin(\pi/(2N))}
\tag{19a}
$$

이 양수이면 다음의 전구간 결론이 따른다.

**[정리: full-circle resolvent 인증]** (19a)의 모든 하한·상한이 엄밀 enclosure이고 $\widehat\delta_N>0$이면

$$
\inf_{z\in\Gamma}\sigma_{\min}(zI-U)\ge\widehat\delta_N,
\qquad
\sup_{z\in\Gamma}\|(zI-U)^{-1}\|_2\le\widehat\delta_N^{-1}.
\tag{19b}
$$

증명. 최소특이값은 연산자 차이에 대해 1-Lipschitz다. 원 위 임의 점을 가장 가까운 표본점과 비교하면 특이값 하한은 표본 하한에서 chord 상한만큼만 줄어든다. 양수 하한은 모든 점에서 가역성을, 역연산자 노름의 표준 등식은 두 번째 부등식을 준다. □

**[정리: analytic-strip 사다리꼴 오차]** $a>0$이고 닫힌 환대 $re^{-a}\le|z-c|\le re^a$가 스펙트럼을 피하며, 안쪽·바깥쪽 두 원에서 (19b)의 엄밀 하한 $\delta_-,\delta_+$를 얻었다고 하자. 그러면

$$
M_a=\max\left\{\frac{re^{-a}}{\delta_-},\frac{re^a}{\delta_+}\right\},
\qquad
\|P_N-P\|_2\le\frac{2M_a}{e^{aN}-1}.
\tag{19c}
$$

증명. resolvent 적분의 각도 매개화는 폭 $a$의 해석 strip으로 연장되고, 안쪽·바깥쪽 경계의 resolvent 상계가 그 strip의 적분함수 상계 $M_a$를 준다. 해석적 주기함수의 사다리꼴 오차 정리를 적용하면 (19c)가 나온다. □

이 두 정리는 float64 표본 계산과 다르다. `finite_contour_bounds.py`는 원 중앙·안쪽·바깥쪽의 sampled 최소특이값과 chord 보정값을 계산해 14개의 focused test를 통과했지만, 결과에는 `FLOAT64_UNVERIFIED_FULL_CIRCLE_ESTIMATE` 또는 `FLOAT64_UNVERIFIED_ANALYTIC_STRIP_ESTIMATE`라는 표지를 붙인다. 부동소수점 SVD와 삼각함수 값은 outward-rounded enclosure가 아니므로 (19b)나 (19c)의 전제를 충족시키지 않는다. 이 구현은 인증 경로의 입력·실패 조건을 실행 가능하게 만든 estimate이지, verified arithmetic이나 정확한 Riesz 사영을 산출한 것이 아니다.

### 5.1.2 정확 유리수 네 점 인증이 메우는 빈자리

float64 표본이 충분하지 않았던 이유는 두 가지다. 첫째, 화면에 출력된 최소특이값은 반올림된 근삿값이므로 실제 값보다 작지 않다는 보장이 없다. 둘째, 원 위의 유한 표본을 모두 통과해도 표본 사이의 점까지 가역이라는 결론은 chord 보정과 그 보정값 자체의 엄밀 상한 없이는 나오지 않는다. 따라서 여기서는 기존의 float64 경로를 바꾸지 않고, 선언한 입력 자체가 정확한 유리수 복소행렬일 때만 별도의 좁은 인증 경로를 둔다.

**[정리: 조건부 정확 유리수 full-circle 인증]** $U\in\mathbb Q(i)^{n\times n}$, $c\in\mathbb Q(i)$, $r>0$, 그리고 이들과 같은 spectral 단위를 갖는 유리수 기준척도 $s_*>0$를 택한다. 먼저

$$
\widetilde U=U/s_*,\qquad
\widetilde c=c/s_*,\qquad
\widetilde r=r/s_*
\tag{19d}
$$

로 무차원 대표를 만든 뒤에만 모든 exact elimination과 dyadic 제곱근 enclosure를 수행한다. 네 점 $d_k=i^k$와 $\widetilde A_k=(\widetilde c+\widetilde r d_k)I-\widetilde U$에 대해 exact Gaussian elimination이 역행렬을 주고, 그 Frobenius 노름의 엄밀 상한 $q_k^+$가 주어졌다고 하자. 또한 $\widetilde r\sqrt{2-\sqrt2}$의 엄밀 상한을 $\widetilde\chi^+$라 하자. 그러면

$$
\underline{\widetilde\delta}_4=
\min_{0\le k<4}(q_k^+)^{-1}-\widetilde\chi^+>0
\tag{19e}
$$

이면 중앙 원 전체가 resolvent-free이고, $\sup_\Gamma\|(zI-\widetilde U)^{-1}\|_2\le\underline{\widetilde\delta}_4^{-1}$이다. 원래 단위의 separation과 resolvent 상한은 각각 $s_*\underline{\widetilde\delta}_4$와 $\underline{\widetilde\delta}_4^{-1}/s_*$로 그 뒤에만 복원한다.

증명. exact inverse의 Frobenius 노름은 spectral 노름의 상한이므로 $(q_k^+)^{-1}\le\sigma_{\min}(\widetilde A_k)$이다. 네 점 원의 임의 점은 가장 가까운 표본점에서 $\widetilde r\sqrt{2-\sqrt2}$ 이하만큼 떨어진다. 최소특이값의 1-Lipschitz 성질에 이 거리의 엄밀 상한을 적용하면 (19e)가 원 전체의 양의 하한을 준다. 양의 하한은 가역성과 resolvent 노름 상한을 함께 준다. □

정규화를 먼저 하는 순서도 정리의 일부다. 고정된 dyadic 격자를 원래 단위에 바로 적용하면 같은 물리량을 모두 같은 비율로 바꾸었을 때 정규화된 반올림 결과가 달라질 수 있다. 반대로 (19d) 뒤에 격자를 적용하면 공통의 양의 유리수 rescaling 아래 입력, 분기, certificate 상태가 그대로이고, 원래 단위의 두 보고값만 공변적으로 변한다.

**[정리: 제한된 정확 유리수 analytic-strip 인증]** 유리수 $q>1$에 대해 안쪽·바깥쪽 반지름을 $r_-=r/q$, $r_+=rq$로 정하고, 중앙·안쪽·바깥쪽 원 모두에 위의 full-circle 인증이 성립한다고 하자. 더 나아가 $UV=V\Lambda$를 정확히 만족하는 가역 $V\in\mathbb Q(i)^{n\times n}$와 대각 $\Lambda$가 주어지고, 모든 대각원소 $\lambda_j$가 닫힌 환대 $r/q\le|\lambda_j-c|\le rq$의 바깥에 엄밀히 놓인다고 하자. 이때

$$
P=V\operatorname{diag}\!\left(1_{|\lambda_j-c|<r}\right)V^{-1},
\qquad
P_4=\frac14\sum_{k=0}^{3}(z_k-c)(z_kI-U)^{-1}
\tag{19f}
$$

이고, $M^+=\max\{r_-/\underline\delta_-,r_+/\underline\delta_+\}$에 대해

$$
\|P_4-P\|_2\le\frac{2M^+}{q^4-1}
\tag{19g}
$$

가 성립한다. 증명. 정확 witness는 닫힌 환대에 pole이 없음을 보이고 $P$를 정확히 고정한다. $a=\log q$인 strip의 양쪽 경계에는 앞 절의 resolvent 상한과 반지름 인자가 $M^+$를 준다. 중심 적분함수의 Fourier 계수는 $e^{-a|m|}$로 감쇠하며, 네 점 사다리꼴합은 $4$의 배수 계수만 alias한다. 기하급수 꼬리를 합하면 (19g)가 나온다. 이 오차식은 중앙의 $P_4$에만 해당하며 안쪽·바깥쪽 이산 사영에는 해당하지 않는다. □

이 경로는 `verified_rational_contour.py`가 exact `Fraction`/문자열 입력, 네 점 mesh, inverse·제곱근·chord의 정확 잔차, 그리고 필요한 경우 witness와 닫힌 환대 배제를 모두 통과했을 때만 결과를 낸다. focused test 11개는 양의 원과 비직교 diagonalizable witness뿐 아니라 singular node, 비양의 보수적 하한, 잘못된 witness, 환대 내부·경계 고유값, binary float, 지원하지 않는 mesh를 거절하는지를 점검했다. 이는 선언한 유리수 입력에 관한 소프트웨어·수학 경로의 검증이지, 미지의 측정 행렬을 정확히 알았다는 뜻은 아니다.

exact 기준행렬만을 다루는 제한 중 입력오차 부분은 다음 구간-family 정리로 메웠다. 다만 네 node와 nominal strip의 exact rational diagonalization witness 제한은 그대로이고, 실제 측정 오차가 아래 구간 안에 든다는 통계적 보장은 별도 문제다.

