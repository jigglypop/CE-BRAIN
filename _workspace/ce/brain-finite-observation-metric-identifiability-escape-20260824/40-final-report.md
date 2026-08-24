# BA-OBS-ID1: 능동 개입 아래 유한 계량족의 국소 식별성

Status: COMPLETE

Claim ceiling: `MATHEMATICAL_LOCAL_IDENTIFIABILITY_WITHIN_A_GAUGE_FIXED_FINITE_METRIC_FAMILY / DETERMINISTIC_SYNTHETIC_INTERVENTION_WITNESS / INFINITE_AMBIENT_SPACE_ALLOWED_BUT_NOT_RECOVERED / NO_EMPIRICAL_BRAIN_CONSCIOUSNESS_SELF_OR_AGI_VALIDATION`

## 초록

유한한 수동 관측만으로는 무한차원 주변 계량을 식별할 수 없다는 선행 no-go 뒤에, 어떤 추가 조건이 그 한계를 피하는지 묻는다. 본 보고서는 gauge를 고정한 유한 매개변수 계량족, 알려진 동역학, 알려진 능동 개입, 양의 정부호 민감도 Gramian을 가정하면 그 계량족 좌표가 국소적으로 식별됨을 증명한다. 증명은 가중 Hilbert 출력공간의 미분 $A=D\Phi$와 $\mathcal I=A^*A$로부터 유한차원 readout을 구성한 뒤 통상적인 역함수 정리를 적용한다. 별도로 $\mathbb R^2\oplus\ell^2$의 무한 주변공간에서 정확한 복원식을 갖는 합성 witness와 사전 고정된 train/holdout 검증을 실행했으며, 최대 매개변수 오차는 $2.220446049250313\times10^{-16}$, held-out NSE의 최댓값은 $1.4204367480745902\times10^{-32}$였다. 이는 조건부 수학 정리와 결정론적 합성 구현 결과이며, 실제 뇌 계량·의식·자아·AGI에 관한 검증은 포함하지 않는다.

## 문제와 독자

이 보고서는 앞선 수동 관측 no-go가 남긴 정확한 질문, 곧 “무엇을 더 알거나 조작해야 계량에 관한 제한된 주장을 할 수 있는가”에 답한다. 먼저 가정과 기호를 정하고, 이어 정리 T3와 그 증명을 제시하며, 영-잔차 손실의 따름정리 C2와 특이 Gramian의 경계를 분리한다. 그 다음 무한차원 witness W1, 결정론적 구현 수령증, 선행 no-go와의 양립성, 재현 경로와 미완성 다리를 순서대로 기록한다.

대상 독자는 미분방정식 또는 시스템 식별을 한 번이라도 접한 독자이며, 무한차원 계량을 곧바로 복원한다는 주장을 기대하지 않는 독자이다. 이 글에서 증명하는 것은 고정된 유한 계량족의 좌표에 한정된 국소 식별성이다. 계량족의 선택, 동역학의 정확성, 초기조건과 개입의 알려짐은 모두 증명의 전제이지 데이터로부터 얻은 결론이 아니다.

## 직관: 그림자와 제약된 기계

수동 관측은 큰 물체의 그림자 한 장과 같다. 그림자가 같아도 뒤쪽의 형상과 깊이는 달라질 수 있으므로, 그림자만으로 물체 전체를 고를 수 없다. 이것이 BA-OBS-NOGO1이 다룬 경우다. 반면 본 보고서의 대상은 모든 물체가 아니라, 나사 몇 개의 위치만 바뀌는 미리 정한 기계다. 그 기계를 알려진 방식으로 밀고, 시간에 따른 반응 전체를 측정하면 각 나사의 위치가 다른 반응을 남길 수 있다.

이 비유는 두 곳에서 멈춘다. 첫째, 실제 뇌가 그러한 유한 계량족과 알려진 방정식을 따른다는 보장은 없다. 둘째, 실험에서 충분히 다른 반응을 만들 개입을 가할 수 있다는 보장도 없다. 따라서 “밀어서 구별했다”는 합성 기계의 결과를 뇌의 계량, 의식, 자아, 해마의 해시 해석으로 옮길 수 없다.

## 설정과 가정

상태공간을 Hilbert 공간 $\mathcal H$라 하고, 열린 집합 $\Theta\subset\mathbb R^p$의 기준점 $\vartheta_*$를 택한다. 미지 계량은 중복 좌표를 미리 제거한 gauge-fixed 유한 계량족 $\vartheta\mapsto G(\vartheta)$로 제한한다. 각 $G(\vartheta)$는 bounded, self-adjoint, coercive인 strong metric operator라고 가정한다. 여기서 이 가정은 무한한 모든 계량을 유한 개의 수로 복원한다는 뜻이 아니라, 모델이 허용하는 계량 자유도를 미리 $p$개 좌표로 제한했다는 뜻이다.

실험 $e=1,\ldots,E$마다 알려진 초기조건과 알려진 개입 $u^{(e)}$ 및 알려진 계량-결합 동역학이 무차원 출력 $\widetilde y_e$를 생성한다고 둔다. 무차원 시간은 $\tau=t/t_*$이고, 출력공간과 forward map은 다음과 같다.

$$
\mathcal Y=\bigoplus_{e=1}^{E}L^2([0,T_e],\mathbb R^{r_e}),
\qquad
\Phi:\Theta\to\mathcal Y,
\qquad
\Phi(\vartheta)=(\widetilde y_e(\cdot;\vartheta))_{e=1}^E.
$$

$\Phi$는 $\vartheta_*$ 근방에서 $C^1$이라고 가정한다. 이는 해당 동역학의 well-posedness와 매개변수 미분 가능성을 포함한다. 각 $R_e(\tau)$는 강측정 가능하고 대칭이며 매개변수와 무관한 양의 정부호 행렬이고, 어떤 양수 $r_-$와 유한한 $r_+$에 대하여 거의 모든 $\tau$에서 $r_-I\preceq R_e(\tau)\preceq r_+I$라고 가정한다. 따라서 다음은 $\mathcal Y$에 표준 $L^2$ 노름과 동치인 Hilbert 내적을 준다.

$$
\langle f,g\rangle_{\mathcal Y,R}
=\sum_{e=1}^{E}\int_0^{T_e}f_e(\tau)^\top R_e(\tau)^{-1}g_e(\tau)\,d\tau.
$$

민감도와 가중 민감도 Gramian은 각각 다음과 같다.

$$
S_e(\tau;\vartheta)=\frac{\partial\widetilde y_e(\tau;\vartheta)}{\partial\vartheta}\in\mathbb R^{r_e\times p},
\qquad
\mathcal I(\vartheta)=\sum_{e=1}^{E}\int_0^{T_e}S_e^\top R_e^{-1}S_e\,d\tau.
$$

## 정리 T3: 양의 정부호 Gramian의 국소 식별성

**[정리 T3]** 위 가정 아래 $\mathcal I(\vartheta_*)\succ0$이면, $\Phi$는 $\vartheta_*$의 어떤 근방에서 일대일이다. 따라서 알려진 동역학·초기조건·개입과 관측모형 아래 gauge-fixed 유한 계량족의 좌표 $\vartheta$는 국소적으로 구조 식별 가능하다.

**증명.** $A:=D\Phi_{\vartheta_*}:\mathbb R^p\to\mathcal Y$라고 둔다. $\mathbb R^p$의 표준기저를 $e_a$로 쓰면 $Ae_a$의 $e$번째 성분은 민감도 $S_{e,\cdot a}$다. 그러므로 임의의 $v\in\mathbb R^p$에 대하여

$$
\begin{aligned}
\|Av\|_{\mathcal Y,R}^2
&=\sum_{e=1}^{E}\int_0^{T_e}
v^\top S_e(\tau;\vartheta_*)^\top R_e(\tau)^{-1}S_e(\tau;\vartheta_*)v\,d\tau\\
&=v^\top\mathcal I(\vartheta_*)v.
\end{aligned}
$$

유클리드 내적과 위 가중 Hilbert 내적에 관한 수반연산자를 $A^*$로 쓰면 이 등식은 $\mathcal I(\vartheta_*)=A^*A$를 뜻한다. $\mathcal I(\vartheta_*)\succ0$이면 $Av=0$인 $v$는 $v=0$뿐이므로 $A$는 단사다. 이 단사성을 유한차원 출력으로 읽기 위해 다음 bounded readout을 둔다.

$$
L:=\mathcal I(\vartheta_*)^{-1}A^*:\mathcal Y\to\mathbb R^p.
$$

$\mathcal I(\vartheta_*)$는 양의 정부호 $p\times p$ 행렬이므로 역행렬이 존재하고, $A^*$와 합성한 $L$도 bounded다. 정의에서

$$
LA=\mathcal I(\vartheta_*)^{-1}A^*A=I_p.
$$

이제 $\Psi=L\circ\Phi:\Theta\to\mathbb R^p$라고 두면 $\Psi$는 $C^1$이고 $D\Psi_{\vartheta_*}=I_p$다. 도메인과 공역이 모두 유한차원인 통상적 역함수 정리에 따라, $\vartheta_*$의 어떤 열린 근방 $U$에서 $\Psi|_U$는 일대일이다. $\vartheta_1,\vartheta_2\in U$에서 $\Phi(\vartheta_1)=\Phi(\vartheta_2)$이면 $\Psi(\vartheta_1)=\Psi(\vartheta_2)$이고, 따라서 $\vartheta_1=\vartheta_2$다. 그러므로 $\Phi|_U$가 일대일이며 정리가 따른다. $\square$

이 정리는 전역 일대일성, 임의 주변 계량의 복원, 모델 정확성, 또는 관측되지 않은 nuisance의 식별성을 주지 않는다. Gramian은 충분조건이며, 실제 적용에서는 gauge 고정, 입력·초기조건의 알려짐, 동역학의 적합성, 그리고 충분히 자극적인 개입을 별도로 검증해야 한다.

## 따름정리 C2와 특이 Gramian의 경계

**[따름정리 C2]** $\Phi$가 $C^2$이고 영-잔차 손실을

$$
\mathcal L(\vartheta)=\frac12\|\Phi(\vartheta)-\Phi(\vartheta_*)\|_{\mathcal Y,R}^2
$$

로 두면 $\nabla^2\mathcal L(\vartheta_*)=\mathcal I(\vartheta_*)$다. 따라서 T3의 조건 아래 $\vartheta_*$는 고립된 strict local minimizer다.

**증명.** 잔차를 $r(\vartheta)=\Phi(\vartheta)-\Phi(\vartheta_*)$로 두면 좌표 미분은

$$
\partial_a\mathcal L=\langle\partial_a\Phi,r\rangle_{\mathcal Y,R},
\qquad
\partial_{ab}^2\mathcal L=\langle\partial_a\Phi,\partial_b\Phi\rangle_{\mathcal Y,R}+\langle\partial_{ab}^2\Phi,r\rangle_{\mathcal Y,R}.
$$

기준점에서는 $r(\vartheta_*)=0$이므로 둘째 항이 사라지고 Hessian은 $A^*A=\mathcal I(\vartheta_*)$다. 양의 정부호 Hessian에 대한 2차 충분조건이 고립된 strict local minimum을 준다. $\square$

Gramian이 특이면 어떤 $v\ne0$에 대해 $Av=0$이고, $\Phi(\vartheta_*+sv)=\Phi(\vartheta_*)+o(s)$인 일차 blind direction이 있다. 그러나 이것만으로 전역 또는 고차 비식별성을 결론낼 수는 없다. 예를 들어 $\Phi(\theta)=\theta^3$는 $\theta_*=0$에서 Gramian이 $0$이지만 여전히 국소적으로, 더 나아가 전역으로 일대일이다. 따라서 특이성은 T3의 충분조건 실패이지 일반적 비식별성의 증명은 아니다.

## 정리 W1: 무한 주변공간의 능동 복원 witness

**[정리 W1]** 상태공간을 $\mathcal H=\mathbb R^2\oplus\ell^2$로 두고 $q=(x,z,w)$라 하자. $\kappa=0.30$, $\theta\in\mathbb R$에 대하여

$$
G_\theta=\operatorname{diag}(1,e^\theta)\oplus I_{\ell^2},
$$

$$
V_u(x,z,w)=\frac12(x-z)^2+\frac\kappa2z^2-u(\tau)z+\frac12\|w\|_{\ell^2}^2.
$$

각 고정된 $\theta$에서 $G_\theta$는 strong metric이고

$$
\min(1,e^\theta)\|h\|^2\le\langle h,G_\theta h\rangle\le\max(1,e^\theta)\|h\|^2.
$$

$u\in L^\infty([0,T])$와 $q(0)=0$에 대해 metric gradient flow $q'=-G_\theta^{-1}\nabla V_u$ 및 관측 $y=x$를 쓴다. $u(\tau)=u_0\ne0$가 $[0,\epsilon)$에서 상수이면 다음의 우미분 식이 성립한다.

$$
y'(0+)=0,
\qquad
y''(0+)=e^{-\theta}u_0,
\qquad
\theta=-\log\!\left(\frac{y''(0+)}{u_0}\right).
$$

**증명.** Hilbert 기울기는 $\nabla V_u=(x-z,(1+\kappa)z-x-u,w)$다. 따라서 운동방정식은

$$
x'=z-x,
\qquad
z'=e^{-\theta}\bigl(x-(1+\kappa)z+u\bigr),
\qquad
w'=-w,
\qquad y=x.
$$

입력은 유계 가측이고 우변은 상태에 대해 bounded linear이므로 유일한 absolutely-continuous Carathéodory 해가 존재한다. $w(0)=0$이면 $w(\tau)=0$이므로 $\ell^2$ block은 남아 있으나 두 좌표 부분계는 불변이다. 상수 입력의 오른쪽 근방에서 $x(0)=z(0)=0$이므로 $x'(0+)=0$이며, 위 식을 한 번 더 사용하면 $x''(0+)=z'(0+)-x'(0+)=e^{-\theta}u_0$다. $e^{-\theta}>0$이고 $u_0\ne0$이므로 비율은 양수이고 로그가 정의되어 복원식이 따른다. $\square$

이 witness는 무한 차원을 없애지 않는다. $\ell^2$ spectator block은 그대로 남고 복원의 대상도 아니다. 반대로 동일한 초기조건에서 $u\equiv0$이면 유일해는 $q\equiv0$이므로 $y\equiv0$, 민감도 $S\equiv0$, Gramian은 $0$이다. 즉 active-positive와 zero-control의 차이는 “무한 공간을 모두 보았는가”가 아니라, 사전 제한한 한 좌표가 출력 궤적에 실제로 들어왔는가다.

## 무차원성 감사

시간 $\tau$, 상태 $x,z,w$, 입력 $u$, potential $V_u$, 계량 비율 $e^\theta$를 모두 기준 스케일로 무차원화했다. 따라서 $\theta$와 $e^\theta$, $\mathcal I=\int S^\top R^{-1}S\,d\tau$, 그리고 $y''(0+)/u_0$가 무차원이다. 로그의 인자는 양의 무차원 비율이고, held-out normalized squared error의 분자와 분모도 같은 무차원 제곱 출력 노름이다. 이 감사는 수학식의 단위 일관성에 한정되며 생물학적 단위나 측정 가능성을 주장하지 않는다.

## 결정론적 합성 구현

수학 증명과 구현은 별개다. 구현은 W1의 우미분을 샘플 자료에서 추정하지 않고, 사전 고정된 궤적 적합이 같은 구조를 재현하는지만 검사했다. 기준값은 $\theta_*\in\{-1.20,-0.40,0.30,1.10\}$, 시간 구간은 $T=4.0$, 간격은 $\Delta\tau=0.005$다. TRAIN-A와 TRAIN-B만으로 $[-1.5,1.5]$의 241개 grid 및 80회 golden-section refinement로 $\theta$를 적합했고, HOLDOUT-C는 적합 뒤 한 번만 평가했다. 중앙차분 간격은 $10^{-5}$이며 active Gramian은 두 train 궤적의 민감도로 계산했다.

사전 고정한 성공 기준은 모든 기준값에서 $|\widehat\theta-\theta_*|\le10^{-6}$, held-out NSE $\le10^{-10}$, active Gramian $>10^{-8}$이며, NEGATIVE-ZERO에서는 Gramian과 grid-loss spread가 모두 각각 $10^{-20}$ 이하여야 한다. 결과는 다음과 같다.

| 항목 | 사전 기준 | 결과 | 해석 |
|---|---:|---:|---|
| 최대 매개변수 오차 | $\le10^{-6}$ | $2.220446049250313\times10^{-16}$ | 결정론적 적합은 모든 기준값을 재현했다. |
| active Gramian | $>10^{-8}$ | $0.02411321617958606$–$0.04213001401324671$ | 사전 고정한 active 입력에서 일차 민감도가 사라지지 않았다. |
| 최대 held-out NSE | $\le10^{-10}$ | $1.4204367480745902\times10^{-32}$ | 사용하지 않은 입력 궤적에서도 합성 출력이 일치했다. |
| zero-control Gramian | $\le10^{-20}$ | $0$ | 영입력에는 식별 정보가 없었다. |
| zero-control loss spread | $\le10^{-20}$ | $0$ | 영입력에서는 어느 $\theta$도 출력으로 구별되지 않았다. |

첫 구현은 negative-control loss를 active TRAIN schedule에 대해 계산하여 STOP했다. 이는 동역학식, 데이터, 기준값, 임계값, 적분기, estimator를 바꾼 실패가 아니라, 고정된 NEGATIVE-ZERO 정의와 맞지 않는 코드 경로였다. 수정 범위는 해당 loss 평가가 zero-input schedule을 사용하도록 바꾼 계산 경로에 한정됐으며, 공식·자료·프로토콜·임계값은 바꾸지 않았다. 최종 수령증은 이 code-only 정정 뒤의 결과다.

## 선행 no-go와의 관계 및 중립적 관측 비교

BA-OBS-NOGO1은 임의 주변 계량과 유한 수동 관측의 조합에서 관측 quotient만 정해지고 숨은 block 및 주변 차원은 정해지지 않음을 보였다. 본 보고서는 그 명제를 약화하거나 삭제하지 않는다. T3는 임의 계량 대신 gauge-fixed 유한 계량족만 허용하고, 점별 수동 map 대신 알려진 동역학과 여러 개입이 만든 전체 출력 궤적을 쓴다. 그러므로 두 결론의 논리형은 서로 다르다.

$$
\text{arbitrary ambient metric + finite passive map}
\Longrightarrow\text{non-identifiable},
$$

$$
\text{finite gauge-fixed family + known dynamics + informative intervention}
\xRightarrow{\mathcal I\succ0}\text{locally identifiable family coordinate}.
$$

수동 중립 대조는 이 차이를 합성적으로만 보인다. 영입력에서는 모든 참값이 영출력을 만들어 loss landscape가 평평했으며, 능동 입력에서는 같은 모델의 제한된 좌표가 궤적에 들어와 Gramian이 양수가 되었다. 이것은 EEG, fMRI, 단일세포, connectome 자료와 비교한 결과가 아니며, 생물학적 기전의 증거도 아니다.

## 미완성 다리

실제 신경계가 유한하고 gauge-fixed인 어떤 계량족으로 충분히 표현되는지, 그 동역학과 관측 연산자가 알려졌는지, 윤리적·기술적으로 충분한 개입이 가능한지, 실제 자료에서 Gramian이 양의 정부호인지가 모두 미검증이다. 더구나 의식이 특권적 현재 세계 다양체인지, 자아가 궤적의 길이인지, 해마가 해시 역할인지, 세계모델의 유효 차원이 $3+1$인지에 대해서는 이 run이 정의·증명·데이터를 제공하지 않는다. 그 질문들은 이 합성 witness를 인용하여 닫을 수 없고, 독립된 생물학적 출발기전·측정모형·사전 고정 holdout 및 개입 검증을 요구한다.

## 재현성

고정 계약과 수학 근거는 [00-contract.md](00-contract.md), [11-math.md](11-math.md), 경로 선택은 [12-routes.md](12-routes.md), 안정 감사는 [20-audit.md](20-audit.md), 구현 및 검증은 [30-implementation.md](30-implementation.md), [31-validation.md](31-validation.md)에 있다. 이 문서가 읽은 route ledger의 SHA-256은 `5dea30dfe8f22f322554fe350284cb84a484bc7f57cd493c23d34c0c7598c578`이다. 입력 stage hash는 순서대로 `224c2a6701144cca089dd2a60054e443401b8ec4a1c28095281b947e412fbdc1`, `b9f743852bc60dd5f15572b9ad358c006de838b3efdf88128d8553a63177c8f9`, `982574ca384336329a557249e58304d102d2711c979b05468b004cc7be05573f`, `17394fffe0b40b41739170b25159f2f7e1997b8e43e700072a0cf659a8222b8a`, `66d8334b0d5c844569ae7aac85b38238a79787448c6f7a036d423abb5a01f361`, `8a3d1fe4da7ef244b3c0e087ef02f1a352115fb01b8e7ac5521243fc24f63551`, `c74e50ef601904dead2ee1729685fe4e5f9ff34c69d4dcbd421141f8907bfe20`이다. validator script, receipt의 SHA-256은 각각 `5e6f5f71dffdb3a2d0be84a4b614ec1518a167b1440721e245b98d4e3b061d8b`, `9adc50dac7df5ba87a75a357c2414dd0575a1777621eef59ffeb76075dd54b49`이다.

재현 명령은 다음과 같다.

```text
.codex\hooks\python.cmd doctor
.codex\hooks\python.cmd python -c "from pathlib import Path; compile(Path(r'_workspace/ce/brain-finite-observation-metric-identifiability-escape-20260824/artifacts/validate_metric_escape.py').read_text(encoding='utf-8'), 'validate_metric_escape.py', 'exec')"
.codex\hooks\python.cmd python _workspace\ce\brain-finite-observation-metric-identifiability-escape-20260824\artifacts\validate_metric_escape.py
```

## 참고문헌

Bellman, R. and Åström, K. J. (1970). On structural identifiability. *Mathematical Biosciences*, 7(3–4), 329–339. [DOI](https://doi.org/10.1016/0025-5564(70)90132-X), accessed 2026-08-24.

Hermann, R. and Krener, A. J. (1977). Nonlinear controllability and observability. *IEEE Transactions on Automatic Control*, 22(5), 728–740. [DOI](https://doi.org/10.1109/TAC.1977.1101601), [author PDF](https://www.math.ucdavis.edu/~krener/1-25/10.IEEETAC77.pdf), accessed 2026-08-24.

Ambrosio, L., Gigli, N. and Savaré, G. (2008). *Gradient Flows in Metric Spaces and in the Space of Probability Measures*, 2nd ed. Birkhäuser. [DOI](https://doi.org/10.1007/978-3-7643-8722-8), accessed 2026-08-24.

Absil, P.-A., Mahony, R. and Sepulchre, R. (2009). *Optimization Algorithms on Matrix Manifolds*. Princeton University Press. [Publisher record](https://press.princeton.edu/books/hardcover/9780691132983/optimization-algorithms-on-matrix-manifolds), accessed 2026-08-24.
