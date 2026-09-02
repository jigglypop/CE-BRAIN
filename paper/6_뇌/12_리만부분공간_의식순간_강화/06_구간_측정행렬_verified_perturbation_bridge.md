# 06. 구간 측정행렬 전체로 옮기는 verified perturbation bridge

### 5.1.3 구간 측정행렬 전체로 옮기는 verified perturbation bridge

기준행렬 $U_0\in\mathbb Q(i)^{n\times n}$의 각 성분에 대해 비음수 유리수 반경 $a_{ij},b_{ij}$를 고정하고

$$
\mathcal U(U_0;a,b)=\left\{U_0+\Delta:
|\Re\Delta_{ij}|\le a_{ij},\quad
|\Im\Delta_{ij}|\le b_{ij}\right\}
\tag{19h}
$$

를 정의한다. 이 집합의 실제 원소는 유리수일 필요가 없다. 기준척도 $s_*$로 먼저 정규화한 뒤

$$
\widetilde S=\sum_{ij}\left[left(\frac{a_{ij}}{s_*}\right)^2+
\left(\frac{b_{ij}}{s_*}\right)^2\right],
\qquad
(\widetilde\varepsilon^+)^2\ge\widetilde S
\tag{19i}
$$

인 dyadic 유리수 상계 $\widetilde\varepsilon^+$를 잡으면 모든 $U\in\mathcal U$에 대해

$$
\|\widetilde\Delta\|_2\le\|\widetilde\Delta\|_F
\le\sqrt{\widetilde S}\le\widetilde\varepsilon^+
\tag{19j}
$$

이다. 마지막 부등식은 각 성분의 실수부·허수부 직사각형을 원판 상계로 바꾸고 Frobenius 노름을 합한 결과다.

**[정리: 구간-family full-circle와 rank 안정성]** 기준행렬의 앞 절 인증이
$\inf_{z\in\Gamma}\sigma_{\min}(zI-\widetilde U_0)\ge
\underline{\widetilde\delta}_0>0$을 주고

$$
\widetilde\varepsilon^+<\underline{\widetilde\delta}_0
\tag{19k}
$$

라 하자. 그러면 모든 $U\in\mathcal U$와 $z\in\Gamma$에 대해

$$
\sigma_{\min}(zI-\widetilde U)
\ge\underline{\widetilde\delta}_0-\widetilde\varepsilon^+>0,
\qquad
\|(zI-\widetilde U)^{-1}\|_2
\le\frac{1}{\underline{\widetilde\delta}_0-\widetilde\varepsilon^+}.
\tag{19l}
$$

또한 같은 contour로 정의한 정확한 Riesz 사영은 전 구간 family에서 rank가 같고

$$
\|P(U)-P(U_0)\|_2
\le
\rho_P^+
:=
\frac{\widetilde r\,\widetilde\varepsilon^+}
{\underline{\widetilde\delta}_0
\left(\underline{\widetilde\delta}_0-\widetilde\varepsilon^+\right)}.
\tag{19m}
$$

증명. 최소특이값의 1-Lipschitz 성질을 (19j)에 적용하면 (19l)이 나온다. $U_t=U_0+t\Delta$는 (19k)에 의해 $0\le t\le1$ 내내 contour를 피한다. $P(U_t)$는 연속이고 유한차원 사영의 trace와 rank는 같은 정수이므로 rank가 변하지 않는다. 마지막으로 resolvent identity
$R_U-R_0=R_U\Delta R_0$를 길이 $2\pi r$인 원에 적분하면 (19m)을 얻는다. 이 증명은 eigenvector 직교성을 쓰지 않으므로 비정규 행렬에도 성립한다. □

nominal analytic-strip 인증이 $\eta_4^+\ge\|P_4(U_0)-P(U_0)\|_2$를 주는 경우에는 오차 원인을 합치지 않고

$$
\|P(U)-P_4(U_0)\|_2\le\rho_P^++\eta_4^+
\tag{19n}
$$

로 분리한다. 첫 항은 미지 행렬이 기준행렬에서 움직이는 비용이고, 둘째 항은 기준행렬의 네 점 적분 오차다. 따라서 (19n)은 $P_4(U)$를 계산했다거나 네 점 사영이 정확하다는 주장이 아니다.

엄격부등식 (19k)은 기술적 장식이 아니다. 스칼라 $U_0=0$, 단위원, $\Delta=1$에서는 nominal margin과 오차가 모두 $1$이고 $z=1$이 실제 singular point가 된다. 등호를 허용할 수 없는 완전한 반례다. 반대로 rank 보존도 작은 projector 이동을 뜻하지 않는다. $U_e=\begin{pmatrix}0&e\\0&2\end{pmatrix}$는 고유값과 선택 rank가 변하지 않지만 $P(U_e)-P(U_0)=\begin{pmatrix}0&-e/2\\0&0\end{pmatrix}$이므로 projector는 실제로 움직인다.

`verified_interval_contour.py`는 (19h)–(19n)을 별도 exact apparatus로 구현한다. 음수·Boolean·binary float·shape mismatch를 거절하고, 정규화된 $\widetilde S$와 제곱근 양쪽 bracket·제곱 잔차, raw/normalized uncertainty·separation·resolvent, rank 보존 Boolean, projector 두 오차항을 노출한다. focused test는 15/15, predecessor와의 인접 통합은 26/26, 무차원 게이트는 21/21을 통과했다.

(19i)의 Frobenius 상계가 보수적이라는 공백도 한 단계 더 닫았다. 각 정규화된 직사각형 성분에 대해 outward dyadic 상계
$c_{ij}^+\ge\sqrt{\widetilde a_{ij}^2+\widetilde b_{ij}^2}$를 만들고

$$
L_1^+=\max_j\sum_i c_{ij}^+,\qquad
L_\infty^+=\max_i\sum_jc_{ij}^+,\qquad
\widetilde\varepsilon_{1\infty}^+
\ge\sqrt{L_1^+L_\infty^+}
\tag{19o}
$$

로 둔다. $\|A\|_2^2\le\|A\|_1\|A\|_\infty$이므로 이것도 전 구간상자의 연산자 노름 상계다. 따라서 실제 apparatus는 Frobenius만 버리거나 induced만 고르는 대신

$$
\widetilde\varepsilon_*^+
=\min\left\{\widetilde\varepsilon_F^+,
\widetilde\varepsilon_{1\infty}^+\right\}
\tag{19p}
$$

를 사전에 고정해 (19k)–(19n)에 대입한다. 두 상계를 매번 모두 계산하므로 (19p)는 실패 뒤 방법을 바꾸는 post-hoc 선택이 아니며, 어느 경우에도 기존 상계보다 나빠지지 않는다. $C=I_n$이면 Frobenius는 $\sqrt n$, induced는 $1$이라 induced가 엄격히 낫다. 반면 $C=\begin{pmatrix}1&1\\1&0\end{pmatrix}$이면 각각 $\sqrt3$과 $2$라 Frobenius가 낫다. 이 비지배성 때문에 minimum이 필요하다.

`verified_interval_tightening.py`는 기존 Frobenius 결과 객체를 그대로 보존하면서 entry bracket, $L_1^+$, $L_\infty^+$, product bracket, 두 후보와 선택법을 모두 노출한다. 고정된 대각 구간 fixture에서는 기존 Frobenius 경로가 margin을 소진해 non-certificate였지만 동일한 상자의 induced 상계가 통과했다. focused test는 13/13, exact-rational부터 세 단계 인접 통합은 39/39를 통과했다.

전역 상계가 구조를 잃는 공백은 componentwise residual/Krawczyk 경로로 한 단계 더 닫았다. 네 contour node의 정규화된 기준행렬
$A_{0k}=(\widetilde c+\widetilde r d_k)I-\widetilde U_0$마다 정확 유리수 근사역행렬 후보 $B_k$를 공급하되, 이를 역행렬이라고 가정하지 않는다. 대신

$$
R_k=I-B_kA_{0k},\qquad
G_k^+=|R_k|^++|B_k|^+D^+,\qquad
q_{1k}^+=\|G_k^+\|_1,\quad
q_{\infty k}^+=\|G_k^+\|_\infty
\tag{19q}
$$

를 전부 outward arithmetic으로 계산한다. 여기서 $D^+$는 (19h)의 모든 $|\widetilde\Delta_{ij}|$를 성분별로 덮는 행렬이다.

**[정리: componentwise residual full-circle]** 네 node 모두에서 $q_{1k}^+<1$ 및 $q_{\infty k}^+<1$이라 하자. 그러면 Neumann 급수와 $A_k^{-1}=(B_kA_k)^{-1}B_k$에 의해

$$
M_{1k}^+=\frac{\||B_k|^+\|_1}{1-q_{1k}^+},\qquad
M_{\infty k}^+=\frac{\||B_k|^+\|_\infty}{1-q_{\infty k}^+},\qquad
\ell_k\ge\frac{1}{\sqrt{M_{1k}^+M_{\infty k}^+}}
\tag{19r}
$$

가 전 구간상자에 대해 성립한다. 실제 구현은 마지막 제곱근의 outward upper를 취해 그 역수를 $\ell_k$로 쓴다. 따라서

$$
\underline{\widetilde\delta}_{\rm res}
=\min_k\ell_k-\widetilde\chi^+>0
\tag{19s}
$$

이면 전 family가 원 전체를 피하고 같은 Riesz rank를 갖는다. 증명은 $I-B_kA_k=R_k+B_k\widetilde\Delta$의 성분별 절댓값을 (19q)로 덮고, 두 induced norm의 Banach 수축으로 (19r)을 얻은 뒤, 네 node와 원 사이 chord에 최소특이값의 1-Lipschitz 성질을 적용하는 순서다. $q=1$을 허용할 수는 없다. 스칼라 $A_0=B=1$, $|\Delta|\le1$은 $q=1$이면서 실제 singular $A=0$을 포함하는 완전한 반례다. □

residual 원의 공통 resolvent 상계를 $\overline{\widetilde R}_{\rm res}=\underline{\widetilde\delta}_{\rm res}^{-1}$라 하면 projector 이동도

$$
\|P(U)-P(U_0)\|_2
\le\widetilde r\,\widetilde\varepsilon_*^+
\overline{\widetilde R}_{\rm res}^{\,2}
=:\rho_{P,\rm res}^+,
\qquad
\|P(U)-P_4(U_0)\|_2\le\rho_{P,\rm res}^++\eta_4^+
\tag{19t}
$$

로 분리된다. 뒤 식은 독립적인 nominal strip 인증이 있을 때만 쓴다.

이 경로가 단순한 식 변경이 아님을 구조적 fixture가 보인다. $U_0=\operatorname{diag}(0,10)$이고 $|\Delta_{22}|\le1$만 허용하면 전역 uncertainty 상계는 $1$이라 기존 margin을 소진한다. 그러나 $z=1$에서 $B=A_0^{-1}=\operatorname{diag}(1,-1/9)$이고 $G^+=\operatorname{diag}(0,1/9)$이므로 먼 두 번째 성분은 $1/9$로 수축한다. 네 node와 chord를 모두 exact하게 검사한 결과, 동일한 상자에서 보존된 global 결과는 non-certificate이고 residual 결과는 positive certificate다.

`verified_interval_residual.py`는 exact·inexact rational $B_k$를 모두 잔차로 검증하며, witness·magnitude bracket·$G_k^+$·두 $q$·Banach inverse·node lower·chord·rank·projector 항을 노출한다. focused test는 14/14, exact nominal부터 네 단계 인접 통합은 53/53을 통과했다.

**[정리: exact rational witness 자동 구성]** 기준행렬과 contour 입력이 $\mathbb Q(i)$에서 정확히 주어지면, 네 정규화 node 행렬 $A_{0k}$에 대해 열을 왼쪽부터 처리하고 현재 열에서 처음 만나는 nonzero pivot을 택하는 Gauss--Jordan 규칙을 고정할 수 있다. 모든 pivot이 존재하면 field 연산만으로 $B_k$를 만들고

$$
B_kA_{0k}=I=A_{0k}B_k
\tag{19u}
$$

를 exact하게 검사한다. 어떤 node에서 pivot이 없으면 그 node 행렬은 singular이므로 witness를 만들지 않는다. 공통 raw spectral 단위변환 뒤 normalize-first $A_{0k}$가 같으면 pivot 경로와 witness도 같다.

이렇게 만든 exact inverse에서는 $R_k=0$이라 (19k)가 $G_k^+=|B_k|^+D^+$로 줄어든다. 그러나 uncertainty가 크면 두 contraction은 여전히 실패할 수 있다. 실제로 $U_0=[0]$에 반지름 1의 scalar uncertainty를 두면 nominal inverse 네 개는 모두 존재하지만 contraction 경계가 1에 닿아 family certificate는 실패한다. 반대로 $U_0=[1]$, 중심 0, contour 반지름 1이면 첫 node가 정확히 singular라 constructor가 먼저 멈춘다. 따라서 “witness 생성 성공”과 “구간 family 성공”은 서로 다른 gate다.

`exact_nominal_node_inverse_witnesses`와 convenience bridge는 이 지위 분리를 그대로 구현했다. 자동구성 focused test는 14/14, 기존 residual과의 연동은 28/28, exact contour부터 witness까지 전체 사슬은 67/67을 통과했다. 이로써 **exact rational nominal 입력**의 수동 witness 공급 공백은 닫혔다.

#### 대각 weighted residual: 좌표계를 바꾼 뒤 반드시 원래 norm으로 돌아오기

성분별 residual은 좌표축의 상대척도에 민감하다. 미리 공급한 양의 대각행렬 $W=\operatorname{diag}(w_i)$로

$$
A'_k=W^{-1}A_{0k}W,
\qquad B'_k=W^{-1}B_kW,
\qquad D'^+=W^{-1}D^+W
\tag{19v}
$$

를 만들면 transformed residual은

$$
G_k'^+=|I-B'_kA'_k|^+ + |B'_k|^+D'^+
\tag{19w}
$$

가 된다. 이 행렬의 induced $1$-norm과 $\infty$-norm이 모두 1보다 작으면 기존 Banach 논증으로 $\|(A'_k)^{-1}\|_2\le M'_{2k}$를 얻는다. 그러나 이것은 transformed norm의 상계이므로 그대로 원래 좌표의 singular lower로 쓰면 안 된다.

**[정리: conditioning을 포함한 weighted lower]** 양의 대각 $W$에 대해

$$
A_{0k}^{-1}=W(A'_k)^{-1}W^{-1},
\qquad
\kappa_2(W)=\frac{\max_iw_i}{\min_iw_i}
\tag{19x}
$$

이므로

$$
\sigma_{\min}(A_{0k})
\ge \ell_{wk}:=\frac{1}{\kappa_2(W)M'_{2k}}.
\tag{19y}
$$

기존 unweighted lower $\ell_{uk}$도 같은 원래 좌표의 하한이므로 $\ell_k^*=\max(\ell_{uk},\ell_{wk})$를 취해도 엄밀하다. 하지만 full circle은 여전히

$$
\delta_w^*=\min_k\ell_k^*-\widetilde\chi^+>0
\tag{19z}
$$

일 때만 통과한다. 여기의 chord $\widetilde\chi^+$는 원래 $2$-norm 좌표의 값이며 weighted node contraction만으로 대체할 수 없다.

conditioning 항이 필수라는 완전 반례가 있다. $A'=\begin{pmatrix}1&1\\0&1\end{pmatrix}$와 $W=\operatorname{diag}(K,1)$이면 $A=WA'W^{-1}=\begin{pmatrix}1&K\\0&1\end{pmatrix}$이고, $A^{-1}(0,1)^T=(-K,1)^T$이므로 $\|A^{-1}\|_2\ge\sqrt{K^2+1}$. transformed 하한을 $\kappa_2(W)=K$ 없이 원래 좌표에 쓰면 오차가 제한 없이 커진다.

`verified_weighted_interval_residual.py`는 $w$의 공통배율을 제거하고, transformed contraction·condition·번역된 lower·unweighted/weighted 선택·원래 chord를 모두 기록한다. focused 16/16, residual·witness 연동 44/44, 전체 contour 사슬 83/83, 현재 무차원 게이트 27/27을 통과했다. 구조적 nonnormal fixture에서는 unweighted node contraction이 실패하고 weighted 네 node가 모두 수축하지만, conditioning 뒤 chord lower가 비양수여서 full-circle 승격은 거절된다. 이것은 weighted 좌표 개선을 잘못된 물리 norm 개선으로 바꾸지 않는 음성 검증이다.

여전히 실제 신경 추정량의 오차가 (19h)에 동시에 포함된다는 보장은 없다. 후속 CE-B64는 floating solver가 저장한 binary64 witness의 **값**을 exact rational $B_k$로 복원하고 residual을 다시 검증하는 경로를 닫았다. 아래의 CE-WSEL은 사전고정된 **유한 대각 menu**의 개발 선택과 선택된 한 후보의 홀드아웃 확인까지 닫고, CE-DSR은 한 개의 공급된 exact block/dense similarity까지 닫는다. 그러나 solver algorithm·operation rounding mode·hardware/BLAS receipt와 연속·적응형 similarity 최적화는 별도 후보이다. estimator, sampling unit, 전처리, 의존성·결측, simultaneous coverage와 held-out 정책을 고정한 측정 계약 없이는 이 구간 정리를 실뇌 결과로 승격할 수 없다.

#### 사전고정 대각 가중치 menu: 개발 선택과 단일 홀드아웃 확인

한 개의 가중치 $W$를 공급하는 정리와, 자료를 본 뒤 좋은 $W$를 고르는 절차는 같은 주장이 아니다. 후자를 제한된 범위에서 닫기 위해 양의 대각행렬의 유한 menu

$$
\mathcal W=(W_1,\ldots,W_J),\qquad
W_j=\operatorname{diag}(w_{j1},\ldots,w_{jn}),\quad J\ge2
\tag{19za}
$$

를 개발 집합을 보기 전에 고정한다. 각 가중치 벡터는 최소 성분으로 나누어 정규화하며, 공통배율만 다른 후보는 중복으로 거절한다. 정렬된 후보 ID와 정확 유리수 가중치의 SHA-256은 menu 동일성 영수증일 뿐, 자료 출처 영수증은 아니다.

**[정의]** 개발 집합에서 후보 $j$의 가중 좌표 node 하한을 원래 $2$-norm으로 되돌린 값을 $\ell^{(D)}_{jk}=1/(\kappa_2(W_j)M'^{(D)}_{2,jk})$라 하고

$$
\delta_j^{(D)}=\min_k\ell^{(D)}_{jk}-\chi_D^+
\tag{19zb}
$$

를 후보 고유 점수로 둔다. 모든 변환 node가 수축하고 $\delta_j^{(D)}>0$인 후보만 적격이다. 여기서는 기존 구현의 $\max(\ell_{uk},\ell_{jk})$를 점수로 쓰지 않는다. 그 값은 모든 후보에 공통인 unweighted fallback을 보존하므로, 서로 다른 가중치가 실제로는 다른 하한을 내더라도 점수가 똑같아져 선택 문제가 퇴화할 수 있기 때문이다.

**[정리: 유한 menu의 개발 전용 선택]** 사전고정한 $\gamma\ge0$에 대해 적격 후보 중 $\delta_j^{(D)}$의 최대 후보 $j_*$와 차상위 후보가 각각 유일하고

$$
\delta_{j_*}^{(D)}-\delta_{j_{(2)}}^{(D)}>\gamma
\tag{19zc}
$$

라고 하자. 등호는 실패이며 후보 순서는 동점 해소 규칙이 아니다. 그러면 $j_*$는 개발 집합만으로 유일하게 정해진다. 홀드아웃에서는 다른 후보를 계산하지 않고 $W_{j_*}$ 하나만 계산하여

$$
\delta_{j_*}^{(H)}=\min_k\ell^{(H)}_{j_*k}-\chi_H^+>0
\tag{19zd}
$$

를 요구한다. 이때 개발·홀드아웃 두 구간 family 각각에 기존 Riesz rank 보존 정리를 적용할 수 있다. 증명은 각 양의 margin에 conditioning을 포함한 weighted full-circle 정리를 적용하고, 유한 정확 비교로 (19zc)의 유일성을 확인하면 된다. 홀드아웃에서 선택된 가중치 자체의 (19zd)가 실패하면 unweighted fallback이 통과하더라도 선택 확인은 실패한다. □

**[산출]** `predeclared_weighted_residual_selection.py`는 정규화 menu와 digest, 각 개발 후보의 가중치 고유 margin, 유일 승자·차상위·엄격한 advantage, 선택된 한 후보의 홀드아웃 인증을 분리해 기록한다. 최상위 동점, 차상위 동점, advantage 경계 등호, 적격 후보 부재, 선택 후보의 홀드아웃 실패는 모두 fail-closed다. 호출 계수 회귀는 개발 후보 $J$회 뒤 홀드아웃을 정확히 한 번만 실행함을 확인한다.

**[미완성: 확장·경험 적용]** 이 정리는 사전고정된 유한 대각 menu를 닫는다. 아래 정리들은 한 개의 공급된 exact block/dense similarity와 사전고정 유한 dense menu까지 별도로 닫지만, 연속·적응형 similarity 선택, 실제 solver 실행 provenance, source-locked 신경행렬과 동시구간 coverage는 닫지 않는다. 따라서 이 결과는 인간 의식이나 4--6차원에 대한 경험적 지지를 추가하지 않는다.

#### Exact block/dense similarity: 불확실성 상자와 원래 노름을 함께 운반하기

**[정리: dense similarity residual bridge]** $T\in\mathbb Q(i)^{n\times n}$가 가역이고 정규화된 성분별 불확실성이 $|\Delta|\le D^+$를 만족한다고 하자. 변환된 node와 witness를

$$
A'_{0k}=T^{-1}A_{0k}T,\qquad B'_k=T^{-1}B_kT
\tag{19ze}
$$

로 둔다. 그러면 삼각부등식으로

$$
|T^{-1}\Delta T|
\le |T^{-1}|D^+|T|
\le C^-D^+C^+=:D_T^+
\tag{19zf}
$$

이다. 여기서 $C^-\ge|T^{-1}|$, $C^+\ge|T|$는 각 복소 성분 크기의 outward rational 상계다. 또한

$$
\tau^+=\sqrt{\|C^+\|_1\|C^+\|_\infty},\qquad
\iota^+=\sqrt{\|C^-\|_1\|C^-\|_\infty},\qquad
\kappa_T^+=\tau^+\iota^+
\tag{19zg}
$$

를 outward dyadic 상계로 계산하면 $\kappa_T^+\ge\|T\|_2\|T^{-1}\|_2$다. 변환 좌표 residual 정리가 $\|(A'_{0k}+\Delta')^{-1}\|_2\le M'_{2k}$를 주는 경우 원래 좌표 node 하한은

$$
\ell_{Tk}=\frac{1}{\kappa_T^+M'_{2k}}
\tag{19zh}
$$

이다. 따라서 untransformed 하한과 같은 좌표에서 $\ell_k^*=\max(\ell_{uk},\ell_{Tk})$를 취하고

$$
\delta_T^*=\min_k\ell_k^*-\chi^+>0
\tag{19zi}
$$

일 때만 전체 contour와 공통 Riesz rank를 인증한다. 증명은 (19zf)의 성분별 곱 상계와 $(A_0+\Delta)^{-1}=T(A'_0+\Delta')^{-1}T^{-1}$에 (19zg)를 적용한 뒤 기존 full-circle 정리를 쓰면 된다. block-diagonal $T$는 이 dense 정리의 입력 부분류이고, 양의 대각 $T=W$에서는 앞의 weighted 정리로 정확히 환원된다. □

**[산출]** `verified_dense_similarity_interval_residual.py`는 $T^{-1}T=TT^{-1}=I$의 exact 양방향 검사, $C^\pm$, $D_T^+$, 두 induced norm 상계, $\kappa_T^+$, 변환 node와 원래 좌표로 번역된 하한을 모두 노출한다. 항등행렬 환원, 대각 weighted 환원, 비항등 유리 회전의 dense-only 양의 margin, 특이·차원불일치·float 입력 거절을 회귀한다.

**[후속 정리로 부분 폐쇄 / 미완성: 선택·경험 적용]** $T$ 하나를 공급한 정리 자체는 최적화 정리가 아니다. 아래 CE-DSEL이 사전고정 유한 dense menu 선택을 닫고, CE-ISR이 사전공급된 interval-valued $T$ family를 닫는다. 연속·적응형 최적화, 더 날카로운 verified singular-value condition bound, 실제 자료의 동시구간과 실행 provenance는 별도 문제다. 실패는 스펙트럼 교차의 증거가 아니며 더 나은 좌표계의 부재도 뜻하지 않는다.

#### Interval-valued dense similarity: 좌표계 오차까지 함께 운반하기

exact한 한 행렬 $T$ 대신

$$
T=T_0+E,\qquad |E|\le E^+,
\tag{19zi-a}
$$

만 아는 경우에는 모든 허용 $T$가 가역인지부터 증명해야 한다. $T_0$가 exact 가역이고

$$
Q=|T_0^{-1}|E^+,\qquad \theta=\|Q\|_\infty<1
\tag{19zi-b}
$$

이라 하자. $T=T_0(I+H)$, $H=T_0^{-1}E$이고 $|H|\le Q$이므로 Neumann 급수의 성분별 우세로

$$
|T^{-1}|\le K:=(I-Q)^{-1}|T_0^{-1}|,
\qquad |T|\le T^+:=|T_0|+E^+.
\tag{19zi-c}
$$

여기서 $(I-Q)^{-1}=\sum_{m\ge0}Q^m$은 성분별 비음수가 아니다. 등호 경계 $\theta=1$은 가역성을 보장하지 않으므로 반드시 거절한다.

정규화된 원행렬 family가 $A=A_0+D$, $|D|\le D^+$일 때 중심 변환 $S_0=T_0^{-1}A_0T_0$와 실제 변환 $S=T^{-1}AT$의 차이는 정확히

$$
S-S_0=T^{-1}D(T_0+E)+T^{-1}A_0E-T^{-1}ET_0^{-1}A_0T_0.
\tag{19zi-d}
$$

따라서 다음 성분별 외향 상계가 성립한다.

$$
\boxed{
D_S^+=KD^+T^+ + K|A_0|E^+
+KE^+|T_0^{-1}||A_0||T_0|
}
\tag{19zi-e}
$$

또한

$$
\tau^+=\sqrt{\|T^+\|_1\|T^+\|_\infty},\qquad
\iota^+=\sqrt{\|K\|_1\|K\|_\infty},\qquad
\kappa_I^+=\tau^+\iota^+
\tag{19zi-f}
$$

이면 모든 허용 $T$에 대해 $\kappa_2(T)\le\kappa_I^+$이다. 각 contour node에서 $(S_0,D_S^+)$의 residual 인증이 transformed 하한 $\ell'_{Ik}$를 주면 원래 좌표의 하한은

$$
\ell_{Ik}=\frac{\ell'_{Ik}}{\kappa_I^+},\qquad
\delta_I=\min_k\ell_{Ik}-\chi_{\mathcal M}^+.
\tag{19zi-g}
$$

**[정리: interval similarity residual bridge]** (19zi-b)의 엄격한 가역성, (19zi-e)의 외향 상자, 모든 node의 엄격한 residual 수축, 그리고 $\delta_I>0$가 성립하면 모든 $A_0+D$와 모든 $T_0+E$에 대해 전체 원 contour가 resolvent 집합에 있고 Riesz rank가 공통이다.

증명. (19zi-c)는 모든 허용 $T$의 가역성을 보인다. (19zi-d)에 절댓값 삼각부등식과 성분별 비음수 곱을 적용하면 (19zi-e)를 얻는다. residual 정리가 $\sigma_{\min}(T^{-1}(zI-A)T)\ge\ell'_{Ik}$를 주고, $zI-A=T[T^{-1}(zI-A)T]T^{-1}$이므로 singular-value 곱 부등식과 (19zi-f)에서 $\sigma_{\min}(zI-A)\ge\ell_{Ik}$를 얻는다. 마지막으로 mesh chord Lipschitz 확장을 적용하면 $\delta_I>0$가 전체 contour 비특이성과 rank 불변을 준다. □

**[산출·반례]** `verified_interval_similarity_residual.py`는 $Q$, $\theta$, Neumann 역행렬 envelope $K$, 세 항의 $D_S^+$, uniform condition 상계와 node별 번역 하한을 exact rational/dyadic outward arithmetic으로 산출한다. $E^+=0$이면 fixed identity route로 정확히 환원되고, 실제 rational 표본 $T,A$가 (19zi-c), (19zi-e)에 포함됨을 검사한다. $\theta=1$에서는 fail-closed다. 이는 supplied interval family 정리이지 interval을 자료에서 추정하거나 최적화하는 정리가 아니다.

#### 사전고정 finite dense menu

$T$와 $aT$ ($a\ne0$)는 같은 similarity를 만들므로 dense 후보는 첫 번째 row-major 비영 성분으로 나누어 exact canonical representative를 만든다. 이 정규화 뒤 같은 후보는 중복으로 거절한다.

**[정리: finite dense development selection]** 개발 자료를 보기 전에 exact 가역행렬 menu $\mathcal T=(T_1,\ldots,T_J)$와 $\gamma\ge0$을 고정하자. 각 후보에 대해 untransformed fallback이 아닌 dense 자체의 원래 좌표 margin

$$
\delta_j^{(D)}=\min_k\ell_{T_jk}^{(D)}-\chi_D^+
\tag{19zr}
$$

가 양수일 때만 적격으로 둔다. 최대 후보 $j_*$와 차상위가 각각 유일하고

$$
\delta_{j_*}^{(D)}-\delta_{j_{(2)}}^{(D)}>\gamma
\tag{19zs}
$$

일 때만 개발 승자를 고른다. 홀드아웃에서는 다른 $T_j$를 계산하지 않고 $T_{j_*}$ 하나에 대해

$$
\delta_{j_*}^{(H)}>0
\tag{19zt}
$$

를 요구한다. 각 margin은 이미 (19zf)--(19zi)의 transformed box, condition, 원래 chord를 포함하므로 두 family의 조건부 contour/rank 결론이 따른다. □

**[산출]** `predeclared_dense_similarity_selection.py`는 complex scalar-equivalence 정규화, exact invertibility, canonical digest, dense-only 개발 점수, 유일 승자·차상위·strict advantage와 선택된 한 후보의 홀드아웃을 기록한다. 적격 후보 0개·1개, 두 종류의 동점, 경계 등호, menu 위조와 홀드아웃 실패는 모두 분리해 거절한다.

**[후속 정리로 부분 폐쇄 / 미완성]** 유한 menu 밖의 연속 원 중심·반지름 최적화는 아래 CE-COPT가 complete exact diagonalization witness와 frozen signed-margin 목적함수에 한해 닫고, CE-CAOPT가 고정 exact 대수적 사영자와 균일 외부 역행렬 영역이 있는 defective/nonnormal 경우를 조건부로 닫는다. CE-EOPT/CE-SEOPT/CE-GAOPT는 compact diagonalized general-affine ellipse를 닫고 CE-KOPT는 moving-knot automatic-$C^q$ 기하와 spacing을 닫는다. 기준 사영자·균일 영역이 없는 경우, moving-knot family의 resolvent/rank, defective ellipse, 자료에 따른 목적함수·label 변경, mesh와 similarity의 공동 최적화와 empirical provenance는 여전히 열린 문제다.

#### 네 점을 넘는 exact rational contour mesh

기존 $d_k=i^k$ 네 점은 정리가 요구하는 본질적 수가 아니라, 원 전체를 덮는 가장 단순한 exact mesh였다. 더 촘촘한 mesh를 쓰려면 node 수만 늘리는 것이 아니라 순서·winding·최대 빈틈을 함께 인증해야 한다.

**[정의]** 서로 다른 $d_0,\ldots,d_{N-1}\in\mathbb Q(i)$가 $|d_k|^2=1$, $N\ge3$을 만족하고, 정확히 한 번 반시계방향으로 단위원을 돈다고 하자. 순환하는 이웃마다

$$
c_k=\operatorname{Re}(\overline d_kd_{k+1}),\qquad
s_k=\operatorname{Im}(\overline d_kd_{k+1})
\tag{19zj}
$$

라 하고 $s_k>0$, 또는 $s_k=0,c_k=-1$을 요구한다. 그러면 각 gap $\theta_k$는 $(0,\pi]$에 있다. 같은 점의 중복, 역순, 건너뛴 polar 순서, 원을 여러 번 도는 배열은 거절한다.

**[정리: rational mesh chord]** $d_k$와 $d_{k+1}$ 사이 원호의 한 점이 더 가까운 끝점에서 가장 멀어지는 곳은 중점이다. 그 단위원 거리는

$$
h_k=2\sin\frac{\theta_k}{4}
=\sqrt{2-\sqrt{2+2c_k}}
\tag{19zk}
$$

이다. 안쪽 제곱근에는 lower dyadic bound, 바깥 제곱근에는 upper dyadic bound를 써서 $h_k^+$를 만들고

$$
\chi_{\mathcal M}^+=\widetilde r\max_k h_k^+
\tag{19zl}
$$

라 하자. 각 $z_k=\widetilde c+\widetilde r d_k$에서 기존 componentwise residual 검사가 하한 $\ell_k$를 주고

$$
\delta_{\mathcal M}=\min_k\ell_k-\chi_{\mathcal M}^+>0
\tag{19zm}
$$

이면 전체 원에서 interval family의 resolvent가 존재하고 공통 Riesz rank가 보존된다. 최소특이값의 scalar shift에 대한 1-Lipschitz 성질과 (19zl)을 결합하면 바로 증명된다. □

**[산출]** `verified_rational_mesh_residual.py`는 exact unit·유일성·단일 winding·반시계 순서·$\pi$ 이하 gap을 검사하고, node마다 exact nominal inverse를 만들거나 첫 singular node를 별도 보고한다. 네 cardinal node를 넣으면 기존 node·chord·margin·resolvent·projector 출력과 정확히 일치한다. 반면 $U_0=0$, 반지름 1, scalar uncertainty $1/2$인 같은 상자는 네 점에서 chord 여유가 비양수지만 cardinal과 $(\pm3/5,\pm4/5)$를 합친 정렬된 8점 mesh에서는 양의 여유로 통과한다.

**[후속 정리로 부분 폐쇄 / 미완성: quadrature·자료]** 이 정리는 원형 contour의 배제와 rank 안정성을 유한 rational mesh로 확장한다. 아래 CE-RPOLY가 단순 유리 다각형 Jordan contour를 닫지만, 임의의 매끄러운 Jordan 곡선, 임의 mesh의 projector quadrature, 자료를 보며 하는 adaptive refinement는 아직 아니다. 특히 여기서 node를 늘렸다고 기존 네 점 analytic-strip 사다리꼴 오차식이 자동으로 일반화되지는 않는다.

#### 원을 벗어난 단순 유리 다각형 Jordan contour

원형 mesh의 핵심은 원이 아니라 “contour의 모든 점이 검사 node에서 얼마나 먼가”였다. 이를 일반화해 서로 다른 exact 정점

$$
v_0,\ldots,v_{N-1}\in\mathbb Q(i),\qquad N\ge3,
\tag{19zm-a}
$$

을 순환 연결한다. 정점은 반시계 순서이고 shoelace 부호면적

$$
\mathcal A_2=sum_{k=0}^{N-1}
\operatorname{Im}(\overline v_kv_{k+1})>0
\tag{19zm-b}
$$

이어야 한다. 모든 비인접 변 쌍은 교차하거나 접하지 않아야 한다. 연속한 두 변이 일직선인 것은 같은 방향으로 세분할 때만 허용하고, 되짚기·중복 정점·자기접촉·자기교차·시계방향 배열은 거절한다. 이 exact 조건들이 다각형을 양의 방향의 단순 Jordan contour로 만든다.

변 $e_k=[v_k,v_{k+1}]$의 길이에 대한 dyadic outward upper를 $L_k^+$라 하자. 선분 위 임의의 $z$는 더 가까운 끝점에서 길이의 절반 이내이므로

$$
\min\{|z-v_k|,|z-v_{k+1}|\}\le\frac{L_k^+}{2}.
\tag{19zm-c}
$$

각 정점에서 componentwise residual 인증이 원래 좌표의 최소특이값 하한 $\ell_k$를 준다면 변별 여유는

$$
\delta_k=min(\ell_k,\ell_{k+1})-\frac{L_k^+}{2},
\qquad
\delta_{\rm poly}=\min_k\delta_k.
\tag{19zm-d}
$$

**[정리: rational polygon residual bridge]** 모든 node residual 수축이 엄격하고 $\delta_{\rm poly}>0$이면, 전체 다각형 contour에서 모든 interval-family 행렬의 resolvent가 존재한다. 따라서 $A(t)=A_0+tD$, $0\le t\le1$의 Riesz projector rank는 일정하고, family 전체가 nominal rank를 보존한다.

증명. $z\in e_k$에서 가까운 끝점을 $v_j$라 하면 최소특이값의 scalar shift 1-Lipschitz 성질과 (19zm-c)에서

$$
\sigma_{\min}(zI-A)
\ge \sigma_{\min}(v_jI-A)-|z-v_j|
\ge\delta_k>0.
$$

따라서 contour 전체가 모든 $t$에서 resolvent 집합 안에 있다. Riesz projector는 $t$에 연속이고 유한차원 projector의 rank는 정수이므로 연결구간에서 일정하다. □

정규화된 둘레 상계를 $\mathcal L^+=\sum_kL_k^+$, interval perturbation의 선택된 2-norm 상계를 $D_2^+$라 하자. resolvent 상계가 $R^+=1/\delta_{\rm poly}$이면 resolvent identity와 $\pi>3$에서

$$
\boxed{
\|P(A)-P(A_0)\|_2
\le \frac{\mathcal L^+}{6}D_2^+(R^+)^2
}
\tag{19zm-e}
$$

라는 exact rational-compatible 외향 상계를 얻는다. 이는 nominal projector의 값을 계산하는 quadrature가 아니라, 존재하는 두 exact Riesz projector 사이의 perturbation 상계다.

**[산출·반례]** `verified_rational_polygon_residual.py`는 signed area, 비인접 변 전수 교차 검사, forward collinear refinement, 각 변 길이 bracket, node residual, 변별 margin, 둘레와 projector 상계를 출력한다. scalar uncertainty $1/2$인 같은 정사각형 contour는 네 꼭짓점만 쓰면 half-edge cover가 실패하지만 각 변을 네 구간으로 exact 세분한 16점 contour는 통과한다. 반대로 bow-tie, 비인접 접촉, 시계방향, collinear backtracking과 margin 등호는 모두 fail-closed다. 이 정리는 공급된 polygon을 인증할 뿐 최적 contour 발견이나 empirical matrix를 제공하지 않는다. 다음 정리가 frozen midpoint subdivision에 한해 nominal projector quadrature와 rank 숫자를 추가한다.

#### 다각형 midpoint Riesz quadrature와 nominal rank 숫자

양의 방향 polygon $Gamma$와 nominal 행렬 $A_0$에 대해 스케일을 먼저 정규화하고

$$
K:=-i\oint_\Gamma(zI-A_0)^{-1},dz=2\pi P_\Gamma(A_0)
\tag{19zm-f}
$$

라 하자. 변 $h_k=v_{k+1}-v_k$를 사전고정한 양의 정수 $m_k$개로 나누고 합성 midpoint를 쓰면 exact $mathbb Q(i)$ 행렬

$$
K_m=-i\sum_k\frac{h_k}{m_k}
\sum_{j=0}^{m_k-1}
\left[left(v_k+\frac{2j+1}{2m_k}h_k\right)I-A_0\right]^{-1}
\tag{19zm-g}
$$

을 얻는다. 앞 정리의 변별 margin을 $delta_k>0$, $R_k^+=1/\delta_k$라 하고 변 길이 upper를 $L_k^+$라 하자.

**[정리: composite midpoint error]**

$$
\boxed{
\|K-K_m\|_2
\le E_K^+:=
\sum_k\frac{(L_k^+)^3(R_k^+)^3}{12m_k^2}
}
\tag{19zm-h}
$$

이다. 실제로 한 변을 $z(t)=v_k+th_k$로 쓰면 적분함수 $-ih_kR(z(t))$의 이차미분은 norm에서 $2|h_k|^3\|R(z(t))\|^3$ 이하이고, 합성 midpoint 오차 $\sup\|f''\|/(24m_k^2)$를 적용하면 각 항이 나온다. □

$\pi$를 host float 상수로 넣지 않기 위해 Machin 항등식

$$
\frac\pi4=4\arctan\frac15-\arctan\frac1{239}
\tag{19zm-i}
$$

과 $\arctan x$의 교대급수 연속 부분합을 사용해 exact rational bracket $\pi^-<\pi<\pi^+$를 만든다. 이 bracket은 $3<\pi^-<\pi^+<22/7$도 exact 비교로 자체 검사한다.

nominal rank를 $r$라 하면 $\operatorname{tr}K=2\pi r$이고

$$
|\operatorname{tr}K_m-2\pi r|\le nE_K^+.
\tag{19zm-j}
$$

따라서 각 정수 $q\in\{0,\ldots,n\}$에 대해 complex 수 $\operatorname{tr}K_m$와 실수구간 $[2\pi^-q,2\pi^+q]$ 사이의 정확한 제곱거리가 $(nE_K^+)^2$ 이하인지 검사한다.

**[정리: verified polygon rank extraction]** 가능한 정수 집합이 정확히 ${r}$ 하나이면 nominal Riesz rank는 $r$이고, 앞의 interval-family rank 보존 정리와 결합해 family 전체 rank도 $r$이다. 가능한 값이 둘 이상이면 subdivision 순서나 자료를 보고 하나를 고르지 않고 `UNRESOLVED`로 남긴다. 실제 rank는 외향 오차 때문에 가능한 집합에 반드시 포함되므로 빈 집합은 구현 불변식 위반이다. □

또한

$$
s^-=(2\pi^+)^{-1},\qquad s^+=(2\pi^-)^{-1},
\qquad \bar s=\frac{s^-+s^+}{2}
\tag{19zm-k}
$$

라 하고 $\|K_m\|_2\le M_K^+$를 outward Frobenius bound로 잡으면

$$
\boxed{
\|P_\Gamma(A_0)-\bar sK_m\|_2
\le s^+E_K^++\frac{s^+-s^-}{2}M_K^+
}
\tag{19zm-l}
$$

이므로 projector 근사행렬 자체에도 검증 오차가 붙는다.

**[산출·경계]** `verified_polygon_riesz_quadrature.py`는 Machin bracket, 모든 exact midpoint inverse 양방향 항등식, 변별 오차, $K_m$, scaled projector와 그 오차, 가능한 rank 집합을 출력한다. 정사각형에서 scalar inside/outside rank 1/0과 diagonal $2\times2$ rank 1을 고유하게 복원하고, $m_k=1$인 coarse fixture는 여러 rank를 남겨 거절한다. frozen refinement에서는 (19zm-h)가 정확히 $m^{-2}$로 줄어든다. 이는 supplied subdivision의 verified quadrature이지 실제 뇌 rank 결과가 아니다. 아래 정리는 polygon geometry를 고정한 채 subdivision만 결정론적으로 늘리는 제한된 adaptive 경로를 닫는다.

#### 검증 오차만 보는 결정론적 adaptive subdivision

초기 panel 수 $m_k^{(0)}\in\mathbb N$, 배수 $a\ge2$, 최대 refinement 횟수 $B\ge0$를 자료를 보기 전에 고정한다. 라운드 $t$의 변별 quadrature 오차를

$$
e_k^{(t)}=\frac{(L_k^+)^3(R_k^+)^3}{12(m_k^{(t)})^2}
\tag{19zm-m}
$$

라 하자. 허용 전략은 두 가지다.

$$
I_t={0,\ldots,N-1\}
\quad\text{(UNIFORM)},
\tag{19zm-n}
$$

또는

$$
I_t=\operatorname*{argmax}_k e_k^{(t)}
\quad\text{(MAX\_ERROR\_TIES)}.
\tag{19zm-o}
$$

정확한 동률은 모두 함께 선택하고

$$
m_k^{(t+1)}=
\begin{cases}
a,m_k^{(t)},&k\in I_t,\\
m_k^{(t)},&k\notin I_t
\end{cases}
\tag{19zm-p}
$$

로 갱신한다. 각 라운드는 앞 절의 전체 exact quadrature와 가능한 rank 집합을 새로 계산한다.

**[정리: deterministic verified refinement]** 어떤 라운드 $t\le B$에서 가능한 rank 집합이 singleton이면 그 rank는 앞 절의 정리에 따라 nominal/family rank다. $B$까지 singleton이 아니면 결과는 `REFINEMENT_EXHAUSTED`이며 rank를 내지 않는다. UNIFORM에서는 모든 $e_k$가 refinement마다 $a^{-2}$배가 된다. MAX_ERROR_TIES도 현재 최대오차의 모든 exact tie를 갱신하므로 어느 한 변을 영원히 무시하지 않고 최대오차를 0으로 보낸다. 따라서 무제한 수열에서는 Machin rank 구간들이 실제 rank 주변에서 분리된다는 추가 조건 아래 결국 singleton에 도달한다. 유한 구현은 이 점근 결론을 완료로 가장하지 않고 $B$를 엄격히 지킨다. □

**[산출·반례]** `verified_adaptive_polygon_riesz.py`는 매 라운드의 subdivision vector, 변별 오차, 가능한 rank, 선택된 모든 tie edge와 최종 exhaustion 여부를 보존한다. 초기 $m=1$의 모호한 정사각형은 uniform doubling으로 rank 1에 도달하고, $B=0$이면 그대로 실패한다. 비대칭 초기 vector에서는 최대오차 변만 먼저 두 배가 되며, 같은 입력은 byte-level dataclass 결과가 동일하다. polygon 정점, interval box, 전략, 배수, budget는 실행 중 바뀌지 않는다. 따라서 이는 검증 오차 기반 수치 refinement이지 자료를 본 contour 재설계나 empirical dimension 선택이 아니다.

#### 매끄러운 비다각형 부분류: rational affine ellipse

원형을 벗어나면서도 단순성·방향·전역 cover를 exact하게 유지하는 첫 smooth 부분류로 단위원의 affine image를 둔다. 정규화된 complex 평면에서

$$
\gamma(u)=c+a u_1+b u_2,
\qquad u_1^2+u_2^2=1,
\tag{19zm-q}
$$

이며 $a,b\in\mathbb Q(i)$를 실수 $2\times2$ 축행렬 $L=[a\ b]$의 열로 본다. 방향 determinant

$$
d=\det L=\operatorname{Re}(a)\operatorname{Im}(b)
-\operatorname{Im}(a)\operatorname{Re}(b)>0
\tag{19zm-r}
$$

를 요구한다. 그러면 $L$은 가역이고 $gamma$는 단위원의 smooth injective image이므로 양의 방향의 매끄러운 Jordan ellipse다. $d=0$은 퇴화 선분이고 $d<0$은 역방향이므로 거절한다.

축행렬의 정확한 spectral norm은 $L^TL$의 큰 고유값으로 정한다. 즉

$$
\tau=|a|^2+|b|^2,
\qquad
\Delta_L=\tau^2-4d^2\ge0,
\tag{19zm-s}
$$

$$
\lambda_+=\frac{\tau+\sqrt{\Delta_L}}2,
\qquad
\|L\|_2=\sqrt{\lambda_+}.
\tag{19zm-t}
$$

중첩 제곱근에 dyadic outward enclosure를 적용해 $\|L\|_2\le S_L^+$를 얻는다. 앞의 rational unit mesh가 단위원의 모든 점을 가까운 node에서 $h_{\max}^+$ 이내로 덮으면

$$
\boxed{
\chi_E^+=S_L^+h_{\max}^+
}
\tag{19zm-u}
$$

가 ellipse 전체의 node cover다.

**[정리: rational affine-ellipse residual bridge]** 각 mapped node $z_k=c+a\operatorname{Re}d_k+b\operatorname{Im}d_k$에서 interval residual 하한 $\ell_k$가 있고

$$
\delta_E=\min_k\ell_k-\chi_E^+>0
\tag{19zm-v}
$$

이면 ellipse 전체가 interval family의 resolvent 집합에 있으며 nominal Riesz rank가 family 전체에서 보존된다. 증명은 $|\gamma(u)-\gamma(d_k)|\le\|L\|_2|u-d_k|$와 최소특이값의 1-Lipschitz 성질을 결합하면 된다. □

ellipse 길이에는

$$
\mathcal L_E
=\int_0^{2\pi}\|L(-\sin\theta,\cos\theta)\|,d\theta
\le2\pi S_L^+
\tag{19zm-w}
$$

가 성립하므로, 선택된 matrix uncertainty $D_2^+$와 $R_E^+=1/\delta_E$에 대해

$$
\boxed{
\|P_E(A)-P_E(A_0)\|_2
\le S_L^+D_2^+(R_E^+)^2
}
\tag{19zm-x}
$$

도 얻는다.

**[환원·반례·산출]** $a=r$, $b=ir$이면 $S_L^+=r$이고 기존 circle node·chord·margin·projector bound로 정확히 환원된다. $a=2,b=i$인 ellipse는 네 cardinal node에서 cover가 실패하지만 rational 8-node mesh에서 통과한다. 회전축 $a=1+i,b=-1+i$는 중복 고유값 $\lambda_+=2$를 exact enclosure로 처리한다. `verified_rational_ellipse_residual.py`는 determinant, Gram discriminant, 축 norm bracket, mapped nodes, smooth cover, residual과 projector bound를 모두 출력한다. 이 정리는 rational affine ellipse 부분류만 닫으며 임의 smooth spline, contour 위치 최적화, empirical rank를 주장하지 않는다. 다음 bridge가 ellipse와 inscribed polygon의 sector 전체를 같은 cover로 묶어 앞의 polygon quadrature rank를 ellipse로 옮긴다.

#### ellipse–inscribed polygon homotopy와 smooth rank 숫자

unit mesh의 이웃 $d_k,d_{k+1}$ 사이 gap을 $\theta_k\le\pi$라 하고, $t\in[0,1]$에서 단위원 원호와 chord를

$$
u_{\rm arc}(t)=e^{i[(1-t)\phi_k+t\phi_{k+1}]},
\qquad
u_{\rm lin}(t)=(1-t)d_k+td_{k+1}
\tag{19zm-y}
$$

로 쓴다. 실제 계산에는 각도나 지수함수를 넣지 않고 이 식은 증명에만 사용한다. sector homotopy는

$$
u_s(t)=(1-s)u_{\rm arc}(t)+s u_{\rm lin}(t),
\qquad 0\le s\le1
\tag{19zm-z}
$$

이다. $t\le1/2$이면 endpoint $d_k$, $t\ge1/2$이면 $d_{k+1}$를 택한다. 원호점은 정의상 $h_k$ 이내이고 chord점은

$$
\min(t,1-t)|d_{k+1}-d_k|
\le\sin\frac{\theta_k}{2}
\le2\sin\frac{\theta_k}{4}=h_k
\tag{19zm-aa}
$$

이내다. norm의 convexity 때문에 모든 $u_s(t)$도 같은 endpoint에서 $h_k$ 이내다. affine 축행렬을 적용하면 sector 전체가 mapped node에서 $S_L^+h_k^+$ 이내다.

**[정리: ellipse–polygon contour homotopy]** CE-ELL의 margin $\delta_E>0$가 성립하면 ellipse와 mapped inscribed polygon 사이의 모든 homotopy contour가 interval family의 resolvent 집합 안에 있다. 따라서 두 contour의 winding-weighted Riesz projector는 같고 rank도 같다.

증명. 각 homotopy 점의 node 거리에는 (19zm-aa)와 affine norm bound를 적용한다. node residual lower에서 그 거리를 빼도 $\delta_E>0$이므로 모든 $s,t$에서 resolvent가 존재한다. contour integral은 resolvent 영역 안의 homotopy에 불변이므로 양 끝의 projector가 같다. 중간 contour의 단순성은 필요하지 않으며, 시작 ellipse와 끝 inscribed polygon은 각각 양의 단순 contour다. □

**[정리: verified smooth ellipse rank extraction]** mapped rational nodes를 inscribed polygon의 정점으로 넣고 CE-APREF/CE-PQUAD가 유일한 rank $r$과 projector 근사 $\widehat P$ 및 오차 $E_P^+$를 내면, smooth ellipse의 nominal rank와 interval-family rank도 $r$이고

$$
\|P_E(A_0)-\widehat P\|_2\le E_P^+
\tag{19zm-ab}
$$

이다. polygon refinement budget이 소진되면 ellipse residual과 sector homotopy는 통과했더라도 rank 숫자와 projector 근사는 내지 않는다. □

**[산출·경계]** `verified_ellipse_polygon_rank_bridge.py`는 ellipse exact witness, smooth residual, raw inscribed vertices, sector cover/margin, 모든 adaptive polygon round, smooth rank와 projector error를 한 receipt로 묶는다. anisotropic ellipse의 inside/outside scalar rank 1/0, nonzero interval family 상속, $B=0$ unresolved, cardinal mesh cover 실패, singular ellipse node, raw-scale covariance를 분리 검증한다. geometry는 자료에 따라 움직이지 않으며, 이 bridge는 general spline quadrature나 empirical rank가 아니다.

#### ellipse를 넘는 smooth 비선형 부분류: 양의 affine-linear radial contour

smooth contour를 더 넓히기 위해 단위원 방향 $u=(u_1,u_2)$에 양의 radial 함수

$$
\rho(u)=r_0+p_1u_1+p_2u_2,
\qquad
p_*:=\sqrt{p_1^2+p_2^2}
\tag{19zm-ac}
$$

를 곱한다. exact rational 계수에 대해 nested dyadic upper $p_*^+$를 만들고

$$
\boxed{r_0-p_*^+>0}
\tag{19zm-ad}
$$

를 요구한다. contour는

$$
\gamma(u)=c+L[\rho(u)u],
\qquad |u|=1,qquad \det L>0
\tag{19zm-ae}
$$

이다. 양의 $\rho$ 때문에 서로 다른 polar 방향은 같은 점이 될 수 없고, 각도미분은 affine 이전에

$$
\frac{d}{d\theta}[\rho(u)u]
=\rho'(u)u+\rho(u)u_\perp,
\tag{19zm-af}
$$

이며 두 항은 직교하고 $\rho>0$이므로 0이 아니다. 가역인 $L$을 적용해도 injectivity와 regularity가 유지되어 양의 smooth star-shaped Jordan contour가 된다.

전역 cover에는 단위원 disk까지 확장한

$$
F(u)=\rho(u)u,
\qquad
DF(u)=\rho(u)I+u(p_1,p_2)
\tag{19zm-ag}
$$

를 쓴다. $|u|\le1$에서

$$
\|DF(u)\|_2
\le r_0+p_*^++p_*^+
=:C_\rho^+=r_0+2p_*^+.
\tag{19zm-ah}
$$

따라서 축 norm $S_L^+$와 unit-mesh chord $h_{\max}^+$를 합쳐

$$
\boxed{
\chi_R^+=S_L^+C_\rho^+h_{\max}^+
}
\tag{19zm-ai}
$$

를 얻는다.

**[정리: rational affine-radial residual bridge]** mapped node에서 residual 하한 $\ell_k$가 있고

$$
\delta_R=\min_k\ell_k-\chi_R^+>0
\tag{19zm-aj}
$$

이면 smooth radial contour 전체가 interval family의 resolvent 집합 안에 있고 nominal Riesz rank가 family 전체에서 보존된다. 또한 각도 방향 속도가 $S_L^+C_\rho^+$ 이하이므로 contour 길이는 $2\pi S_L^+C_\rho^+$ 이하이고

$$
\boxed{
\|P_R(A)-P_R(A_0)\|_2
\le S_L^+C_\rho^+D_2^+(1/\delta_R)^2
}
\tag{19zm-ak}
$$

이다. □

**[환원·반례·산출]** $p_1=p_2=0$이면 $\rho=r_0$이고 축 $r_0L$의 affine ellipse로 node·cover·margin이 정확히 환원된다. $r_0=1,p_1=1/4,p_2=0$인 진짜 비ellipse contour는 rational 8-node mesh에서 통과하지만 네 cardinal node에서는 cover가 실패한다. $r_0=p_*$ 경계, $r_0=0$, 역방향/퇴화 affine 축은 모두 거절한다. `verified_rational_radial_contour_residual.py`는 positivity margin, radial norm, $C_\rho^+$, mapped nodes, smooth cover, rank와 projector bound를 산출한다. 이는 affine-linear radial 함수 부분류이며 일반 고차 spline이나 자료 기반 contour 선택은 아니다.

#### nonlinear radial contour에서 polygon numeric rank로

인접 mesh 방향을 $u_0,u_1$, 그 사이의 원호를 $u(t)$, $0\le t\le1$이라 하고 간격은 $\theta\le\pi$라 하자. affine 이전의 radial map을 $F(u)=\rho(u)u$라 두면 inscribed chord와 smooth arc 사이의 homotopy는

$$
H_s(t)=(1-s)F(u(t))+s\{(1-t)F(u_0)+tF(u_1)\},
\qquad 0\le s\le1
\tag{19zm-al}
$$

이다. $t\le1/2$이면 $u_0$를, $t\ge1/2$이면 $u_1$을 가까운 endpoint로 잡는다. $h=2\sin(\theta/4)$와 $C_\rho^+=r_0+2p_*^+$에 대해 smooth 항은 Lipschitz 정리로, chord 항은 convexity와 endpoint 차이로 각각

$$
\|F(u(t))-F(u_e)\|_2\le C_\rho^+h,
\qquad
\|(1-t)F(u_0)+tF(u_1)-F(u_e)\|_2\le C_\rho^+h
\tag{19zm-am}
$$

를 만족한다. 따라서 모든 $s,t$에서 affine image는 같은 node로부터

$$
\boxed{\|L H_s(t)-L F(u_e)\|_2\le S_L^+C_\rho^+h}
\tag{19zm-an}
$$

안에 있다. 양의 radial vertex를 각도 순서로 잇고 각 gap을 $\pi$ 이하로 제한하면 각 edge는 자기 angular sector 안에 있으므로 polygon은 simple Jordan contour이고, orientation-preserving affine map은 이 성질을 보존한다.

**[정리: radial-to-polygon rank bridge]** (19zm-aj)의 양의 smooth residual margin이 있으면 (19zm-al)의 모든 중간 contour가 interval family의 resolvent 집합에 남는다. 따라서 smooth radial contour와 inscribed polygon의 Riesz projector 및 rank가 같다. polygon adaptive midpoint quadrature가 유일한 integer rank $d$와 projector 오차 $E_P^+$를 내면

$$
\boxed{\operatorname{rank}P_R(A)=d,
\qquad \|P_R(A_0)-\widehat P_{\rm poly}\|_2\le E_P^+}
\tag{19zm-ao}
$$

가 nominal matrix와 인증된 interval family에 함께 성립한다. refinement budget이 소진되면 homotopy가 통과했더라도 numeric rank와 projector 근사는 출력하지 않는다. □

**[산출·경계]** `verified_radial_polygon_rank_bridge.py`는 genuine nonellipse rank 1, outside rank 0, interval 상속, projector enclosure, coarse cover 실패, singular node, zero-budget 미결정, raw-scale covariance를 분리 검증한다. 이는 supplied affine-linear radial family의 numeric bridge이며 고차 radial polynomial/spline, 자동 contour 선택, 실뇌 rank는 아니다.

#### 임의 유한 차수의 positive polynomial radial contour

1차 radial 함수에 머물 필요는 없다. multi-index $\alpha=(\alpha_1,\alpha_2)$, $|\alpha|=\alpha_1+\alpha_2$에 대해 exact rational 유한 다항식을

$$
\rho(u)=r_0+p\cdot u+
\sum_{2\le|\alpha|\le m}a_\alpha u_1^{\alpha_1}u_2^{\alpha_2}
\tag{19zm-ap}
$$

로 둔다. 고차항의 amplitude와 gradient를

$$
A_0=\sum_{|\alpha|\ge2}|a_\alpha|,
\qquad
A_1=\sum_{|\alpha|\ge2}|a_\alpha||\alpha|
\tag{19zm-aq}
$$

로 감싼다. $|u_1|,|u_2|\le1$이므로 각 monomial의 절댓값은 1 이하이고, 그 gradient의 Euclidean norm은 보수적으로 $|\alpha|$ 이하이다. 따라서 outward $p_*^+\ge\|p\|_2$에 대해

$$
\boxed{m_\rho^+=r_0-p_*^+-A_0>0}
\tag{19zm-ar}
$$

이면 closed unit disk와 unit circle에서 $\rho>0$이다. polar 방향별 유일성과

$$
\frac{d}{d\theta}[\rho(u)u]=\rho'(u)u+\rho(u)u_\perp
\tag{19zm-as}
$$

의 직교 분해는 차수와 무관하므로 injective regular smooth Jordan 성질이 그대로 성립한다.

또한 $F(u)=\rho(u)u$에 대해 $DF=\rho I+u(\nabla\rho)^T$이고

$$
\boxed{
C_{\rm poly}^+
=r_0+2p_*^++A_0+A_1
}
\tag{19zm-at}
$$

가 disk 전체의 Lipschitz 상계다. 첫 $r_0+p_*^++A_0$는 $|\rho|$를, 나머지 $p_*^++A_1$은 $\|\nabla\rho\|_2$를 감싼다. 따라서

$$
\chi_{\rm poly}^+=S_L^+C_{\rm poly}^+h_{\max}^+,
\qquad
\delta_{\rm poly}=\min_k\ell_k-\chi_{\rm poly}^+>0
\tag{19zm-au}
$$

이면 전체 polynomial radial contour와 interval family의 rank가 인증되고

$$
\|P_{\rm poly}(A)-P_{\rm poly}(A_0)\|_2
\le S_L^+C_{\rm poly}^+D_2^+(1/\delta_{\rm poly})^2
\tag{19zm-av}
$$

이다. 앞 절의 sector homotopy 증명은 radial 함수의 차수가 아니라 positivity와 disk Lipschitz 상계만 사용하므로 그대로 적용된다. 따라서 adaptive polygon quadrature의 유일 integer rank와 projector error도 이 smooth 고차 contour로 이전된다. □

**[환원·반례·산출]** 고차 계수가 0이면 $A_0=A_1=0$이고 (19zm-at)는 기존 affine-linear $r_0+2p_*^+$와 정확히 일치한다. 반면 $r_0=p_*^++A_0$ 등호는 통과시키지 않는다. 같은 monomial이 반복 입력되면 exact rational로 합치고 0 계수는 제거하며, 음수 지수·상수항의 중복 표현·비정수 지수는 거절한다. `verified_polynomial_radial_contour_residual.py`와 `verified_polynomial_radial_polygon_rank_bridge.py`는 quadratic genuine contour, 1차 exact reduction, duplicate normalization, coarse-cover failure, singular node, interval/scale covariance, ranks 0/1, projector enclosure와 budget exhaustion을 검증한다.

#### periodic piecewise-polynomial radial $C^q$ spline

전역 다항식 하나로 충분하지 않으면 ordered rational 방향 $u_0,\dots,u_{N-1}$이 정하는 각 sector마다 서로 다른 exact polynomial $\rho_k(u)$를 둔다. 단순한 node 값 일치만으로는 smooth spline이 아니다. 원 위의 각도미분 연산자

$$
\boxed{
T=-u_2\frac{\partial}{\partial u_1}
+u_1\frac{\partial}{\partial u_2}
}
\tag{19zm-aw}
$$

를 쓰고, 주기적 knot $u_k$에서

$$
\boxed{
(T^j\rho_{k-1})(u_k)=(T^j\rho_k)(u_k),
\qquad j=0,1,\dots,q
}
\tag{19zm-ax}
$$

를 exact rational equality로 요구한다. $T$는 polynomial을 polynomial로 보내므로 이 검사는 유한 exact 연산이다. $q\ge1$이면 radial 함수는 원 위에서 periodic $C^q$이고, positive radial 조건과 결합해 contour는 적어도 $C^1$ regular Jordan curve다. $C^1$까지만 맞는 patch를 $C^2$로 선언하면 (19zm-ax)의 $j=2$에서 거절된다.

각 patch를 linear 부분 $p_k$와 degree 2 이상 계수로 나누고

$$
A_{0,k}=\sum_{|\alpha|\ge2}|a_{k,\alpha}|,
\qquad
A_{1,k}=\sum_{|\alpha|\ge2}|a_{k,\alpha}||\alpha|
\tag{19zm-ay}
$$

라 하자. 모든 $k$에 대해

$$
r_{0,k}-\|p_k\|_2^+-A_{0,k}>0
\tag{19zm-az}
$$

를 요구하고

$$
C_{\rm spl}^+=
\max_k\{r_{0,k}+2\|p_k\|_2^++A_{0,k}+A_{1,k}\}
\tag{19zm-ba}
$$

를 택하면 모든 sector의 disk Lipschitz 상계를 동시에 지배한다. 따라서

$$
\chi_{\rm spl}^+=S_L^+C_{\rm spl}^+h_{\max}^+,
\qquad
\delta_{\rm spl}=\min_k\ell_k-\chi_{\rm spl}^+>0
\tag{19zm-bb}
$$

이면 piecewise-polynomial radial $C^q$ contour 전체와 interval family rank가 인증된다. 길이 상계와 projector perturbation은 $C_{\rm poly}^+$ 대신 $C_{\rm spl}^+$를 넣은 (19zm-av)이고, sector별 arc-to-chord homotopy도 같은 cover 안에 있으므로 polygon numeric rank와 projector error가 그대로 이전된다. □

**[구성·반례·산출]** sector endpoints $u_k,u_{k+1}$에 대해

$$
\rho_k(u)=1+\varepsilon_k(1-u\cdot u_k)(1-u\cdot u_{k+1})
\tag{19zm-bc}
$$

는 patch마다 서로 다르지만 양 endpoint에서 값 1, 첫 각도미분 0이므로 genuine periodic $C^1$ quadratic spline fixture를 준다. 서로 다른 $\varepsilon_k$에서는 일반적으로 둘째 미분이 달라 false $C^2$ 승격을 막는다. `verified_piecewise_polynomial_radial_contour_residual.py`와 `verified_piecewise_polynomial_radial_polygon_rank_bridge.py`는 모든 knot의 $T^j$ 값·self-check, patch positivity와 최대 Lipschitz, residual, homotopy, numeric rank/projector를 한 receipt로 연결한다. 이는 polynomial spline이며 분모가 있는 rational spline이나 자료에서 knot를 고르는 최적화는 아니다.

#### pole-free piecewise-rational radial $C^q$ spline

분모가 있는 patch는

$$
\rho_k(u)=\frac{N_k(u)}{D_k(u)}
\tag{19zm-bd}
$$

로 둔다. knot에서 $D_k(u_k)\ne0$인 것만으로는 patch 내부의 pole을 막지 못한다. numerator와 denominator의 coefficient-sum 영수증을 각각

$$
0<N_k^-\le N_k(u)\le N_k^+,
\qquad
0<D_k^-\le D_k(u)\le D_k^+
\tag{19zm-be}
$$

로 만들고, disk 전체 gradient 상계를 $G_{N,k}^+,G_{D,k}^+$라 한다. 그러면 pole이 전역 배제되고

$$
\frac{N_k^-}{D_k^+}\le\rho_k(u)\le\frac{N_k^+}{D_k^-}
\tag{19zm-bf}
$$

이며 quotient rule로

$$
\|\nabla\rho_k(u)\|_2
\le
\frac{G_{N,k}^+}{D_k^-}
+\frac{N_k^+G_{D,k}^+}{(D_k^-)^2}
\tag{19zm-bg}
$$

이다. 따라서 patch Lipschitz 상계는

$$
C_{{\rm rat},k}^+
=\frac{N_k^+}{D_k^-}
+\frac{G_{N,k}^+}{D_k^-}
+\frac{N_k^+G_{D,k}^+}{(D_k^-)^2},
\qquad
C_{\rm rat}^+=\max_k C_{{\rm rat},k}^+
\tag{19zm-bh}
$$

이다.

junction에서는 quotient를 symbolic expansion으로 폭발시키지 않는다. $N_{k,j}=(T^jN_k)(u)$, $D_{k,j}=(T^jD_k)(u)$라 하면 $N_k=D_k\rho_k$의 Leibniz 식에서 quotient jet은 exact recurrence

$$
\boxed{
\rho_{k,n}
=\frac{N_{k,n}-\sum_{j=1}^n{n\choose j}D_{k,j}\rho_{k,n-j}}
{D_{k,0}}
}
\tag{19zm-bi}
$$

로 계산된다. 각 knot에서 좌우 $\rho_{k,n}$을 $0\le n\le q$까지 exact 비교하면 periodic rational $C^q$ compatibility가 성립한다. $q\ge1$, (19zm-be), 양의 numerator와 orientation-preserving $L$ 아래 contour는 positive regular Jordan curve다.

마지막으로

$$
\chi_{\rm rat}^+=S_L^+C_{\rm rat}^+h_{\max}^+,
\qquad
\delta_{\rm rat}=\min_k\ell_k-\chi_{\rm rat}^+>0
\tag{19zm-bj}
$$

이면 family residual/rank와 projector perturbation이 성립하고, patchwise sector homotopy가 polygon numeric rank/projector error를 rational spline으로 이전한다. $D_k\equiv1$이면 bound·node·junction jet·residual은 piecewise-polynomial 경로로 정확히 환원된다. □

**[구성·반례·산출]** (19zm-bc)의 bump를 $b_k$라 하고 $D_k=1+d_kb_k$, $N_k=D_k+e_kb_k$로 두면 분모가 실제로 변하는 genuine rational $C^1$ fixture이면서 endpoints에서 quotient 값 1과 첫 jet 0을 공유한다. $D_k^-=0$ 등호, numerator positivity 등호, quotient value/derivative 불일치, false $C^2$, singular knot, cover 실패, budget exhaustion은 모두 분리 거절한다. `verified_piecewise_rational_radial_contour_residual.py`와 `verified_piecewise_rational_radial_polygon_rank_bridge.py`는 denominator pole margin, quotient jets, global Lipschitz, residual/homotopy/rank/projector를 기록한다.

#### 사전고정 유한 contour menu의 누출 없는 선택

형상 후보가 여러 개라면 검증 margin이 가장 큰 contour를 사후적으로 고르고 같은 자료에서 성능을 보고해서는 안 된다. 후보 ID, normalized rational geometry, patch, knot, $q$와 mesh를 canonical hash로 동결한

$$
\mathcal M=\{\Gamma_1,\dots,\Gamma_J\},
\qquad J\ge2
\tag{19zm-bk}
$$

를 먼저 만든다. development matrix/family에서 후보 $j$가 residual·homotopy·numeric-rank gate를 모두 통과하면

$$
s_j=\delta_j^{\rm dev}>0
\tag{19zm-bl}
$$

를 점수로 주고, 실패하면 eligibility를 주지 않는다. 유일 winner $j_*$와 유일 runner-up $j_{(2)}$에 대해 사전고정 advantage $\eta\ge0$를 사용해

$$
\boxed{s_{j_*}-s_{j_{(2)}}>\eta}
\tag{19zm-bm}
$$

를 요구한다. tie와 등호는 ID 순서로 깨지 않고 실패다.

heldout에서는 $j_*$ 하나만 다시 계산한다. alternatives를 heldout에서 열어보지 않고

$$
\delta_{j_*}^{\rm hold}>0,
\qquad
d_{j_*}^{\rm hold}=d_{j_*}^{\rm dev}
\tag{19zm-bn}
$$

를 모두 요구한다. 첫 조건은 contour certificate의 재현, 둘째는 격리한 spectral bundle의 rank 일관성이다. heldout contour가 안전해도 rank가 달라지면 확인 실패다. □

**[산출·경계]** `predeclared_rational_contour_selection.py`는 canonical menu hash, 모든 development certificate/score, winner/runner/advantage, selected-only heldout certificate, rank consistency와 `heldout_alternative_candidates_evaluated=False`를 산출한다. exact duplicate geometry, winner/runner tie, advantage equality, no eligible candidate, heldout singularity, heldout rank mismatch, forged menu와 dimension mismatch를 거절한다. 이 모듈 자체는 동결된 유한 menu의 조건부 선택이다. 아래 CE-COPT/CE-CAOPT가 연속 circle box를, CE-EOPT/CE-SEOPT/CE-GAOPT가 compact diagonalized general-affine ellipse box를 별도로 닫지만, adaptive spline knot 생성과 실측 자료의 독립성 자체는 증명하지 않는다.

정식 affine-linear residual 기록은 `_workspace/ce/brain-rational-radial-contour-residual-20260826/40-final-report.md`, affine-linear rank 이전은 `_workspace/ce/brain-radial-polygon-rank-bridge-20260826/40-final-report.md`, finite global polynomial 확장은 `_workspace/ce/brain-polynomial-radial-rank-bridge-20260826/40-final-report.md`, periodic piecewise-polynomial $C^q$ 확장은 `_workspace/ce/brain-piecewise-polynomial-radial-spline-20260826/40-final-report.md`, pole-free piecewise-rational $C^q$ 확장은 `_workspace/ce/brain-piecewise-rational-radial-spline-20260826/40-final-report.md`, finite menu 선택은 `_workspace/ce/brain-predeclared-rational-contour-selection-20260826/40-final-report.md`를 따른다.

#### 대각화 없이 exact Riesz projector를 확인하는 대수적 witness

정확한 고유벡터 행렬 $V$를 요구하면 Jordan block과 비유리 고유값을 가진 유리행렬이 빠진다. projector 자체와 invariant split을 직접 검사하면 이 제한을 피할 수 있다.

**[정리: algebraic Riesz projector]** $U\in\mathbb Q(i)^{n\times n}$, 중심 $c$, 반지름 $r>0$에 대해 exact 행렬 $P$가

$$
P^2=P,\qquad PU=UP,\qquad Q=I-P
\tag{19zn}
$$

를 만족한다고 하자. $A=U-cI$라 하고 inside gate

$$
\|AP\|_2^+<r
\tag{19zo}
$$

를 요구한다. 또 정규화 좌표의 exact $R$가

$$
R=RQ=QR=QRQ,\qquad RAQ=Q,\qquad AR=Q
\tag{19zp}
$$

를 만족하고

$$
r\|R\|_2^+<1
\tag{19zq}
$$

이라고 하자. 그러면 $P$의 range에 제한한 $A$의 스펙트럼은 (19zo)에 의해 원 안에 있고, $Q$-부분공간에서 $R=A^{-1}$이므로 (19zq)에 의해 나머지 스펙트럼은 원 밖에 있다. 따라서 원의 exact Riesz projector는 $P$이며 rank는 정수 $\operatorname{tr}P$다. 이 증명은 invariant direct sum에 대한 spectral radius bound만 쓰므로 대각화 가능성이나 고유값의 유리성을 요구하지 않는다. □

$\|AP\|_2^+$와 $\|R\|_2^+$는 각 성분 크기의 outward enclosure에서 Frobenius 상계와 $\sqrt{\|C\|_1\|C\|_\infty}$를 모두 계산해 작은 쪽을 쓴다. 등호는 두 gate 모두 실패다.

**[산출]** `verified_algebraic_riesz_projector.py`는 idempotence, 두 commutator, complement support, 양방향 inverse identity, exact trace/rank, 두 norm과 strict margin을 기록한다. 원 안의 $2\times2$ nilpotent Jordan block과 바깥 고유값 4는 반지름 2에서 통과한다. 또 $\begin{pmatrix}0&2\\1&0\end{pmatrix}$의 고유값은 $\pm\sqrt2$로 비유리지만, 고유값을 입력하지 않고 반지름 3의 inside block으로 인증된다.

#### coprime spectral factor에서 exact projector를 자동 구성

공급된 $P,R$ 검증에서 한 단계 더 나아갈 수 있다. normalized transition $U$에 대해 monic rational polynomial $f_{\rm in},f_{\rm out}$이

$$
f_{\rm in}(U)f_{\rm out}(U)=0,
\qquad
\gcd(f_{\rm in},f_{\rm out})=1
\tag{19zq-a}
$$

을 만족한다고 하자. extended Euclidean algorithm이 exact rational polynomial $a,b$를 찾아

$$
a(z)f_{\rm in}(z)+b(z)f_{\rm out}(z)=1
\tag{19zq-b}
$$

을 준다. 그러면 inside factor의 primary component로 가는 projector는 입력받지 않고

$$
\boxed{P=b(U)f_{\rm out}(U)},
\qquad Q=I-P
\tag{19zq-c}
$$

로 구성된다. 실제로 $\ker f_{\rm in}(U)$에서는 (19zq-b)에 의해 $P=I$이고 $\ker f_{\rm out}(U)$에서는 $P=0$이다. coprime product annihilation은 두 primary component의 direct sum을 주므로 $P^2=P$, $PU=UP$가 exact하게 따른다.

centered operator $C=U-cI$에 대해

$$
B=P+QCQ
\tag{19zq-d}
$$

를 만든다. $B$가 exact invertible이면 complement inverse도

$$
\boxed{R=QB^{-1}Q}
\tag{19zq-e}
$$

로 자동 구성되어 $RCQ=CR=Q$를 만족한다. 이 $P,R$를 앞 절의 strict inside/outside norm gate에 다시 넣어야 최종 Riesz projector가 된다. factor label을 뒤집거나 radius가 부적절하면 algebraic norm gate가 실패하며, complement가 center eigenvalue를 포함하면 (19zq-d)가 singular라서 $R$ 구성 단계에서 멈춘다. □

**[산출·경계]** `verified_polynomial_spectral_projector_construction.py`는 factor monic normalization, extended gcd/Bézout identity, product annihilation, 자동 $P,Q,B^{-1},R$, 최종 algebraic certificate를 산출한다. defective Jordan inside block, $\pm\sqrt2$ irrational spectrum, rank 0/full, factor scaling과 raw spectral scale covariance를 검증한다. diagonalization이나 eigenvector는 요구하지 않는다. 다만 $f_{\rm in},f_{\rm out}$ split 자체는 공급되며 characteristic/minimal polynomial factorization을 자동 발견한 것은 아니다.

#### characteristic polynomial과 임의 차수 exact factor split의 자동 발견

real rational normalized matrix $U\in\mathbb Q^{n\times n}$에서는 characteristic polynomial 자체도 입력받을 필요가 없다. Faddeev--LeVerrier recurrence

$$
B_0=I,
\qquad
c_k=-\frac1k\operatorname{tr}(UB_{k-1}),
\qquad
B_k=UB_{k-1}+c_kI
\tag{19zq-f}
$$

를 exact rational로 계산하면

$$
\chi_U(z)=z^n+c_1z^{n-1}+\cdots+c_n
\tag{19zq-g}
$$

을 얻고 $B_n=\chi_U(U)=0$을 exact Cayley--Hamilton self-check로 다시 확인한다.

계수 분모의 최소공배수를 곱하고 content를 나누어 primitive integer polynomial $F\in\mathbb Z[z]$로 만든다. rational-root theorem은 선형 인자를 빠르게 노출하는 진단 경로로 유지한다. 발견된 root $r$는 나눗셈 remainder가 정확히 0인 동안 반복 제거하여

$$
\chi_U(z)=\prod_{j=1}^J(z-r_j)^{m_j}\,g(z)
\tag{19zq-h}
$$

로 묶는다. 같은 root의 반복 인자는 하나의 primary atom으로 유지하므로 Jordan multiplicity를 inside/outside 양쪽으로 잘못 찢지 않는다. 그러나 rational root 부재만으로 고차 irreducibility를 주장하지 않고, 다음 Gauss--Kronecker 완전 탐색으로 모든 차수를 처리한다.

**[정리: 유한 Kronecker 인수 탐색]** $F\in\mathbb Z[z]$가 primitive이고 $\deg F=n\ge2$라 하자. $F=GH$가 $\mathbb Q[z]$의 비자명한 분해이면 Gauss 보조정리에 의해 부호를 제외하고 primitive $G,H\in\mathbb Z[z]$로 잡을 수 있으며, 둘 중 하나는

$$
1\le m:=\deg G\le\left\lfloor\frac n2\right\rfloor
\tag{19zq-k}
$$

를 만족한다. $F(a_i)\ne0$인 서로 다른 정수점 $a_0,\ldots,a_m$을 잡으면

$$
G(a_i)\mid F(a_i),
\qquad
D_i:=\{d\in\mathbb Z:d\mid F(a_i)\}
\tag{19zq-l}
$$

이다. 따라서 실제 $G$의 값 벡터는 유한집합 $D_0\times\cdots\times D_m$ 안에 반드시 들어 있다. 각 후보 $y=(y_0,\ldots,y_m)$가 정하는 유일한 보간다항식은

$$
G_y(z)=\sum_{i=0}^{m}y_i
\prod_{\substack{0\le j\le m\\j\ne i}}
\frac{z-a_j}{a_i-a_j}.
\tag{19zq-m}
$$

$\deg G_y=m$, 모든 계수가 정수, primitive normalization 뒤 $G_y\mid F$의 exact remainder가 0인 후보만 인수로 채택한다. $m=1,\ldots,\lfloor n/2\rfloor$의 모든 값 벡터를 소진했는데 인수가 없으면 (19zq-k)--(19zq-m)에 의해 $F$는 $\mathbb Q$ 위 irreducible이다. 인수가 발견되면 양쪽 몫에 같은 절차를 재귀 적용한다. 유한 차수와 각 점의 유한 divisor 집합 때문에 알고리즘은 유한하며, 수치 근찾기나 허용오차가 들어가지 않는다. □

**[정리: multiplicity와 primary atom 재구성]** 재귀 결과의 서로 같은 monic irreducible factor를 $h_j$와 multiplicity $\mu_j$로 묶으면

$$
\chi_U(z)=\prod_{j=1}^{M}h_j(z)^{\mu_j},
\qquad
g_j(z):=h_j(z)^{\mu_j}.
\tag{19zq-n}
$$

구현은 우변을 exact rational로 다시 곱해 $\chi_U$와 계수별 동일한지 확인한다. 각 $g_j$가 하나의 primary atom이므로 동일 irreducible factor의 generalized eigenspace를 partition이 multiplicity 중간에서 절단하지 않는다. □

탐색 비용도 증명 계약의 일부다. degree $m$에서 필요한 값 벡터 수는

$$
N_m=\prod_{i=0}^{m}\#D_i.
\tag{19zq-o}
$$

누적 후보 수가 사전 선언한 $B_{\rm fac}$을 넘으면 그 search space에 들어가기 전에 `Q_FACTORIZATION_CANDIDATE_BUDGET_EXCEEDED`로 멈추며 complete factorization을 주장하지 않는다. 반대로 성공 receipt는 실제 공급된 다항식에 대해 필요한 모든 irreducibility search가 소진됐거나 exact proper factor가 발견되어 재귀적으로 닫혔음을 뜻한다. 이는 실행시간이 모든 차수에서 균일하게 작다는 주장이 아니라, **예산 안에 들어온 임의 유한 차수 입력에 대한 완전성 정리**다.

#### Gaussian-rational 행렬의 실수 characteristic envelope

복소 유리수 행렬 $U=A+iB\in\mathbb Q(i)^{n\times n}$를 단순 거절할 필요는 없다. 단, 중심 $c\in\mathbb R$인 원은 켤레대칭이므로 다음 exact realification을 사용할 수 있다.

$$
\mathcal R(U)=
\begin{pmatrix}
A&-B\\
B&A
\end{pmatrix}
\in\mathbb Q^{2n\times2n}.
\tag{19zq-p}
$$

**[정리: real characteristic envelope]** $\chi_U(z)=\det(zI-U)\in\mathbb Q(i)[z]$라 하고 계수 켤레 다항식을 $\overline{\chi_U}(z)$라 하면

$$
\chi_{\mathcal R(U)}(z)
=\chi_U(z)\,\overline{\chi_U}(z)
\in\mathbb Q[z].
\tag{19zq-q}
$$

또한 Cayley--Hamilton으로 $\chi_U(U)=0$이므로

$$
\chi_{\mathcal R(U)}(U)
=\overline{\chi_U}(U)\chi_U(U)=0.
\tag{19zq-r}
$$

따라서 (19zq-q)의 complete Q factor를 원래 복소 행렬 $U$의 annihilating primary atom으로 사용할 수 있다. 여기서 realification은 characteristic factor **발견에만** 쓰고, Bézout projector와 exterior inverse는 원래 $n\times n$ Gaussian-rational $U$에서 구성한다. □

**[정리: 실수 중심의 켤레 label 보존과 rank convention]** $c\in\mathbb R$이면 모든 $\lambda\in\mathbb C$에 대해

$$
|\lambda-c|=|\overline\lambda-c|.
\tag{19zq-s}
$$

그러므로 envelope가 함께 묶는 켤레 성분은 원 $|z-c|=r$의 서로 다른 쪽에 놓이지 않는다. 최종 projector $P\in\mathbb Q(i)^{n\times n}$의 답은

$$
d_{\mathbb C}=\operatorname{tr}_{\mathbb C}P
=\operatorname{rank}_{\mathbb C}P,
\qquad
\operatorname{rank}_{\mathbb R}\mathcal R(P)=2d_{\mathbb C}
\tag{19zq-t}
$$

이며 구현은 첫 번째 값만 `projector_rank`로 반환한다. 즉 실수화의 $2n$ ambient dimension이나 $2d_{\mathbb C}$를 의식 부분공간 차원으로 잘못 보고하지 않는다. □

**[정리: 임의 Gaussian-rational 중심의 영점 이동]** 이제 $c\in\mathbb Q(i)$가 비실수여도

$$
W=U-cI,
\qquad
\lambda\in\sigma(U)iff \mu:=\lambda-c\in\sigma(W),
\qquad
|\lambda-c|=|\mu|
\tag{19zq-u}
$$

로 먼저 옮긴다. $W$의 contour 중심은 0이므로 $|\mu|=|\bar\mu|$가 항상 성립하고, $\chi_{\mathcal R(W)}\in\mathbb Q[z]$의 atom은 다시 켤레 label을 보존한다. 변수변환 $z=c+w$와 resolvent 항등식

$$
(zI-U)^{-1}=(wI-W)^{-1}
\tag{19zq-v}
$$

때문에 $U$의 중심 $c$, 반지름 $r$ Riesz projector와 $W$의 중심 0, 반지름 $r$ projector는 정확히 같다. 구현은 envelope가 필요한 모든 경우에 raw/normalized center를 먼저 빼고, factor와 strict norm gate를 $W$에 적용한다. 따라서 실수 또는 Gaussian-rational $U$와 임의 exact Gaussian-rational 중심을 처리하면서도 반환 rank는 원래 복소 상태공간의 rank다. □

검증된 atom $g_1,\dots,g_M$에 대해 사전고정 partition budget $B_{\rm part}$ 안에서

$$
f_{\rm in}=\prod_{j\in S}g_j,
\qquad
f_{\rm out}=\prod_{j\notin S}g_j
\tag{19zq-i}
$$

를 모두 검사한다. empty/full partition에는 $\chi_U$와 coprime인 자동 생성 dummy linear factor를 붙여 rank 0/full도 허용한다. 각 partition은 앞 절의 Bézout $P,R$ 구성과 strict spectral norm gate를 모두 통과해야 한다. 유일한 partition만

$$
\boxed{
(f_{\rm in}^*,f_{\rm out}^*,P^*,R^*,d^*)
}
\tag{19zq-j}
$$

로 승격하며, 0개면 미분류, 둘 이상이면 ambiguous다. contour 위 eigenvalue의 등호는 inside/outside 어느 partition도 통과하지 못한다. □

**[산출·경계]** `verified_complete_q_polynomial_factorization.py`는 primitive lift, 각 trial degree의 정수 평가점, divisor-product 후보 수, 실제 소진 수, 발견 인수, irreducibility·multiplicity·primary-factor receipt와 exact product reconstruction을 산출한다. `verified_characteristic_spectral_split_discovery.py`는 이를 real input의 $\chi_U$ 또는 Gaussian-rational input의 $\chi_{\mathcal R(U)}$에 연결하여 atom/partition, 모든 passing construction과 원래 복소 행렬의 유일 projector rank를 산출한다. rational diagonal spectrum, defective repeated root, $\pm\sqrt2$, irreducible quartic·degree-eight, repeated nonlinear factor, Gaussian-rational diagonal/defective block, rank 0/full, scale covariance와 두 quartic atom의 rank-4 split을 자동 검증한다. factor 후보 budget과 partition budget 초과는 서로 다른 코드로 partition 전에 또는 partition 열거 전에 각각 멈춘다.

**[미완성: interval·자료]** 임의 차수 exact $\mathbb Q$ factorization과 임의 Gaussian-rational 중심 원의 realification envelope는 공급 입력별 유한 후보 예산 조건 아래 닫혔다. 남은 factor 공백은 interval-valued coefficient·factor witness와 empirical provenance다. 직접적인 $\mathbb Q(i)[z]$ irreducible factor 목록도 산출하지 않지만, circular projector/rank에는 centered real envelope가 충분하다. 또한 factor가 정확해도 비정규 matrix의 충분조건 norm gate가 실패할 수 있다. 예를 들어 고윳값이 원 밖에 있어도 companion 좌표의 exterior inverse norm이 클 수 있으므로, 그 실패를 스펙트럼 배치의 부정으로 읽지 않는다. 새 기록은 `_workspace/ce/brain-complex-rational-spectral-envelope-20260826/40-final-report.md`와 `_workspace/ce/brain-complete-q-polynomial-factorization-20260826/40-final-report.md`, factor-to-projector 기록은 `_workspace/ce/brain-polynomial-spectral-projector-construction-20260826/40-final-report.md`, characteristic discovery 기록은 `_workspace/ce/brain-characteristic-spectral-split-discovery-20260826/40-final-report.md`를 따른다.

#### 명목 자동분할에서 구간 행렬족 전체 rank로

구간 계수 다항식을 직접 인수분해하지 않아도, 명목 행렬에서 자동 발견한 exact rank를 직사각 행렬 상자 전체로 이전할 수 있다. 정규화된 명목 행렬을 $\widetilde U_0$라 하고 모든 허용 오차 $E$가 성분별로

$$
|\Re E_{ij}|\le a_{ij},
\qquad
|\Im E_{ij}|\le b_{ij}
\tag{19zq-w}
$$

를 만족한다고 하자. exact dyadic square-root enclosure로

$$
\|E\|_2\le\|E\|_F
\le \varepsilon^+,
\qquad
(\varepsilon^+)^2\ge
\sum_{i,j}(a_{ij}^2+b_{ij}^2)
\tag{19zq-x}
$$

를 얻는다.

**[정리: 자동 명목 rank의 구간족 보존]** 명목 자동분할이 exact projector $P_0$와 rank $d_0$를 구성하고, 독립적인 full-circle certificate가 모든 $z\in\Gamma$에 대해

$$
\sigma_{\min}(zI-\widetilde U_0)\ge\delta_0>0
\tag{19zq-y}
$$

를 증명했다고 하자. $\varepsilon^+<\delta_0$이면 모든 $t\in[0,1]$과 허용 $E$에 대해

$$
\sigma_{\min}\!\left(zI-(\widetilde U_0+tE)\right)
\ge\delta_0-t\|E\|_2
\ge\delta_0-\varepsilon^+>0.
\tag{19zq-z}
$$

따라서 선형 호모토피 전체에서 contour crossing이 없고 Riesz projector rank는 정수값 연속량으로 일정하므로

$$
\boxed{\operatorname{rank}P(\widetilde U_0+E)=d_0}
\tag{19zq-aa}
$$

이다. resolvent identity와 contour 길이 $2\pi\widetilde r$로부터

$$
\|P(\widetilde U_0+E)-P_0\|_2
\le
\frac{\widetilde r\,\varepsilon^+}
{\delta_0(\delta_0-\varepsilon^+)}
\tag{19zq-ab}
$$

도 얻는다. 이 정리는 개별 구간 characteristic polynomial의 root를 추적하거나 인수분해하지 않는다. 필요한 것은 명목 exact factor/projector와 행렬 상자 전체의 strict contour margin이다. □

**[산출·경계]** `verified_interval_characteristic_spectral_split.py`는 명목 complete-Q/centered-envelope discovery receipt, 구간 full-circle receipt, 명목 exact projector/rank, robust margin, family rank와 exact-projector perturbation 상계를 한 객체로 묶는다. 명목 factor budget 실패, contour 위 고윳값, $\varepsilon^+\ge\delta_0$, 잘못된 uncertainty schema를 각각 거절한다. Gaussian-rational 비실수 중심도 먼저 중심이동한 명목 rank와 원래 중심의 interval circle certificate를 결합한다. uncertainty radii가 실제 추정오차를 덮는다는 경험적 calibration은 여전히 별도다. 기록은 `_workspace/ce/brain-interval-characteristic-spectral-split-20260826/40-final-report.md`를 따른다.

#### 19u-a. 불변 좌표 블록에서의 직접 구간 인수 계수

앞 절의 IVSPEC 정리는 rank 보존에 구간 특성다항식 인수가 필요 없음을 보였다. 그러나 행렬이 정확한 불변 좌표 분할을 이미 갖는 부분족에서는 인수 자체도 직접 산출할 수 있다. 정규화된 행렬 상자 $\mathcal A$와 좌표 분할 $I\sqcup O=\{1,\ldots,n\}$를 잡고, 모든 $A\in\mathcal A$에 대해 교차 블록이 정확히 0이라고 하자.

$$
A=\begin{pmatrix}A_I&0\\0&A_O\end{pmatrix}.
\tag{19u-a1}
$$

여기서 ‘정확히 0’은 작은 수라는 뜻이 아니다. 명목 성분과 그 성분의 실수·허수 uncertainty radius가 모두 0이어야 한다. 이 조건이 깨지면 아래 인수화는 적용하지 않는다.

**[정리: 조건부 직접 구간 인수]** (19u-a1)이 성립하고 행렬식 순열 전개 예산이 허용되면, 모든 $A\in\mathcal A$에 대해

$$
\chi_A(z)=\det(zI-A)
=\det(zI_I-A_I)\det(zI_O-A_O)
=\chi_{A_I}(z)\chi_{A_O}(z).
\tag{19u-a2}
$$

각 성분 상자를 $[a^-_{ij},a^+_{ij}]+i[b^-_{ij},b^+_{ij}]$로 쓰자. 복소 직사각형의 사칙연산을 바깥쪽으로 닫고 Leibniz 전개

$$
\det(zI_k-B)
=\sum_{\pi\in S_k}\operatorname{sgn}(\pi)
\prod_{j=1}^{k}\bigl(z\,\mathbf 1_{j=\pi(j)}-B_{j,\pi(j)}\bigr)
\tag{19u-a3}
$$

를 수행하면 두 monic 다항식의 모든 계수에 대한 유리수 복소 직사각형 $\mathbf C^I_m,\mathbf C^O_m$을 얻는다. 구간 연산의 의존성 때문에 상자가 넓어질 수는 있지만, 실제 모든 허용 행렬의 해당 계수는 그 상자 안에 들어간다. 필요한 순열 항 수는 보수적으로

$$
N_{\det}=|I|!+|O|!+n!
\tag{19u-a4}
$$

이며, 선언된 예산을 넘으면 결과 없이 실패한다. (19u-a2)는 블록 대각 행렬식 항등식이고, (19u-a3)의 각 기본 연산이 포함 단조성을 가지므로 계수 포함이 따른다. 최고차항은 두 블록 모두 정확히 1이어서 monic 조건도 보존된다. □

이제 IVSPEC가 같은 행렬 상자에 성공하고, 자동 발견한 명목 Riesz projector가 좌표 projector

$$
P_I=\operatorname{diag}(\mathbf 1_{j\in I})
\tag{19u-a5}
$$

와 정확히 같다고 하자. 그러면 $\deg\chi_{A_I}=|I|$는 상자 전체에서 보존된 내부 Riesz rank와 같고, $\deg\chi_{A_O}=|O|$는 외부 rank와 같다. 따라서 이 부분족에서는 root를 개별 추적하지 않고도 ‘직접 인수 계수 상자’와 ‘스펙트럼 순위’를 한 영수증으로 연결한다.

**[산출·실패 경계]** `verified_direct_interval_coordinate_block_factors.py`는 실수·Gaussian-rational 성분 상자를 정규화하고, 교차 블록 0, 순열 예산, IVSPEC 성공, projector 일치, degree-rank 일치와 monic 조건을 차례로 검사한다. IVSPEC가 실패한 defective 예에서는 대수적 계수 상자를 계산해도 이를 스펙트럼 안/밖 인수로 승격하지 않는다. 일반적으로 결합된 구간 행렬, interval irreducible factor 판정, root localization, uncertainty의 실측 coverage, 의식 차원 4--6의 경험적 식별은 여전히 미완성이다. 기록은 `_workspace/ce/brain-direct-interval-coordinate-block-factors-20260826/40-final-report.md`를 따른다.

#### 연속 원 매개변수 상자의 전역 margin 최적화

유한 menu를 넘어 연속적으로 중심과 반지름을 선택하려면 목적함수와 전역 최적성 오차를 먼저 고정해야 한다. exact diagonalization witness

$$
UV=V\operatorname{diag}(\lambda_1,\ldots,\lambda_n),
\qquad V\in\mathbb Q(i)^{n\times n}\text{ invertible}
\tag{19zq-ac}
$$

가 공급되어 전체 스펙트럼과 대수적 중복도를 고정한다고 하자. 각 고윳값에 목표 label $\ell_j\in\{\mathrm{in},\mathrm{out}\}$을 사전고정하고, 정규화된 원 매개변수 $\theta=(x,y,r)$에 대해

$$
q_j(\theta)=
\begin{cases}
r^2-|\lambda_j-(x+iy)|^2,&\ell_j=\mathrm{in},\\
|\lambda_j-(x+iy)|^2-r^2,&\ell_j=\mathrm{out},
\end{cases}
\qquad
\Phi(\theta)=\min_j q_j(\theta)
\tag{19zq-ad}
$$

로 정의한다. $\Phi>0$은 모든 목표 label이 strict하게 맞음을 뜻하고, $\Phi=0$은 적어도 하나가 contour 위에 있음을 뜻한다. 제곱거리 목적함수이므로 square root나 floating tolerance가 필요 없다.

**[정리: cell 전역 상계]** 직육면체 cell $C$의 midpoint를 $\theta_C=(x_C,y_C,r_C)$, 각 half-width를 $h_x,h_y,h_r$라 하자. 고윳값 $\lambda_j=a_j+ib_j$에 대해 cell 전체의 좌표거리 상계를

$$
D_{x,j}=\max_{x\in C}|x-a_j|,
\quad
D_{y,j}=\max_{y\in C}|y-b_j|,
\quad
R_C=\max_{r\in C}|r|
\tag{19zq-ae}
$$

로 놓으면 좌표별 평균값정리로

$$
|q_j(\theta)-q_j(\theta_C)|
\le V_{j,C}:=2D_{x,j}h_x+2D_{y,j}h_y+2R_Ch_r.
\tag{19zq-af}
$$

따라서

$$
\sup_{\theta\in C}\Phi(\theta)
\le U_C:=\min_j\bigl(q_j(\theta_C)+V_{j,C}\bigr).
\tag{19zq-ag}
$$

이 상계는 cell midpoint만 비교하는 grid heuristic이 아니라 cell 안의 모든 실수 매개변수를 덮는다. □

**[정리: branch-and-bound의 $\eta$-전역 최적성]** 현재 partition의 모든 cell 상계 중 최대를 $U=\max_CU_C$, 지금까지 평가한 midpoint score의 최대를 $L$이라 하자. 항상

$$
L\le\max_{\theta\in\mathcal B}\Phi(\theta)\le U.
\tag{19zq-ah}
$$

$U-L\le\eta$가 될 때까지 가장 큰 $U_C$ cell의 가장 긴 축을 exact midpoint에서 양분하면, 선택점 $\theta_*$는

$$
0\le
\max_{\theta\in\mathcal B}\Phi(\theta)-\Phi(\theta_*)
\le\eta
\tag{19zq-ai}
$$

를 만족한다. $\Phi(\theta_*)>0$이어야만 선택을 승인하고, 선택 원은 다시 complete characteristic discovery와 strict algebraic projector/rank gate를 통과해야 한다. cell budget이 먼저 소진되면 연속 최적성도 rank도 내지 않는다. □

**[산출·경계]** `verified_continuous_circle_spectral_margin_optimization.py`는 exact diagonalization, 연속 center-real/imag/radius box, target labels, tolerance와 cell budget을 검사하고, 모든 terminal cell의 midpoint·variation·global upper, incumbent, certified gap, 선택 contour와 최종 exact rank를 산출한다. rank 0/full, Gaussian-rational 비실수 중심, raw-scale covariance, invalid witness, impossible labels와 budget exhaustion을 분리 검증한다. 이는 exact diagonalization witness가 있는 **원형 contour와 signed squared spectral margin**의 조건부 연속 최적화다. defective/no-witness 일반행렬의 pseudospectral 목적함수, spline/ellipse의 연속 knot·shape 최적화, empirical objective 선택은 후속 경계다. 기록은 `_workspace/ce/brain-continuous-circle-spectral-margin-optimization-20260826/40-final-report.md`를 따른다.

#### 대각화 없는 algebraic projector margin의 연속 최적화

defective 행렬에서는 개별 고윳값 label 목적함수 대신, 기준 원에서 자동 구성된 exact algebraic projector $P$와 $Q=I-P$를 고정한다. 정규화된 행렬을 $\widetilde U$라 하고

$$
A(c)=(\widetilde U-cI)P,
\qquad
B(c)=P+Q(\widetilde U-cI)Q,
\qquad
R(c)=QB(c)^{-1}Q
\tag{19zq-aj}
$$

로 둔다. $B(c)$가 가역인 영역에서 다음 exact rational 목적함수를 정의한다.

$$
\Phi_{\rm alg}(c,r)=
\min\left\{
r^2-\|A(c)\|_F^2,
\;1-r^2\|R(c)\|_F^2
\right\}.
\tag{19zq-ak}
$$

**[정리: 양의 algebraic margin]** $\Phi_{\rm alg}(c,r)>0$이면

$$
\|A(c)\|_2\le\|A(c)\|_F<r,
\qquad
\|R(c)\|_2\le\|R(c)\|_F<\frac1r.
\tag{19zq-al}
$$

따라서 앞의 algebraic Riesz theorem의 strict inside/exterior-inverse gate가 성립하고, $P$는 그 원의 exact Riesz projector다. 이 충분조건은 비정규 행렬에서도 eigenvector나 diagonalization을 요구하지 않는다. □

중심 상자 전체에서 $R(c)$가 존재하는지도 먼저 증명한다. 기준 중심 $c_0$의 $R_0=R(c_0)$와 상자의 최대 중심 이동 $H\ge|c-c_0|$에 대해

$$
H\|R_0\|_F^+<1
\tag{19zq-am}
$$

이면 Neumann 정리에 의해 모든 허용 중심에서 complement block이 가역이다.

**[정리: algebraic cell 상계]** 한 cell midpoint를 $c_C$, 중심 half-width의 복소 절댓값 상계를 $h_C$, midpoint Frobenius bracket을 $a_C^-\le\|A(c_C)\|_F$와 $b_C^-\le\|R(c_C)\|_F\le b_C^+$라 하자. 그러면

$$
\underline a_C=max\{0,a_C^- -h_C\|P\|_F^+\},
\tag{19zq-an}
$$

이고 $h_Cb_C^+<1$이면 resolvent identity로

$$
\|R(c)-R(c_C)\|_F
\le
\frac{h_C(b_C^+)^2}{1-h_Cb_C^+}
=:\Delta_{R,C}^+,
\qquad
\underline b_C=max\{0,b_C^- -\Delta_{R,C}^+\}.
\tag{19zq-ao}
$$

따라서 cell 전체에서

$$
\sup_C\Phi_{\rm alg}
\le
U_C^{\rm alg}:=min\left\{
(r_C^+)^2-\underline a_C^2,
\;1-(r_C^-)^2\underline b_C^2
\right\}.
\tag{19zq-ap}
$$

$h_Cb_C^+\ge1$인 거친 cell에서는 두 번째 상계를 안전한 값 1로 두고 세분화한다. 단일점 cell에서는 exact Frobenius 제곱을 그대로 사용한다. 이 $U_C^{\rm alg}$를 (19zq-ah)--(19zq-ai)의 branch-and-bound에 넣으면 diagonalization 없이도 연속 circle box의 $\eta$-전역 algebraic margin optimum을 인증한다. 선택점은 다시 자동 characteristic discovery를 통과하고 reference projector와 exact 행렬로 동일해야 한다. □

**[산출·경계]** `verified_continuous_algebraic_circle_margin_optimization.py`는 reference discovery, uniform Neumann center domain, 모든 cell의 inside/exterior Frobenius 제곱·차분 상계·global upper, 선택 margin과 projector identity를 산출한다. defective Jordan rank 2, $\pm\sqrt2$ irreducible block, scale covariance, 기준 contour 실패, uniform-domain 실패, cell budget과 비양수 margin을 검증한다. 이는 **기준 exact projector와 uniform exterior center domain이 있는 원형 family**를 닫는다. 아래 CE-EOPT/CE-SEOPT/CE-GAOPT가 compact diagonalized general-affine ellipse를 별도로 닫지만, 기준 projector조차 없는 상자, defective ellipse, spline knot와 empirical objective는 남는다. 기록은 `_workspace/ce/brain-continuous-algebraic-circle-margin-optimization-20260826/40-final-report.md`를 따른다.

#### 고정 유리 방향 ellipse의 연속 중심·두 축 최적화

비원형 후보를 실제 연속 최적화 문제로 만들기 위해 방향과 shape를 분리한다. $p=(p_x,p_y)\in\mathbb Q^2$, $p_x^2+p_y^2=1$을 탐색 전에 고정하고 $p_\perp=(-p_y,p_x)$라 하자. 중심 $c=(c_x,c_y)$와 양의 두 반축 $a,b$는 compact rational box에서 연속적으로 움직인다. complete exact diagonalization $UV=V\operatorname{diag}(\lambda_j)$와 frozen label $s_j\in\{\mathrm{in},\mathrm{out}\}$에 대해

$$
\xi_j=p\cdot(\lambda_j-c),
\qquad
\eta_j=p_\perp\cdot(\lambda_j-c),
\tag{19zq-aq}
$$

$$
g_j(c,a,b)=a^2b^2-b^2\xi_j^2-a^2\eta_j^2,
\qquad
q_j=\begin{cases}g_j,&s_j=\mathrm{in},\\-g_j,&s_j=\mathrm{out},\end{cases}
\qquad
\Phi_{\rm ell}=\min_jq_j
\tag{19zq-ar}
$$

로 둔다. 모든 양은 spectral reference scale로 먼저 나누므로 $g_j,q_j,\Phi_{\rm ell}$은 정규화된 4차 무차원량이다.

**[정리: 양의 ellipse spectral margin]** $a,b>0$일 때 $g_j>0$은

$$
\frac{\xi_j^2}{a^2}+\frac{\eta_j^2}{b^2}<1
\tag{19zq-as}
$$

과 동치이고 $g_j<0$은 반대의 strict 부등식과 동치다. 따라서 $\Phi_{\rm ell}>0$이면 모든 inside 고유값은 ellipse 내부, 모든 outside 고유값은 외부에 있으며 경계에는 스펙트럼이 없다. $P=V\operatorname{diag}(1_{s_j=\mathrm{in}})V^{-1}$는 그 ellipse의 exact Riesz projector이고 rank는 frozen label 수다. 대각화 witness가 exact이므로 oblique $V$도 허용된다. □

**[정리: exact cell range와 전역 최적성]** parameter cell $C=I_x\times I_y\times I_a\times I_b$에서 affine interval arithmetic로 $\Xi_{j,C}\supset\xi_j(C)$, $H_{j,C}\supset\eta_j(C)$를 계산하고, 0을 지나는지까지 포함하는 exact square interval을 $S(I)\supset\{z^2:z\in I\}$라 하자. 양의 축 때문에

$$
G_{j,C}=
S(I_a)S(I_b)-S(I_b)S(\Xi_{j,C})-S(I_a)S(H_{j,C})
\supset g_j(C).
\tag{19zq-at}
$$

inside에는 $Q_{j,C}=G_{j,C}$, outside에는 $Q_{j,C}=-G_{j,C}$를 쓰면

$$
\sup_{\theta\in C}\Phi_{\rm ell}(\theta)
\le U_C:=\min_j\sup Q_{j,C}.
\tag{19zq-au}
$$

이는 표본 근사가 아니라 cell의 모든 실수점을 포함하는 inclusion bound다. 연산은 유한 다항식의 자연 구간확장이므로 cell 폭이 0으로 갈 때 각 $Q_{j,C}$도 exact 점값으로 수렴한다. 가장 큰 $U_C$ cell의 가장 긴 축을 exact 이분하고 incumbent $L$과 $U=\max_CU_C$가 $U-L\le\eta_4$가 될 때 승인하면 선택 ellipse는 전체 4변수 box에서 $\eta_4$-전역 최적이다. 예산 소진이나 선택 margin 비양수는 승격을 거절한다. □

**[환원·산출·경계]** $a=b=r$이면 $g_j=r^2(r^2-|\lambda_j-c|^2)$이므로 원형 signed-squared margin과 부호가 정확히 같고, 비원형일 때는 두 축을 독립적으로 최적화한다. `verified_continuous_axis_aligned_ellipse_spectral_margin_optimization.py`는 fixed rational rotation, 연속 center/two-semiaxis box, exact rational outward interval enclosure, terminal partition, quartic incumbent/upper/gap과 exact oblique projector를 산출한다. 이 enclosure는 포함관계가 엄밀하지만 일반적으로 최소 range라고 주장하지 않는다. 고정·회전 ellipse, circle 환원, raw-scale covariance, boundary contact, invalid witness와 cell-budget refusal을 검증한다. focused 18/18, 직접 인접 68/68, 무차원·원장 결합 156/156, 전체 연속/구간/contour 사슬 436/436을 통과했다. 닫힌 범위는 **complete exact diagonalization과 사전 고정된 유리 방향** 아래의 중심·두 축 shape 최적화이며, 아래 CE-SEOPT가 같은 orthogonal-axis family의 방향까지 연속화한다. general-affine shear, spline knot, defective/no-witness ellipse, empirical objective는 남는다. 기록은 `_workspace/ce/brain-continuous-axis-aligned-ellipse-spectral-margin-optimization-20260826/40-final-report.md`를 따른다.

#### stereographic 유리 chart에서 ellipse 방향까지 연속 최적화

방향을 유한 menu로 고정하지 않고 연속 변수로 만들되 삼각함수의 비엄밀 근사를 피한다. 무차원 stereographic 좌표 $t\in I_t\subset\mathbb R$에 대해

$$
u(t)=1-t^2,
\qquad v(t)=2t,
\qquad d(t)=1+t^2>0,
\tag{19zq-av}
$$

$$
p(t)=\frac{(u(t),v(t))}{d(t)},
\qquad p_\perp(t)=\frac{(-v(t),u(t))}{d(t)}
\tag{19zq-aw}
$$

로 둔다. $u^2+v^2=d^2$이므로 모든 실수 $t$에서 두 벡터는 exact orthonormal positive frame이다. ellipse의 축은 부호를 뒤집어도 같은 직선이므로 이 chart의 빠진 극한 방향 $p=(-1,0)$은 $p=(1,0)$과 동일한 무향 축이며 $t=0$에서 대표된다. 실제 최적화 주장은 사전 선언한 compact $I_t$에 대해서만 한다.

고유값 차이 $\delta_j=\lambda_j-c$와 분자 좌표

$$
\widehat\xi_j=u\,\Re\delta_j+v\,\Im\delta_j,
\qquad
\widehat\eta_j=-v\,\Re\delta_j+u\,\Im\delta_j
\tag{19zq-ax}
$$

를 쓰면 fixed-orientation의 기하 margin과 정확히 같은 값은

$$
g_j(c,a,b,t)=
\frac{
d^2a^2b^2-b^2\widehat\xi_j^2-a^2\widehat\eta_j^2
}{d^2}.
\tag{19zq-ay}
$$

여기서 분자를 없애지 않고 $d^2$로 다시 나누는 것이 필수다. 분자만 목적함수로 쓰면 부호 판정은 같지만 $(1+t^2)^2$가 큰 chart 위치를 인위적으로 선호하여 서로 다른 방향의 margin 크기를 왜곡한다. (19zq-ay)는 (19zq-ar)의 $\xi_j=p(t)\cdot\delta_j$, $\eta_j=p_\perp(t)\cdot\delta_j$를 대입한 동일한 기하량이다.

**[정리: 연속 orientation cell enclosure]** $C=I_x\times I_y\times I_a\times I_b\times I_t$에서 $u,v,d^2,\widehat\xi_j,\widehat\eta_j$의 자연 interval extension을 exact rational endpoint 연산으로 계산한다. 분자 enclosure를 $N_{j,C}$, 양의 분모 enclosure를 $D_C=[D_C^-,D_C^+]$라 하면 $D_C^-\ge1$이고

$$
G_{j,C}=N_{j,C}/D_C
:=\operatorname{hull}\left\{
\frac{n}{d}:n\in\partial N_{j,C},\ d\in\partial D_C
\right\}
\supset g_j(C).
\tag{19zq-az}
$$

inside/outside 부호를 적용한 $Q_{j,C}$에 대해 다시

$$
\sup_C\Phi_{\rm sell}
\le U_C:=\min_j\sup Q_{j,C}
\tag{19zq-ba}
$$

가 성립한다. 모든 연산은 분모가 0에서 균일하게 떨어진 유한 다항식·나눗셈의 자연 interval extension이므로 cell 폭과 함께 enclosure 폭도 0으로 간다. 5축 exact bisection에서 $U-L\le\eta$를 얻으면 중심·두 반축·방향을 합친 전체 box의 $\eta$-전역 최적성이 성립한다. □

**[산출·경계]** `verified_continuous_stereographic_ellipse_spectral_margin_optimization.py`는 orientation parameter cell, 분자·양수분모 interval division, 불변 기하 margin, 선택 exact rational orthonormal frame과 oblique Riesz projector를 산출한다. 방향 box 전역성, fixed-orientation 값과의 항별 동일성, dense rational containment, 5변수 동시 변화, circle 방향불변, 스케일 공변성, 경계·witness·budget 거절을 검증한다. focused 20/20, 직접 인접 88/88, 무차원·원장 결합 177/177, 전체 연속/구간/contour 사슬 457/457을 통과했다. 이는 diagonalization된 ellipse의 **한 compact stereographic chart에서 중심·두 축·방향을 함께** 닫고, 아래 CE-GAOPT가 shear까지 연속화한다. spline knot, defective/no-witness ellipse와 empirical objective는 남는다. 기록은 `_workspace/ce/brain-continuous-stereographic-ellipse-spectral-margin-optimization-20260826/40-final-report.md`를 따른다.

#### QR 좌표로 general-affine ellipse shear까지 연속 최적화

orthogonal semiaxis만 허용하면 회전된 ellipse는 모두 표현하지만, 공급된 두 affine 축벡터 자체의 shear 좌표와 conditioning을 직접 탐색하지 못한다. 이를 위해 stereographic frame $[p(t),p_\perp(t)]$ 뒤에 양의 대각을 가진 upper-triangular 행렬을 둔다.

$$
L(t,a,b,s)=
[p(t),p_\perp(t)]
\begin{pmatrix}a&s\\0&b\end{pmatrix},
\qquad a>0,\quad b>0.
\tag{19zq-bb}
$$

두 contour 축은

$$
\ell_u=a,p(t),
\qquad
\ell_v=s,p(t)+b,p_\perp(t),
\qquad
\det L=ab>0
\tag{19zq-bc}
$$

이다. 반대로 임의의 $2\times2$ real matrix $L_*$가 $\det L_*>0$이면 positive-diagonal QR 분해 $L_*=QR$가 존재하고 $Q\in SO(2)$, $R=\begin{psmallmatrix}a&s\\0&b\end{psmallmatrix}$, $a,b>0$이다. ellipse는 unit disk의 affine image이므로 축행렬 전체 부호의 차이는 같은 contour를 나타내며, 앞의 stereographic 무향 방향 chart와 합쳐 (19zq-bb)는 orientation-preserving general-affine ellipse의 표준 좌표를 준다. 실제 인증은 선언한 compact $(a,b,s,t)$ box에 한정한다.

rotated coordinates를 $\xi=p\cdot(\lambda-c)$, $\eta=p_\perp\cdot(\lambda-c)$라 하면

$$
L^{-1}(\lambda-c)=
\begin{pmatrix}
(b\xi-s\eta)/(ab)\\[2pt]
\eta/b
\end{pmatrix}.
\tag{19zq-bd}
$$

따라서 general-affine ellipse의 exact signed margin은

$$
g_j^{\rm aff}
=a^2b^2-(b\xi_j-s\eta_j)^2-a^2\eta_j^2.
\tag{19zq-be}
$$

**[정리: general-affine 내부·외부와 Riesz projector]** $g_j^{\rm aff}>0$은 $\|L^{-1}(\lambda_j-c)\|_2<1$과 동치이고, 음수는 strict exterior와 동치다. frozen label 부호를 적용한 $\Phi_{\rm aff}=\min_jq_j^{\rm aff}>0$이면 affine ellipse 경계에 스펙트럼이 없고 exact diagonalization의 $V\operatorname{diag}(labels)V^{-1}$가 그 Riesz projector다. $s=0$에서는 (19zq-ar)에 항별로 환원된다. □

stereographic 분자를 쓰면

$$
g_j^{\rm aff}
=\frac{
d^2a^2b^2-(b\widehat\xi_j-s\widehat\eta_j)^2-a^2\widehat\eta_j^2
}{d^2}.
\tag{19zq-bf}
$$

**[정리: 6변수 outward enclosure와 전역 최적성]** $C=I_x\times I_y\times I_a\times I_b\times I_s\times I_t$에서 각 곱은 부호를 보존하는 네 endpoint hull로, 제곱은 0 포함 여부를 반영해 계산한다. $(I_b\widehat\Xi-I_s\widehat H)^2$를 한 덩어리로 enclosure하고, 전체 분자를 양의 $D_C\supset d^2$로 interval-divide하면 $G_{j,C}^{\rm aff}\supset g_j^{\rm aff}(C)$다. label별 부호와 최소를 취한 $U_C$는 cell 전체의 global upper다. 분모 하한은 1이고 식은 compact box에서 연속인 유리함수이므로 exact longest-axis subdivision의 cell 폭과 함께 enclosure 폭이 0으로 간다. $U-L\le\eta$이면 중심·두 양의 축·shear·방향을 합친 6변수 box에서 $\eta$-전역 최적이다. □

**[산출·경계]** `verified_continuous_general_affine_ellipse_spectral_margin_optimization.py`는 shear interval, QR axes, exact determinant $ab$, coupled coordinate square, 양수분모 division, terminal 6-cells와 exact projector를 산출한다. shear 선택, $s=0$ 환원, direct inverse-coordinate identity, determinant 불변성, dense $(s,t)$ containment, 6변수 동시 변화, scale·oblique·경계·budget을 검증한다. focused 21/21, 직접 인접 109/109, 무차원·원장 결합 199/199, 전체 연속/구간/contour 사슬 479/479을 통과했다. 이는 diagonalized finite matrix의 compact **general-affine ellipse box**를 닫는다. spline knot와 defective/no-witness noncircular algebraic margin, empirical objective는 남는다. 기록은 `_workspace/ce/brain-continuous-general-affine-ellipse-spectral-margin-optimization-20260826/40-final-report.md`를 따른다.

#### 이동 knot에도 자동으로 유지되는 periodic $C^q$ radial spline

기존 piecewise-polynomial/rational spline은 공급된 고정 knot에서 좌우 jet을 검사한다. 일반 patch를 그대로 둔 채 knot만 움직이면 그 등식은 보통 즉시 깨진다. 연속 knot 최적화에는 접합을 매번 우연히 다시 맞추는 대신, 모든 knot 위치에서 접합을 구조적으로 강제하는 family가 필요하다.

directed unit-circle knot를 $u_k\in S^1$라 하고 각 arc $[u_k,u_{k+1}]$에 비음수 amplitude $\varepsilon_k$와

$$
m=q+1,
\qquad
\rho_k(u)=1+\varepsilon_k
(1-u\cdot u_k)^m(1-u\cdot u_{k+1})^m
\tag{19zq-bg}
$$

를 둔다. $u(\theta)\cdot u_k=\cos(\theta-\theta_k)$이므로

$$
1-u(\theta)\cdot u_k
=1-\cos(\theta-\theta_k)
=\frac12(\theta-\theta_k)^2+O((\theta-\theta_k)^4).
\tag{19zq-bh}
$$

따라서 $(1-u\cdot u_k)^m$은 knot에서 정확히 $2m$차로 사라지고 각도 도함수 $0,\ldots,2m-1$이 모두 0이다.

**[정리: knot-independent automatic $C^q$ junction]** (19zq-bg)의 모든 patch는 양 끝에서 값 1을 가지며 $1\le r\le q$차 angular derivative가 0이다. 실제로 $2m-1=2q+1\ge q$다. 그러므로 knot를 연속적으로 움직여도 좌우 patch는 공통 jet $(1,0,\ldots,0)$로 periodic $C^q$ 접합한다. $\varepsilon_k\ge0$이면 $\rho_k\ge1$이라 radial positivity도 자동이다. □

directed 원 전체의 knot를 exact rational로 움직이기 위해 anchor $u_\infty=(-1,0)$를 고정하고 나머지를

$$
u(t)=\left(\frac{1-t^2}{1+t^2},\frac{2t}{1+t^2}\right),
\qquad
t_1<\cdots<t_N
\tag{19zq-bi}
$$

로 둔다. 첫 box는 음수, 마지막 box는 양수이고, anchor를 포함한 모든 인접쌍에 대해 determinant interval의 하한을 양수로 요구한다. 이 조건은 각 directed arc가 strict $\pi$ 미만이고 knot 순서가 cell 전체에서 뒤집히지 않음을 보인다.

인접 arc의 endpoint chord 제곱은 $h_k^2=2-2u_k\cdot u_{k+1}$다. 최악 chord를 최소화하는 것과

$$
\Phi_{\rm knot}(t_1,\ldots,t_N)
=\min_k\{2+2u_k\cdot u_{k+1}\}
\tag{19zq-bj}
$$

를 최대화하는 것은 같다. 각 stereographic dot product의 exact rational interval enclosure $D_{k,C}$를 계산하면

$$
\sup_C\Phi_{\rm knot}
\le U_C:=\min_k\sup(2+2D_{k,C}).
\tag{19zq-bk}
$$

분모는 양수이고 compact strict-order box에서 연속이므로 exact subdivision enclosure가 점값으로 수렴한다. 따라서 incumbent와 global upper의 차가 $\eta$ 이하이면 전체 연속 knot box의 $\eta$-전역 spacing optimum이다.

**[정리: 선택 spline의 전역 기하 상계]** $\varepsilon_*=\max_k\varepsilon_k$라 하자. unit disk에서 각 factor는 $[0,2]$이고 gradient norm은 1 이하이므로

$$
1\le\rho\le1+\varepsilon_*2^{2m},
\qquad
\|\nabla\rho\|_2\le\varepsilon_*m2^{2m},
\tag{19zq-bl}
$$

$$
C_{\rm spl}^+
=1+\varepsilon_*(1+m)2^{2m}
\tag{19zq-bm}
$$

은 $u\mapsto\rho(u)u$의 global Lipschitz 상계다. 모든 strict minor arc의 점은 한 endpoint knot에서 endpoint-to-endpoint chord 이하 거리에 있으므로, 선택된 최대 chord의 outward square-root $h^+$에 대해 $C_{\rm spl}^+h^+$가 contour-node cover 상계다. □

**[산출·경계]** `verified_continuous_periodic_spline_knot_optimization.py`는 strict cyclic order/minor-arc domain, automatic vanishing order $2(q+1)$, 연속 knot cell의 dot/determinant enclosure, spacing incumbent/upper/gap, 선택 exact directions와 radial/gradient/Lipschitz/cover 상계를 산출한다. 균등 4-arc singleton, dense ordered samples, 임의 $q=0,1,2,3,6,10$, zero-amplitude circle 환원, invalid order·long arc·budget을 검증한다. focused 20/20, 직접 인접 85/85, 무차원·원장 결합 176/176, 전체 연속/구간/contour 사슬 500/500을 통과했다. 이 모듈 자체는 **spline 기하와 knot spacing**만 닫고 `spectral_split_verified=False`를 명시한다. CE-MKSPEC/MKRES/MKINT 후속 정리가 exact diagonalization과 uniform radial envelope 아래에서 명목 resolvent/rank, 정량 norm, supplied interval-matrix ball까지 별도로 닫는다. adaptive amplitude/patch coefficient, defective/no-witness noncircular margin과 empirical objective는 남는다. 기록은 `_workspace/ce/brain-continuous-periodic-spline-knot-optimization-20260826/40-final-report.md`를 따른다.

#### uniform radial envelope로 moving-knot family 전체의 exact rank 이전

앞의 knot optimizer가 주는 family는 knot 위치와 무관하게

$$
0<\rho^-:=1\le\rho_k(u)\le
\rho^+:=1+\varepsilon_*2^{2(q+1)}.
\tag{19zq-bn}
$$

고정 중심 $c$와 orientation-preserving affine 축행렬 $L=[\ell_u,\ell_v]$를 적용한 모든 contour는

$$
\Gamma_\kappa
=\{c+L(\rho_\kappa(u)u):u\in S^1\},
\qquad \kappa\in\mathcal K
\tag{19zq-bo}
$$

로 쓸 수 있다. 여기서 $\mathcal K$는 연속 knot box 전체다. $\rho_\kappa>0$이면 $u\mapsto\rho_\kappa(u)u$는 서로 다른 방향을 같은 점으로 보내지 않으므로 simple star-shaped Jordan curve이고, 가역 affine map도 단순성을 보존한다.

exact diagonalization $UV=V\operatorname{diag}(\lambda_j)$와 frozen labels에 대해

$$
r_j^2:=\|L^{-1}(\lambda_j-c)\|_2^2
\tag{19zq-bp}
$$

를 exact rational로 계산한다. 다음 uniform signed squared margin을 둔다.

$$
m_j^{\rm knot}=
\begin{cases}
(\rho^-)^2-r_j^2,&j\text{ inside},\\
r_j^2-(\rho^+)^2,&j\text{ outside},
\end{cases}
\qquad
m_*^{\rm knot}=\min_jm_j^{\rm knot}.
\tag{19zq-bq}
$$

**[정리: moving-knot family uniform Riesz rank]** $m_*^{\rm knot}>0$이면 모든 $\kappa\in\mathcal K$와 모든 inside label에 대해 $r_j<\rho^-\le\rho_\kappa(u)$이고, 모든 outside label에 대해 $r_j>\rho^+\ge\rho_\kappa(u)$다. 따라서 모든 inside 고유값은 모든 $\Gamma_\kappa$의 내부, outside 고유값은 외부에 있으며 어느 contour도 스펙트럼을 만나지 않는다. 모든 family member의 exact Riesz projector는

$$
P=V\operatorname{diag}(1_{j\text{ inside}})V^{-1}
\tag{19zq-br}
$$

로 동일하고 rank도 frozen inside label 수로 일정하다. 이는 knot cell의 표본점이 아니라 (19zq-bn)의 uniform envelope가 box 전체를 덮기 때문이다. □

**[정리: conditioned uniform resolvent bound]** $f_L^2=\|L\|_F^2$, $d_L=\det L>0$라 쓰면

$$
s_L^-:=\frac{d_L^2}{f_L^2}\le \sigma_{\min}(L)^2.
\tag{19zq-bs}
$$

inside에는 $b_j=\rho^-$, outside에는 $b_j=\rho^+$를 놓고 (19zq-bp)의 signed squared margin을 $m_j$라 하면, reverse triangle inequality와 $(r_j+b_j)^2\le2(r_j^2+b_j^2)$에서

$$
d_j^2:=\frac{m_j^2}{2(r_j^2+b_j^2)}
\le \inf_{\kappa,u}\left|\rho_\kappa(u)u-L^{-1}(\lambda_j-c)\right|^2.
\tag{19zq-bt}
$$

따라서 $\delta_*^2=s_L^-\min_jd_j^2>0$는 affine image contour와 모든 고유값 사이의 normalized physical distance 제곱 하계다. exact $\widetilde U=V\Lambda V^{-1}$에 대해 모든 knot-box contour와 그 위의 모든 $z$에서

$$
\left\|(zI-\widetilde U)^{-1}\right\|_2^2
\le
\frac{\|V\|_F^2\|V^{-1}\|_F^2}{\delta_*^2}.
\tag{19zq-bu}
$$

즉 고유값 거리만 쓴 것이 아니라 affine 최소 특이값과 eigenvector conditioning을 모두 포함한다. 비정규 행렬에서 $V$의 조건수를 빼면 이 결론은 거짓이다. □

**[산출·경계]** `verified_moving_knot_spline_spectral_rank_bridge.py`는 knot optimization receipt, normalized affine inverse 좌표 제곱, uniform radial inner/outer bound, 각 고유값 signed margin, affine singular-value·contour-distance 하계, eigenvector Frobenius conditioning, self-checked dyadic resolvent norm 상계, exact oblique projector/idempotence/commutation과 rank를 산출한다. identity·general-affine·scale·oblique conditioning, inner/outer equality, wrong label/witness, knot budget, rank 0/full을 focused fixture로 검증한다. 이 명목 모듈 자체의 `interval_matrix_family_verified=False`는 바로 다음 독립 MKINT successor가 supplied Frobenius ball에 대해 닫는다. adaptive amplitude/coefficient, defective/no-witness spline과 empirical objective는 남는다. 기록은 `_workspace/ce/brain-moving-knot-spline-spectral-rank-bridge-20260826/40-final-report.md`를 따른다.

**[정리: moving-knot interval-matrix bridge]** normalized matrix family를 $\widetilde U_E=\widetilde U+E$, $\|E\|_F\le\varepsilon^+$라 하자. (19zq-bu)의 norm 상계를 $R^+$라 쓰고

$$
\nu^+:=R^+\varepsilon^+<1
\tag{19zq-bv}
$$

을 요구한다. 그러면 모든 $t\in[0,1]$, 모든 knot-box member와 contour point에서

$$
zI-(\widetilde U+tE)
=\{I-tE(zI-\widetilde U)^{-1}\}(zI-\widetilde U)
$$

가 Neumann 급수로 가역이고

$$
\left\|(zI-\widetilde U_E)^{-1}\right\|_2
\le \frac{R^+}{1-\nu^+}.
\tag{19zq-bw}
$$

따라서 $tE$ homotopy 동안 Riesz rank가 변하지 않는다. 또한 $C_{\rm spl}^+$를 radial Lipschitz 상계라 하면 $\mathcal L/(2\pi)\le\|L\|_F C_{\rm spl}^+$이고 resolvent identity에서

$$
\|P(\widetilde U_E)-P(\widetilde U)\|_2
\le
\|L\|_F^+C_{\rm spl}^+
\frac{\varepsilon^+(R^+)^2}{1-\nu^+}.
\tag{19zq-bx}
$$

이 결과는 supplied Frobenius ball 전체와 moving-knot box 전체를 동시에 덮지만, 그 ball이 실제 추정오차를 통계적으로 덮는다는 뜻은 아니다. □

**[산출·경계]** `verified_interval_moving_knot_spline_spectral_rank_bridge.py`는 normalized uncertainty, Neumann product/margin, perturbed resolvent, contour-length-over-$2\pi$, projector perturbation과 interval-family rank 영수증을 산출한다. equality/failure, oblique conditioning, scale covariance, zero uncertainty를 focused 10개 fixture로 검사한다. defective/no-witness, empirical coverage와 4–6차원 선택은 여전히 거짓으로 둔다. 기록은 `_workspace/ce/brain-interval-moving-knot-spline-spectral-rank-bridge-20260826/40-final-report.md`를 따른다.

#### defective Jordan block을 허용하는 conformal moving-knot 부분류

일반 shear-affine $L$은 $L^{-1}$가 복소선형 행렬 함수가 아니므로 다음 정리를 그대로 적용할 수 없다. 여기서는 $L=sR_\theta$, $s>0$인 conformal affine 부분류를 고정한다. exact projector $P^2=P$, $PU=UP$, $Q=I-P$와 complement-supported two-sided inverse

$$
R_Q=Q\{Q(\widetilde U-cI)Q\}^{-1}Q
$$

를 공급하고

$$
a^+:=\|(\widetilde U-cI)P\|_2^+,qquad
b^+:=\|R_Q\|_2^+
\tag{19zq-by}
$$

라 하자.

**[정리: defective conformal moving-knot split]** 다음 두 strict gate

$$
g_-:=s\rho^- -a^+>0,qquad
g_+:=1-s\rho^+b^+>0
\tag{19zq-bz}
$$

가 성립하면 $P$-block의 모든 고유값은 $|\lambda-c|<s\rho^-$이고 $Q$-block의 모든 고유값은 $|\lambda-c|>s\rho^+$다. 첫 결론은 spectral radius가 operator norm 이하라는 사실, 둘째는 inverse block의 spectral radius가 $b^+$ 이하라는 사실에서 따른다. 따라서 diagonalization 가능성과 무관하게 모든 moving-knot contour가 동일한 exact Riesz projector $P$와 rank $\operatorname{tr}P$를 갖는다. 특히 $P$-block은 Jordan block이어도 된다. □

**[정리: algebraic resolvent bound]** $p^+=\|P\|_2^+$라 하면 block Neumann series로 모든 family contour에서

$$
\|(zI-\widetilde U)^{-1}\|_2
\le \frac{p^+}{g_-}+\frac{b^+}{g_+}.
\tag{19zq-ca}
$$

첫 항은 내부 block에 대해 $|(z-c)|\ge s\rho^-$를, 둘째 항은 외부 block에 대해 $|(z-c)|\le s\rho^+$를 사용한다. 비직교 projector의 norm $p^+$를 생략하지 않는다. □

**[산출·경계]** `verified_defective_conformal_moving_knot_spline_bridge.py`는 CE-KOPT geometry와 exact algebraic projector 영수증을 합성해 inner/outer gate, projector norm, algebraic resolvent, defective rank를 산출한다. Jordan block, 회전, equality, 잘못된 projector/inverse, scale covariance를 focused 9개 fixture로 검증한다. `diagonalization_witness_required=False`지만 exact projector/inverse witness는 여전히 필요하고 `general_shear_affine_verified=False`다. 기록은 `_workspace/ce/brain-defective-conformal-moving-knot-spline-bridge-20260826/40-final-report.md`를 따른다.

**[정리: defective interval successor]** (19zq-ca)의 상계를 $R_{\rm alg}^+$라 하고 $\|E\|_F\le\varepsilon^+$, $R_{\rm alg}^+\varepsilon^+<1$이라 하자. 그러면 DEFCON의 defective nominal matrix에 diagonalization을 추가하지 않고도 모든 $tE$와 moving contour에서 resolvent가 존재하고 rank가 보존된다. 또한 conformal 길이 상계 $\mathcal L/(2\pi)\le sC_{\rm spl}^+$로

$$
\|P(U+E)-P(U)\|_2
\le sC_{\rm spl}^+
\frac{\varepsilon^+(R_{\rm alg}^+)^2}
{1-R_{\rm alg}^+\varepsilon^+}.
\tag{19zq-cb}
$$

**[산출·경계]** `verified_interval_defective_conformal_moving_knot_spline_bridge.py`는 defective algebraic receipt를 strict Neumann ball에 합성한다. exact equality/failure, nominal failure, scale covariance, zero uncertainty를 focused 9/9로 검사한다. 일반 shear와 empirical coverage는 여전히 제외된다. 기록은 `_workspace/ce/brain-interval-defective-conformal-moving-knot-spline-bridge-20260826/40-final-report.md`를 따른다.

**[정리·구성: automatic defective witness discovery]** CE-KOPT envelope에서

$$
r_{\rm ref}=s\frac{\rho^-+\rho^+}{2}
\tag{19zq-cc}
$$

를 자동 구성한다. exact characteristic polynomial을 완전 $\mathbb Q$-인수분해하고 $r_{\rm ref}$ 안/밖 primary atom의 유일한 partition을 찾는다. 서로소 inside/outside factor의 Bézout 항등식을 행렬에 평가하면 exact commuting projector $P$가 생기고, $Q(U-cI)Q$를 exact inversion하여 $R_Q$를 만든다. 이 영수증이 DEFCON의 (19zq-bz)를 통과하면 supplied projector, supplied inverse, eigenvector와 diagonalization 없이 moving-knot rank와 (19zq-ca)의 resolvent 상계를 얻는다. repeated factor는 multiplicity를 보존하므로 Jordan block을 잘못 서로 다른 고유벡터로 분해하지 않는다. □

**[산출·경계]** `verified_automatic_defective_conformal_moving_knot_spline_bridge.py`는 knot envelope→reference circle→complete characteristic factorization→unique partition→Bézout projector/inverse→DEFCON을 합성한다. defective repeated root, irreducible quadratic, budget, contour crossing과 scale을 focused 8/8로 검증한다. general shear와 empirical coverage는 여전히 제외된다. 기록은 `_workspace/ce/brain-automatic-defective-conformal-moving-knot-spline-bridge-20260826/40-final-report.md`를 따른다.

#### general-affine shear defective sandwich

이제 $L$을 임의의 orientation-preserving invertible real $2\times2$ affine frame으로 둔다. exact dyadic bounds

$$
\sigma_L^-\le\sigma_{\min}(L),qquad
S_L^+\ge\|L\|_2,qquad
(\sigma_L^-)^2\le\frac{\det(L)^2}{\|L\|_F^2},\quad
S_L^+\ge\|L\|_F
\tag{19zq-cd}
$$

를 self-check한다. 모든 affine radial contour의 내부는 반지름 $\sigma_L^-\rho^-$인 Euclidean disk를 포함하고 전체 contour는 반지름 $S_L^+\rho^+$인 disk 안에 있다.

**[정리: general-affine defective block gate]** exact commuting $P$, complement inverse $R_Q$에 대해

$$
g_-^{aff}=\sigma_L^-\rho^- -\|(U-cI)P\|_2^+>0,qquad
g_+^{aff}=1-S_L^+\rho^+\|R_Q\|_2^+>0
\tag{19zq-ce}
$$

이면 shear 여부와 무관하게 $P$-block은 모든 contour 내부, $Q$-block은 외부다. 따라서 defective Jordan block을 포함해 exact projector와 rank가 보존되고

$$
\sup_{\kappa,z\in\Gamma_\kappa}\|(zI-U)^{-1}\|_2
\le
\frac{\|P\|_2^+}{g_-^{aff}}+
\frac{\|R_Q\|_2^+}{g_+^{aff}}.
\tag{19zq-cf}
$$

이는 실제 ellipse 좌표의 정밀 root localization보다 보수적이지만 general shear를 제거하지 않는 엄밀한 충분조건이다. □

**[산출·경계]** `verified_defective_general_affine_moving_knot_spline_bridge.py`는 axes/determinant/Frobenius, dyadic singular sandwich, algebraic gaps, defective rank와 resolvent를 산출한다. shear Jordan fixture, exact equality, orientation, bad witness, scale을 focused 9/9로 검증한다. 기록은 `_workspace/ce/brain-defective-general-affine-moving-knot-spline-bridge-20260826/40-final-report.md`를 따른다.

**[정리·구성: automatic interval general-shear defective bridge]** (19zq-cd)의 inner/outer radius 중점을 reference circle로 잡고 complete characteristic factorization과 unique primary partition으로 $P,R_Q$를 자동 생성한다. 생성 영수증이 (19zq-ce)를 통과해 (19zq-cf)의 $R_{aff}^+$를 내고, $\|E\|_F\le\varepsilon^+$와

$$
R_{aff}^+\varepsilon^+<1
\tag{19zq-cg}
$$

을 요구하면 shear defective interval family 전체의 rank가 보존된다. $\mathcal L/(2\pi)\le S_L^+C_{spl}^+$이므로

$$
\|P(U+E)-P(U)\|_2
\le S_L^+C_{spl}^+
\frac{\varepsilon^+(R_{aff}^+)^2}{1-R_{aff}^+\varepsilon^+}.
\tag{19zq-ch}
$$

따라서 exact-rational admitted class에서는 eigenvectors, diagonalization, supplied projector와 supplied inverse 없이 general shear와 deterministic uncertainty를 함께 처리한다. □

**[산출·경계]** `verified_automatic_interval_defective_general_affine_moving_knot_spline_bridge.py`는 singular sandwich→characteristic discovery→GADEF→Neumann interval/projector를 합성한다. automatic shear Jordan, equality, budget, zero uncertainty, scale을 focused 8/8로 검증한다. 경험적 coverage와 4–6차원 선택은 포함하지 않는다. 기록은 `_workspace/ce/brain-automatic-interval-defective-general-affine-moving-knot-spline-bridge-20260826/40-final-report.md`를 따른다.

#### continuous amplitude-box optimization

각 patch amplitude를 독립 exact interval $\epsilon_k\in[\ell_k,u_k]$, $0\le\ell_k\le u_k$로 확장한다. $m=q+1$이고 radial cap $\rho_{cap}\ge1$을 고정하면

$$
\epsilon_{cap}=\frac{\rho_{cap}-1}{2^{2m}}.
\tag{19zq-ci}
$$

**[정리: separable global amplitude optimum]** admissibility의 필요충분조건은 모든 $k$에 대해 $\ell_k\le\epsilon_{cap}$이고, 목적함수 $J_\epsilon=\sum_k\epsilon_k$를 최대화하는 exact 전역해는

$$
\epsilon_k^*=\min(u_k,\epsilon_{cap}).
\tag{19zq-cj}
$$

목적함수가 각 좌표에 단조 증가하고 제약이 좌표별 box와 공통 upper cap뿐이므로 증명은 좌표별 endpoint 선택으로 끝난다. 선택 subbox $[\ell_k,\epsilon_k^*]$ 전체에서 endpoint vanishing order $2m$과 automatic periodic $C^q$ 접합은 amplitude와 무관하게 유지된다. 또한 $\epsilon_*:=\max_k\epsilon_k^*$에 대해

$$
1\le\rho\le1+\epsilon_*2^{2m}\le\rho_{cap},quad
\|\nabla\rho\|\le\epsilon_*m2^{2m},quad
C_{spl}^+\le1+\epsilon_*(1+m)2^{2m}.
\tag{19zq-ck}
$$

**[산출·경계]** `verified_continuous_periodic_spline_amplitude_optimization.py`는 original/selected box, exact cap, global objective equality, radial/gradient/Lipschitz와 knot geometry를 산출한다. cap clipping, arbitrary $q$, infeasible lower, zero/large cap, knot budget을 focused 10/10으로 검증한다. 이 단계 자체는 geometry/amplitude 최적화이며 `spectral_split_verified=False`다. 기록은 `_workspace/ce/brain-continuous-periodic-spline-amplitude-optimization-20260826/40-final-report.md`를 따른다.

#### general coefficient-vector optimization with automatic junctions

단일 patch amplitude를 유한 coefficient vector로 확장한다. 앞의 automatic-junction patch에서 사용한 비음수 base bump를 $b_k(\theta)$라 쓰면, knot box 전체에서 $0\le b_k\le4$이고 양 끝에서 적어도 $m=q+1$차로 사라진다. 서로 다른 유한 정수 $p_r\ge m$과 비음수 계수 상자 $a_{kr}\in[\ell_{kr},u_{kr}]$를 두고

$$
\rho_k(\theta)=1+\sum_{r=1}^{R}a_{kr}b_k(\theta)^{p_r}.
\tag{19zq-ck1}
$$

로 정의한다. 각 $b_k^{p_r}$는 양 끝에서 $p_r\ge q+1$차로 사라지므로, 모든 coefficient와 moving-knot 선택에 대해 공통 endpoint jet은 여전히 $(1,0,\ldots,0)$이다. 따라서 periodic $C^q$ 접합은 coefficient 최적화와 독립적으로 자동 유지된다.

**[정리: coefficient box의 exact 선형 최적화]** frozen 비음수 rational weight $w_{kr}$에 대해

$$
J_a=\sum_{k,r}w_{kr}a_{kr}
\tag{19zq-ck2}
$$

를 최대화하고 radial cap $\rho_{cap}\ge1$을 요구하자. 충분한 patch별 제약은

$$
\sum_r4^{p_r}a_{kr}\le \rho_{cap}-1.
\tag{19zq-ck3}
$$

이다. lower corner의 비용이 cap을 넘으면 infeasible이다. 그렇지 않으면 각 patch에서 비율 $w_{kr}/4^{p_r}$이 큰 순서로 upper bound까지 채우고, 마지막 mode만 남은 용량만큼 분수로 채운다. 이는 연속 bounded fractional-knapsack의 교환 논증으로 exact 전역해다. 즉 낮은 비율 mode에 양의 여유가 있고 더 높은 비율 mode가 upper에 도달하지 않았다면, 같은 radial 비용을 높은 비율 쪽으로 옮겨 목적함수를 엄격히 증가시킬 수 있다. 이 교환이 더 불가능한 점이 위 greedy 해이며 모든 patch 제약과 목적함수가 분리되므로 전체 전역해다. □

선택된 whole subbox $[\ell_{kr},a^*_{kr}]$에는

$$
1\le\rho\le1+\max_k\sum_r4^{p_r}a^*_{kr},\qquad
|\partial_\theta\rho|\le\max_k\sum_rp_r4^{p_r}a^*_{kr}
\tag{19zq-ck4}
$$

의 uniform envelope를 사용한다. 이 bound는 날카롭다고 주장하지 않지만 exact rational이고 coefficient 수와 차수를 명시적으로 보존한다.

**[산출·경계]** `verified_continuous_periodic_spline_coefficient_optimization.py`는 powers, coefficient boxes, objective weights, radial/gradient basis weights, fractional-knapsack 선택점과 whole selected subbox, exact objective equality, knot/junction 영수증을 산출한다. powers 2/3과 4/7, cap infeasibility, zero/full corner, knot budget을 focused 10/10으로 검증한다. 이는 비음수 automatic-jet basis의 일반 coefficient geometry를 닫지만 signed coefficient, 임의 equality-constrained polynomial basis, spectral/defective 합성, empirical objective는 아직 별도다. 기록은 `_workspace/ce/brain-continuous-periodic-spline-coefficient-optimization-20260826/40-final-report.md`를 따른다.

**[정리: spectral-derived amplitude cap]** exact diagonalization과 frozen labels 아래 각 고유값의 affine inverse radius 제곱을 $r_j^2=\|L^{-1}(\lambda_j-c)\|^2$라 한다. outside radius마다 self-checked dyadic lower $r_j^-$를 만들고 사전 고정 safety $\mu_\rho>0$, ceiling $\rho_{ceil}\ge1$에 대해

$$
\rho_{cap}^{spec}
=\min\left\{\rho_{ceil},\min_{j\in out}r_j^- -\mu_\rho\right\},
\tag{19zq-cl}
$$

outside label이 없으면 두 번째 항을 생략한다. 모든 inside label에는 $r_j^2<1$을 요구한다. $\rho_{cap}^{spec}\ge1$이면 (19zq-ci)–(19zq-cj)로 얻은 amplitude optimum과 선택 subbox 전체에서 inside는 $r_j<1\le\rho$, outside는 $\rho\le\rho_{cap}^{spec}<r_j$다. 따라서 amplitude box×knot box 전체의 exact projector/rank와 conditioned resolvent가 동일하다. □

**[산출·경계]** `verified_spectral_spline_amplitude_optimization.py`는 affine radii, dyadic outside lower, safety-derived cap, AOPT optimum/subbox와 MKSPEC projector/rank/resolvent를 합성한다. general affine, full rank, inside/safety failure, oblique conditioning, scale와 knot budget을 focused 9/9로 검증한다. 기록은 `_workspace/ce/brain-spectral-spline-amplitude-optimization-20260826/40-final-report.md`를 따른다.

**[정리·구성: defective algebraic amplitude cap]** zero-amplitude unit-core에서 AIGADEF characteristic discovery로 exact $P,R_Q$를 자동 생성한다. $b^+=\|R_Q\|_2^+$, predeclared exterior safety $0<\mu_{out}<1$에 대해

$$
\rho_{cap}^{alg}
=\min\left\{\rho_{ceil},\frac{1-\mu_{out}}{S_L^+b^+}\right\}
\tag{19zq-cm}
$$

을 정의한다. $\rho_{cap}^{alg}\ge1$이면 AOPT의 선택 amplitude box 전체에서 GADEF exterior gap은 적어도 $\mu_{out}$이고 inside unit-core gate는 amplitude와 무관하게 유지된다. 최종 algebraic resolvent를 $R_{alg}^+$라 하고 matrix uncertainty가 $R_{alg}^+\varepsilon^+<1$을 만족하면 amplitude×knot×matrix product family 전체의 rank와 projector perturbation까지 보존된다. 따라서 shear와 defective block을 허용하면서 eigenvalues, eigenvectors, diagonalization, supplied $P,R_Q$ 없이 amplitude 전역 최적화를 수행한다. □

**[산출·경계]** `verified_defective_algebraic_spline_amplitude_optimization.py`는 zero-amplitude discovery, algebraic cap, AOPT, final GADEF, interval Neumann/projector를 합성한다. safety, amplitude box, interval equality, budget, zero uncertainty, scale를 focused 9/9로 검증한다. 기록은 `_workspace/ce/brain-defective-algebraic-spline-amplitude-optimization-20260826/40-final-report.md`를 따른다.

반례가 이 경계를 설명한다. contour가 고유값을 지나면 resolvent와 (29)는 정의되지 않는다. $U=\begin{pmatrix}0&M\\0&1\end{pmatrix}$에서는 고유값 거리만 양수여도 $M$에 따라 resolvent가 커져 pseudospectral 불안정성이 생긴다. 또 $U=(0.9)$와 단위원에서는 정확한 $P=1$이지만 $P_N=(1-0.9^N)^{-1}$이므로, contour가 안전해도 조악한 $N$은 비멱등 근사를 낼 수 있다. 그러므로 sampled gap, sampled rank, 한 번의 $P_N$을 정확한 Riesz rank 증거로 승격하지 않는다.

