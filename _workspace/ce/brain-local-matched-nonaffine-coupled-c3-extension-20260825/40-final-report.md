# 국소·정합 정의역의 비아핀 결합 C3 그래프 변환

Status: COMPLETE

Date: 2026-08-25

## 초록

전역 비아핀 결합 C3 그래프 변환을 경계가 있는 국소 chart로 제한하려면
핵심 역정의역 포함만으로 충분하지 않다. 본 보고서는 양의 입력·출력 C3
연장 collar와 확장 출력 collar의 균일 역상 포함을 별도 전제로 추가해
경계까지의 C3 합성을 닫는다. 정확한 전·후방 접촉과 경계 anchoring을 더한
matched 정리는 완전 전방·후방 불변성을 준다. 정확 접촉의 domain margin은
영이지만 미분·collar margin은 양수일 수 있다. 구현은 집중 28개, 무차원
42개, 직접 선행 계층 134개 검사를 통과했다. 이는 조건부 수학 결과이며
실제 뇌 구조나 인간 의식의 4--6차원을 입증하지 않는다.

## 핵심 정의와 정리

핵심 입력·출력 반지름을 $R_t,R_{t+1}$, 양의 C3 collar 폭을
$\eta_t,\eta_{t+1}$라 한다. 모든 허용 graph에 대해

$$
F_h^{-1}(B_{R_{t+1}})\subseteq B_{R_t},
$$

$$
F_h^{-1}(B_{R_{t+1}+\eta_{t+1}})
\subseteq B_{R_t+\eta_t}
$$

를 독립적으로 요구한다. 첫 포함은 핵심 graph transform의 정의역을,
둘째 포함은 핵심 경계에서 C3 연쇄법칙을 적용할 열린 근방을 보장한다.

**[정리]** 전역 비아핀 결합 C3 인증서와 위 두 포함이 통과하면, 제한된
graph transform은 전역 인증서의 클래스 상계와 네 층 재귀 계수를 그대로
보존한다. 따라서 유일한 local invariant graph는 C3이다. 두 coverage
margin과 전역 margin이 엄격하면 local 인증서는 강건한 내부점이다.

**[정리]** 여기에 정확한 전·후방 경계 접촉, 경계 graph 값 영, 경계 fiber
forcing 영을 더하면 $F_h(U_t)=U_{t+1}$이고 경계 고정 C3 graph class가
보존된다. 유일한 graph는 두 matched 정의역에서 완전히 전방·후방
불변이다. 정확 접촉 때문에 domain-contact robust interior는 거짓이다.

## 정확 예시와 반증 경계

$F_h(x)=x+a x(1-x^2)+\varepsilon h(x)$를 입력 collar까지 연장하면
최소 팽창은 핵심 구간의 값과 달라진다. $a=\varepsilon=1/100$,
$\|h'\|\le1/2$, $\eta_t=1/10$에서

$$
\alpha_{\rm core}=\frac{39}{40},
\qquad
\alpha_{\rm collar}=\frac{9687}{10000}.
$$

$\eta_{t+1}=9687/200000$을 택하면 확장 역상 반지름은 $21/20$ 이하이고
입력 collar margin은 $1/20$이다. collar Hessian 상계는 $33/500$이다.
zero collar, 확장 역상 overrun, core보다 작은 collar 역상 상계, 부정확한
matched 접촉, 비영 boundary residual은 각각 독립된 실패 코드로 고정했다.

## 형식 지위와 한계

collar와 coverage는 `[공리: 수학 전제]`, 두 합성 결과는 `[정리]`, 유리수
값은 `[산출]`이다. 데이터로 선택한 항이나 관측 예측은 없다. C4 이상에는
다음 Faà di Bruno 계층이 필요하다. 실제 뇌 적용에는 측정된 신경장,
측정모형, 독립 holdout에서의 collar 전체 미분 상계와 개입 falsifier가
필요하다. 입력 차원은 보존될 뿐 선택되지 않는다.

## 재현성

```powershell
.codex\hooks\python.cmd python _workspace\ce\brain-local-matched-nonaffine-coupled-c3-extension-20260825\artifacts\local_matched_c3_math_audit.py
.codex\hooks\python.cmd pytest -q tests\test_quantitative_local_matched_nonaffine_coupled_c3_graph_transform.py
```

전체 suite, benchmark, network, 실데이터 분석은 실행하지 않았다.
