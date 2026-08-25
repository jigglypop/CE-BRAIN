# 수학 레인 — 전수 endpoint와 witness 재계산

Status: COMPLETE

## Endpoint 정의역

각 clean trial $i$와 window $W$에서 baseline 평균 $b_i$를 뺀 P2P는

$$
P_{i,W}=\max_{j\in W}(x_{ij}-b_i)-\min_{j\in W}(x_{ij}-b_i)
=\operatorname{ptp}_{j\in W}x_{ij}.
$$

$b_i$는 trial 안에서 시간에 무관한 상수이므로 P2P 자체에는 영향을 주지 않는다.
baseline 보정은 mean waveform 재현을 위해 유지한다. nonfinite trace는 endpoint 전에
QC에서 제거하고, clean count $n\ge1$이면 trial-mean과 mean-waveform estimand가 모두
정의된다. 모든 P2P, participant 변화와 $D$의 단위는 microvolt다.

trial-mean과 mean-waveform P2P는

$$
\bar P_W=\frac1n\sum_i\operatorname{ptp}_W(x_i),
\qquad
P_W^{mean}=\operatorname{ptp}_W\!\left(\frac1n\sum_i x_i\right)
$$

로 서로 다르다. max의 convexity와 min의 concavity에서
$P_W^{mean}\le\bar P_W$가 성립한다. 따라서 mean-waveform sensitivity가 primary
trial-mean을 대체할 수 없다.

clinical endpoint trace는 selected QC tensor의 첫 channel $q[:,0,:]$이고, p20의
나머지 selected channels는 keep-mask union에만 참여한다. local-bipolar는 source
lock의 endpoint channel minus 인접 channel이다.

## Participant contrast

TS participant는 p16, p17, p18, p19이고 PB participant는 p17, p19, p20, UC004,
UC005다. 각 participant의 post-pre 변화 $\Delta_s$를 먼저 만든 뒤

$$
D=\frac14\sum_{s\in TS}\Delta_s-
  \frac15\sum_{s\in PB}\Delta_s
$$

를 계산한다. 이 순서는 clean trial 수가 participant 가중치가 되는 것을 막는다.

bootstrap은 일곱 unique participant에 독립 $\operatorname{Exp}(1)$ weight를 준다.
TS는 weight indices `0..3`, PB는 `1,3,4,5,6`을 arm 안에서 각각 정규화하므로 p17과
p19의 weight는 두 arm에서 공유된다. PCG64 seed `20260825`, 65,536 draws를 고정한다.
quantile과 $P(D>0)$은 이 일곱 participant에 조건부인 기술적 요약이다.

LOO는 unique participant 한 명을 삭제하고 각 arm의 분모를 다시 정규화한다. p17과
p19를 삭제할 때 두 arm에서 모두 빠지며, 나머지는 속한 arm에서만 빠진다. 모든 경우
남은 arm 분모는 양수다. paired sensitivity는

$$
D_{pair}=\frac12\sum_{s\in\{p17,p19\}}
(\Delta_{s,TS}-\Delta_{s,PB})
$$

이고 matched participant가 둘뿐이므로 기술적 sensitivity 이상의 지위가 없다.

## Zero-clean과 bipolar 정의역

고정 clinical 18 cell 중 하나라도 zero clean이면 participant를 사후 제외하지 않고
`CLINICAL_PAIR_UNAVAILABLE`로 종료한다. bipolar cell 하나라도 zero clean이면 clinical
primary는 보존하되 bipolar의 세 window·두 estimand·bootstrap·LOO·paired 전체 bundle을
생략한다. 이는 임의의 MIN threshold가 아니라 분모 0과 partial selection을 막는 규칙이다.

## Witness-backed 재계산

selected-source witness는 rejected trial을 포함한 모든 selected QC trace와 bipolar
trace를 microvolt 단위로 저장한다. validator는 witness의 exact key·shape·dtype·array
hash를 확인한 뒤 corrected dual-path QC를 다시 실행하여 keep mask를 재구성한다. 그
mask에서 baseline, 모든 trialwise P2P, mean waveform, participant 변화, $D$, bootstrap,
LOO와 paired 값을 producer와 독립된 endpoint/aggregate 코드로 다시 계산한다.

이 구조는 선행 Stage-E P0 두 건을 닫는다. 첫째, JSON trialwise P2P를 원 clean trace와
무관하게 바꿀 수 없다. 둘째, bipolar availability는 재계산한 18개 keep mask에서
all-or-none으로 결정되므로 불리한 sensitivity bundle만 삭제할 수 없다.

남는 provenance ceiling은 raw object에서 witness로 selected trace를 추출하는 단계가
독립 구현으로 재현되지 않는다는 점이다. 그 구간은 frozen loader code hash와 각 full
object의 expected/observed SHA·size·version ID·ETag 검증에 의존한다. 따라서 PASS는
witness 이후의 독립 endpoint 재계산이지 exact raw-decoder 이중 구현 증명은 아니다.

## 판정

수식·정의역·shared-participant bootstrap·LOO·paired·zero-clean 처리에는 P0/P1이 없다.
raw-to-witness 독립 추출 부재는 명시된 provenance P2 ceiling으로 남긴다. 결과 $D$의
부호, interval 또는 probability는 실행 gate가 아니므로 완결 규칙은 direction-blind다.

