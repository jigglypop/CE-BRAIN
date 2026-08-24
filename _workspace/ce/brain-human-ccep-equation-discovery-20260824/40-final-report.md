# BA-OBS-DISC1 최종 보고서: 실제 CCEP에서의 식 발견은 D2에서 멈췄다

Status: COMPLETE

## 결론

BA-OBS-DISC1은 실제 인간 CCEP 자료에서 사전 고정한 15개 시간·거리 response-kernel 후보를 비교했다. 24쌍 D0은 CABLE을 선택했고, 48쌍 D1은 primary bipolar gate를 통과했다. 그러나 39쌍 D2에서 source-cluster bootstrap 95% 구간이 0을 가로질러 후보를 기각했다. 최종 지위는 `COMPLETE_WITH_NEGATIVE_GATE / CANDIDATE_KILLED_AT_D2 / NOT_CONFIRMED`이며, 40쌍 D3은 열지 않았다.

## 무엇을 시험했는가

이 실험은 전류와 전압의 실제 막전류 법칙을 단순 직선으로 대체한 것이 아니다. 짧은 CCEP 창에서 선형화한 전기 네트워크의 Green/cable 감쇠가 관측 RMS 진폭을 설명하는 작은 후보식을 동기화할 수 있는지 묻는다. 하지만 전극 신호는 신경 반응만이 아니라 reference, volume conduction, artifact, noise가 섞인 readout이다. 따라서 모델은 생물물리 PDE나 뇌 전체 리만 기하의 추정기가 아니라 observed CCEP response kernel의 경쟁 모형이다.

예측 대상은 baseline-scale로 정규화한 무차원 RMS 진폭 $E$에 대해 $z=\log(E+10^{-6})$, $x=t/(50\,\mathrm{ms})$, $r=\ell/(50\,\mathrm{mm})$다. $10^{-6}$은 무차원 floor다. D0 winner CABLE은

$$
\widehat z=\beta_0+\beta_1\log x+\beta_2x-a r,
\qquad a\ge0.
$$

이다. 거리 계수 $a$는 관측 kernel의 감쇠 계수일 뿐, 해부학적·축삭 geodesic이나 리만 계량의 측정값이 아니다.

## 결과의 논리

원천은 OpenNeuro `ds003708`의 단일 epilepsy 환자 6 mA CCEP, 255 eligible epoch다. endpoint-blind 151 pair를 `24/48/39/40`으로 분할했고, D0은 CABLE에 $I_{\rm bip}=0.05211328272681981$, $I_{\rm mean}=0.08361287750306079$, 6 fold 중 4 bipolar 승리를 부여했다. D0은 모델 선택 단계라서 이 숫자만으로 확인을 주장할 수 없다.

D1 bipolar는 평균 loss 개선 $0.036304411549773374$, source-cluster 95% CI $[0.01139441475506768,\,0.06097480548090294]$, geometry permutation $p=0.000975609756097561$로 통과했다. D2 bipolar는 평균 개선 $0.02351873345804861$ 및 $p=0.001951219512195122$를 보였지만 CI가 $[-0.005757602832834792,\,0.04929832365415101]$이라서 primary gate를 통과하지 못했다. 이때 작은 permutation $p$는 geometry label과의 연관이 무작위 label보다 크다는 비교이고, CI의 0 교차는 source를 다시 뽑으면 평균 예측 이득의 부호가 안정적이지 않다는 비교다. 둘은 서로 다른 질문에 답하므로 동시에 성립할 수 있다.

D2는 효과의 역전이 아니다. D1의 source별 개선 표준편차는 $0.06328$이고 24 source 중 19개가 양수였으나, D2의 표준편차는 $0.07175$, 양수 source는 16/24개였다. 두 단계에서 공통 source의 효과 상관은 $-0.0833$이었다. 따라서 이 자료는 source 수준의 예측 이득이 안정적이라는 결론에 필요한 정밀도를 주지 못한다. 이것만으로 잡음과 누락된 구조를 구분할 수는 없다.

D2 mean은 개선 $0.030867609165603892$, CI $[0.003784792373941817,\,0.05676835240113891]$, $p=0.000975609756097561$로 통과했다. 그러나 mean은 common/reference 성분에 민감할 수 있는 진단이며, primary bipolar의 실패를 대체할 수 없다. 이 reference 불일치는 ‘어느 readout에서나 안정적인 kernel 예측’이라는 더 강한 주장을 막는다.

## 감사 가능성과 다음 경계

source cache, split, fixture, D0, D1, D2 receipt는 version-bound source identity와 코드 SHA-256 `af70dc054714fccc496bd50a8e25139bd7e4b28dc7a5ddd3acc7a008a36bd8da`를 사슬로 기록한다. fixture는 heat-kernel 생성 모형 회복, geometry-null control, common-reference control, fail-closed source checks, downstream barrier를 통과했다. 이 기록은 결과를 강하게 만드는 증명이 아니라, D2 기각이 사후 formula/window/threshold 조정으로 만들어진 것이 아님을 추적 가능하게 한다.

이 판본의 다음 규칙은 단순하다. D3을 열지 않으며, CABLE의 formula·window·threshold를 바꾼 다음 D3을 실행하지 않는다. 새로운 식 계열은 새 contract와 새로운 preregistration, 그리고 열리지 않은 validation pool 또는 독립 subject에서 처음부터 시험해야 한다. 현재 산출은 ambient 또는 무한차원 리만 계량, 해부학적/축삭 geodesic, 의식, 자아, 해마 hash, AGI를 검증하거나 반증하지 않는다. 그것들은 이 단일-환자 observed CCEP 비교의 바깥에 남는다.

참고로 다른 후보가 D0에서 탈락한 사실은 heat-kernel 일반의 반증이 아니다. H-Q 계열은 첫 fold에서 $\lambda$가 거의 경계에 붙었고, delay 계열은 $\delta\simeq0$, BIEXP는 $\delta=0$ 및 fraction $\simeq0.999$의 식별 불량 경계에 붙어 중단됐다. 후속 독립 판본에서는 경계를 줄인 $H\text{-}Q^0$ 또는 아직 시험하지 않은 anisotropic-cable을 별도 사전등록 후보로 둘 수 있다. 반대로 delay와 BIEXP는 더 높은 시간 해상도와 별도의 설계가 필요하다. 이는 다음 설계의 후보 목록이지, 현 실행의 데이터가 지지한 결론은 아니다.
