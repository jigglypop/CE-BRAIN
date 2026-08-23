# BA-ERC1-E3a: 관측 평균이 지우는 가지-대조 정보

Status: COMPLETE  
Verdict: PASS — `E3A_OBSERVATION_QUOTIENT_SYNTHETIC_ONLY`

## 결과와 실질적 의미

평균만 남긴 데이터는 반대칭 가지 모드 $A0$를 구별할 수 없다. 세 가지 전압을 평균하면 $A0$의 값은 모든 시각에서 정확히 0이므로, 시간 표본을 아무리 촘촘히 늘려도 그 관측만으로 cable 대 point의 이 seam을 시험할 수 없다. 반대로 같은 위치의 세 branch-resolved 전압은 $A0$ 전체를, 혼합 모드 $M1$에서는 총 관측 에너지의 $35.3474\%$를 branch-shared 성분 밖에 보존했다. 이는 특정한 무잡음 합성 관측 설계가 어떤 정보를 버리는지를 확인한 결과이며, 실제 기록 일반론이나 생물학적 식별 결과는 아니다.

## 무엇과 무엇을 비교했는가

E2의 정확한 수동 Y-cable 장을 같은 호길이 $s_0=0.6$에서 세 간선 모두 측정하고, $[0,0.2]$의 41개 시각에 표본화했다. $S1$은 세 가지가 같은 대칭 모드, $A0$은 branch contrast만 남는 반대칭 모드, $M1$은 둘의 혼합이다. 가장 강한 scalar baseline으로, 매 시각마다 새 값을 자유롭게 고를 수 있는 branch-shared oracle을 허용했다. 이 baseline은 어떤 scalar ODE를 적합한 것보다 강하다. 그럼에도 oracle은 세 관측의 평균 방향만 재현할 수 있고, 다음 사영 잔차를 줄일 수 없다.

$$
\Pi=\frac13\mathbf1\mathbf1^T,
\qquad
\eta_\perp=\frac{\|(I-\Pi)Y\|_F^2}{\|Y\|_F^2}.
\tag{1}
$$

여기서 $Y$는 $3\times41$ branch-voltage 행렬이고, $\eta_\perp$는 point oracle이 되살릴 수 없는 branch-contrast 에너지의 비율이다. projector는 rank 1이고 대칭·멱등·shared-subspace 오류가 모두 0이었다.

## 봉인된 점검

$S1$의 $\eta_\perp$는 $1.25188\times10^{-32}$이고 oracle 상대오차는 $1.11887\times10^{-16}$였다. 따라서 대칭 모드는 의도한 대로 branch-shared point output과 구별되지 않는다. $A0$에서는 $\eta_\perp=1$ 및 oracle 상대오차 1이 나왔고, branch mean의 최대 절댓값은 0이었다. 즉 세 channel은 $A0$를 완전히 보존하지만 평균 관측은 정확히 quotient로 없앤다. $M1$의 $\eta_\perp=0.3534735545$와 oracle 상대오차 $0.5945364198$은 혼합된 상태에서도 전체 관측 에너지의 35.35%가 scalar shared readout 밖에 남는다는 뜻이다.

이 PASS는 analytic machine certificate이며, 설계상 선형대수의 tautology다. 기계는 projector 구성, 표본 조립, 수치 경계, hash와 seal, 그리고 평균 no-go control이 계약대로 실행됐음을 확인한다. 새 생물학적 법칙을 발견했거나 실제 recording에서 point neuron을 배제했다는 증거는 아니다. post-run audit SHA-256은 `0ed074b4f467c9287841211d9d1be900a1428dcc378de090e3b908be5bb24f74`이고, receipt는 failed check 0개 및 모든 promotion flag의 false를 기록한다.

## 제한과 다음 경계

결과는 동일 가중치, 동일 호길이, 동일 전압형, 무잡음 sensor, 고정 branch 순서와 공통 clock을 전제한다. 알려지지 않은 gain·offset·filter·time warp·missing channel, 가중 평균, 다른 sensor 배치, 실제 morphology는 이 certificate의 범위 밖이다. 또한 per-time oracle의 실패는 이 사영 관측에서의 결과일 뿐, 다른 observation map 아래 모든 point-neuron 모형에 대한 no-go 정리는 아니다.

정확한 claim ceiling은 `SYNTHETIC_BRANCH_OBSERVATION_QUOTIENT_IDENTIFIABILITY / E3A_ANALYTIC_SCREEN_ONLY / BIOLOGICAL_VALIDATION_UNOPENED`이다. 실제 데이터, 적합된 모형, 행동, 상태 차원, 의식·기억·해마·AGI에 관한 주장은 열리지 않았다. E3b history-synapse 비교는 별도의 계약으로 관측모형·대조군·falsifier·분할을 다시 동결하기 전까지 locked 상태다.
