# BA-SELF3-L3 연구 계약 — 채널별 affine 불변 QC 뒤의 경로 예측

Status: COMPLETE

PREDECESSOR: `_workspace/ce/brain-self-trajectory-human-eeg-qc2-l3-20260824`

CE_RUN: `_workspace/ce/brain-self-trajectory-human-eeg-channel-qc3-l3-20260824`

## 1. 질문과 판본 차이

과학 질문은 그대로다. 현재 관측 EEG quotient, 국소 변화율, 시작점, 길이·에너지와 순서를 버린 증분 통계를 조건화한 뒤에도, 순서가 있는 과거 경로의 2차 반대칭 area가 100 ms 뒤 관측 EEG 변화를 held-out 자료에서 추가 예측하는가?

BA-SELF1의 절대 QC는 D1에서 0/32 pair를 남겼다. BA-SELF2의 공통-gain 불변 QC는 13/32 pair만 남겼고 session별 8/16, 5/16으로 사전 24/32 및 12/16 gate를 실패했다. 두 판본 모두 quotient, target, feature, loss 또는 모델을 계산하기 전에 끝났다. 따라서 경로 식은 아직 **[경험 후보: 미검증]**이다.

BA-SELF2의 대안 경로 문서는 D1 scale-free 값을 보기 전에 채널별 정규화 R2를 별도 계약 후보로 고정했다. 이 판본은 그 R2만 실행한다. 신호 변환, 경로식, model menu, target, 성공 기준과 `sub-03` confirmation은 바꾸지 않는다. 바뀌는 것은 QC의 분모를 각 채널 자체 scale에 대응시키는 것과, 아직 열지 않은 D2 중 32 pair를 signal-blind B1 apparatus subset으로 영구 분리하는 것뿐이다.

`docs/axium.md`는 저장소에 없으므로 이 계약이 그것을 대체한다고 주장하지 않는다. 모든 기호와 판정 경계를 아래에 국소적으로 정의한다.

## 2. source lock과 선행 실패의 허용 사용

자료는 OpenNeuro `ds006033` version `1.0.1`, DOI `10.18112/openneuro.ds006033.v1.0.1`, Git tag object `3af0502b0664b80dacf015e76c436c9ba371527c`, CC0다. 1차 자료 논문 DOI는 `10.1016/j.dib.2025.112258`이다. 원 EEG payload와 decoded window를 저장소에 저장하거나 commit하지 않는다.

| 선행 항목 | SHA-256 | 이 판본에서 허용하는 사용 |
|---|---|---|
| BA-SELF2 contract | `8eb85e4ce7218112c082b84e0f754ae3fa0afb1995374a9675c581164880517f` | 고정 전처리, quotient/path/model/confirmation 경계 |
| BA-SELF2 sources | `54c318e3d42af474c253e97c2a9b56f83fe906959239b380c81365027defe55f` | dataset와 측정 provenance |
| BA-SELF2 math | `403c7d73d01d8d736aff2db220d74f985cbcf9b4ff3d6aeb1c7173c1e8d7f827` | 공통-gain QC의 한계와 state/path no-go |
| BA-SELF2 routes | `b4cb7f0115a9158c9b9b02e2835845104eefaa4a7f398de8884ef2e8ece7206c` | D1 값을 보기 전에 선언된 R2 후보 |
| BA-SELF2 audit | `c91670bfc8e3fd1d9d95b22fe5ff886996408db10e958098f2f2a9dfc43e548d` | D1 outcome 비개방과 confirmation 봉인 |
| BA-SELF2 final | `f7a2c993751d8357226c71d6abc27305cddb39f0639aee151241720efc0f295b` | R1 apparatus 실패 사실만 |
| A0 metadata receipt | `5bc7fb8acebe366db84ba6f4aa9b95eae2051e3bf0f5760792c7ac9e6520a3f7` | header, URL, ETag, binary geometry |
| trial manifest | `4ebc8efdca4e277a989c8e7aceb0f00911d84fd20e6b6980dc94cbce7062a061` | 원래 A/D/C 배정과 trial hash |
| BA-SELF2 D1 receipt | `7ea150e088625774b75ce1ceec35b8529e3abae470348fa4f693188e3820d28a` | R1이 실패했고 D1은 QC-only로 소진됐다는 사실만 |

D1의 R2 값은 계산하지 않으며 cutoff, B1 gate 또는 model에 사용하지 않는다. D1 32 pair는 영구 제외한다. 선행 D1과 동일한 `sub-02` recording에서 신호 분포를 이미 일부 보았으므로 B1을 독립 피험자 replication이라고 부르지 않는다. B1은 신호값이 미개봉인 **held-out window apparatus gate**일 뿐이다.

실제 binary 권위는 다섯 BrainVision header의 64열, ECG index 31(0-based), 63 scalp channel과 `DataPoints*64*4=Content-Length`다. sidecar 합계 66과의 불일치는 선언된 metadata 결함으로 유지한다.

## 3. 고정 전기 변환

각 anchor에서 5 kHz 표본 `anchor-2500`부터 `anchor+500`까지 3,001개, 즉 768,256 byte만 정확한 HTTP Range로 읽는다. `206`, `Content-Range`, byte 수, A0 ETag를 모두 검사하고 payload SHA-256을 receipt에 남긴다. little-endian multiplexed float32로 해석하고 ECG를 제거한 뒤 63 scalp channel에 common-average reference를 적용한다.

501-tap Hamming FIR, cutoff 45 Hz를 `scipy.signal.lfilter`로 인과 적용하고 첫 500 raw sample을 버린 뒤 20배 decimation하여 250 Hz의 $126\times63$ 창 $X$를 만든다. zero-phase, 역방향 filtering과 미래 sample을 이용한 group-delay 보정은 금지한다. anchor index는 100, target index는 125다.

## 4. R2 채널별 무차원 QC

[정의] 채널별 시간 중앙값을 뺀 residual과 그 robust scale을

\[
R_{tc}=X_{tc}-\operatorname{median}_{u}X_{uc},\qquad
s_c=1.4826\operatorname{median}_{t}|R_{tc}|
\]

로 둔다. 1-step difference와 그 중심 robust scale은

\[
D_{tc}=X_{t+1,c}-X_{tc},\qquad
r_c=1.4826\operatorname{median}_{t}
|D_{tc}-\operatorname{median}_{u}D_{uc}|
\]

다. R2 gate는

\[
Q_A^{\rm ch}=\max_{t,c}\left|\frac{R_{tc}}{s_c}\right|,
\qquad
Q_D^{\rm ch}=\max_{t,c}\left|\frac{D_{tc}}{r_c}\right|
\]

다. 둘은 무차원이다. 각 채널에 시간불변 nonzero gain과 offset이 따로 작용하는

\[
X'_{tc}=a_cX_{tc}+b_c,\qquad a_c\ne0
\]

에서도 절댓값 비율이므로 정확히 불변이다. 시간에 따라 변하는 gain, channel mixing/montage, nonlinear saturation, 다채널 동시 artifact 또는 생리 차이에 불변이라고 주장하지 않는다. 넓고 오래 지속되는 artifact가 자기 scale을 키워 통과할 수 있다는 약점도 의도적으로 공개한다.

nonfinite가 하나라도 있거나 어떤 $s_c,r_c$라도 0/nonfinite이면 해당 창을 즉시 탈락시킨다. task/rest 중 하나라도 탈락하면 pair 전체를 탈락시킨다. A2의 64개 창만으로 각 $Q$에 대해

\[
c_Q=\operatorname{median}(Q)+6\operatorname{median}|Q-\operatorname{median}(Q)|
\]

를 한 번 동결한다. cross-window MAD가 0/nonfinite이면 `APPARATUS_INVALID_QC_SCALE`다. BA-SELF1/2의 absolute/R1 지표는 matched diagnostic으로만 기록하고 R2 판정에는 쓰지 않는다.

## 5. signal-blind B1 배정과 단계

선행 manifest에서 `split=D2`인 trial만 사용한다. 각 session 안에서

\[
k_i=\operatorname{SHA256}(\text{UTF8}(``BA\text{-}SELF3\text{-}B1\text{-}v1:''\Vert\text{trial\_hash}_i))
\]

를 계산하고 `(k_i,trial_hash)` 오름차순의 첫 16개를 B1, 나머지를 D2-M으로 고정한다. 신호 접근 전에 allocation receipt에 모든 trial hash, 원래 split, 새 split, session, word와 key를 기록하고 SHA-256으로 봉인한다. 배정 산술은 B1 32 pair(16/16), D2-M 100 pair(`ses-01=57`, `ses-02=43`)다. 두 D2-M session 모두 8개 word level을 포함해야 하며 아니면 신호 접근 전에 `APPARATUS_INVALID_DESIGN`이다.

| 단계 | 허용 신호 | 다음 문 |
|---|---:|---|
| P0/A0 | 0 | parser·filter 상속 hash, allocation, affine/channelwise invariance, unit scaling, spike/step와 broad-artifact adverse synthetic test |
| A1 | 기존 `sub-01/ses-02` 8 trial, 16창 | exact range와 R2 정의역만; endpoint 금지 |
| A2 | 같은 recording 총 32 trial, 64창 | R2 cutoff 동결; 효과를 보고 변경 금지 |
| B1 | 미개봉 D2에서 hash 배정한 `sub-02` 32 pair | R2 held-out-window apparatus transfer만; $z$/target/feature/loss/model 금지 |
| D2-M | B1을 제외한 `sub-02` 100 pair | B1 통과 뒤 최초 경로식 development/selection |
| C1/C2/C3 | `sub-03` 25/50/175 | 고정 futility/futility/final confirmation; 그 전까지 봉인 |

B1 통과 조건은 총 24/32 pair 이상 및 각 session 12/16 이상이다. 실패하면 `APPARATUS_INVALID_CHANNELWISE_QC_TRANSFER`로 이 판본을 닫는다. 통과해도 B1은 모델에 재사용하지 않는다.

D2-M에서 R2 paired QC를 적용한 뒤 어느 session이든 30 pair 미만이면 $2N\le59$가 되어 최대 모델의 행 수 gate를 만족하지 못하므로 `APPARATUS_INVALID_D2_DESIGN`으로 닫는다.

## 6. 동결된 quotient와 경로식

D2-M training fold에서만 채널 중앙값/`1.4826*MAD` scaling, PCA와 whitening을 fit한다. 후보 rank는 $d\in\{2,3,4\}$이며

\[
\lambda_{d,\min}/\lambda_{1,\max}\ge10^{-6},\qquad
\kappa_d=\lambda_{1,\max}/\lambda_{d,\min}\le10^6
\]

를 만족해야 한다. whitening 좌표에서 $g_d=I_d$는 유한 관측 quotient의 metric일 뿐 ambient 63차원 또는 실제 뇌 전체의 Riemannian metric이 아니다.

history $H\in\{0.1,0.2,0.4\}$ s에 대해 $M_0$는 현재 $z_k$, 국소 미분, 시작점, 길이, 에너지, 증분 평균·공분산·3/4차 중심모멘트·최소/최대, word와 condition을 모두 포함한다. $M_1$은 같은 baseline에

\[
A_{ab}(k)=\frac12\sum_{k-L<p<q\le k}
(\Delta z_p^a\Delta z_q^b-\Delta z_p^b\Delta z_q^a),\quad a<b
\]

만 추가한다. target은 $y=z_{k+25}-z_k$다. $d=4$에서 intercept 포함 $p_0=53,p_1=59$다. ridge menu는 $\lambda\in\{10^{-4},10^{-2},1,10^2\}$이고 intercept는 penalty에서 제외한다. 모든 transform, standardization과 coefficient는 training session에서만 fit하며 normal equation은 금지하고 SVD/lstsq를 쓴다.

reverse control은 고정 coefficient에서 $A\mapsto-A$, shuffle control은 trial hash로 고정한 20개 증분 순열이다. adverse input에서 재적합하지 않는다.

## 7. D2-M 선택과 confirmation

모든 $(d,H,\lambda)$를 두 방향 leave-one-session-out으로 평가한다. 양 방향 normalized MSE 평균이 최소인 하나를 선택하고 차이가 $10^{-4}$ 이내면 작은 $d$, 짧은 $H$, 큰 regularization 순으로 고른다. 한 방향이라도 $G_{task}\le0$이거나 이득이 한 word에만 의존하면 confirmation을 열지 않고 `STOP_NO_ROBUST_DEVELOPMENT_GAIN`이다.

\[
L_{i,c}=d^{-1}\|y_{i,c}-\widehat y_{i,c}\|_2^2,\quad
G_c=\frac{\overline L_{0,c}-\overline L_{1,c}}{\overline L_{0,c}},\quad
D=G_{task}-G_{rest}.
\]

C1/C2는 평균 $G_{task}\le0$, reverse/shuffle 열위 또는 QC failure일 때만 futility STOP을 허용하고 성공 수치나 CI를 보고하지 않는다. 통과하면 별도 C3 175 trial에서 session/block pair-preserving 10,000회 percentile bootstrap으로 한 번만 95% CI를 계산한다.

`GENERIC_HISTORY_PASS`는 $G_{task}\ge0.02$, 95% lower bound $>0$, oriented $M_1$이 reverse와 20개 shuffle 각각보다 normalized MSE 0.01 이상 낮을 때다. 여기에 $D\ge0.01$이고 95% lower bound $>0$이면 `INNER_SPEECH_SPECIFIC_PASS`다. threshold, QC, feature 또는 menu 변경은 새 판본이다.

## 8. 형식 지위, no-go와 필수 필드

[정의/측정모형] $Q_A^{\rm ch},Q_D^{\rm ch}$는 관측장치 gate다. 통과가 생물학적 동질성이나 신경 품질의 충분조건은 아니다.

[조건부 정리] retained quotient의 $g_d=I_d$와 area reversal은 정의역/rank 조건 아래 성립한다.

[경험 후보: 미검증] ordered area가 matched baseline보다 held-out 미래 EEG를 더 잘 예측할 수 있다.

[미완성/no-go] 유한 history를 확장 상태로 쓰면 path predictor는 state function이 된다. 유한 EEG는 전체 신경 상태가 아니라 관측 quotient만 식별한다. 따라서 양성/음성 예측 결과 어느 쪽도 자아가 상태인지 경로인지 존재론적으로 결정하지 못한다.

`BIO_STARTING_MECHANISM`: scalp EEG는 동시 신경 전류의 체적전도 관측이며 단일 막전압이나 시냅스 전류가 아니다.

`CE_DELTA`: 순서를 버린 강한 baseline에 2차 antisymmetric path area만 추가한다.

`MEASUREMENT_MODEL`: header-locked 63 scalp channel, common-average, causal 45 Hz FIR, 250 Hz decimation, channelwise affine-invariant R2 QC, fold-local quotient transform.

`DATA_PROVENANCE`: section 2 source와 모든 exact range receipt.

`DATA_SPLIT`: A1/A2 32 calibration, D1 32 burned, B1 32 apparatus-only, D2-M 100 development, C1/C2/C3 25/50/175 confirmation, `sub-01` unused 93 sealed.

`OBSERVABLES`: R2 ratios/cutoffs, pair/session acceptance, matched prior QC, model losses/gains, adverse controls, rank/condition number와 selected menu.

`RESIDUAL_RULE`: B1 24/32 및 12/session, D2-M 30/session design gate, section 7 effect gates.

`FALSIFIER`: B1 transfer 실패, D2-M robust gain 실패 또는 confirmation fixed gate 실패에서 즉시 해당 route를 닫는다.

`MATCHED_CONTROLS`: prior absolute/R1 diagnostics, 동일 current/derivative/start/length/energy/increment statistics, word/condition, task/rest pair, reverse area, 20 shuffles.

`MODEL_SELECTION`: D2-M에서만 허용한다. A1/A2/B1/D1/confirmation 선택은 금지한다.

`REVISION_TRIGGER`: parser/receipt-only 결함만 같은 판본에서 보수한다. R2 식, cutoff 법칙, split, gate, target, feature, menu 또는 success threshold 변경은 새 계약이다.

`CLAIM_CEILING`: `L3_REAL_HUMAN_EEG_OBSERVATION_QUOTIENT / CHANNELWISE_QC_HELDOUT_WINDOW_TRANSFER_REQUIRED / WITHIN_DATASET_TEMPORAL_HISTORY_PILOT_ONLY / SELF_CONSCIOUSNESS_INFINITE_DIMENSION_UNIDENTIFIED / POPULATION_GENERALIZATION_PROHIBITED`.

## 9. 허용 판정

- `APPARATUS_INVALID_CHANNELWISE_QC_TRANSFER`
- `APPARATUS_INVALID_D2_DESIGN`
- `STOP_NO_ROBUST_DEVELOPMENT_GAIN`
- `STOP_NO_ORDERED_HISTORY_GAIN`
- `STOP_CONFOUND_OR_NONREPLICATION`
- `PASS_L3_GENERIC_HISTORY_ONLY`
- `PASS_L3_INNER_SPEECH_HISTORY_PILOT`

어떤 판정도 자아·의식·무한차원·해마 hash·뇌 기전·AGI·모집단 일반화를 활성화하지 않는다.
