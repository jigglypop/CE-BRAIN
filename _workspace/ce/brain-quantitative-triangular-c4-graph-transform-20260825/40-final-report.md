# 정량적 아핀 삼각형 C4 그래프 변환

Status: COMPLETE

Date: 2026-08-25

## 초록

본 보고서는 아핀 삼각형 그래프 변환의 C3 계층을 C4까지 확장한다. 4차
연쇄법칙의 집합분할 계수 $1,4,3,6,1$을 모두 전개해 C4 class 반지름을
얻고, 두 graph 비교에서 D5 수준 모듈러스 $K_5$가 필요한 위치를 분리했다.
그 결과 대각 계수 $\beta_4=q\mu^4$인 5층 상삼각 재귀를 명시했다. 기준
fixture의 출력 반지름은 $95/16$이고 집중 26개, 무차원 43개, 인접 계층
113개 검사를 통과했다. 결과는 조건부 유한차원 정리이며 실제 뇌의 고차
정칙성이나 의식의 4--6차원을 입증하지 않는다.

## 서론

C3 정리의 계수를 단순히 한 차수 올리는 방식으로는 C4를 얻을 수 없다.
네 번 미분하면 두 개의 2차 삽입 미분이 만나는 새로운 분할항이 생기고,
두 graph의 4차 미분을 비교하려면 한 graph에서의 $D^4g$ 크기와 별개인
증가량 상계가 필요하다.

핵심 기여는 정확한 4차 합성 항등식, C4 class 보존식, 모든 교차계수를 가진
5층 재귀와 엄격성 반례를 하나의 전제 회계로 묶은 것이다. 이 정리는 이후
결합·비아핀 C4가 정확히 환원해야 할 기준식을 제공한다.

## 정의와 전제

$H_h=(I,h)$, $J_h=DH_h=(I,Dh)$,
$H_{k,h}=(0,D^kh)$, $S_h=Bh+g\circ H_h$라 한다. 통과한 C3 인증서의
기호를 유지하고 $r=1+\kappa$로 둔다. 새 전제는
$\|D^4h\|\le\Lambda_4$, $\|D^4g\|\le K_4$, 그리고 같은 기저점에서
$D^4g$의 graph 값 방향 Lipschitz 모듈러스 $K_5$다. 허용 graph 값 사이의
fiber segment는 정규화 tube 안에 있다고 가정한다.

## 4차 class 정리

**[정리]** 정확한 4차 연쇄법칙은

$$
\begin{aligned}
D^4S_h={}&(B+D_yg)H_4+4D^2g[H_3,J]+3D^2g[H_2,H_2]\\
&+6D^3g[H_2,J,J]+D^4g[J,J,J,J]
\end{aligned}
$$

이다.

증명. 네 미분 입력의 집합분할을 블록 크기별로 묶는다. 크기 $4$는 한 개,
$3+1$은 네 개, $2+2$는 세 개, $2+1+1$은 여섯 개,
$1+1+1+1$은 한 개다. 선형 $Bh$는 첫 항의 $BH_4$만 더한다. □

아핀 역함수의 네 입력 슬롯을 합성하면

$$
\Lambda_{4,\mathrm{out}}=\mu^4\left(
q\Lambda_4+4K_2\Lambda_3r+3K_2\Lambda_2^2
+6K_3\Lambda_2r^2+K_4r^4\right).
$$

따라서 $\Lambda_{4,\mathrm{out}}\le\Lambda_4$이면 C4 class가 보존된다.

## 5층 재귀와 엄격성

두 graph의 0차부터 4차 거리를 $\delta,d,e,f,j$라 하면 slotwise
telescoping으로

$$
j'\le\beta_4j+c_{43}f+c_{42}e+c_{41}d+c_{40}\delta
$$

를 얻는다. 계수는

$$
\beta_4=q\mu^4,qquad c_{43}=4\mu^4K_2r,
$$

$$
c_{42}=\mu^4(6K_2\Lambda_2+6K_3r^2),
$$

$$
c_{41}=\mu^4(4K_2\Lambda_3+12K_3\Lambda_2r+4K_4r^3),
$$

$$
\begin{aligned}
c_{40}=\mu^4(&K_2\Lambda_4+4K_3\Lambda_3r+3K_3\Lambda_2^2\\
&+6K_4\Lambda_2r^2+K_5r^4)
\end{aligned}
$$

이다. $K_5$는 마지막 계수에만 들어가지만 이를 생략할 수는 없다.
$D^4g$의 크기는 서로 다른 graph 값에서의 증가량을 제어하지 않기 때문이다.

**[정리]** 하위 gate, C4 class 보존, 엄격한 $q\mu^4<1$ 아래에서 5층
상삼각 재귀가 수렴하므로 유일한 불변 graph는 C4이다.

$q\mu^4=1$인 $x'=x/2$, $y'=y/16$에서는
$h_c(x)=cx|x|^3$이 불변이다. 이 함수는 C3이지만 원점의 좌우 4차 미분이
$-24c$와 $24c$이므로 등호에서는 C4 결론이 성립하지 않는다.

## 정확 산출과 관측 경계

기준 유리수 입력에서

$$
\Lambda_{4,\mathrm{out}}=\frac{95}{16},
\qquad
(\beta_4,c_{43},c_{42},c_{41},c_{40})
=\left(\frac12,\frac12,\frac{15}{8},\frac52,2\right).
$$

이는 구현 fixture의 정확 산출이지 관측 상수나 자연상수가 아니다. 데이터,
측정모형, fitting, 외부 수치를 사용하지 않았으므로 관측 비교는 없다.

## 남은 문제와 재현성

결합·비아핀·local/matched C4는 아직 미완성이다. C5 이상과 임의 차수에는
차수별 Bell-polynomial 상계 family가 필요하다. 실제 뇌 적용에는 측정된
신경장과 holdout 고차 미분 상계, 측정모형과 개입 falsifier가 필요하다.

```powershell
.codex\hooks\python.cmd python _workspace\ce\brain-quantitative-triangular-c4-graph-transform-20260825\artifacts\triangular_c4_math_audit.py
.codex\hooks\python.cmd pytest -q tests\test_quantitative_c4_graph_transform.py
```

전체 suite, benchmark, network와 실데이터 분석은 실행하지 않았다.

## 참조

- `_workspace/ce/brain-quantitative-triangular-c3-graph-transform-20260825`,
  repository predecessor, accessed 2026-08-25.
- `docs/검증_원장/리만부분공간_의식순간_주장원장.md`, claims
  CE-C4GRAPH-001--004, accessed 2026-08-25.
