# 복구 권위의 형식 조건

Status: COMPLETE

이 run은 새 추정량을 정의하거나 수치를 변경하지 않는다. 선행 witness를 \(W\), result를
\(R\), 선행 terminal progress를 \(P_0\), 새 validator progress를 \(P_1\), frozen
independent validator를 \(V\)라 하자.

복구 성공 술어는

\[
A = H(W,R,P_0,L_A,L_E,V) \land T(P_0) \land
V(R,W,P_1^{\mathrm{in\ progress}}) \land
V(R,W,P_1^{\mathrm{complete}}),
\]

이다. \(H\)는 계약에 적은 SHA exact equality, \(T\)는 18 completed rows와 exact terminal
error를 뜻한다. 마지막 두 validator 호출은 동일 witness에서 독립 DFT/filter/QC,
baseline, 모든 trialwise/mean-waveform P2P, 두 reference × 두 estimand × 세 window,
participant delta, participant-equal \(D\), 65,536 shared-weight bootstrap, 7 LOO,
p17/p19 paired sensitivity를 재계산한다.

새 validator progress는 수치 leaf를 소유하지 않고 오직 \(W\)와 \(R\)의 SHA, exact
records, analysis/execution lock을 결박한다. 별도 recovery progress와 receipt가 거래 상태와
provenance를 기록한다. 따라서 복구는 \(R\mapsto R\)인 authority transaction이며 새
효과크기, 새 신뢰구간 또는 새 선택 규칙을 만들지 않는다.

선행 result나 witness의 단일 byte, record identity/integrity, claim status, QC diagnostic,
P2P 또는 aggregate leaf를 바꾸면 \(H\) 또는 \(V\)가 거짓이 된다. 원 progress를 직접
COMPLETE로 바꾸는 것은 이 술어를 만족하지 않으며 금지된다.

잔여 P2는 raw object에서 selected witness를 만든 decoder가 하나뿐이라는 점이다. witness
이후 수학 재계산은 독립적이지만 raw decode의 독립 구현 parity를 주장하지 않는다.

