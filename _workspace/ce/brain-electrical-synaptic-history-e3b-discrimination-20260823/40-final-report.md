# BA-ERC1-E3b: 유한 지수 시냅스와 compact history kernel의 합성 판별

Status: COMPLETE  
Verdict: PASS — `E3B_FIXED_KERNEL_DISCRIMINATION_SYNTHETIC_ONLY`

## 결과

고정한 합성 장치는 자신이 만든 유한 두-상태 지수 응답에서는 $E_2$를, compact $C^\infty$ history bump 응답에서는 $B$를 선택했다. 즉 이 장치는 선언된 event split과 model menu 안에서 finite truth와 compact-bump truth를 혼동하지 않았다. 이 PASS는 실제 시냅스의 성질을 판정한 것이 아니라, 더 비싼 비선형·실험 단계 전에 selection apparatus가 최소한 자기의 두 합성 진실을 구별하는지 확인한 것이다.

## 시험한 식

유한 후보 $E_M$은 event 뒤 보조상태가 지수적으로 감소하는 선형 시냅스다.

$$
\frac{dx_m}{d\theta}=-\frac{x_m}{\tau_m},
\qquad
x_m(\theta_r^+)=x_m(\theta_r^-)+A_r,
\qquad
q_M(\theta)=\sum_{m=1}^M w_m\frac{x_m(\theta)}{\tau_m}.
\tag{1}
$$

비교 대상 $B$는 제한된 시간 구간에만 지지되고 끝점에서 flat한 비대칭 compact bump의 event convolution이다. calibration에서만 SVD least squares로 계수를 정하고, development에서는 메뉴를 고르고, confirmation은 그 선택을 바꾸지 않는 순서로 열었다. finite menu에는 $E_1,E_2,E_4,E_8$만 포함했다.

음성 generator $E_2$의 confirmation error는 $6.17410328886224\times10^{-16}$였고 tie-break는 $E_2$를 선택했다. 양성 bump generator에서는 $B$의 error가 $1.60615500530870\times10^{-16}$인 반면 최선 finite $E_8$은 $0.2270211315620434$였다. dense lag grid에서도 $E_8$의 kernel error는 $0.2891662558095040$였으며, time-reversed bump control은 $0.5722092307645735$의 error를 냈다. full-rank 설계와 최대 condition number $403.493915735834$까지 포함해 모든 사전 관문이 통과했다.

## 무엇이 성립하고 무엇이 성립하지 않는가

[정리: 조건부] 0이 아닌 compactly supported $C^\infty$ regular impulse response는 pure delay와 distributed state가 없는 유한차원 causal continuous-time constant-matrix LTI 시스템으로 정확히 실현할 수 없다. 그런 LTI 응답은 $Ce^{At}B$ 꼴의 해석함수이고, 어떤 열린 꼬리 구간에서 0이면 전체 양의 시간축에서 0이어야 하므로 nonzero bump와 모순한다.

그러나 이 정리는 “모든 유한차원이 불가능하다”는 말이 아니다. 유한 grid에서 $E_8$의 근사 오차가 반드시 일정 이상이라는 하한도 주지 않는다. 이번 $0.227$과 $0.289$의 여유는 고정된 8개 지수, 고정 time constant, 무잡음 직접 $q$ 표본, 고정 event split에서 얻은 합성 수치 결과다. 비선형, 지연, 더 높은 차수, Volterra, 다른 time constant, 실제 측정 filter나 전압 결합을 배제하지 않는다.

## 다음 경계

검증기는 AST parse, receipt seal, 무차원 규율, numerical audit을 통과했고 focused pytest도 `19 passed in 0.35s`였다. 이는 numerical integrity이지 biological truth가 아니다. 실제 synapse, 무한한 생물학적 차원, 의식, 기억이나 해마, AGI에는 어떤 증거도 추가하지 않는다.

정확한 claim ceiling은 `SYNTHETIC_HISTORY_SYNAPSE_OBSERVATION_DISCRIMINATION / E3B_FIXED_MODEL_MENU_ONLY / BIOLOGICAL_VALIDATION_UNOPENED`이다. E3b-3의 nonlinear Volterra/history route, cable/HH 재결합, measurement stress, real brain data는 이 PASS로 열리지 않는다. 각각은 대조군·관측모형·falsifier·분할을 다시 동결한 별도 계약을 필요로 한다.
