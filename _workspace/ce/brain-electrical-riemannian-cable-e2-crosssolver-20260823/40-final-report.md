# BA-ERC1-E2: 수동 Y-케이블의 독립 이산화 교차검증

Status: COMPLETE  
Verdict: PASS — `E2_CROSSSOLVER_MANUFACTURED_ONLY`

## 결과

동일한 수동 metric-graph Y-케이블을 보존적 cell-centred finite-volume(FV/RK4)와 shared-node finite-element(FEM/generalized eigen)로 각각 풀었을 때, 봉인된 세 panel 모두에서 두 해법은 정확 해와 서로에게 정해 둔 오차 한계 안에서 수렴했다. 이는 수동·무차원·합성 문제에 한정한 교차 solver 수치 검증이며, 생물학적 검증이나 독립 실험 재현은 아니다. post-run audit의 SHA-256은 `2e64fe533dba988363346f2425d22d1601b3897ccb39676170c5a501d0e8f0d3`이고, receipt는 source·predecessor·preflight archive·environment seal의 일치와 failed check 0개를 기록한다.

## 무엇을 계산했는가

세 동일 길이 간선이 중앙 정점에서 만나고, 각 간선의 바깥 방향 좌표를 $s\in[0,1]$로 잡았다. 검증한 식은

$$
\partial_\theta u_e=D_*\partial_s^2u_e-\kappa_*u_e,
\qquad D_*=0.2,\quad\kappa_*=0.3,
\tag{1}
$$

이며, 중앙에서는 전압 연속성과 $\sum_e\partial_su_e(0,\theta)=0$, 말단에서는 sealed-end 조건을 둔다. $S1$은 세 간선에 같은 $\cos(\pi s)$를 주는 대칭 모드라서 양의 대조군이다. $A0$은 계수 $(1,-1,0)/\sqrt2$를 갖는 $\sin(\pi s/2)$ 반대칭 모드로, 중앙 연속성과 Kirchhoff 접합을 확인하는 sealed confirmation panel이다. $M1$은 두 모드의 혼합으로 선형 중첩이 두 sector에서 함께 보존되는지 시험한다. 반대로 $D0$은 $A0$ 초기값을 유지하되 중앙의 세 면을 서로 분리된 sealed face로 잘못 처리한 adverse control이다. $S1$만 맞아도 분리된 세 가지는 우연히 비슷해질 수 있으므로, $A0$, $M1$, $D0$이 접합 조건을 실제로 구별하는 장치다.

## 수치 결과

미세 격자 $N=64$에서 $S1$의 FV/FEM 정확해 오차는 각각 $7.92685\times10^{-5}$, $3.80432\times10^{-4}$이고 solver 간 오차는 $4.59876\times10^{-4}$였다. $A0$에서는 각각 $4.95440\times10^{-6}$, $8.02524\times10^{-5}$, $8.52136\times10^{-5}$였고, $M1$에서는 $7.52312\times10^{-5}$, $3.61866\times10^{-4}$, $4.37175\times10^{-4}$였다. 모든 값은 사전 고정한 $10^{-3}$ 이하 조건을 통과했다.

각 solver와 각 panel의 $32\rightarrow64$ 정확해 오차 비는 $3.99887$에서 $3.99982$ 사이다. 이는 최소 기준 3을 넘고 사실상 4에 가까우므로 이 장치의 두 해법이 예상한 2차 공간 수렴을 보인다는 뜻이다. FV의 최대 강한 Kirchhoff 잔차는 $5.68434\times10^{-14}$, FEM의 최대 약한 잔차는 $4.38028\times10^{-12}$로 각각 $10^{-12}$, $10^{-11}$ 한계 안에 들었다. shared node의 FEM 전압 연속 잔차는 정확히 0이었고, 표본화한 에너지는 증가하지 않았다. 질량행렬 Cholesky 분해도 모든 격자에서 성공했으며 일반화 고유값의 최솟값은 허용 오차 범위의 수치적 0이었다.

$D0$은 정답인 결합 star 해에 대해 $0.163843$의 오차를 냈다. 요구한 adverse-control 신호 $0.02$보다 약 8.2배 크므로, 이 검증은 잘못 분리된 중앙 접합을 통과시키지 않았다.

## 보존한 STOP과 해석 한계

첫 preflight는 반대칭 모드의 말단 경계 증명에 들어간 잘못된 cosine token 때문에 STOP으로 끝났다. STOP math와 audit은 각각 `36e133bf59a428c9658ad82ae3adc59c8cce708c30781a143447f2c161909713`, `91e6dc6797780a5b6f6545152c489111b514b613d449d0b42b7df6ac6a06419d`로 보존했다. verifier를 만들기 전 그 token과 명시적 합 표기만 바로잡았고, PDE, exact mode, panel, mesh, coefficient, solver, threshold, split, claim ceiling은 바꾸지 않았다.

두 P1 한계도 결과의 일부다. 첫째, FV의 Kirchhoff 조건은 common face value가 구조적으로 강제하므로 그 잔차만으로 연속 방정식의 충실도를 증명하지 않는다. $A0$의 정확해 수렴과 $D0$ 검출이 이 취약점을 보완한다. 둘째, FEM의 약한 잔차는 같은 generalized eigenpair에서 재구성하므로 독립적인 점별 flux 측정이 아니라 eigensolver 내부의 대수적 정합성 검사다. 이 경우에도 외부 기준은 $A0$의 정확해 수렴이다. 따라서 “독립 solver”는 서로 다른 이산화와 시간전파 경로를 뜻하며, 독립 팀·실험실·생물학적 재현을 뜻하지 않는다.

## 결론과 다음 경계

이 PASS가 허용하는 정확한 주장 상한은 `PASSIVE_METRIC_GRAPH_CROSSSOLVER_EQUIVALENCE / SYNTHETIC_MANUFACTURED_STIMULI / E2_NUMERICAL_VALIDATION_ONLY / BIOLOGICAL_VALIDATION_UNOPENED`이다. 수동 equal-edge Y-케이블의 봉인된 합성 자극에서 두 수치 구성의 2차 예측이 일치했다는 것까지가 결론이다.

실제 morphology와 생물학적 파라미터, active HH 전파, 유한 상태와 history synapse의 모델 선택, 상태공간 계량, effective dimension, 실제 신경자료, 행동, 의식·기억·해마·AGI는 이 실행에서 검증하지 않았고 어떠한 승격도 없다. E3는 이 PASS로 자동 열리지 않으며, 비교 모형·관측량·falsifier·분할을 새로 동결한 별도 계약이 있어야만 고려할 수 있다.
