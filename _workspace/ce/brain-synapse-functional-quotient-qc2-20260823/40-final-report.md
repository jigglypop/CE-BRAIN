# BA-SRM3 최종 보고서

Status: COMPLETE

## 초록

BA-SRM3는 과거 펄스 이력에서 미래 시냅스 반응으로 가는 유한 관측 quotient를 실제
Allen-SynPhys 자료에서 추정하려 했다. train 구조를 본 뒤 clamp-mode 감사를 수행한 결과,
presynaptic stimulus command가 current clamp에서는 전류이고 voltage clamp에서는 전압인데
기존 extractor가 모든 command를 전류로 처리한 사실을 확인했다. 따라서 기존 operator,
rank, covariance와 model score는 생물학적으로 해석할 수 없다. development와 confirmation은
열지 않았다. 유한 출력 pullback이 전체 무한차원 공간이 아니라 관측 kernel을 나눈 quotient만
식별한다는 조건부 정리는 그대로 남는다.

## 문제와 방법

이 run은 시냅스를 단일 $W_{ij}$가 아니라 과거 자극과 반응 이력에 작용하는 함수로 보고,
그 반응연산자의 미분에서 관측 기하를 만들려 했다. 그러나 기하 계산보다 먼저 입력 좌표와
측정 단위가 동일한 물리량을 뜻하는지 확인해야 한다. clamp-mode 감사는 1,383개 sequence와
16,596개 event row를 검사했다. 모든 postsynaptic recording은 current clamp였지만
presynaptic recording에는 current clamp와 voltage clamp가 함께 있었다.

## 보존되는 수학

[정리] Fréchet 미분 가능한 관측 연산자 $M$과 양의 정부호 잔차 공분산 $R$을 주면

$$
G_x(u,v)=\langle R^{-1/2}DM_xu,\,R^{-1/2}DM_xv\rangle
$$

는 양의 준정부호 쌍선형형식이다. 출력이 유한차원일 때 그 rank는 출력 차원을 넘지 않으므로,
전체 함수공간이 아니라 $T_x\mathcal H/\ker DM_x$의 관측가능 방향만 식별한다. 일정 rank와
매끄러운 closed kernel subbundle은 quotient manifold를 부르기 위한 추가 전제다.

## 무효화된 경험적 적용

[산출: 측정모형 감사] stimulus command amplitude는 presynaptic clamp mode에 따라 A 또는 V다.
기존 extractor는 clamp mode를 기록하지 않고 모든 값을 pA 계열 좌표로 처리했다. 서로 다른
물리 차원의 값을 같은 좌표로 합쳤으므로, 이후 PCA 차원·Jacobian rank·metric·예측 score는
해석할 수 없다. 이 결과는 무한차원 상태공간 가설의 반례가 아니며, 낮은 경험적 차원의
증거도 아니다.

## 한계와 재개 조건

[미완성] 새 판본은 IC와 VC command를 typed channel로 분리하고 response/noise 단위도
postsynaptic clamp mode에 따라 검사해야 한다. discovery/train에서 후보식을 만들고,
validation에서 구조와 유효 차원을 선택하며, test/confirmation은 마지막 한 번만 열어야 한다.
같은 test를 식 유추와 검증에 함께 쓰지 않는다. conductance, release, STDP, homeostasis,
기억 또는 AGI 기전은 이 자료만으로 식별되지 않는다.

## 재현성

단위 감사 구현은 `artifacts/audit_clamp_unit_semantics.py`에 보존돼 있다. 과거 disk-only
receipt는 현재 분리 저장소에 없고, 판정 요약과 원래 SHA-256은
`_workspace/ce/brain-algorithm-route-ledger.md`의 BA-SRM3 행에서 관리한다.
