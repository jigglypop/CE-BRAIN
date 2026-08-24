# BA-OBS-ID1 route decision

Status: COMPLETE

## 질문을 푸는 최소 경로

선행 no-go가 막은 것은 임의의 ambient metric을 유한 수동 관측에서 복원하는 경로다.
따라서 이번 판본은 정의역을 바꾼다. 무한차원 상태공간은 그대로 두고, 미지수만
gauge-fixed finite metric family의 좌표 $\vartheta\in\mathbb R^p$로 제한한다. 그런 뒤
점별 observation pullback이 아니라 알려진 동역학과 여러 개입이 만드는 전체 궤적 map
$\Phi(\vartheta)$를 조사한다.

| route | disposition | reason |
|---|---|---|
| positive-definite sensitivity Gramian $\Rightarrow$ local identifiability | SELECTED | 유한 매개변수 정의역에서 bounded readout과 역함수정리로 닫을 수 있는 가장 좁은 충분조건이다. |
| metric gradient-flow witness의 $y''(0+)$ 복원식 | SELECTED | hidden metric scale가 개입 뒤 관측 가능한 가속도에 들어가는 것을 폐형식으로 보인다. |
| 동결 TRAIN에서 추정하고 별도 HOLDOUT 입력에서 예측 | SELECTED AS SYNTHETIC RECEIPT | 수학 정리와 구현 오류를 분리해 확인하며 경험적 증거로는 승격하지 않는다. |
| $u\equiv0$ matched control | SELECTED NEGATIVE CONTROL | 동일 모델에서도 excitation이 없으면 Gramian과 식별성이 함께 사라져야 한다. |
| 임의의 infinite-dimensional ambient metric 직접 복원 | KILLED BY PREDECESSOR | BA-OBS-NOGO1의 hidden-block witness와 충돌한다. |
| singular Gramian이면 전역 비식별이라고 결론 | REJECTED | singularity는 일차 민감도 kernel만 보이며 고차 식별성까지 배제하지 않는다. |
| 일반 정리에서 전역 단사성 주장 | REJECTED | inverse function theorem이 주는 결론은 국소 단사성이다. |
| 실제 EEG·뉴런·의식 데이터로 이동 | NOT OPENED | 이 판본은 수학과 결정론적 합성 witness만 사전등록했다. |
| 의식의 유효차원 또는 자아 궤적 해석 | PROHIBITED | 식별성 탈출 조건은 그런 존재론적 명제를 함의하지 않는다. |

## 단계별 kill rule

1. **수학 kill:** $\mathcal I\succ0$인데도 계약의 가정 아래 $\Phi$가 국소 단사가
   아닌 반례가 있거나, finite-dimensional readout 구성이 bounded하지 않으면 T3를
   기각하고 구현을 열지 않는다.
2. **witness kill:** $G_\theta$가 strong metric이 아니거나 gradient-flow 식,
   $y''(0+)=e^{-\theta}u_0$, log 복원식 가운데 하나라도 틀리면 W1을 기각한다.
3. **무차원 kill:** exp/log/Gramian/손실의 입력이 기준 스케일 없이 차원을 가지면 식을
   코어에 넣지 않는다.
4. **구현 kill:** 안정된 수학 감사 뒤에만 동결된 수치 프로토콜을 1회 실행한다. 한
   PASS 문턱이라도 실패하면 결과에 맞춰 같은 run의 식·입력·문턱을 바꾸지 않는다.
5. **해석 kill:** synthetic PASS가 나와도 실제 brain metric, consciousness, self,
   hippocampal hash, 3+1 world model 또는 AGI 검증으로 승격하지 않는다.

## no-go와 탈출 정리의 관계

두 결과는 모순이 아니다.

$$
\text{arbitrary ambient metric + finite passive map}
\quad\Longrightarrow\quad
\text{non-identifiable},
$$

반면 이번 경로는

$$
\text{finite gauge-fixed family + known dynamics + informative intervention}
\quad\Longrightarrow[\mathcal I\succ0]{}\quad
\text{locally identifiable family coordinate}
$$

를 증명하려 한다. hidden directions 전체를 데이터가 알아낸 것이 아니라, 모델 가정이
그 자유도를 미리 제거하고 남은 유한 좌표가 궤적에 충분히 민감하게 나타나는 경우다.

## Claim ceiling

`MATHEMATICAL_LOCAL_IDENTIFIABILITY_WITHIN_A_GAUGE_FIXED_FINITE_METRIC_FAMILY / DETERMINISTIC_SYNTHETIC_INTERVENTION_WITNESS / INFINITE_AMBIENT_SPACE_ALLOWED_BUT_NOT_RECOVERED / NO_EMPIRICAL_BRAIN_CONSCIOUSNESS_SELF_OR_AGI_VALIDATION`
