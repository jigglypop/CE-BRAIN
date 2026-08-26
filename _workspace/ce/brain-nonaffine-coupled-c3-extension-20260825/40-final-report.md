# 전역 비아핀 결합 기저의 정량적 C3 그래프 변환

Status: COMPLETE

Date: 2026-08-25

## 초록

이 보고서는 그래프 높이에 의존하는 기저 결합과 그래프 독립 비아핀
기저곡률이 동시에 있을 때 전역 그래프 변환의 C3 정칙성을 다룬다.
정확한 수정 3차 미분에 $T_\phi=\sup\|D^3\phi\|$를 추가하고, C3,1 및
두 그래프 비교에 $U_\phi=\operatorname{Lip}(D^3\phi)$를 추가했다.
그 결과 C3 클래스, 조건부 C3,1 클래스와
$\beta_{3,c}^{\rm na}=Q/\alpha^3$인 4층 상삼각 재귀의 모든 계수를
명시했다. 구현 검증은 집중 33개, 무차원 40개, 인접 계층 326개 검사를
통과했다. 결과의 형식 지위는 명시한 전역 미분 상계 아래의 조건부
정리이며, 실제 뇌·의식 또는 4--6차원 선택의 증거가 아니다.

## 서론

공통 역함수형 비아핀 C3 정리는 한 비아핀 기저의 역함수 미분을 모든
그래프가 공유할 때 성립한다. 아핀 결합 C3 정리는 그래프마다 역상이
달라지는 효과를 다루지만 공유 기저 자체의 3차·4차 굽음은 영으로 둔다.
따라서 두 효과가 동시에 있을 때는 어느 한 선행식도 그대로 쓸 수 없다.

핵심 기여는 두 선행 정리의 공통 수정-미분 골격을 유지하면서 공유
기저가 새로 만드는 항을 정확히 분리한 것이다. 한 그래프의 3차 상계에는
$T_\phi$가 더해지고, 점 또는 그래프 사이의 증가량에는 $U_\phi$와
$U_\phi r_x$가 더해진다. 이 두 항을 포함하면 영 기저곡률에서는 아핀
결합 C3로, 영 기저결합에서는 공통 역함수형 비아핀 삼각 C3로 정확히
환원된다.

## 정의와 표기

정규화된 유한차원 실노름공간에서

$$
F_h(x)=\phi(x)+f(x,h(x)),
$$

$$
Y_h(x)=Bh(x)+g(x,h(x)),
$$

$$
\mathcal Th=Y_h\circ F_h^{-1}
$$

로 정의한다. $\phi$는 그래프 독립 비아핀 기저지도이고, $f$는 그래프
높이를 기저 위치에 결합하는 항이다. 허용 그래프 기울기를 $\kappa$라
하고 $r=1+\kappa$로 둔다. 그래프의 2차·3차 반지름은
$\Lambda_2,\Lambda_3$이며, 3차 미분 Lipschitz 반지름은 $\Xi_3$이다.

한 역상점에서

$$
J=DF_h,\quad P=D^2F_h,\quad U=D^3F_h,
$$

$$
K=DY_h,\quad R=D^2Y_h,\quad V=D^3Y_h
$$

라 한다. 수정 1차·2차·3차 미분을

$$
T=KJ^{-1},\qquad N=R-TP,
$$

$$
M=V-TU-3N[J^{-1}P,\,\cdot\,]
$$

로 정의한다.

## 공리와 전제

**[공리: 수학 전제]** 선행 전역 tube, 가역성, C1, C1,1, C2와 조건부
C2,1 인증서가 모두 통과했다고 가정한다. $DF_h$의 최소 팽창 하한은
$\alpha>0$이고 C0 그래프 변환 상계는 $Q$다.

**[공리: 정규화]** 모든 도함수와 모듈러스는 선언한 기저·섬유 기준
스케일로 나눈 무차원 연산자 노름이다. 입력 차원은 외부에서 주어지며
정리에서 선택하지 않는다.

**[공리: 고차 상계]** $H_f,H_g$는 $f,g$의 2차 미분 상계,
$T_f,T_g$는 3차 미분 상계, $U_f,U_g$는 3차 미분 Lipschitz 상계다.
비아핀 기저에는

$$
T_\phi=\sup\|D^3\phi\|,qquad
U_\phi=\operatorname{Lip}(D^3\phi)
$$

를 가정한다. 이 상계들은 뇌 데이터에서 산출한 값이 아니다.

## 수정 3차 미분 정리

**[정리]** 위 정의와 전제 아래

$$
D^3(\mathcal Th)=M[J^{-1},J^{-1},J^{-1}]
$$

이다.

증명. 항등식 $Y_h=(\mathcal Th)\circ F_h$를 세 번 미분한다. 한 번
미분한 식에서 $T=KJ^{-1}$를 얻는다. 두 번 미분한 식의 $D^2F_h$ 항을
옮기면 $N=R-TP$이고
$D^2(\mathcal Th)=N[J^{-1},J^{-1}]$이다. 세 번 미분한 식에는
$D^3Y_h$, $TD^3F_h$, 그리고 $D^2(\mathcal Th)$와 $D^2F_h$가 만나는
세 순환항이 생긴다. 두 번째 미분식을 대입하고 세 입력 슬롯에
$J^{-1}$를 적용하면 정의한 $M$과 결론을 얻는다. □

스칼라 제트에서는 이 항등식이

$$
\frac{VJ^2-KUJ-3RJP+3KP^2}{J^5}
$$

와 일치한다. 독립 exact-rational artifact가 두 표현의 동일성을 검산한다.

## C3와 C3,1 클래스

$L_{fy}$를 $f$의 그래프 높이 방향 1차 상계,
$\rho=(q\kappa+L_{gx})/\alpha$라 하자. 정확한 3차 연쇄법칙에서

$$
C_U^{\rm na}
=T_\phi+L_{fy}\Lambda_3
+3H_f\Lambda_2r+T_fr^3,
$$

$$
C_V=q\Lambda_3+3H_g\Lambda_2r+T_gr^3
$$

를 얻는다. 선행 수정 헤시안과 기저 야코비안 상계를 $C_N,C_F$라 하면

$$
C_M^{\rm na}
=C_V+\rho C_U^{\rm na}
+\frac{3C_NC_F}{\alpha},
$$

$$
\Lambda_{3,\mathrm{out}}^{\rm na}
=\frac{C_M^{\rm na}}{\alpha^3}.
$$

따라서
$\Lambda_{3,\mathrm{out}}^{\rm na}\le\Lambda_3$는 선언한 C3 반지름을
보존하는 충분조건이다.

C3,1 비교에서는

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
&+6T_g\Lambda_2r^2+U_gr^4
\end{aligned}
$$

를 얻는다. 선행 Lipschitz 상계를 $C_T,C_N^{(1)},C_P$라 쓰면

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

$$
\Xi_{3,\mathrm{out}}^{\rm na}
=\frac{C_{M,1}^{\rm na}}{\alpha^4}
+\frac{3C_M^{\rm na}C_F}{\alpha^5}.
$$

**[정리]** $L_{fy}>0$이면
$\Xi_{3,\mathrm{out}}^{\rm na}\le\Xi_3$도 요구한다. $L_{fy}=0$이면 두
그래프의 역상이 같으므로 이 gate는 필요하지 않다. $U_\phi$를 빼면
$D^3\phi$의 점간 증가량이 제어되지 않으므로 일반 비아핀 C3,1 명제는
성립하지 않는다.

## 네 단계 차이 재귀

그래프값, 1차, 2차, 3차 미분 거리를 $\delta,d,e,f$라 하고, 선행
역상·상태 거리 계수를 $r_x,Z$라 한다. $U=D^3F_h$의 차이는

$$
\|\Delta U\|\le U_e e+U_d d+U_\delta^{\rm na}\delta
$$

이며

$$
U_e=3H_fr,qquad
U_d=3H_f\Lambda_2+3T_fr^2,
$$

$$
\begin{aligned}
U_\delta^{\rm na}={}&U_\phi r_x+L_{fy}\Xi_3r_x
+H_fZ\Lambda_3+3H_fr\Lambda_3r_x\\
&+3H_f\Lambda_2^2r_x+3T_fZ\Lambda_2r
+3T_fr^2\Lambda_2r_x+U_fZr^3.
\end{aligned}
$$

$V=D^3Y_h$의 계수는

$$
V_e=3H_gr,qquad
V_d=3H_g\Lambda_2+3T_gr^2,
$$

$$
\begin{aligned}
V_\delta={}&q\Xi_3r_x+H_gZ\Lambda_3
+3H_gr\Lambda_3r_x+3H_g\Lambda_2^2r_x\\
&+3T_gZ\Lambda_2r+3T_gr^2\Lambda_2r_x
+U_gZr^3.
\end{aligned}
$$

선행 수정 헤시안 차이 계수를 $N_d,N_\delta$, 기저 헤시안 차이 계수를
$P_d,P_\delta$, 기저 야코비안의 값 차이 계수를 $A_\delta$, C1 재귀
계수를 $\beta_1,c_{10}$이라 하자. 보정항

$$
E_{\rm corr}=\frac{QC_F}{\alpha}+\frac{C_NL_{fy}}{\alpha},
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

를 쓰면

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

**[정리]** 최종 네 단계 재귀는

$$
f'\le\beta_{3,c}^{\rm na}f
+c_{32,c}^{\rm na}e+c_{31,c}^{\rm na}d
+c_{30,c}^{\rm na}\delta,
$$

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
+\frac{3C_M^{\rm na}A_\delta}{\alpha^4}
$$

이다. 모든 하위 gate와 클래스 불변성, 엄격한 $Q/\alpha^3<1$ 아래
네 층의 상삼각 재귀가 수축하므로 유일한 불변 그래프는 C3이다.

## 축약, 예시와 경계

**[산출]** $H_\phi=T_\phi=U_\phi=0$이면 새 항이 모두 사라지고 아핀
결합 C3 인증서와 모든 계수가 정확히 같다.

**[산출]** 그래프-기저 결합이 영이면 $r_x=0$이고 역상이 공통이다.

$$
\mu=\alpha^{-1},qquad
\nu=H_\phi\mu^3,
$$

$$
\tau=T_\phi\mu^4+3H_\phi^2\mu^5
$$

를 대입하면 공통 역함수형 비아핀 삼각 C3 인증서와 모든 4층 재귀
계수가 정확히 같다.

**[산출: 예시]**
$\phi_{\lambda,a}(x)=\lambda x+a\sin x$, $\lambda>a\ge0$이면

$$
\mu=(\lambda-a)^{-1},qquad
H_\phi=T_\phi=U_\phi=a.
$$

기준 exact fixture에서

$$
C_U^{\rm na}=\frac{239}{1600},qquad
C_M^{\rm na}=\frac{144697379}{273800000},
$$

$$
\Lambda_{3,\mathrm{out}}^{\rm na}
=\frac{1157579032}{1733598925},qquad
\beta_{3,c}^{\rm na}=\frac{492800}{1874161}
$$

이다. 이 수치는 구현의 exact-rational witness이며 경험적 뇌 상수가 아니다.

**[정리: no-go 경계]** $Q/\alpha^3=1$인
$x\mapsto x/2$, $y\mapsto y/8$에서는
$h_c(x)=c|x|^3$이 비영 불변족이다. 이 함수는 C2이지만 원점에서 C3가
아니므로 등호 경계에서는 C3 수축 결론이 성립하지 않는다.

## 관측 비교

이 run은 관측값, 데이터셋, 측정모형 또는 적합 파라미터를 사용하지
않았다. 따라서 비교할 모델값·기준값·불확도·잔차가 없다. 구현 수치가
정확히 일치한다는 사실은 수학식의 코드 재현을 확인할 뿐, 뇌가 이
그래프 변환을 사용한다는 관측 증거가 아니다.

## 미완성 과제와 한계

**[미완성]** 국소·matched-domain 비아핀 결합 C3에는 전역 계수 외에
역정의역 coverage, 전방 접촉, 경계 collar의 C3 연장이 필요하다.

**[미완성]** C4 이상에서는 4차 역함수 Faà di Bruno 항, C4 그래프
반지름과 D5 수준 지도 모듈러스가 필요하다.

**[미완성]** 실제 뇌 적용에는 출처가 고정된 생물 기전식과 측정모형,
실데이터에서 식별 가능한 정규화 좌표, 독립 holdout의 균일 미분 상계와
개입 반증이 필요하다. 현재 결과는 인간 의식의 차원을 4--6으로 선택하지
않고, 거대차원 상태공간 또는 순간 저차원 집중을 경험적으로 입증하지
않는다.

## 재현성

수학 독립 검산:

```powershell
.codex\hooks\python.cmd python _workspace\ce\brain-nonaffine-coupled-c3-extension-20260825\artifacts\nonaffine_coupled_c3_math_audit.py
```

집중 구현 검사:

```powershell
.codex\hooks\python.cmd pytest -q tests\test_quantitative_nonaffine_coupled_c3_graph_transform.py
```

결과는 33개 통과다. 무차원 검사는 `tests/test_dimensionless.py`의 40개,
인접 graph/triangular/coupled/nonaffine C0--C3 검사는 326개가 통과했다.
전체 저장소 suite, benchmark, network, 데이터 분석은 실행하지 않았다.

## 참조

- `brain-nonaffine-coupled-c2-extension-20260825`, global nonaffine coupled
  C2 predecessor, repository artifact, accessed 2026-08-25.
- `brain-quantitative-coupled-c3-graph-transform-20260825`, affine coupled C3
  predecessor, repository artifact, accessed 2026-08-25.
- `brain-nonaffine-triangular-c3-extension-20260825`, common-inverse nonaffine
  triangular C3 predecessor, repository artifact, accessed 2026-08-25.
- `docs/검증_원장/리만부분공간_의식순간_주장원장.md`, claims
  CE-NACC3-001--004, accessed 2026-08-25.
