# BA-OBS-DISC1 순차 검증

Status: COMPLETE

이 실행의 결론은 `COMPLETE_WITH_NEGATIVE_GATE / CANDIDATE_KILLED_AT_D2 / NOT_CONFIRMED`이다. D0의 CABLE 선택과 D1 통과는 D2에서의 primary bipolar 재현을 보장하지 못했다. 따라서 D3의 40쌍은 열지 않았고, 이 판본에는 확인된 식이 남지 않는다.

## 자료와 검증 장치

OpenNeuro `ds003708`의 단일 epilepsy 환자 6 mA CCEP에서 얻은 255 적격 epoch를 사용했다. endpoint를 보지 않은 151 pair를 D0 24쌍, D1 48쌍, D2 39쌍, D3 40쌍으로 사전 분할했다. D0 apparatus는 48 directed edge의 cross-half Spearman과 post/prestimulus ratio를 확인했다. bipolar는 $0.4198388860917723$ 및 $1.864798356503853$, mean은 $0.5009175506519209$ 및 $1.9592438778517676$으로 모두 사전 문턱을 통과했다.

후속 단계에서는 D0에서 고른 CABLE 구조를 바꾸지 않고, 이전에 열린 자료로만 수치 계수를 재적합해 다음 단계의 쌍에 예측을 냈다. primary bipolar gate는 source별 loss 개선 평균이 양수이고, source-cluster bootstrap 95% 구간의 하한이 양수이며, geometry descriptor의 joint permutation $p_{\rm geom}\le0.05$일 때만 통과한다. 같은 계산을 mean에도 적용했지만 mean은 primary를 대체하지 않는 reference 진단이다.

## D1 fast-kill 통과

D1의 48 held-out pair와 24 stimulation source에서 bipolar 평균 개선은 $0.036304411549773374$였다. source-cluster 95% 구간은 $[0.01139441475506768,\,0.06097480548090294]$, $p_{\rm geom}=0.000975609756097561$로 세 조건을 모두 통과했다. mean도 개선 $0.03337053090752439$, 95% 구간 $[0.009315193535500685,\,0.05803188956697309]$, $p_{\rm geom}=0.000975609756097561$로 통과했다. 이 결과는 CABLE이 첫 독립 단계에서 B0보다 나은 관측 response 예측 후보였음을 뜻하지만, 여전히 한 단계의 중간 검증일 뿐이다.

## D2 intermediate 기각

D2의 39 held-out pair에서 bipolar 평균 개선은 여전히 양수인 $0.02351873345804861$이고, geometry permutation도 $p_{\rm geom}=0.001951219512195122$였다. 그러나 source-cluster bootstrap 95% 구간은 $[-0.005757602832834792,\,0.04929832365415101]$으로 0을 가로질렀다. primary bipolar gate는 이 조건 하나만으로 실패하며, receipt 상태는 `SEQUENTIAL_BIPOLAR_GATE_FAIL`이다.

이 조합은 모순이 아니다. permutation 유의성은 관측된 geometry association이 descriptor를 무작위로 섞은 경우보다 크다는 뜻이다. 반면 bootstrap 구간이 0을 가로지른다는 것은 stimulation source를 다시 표본화했을 때 평균적인 예측 이득의 부호가 안정적이지 않다는 뜻이다. 즉 기하 descriptor와 반응 사이의 연관 신호는 있어도, B0보다 낫다는 평균 predictive benefit이 source 전반에서 견고하다고 말할 수 없다.

mean 진단은 D2에서 개선 $0.030867609165603892$, 95% 구간 $[0.003784792373941817,\,0.05676835240113891]$, $p_{\rm geom}=0.000975609756097561$로 통과했다. 하지만 reference가 바뀌면 결론이 바뀔 수 있다는 신호이므로, mean 통과는 bipolar의 primary 실패를 보정하지 않는다.

## 종료 규칙

D2 실패 뒤 D3 40쌍은 unopened이며 receipt도 존재하지 않는다. 이 고정 판본에서는 공식·time window·threshold·선택 규칙을 고친 뒤 D3을 실행하지 않는다. 수정된 후보군을 시험하려면 새 preregistration, 새로운 unopened validation pool 또는 독립 subject가 필요하다. 이 결과는 CABLE의 완전한 생물학적 반증도, 어떤 리만 계량이나 의식 이론의 반증도 아니다. 이 실행이 기각한 것은 이 단일-환자 관측 조건에서의 고정된 CABLE 후보가 primary sequential gate를 통과한다는 주장이다.
