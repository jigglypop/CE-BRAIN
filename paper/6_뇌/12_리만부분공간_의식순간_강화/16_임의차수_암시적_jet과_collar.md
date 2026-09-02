# 16. 그래프 의존 역상의 임의차수 암시적 jet 재귀와 local/matched collar

## 그래프마다 역상이 달라질 때의 임의차수 암시적 jet 재귀

앞 절의 공통 역상 비아핀 계층은 두 그래프가 같은 역좌표를 쓰는 경우다.
결합 기저에서는 그래프 (h)가 바뀌면 기저 사상 (F_h)도 바뀌므로,
새 그래프 (T_h)는 직접 합성식으로 주어지지 않고

$$
Y_h=T_h\circ F_h
$$

라는 암시적 항등식으로 정해진다. 여기서 중요한 것은 지도별 미분항을
무작정 전개하는 것보다, 모든 차수에 공통인 역해법을 먼저 분리하는
일이다.

정수분할 (m=(m_1,ldots,m_n))에 대해

$$
\sum_{j=1}^n jm_j=n,
\qquad |m|=\sum_{j=1}^n m_j,
\qquad
C_n(m)=\frac{n!}{\prod_{j=1}^n(j!)^{m_j}m_j!}
$$

로 놓으면 유한차수 Faà di Bruno 식은

$$
D^nY_h=
\sum_{m\in\mathfrak P_n}C_n(m)
D^{|m|}T_h\prod_{j=1}^n(D^jF_h)^{m_j}
$$

이다. 이때 미지의 최고차 항 (D^nT_h)를 싣는 분할은

$$
s_n=(n,0,\ldots,0)
$$

이다. 즉 (DF_h)가 들어가는 한 점 블록이 (n)개인 항이다. 반대로
((0,ldots,0,1))은 이미 아는 (DT_hD^nF_h) 항이다. 이 둘을 바꾸면
임의차수 역재귀 전체가 잘못된다.

(operatorname{conorm}(DF_h)ge\alpha>0)이고 (F_j,Y_j,X_j)가 각각
(D^jF_h,D^jY_h,D^jT_h)의 정규화 노름 상계라고 하자. 그러면

$$
B_n=Y_n+
\sum_{m\in\mathfrak P_n\setminus\{s_n\}}C_n(m)
X_{|m|}\prod_{j=1}^nF_j^{m_j},
\qquad
\boxed{X_n\le\alpha^{-n}B_n}
$$

을 얻는다. 남은 모든 분할은 (|m|<n)이므로 이는 진짜 재귀다. 처음
세 층은 다음처럼 기존 C2--C4 전개를 정확히 복원한다.

$$
B_2=Y_2+X_1F_2,
$$

$$
B_3=Y_3+3X_2F_1F_2+X_1F_3,
$$

$$
B_4=Y_4+6X_3F_1^2F_2+3X_2F_2^2
+4X_2F_1F_3+X_1F_4.
$$

두 그래프의 차이를 계산할 때는 곱의 각 슬롯을 한 번씩 바꾸는
telescoping을 적용한다. (delta F_j,delta Y_j,delta X_j)를
(Delta_0,ldots,Delta_j)에 대한 비음수 계수행으로 보면

$$
\delta B_n=\delta Y_n+
\sum_{m\ne s_n}C_n(m)\left[
(\delta X_{|m|})\prod_jF_j^{m_j}
+X_{|m|}\sum_jm_j(\delta F_j)F_j^{m_j-1}
\prod_{\ell\ne j}F_\ell^{m_\ell}
\right].
$$

여기에

$$
DF_h^{-1}-DF_k^{-1}
=DF_h^{-1}(DF_k-DF_h)DF_k^{-1}
$$

을 쓰고 역미분 텐서의 (n)개 슬롯을 다시 telescoping하면

$$
\boxed{
\delta X_n\preceq
\alpha^{-n}\delta B_n
+nB_n\alpha^{-(n+1)}\delta F_1
}
$$

을 얻는다. 두 번째 항이 바로 그래프별 역상이 달라질 때 생기는
보정이다. 공통 역상 계층에서는 (delta F_1=0)이어서 이 항이
사라진다. 귀납 가정으로 낮은 차수의 (delta X_b) 행이 주어지면,
곱 telescoping은 (delta B_n)의 모든 항을 만들고 역슬롯 항이 마지막
누락분을 채우므로 전체 상삼각 재귀가 닫힌다.

단, 현재 닫힌 것은 이 **암시적 대수 층**이다. 실제 결합 지도에서
(F_j,Y_j,delta F_j,delta Y_j)를 모든 차수에 대해 산출하는
map-specific raw-jet 생성기는 아직 별도 증명이 필요하다. 따라서 이를
곧바로 “그래프 의존 결합 (C^n) 정리 완성”이라고 부르지 않는다.
(F_j=0 (j\ge2)), (F_1=\alpha)이면 모든 차수에서
(X_n=Y_n/\alpha^n)으로 환원되고, 대각계수 (\beta_n=1)이면 엄격
수축이 아니므로 경계는 실패로 처리된다. 유한한 (n)의 성공은
(C^\infty), analytic, Gevrey 성장률도 뜻하지 않는다.

이 결과 역시 입력 기저 차원을 보존할 뿐 4--6차원을 선택하지 않는다.
따라서 제안된 “고차원 세계 상태가 순간적으로 저차원 의식 부분공간에
집중된다”는 해석에서, 이번 진전은 좌표 접힘의 고차 미분 일관성을
강화한 것이다. 인간 의식이 실제로 4--6차원이라는 실증 결론은 아니다.

조건부 암시적 jet 확장은 `_workspace/ce/brain-coupled-arbitrary-order-implicit-jet-20260825/40-final-report.md`를 따른다.

## 결합 지도에서 raw jet을 실제로 만드는 식

앞 절은 (F_j,Y_j,delta F_j,delta Y_j)가 주어졌을 때의 보편
역재귀였다. 이제 결합 지도를

$$
F_h=f\circ G_h,\qquad Y_h=g\circ G_h,\qquad G_h=(I,h)
$$

로 두고 이 네 입력을 지도 modulus로부터 만든다. 같은 출력점 (z)의
두 역상점을 (x_h,x_k)라 하고

$$
F_h(x_h)=F_k(x_k)=z,
\qquad |x_h-x_k|\le r_x\Delta_0
$$

를 가정한다. 곱노름에서 graph embedding의 jet 반경은

$$
R_1=1+\Lambda_1,\qquad R_j=\Lambda_j\quad(j\ge2)
$$

이다. 두 상태점의 거리는

$$
|G_h(x_h)-G_k(x_k)|
\le S_0\Delta_0,\qquad
S_0=1+(1+\Lambda_1)r_x
$$

로 제어된다. 또한 (D^jh)를 서로 다른 역상점에서 비교해야 하므로

$$
\boxed{
\delta R_j\preceq
\Delta_j+\Lambda_{j+1}r_x\Delta_0
}
$$

가 필요하다. 여기서 (Lambda_{n+1})는 고전적 (D^{n+1}h)가 아니라
(D^nh)의 Lipschitz modulus여도 충분하다. 따라서 결합 (C^n) 차분
정리에서 이 한 단계 높은 점변동 상계를 빼는 축약은 허용되지 않는다.

일반 지도 (a)에 대해 (K_bge|D^ba|),
(H_bgeoperatorname{Lip}(D^ba))라 하자. 그러면
(A_h=a\circ G_h)의 raw jet 크기는

$$
\boxed{
A_n=
\sum_{m\in\mathfrak P_n}C_n(m)K_{|m|}
\prod_jR_j^{m_j}
}
$$

이고, 두 그래프 차분은

$$
\boxed{
\delta A_n\preceq
\sum_mC_n(m)\left[
H_{|m|}S_0\Delta_0\prod_jR_j^{m_j}
+K_{|m|}\sum_jm_j(\delta R_j)R_j^{m_j-1}
\prod_{\ell\ne j}R_\ell^{m_\ell}
\right]
}
$$

이다. 첫 대괄호 항은 서로 다른 graph-state 점에서 (D^{|m|}a)가
변하는 효과이고, 둘째 항은 각 graph jet 슬롯이 변하는 효과다. 모든
항이 비음수 노름 상계이므로 각 곱의 슬롯을 한 번씩 교체하는 유한
telescoping으로 증명된다.

이 식을 (a=f)와 (a=g)에 각각 적용하면 바로 앞 절의
(F_n,delta F_n,Y_n,delta Y_n)이 생성된다. 따라서

$$
B_n=Y_n+
\sum_{m\ne(n,0,\ldots,0)}C_n(m)X_{|m|}\prod_jF_j^{m_j},
$$

$$
X_n\le\alpha^{-n}B_n,\qquad
\delta X_n\preceq
\alpha^{-n}\delta B_n+nB_n\alpha^{-(n+1)}\delta F_1
$$

까지 하나의 계산 사슬로 연결된다. 예를 들어
(R=(2,2,3,4)), (K=(2,3,5,7))인 exact fixture는

$$
A_1=4,\qquad A_2=16,\qquad A_3=82,\qquad A_4=468
$$

을 내며, 곡률이 있는 C6 fixture에서도 모든 class margin과
(\beta_j<1) margin이 엄격히 양수임을 exact arithmetic으로 확인했다.

이로써 **전역 정규화 지도 modulus를 가정한 결합 도함수 jet 계층**은
모든 주어진 유한차수에서 닫혔다. 남은 수학은 구분해서 적어야 한다.
C0 불변 ball과 역상 존재는 선행 gate를 연결해야 하고, local/matched
버전은 차수별 collar와 경계 접촉 정리가 더 필요하다. 또한 isotropic
곱노름 Bell 상계는 명시적 C1--C4 수정 tensor보다 보수적일 수 있다.
실제 뇌 지도 modulus, 측정 오차, holdout 상계가 없으므로 이것은 아직
인간 의식이나 4--6차원의 실증 판정이 아니다.

결합 raw-jet 생성기 확장은 `_workspace/ce/brain-coupled-arbitrary-order-raw-jet-generator-20260825/40-final-report.md`를 따른다.

## 임의차수 local/matched collar와 정확 경계

전역 (C^n) 도함수 계층을 유한한 chart에서 쓰려면, 역상점과 그
점변동 비교에 필요한 모든 modulus가 실제로 정의된 영역 안에 남아야
한다. 기준 기저척도를 (X_0>0)라 하고 물리 반경을 나누어

$$
r_{\rm in}=R_{\rm in}/X_0,quad
r_{\rm out}=R_{\rm out}/X_0,quad
r_{\rm pre}=R_{\rm pre}/X_0
$$

로 둔다. core의 backward coverage는

$$
\boxed{m_{\rm core}=r_{\rm in}-r_{\rm pre}\ge0}
$$

이다. 입력과 출력의 열린 collar를 각각
(eta_{\rm in}>0,eta_{\rm out}>0), collar에서의 균일 역상반경을
(r_{\rm pre,col})이라 하면

$$
r_{\rm pre,col}\ge r_{\rm pre},\qquad
\boxed{m_{\rm col}=r_{\rm in}+\eta_{\rm in}-r_{\rm pre,col}\ge0}
$$

도 필요하다. 앞 절에서 (D^nh)의 서로 다른 역상점 비교가
(Lambda_{n+1})를 사용했으므로, 같은 지도·graph modulus 판본이
collar 전체에서 **차수 (n+1)까지** 유효해야 한다. core에서 (n)차
상계만 통과한 것은 local (C^n) 차분 정리의 충분조건이 아니다.

전역 미분 certificate, core coverage, 열린 collar, (n+1)차까지의
collar modulus coverage가 모두 통과하면 모든 Bell 항과 역상 이동항의
평가점이 선언된 영역 안에 머문다. 따라서 전역 상삼각 재귀는 계수를
바꾸지 않고 local chart에 제한된다. (m_{\rm core}>0),
(m_{\rm col}>0)과 전역 미분 margin이 모두 엄격하면 이 미분/collar
부분은 robust interior다. 등호 coverage는 정리에는 포함되지만 robust
interior는 아니다.

입력·출력 영역을 정확히 맞추려면 추가로

$$
\boxed{
r_{\rm pre}^{\rm exact}=r_{\rm in},\qquad
r_{\rm fwd}^{\rm exact}=r_{\rm out}
}
$$

을 요구하고, fiber 기준척도 (Y_0)로 정규화한 경계 잔차가

$$
\boxed{
h|_{\partial X}=0,\qquad g|_{\partial X}=0
}
$$

이어야 한다. 구현은 inverse exact-bound 불일치, inverse 접촉 실패,
forward 미도달, forward 과소접촉, graph 경계 비고정, fiber 경계
비보존을 서로 다른 실패 코드로 분리한다.

여기서 exact matched contact는 의도적으로 `robust_interior=False`다.
정확한 등식은 작은 섭동 아래 열린 조건이 아니기 때문이다. 대신
`differential_and_collar_robust_interior`와
`domain_contact_robust_interior`를 분리하여, 미분 수축과 collar 여유는
강건하지만 경계 접촉 자체는 정확 등식이라는 사실을 보존한다.

wrapper는 특정 C4 계수를 사용하지 않고 전역 certificate의 최대차수
(n)과 coverage 차수 (n+1)만 읽는다. 그래서 C2, C4, C6 fixture에서
같은 논리가 통과하며, local/matched 반복 결과는 전역 상삼각 반복과
정확히 같다. 모든 기저 반경과 collar를 (X_0)배, fiber 경계량을
(Y_0)배 하면 정규화 margin과 접촉은 변하지 않는다.

이로써 **유한차수 global → local → exact matched 도함수 계층**은
조건부로 닫혔다. 그러나 실제 neural chart가 이 collar를 가지는지,
생물학적 경계에서 graph와 forcing이 정확히 0인지, 차수 전체에 균일한
성장률이 있는지는 전혀 별개의 미완성 문제다. 차원 1, 4, 5, 6, 100
검증은 입력 차원을 보존한다는 뜻이지 4--6을 선택한다는 뜻이 아니다.

local/matched 임의차수 확장은 `_workspace/ce/brain-local-matched-coupled-arbitrary-order-20260825/40-final-report.md`를 따른다.

