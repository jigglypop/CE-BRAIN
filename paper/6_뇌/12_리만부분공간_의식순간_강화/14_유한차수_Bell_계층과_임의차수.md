# 14. C5 이상을 묶는 유한차수 Bell 계층과 임의 유한차수

## C5 이상을 한 식으로 묶는 유한차수 Bell 계층

C4 다음의 식을 손으로 계속 나열하면 계수 누락 가능성이 급격히 커진다.
예를 들어 C5에는 7종, C6에는 11종의 정수분할 형태가 나타난다. 따라서
아핀 삼각형 경로에서는 모든 유한 차수를 하나의 정수분할 식으로 묶는다.

차수 $n$에 대해

$$
\mathfrak P_n=\left\{(m_1,\ldots,m_n):m_j\in\mathbb N_0,
\ \sum_{j=1}^n j m_j=n\right\}
$$

라 하고 $|m|=\sum_jm_j$로 쓰자. 같은 크기의 block들이 서로 구별되지
않음을 반영한 정확한 조합계수는

$$
C_n(m)=\frac{n!}{\prod_{j=1}^n(j!)^{m_j}m_j!}
\tag{83}
$$

이다. $R_1=1+\kappa$, $R_j=\Lambda_j$로 두고, 최고 graph 미분 하나만
들어가는 분할 $e_n=(0,\ldots,0,1)$을 따로 떼면

$$
A_n=q\Lambda_n+
\sum_{m\in\mathfrak P_n\setminus\{e_n\}}
C_n(m)K_{|m|}\prod_{j=1}^nR_j^{m_j}.
\tag{84}
$$

아핀 역좌표에서는

$$\Lambda_{n,\mathrm{out}}=\mu^nA_n.$$

**[정리: 아핀 삼각형 임의 유한 Cn class]** 통과한 C4 전임과 각 유한
차수까지의 graph·지도 미분 상계가 주어지고 식 (84)가 모든 추가 차수의
class를 보존하면 선언한 최대차수 $n$까지 graph class가 보존된다.

두 graph 사이의 $k$차 미분 거리를 $\Delta_k$, 값 거리를 $\Delta_0$라
하면

$$
\Delta_n'\le\sum_{k=0}^n a_{n,k}\Delta_k,
\qquad a_{n,n}=q\mu^n.
\tag{85}
$$

$1\le k<n$의 교차계수는

$$
a_{n,k}=\mu^n\sum_{m\ne e_n}C_n(m)K_{|m|}m_k
R_k^{m_k-1}\prod_{j\ne k}R_j^{m_j},
\tag{86}
$$

값 계수는

$$
a_{n,0}=\mu^n\left[K_2\Lambda_n+
\sum_{m\ne e_n}C_n(m)K_{|m|+1}\prod_jR_j^{m_j}\right].
\tag{87}
$$

식 (87)은 왜 $K_{n+1}$이 필요한지를 분명히 한다. 모든 block이 크기
1인 분할은 $|m|=n$이므로 지도 $D^n g$를 서로 다른 graph 값에서 비교할
때 다음 모듈러스 $K_{n+1}$이 필요하다. 이 상수는 한 graph의 Cn 반지름과
$k\ge1$ 계수에는 들어가지 않고 값 계수 $a_{n,0}$에만 들어간다.

**[정리: 유한 (n+1)층 뭉침]** 모든 하위 class와 엄격한
$q\mu^k<1$이 $k\le n$에서 성립하면 식 (85)의 유한 비음수 상삼각
재귀가 수렴하여 불변 graph는 Cn이다.

$n=4$에서 식 (83)의 분할계수는 정확히 $1,6,4,3,1$이며, 재배열하면
앞서 얻은 $1,4,3,6,1$ 연쇄식과 네 교차계수를 그대로 복원한다. 기준
fixture에서는

$$
\Lambda_{5,\mathrm{out}}=\frac{133}{4},\qquad
\Lambda_{6,\mathrm{out}}=\frac{2283}{8}.
$$

경계 반례도 모든 유한 차수에서 한 family로 쓸 수 있다. $a>1$에 대해
$x'=x/a$, $y'=y/a^n$로 놓으면

$$h_c(x)=c\max(x,0)^n$$

은 $h_c(x/a)=h_c(x)/a^n$을 만족한다. 이 함수는 C(n-1)이지만 원점의
n차 좌우 미분이 $0$과 $cn!$로 다르다. 따라서 $q\mu^n=1$은 Cn을
강제하지 못한다.

**[미완성]** 여기서 “임의”는 사용자가 유한한 최대차수와 그때까지의
상계열을 제공하면 동일 알고리즘이 작동한다는 뜻이다. $C^\infty$,
analytic, Gevrey 정칙성에는 차수 전체의 성장률과 수렴반경이 별도로
필요하다. 또한 비아핀·결합·local/matched 임의차수 계층은 아직
재귀적 역함수 Bell 다항식으로 올리지 않았다.

정식 증명과 검증 기록은
`_workspace/ce/brain-affine-triangular-arbitrary-order-graph-transform-20260825/40-final-report.md`를 따른다.

## 공통 역좌표가 휜 경우의 임의 유한차수

아핀 Bell 계층에서 빠진 것은 역좌표 자체의 고차 미분이다. 공통 역함수
$\psi=\phi^{-1}$를 사용하는 비아핀 삼각형에서는 이 미분들도 같은
정수분할 구조로 생성할 수 있다.

$I_1=\mu$, $\Phi_k\ge\|D^k\phi\|$라 하자. 항등식
$\phi\circ\psi=I$를 $n$번 미분하고 $D\phi D^n\psi$ 항을 분리하면

$$
I_n=\mu\sum_{m\in\mathfrak P_n\setminus\{e_n\}}
C_n(m)\Phi_{|m|}\prod_{j=1}^{n-1}I_j^{m_j}.
\tag{88}
$$

첫 세 비자명한 층은

$$I_2=\Phi_2\mu^3,$$

$$I_3=\Phi_3\mu^4+3\Phi_2^2\mu^5,$$

$$
I_4=\Phi_4\mu^5+10\Phi_2\Phi_3\mu^6+15\Phi_2^3\mu^7.
$$

즉 앞에서 따로 적었던 $\nu,\tau,\upsilon$이 하나의 역함수 Bell 재귀의
첫 항들이 된다. 전방 기저지도 상계로 계산한 $I_1$--$I_4$가 기존 C4
인증서와 일치하지 않으면 후속 계층은 fail-closed 한다.

이제 $A_b$를 역좌표 적용 전 $S_h=Bh+g\circ(I,h)$의 $b$차 상계,
$\Delta A_b$를 그 전체 graph 차분 vector라 하자. 공통 역함수는 두
graph에서 같으므로

$$
\Lambda_{n,\mathrm{out}}^{\mathrm{na}}
=\sum_{m\in\mathfrak P_n}C_n(m)A_{|m|}
\prod_{j=1}^nI_j^{m_j},
\tag{89}
$$

$$
\Delta_n'\preceq
\sum_{m\in\mathfrak P_n}C_n(m)
\left(\prod_jI_j^{m_j}\right)\Delta A_{|m|}.
\tag{90}
$$

**[정리: 공통 역상 비아핀 임의 유한 Cn]** 일관된 전방 기저·graph·지도
상계열, 모든 class 보존과 엄격한 $q\mu^k<1$ 아래에서 식 (88)--(90)은
명시된 모든 유한차수까지 Cn graph와 유한 상삼각 수렴을 보장한다.

$n=4$에서는 식 (89)--(90)이 앞의 비아핀 C4 반지름과 다섯 재귀계수를
정확히 복원한다. 모든 $\Phi_k=0$, $\mu=1$이면 $I_k=0$ $(k\ge2)$가 되어
모든 차수에서 아핀 Bell 계층으로 항별 환원된다. 따라서 아핀 부분족의
$c\max(x,0)^n$ 경계 반례가 더 큰 비아핀 class에서도 뭉침 등호를 막는다.

기준 곡률 fixture에서는

$$
I_5=\frac{488600}{129140163},\qquad
I_6=\frac{3797600}{1162261467},
$$

$$
\Lambda_{5,\mathrm{out}}^{\mathrm{na}}
=\frac{116441578775}{43046721},\qquad
\Lambda_{6,\mathrm{out}}^{\mathrm{na}}
=\frac{75171452147900}{387420489}.
$$

**[미완성]** graph마다 역상이 달라지는 결합형에서는 식 (90)에 역함수
차분도 들어가므로 이 공통-역상 정리를 직접 사용할 수 없다. 그 경우에는
implicit inverse와 수정 tensor의 재귀 Bell 대수가 추가로 필요하다.
local/matched 임의차수와 $C^\infty$/analytic 성장률도 아직 별도 과제다.

정식 증명과 검증 기록은
`_workspace/ce/brain-nonaffine-triangular-arbitrary-order-graph-transform-20260825/40-final-report.md`를 따른다.

