# BA-SRM6 대안 경로와 falsifier

Status: COMPLETE

Date: 2026-08-23

## Route A — 고정 basis의 observed soft spectrum

현재 선택 경로다. 각 recording의 train prefix에서 neuronwise 표준화 basis를
고정하고 window covariance의 resolvent trace로 $d_{\rm eff}$를 계산한다. 이 경로는
일반 좌표불변성을 주장하지 않고 orthogonal invariance와 scale sensitivity curve만
보고한다. C. elegans 실제자료에서는 미래 velocity의 temporal holdout 예측이
AR, fixed-d, participation-ratio, raw-spectrum, red-channel과 GFP control을 넘는지 본다.

가장 강한 falsifier는 두 held-out recording 중 하나라도 CE_SOFT가 best matched
control을 이기지 못하는 경우다. 그때 `SOFT_DIMENSION_INCREMENT_NOT_SUPPORTED`로
닫고 수식의 algebraic 성립과 biological utility를 분리한다.

## Route B — reference-metric generalized spectrum

일반 가역 선형 rechart까지 불변성이 필요하면 train-only $C\succ0$를 고정하고

$$
B_t=C^{-1/2}G_tC^{-1/2},
\qquad
S_t=B_t(B_t+\lambda I)^{-1}
$$

를 쓴다. $G$와 $C$를 함께 congruence transform하면 generalized eigenvalue는
보존된다. 그러나 $C$의 shrinkage, condition cutoff와 cross-animal transport가 새
자유도이므로 이번 결과를 본 뒤 Route A를 Route B로 바꾸지 않는다.

Route B의 falsifier는 reference choice를 바꾸면 validation 우위가 사라지거나,
fixed raw-spectrum baseline을 못 이기는 경우다. 그때 더 강한 invariance가 예측력을
만든다는 해석을 기각한다.

## Route C — directed dynamics, edge와 loop의 별도 경로

Covariance는 시간 순서를 버리므로 directed edge나 recurrent return을 검정할 수 없다.
그 질문에는 causal history predictor 또는 state-space transition operator를 별도
사전등록하고 time reversal, lag shuffle, source ablation을 같은 정보 budget으로
비교해야 한다. 관측자료만으로는 directed predictive transfer이며 intervention 없는
causal connectivity가 아니다.

가장 강한 falsifier는 directed model이 time-reversed 또는 symmetric model을
held-out에서 이기지 못하는 경우다. C. elegans의 cross-record neuron identity가
없으므로 anatomical edge route는 현재 `BLOCKED_INPUT`이다.

## Route D — fractal/information dimension

Hausdorff, correlation 또는 information dimension은 비정수일 수 있지만 resolvent
$d_{\rm eff}$와 다른 양이다. 별도 route는 embedding, scale range, noise floor,
sample-size bias와 convergence plateau를 결과 전에 고정해야 한다. 유한 noisy cloud에서
기울기 하나를 fit해 Riemannian dimension으로 부르지 않는다.

가장 강한 falsifier는 추정 dimension이 scale range·noise correction·embedding에
안정적이지 않은 경우다. 이번 run은 이 route를 실행하지 않는다.

## Route E — hippocampal sparse address

해마 index는 Norman iEEG 같은 hippocampus–cortex 자료에서 sparse address가 cortical
reinstatement target/latency에 주는 incremental information으로 따로 시험한다.
C. elegans에는 hippocampus가 없으므로 현재 결과를 해마 hash의 증거로 사용하지 않는다.
Literal cryptographic hash와 lossless 4D bottleneck은 BA-SRM5 no-go 때문에 계속 닫혀 있다.

## fixed 4와 고차원 대조군

$d=4$는 Route A의 matched hard-rank control 하나다. 비교 menu는
$\{2,4,8,16,32,48\}$이고 validation 결과 전에 고정됐다. 4가 선택되지 않아도
soft spectrum 식의 수학은 무너지지 않지만 `FIXED4_NOT_SUPPORTED`가 된다.
반대로 4가 이기더라도 의식 차원이 4라는 결론은 나오지 않는다. 높은 fixed-d와
raw spectrum이 같거나 더 좋으면 soft bottleneck이 불필요하다는 대안이 살아남는다.

## 현재 route 판정

Route A만 이번 run의 input·apparatus·실데이터 gate로 진행한다. Route B--E는 결과를
구하기 위한 사후 대체제가 아니라 서로 다른 질문과 새 계약이 필요한 대안이다.
Route A의 음성 결과도 fixed 4를 다시 살리거나 synthetic seed 탐색으로 우회하지 않는다.
