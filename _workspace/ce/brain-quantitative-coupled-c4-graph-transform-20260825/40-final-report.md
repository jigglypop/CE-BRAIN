# 정량적 아핀 결합 기저 C4 그래프 변환

Status: COMPLETE

Date: 2026-08-25

## 초록

그래프 높이에 따라 기저 역상이 달라지는 아핀 결합 그래프 변환을 C4까지
확장했다. 네 번 미분한 합성 항등식에서 수정 4차 tensor를 분리하고, 이를
C4 class, 조건부 C4,1 class와 5층 차분 재귀로 전개했다. 대각 계수는
$\beta_{4,c}=Q/\alpha^4$이며 영 기저결합에서 모든 계수가 삼각형 C4로
정확히 환원된다. 구현은 집중 22개, 무차원 44개, 인접 141개 검사를
통과했다. 결과는 조건부 유한차원 정리이며 실제 신경장이나 의식 차원을
식별하지 않는다.

## 서론

삼각형 C4에서는 기저 역함수가 모든 graph에 공통이므로 네 개의 역함수
미분 슬롯만 곱하면 된다. 결합 기저에서는 $F_h^{-1}$ 자체가 graph에 따라
달라진다. 따라서 기저의 2차부터 4차 미분이 출력 graph의 미분과 만나는
수정항을 먼저 제거해야 한다.

핵심 기여는 수정 4차 tensor $O$를 정의하고, 그 크기·점간 모듈러스·두
graph 차분을 같은 항등식에서 각각 유도한 것이다. 차분은 이미 검증된
$J,P,U,T,N,M$ 계수 vector를 재사용하므로 하위 항의 누락 여부를 직접
감사할 수 있다.

## 정의와 공리

$Y_h=(\mathcal Th)\circ F_h$라 하고

$$
J=DF_h,\ P=D^2F_h,\ U=D^3F_h,\ W=D^4F_h,
$$

$$
K=DY_h,\ R=D^2Y_h,\ V=D^3Y_h,\ Z=D^4Y_h
$$

로 둔다. $L=J^{-1}$이고, $T,N,M$은 통과한 coupled C3 전임의 수정
1차·2차·3차 tensor다.

**[공리: 수학 전제]** 모든 하위 coupled C3 gate가 통과하며
$\|L\|\le\alpha^{-1}$라고 가정한다. D4 지도 상계와 graph 반지름
$\Lambda_4$가 유한하고, graph-dependent inverse에서는 D5 지도 모듈러스와
$\Xi_4=\operatorname{Lip}(D^4h)$도 유한하다고 가정한다.

## 수정 4차 tensor

**[정리]** 수정 4차 tensor를

$$
O=Z-TW-4N[LU,\cdot]-3N[LP,LP]-6M[LP,\cdot,\cdot]
$$

로 정의하면

$$
D^4(\mathcal Th)=O[L,L,L,L]
$$

이다.

증명. $Y_h=(\mathcal Th)\circ F_h$를 네 번 미분한다. 4차 출력 미분 외에
세 종류의 분할항이 생긴다. $D^3(\mathcal Th)$와 $P,J,J$의 결합은 여섯
개, $D^2(\mathcal Th)$와 $P,P$의 결합은 세 개, $D^2(\mathcal Th)$와
$U,J$의 결합은 네 개다. 전임의 $N,M$ 표현을 대입하고 각 입력에 $L$을
적용하면 결론을 얻는다. □

## C4와 C4,1 class

$r=1+\kappa$라 하자. D2--D4 지도 상계를 $H_f,T_f,U_f$와
$H_g,T_g,U_g$라 쓰면

$$
C_W=L_{fy}\Lambda_4+4H_f\Lambda_3r+3H_f\Lambda_2^2
+6T_f\Lambda_2r^2+U_fr^4,
$$

$$
C_Z=q\Lambda_4+4H_g\Lambda_3r+3H_g\Lambda_2^2
+6T_g\Lambda_2r^2+U_gr^4.
$$

수정 tensor의 크기는

$$
C_O=C_Z+\rho C_W+\frac{4C_NC_U}{\alpha}
+\frac{3C_NC_F^2}{\alpha^2}+\frac{6C_MC_F}{\alpha}
$$

이고

$$
\Lambda_{4,\mathrm{out}}=C_O/\alpha^4
$$

이다. 따라서 이 값이 $Lambda_4$ 이하이면 C4 class를 보존한다.

D5 지도 모듈러스 $V_f,V_g$와 graph 모듈러스 $\Xi_4$를 사용해
$C_{W,1},C_{Z,1},C_{O,1}$을 같은 방식으로 전개하면

$$
\Xi_{4,\mathrm{out}}=\frac{C_{O,1}}{\alpha^5}
+\frac{4C_OC_F}{\alpha^6}
$$

을 얻는다. $L_{fy}>0$이면 이 값이 $Xi_4$ 이하여야 한다. $L_{fy}=0$이면
모든 graph가 역함수를 공유하므로 이 gate는 필요하지 않다.

## 차분 vector와 5층 재귀

두 graph의 거리를 $(j,f,e,d,\delta)$ 순서로 둔다. 기존
$\Delta J,\Delta P,\Delta U,\Delta T,\Delta N,\Delta M$과 새
$\Delta W,\Delta Z$를 비음수 coefficient vector로 표현한다. $A=LP$라
두고 $\Delta A\preceq C_F\Delta L+\alpha^{-1}\Delta P$를 사용하면

$$
\begin{aligned}
\Delta O\preceq{}&\Delta Z+\rho\Delta W+C_W\Delta T\\
&+4\left(\frac{C_U}{\alpha}\Delta N+C_NC_U\Delta L
+\frac{C_N}{\alpha}\Delta U\right)\\
&+3\left(\frac{C_F^2}{\alpha^2}\Delta N
+\frac{2C_NC_F}{\alpha}\Delta A\right)\\
&+6\left(\frac{C_F}{\alpha}\Delta M+C_M\Delta A\right)
\end{aligned}
$$

를 얻는다. 그 성분을 $(Q,O_f,O_e,O_d,O_\delta)$라 쓰면

$$
j'\le\frac{Q}{\alpha^4}j+rac{O_f}{\alpha^4}f
+\frac{O_e}{\alpha^4}e
+\left(\frac{O_d}{\alpha^4}+\frac{4C_OL_{fy}}{\alpha^5}\right)d
+\left(\frac{O_\delta}{\alpha^4}+\frac{4C_OA_\delta}{\alpha^5}\right)\delta.
$$

**[정리]** 모든 class gate와 엄격한 $Q/\alpha^4<1$ 아래에서 5층
상삼각 재귀가 수렴하므로 유일한 불변 graph는 C4이다.

## 축약, 반례와 산출

**[산출]** 기저결합과 모든 기저 비선형 도함수 상계를 영으로 두면
$C_W=0$이고 $O=Z$가 된다. class 출력과 네 교차계수는 아핀 삼각형 C4와
정확히 일치한다.

**[정리: 경계]** $Q/\alpha^4=1$인 $x'=x/2$, $y'=y/16$에서는
$h_c(x)=cx|x|^3$이 불변 C3/non-C4 graph다. 따라서 뭉침 등호는 허용할 수
없다.

기준 fixture에서는

$$
\Lambda_{4,\mathrm{out}}
=\frac{616648668720}{94931877133},
\qquad
\beta_{4,c}=\frac{19712000}{69343957}.
$$

이는 정확 구현 fixture의 산출이며 자연상수나 신경 상수가 아니다.

## 관측 비교와 남은 문제

데이터나 측정모형을 사용하지 않았으므로 관측 비교는 없다. 비아핀 coupled
C4에는 graph-independent 기저의 D2--D5 항이 추가로 필요하다.
local/matched C4는 같은 상계가 extension collar 전체에서 성립해야 한다.
실제 뇌 적용과 의식 차원 선택은 별도 실증 과제다.

## 재현성

```powershell
.codex\hooks\python.cmd python _workspace\ce\brain-quantitative-coupled-c4-graph-transform-20260825\artifacts\coupled_c4_math_audit.py
.codex\hooks\python.cmd pytest -q tests\test_quantitative_coupled_c4_graph_transform.py
```

전체 suite, benchmark, network와 실데이터 분석은 실행하지 않았다.

## 참조

- `_workspace/ce/brain-quantitative-coupled-c3-graph-transform-20260825`,
  repository predecessor, accessed 2026-08-25.
- `_workspace/ce/brain-quantitative-triangular-c4-graph-transform-20260825`,
  repository predecessor, accessed 2026-08-25.
