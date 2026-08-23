# BA-SRM7 대안 경로 감사

Status: COMPLETE

Date: 2026-08-23

## 1. 목표와 선택

목표량은 public calcium recording의 source-rooted observed quotient에서 계산한 연속
유효 자유도와 그 temporal change가 future locomotion에 주는 증분 예측값이다. 구조
edge, 의식, 해마 또는 AGI를 목표량으로 두지 않는다.

BA-SRM6 input STOP 뒤 선택할 수 있는 경로를 source 연결성, PSD 보존, causal leakage,
추가 자유도와 falsifier 순서로 비교했다. 선택 경로는 R1이다.

## 2. 후보 표

| ID | 경로 | 지위 | 새 선택 자유도 | target-aware | 교차 예측ㆍ죽이는 시험 |
|---|---|---|---:|---|---|
| R1 | source-rooted raw red/green → train-fit causal $I$ → fixed reliability PSD → resolvent | `[예측: 선택]` | measurement revision 1건; $\sigma=5,L=20,W=60,\lambda=1$ 고정 | **yes**, BA-SRM6 missingness 뒤 제안 | mask-onlyㆍredㆍGFPㆍfixed-$d$ㆍtemporal null 중 하나가 CE와 같거나 우수하면 생물 해석 기각 |
| R2 | archived symmetric `I_smooth_interp_crop_noncontig` | `[산출: source diagnostic]` | 없음 | no | causal feature와 descriptive agreement만; future-neural leakage 때문에 predictive evidence 금지 |
| R3 | neuron별 `Ratio2` threshold 하향 | `[경험식 후보: 기각]` | threshold 1+ | **yes** | 0.60은 source 근거가 없고 BA-SRM6 input을 본 뒤 선택되므로 재시도 금지 |
| R4 | pairwise-complete covariance | `[미완성: 기각]` | pair thresholdㆍPSD repair | yes | explicit minimum eigenvalue $-0.8$ witness; projection repair가 결과를 바꾸므로 현재 core에서 금지 |
| R5 | train reference metric $C^{-1/2}GC^{-1/2}$ | `[미완성: 후속]` | shrinkageㆍconditioningㆍreference window | no | 일반 linear rechart invariance가 필요할 때만 새 계약; current neuron-basis claim에는 불필요 |
| R6 | directed state-transition/Volterra operator | `[미완성: 별도 기전]` | lag/order/state/regularizer/intervention map | no | time reversalㆍheld-out transfer만으로 causal edge가 되지 않음; intervention 또는 source-locked dynamics 필요 |
| R7 | correlation/information fractal dimension | `[미완성: 별도 수학]` | embeddingㆍscale rangeㆍnoise floor | no | resolvent $d_{\rm eff}$와 동치 아님; scale-law plateau가 없으면 기각 |

## 3. R1을 고른 이유

R1은 archived code가 실제 prediction input으로 사용한 motion-corrected $I$와
timepoint majority-missing rule을 출발점으로 한다. centered symmetric smoothing은
future-prediction에서 leakage가 가능하므로 one-sided filter로 바꾸고, 그 변경을
source claim이 아니라 analyst measurement revision으로 표시한다. fixed $D_r$를 사용한
covariance는 PSD를 보존하며 missingness-only control이 같은 model capacity로 artifact를
공격한다.

이 경로의 약점은 target-aware라는 점이다. BA-SRM6 input을 본 뒤 measurement rule을
고쳤으므로 Hallinen corpus의 held-out block은 within-run developmental test일 뿐 독립
confirmation이 아니다. 결과가 양성이어도 WormID/DANDI 또는 IBL 같은 새 corpus가
필요하다.

## 4. R2와 source parity의 역할

R2는 upstream code 재현에 필요하지만 causal prediction 경쟁 모델이 아니다. symmetric
filter는 anchor $t$ 뒤 neural sample을 섞을 수 있다. R2와 R1의 feature SpearmanㆍNMAE는
측정 변경량을 보여 주는 descriptive diagnostic으로만 남긴다. R2가 더 높은 prediction
score를 보였다는 문장은 score 자체를 계산하지 않으므로 만들지 않는다.

## 5. 기각 경로와 no-go

R3은 threshold만 바꾼 같은 실패 경로다. R4는 PSD를 잃고, nearest-PSD projection을
추가하면 별도 estimator와 tuning이 생긴다. red 또는 GFP로 primary를 바꾸는 길과 실패
recording을 삭제하는 길도 endpoint/split 변경이므로 후보 표에 올리지 않고 퇴역한다.

R5--R7은 구조적으로 다른 유효한 후속 질문이지만 이번 data contract의 단일 measurement
revision을 넘어선다. 특히 directed loop는 covariance에서 시간 순서를 지운 순간
식별되지 않고, fractal dimension은 비정수라는 표면적 유사성만으로 resolvent trace와
합칠 수 없다.

## 6. 후속 순서

1. R1의 L0-A analytic/property gate;
2. 정답-known L0-B synthetic recovery;
3. behavior를 읽지 않는 L0-C real-background injection;
4. inputㆍL0가 모두 통과할 때만 train/validation behavior 개봉;
5. model selection을 동결한 뒤 held-out final block 한 번 개봉;
6. 결과와 무관하게 maskㆍredㆍGFPㆍtemporal falsifier를 함께 판정;
7. 독립 승격은 새 source-locked corpus에서만 수행.

route 결론: `R1_SELECTED / DEVELOPMENTAL_ONLY / DIRECTED_AND_CONSCIOUSNESS_CLAIMS_EXCLUDED`.
