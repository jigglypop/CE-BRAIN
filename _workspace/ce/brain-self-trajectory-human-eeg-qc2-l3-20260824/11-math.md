# BA-SELF2-L3 수학 검증: 무차원 QC와 경로 특징

Status: COMPLETE

검증한 계약 SHA-256: `8eb85e4ce7218112c082b84e0f754ae3fa0afb1995374a9675c581164880517f`.

## 판정

`Q_A,Q_D`와 A2에서 만드는 두 cutoff는 무차원이고, 사후 공통 gain 및 채널별 상수 offset 변환에 정확히 불변이다. 따라서 BA-SELF1의 절대 전압 cutoff가 피험자 간 gain 차이에 실패한 문제를 겨냥한 **측정장치 QC 대체물**로서 수학적으로 일관된다. 이것은 신경 신호의 생물학적 동등성, 자아, 의식, 또는 경로 가설의 증거가 아니다.

계약 안에서 P0 모순은 찾지 못했다. 다만 (i) channel-specific gain에 불변이라고 해석하면 틀리고, (ii) A2로부터 만든 threshold의 통과율을 확률적 일반화 보장으로 읽으면 틀리다. 둘은 아래의 명시적 한계이며, 계약의 현재 문구는 이를 금지한다. P1로 남는 것은 관측 quotient에서의 예측 이득이 상태/경로의 존재론을 식별하지 못한다는 no-go이다.

## 정의와 차원

한 post-filter window를 전압 단위의 $X\in\mathbb R^{T\times 63}$라 하자. 계약의

$$
R_{tc}=X_{tc}-\operatorname{median}_{u}X_{uc},\qquad
s_c=1.4826\operatorname{median}_{t}|R_{tc}|
$$

및

$$
D_{tc}=X_{t+1,c}-X_{tc},\qquad
r_c=1.4826\operatorname{median}_{t}|D_{tc}-\operatorname{median}_{u}D_{uc}|
$$

에서 $R,s$는 전압 차원, $D,r$는 전압/one-sample 차원이지만 one-sample은 고정된 무차원 index step이다. 실제 단위로 쓰면 $D/\Delta t$와 $r/\Delta t$가 동일 차원을 가지므로 결론은 같다. 따라서

$$
Q_A=\frac{\max_{t,c}|R_{tc}|}{\operatorname{median}_c s_c},\qquad
Q_D=\frac{\max_{t,c}|D_{tc}|}{\operatorname{median}_c r_c}
$$

는 모두 무차원이다. $1.4826$도 무차원 상수다. A2 cutoff

$$
c_Q=\operatorname{median}(Q)+6\operatorname{median}|Q-\operatorname{median}(Q)|
$$

는 무차원 $Q$들의 합과 차만 사용하므로 무차원이다. 전압 단위의 수치가 cutoff로 재도입되지 않는다.

## 정확한 affine 불변성

임의의 $a\ne0$ 및 시간에 독립인 channel offset $b_c$에 대하여 $X'_{tc}=aX_{tc}+b_c$라 하자. 중앙값은 음의 scalar에도 affine-equivariant이므로

$$
R'_{tc}=aR_{tc},\qquad D'_{tc}=aD_{tc},\qquad
s'_c=|a|s_c,\qquad r'_c=|a|r_c.
$$

따라서 분자와 분모가 모두 $|a|$를 곱해져 $Q'_A=Q_A$, $Q'_D=Q_D$다. 이 계산은 $a<0$에도 그대로 성립한다. $b_c$는 $R$의 channelwise temporal centering에서, 그리고 차분 $D$에서 각각 소거된다.

간단한 수치 점검은 $R=(1,-1,2,-2)$와 $a=-3,b=17$에서 $R'=(-3,3,-6,6)$이고, 최대 절댓값과 MAD scale이 모두 정확히 3배가 되는 경우다. 이 계산은 부호 반전이 불변성을 깨지 않음을 보인다.

### channel-specific gain에는 불변이 아님

$X'_{tc}=a_cX_{tc}+b_c$이면 $R'_{tc}=a_cR_{tc}$ 및 $s'_c=|a_c|s_c$이나, numerator는 모든 channel의 최대값이고 denominator는 channel scale의 중앙값이다. 공통 인수 하나를 약분할 수 없다. 예를 들어 63 channel이 모두 scale 1이고 한 channel의 원래 최대 residual이 10이라고 하자. 그 한 channel만 $a_c=100$으로 바꾸면 median channel scale은 여전히 1인 반면 최대 residual은 1000이 된다. $Q_A$는 10에서 1000으로 바뀐다. 이는 설계상 의도된 한계다. 피험자 내/창 내 relative artifact를 잡되, channel별 impedance/gain 재배치를 동등한 관측으로 선언하지 않는다.

## 정의역, fail-closed gate, 강건성의 한계

모든 값이 finite이고 모든 $s_c,r_c$ 및 최종 분모가 양수일 때만 위 비율은 정의된다. 계약은 nonfinite 하나, 어느 $s_c$ 또는 $r_c$의 0/nonfinite 하나, 또는 분모의 0/nonfinite 하나에서 창을 즉시 거절한다. task/rest 중 하나가 거절되면 pair 전체를 거절하므로, 조건별 결측이 model loss에 들어갈 수 없다.

`max numerator / median channel scale`은 한 channel의 급격한 spike/step가 다른 channel들의 전형적인 시간 scale보다 비정상적으로 클 때 민감하며, denominator가 channel median이므로 하나의 오염 channel이 자기 scale을 키워 전체 기준을 느슨하게 만드는 효과를 제한한다. 단, 보장되는 것은 아니다.

- 절반 이상 지속되는 큰 진동/비정상 분산은 channel MAD도 함께 키워 비율을 낮출 수 있다.
- 시간적으로 상수인 channel offset은 정의상 제거된다. 그것이 artifact인지 유의한 생리 성분인지는 이 QC가 판별하지 않는다.
- 다수 channel에 동시 발생하는 구조적 artifact, channel-specific gain 변화, 또는 이미 공통참조/필터를 통과한 체계오류는 통과할 수 있다.
- `max`는 창 크기와 channel 수에 의존한다. 여기서는 $126\times63$와 처리 파이프라인이 고정되어 있으므로 A2 cutoff를 다른 sampling/window 설정으로 이식할 수 없다.

그러므로 이 gate는 품질 보증의 충분조건도 신경 동질성 검사도 아니며, 사전 고정된 다음 단계 진입 조건일 뿐이다.

## A2 calibration과 D1-QC의 누수 점검

$c_{Q_A},c_{Q_D}$는 A2의 64 windows에서 한 번만 계산하고 그 뒤 바꾸지 않는다. A2 값은 endpoint, target, feature, loss, $M_0/M_1$에 접근하지 않으므로 threshold 선택은 모델 outcome에 target-leakage를 만들지 않는다. 독립 표본에서의 오염확률 보장이나 population coverage를 주장하지 않으며, A2의 window들은 같은 recording에서 상관될 수 있다.

D1-QC에서는 $32$ paired trial 중 적어도 $24$, 각 session $16$ 중 적어도 $12$가 **두 window 모두** QC를 통과해야 한다. 이 수는 다음 D2 실행 가능성 gate이지 과학적 효과의 성공 기준이 아니다. D1-QC에서는 $z$, 미래 target, 모든 feature, loss, $M_0/M_1$ 계산을 금지하므로 경로 가설의 outcome은 열리지 않는다. 따라서 D1의 QC 통과/실패 자체가 D2의 경로 예측 점수를 선택하게 하지 않는다.

## D2 자유도 및 회귀의 수치 조건

D2는 session별 73, 59 pair로 총 132 pair다. 한 session을 holdout하는 두 방향에서 더 작은 training partition은 59 pair, 즉 task/rest 두 row를 쓰므로 118 rows다. 최대 모델은 $d=4$에서 intercept를 포함해 $p_0=53$, $p_1=59$ predictor다. 그러므로 최소 방향에도 $118>59$이며, 명시적으로 금지된 normal equation 대신 SVD/ridge를 쓰는 조건과 양립한다.

이는 full-rank 또는 작은 표준오차를 보장하지 않는다. 공선성, whitening rank/condition gate, 그리고 ridge penalty의 필요성은 그대로 남는다. $\lambda$ menu와 $(d,H)$ 선택은 D2 development에서만 하며 C1/C2/C3에는 재선택하지 않는다는 계약이 이 look-elsewhere를 경계한다.

## 면적 방향성 및 존재론 no-go

증분 $v_p=\Delta z_p$에 대해

$$
A_{ab}=\frac12\sum_{p<q}(v_p^av_q^b-v_p^bv_q^a)
$$

는 wedge product의 합이다. 증분 순서를 역순으로 바꾸면 각 ordered pair의 순서가 뒤집혀 $A\mapsto-A$다. 물리적 time reversal처럼 증분에 추가 부호를 붙여도 wedge의 두 부호는 상쇄되고 pair 순서 반전의 음의 부호가 남는다. 따라서 고정 계수에서 $A\mapsto-A$ control은 순서방향에 의존하는 feature인지 확인하는 적합한 adverse control이다. 다만 이는 실제 역시간 뇌를 생성하는 조작이 아니다.

경로 feature의 held-out 이득이 나와도 “자아는 path이고 state가 아니다”라는 결론은 따르지 않는다. history $h_k=(z_{k-L+1},\ldots,z_k)$를 확장 상태로 두면 같은 predictor는 state function $f(h_k)$가 된다. 반대로 유한 EEG 관측은 전체 뇌상태가 아닌 관측 kernel로 나눈 quotient이므로, 서로 다른 hidden histories가 같은 관측 상태를 낼 수 있다. 이 reparameterization/no-go는 존재론적 state-vs-path 판별을 막으며 계약의 claim ceiling과 일치한다. $d\in\{2,3,4\}$도 의식의 차원이 아니라 관측 quotient rank menu다.

## P0/P1 결론과 최소 수리 권고

- P0: 발견하지 못함. 차원, $a<0$를 포함한 common affine invariance, strict zero/nonfinite domain gate, A2-only cutoff, D1-QC-only 분리는 계약대로 일관된다.
- P1: finite quotient prediction은 self/consciousness/infinite-dimensional ontology를 식별하지 못한다. 이는 결함이 아니라 claim ceiling으로 남겨야 할 한계다.
- 최소 수리 권고: 구현 receipt에 각 D1 pair의 `$Q_A,Q_D`, 통과/거절 이유, 그리고 session/total acceptance count를 기록하라. 이는 계약식을 바꾸지 않고 24/32 및 12/session gate의 재현성을 보강한다. contract 문구에 이미 있는 channel-specific-gain 비불변성과 A2의 비확률적 성격은 최종 보고에도 그대로 반복해야 한다.

재현 명령(정의의 scalar algebra 점검): `.codex/hooks/python.cmd python -c "import numpy as np; x=np.array([1.,-1.,2.,-2.]); mad=lambda v:1.4826*np.median(np.abs(v-np.median(v))); q=lambda v:np.max(np.abs(v-np.median(v)))/mad(v); print(q(x),q(-3*x+17))"`.
