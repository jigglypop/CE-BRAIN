# BA-ERC1: 가지친 뉴런의 전기 케이블 방정식과 함수공간 기하

Status: COMPLETE  
Verdict: `L0_NUMERICAL_INTEGRITY_ONLY`

## 초록

이 보고서는 전압 전파를 관측 공분산이나 추상적 기하에서 시작하지 않고, 축방향 Ohm 전류와 전하 보존에서 시작하는 비선형 케이블--HH 모형으로 다시 세운다. 뉴런의 형상은 가지 정점에서 접합하는 metric graph이며, 리만 기하는 먼저 길이 좌표의 가중 연산자로 들어오고, 상태공간의 리만 계량은 별도로 정의한다. 시냅스는 $i\leftarrow j$에서 $j$가 $i$를 구동하는 유향 conductance이며, 후보 확장은 그 conductance를 엄격한 과거 이력의 유계 함수로 만드는 것이다. L0에서는 단위, 부호, Kirchhoff 보존, 수동 케이블의 감쇠와 수렴, 능동 비선형성, 인과적 매끄러운 kernel만 검사했다. 다섯 관문은 통과했지만 이는 수치적 내부 정합성일 뿐 생물학적 적합, 의식, 기억, 해마, AGI에 관한 증거가 아니다. 다음 단계는 독립 solver와 대조 모형을 통한 예측 비교이며, 실제 데이터는 새 계약 없이는 열지 않는다.

## 전기식의 출발점

전압 $V_e(s,t)$는 간선 $e$의 물리적 호길이 $s$ 위의 막전위, $A_e$는 세포내 단면적, $P_e$는 단위 길이당 막면적, $\sigma_{i,e}$는 세포내 전도도이다. 바깥쪽을 양의 막전류로 정하면 축방향 전류는

$$
I_{\parallel,e}=-\sigma_{i,e}A_e\partial_sV_e.
\tag{1}
$$

즉 전류는 전압 기울기를 거슬러 흐른다. 미소 구간의 전하 보존과 막 용량 전류를 함께 쓰면

$$
\partial_s I_{\parallel,e}+P_e i_{m,e}=0,
\qquad
i_m=c_m\partial_tV+i_{\rm ion}+i_{\rm syn}-i_{\rm ext},
\tag{2}
$$

이고, 따라서 지배 전기식은

$$
c_{m,e}\partial_tV_e=
\frac{1}{P_e}\partial_s\!\left(\sigma_{i,e}A_e\partial_sV_e\right)
-i_{{\rm ion},e}(V_e,w_e)-i_{{\rm syn},e}(V_e,h_t)+i_{{\rm ext},e}.
\tag{3}
$$

이다. 모든 항은 막전류 밀도 $\mathrm{A\,m^{-2}}$이고, current clamp의 A와 voltage clamp의 V를 더하지 않는다. 일정 반지름 $r$의 원통에서는 전달 항이 $(\sigma_i r/2)\partial_{ss}V$로 줄어든다. 이것이 먼저 검증할 전파식이며, 관측된 상관행렬은 이 식의 대체물이 아니라 뒤따르는 readout이다.

좌표 $x$에 대해 $ds=\sqrt{g_e(x)}dx$라 두면 전달 항은

$$
\frac{1}{P\sqrt g}\partial_x\!\left(
\frac{\sigma_iA}{\sqrt g}\partial_xV\right)
\tag{4}
$$

가 된다. 따라서 여기의 리만 기하는 무가중 $\Delta_g$를 선언하는 일이 아니라, 호길이·전도·테이퍼·막면적을 보존하는 weighted Laplace--Beltrami/Sturm--Liouville 연산자다. 막의 비선형성은 Hodgkin--Huxley형 전류

$$
i_{\rm ion}=\bar g_{\rm Na}m^3h(V-E_{\rm Na})+
\bar g_{\rm K}n^4(V-E_{\rm K})+g_L(V-E_L),
\tag{5}
$$

와 전압 의존 gate의 동역학에서 들어온다. 이는 매끄러운 계수와 호환되는 초기·경계 자료 아래 간선 내부에서 매끄러운 해를 허용하지만, branch 정점과 충격 입력까지 포함해 전역적으로 $C^\infty$라고 말할 근거는 아니다.

## 가지 접합과 인과적 시냅스

정점 $v$에서는 모든 인접 간선의 전압 trace를 같게 하고, 방향을 포함한 축전류가 Kirchhoff 법칙을 만족시킨다.

$$
V_e(v,t)=V_{e'}(v,t),
\qquad
\sum_{e\sim v}\nu_{e,v}\sigma_{i,e}A_e\partial_sV_e(v,t)=I_v^{\rm node}(t).
\tag{6}
$$

이 조건은 branch가 추상적 loop가 아니라 실제 전기 접합이라는 뜻이다. 시냅스의 기본 포트는 conductance times driving force,

$$
i_{ij}^{\rm syn}=g_{ij}^{\rm syn}(t)(V_i-E_{ij}),
\tag{7}
$$

이고 $i\leftarrow j$는 presynaptic $j$가 postsynaptic $i$를 구동한다는 약속이다. [가설] 후보 확장은 $g_{ij}^{\rm syn}$를 스칼라 가중치가 아니라 정규화된 과거 전압·전류밀도·gate·release 이력 $h_{ij,t}(a)$, $a>0$, 의 유계 함수로 두는 것이다.

$$
g_{ij}^{\rm syn}=g_{\min,ij}+(g_{\max,ij}-g_{\min,ij})
S\!\left(b_{ij}+\langle K_{ij},h_{ij,t}\rangle\right).
\tag{8}
$$

여기에는 $a=0$의 endpoint 평가나 Dirac 질량을 넣지 않아 현재 시각의 대수적 순환을 막는다. $C^\infty$이고 사건 뒤에만 지지되도록 하려면 $0<u<1$에서 $\exp[-1/(u(1-u))]$이고 그 밖에서는 0인 compact bump를 쓴다. 다만 유한한 지수 kernel들의 합은 보조 ODE로 유한차원 Markov 실현이 가능하다. 그러므로 “이력을 쓰는 모든 시냅스는 본질적으로 무한차원”이라는 주장은 반례로 폐기했으며, 이력 conductance는 유한상태 대조군을 이겨야만 남는다.

## 무한차원과 세 종류의 계량

무한차원성의 안전한 근거는 유한 개의 가지라도 $V(\cdot,t)$가 각 간선 위의 함수라는 점이다. 한 에너지 상태는 연속 trace를 갖는 $H^1(\Gamma)$ 전압장에 gate와 선택적 history field를 더한 함수공간이다. 매끄러움 자체가 무한차원성을 만들지는 않는다.

혼동을 피하려고 세 대상을 분리한다. 물리 형상 계량은 graph의 호길이이고, $\sigma_iA$는 전류를 운반하는 물성 계수이며, $\mathsf G_0$는 전압·기울기·gate·history의 미소 변화를 재는 선택된 상태공간 기준 계량이다. 유한 관측 $M$의 pullback $DM_X^*R^{-1}DM_X$는 관측하지 못하는 방향에서 0이므로, 전 상태공간의 리만 계량이 아니라 observable quotient 위의 반양정 계량이다. 여기서 유도할 수 있는 연속 effective dimension도 metric·window·관측·regularization에 의존하는 모드 진단량일 뿐, graph 차원이나 의식 차원이 아니다.

## L0 결과와 실패 보존

이번 실행의 판정은 오직 `L0_NUMERICAL_INTEGRITY_ONLY`이다. U0은 식의 모든 막 항이 $\mathrm{A\,m^{-2}}$임과 clamp 단위 혼합을 거부함을 통과했다. K0은 Y-branch의 정규화 전류 불균형 0과 Ohm 부호를 통과했다. P0은 수동 모드의 fine relative $L^2$ error $4.685124378672343\times10^{-5}$, coarse/fine 비 $4.002034508838505$, 에너지 비증가를 기록했다. N0의 정규화된 비선형 잔차는 $0.5369160749968305$였고, 선형 고정-conductance 대조군은 0이었다. H0은 사건 전·지지 밖 값 0, 정규화 오차 $2.22\times10^{-16}$, 시간반전 adverse control 검출, 닫힌 conductance 경계를 통과했다.

실패도 지우지 않았다. attempt-00은 U0, K0, P0, N0을 통과하고 H0만 실패했다. 원인은 $10^{-20}$의 부동소수점 endpoint proxy와 logistic 경계 처리였고, 전기식은 바꾸지 않은 채 H0 수치 predicate만 machine-precision 규모로 수정했다. 실패 receipt의 SHA-256은 `848a0a5ab528dc681eff9c384dbb0e733366ba3e89e45a2283399965658b41c4`, 최종 receipt의 SHA-256은 `9e643eaf70302ff4369f15bf1fa044f11660a45c9148869395fb65a643006501`이다. 이는 생물학적 실패나 성공이 아니라 apparatus 수준의 음성 산출과 국소 수정 이력이다.

## 다음 검증과 금지된 결론

다음에는 같은 봉인된 형상·자극으로 독립 cable solver를 비교하고(E2), 이어 active cable을 point neuron 및 passive cable과, 이력 conductance를 유한 지수 conductance와 비교한다(E3). 그 뒤에만 IC/VC 분리, filtering, jitter, missingness, time reversal을 포함한 measurement stress(E4)를 수행한다. 소규모 실제 데이터(E5)는 출처·측정모형·분할·falsifier가 새로 고정된 계약을 요구하고, held-out 또는 intervention(E6)이 그 다음이다.

[미완성] 이 보고서는 포유류 채널 파라미터, 실제 morphology, spike propagation, 이력 시냅스의 우월성, 생물학적 상태공간 계량을 검증하지 않았다. 의식의 4차원 고정면, curvature=consciousness 또는 memory, hippocampus=literal hash, 그리고 AGI에 관한 승격은 명시적으로 금지한다. 이전 BA-SRM9 관측-공분산 실험의 terminal futility는 보존하지만, 전기 케이블 방정식의 찬반 증거로 전용하지 않는다.

## 재현과 1차 출처

봉인된 L0 receipt를 생성한 명령은 다음과 같다. post-run ledger를 바꾼 뒤에는 이 명령의 새 출력으로 기존 receipt를 대체하거나 동등하다고 주장하지 않는다.

```powershell
.codex\hooks\python.cmd python _workspace\ce\brain-electrical-riemannian-cable-20260823\artifacts\verify_electrical_cable_l0.py --output _workspace\ce\brain-electrical-riemannian-cable-20260823\artifacts\l0-receipt.json
```

전기적 출발점은 [Hodgkin and Huxley (1952)](https://physoc.onlinelibrary.wiley.com/doi/10.1113/jphysiol.1952.sp004764)의 전압 의존 conductance, [Rall (1959)](https://pubmed.ncbi.nlm.nih.gov/14435979/)의 branching cable, [Yihe and Timofeeva (2020)](https://pmc.ncbi.nlm.nih.gov/articles/PMC6987294/)의 metric-graph cable 일반화에 둔다. Conductance synapse의 경험적 출발점은 [Destexhe et al. (2001)](https://pmc.ncbi.nlm.nih.gov/articles/PMC3320220/)이며, cable 가정의 상위 대조 경계는 [Pods, Sch\u00f6nke, and Bastian (2013)](https://pmc.ncbi.nlm.nih.gov/articles/PMC3703912/)의 Poisson--Nernst--Planck 전기확산이다.
