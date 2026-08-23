# BA-SELF3-L3 수학 검증: 채널별 affine 불변 QC와 경로 검정 경계

Status: COMPLETE

Contract SHA-256: `765c54ee2b20006619b3059c68ec3a5d1a3f007381f6d89593c597015ac41fce`

## 결론

제안한 `R2` QC 통계량은, 유한 실수값 창과 양의 robust scale이라는 명시적 정의역에서, 각 채널에 독립적으로 적용한 임의의 0이 아닌 상수 이득(음수 포함)과 offset에 **정확히 불변**이다. 이는 단위 및 채널별 고정 gain/offset 불변성의 정리일 뿐, 시간가변 gain·montage mixing·포화·넓게 퍼진 artifact를 제거한다는 주장이 아니다. 그러한 반례는 실제 한계로 남으며 숨은 생물학적 주장으로 승격하지 않는다.

`B1`은 outcome을 전혀 열지 않는 held-out-window 장비 전달 검사로 한정하면 target leakage가 없다. 그러나 같은 `sub-02`의 나머지 창이 뒤의 D2-M 개발에 쓰이므로, 독립적인 생물학적 복제나 population generalization은 아니다. 경로 area의 예측 이득이 나오더라도 “자아가 상태가 아니라 경로”라는 존재론을 판정할 수 없다는 state-augmentation no-go가 유지된다.

## 1. 정의역과 무차원성

[정의] 한 QC 창은 실수 행렬 $X\in\mathbb R^{T\times C}$이며 여기서는 $T=126$, $C=63$이다. 채널별 시간 median과 one-step difference를 다음처럼 둔다.

$$
R_{tc}=X_{tc}-\operatorname{med}_{u}X_{uc},\qquad
s_c=1.4826\operatorname{med}_{t}|R_{tc}|,
$$

$$
D_{tc}=X_{t+1,c}-X_{tc},\qquad
r_c=1.4826\operatorname{med}_{t}|D_{tc}-\operatorname{med}_{u}D_{uc}|.
$$

Median은 짝수 표본에서 중앙 두 order statistic의 평균을 쓰는, affine-equivariant한 결정적 median으로 고정한다. gate가 정의되는 필요충분한 계산 정의역은 모든 $X_{tc}$가 유한하고 각 $s_c,r_c$가 유한한 양수인 경우다. nonfinite 값 하나라도 있거나 어떤 channel의 $s_c\le0$ 또는 $r_c\le0$이면 비율을 정의하지 않고 즉시 창을 거절한다. task/rest 둘 중 하나가 거절되면 pair 전체를 거절한다.

[정의] 정의역에서

$$
Q_A^{\rm ch}=\max_{t,c}|R_{tc}/s_c|,\qquad
Q_D^{\rm ch}=\max_{t,c}|D_{tc}/r_c|.
$$

각 $R,s$는 EEG amplitude 단위 $[V]$, 각 $D,r$는 $[V]$이므로 두 비율과 $Q$는 무차원이다. $1.4826$은 무차원 상수다. 시간 index와 채널 index는 수가 아니라 label이며, 이 QC에는 exp/log/fixed-point 인자가 없다. 따라서 차원 게이트는 통과하지만, 차원이 맞는다는 사실은 QC가 생리적으로 타당하다는 증거가 아니다.

## 2. 채널별 affine 불변성

[정리] 모든 채널마다 $a_c\in\mathbb R\setminus\{0\}$, $b_c\in\mathbb R$에 대하여 $X'_{tc}=a_cX_{tc}+b_c$라 하자. 위 정의역이면

$$
Q_A^{\rm ch}(X')=Q_A^{\rm ch}(X),\qquad
Q_D^{\rm ch}(X')=Q_D^{\rm ch}(X).
$$

증명. Affine-equivariant median으로부터 $\operatorname{med}_t(a_cX_{tc}+b_c)=a_c\operatorname{med}_tX_{tc}+b_c$이다. 따라서 $R'_{tc}=a_cR_{tc}$ 및 $s'_c=|a_c|s_c$이고, 각 절댓값 비율은 같다. 차분은 offset을 없애므로 $D'_{tc}=a_cD_{tc}$. 다시 median의 affine equivariance로 $r'_c=|a_c|r_c$이며, $|D'_{tc}/r'_c|=|D_{tc}/r_c|$이다. channelwise maximum도 동일하다. $\square$

음수 gain을 빼면 이 정리는 불완전해진다. 위 증명은 order의 방향이 뒤집혀도 median이 $a\operatorname{med}(x)+b$로 변한다는 성질을 사용하므로 $a_c<0$도 포함한다.

### 재현 가능한 손계산 spot check

한 channel에 $X=(1,3,9,5,7)$을 넣으면 median은 $5$, $R=(-4,-2,4,0,2)$, $s=1.4826\times2=2.9652$이다. 따라서 $Q_A=4/2.9652\approx1.3490$이다. 차분은 $D=(2,6,-4,2)$, median은 $2$, $r=1.4826\times2=2.9652$이고 $Q_D=6/2.9652\approx2.0235$이다.

$a=-3,b=10$이면 $X'=(7,1,-17,-5,-11)$이고 $R'=-3R$, $s'=8.8956$, $D'=-3D$, $r'=8.8956$이다. 따라서 두 $Q$는 각각 $1.3490$, $2.0235$로 원값과 정확히 같다. 이는 공통 gain만이 아니라 channel마다 서로 다른 부호와 크기의 상수 gain을 적용해도 channel별로 같은 계산이 반복됨을 보이는 수치 점검이다.

## 3. 반례와 해석 한계

다음은 정리를 깨지 않지만, gate의 해석을 제한하는 반례다.

| 입력 변화 | 왜 affine 가정 밖인가 | QC가 보장하지 않는 것 |
|---|---|---|
| 느린 broad artifact $X_{tc}\leftarrow X_{tc}+h_t$ | $h_t$가 시간에 따라 변하며 channel offset이 아니다 | median/MAD 자체가 커져 큰 artifact가 통과할 수 있다 |
| 시간가변 gain $X_{tc}\leftarrow a_c(t)X_{tc}$ | 상수 $a_c$가 아니다 | gain modulation과 신경 activity를 구분하지 못한다 |
| montage/mixing $X'_{t}=MX_t+b$ | 일반 $M$은 channelwise diagonal map이 아니다 | 재참조·전극 mixing 뒤 $Q$가 보존되지 않는다 |
| ADC saturation/clip | 비선형 map이다 | clipping이 robust scale을 바꾸거나 숨길 수 있다 |
| 동시에 모든 channel에 나타나는 짧은 artifact | 불변성 자체와는 양립한다 | ratio가 작다고 artifact-free를 뜻하지 않는다 |

[P1: 가정 경계] $Q_A,Q_D$의 통과는 “이 창이 채널별 상수 affine 재표현에 대해 이상치 비율이 크지 않다”는 장비 QC 결과일 뿐, cortical current, membrane voltage, synaptic edge strength, 혹은 의식의 상태를 직접 측정했다는 충분조건이 아니다. 특히 $Q_D$의 분자는 difference median을 다시 빼지 않는다. 일정한 slope는 $r_c$의 작은 dispersion에 비해 큰 $|D|$를 만들 수 있으므로 거절될 수 있다. 이는 정의된 step gate의 성질이며, drift-robustness 주장이 아니다.

## 4. B1 배정과 표본수 감사

[정의] 원래 D2 132 pair에서 session별 trial hash를 `SHA256(UTF8("BA-SELF3-B1-v1:" || trial_hash))`와 trial hash의 사전식 순서로 정렬하고, 각 session 첫 16개를 B1으로 둔다. SHA collision이 있어도 두 번째 key가 순서를 결정한다. 같은 encoding과 hash가 allocation receipt에 기록되면 배정은 signal-blind이고 재현 가능하다.

산술은 다음과 같이 맞다.

| 집합 | ses-01 | ses-02 | 합계 |
|---|---:|---:|---:|
| 원 D2 | 73 | 59 | 132 |
| B1 | 16 | 16 | 32 |
| D2-M | 57 | 43 | 100 |

따라서 $132-32=100$, $73-16=57$, $59-16=43$이다. D2-M의 각 session은 contract의 최소 30 accepted pair보다 큰 원 배정 수를 가진다. QC 뒤에도 각 session에 $N\ge30$ pair가 남으면 task/rest를 각각 한 행으로 쓰는 설계에서 $2N\ge60>p_1=59$다. 이것은 $d=4$의 M1 ridge에 필요한 최소 행 수 guard일 뿐, feature collinearity가 없거나 OLS rank가 충분하다는 보장은 아니다. Ridge/SVD와 contract의 conditioning check는 여전히 필요하다.

각 session의 B1 후 D2-M에 모든 8 word level이 남는다는 것은 hash 정렬만으로 논리적으로 보장되지 않는다. receipt가 B1과 D2-M의 word별 count를 먼저 검증해야 하며 하나라도 빠지면 `APPARATUS_INVALID_DESIGN`이다. 이 조건부 gate 때문에 현재 산술에는 P0가 없다.

### leakage·독립성 경계

B1은 $z$, target, path feature, loss, model menu를 산출하거나 열지 않고 R2 pair acceptance만 계산한다. cut-off는 오직 A2의 64 calibration window에서 먼저 동결된다. 그러므로 이 순서를 지키는 한 B1은 model-outcome target leakage가 없다. 반면 B1과 D2-M은 같은 `sub-02` recording의 서로 다른 window이고, B1에서 QC 전달만 확인한 뒤 D2-M을 개발에 쓰므로 두 집합은 독립 생물학적 replication이 아니다. B1의 $24/32$ 및 각 session $12/16$ pass는 held-out **window apparatus transfer**의 75% gate이고, 뇌 일반화 또는 자아 가설의 75% 지지율이 아니다.

## 5. 상태-경로 판정의 no-go

[정리: 관측 상태-경로 no-go] 유한 history feature $F(z_{k-L:k})$가 미래 관측 EEG 예측에 추가 이득을 준다고 해도, 그것만으로 자아가 상태가 아니라 경로라고 결론낼 수 없다.

증명. 확장 상태 $\tilde z_k=(z_{k-L},\ldots,z_k)$를 정의하면 $F(z_{k-L:k})=\tilde F(\tilde z_k)$로 쓸 수 있다. 즉 finite-memory path functional은 확장된 순간 상태의 함수다. 반대로 scalp EEG quotient는 완전한 신경 상태가 아니므로, 현재 quotient로부터 보이지 않는 history dependence도 가능하다. 그러므로 상대 예측 이득은 관측 quotient에서 ordered history가 유용하다는 경험식만 시험하며, 존재론적 상태/경로 이분법을 식별하지 못한다. $\square$

이는 $d\in\{2,3,4\}$가 의식의 차원이라는 주장도 배제한다. 그 $d$는 fold-local whitening 뒤의 관측 quotient rank 후보일 뿐이다.

## 6. P0/P1 판정과 최소 receipt

| 등급 | 발견 | 처리 |
|---|---|---|
| P0 | 없음 | 계약의 exact channelwise affine claim, B1 arithmetic, 그리고 $2N>p_1$ guard 사이에 치명적 모순을 찾지 못했다. 단, receipt의 word coverage/acceptance 검사가 빠지면 즉시 P0로 승격한다. |
| P1 | QC를 artifact-free 또는 physiology-identifying gate로 읽을 수 없음 | section 3의 counterexample과 claim ceiling을 유지한다. |
| P1 | B1을 독립 생물학적 replication으로 읽을 수 없음 | B1을 apparatus-only held-out window gate로 제한한다. |
| P1 | state-path 존재론 판정 불가 | no-go를 유지하고 결과를 관측 quotient 예측에만 제한한다. |

`P0/A0` receipt의 최소 항목은 source/header lock, exact range `206`·Content-Range·ETag·payload SHA-256, parser/filter hash, 63-channel geometry, allocation hash, 유한성/zero-scale 결과, negative gain/offset synthetic spot check, broad-artifact adverse check이다. A1/A2 receipt는 각 창의 $Q_A,Q_D$, calibration 64-window 목록, median/MAD와 frozen cutoff, accepted/rejected 이유를 보존해야 한다. B1 receipt는 모든 trial hash와 source/new split, session·word count, ordering key/algorithm version, pair acceptance와 $24/32$·$12/16$ gate, 그리고 `model_outcome_opened=false`를 반드시 기록해야 한다. D2-M receipt는 QC 후 session별 pair 수와 $2N>59$ guard, rank/conditioning, 선택 menu 및 모든 loss/control output을 분리 기록해야 한다.

재현 명령은 implementation receipt가 동결한 `.codex/hooks/python.cmd python ...` 경로만 사용한다. 이 lane은 수학 정의와 hand spot check만 수행했으며 raw EEG를 열지 않았다.

