# Mathematical verification

Status: COMPLETE

## 대상, 정의역과 전제

검산 대상은 계약의 전역 그래프 변환

$$
F_h(x)=\phi(x)+f(x,h(x)),\qquad
Y_h(x)=Bh(x)+g(x,h(x)),\qquad
\mathcal T h=Y_h\circ F_h^{-1}
$$

이다. 모든 노름은 기준 스케일로 정규화한 연산자 노름이며, 유한차원은
계산에 필요하지만 차원값 자체는 어떤 상계에도 선택 규칙으로 들어가지
않는다. 하위 $C^0,C^1,C^{1,1},C^2,C^{2,1}$ 전제와 기호는 세 선행 run에서
가져오고 이번 레인은 새 $D^3\phi$와 그 증가량만 독립 검산했다.

## 정확한 역함수 합성 항등식

한 점에서

$$
J=DF_h,\quad P=D^2F_h,\quad U=D^3F_h,
$$

$$
K=DY_h,\quad R=D^2Y_h,\quad V=D^3Y_h
$$

라 하자. 또한

$$
T=KJ^{-1},\qquad N=R-TP
$$

를 둔다. 두 번 미분한 합성 항등식에서
$D^2(\mathcal T h)=N[J^{-1},J^{-1}]$를 얻는다. 이를 한 번 더 미분하면
수정된 3차 미분은

$$
M=V-TU-3N[J^{-1}P,\,\cdot\,]
$$

이고,

$$
D^3(\mathcal T h)=M[J^{-1},J^{-1},J^{-1}].
$$

스칼라 제트에서는 두 번째 식이

$$
\frac{VJ^2-KUJ-3RJP+3KP^2}{J^5}
$$

와 정확히 같다. 독립 유리수 검산은
`artifacts/nonaffine_coupled_c3_math_audit.py`에 기록했다.

## 한 그래프의 3차 상계

$r=1+\kappa$라 두고, $H_f,H_g$를 2차 미분 상계,
$T_f,T_g$를 3차 미분 상계로 쓴다. 그래프의 2차 및 3차 반지름은
$\Lambda_2,\Lambda_3$이다. 여기서 $\Lambda_3$는 $D^3h$의 상계인 동시에
$D^2h$의 Lipschitz 상계로 하위 $C^{2,1}$ gate에 전달한다. 정확한 3차
연쇄법칙에서

$$
C_U^{\rm na}
=T_\phi+L_{fy}\Lambda_3
+3H_f\Lambda_2r+T_fr^3,
$$

$$
C_V
=q\Lambda_3+3H_g\Lambda_2r+T_gr^3.
$$

비아핀 기저가 만드는 새 한 그래프 항은 $T_\phi$ 하나다. 하위 계수
$C_F,C_N,C_T$와 $\rho=(q\kappa+L_{gx})/\alpha$를 쓰면

$$
C_M^{\rm na}
=C_V+\rho C_U^{\rm na}+\frac{3C_NC_F}{\alpha},
$$

$$
\Lambda_{3,{\rm out}}^{\rm na}
=\frac{C_M^{\rm na}}{\alpha^3}.
$$

따라서 $\Lambda_{3,{\rm out}}^{\rm na}\le\Lambda_3$가 닫힌 $C^3$
그래프 반지름의 충분한 인증 조건으로 사용된다. 등호는 클래스
불변성은 주지만 robust interior는 주지 않는다.

## $C^{3,1}$ 상계

$U_\phi=\operatorname{Lip}(D^3\phi)$, $U_f,U_g$를 비선형 항의
3차 미분 Lipschitz 상계라 하자. 한 그래프 안에서 두 점을 비교하면

$$
\begin{aligned}
C_{U,1}^{\rm na}={}&U_\phi+L_{fy}\Xi_3
+4H_fr\Lambda_3+3H_f\Lambda_2^2\\
&+6T_f\Lambda_2r^2+U_fr^4,
\end{aligned}
$$

$$
\begin{aligned}
C_{V,1}={}&q\Xi_3
+4H_gr\Lambda_3+3H_g\Lambda_2^2\\
&+6T_g\Lambda_2r^2+U_gr^4.
\end{aligned}
$$

여기서 $U_\phi$를 빼면 $D^3\phi(x_1)-D^3\phi(x_2)$를 제어할 항이
없다. 수정된 3차 미분의 Lipschitz 상계는

$$
\begin{aligned}
C_{M,1}^{\rm na}={}&C_{V,1}+C_TC_U^{\rm na}
+\rho C_{U,1}^{\rm na}\\
&+3\left(
\frac{C_N^{(1)}C_F}{\alpha}
+\frac{C_NC_F^2}{\alpha^2}
+\frac{C_NC_P}{\alpha}
\right),
\end{aligned}
$$

이고 최종 반지름은

$$
\Xi_{3,{\rm out}}^{\rm na}
=\frac{C_{M,1}^{\rm na}}{\alpha^4}
+\frac{3C_M^{\rm na}C_F}{\alpha^5}.
$$

$L_{fy}>0$이면 서로 다른 그래프가 서로 다른 역상을 만들므로
$\Xi_{3,{\rm out}}^{\rm na}\le\Xi_3$를 요구한다. $L_{fy}=0$이면 두
그래프의 역상이 같아 이 gate는 필요하지 않다. 계산되는 음의 margin은
그때 인증 실패가 아니다.

## 서로 다른 두 그래프의 3차 차이

$\delta,d,e,f$를 차례로 그래프값, 1차, 2차, 3차 미분 거리라 하자.
선행 run의 역상 거리 $r_x\delta$, 상태 거리 $Z\delta$, 1차 계수
$\beta_1,c_{10}$, 2차 계수와 수정 Hessian 차이 계수를 그대로 쓴다.
$U=D^3F_h$의 차이는

$$
\|\Delta U\|\le U_e e+U_d d+U_\delta^{\rm na}\delta,
$$

$$
U_e=3H_fr,qquad U_d=3H_f\Lambda_2+3T_fr^2,
$$

$$
\begin{aligned}
U_\delta^{\rm na}={}&U_\phi r_x+L_{fy}\Xi_3r_x
+H_fZ\Lambda_3+3H_fr\Lambda_3r_x\\
&+3H_f\Lambda_2^2r_x+3T_fZ\Lambda_2r
+3T_fr^2\Lambda_2r_x+U_fZr^3.
\end{aligned}
$$

비아핀 기저가 만드는 새 두 그래프 항은 정확히 $U_\phi r_x$이다.
$V=D^3Y_h$의 $V_e,V_d,V_\delta$는 아핀 결합 선행식과 같다.

수정된 3차 미분 차이에서

$$
E_{\rm corr}
=\frac{QC_F}{\alpha}+\frac{C_NL_{fy}}{\alpha},
$$

$$
D_{\rm corr}
=\frac{N_dC_F}{\alpha}
+C_N\left(\frac{P_d}{\alpha}
+\frac{C_FL_{fy}}{\alpha^2}\right),
$$

$$
\Delta_{\rm corr}
=\frac{N_\delta C_F}{\alpha}
+C_N\left(\frac{P_\delta}{\alpha}
+\frac{C_FA_\delta}{\alpha^2}\right)
$$

를 얻는다. 따라서

$$
M_e=V_e+\rho U_e+3E_{\rm corr},
$$

$$
M_d=V_d+\rho U_d+C_U^{\rm na}\beta_1+3D_{\rm corr},
$$

$$
M_\delta=V_\delta+\rho U_\delta^{\rm na}
+C_U^{\rm na}c_{10}+3\Delta_{\rm corr}.
$$

최종 4단계 재귀 계수는

$$
\beta_{3,c}^{\rm na}=\frac Q{\alpha^3},
$$

$$
c_{32,c}^{\rm na}=\frac{M_e}{\alpha^3},
$$

$$
c_{31,c}^{\rm na}
=\frac{M_d}{\alpha^3}
+\frac{3C_M^{\rm na}L_{fy}}{\alpha^4},
$$

$$
c_{30,c}^{\rm na}
=\frac{M_\delta}{\alpha^3}
+\frac{3C_M^{\rm na}A_\delta}{\alpha^4}.
$$

이 계수로 계약의 4단계 상삼각 재귀를 얻는다.

## 경계와 환원 검산

세 기저 곡률 계수 $H_\phi,T_\phi,U_\phi$를 모두 영으로 두면 하위
비아핀 $C^2$ 인증서가 아핀 결합 $C^2$로 환원되고, 위 식의 새 두 항도
사라진다. 따라서 모든 $C^3$ 계수가 아핀 결합 $C^3$ 계수와 항별로 같다.

그래프-기저 결합을 영으로 두면 $r_x=0$이고 역상은 공통이다. 이때
$\mu=\alpha^{-1}$이며 전방 기저 상계에서

$$
\nu=H_\phi\mu^3,qquad
\tau=T_\phi\mu^4+3H_\phi^2\mu^5
$$

를 얻는다. 한 그래프의 결합식은

$$
\frac{A_3+\rho T_\phi+3(A_2+\rho H_\phi)H_\phi/\alpha}{\alpha^3}
$$

이고, 정확히

$$
\mu^3A_3+3\mu\nu A_2+s\tau
$$

로 정리된다. $U_\phi r_x$도 사라져 공통 역함수형 비아핀 삼각 $C^3$
재귀와 일치한다.

$Q/\alpha^3=1$에서는 $x\mapsto x/2$, $y\mapsto y/8$과
$h_c(x)=c|x|^3$가 비영 고정족을 이룬다. 이 함수는 $C^2$이지만 원점에서
$C^3$가 아니므로 등호 경계는 $C^3$ 수축 결론을 주지 않는다.

## 무차원성, 숨은 공리와 판정

모든 새 입력은 정규화된 도함수 노름이므로 차원 벡터
$(0,0,0,0)$이다. 고정점 코어 $Q/\alpha^3$와 모든 recurrence 계수도
무차원이다. 이 감사는 차원 정합만 보이며 뇌의 물리적 실현을 보이지 않는다.

- P0: 없음.
- P1: 없음. 단, 국소·matched-domain 합성은 이 전역 정리 밖의 후속 과제다.
- P2: `docs/axium.md`는 현재 저장소에 존재하지 않는다. 계약과 세 선행
  정본의 기호를 사용했으며, 이 부재는 이번 수학 항등식의 결론을 바꾸지
  않는다.
- 형식 지위 후보: 명시한 전제 아래의 조건부 정리. 의식·신경장·차원
  동일시는 미완성이다.

재현 명령:

```powershell
.codex\hooks\python.cmd python _workspace\ce\brain-nonaffine-coupled-c3-extension-20260825\artifacts\nonaffine_coupled_c3_math_audit.py
```
