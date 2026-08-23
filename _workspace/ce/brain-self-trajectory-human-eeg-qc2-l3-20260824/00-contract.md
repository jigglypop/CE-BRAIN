# BA-SELF2-L3 연구 계약 — 무차원 EEG QC 뒤의 상태 대 경로 검증

Status: COMPLETE

PREDECESSOR: `_workspace/ce/brain-self-trajectory-human-fmri-l3-20260824`

CE_RUN: `_workspace/ce/brain-self-trajectory-human-eeg-qc2-l3-20260824`

## 1. 질문, 판본 차이, 주장 상한

검사할 좁은 질문은 다음 하나다. 현재 관측 EEG 상태, 그 국소 변화율, 경로의 시작점·길이·에너지와 순서를 버린 증분 통계를 이미 조건화한 뒤에도, **순서가 있는 과거 경로**가 100 ms 뒤의 관측 EEG 변화를 held-out 자료에서 추가로 예측하는가?

선행 BA-SELF1은 모델 outcome 전에 멈췄다. `sub-01`에서 고정한 절대 진폭 cutoff `281.5218166091819`를 `sub-02` D1에 적용하자 64/64 창이 넘었지만, first-difference cutoff는 0/64만 넘었고 nonfinite·zero-MAD는 모두 0이었다. 따라서 판정은 `APPARATUS_INVALID_CROSS_SUBJECT_ABSOLUTE_QC`였으며 식의 반증이 아니었다.

이 판본은 신호 변환, 상태·경로 식, 모델 menu, target, split 및 성공 기준을 바꾸지 않는다. 바꾸는 것은 절대 전압 QC를 아래의 무차원 QC로 대체하고, 이미 QC 목적으로 열린 D1을 모델에서 영구 제외하는 것뿐이다. 이 변경은 선행 실패를 본 뒤 고안된 **측정장치 수정**임을 공개한다. 새 QC 값은 아직 보지 않았으며 이 계약 뒤에는 식·cutoff 법칙·75% 전이 문턱을 바꾸지 않는다.

`docs/axium.md`는 저장소에 존재하지 않는다. 이를 대신했다고 주장하지 않고 이 계약에서 기호와 경계를 국소적으로 정의한다.

[미완성] 유한 EEG로 자아가 현재 상태인지 경로인지 존재론적으로 식별할 수 없다. 과거는 확장된 현재 상태에 포함될 수 있고, 유한 관측은 전체 신경 상태가 아니라 관측 kernel을 나눈 quotient만 본다. $d\in\{2,3,4\}$는 의식의 차원이 아니라 유한 관측 quotient의 후보 rank다. 무한차원, 의식, 자아, 해마 해시, AGI 기전 및 모집단 일반화 주장은 금지한다.

## 2. source lock과 상속 증거

자료는 OpenNeuro `ds006033` snapshot `1.0.1`, DOI `10.18112/openneuro.ds006033.v1.0.1`, Git tag object `3af0502b0664b80dacf015e76c436c9ba371527c`, CC0다. 논문 DOI는 `10.1016/j.dib.2025.112258`이다. 원자료를 저장소에 저장하거나 commit하지 않는다.

다음 선행 증거를 hash로 고정해 재사용한다.

| 항목 | SHA-256 | 허용되는 상속 |
|---|---|---|
| BA-SELF1 contract | `2b08c0fd5eb69ae6f3d096a6542e248b6d2b69da985f90c7d06071e0690be50e` | 데이터, split, 전처리, 경로식, 모델 및 claim ceiling |
| sources | `59066ab8441d562d73176b7486c00c6c770472fa11f1bb04229c845a59110f37` | source provenance와 공개 metadata 결함 |
| math | `a5f51a8c9753cb284a2e74da875d36d8b513b75ab110e74d60fe7a36ce74efac` | quotient metric, area, feature 수, no-go |
| routes | `04fc33f2527e672584c8b92c49af7f9532ab403b4ac0d03ef3ba6ba0820d7c47` | 대안 경로와 중단 기준 |
| final report | `d3e5b30b46bc58fd749e07946e66b0bfed51f2f2613c1bfcea282eb2247a0699` | 절대 QC 실패 사실만 |
| A0 metadata receipt | `5bc7fb8acebe366db84ba6f4aa9b95eae2051e3bf0f5760792c7ac9e6520a3f7` | 5개 recording의 header, ETag, 길이, URL |
| trial manifest | `4ebc8efdca4e277a989c8e7aceb0f00911d84fd20e6b6980dc94cbce7062a061` | A1/A2/D1/D2/C1/C2/C3 배정 |
| repaired D1 receipt | `d05bd70e013a09cfb47d4ab0cb3bb507bba7839fbb00b98a9988246279da92d2` | D1은 QC-only로 열렸고 model outcome은 없었다는 사실 |

공개 sidecar의 채널 합계 66과 실제 BrainVision header/binary 64열은 불일치한다. 다섯 header 모두 `NumberOfChannels=64`, 32번째 열 이름 `ECG`, 나머지 63개가 scalp 이름이고, `DataPoints*64*4=Content-Length`를 만족할 때만 header를 binary schema 권위로 쓴다. 하나라도 어긋나면 `APPARATUS_INVALID_SCHEMA`다.

## 3. 고정 전기 신호 변환

각 anchor에서 `anchor-2500`부터 `anchor+500`까지 3,001개의 5 kHz 표본, 즉 `3,001*64*4=768,256` byte만 HTTP Range로 읽는다. 응답은 `206`, 정확한 `Content-Range`, 길이, A0 ETag를 모두 만족해야 한다. little-endian multiplexed float32로 해석하고 ECG index 31(0-based)을 제거한 63채널에 common-average reference를 적용한다.

501-tap Hamming FIR, cutoff 45 Hz를 `scipy.signal.lfilter`로 인과 적용하고 첫 500 raw sample을 warm-up으로 버린 뒤 20배 decimation해 250 Hz, $126\times63$ 창 $X$를 만든다. zero-phase, 역방향 filtering, group-delay 미래 보정은 금지한다. anchor index는 100, 100 ms target index는 125다.

## 4. 새 무차원 QC

[정의] 필터 뒤 창 $X\in\mathbb R^{T\times63}$에 대해 채널별 시간 중앙값을 빼고

\[
R_{tc}=X_{tc}-\operatorname{median}_{u}X_{uc},\qquad
s_c=1.4826\operatorname{median}_{t}|R_{tc}|
\]

로 둔다. 1-step difference $D_{tc}=X_{t+1,c}-X_{tc}$와

\[
r_c=1.4826\operatorname{median}_{t}
\left|D_{tc}-\operatorname{median}_{u}D_{uc}\right|
\]

를 정의한다. 두 QC 지표는

\[
Q_A=\frac{\max_{t,c}|R_{tc}|}{\operatorname{median}_c s_c},\qquad
Q_D=\frac{\max_{t,c}|D_{tc}|}{\operatorname{median}_c r_c}
\]

다. 둘은 무차원이며 필터 뒤 창의 공통 gain과 채널별 상수 offset

\[
X'_{tc}=aX_{tc}+b_c,\qquad a\ne0
\]

에 정확히 불변이다. 채널별 서로 다른 gain에는 불변이라고 주장하지 않는다.

nonfinite가 하나라도 있거나, 어떤 $s_c$ 또는 $r_c$라도 0/nonfinite이거나, 두 분모 중 하나가 0/nonfinite이면 해당 창은 즉시 탈락한다. task/rest 중 하나라도 탈락하면 pair 전체를 탈락시킨다.

A2의 64개 창만으로 각 $Q\in\{Q_A,Q_D\}$에 대해

\[
c_Q=\operatorname{median}(Q)+6\operatorname{median}|Q-\operatorname{median}(Q)|
\]

를 한 번 고정한다. cross-window MAD가 0/nonfinite이면 `APPARATUS_INVALID_QC_SCALE`다. 선행 절대 amplitude/difference 값은 matched diagnostic으로만 기록하고 새 탈락 판정에는 쓰지 않는다.

## 5. 장치 단계와 즉시 kill

| 단계 | 허용 신호 | 목적과 다음 문 |
|---|---:|---|
| P0 | 0 | parser·offset·인과 filter, $Q_A,Q_D$의 단위/affine-gain 불변성, spike/step adverse synthetic test. 실패 시 코드 수정 뒤 재감사, 실신호 금지 |
| A1 | 기존 `sub-01/ses-02` 8 trial, 16창 | exact range, shape, finite/scale, anchor, 새 QC 계산 가능성만. endpoint 금지 |
| A2 | 같은 recording 추가 24 trial, 총 64창 | $c_{Q_A},c_{Q_D}$ 동결. 효과 크기를 보고 cutoff 변경 금지 |
| D1-QC | 이미 열린 `sub-02` D1 32 pair, session별 16 | **교차 피험자 apparatus transfer만**. $z$, 미래 target, feature, loss, $M_0/M_1$ 계산 금지 |
| D2 | `sub-02` 잔여 132 pair: ses-01 73, ses-02 59 | D1-QC가 통과한 뒤에만 최초 model development/selection |
| C1/C2/C3 | `sub-03` 25/50/175 | 선행 계약과 같은 futility/futility/final confirmation; 그 전까지 봉인 |

D1-QC의 전이 통과 조건은 총 32 pair 중 최소 24 pair와 각 session 16 pair 중 최소 12 pair가 새 paired QC를 통과하는 것이다. 이는 과학 효과 문턱이 아니라 D2 실행 가능성 문턱이다. 실패하면 `APPARATUS_INVALID_CROSS_SUBJECT_SCALE_FREE_QC`로 닫는다. 통과해도 D1 32 pair는 모델에 재사용하지 않는다.

## 6. 동결된 quotient와 경로식

개발 training fold에서만 채널 중앙값/`1.4826*MAD` scaling, PCA와 whitening을 fit한다. $d\in\{2,3,4\}$에 대해 retained eigenvalue가

\[
\lambda_{d,\min}/\lambda_{1,\max}\ge10^{-6},\qquad
\kappa_d=\lambda_{1,\max}/\lambda_{d,\min}\le10^6
\]

를 만족해야 한다. whitening 좌표 $z$에서 $g_d=I_d$를 관측 quotient의 metric으로 쓴다. ambient 63채널의 pullback은 rank-$d$ PSD일 뿐 전체 공간의 Riemannian metric이라고 부르지 않는다.

history $H\in\{0.1,0.2,0.4\}$ s의 증분 $\Delta z_r=z_r-z_{r-1}$에 대해 기존 baseline은 현재 $z_k$, 국소 미분, 시작점, 길이, 에너지, 증분 평균·공분산·3/4차 중심모멘트·최소/최대, word와 condition을 모두 포함한다. 추가 순서항은

\[
A_{ab}(k)=\frac12\sum_{k-L<p<q\le k}
\left(\Delta z_p^a\Delta z_q^b-\Delta z_p^b\Delta z_q^a\right),
\quad a<b
\]

다. target은 $y=z_{k+25}-z_k$다. $M_0$는 baseline만, $M_1$은 같은 baseline과 $A$를 쓴다. $d=4$에서 intercept 포함 predictor 수는 $p_0=53,p_1=59$다. ridge menu는 $\lambda\in\{10^{-4},10^{-2},1,10^2\}$이고 intercept는 penalty에서 제외한다. normal equation은 금지하고 SVD/lstsq를 쓴다. 모든 transform, predictor standardization 및 coefficient는 training fold에서만 fit한다.

reverse control은 고정 coefficient에서 $A\mapsto-A$, shuffle control은 trial hash로 고정한 20개 증분 순열이다. 재적합하지 않는다.

## 7. D2 선택과 confirmation 판정

D2에서 모든 $(d,H,\lambda)$를 두 방향 leave-one-session-out으로 평가한다. 한 방향의 training pair는 최소 59개, 즉 task/rest 118행이며 $p_1=59<118$이다. 양 방향의 normalized MSE 평균이 최소인 하나를 선택하고, 차이가 $10^{-4}$ 이내면 작은 $d$, 짧은 $H$, 큰 regularization 순으로 고른다. D2 밖에서 menu를 다시 고르지 않는다. 양 방향 중 하나라도 $G_{task}\le0$이거나 경로 이득이 한 word에만 의존하면 confirmation을 열지 않고 `STOP_NO_ROBUST_DEVELOPMENT_GAIN`이다.

trial-condition loss와 경로 이득은

\[
L_{i,c}=d^{-1}\|y_{i,c}-\widehat y_{i,c}\|_2^2,\quad
G_c=\frac{\overline L_{0,c}-\overline L_{1,c}}{\overline L_{0,c}},\quad
D=G_{task}-G_{rest}
\]

다. C1과 C2는 평균 $G_{task}\le0$, reverse/shuffle 열위 또는 QC failure일 때만 futility STOP을 허용하며 성공 수치·CI를 보고하지 않는다. 둘을 통과하면 별도 C3 175 trial에서 session/block pair-preserving 10,000회 percentile bootstrap으로 한 번만 95% CI를 계산한다.

`GENERIC_HISTORY_PASS`는 $G_{task}\ge0.02$, 95% lower bound $>0$, oriented $M_1$이 reverse와 20개 shuffle 각각보다 normalized MSE `0.01` 이상 낮을 때다. 여기에 $D\ge0.01$이고 95% lower bound $>0$이면 `INNER_SPEECH_SPECIFIC_PASS`다. 그 밖은 해당 STOP이며 threshold 변경은 새 판본이다.

## 8. 필수 연구 필드

`BIO_STARTING_MECHANISM`: scalp EEG는 동시 신경 전류의 체적전도 관측이며 단일 막전압·시냅스 전류와 동일하지 않다.

`CE_DELTA`: matched baseline 위에 순서를 보존하는 2차 antisymmetric path area를 추가해 held-out 미래 EEG의 조건부 예측 이득을 검사한다.

`MEASUREMENT_MODEL`: header-locked 63 scalp channel, common-average, causal 45 Hz FIR, 250 Hz decimation, training-fold-only quotient transform. 새 QC는 필터 뒤 창의 common gain에 불변인 무차원 장치 gate다.

`DATA_PROVENANCE`: section 2의 OpenNeuro snapshot/DOI/tag와 고정 receipts. 모든 range의 URL, ETag, Content-Range, byte 수와 SHA-256을 receipt에 기록한다.

`DATA_SPLIT`: A1/A2 32 apparatus trial, D1 32 cross-subject QC-only trial, D2 132 model-development trial, C1/C2/C3 25/50/175 confirmation trial, `sub-01` unused 93은 계속 미사용 봉인.

`OBSERVABLES`: (Q_A,Q_D), pair/session acceptance, 절대 QC matched diagnostics, (L_0,L_1,G_{task},G_{rest},D), reverse/shuffle loss, rank/condition number와 선택 menu.

`RESIDUAL_RULE`: section 5의 75% apparatus 문턱과 section 7의 effect/adverse-control 문턱. 모두 사전 고정한다.

`FALSIFIER`: scale-free QC가 D1 session/total 문턱을 못 넘거나, D2 양방향 이득이 없거나, C3의 fixed prediction gate가 실패하면 해당 단계에서 STOP한다.

`MATCHED_CONTROLS`: 동일 current/derivative/start/length/energy/increment statistics, word/condition, task-rest pair, session split, reverse area와 20 shuffles. 선행 절대 QC는 gating하지 않는 matched apparatus diagnostic이다.

`MODEL_SELECTION`: D2만 사용하고 D1-QC와 confirmation에서 선택하지 않는다.

`REVISION_TRIGGER`: parser/receipt-only 결함은 동일 판본에서 보수할 수 있다. QC 식·cutoff 법칙·75% 문턱, 신호 변환, feature, target, menu 또는 성공 기준 변경은 새 계약이다.

`CLAIM_CEILING`: `L3_REAL_HUMAN_EEG_OBSERVATION_QUOTIENT / WITHIN_DATASET_INNER_SPEECH_TEMPORAL_HISTORY_PILOT / SCALE_FREE_QC_TRANSFER_REQUIRED / SELF_CONSCIOUSNESS_INFINITE_DIMENSION_UNIDENTIFIED / POPULATION_GENERALIZATION_PROHIBITED`.

## 9. 허용 판정

- `APPARATUS_INVALID_CROSS_SUBJECT_SCALE_FREE_QC`
- `STOP_NO_ROBUST_DEVELOPMENT_GAIN`
- `STOP_NO_ORDERED_HISTORY_GAIN`
- `STOP_CONFOUND_OR_NONREPLICATION`
- `PASS_L3_GENERIC_HISTORY_ONLY`
- `PASS_L3_INNER_SPEECH_HISTORY_PILOT`

어떤 판정도 `self_identified=true`, `consciousness_claim=true`, `infinite_dimension_proved=true`, `hippocampal_hash=true`, `brain_mechanism_established=true` 또는 `population_generalization=true`를 허용하지 않는다.
