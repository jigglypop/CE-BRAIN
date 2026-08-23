# BA-SELF1-L3 contract — 현재 상태와 순서 있는 뇌 궤적

Status: COMPLETE

PREDECESSOR: `_workspace/ce/brain-electrical-synaptic-history-e3b-discrimination-20260823`

CE_RUN: `_workspace/ce/brain-self-trajectory-human-fmri-l3-20260824`

## 1. 질문과 형식 지위

한 순간의 관측 EEG 상태와 자극·시행 위상을 이미 알고도, 그 순간까지 온 **순서 있는 경로**가 100 ms 뒤의 EEG 변화를 추가로 예측하는가? 그리고 그 추가 예측력이 같은 스캐너 위상의 휴식 구간보다 내적 발화 구간에서 더 큰가?

이것은 `[경험식]`의 L3 실제 기록 파일럿이다. `자아=경로`, `의식=특정 차원`, 해마의 해시, 무한차원 신경상태, 리만 곡률의 생물학적 실재를 정리로 채택하지 않는다. 유한 관측에서 과거를 확장된 현재 상태에 포함시킬 수 있으므로, 이 실험은 존재론적으로 “상태인가 경로인가”를 판정할 수 없다. 판정 가능한 것은 고정한 관측표현 안에서 순서 있는 과거가 추가 예측 정보를 갖는지뿐이다.

`ce-doc-write`가 참조하는 `docs/axium.md`는 현재 저장소에 존재하지 않는다. 이를 추측해 대체하지 않고, 이 계약에서 사용하는 모든 기호와 판정 경계를 아래에 국소적으로 정의한다.

## 2. 실제 자료와 입력 봉인

주 자료는 OpenNeuro `ds006033`, snapshot `1.0.1`, DOI `10.18112/openneuro.ds006033.v1.0.1`, Git tag object `3af0502b0664b80dacf015e76c436c9ba371527c`이다. 라이선스는 CC0이다. 논문 DOI는 `10.1016/j.dib.2025.112258`이다.

자료는 3명의 건강한 오른손잡이 참가자가 8개 단어를 입술·혀 움직임 없이 마음속으로 한 번 발화하도록 한 동시 EEG–fMRI 기록이다. EEG는 5 kHz, BrainVision multiplexed `IEEE_FLOAT_32`이고, 각 `.vhdr` 첫머리의 `Data created from history path`에는 `Scanner Artifact Correction`과 `Pulse Artifact Correction`이 모두 있어야 한다. A0는 이 줄의 원문과 파일 SHA-256을 각각 봉인한다. 하나라도 없으면 측정모형 미확정으로 멈춘다. 이 실행의 주 endpoint는 EEG이다. fMRI 신호는 열지 않으며 후속 공간 검증용으로 봉인한다.

설명서의 명목 설계와 공개 파일은 같지 않다. EEG 기록은 6개가 아니라 5개이고 `sub-01/ses-01` EEG가 없다. `events.tsv`의 앞부분에는 13–14 ms 간격으로 압축된 비물리적 표식 묶음이 있다. 신호를 보기 전에 고정한 유효 시행 규칙은 다음과 같다.

1. EEG `events.tsv`에서 `onset >= 10 s`, `1.9 s <= duration <= 2.1 s`, `trial_type`이 `rest`와 `fixation`이 아닌 행만 자극 시행으로 인정한다.
2. 이 규칙의 메타데이터 전용 결과는 `sub-01/ses-02=125`, `sub-02/ses-01=89`, `sub-02/ses-02=75`, `sub-03/ses-01=125`, `sub-03/ses-02=125`, 총 539 시행이다. 이 가운데 apparatus는 32개만 열고 `sub-01`의 나머지 93개는 끝까지 미사용·봉인한다. 따라서 분석 배정은 `32 apparatus + 164 development + 250 confirmation = 446`, 미사용 93을 더하면 입력 총계 539다.
3. 압축 표식은 복구·재척도화하거나 결과를 보고 되살리지 않는다. 유효 창이 파일 길이를 벗어나면 그 시행은 입력 불량으로 제외한다.
4. 각 원격 byte-range 응답은 요청 길이, `Content-Range`, 파일 ETag, 추출 byte SHA-256을 receipt에 남긴다. 서버가 정확한 range를 주지 않으면 전체 다중-GB 파일을 묵시적으로 받지 않고 `APPARATUS_INVALID`로 멈춘다.

다섯 `.eeg` 객체의 봉인 시점 크기는 각각 2,301,996,288; 1,751,770,880; 1,382,086,656; 2,333,238,528; 2,314,920,704 bytes이다. 경로 순서는 위 유효 시행 수 표와 같다. 원자료는 저장소에 커밋하지 않는다.

공개 sidecar는 `EEGChannelCount=64`, `ECGChannelCount=1`, `MiscChannelCount=1`이라고 쓰지만, 실제 BrainVision header와 binary geometry는 **총 64열**이고 channel 32의 이름이 `ECG`다. 이는 합계가 맞지 않는 공개 메타데이터 결함이다. 이 실행은 sidecar 합계를 조용히 66열로 해석하지 않는다. A0에서 다섯 header가 모두 `NumberOfChannels=64`, 같은 64개 이름·순서, `Ch32=ECG`, 나머지 63개가 계약의 scalp-name 목록, `DataPoints*64*4=Content-Length`를 만족할 때만 header를 binary schema의 정본으로 채택한다. 어느 파일이라도 다르면 `APPARATUS_INVALID`다. sidecar channel-count 필드는 생물학적 channel type 근거로 사용하지 않는다.

## 3. 측정모형과 무차원 관측 quotient

참가자·세션을 $s$, 5 kHz 표본을 $n$이라 하고, ECG로 표기된 header channel 32를 제외한 scalp 전압을 $v_{s,n}\in\mathbb R^{63}$ µV라 한다. 공통평균 참조 행렬을 $R$이라 한다. 개발자료에서만 정한 채널 중심 $\mu_{\cal D}$와 양의 robust scale $a_{\cal D}$로

$$
\widetilde v_{s,n}=\operatorname{diag}(a_{\cal D})^{-1}R(v_{s,n}-\mu_{\cal D})
$$

를 만든다. 따라서 $\widetilde v$는 무차원이다. 5 kHz 신호에는 501-tap Hamming FIR(`firwin`, cutoff 45 Hz)을 과거 방향의 `lfilter`로 한 번 적용한 뒤 20배 decimation하여 $f_0=250$ Hz로 만든다. 첫 분석표본 앞의 원자료 500개를 filter warm-up으로 읽는다. group delay를 미래 표본으로 보정하지 않으며, zero-phase 또는 양방향 filtering은 금지한다.

개발자료 공분산의 고유벡터 $Q_d$와 양의 고유값 $\Lambda_d$를 써

$$
z_{s,k}=\Lambda_d^{-1/2}Q_d^\top\widetilde v_{s,k},
\qquad d\in\{2,3,4\}
$$

를 정의한다. $z$도 무차원이다. 각 training fold에서 retained spectrum은 $\lambda_{d,\min}/\lambda_{1,\max}\ge10^{-6}$이고 $\kappa_d=\lambda_{1,\max}/\lambda_{d,\min}\le10^6$이어야 한다. 실패한 $d$는 그 fold에서 kill하며 세 후보가 모두 실패하면 `APPARATUS_INVALID_NUMERICAL_RANK`다. 모든 eigenvalue·numerical rank·condition number를 receipt에 남긴다. 유지된 $d$차원 quotient에서는 $g_d=I_d$를 리만 metric으로 사용한다. 원래 63채널 좌표의 $Q_d\Lambda_d^{-1}Q_d^\top$는 rank-$d$인 pullback이므로 전체 채널 공간의 양정치 리만 metric이라고 부르지 않는다.

여기서 $d$는 의식의 차원이 아니다. 개발자료에서 예측 안정성으로 고르는 유한 투영 rank이며, 연속 차원이나 무한차원을 이 표본으로 식별한다는 주장을 금지한다.

## 4. 현재 상태, 경로, 전기 예측식

각 유효 자극 onset을 $o_i$라 한다. 내적 발화 anchor는 $t_i^{\rm task}=o_i+1.2$ s, 휴식 anchor는 $t_i^{\rm rest}=o_i+7.2$ s이다. 두 anchor의 차이는 정확히 6 s, 즉 fMRI TR 2 s의 세 배이므로 잔류 scanner 위상을 맞춘다. 기준시간은 $\tau_0=1$ s이고 $\widetilde t=t/\tau_0$는 무차원이다.

anchor 표본을 $k$, 과거 길이를 $H\in\{0.1,0.2,0.4\}$ s, $L=Hf_0$라 한다. 증가량과 현재 미분근사는

$$
\Delta z_r=z_r-z_{r-1},
\qquad \dot z_k^{\,*}=\frac{\tau_0}{1/f_0}\Delta z_k
$$

이다. 둘 다 무차원이다. 순서를 쓰지 않는 경로 요약은 시작점 $z_{k-L}$, 길이

$$
\ell_k=\sum_{r=k-L+1}^{k}\|\Delta z_r\|_{g_d},
$$

및 에너지 $e_k=L^{-1}\sum_r\|\Delta z_r\|_{g_d}^2$이다. 순서를 섞어도 정확히 보존되는 더 강한 matched summary로 increment 평균 $\bar\delta$, 공분산 $C_\delta$, 좌표별 3·4차 중심모멘트 $m_3,m_4$, 좌표별 최소·최대 $r_{\min},r_{\max}$도 사용한다.

$$
\bar\delta=L^{-1}\sum_r\Delta z_r,\qquad
C_\delta=L^{-1}\sum_r(\Delta z_r-\bar\delta)(\Delta z_r-\bar\delta)^\top,
$$

$$
m_j=L^{-1}\sum_r(\Delta z_r-\bar\delta)^{\odot j}\ (j=3,4),
\qquad r_{\min/\max}=\min/\max_r\Delta z_r
$$

이다. 이 유한 목록이 모든 가능한 순서불변 통계량을 망라한다고 주장하지 않는다. 순서를 쓰는 최소 후보는 2차 반대칭 signature area

$$
A_{ab}(k)=\frac12\sum_{k-L<p<q\le k}
\left(\Delta z_p^a\Delta z_q^b-\Delta z_p^b\Delta z_q^a\right),
\quad 1\le a<b\le d.
$$

이다. $\ell,e,A$는 모두 무차원이다. 같은 점들을 역순으로 읽으면 길이와 에너지는 보존되지만 $A$의 시간방향은 뒤집힌다. 단순 경로 길이를 `자아`의 주 변수로 쓰지 않는 이유가 이것이다.

예측 target은 100 ms 뒤 변화

$$
y_{i,c}=z_{k+25}-z_k,\qquad c\in\{\mathrm{task},\mathrm{rest}\}
$$

이다. 순서 없는 기준모형과 경로모형은 각각

$$
M_0:\quad \widehat y=B_0\psi_0,
\qquad
M_1:\quad \widehat y=B_1[\psi_0,\operatorname{vec}_{a<b}A_{ab}],
$$

$$
\psi_0=[1,z_k,\dot z_k^{\,*},z_{k-L},\ell_k,e_k,
\bar\delta,\operatorname{vech}C_\delta,m_3,m_4,r_{\min},r_{\max},
\text{word},\text{condition}]
$$

로 둔다. 즉 $M_0$도 현재값·국소 변화율·과거 시작점·끝점·길이·에너지·increment multiset의 저차 모멘트·범위·단어·조건을 이미 가진다. session은 predictor가 아니라 leave-one-session-out 분할과 bootstrap 층화에만 쓴다. 한 session으로 학습할 때 session dummy는 상수이고 intercept와 공선이므로 금지한다. $M_1$의 유일한 추가 열은 순서에 민감한 $A$다. 결론은 “$A$가 이 명시된 강한 matched baseline을 이긴다”로 한정한다. 두 모형은 표준화된 predictor에 SVD ridge로 적합한다. normal equation은 금지한다.

## 5. 분할과 짧은 단계별 실행

메타데이터에서 Python `json.dumps([DOI,subject,session,onset_text,word,"BA-SELF1-v1"], ensure_ascii=False, separators=(",",":"))`로 만든 UTF-8 canonical string의 SHA-256을 계산한다. 각 subject 안에서 `(rank-within-session-and-word, session, word, hash)` 순으로 정렬해 아래 개수만큼 앞에서 배정한다. 이 round-robin rank는 session×word strata 사이의 개수 차이를 가능한 한 1 이하로 만든다. 신호 접근 전에 manifest에 subject, session, run=`innerspeech`, onset, word, task/rest anchor, 원래 onset 순서로 만든 `block_id=floor((ordinal-1)/5)`, hash와 split을 기록한다. 인접 신호창이나 같은 시행을 서로 다른 split에 나누지 않는다.

| 단계 | 열 수 있는 신호 | 목적과 다음 문 |
|---|---:|---|
| A0 | 0 | 메타데이터, 헤더, 유효 시행 수, range 가능성만 검사 |
| A1 | `sub-01/ses-02` 8 시행 | byte parsing, channel order, causal filter, 유한값, anchor 정렬만 검사; 과학 endpoint 금지 |
| A2 | 같은 세션 추가 24 시행 | QC cutoff와 코드 adverse control 고정; 효과 크기로 식을 채택하지 않음 |
| D1 | `sub-02` 두 세션의 hash 선두 32 시행 | 명백한 무효 후보를 즉시 kill |
| D2 | `sub-02`의 나머지 132 시행 | $d,H,\lambda$ 하나를 session 교차검증으로 선택하고 모든 계수·QC·변환을 동결 |
| C1 | `sub-03`의 25 시행, confirmation의 10% | QC 실패 또는 방향 반대일 때만 futility STOP; 성공 선언 금지 |
| C2 | 다음 50 시행, 추가 20% | 동일한 futility 문만 사용; 성공 선언 금지 |
| C3 | 남은 175 시행 | 한 번의 최종 판정; 재적합·재선택 금지 |

`sub-01`의 배정되지 않은 93 시행은 분석·QC·정규화 어디에도 쓰지 않는다. D1은 164개 development 중 앞 32개이고 D2는 나머지 132개다. C1/C2/C3는 서로 겹치지 않는 25/50/175개다. C1/C2를 보고 threshold, feature, $d$, $H$, anchor, filter, exclusion rule을 바꾸면 confirmation은 오염된 것으로 처리한다. C1/C2는 futility 여부만 기록하고 신뢰구간이나 성공을 보고하지 않는다. 두 문을 통과하면 C3 175개만으로 최종 95% CI와 성공 여부를 한 번 계산하며 C1/C2 loss를 합치지 않는다.

## 6. 선택, 손실과 판정

개발 menu는 $d\in\{2,3,4\}$, $H\in\{0.1,0.2,0.4\}$ s, dimensionless ridge $\lambda\in\{10^{-4},10^{-2},1,10^2\}$뿐이다. target horizon은 100 ms로 고정한다. `sub-02/ses-01 -> ses-02`와 반대 방향의 평균 normalized MSE가 최소인 조합을 선택한다. 각 방향에서 robust center/scale, PCA/whitening, predictor standardization과 ridge coefficient는 **training session만**으로 fit하고 반대 session에 그대로 적용한다. 최종 transform과 coefficient는 두 development session만으로 다시 fit한 뒤 confirmation에 동결한다. 차이가 $10^{-4}$ 이내면 작은 $d$, 짧은 $H$, 큰 regularization 순으로 단순한 모형을 택한다.

범주형 열은 고정 vocabulary를 쓴다. word reference는 `child`, condition reference는 `rest`이며 나머지를 treatment dummy로 둔다. session dummy는 만들지 않는다. 미지 word/condition level은 `APPARATUS_INVALID`다. intercept는 표준화·ridge penalty에서 제외하고 나머지 열은 training fold의 평균·표준편차로만 표준화한다. 0-variance 열은 session을 포함해 자동 삭제하지 않고, 계약상 예상되지 않은 열이면 `APPARATUS_INVALID_DESIGN`다. penalty matrix $P=\operatorname{diag}(0,1,\ldots,1)$에 대해

$$
\operatorname{df}_\lambda=\operatorname{tr}\{X(X^\top X+\lambda P)^{-1}X^\top\}
$$

를 scalar target당 total effective df로 기록하고, $M_1-M_0$의 차이와 joint value $d\,\operatorname{df}_\lambda$도 기록한다. inverse는 구현상 SVD pseudoinverse이며 receipt에는 numerical rank를 함께 쓴다.

시행별 loss는 $L_{i,c}=d^{-1}\|y_{i,c}-\widehat y_{i,c}\|_2^2$이다. 순서 경로의 상대 이득은

$$
G_c=\frac{\overline L_{0,c}-\overline L_{1,c}}{\overline L_{0,c}},
\qquad D=G_{\rm task}-G_{\rm rest}.
$$

C3의 신뢰구간은 manifest의 원래 onset 순 `block_id`를 세션 안에서 복원추출하는 deterministic 10,000회 percentile bootstrap으로 계산한다. seed는 `BA-SELF1-confirm-v1`이고 2.5/97.5 percentile을 쓴다. 한 번 뽑은 `(session,block_id)` index는 같은 시행의 task/rest, $M_0/M_1$, oriented/reverse, 20개 shuffle loss 전체에 공동 적용한다. 20개 shuffle는 시행 hash와 shuffle 번호로 이미 고정해 block 안에 nested하며 bootstrap마다 다시 생성하지 않는다. C1/C2에는 CI를 계산하지 않는다.

최종 결과는 계층적으로만 읽는다.

1. `GENERIC_HISTORY_PASS`: $G_{task}\ge0.02$, 95% block-bootstrap lower bound가 0보다 크고, 고정 계수에서 oriented history가 reverse와 20개 고정 shuffle 각각보다 normalized MSE를 적어도 0.01 낮춘다.
2. `INNER_SPEECH_SPECIFIC_PASS`: 1을 통과한 뒤에만, $D\ge0.01$이고 95% lower bound가 0보다 크다.
3. 1만 통과하면 관측 EEG의 일반적 순서 의존성만 남긴다. 2까지 통과해도 `내적 발화 조건의 궤적 예측 파일럿`이며 자아나 의식의 식으로 승격하지 않는다.

역순·shuffle은 새 계수를 적합하지 않는다. 2차 반대칭 feature는 재적합하면 부호변환을 계수가 흡수할 수 있으므로, 오직 oriented 개발 계수를 고정한 adverse input으로 평가한다.

## 7. 즉시 중단과 품질 규칙

- A1에서 range 길이·float32 크기·`DataPoints*64*4`·header channel 순서 중 하나라도 맞지 않으면 `APPARATUS_INVALID`.
- 비유한 값, zero robust scale, causal filter의 미래 leakage, confirmation 변환 재적합이 하나라도 있으면 `APPARATUS_INVALID`.
- QC는 endpoint loss를 계산하지 않는 A1+A2 32쌍에서만 봉인한다. 각 causal-filtered task/rest 창의 `nonfinite_count`, 채널별 MAD=0 비율, 최대 절대 common-reference amplitude, 최대 절대 1-step difference를 기록한다. nonfinite가 하나라도 있거나 MAD=0 채널 비율이 0보다 크면 그 쌍은 불량이다. 두 amplitude metric의 cutoff는 apparatus 64창 각각의 `median + 6*MAD`이고 해당 MAD가 0이면 `APPARATUS_INVALID_QC_SCALE`이다. task/rest 쌍 중 하나가 cutoff를 넘으면 둘 다 버린다. 어느 confirmation 세션이든 제외율이 20%를 넘으면 효과를 계산하지 않고 STOP한다.
- D1에서 $M_1$이 $M_0$보다 나쁘거나, frozen reverse/shuffle가 oriented와 같거나 더 좋으면 해당 $(d,H)$ 후보를 kill한다. 모든 후보가 죽으면 D2와 confirmation을 열지 않는다.
- D2 session 양방향 중 하나라도 $G_{task}\le0$이거나 이득이 단어 identity 하나에만 의존하면 confirmation을 열지 않는다.
- C1/C2는 평균 $G_{task}\le0$, reverse/shuffle 우위, 또는 QC failure일 때만 futility STOP한다. 양의 값만으로 성공하지 않는다.
- C3에서 section 6 경계를 못 넘으면 해당 주장을 실패로 기록한다. 데이터 불순도를 이유로 사후 threshold를 내리지 않는다.

## 8. 필수 연구 필드

`BIO_STARTING_MECHANISM`: 두피 EEG는 동시 신경 전류원이 체적전도를 거쳐 전극 전압으로 혼합된 관측치이며, 공개 헤더가 기록한 scanner/pulse artifact correction 이후의 5 kHz 전기 신호에서 시작한다. EEG를 뉴런별 막전압이나 완전한 뇌상태와 동일시하지 않는다.

`CE_DELTA`: calibration-whitened 관측 quotient의 고정 metric 위에서, 현재·시작점·길이·에너지를 넘는 2차 순서 signature $A$를 미래 전압변화 예측식에 추가하는 경험적 후보.

`MEASUREMENT_MODEL`: header의 총 64열 중 이름이 `ECG`인 channel 32를 제외한 63 scalp channels의 공통평균 전압 혼합, header history에 봉인된 artifact correction, causal low-pass/decimation, development-training-fold 중심·scale·PCA를 포함한다. 불일치하는 sidecar channel-count 합계는 schema로 쓰지 않는다. 숨은 신경상태는 이 관측 kernel로 나눈 동치류까지만 식별된다.

`DATA_PROVENANCE`: OpenNeuro `ds006033` v1.0.1, DOI와 Git tag object는 section 2와 같다. 원격 S3 byte ranges만 읽고 원자료는 commit하지 않는다. 모든 ETag·크기·range SHA-256·코드·환경은 receipt에 기록한다.

`DATA_SPLIT`: `sub-01` 32개 apparatus/QC와 미사용 93개, `sub-02` 164개 development/model selection, `sub-03` 25/50/175개의 sealed futility/futility/final confirmation. 시행 배정은 신호 접근 전 session×word rank와 고정 hash 순서다.

`OBSERVABLES`: 시행별 $L_0,L_1$, $G_{task}$, $G_{rest}$, $D$, reverse/shuffle 손실, 선택된 $d,H,\lambda$, eigenvalue spectrum, session별 QC/exclusion, range receipts와 source/environment hashes.

`RESIDUAL_RULE`: section 6의 2%, 1%, lower-bound와 adverse-control margin을 그대로 쓴다. MSE는 무차원 whitened target에서 계산한다. 비유한 값은 fail-closed다.

`FALSIFIER`: 순서 feature가 강한 기준모형을 못 이김; 이득이 rest에도 동일함; 방향을 뒤집거나 순서를 섞어도 이득이 유지됨; 독립 참가자 `sub-03`에서 방향이 사라짐; session/QC/word confound가 이득을 복제함.

`MATCHED_CONTROLS`: 현재값·미분·시작점·끝점·길이·에너지·increment 공분산/3·4차 모멘트/범위, 동일 word/condition 정보, session-stratified split, 6 s 차이의 같은 scanner phase task/rest, 고정계수 path reversal, 20개 시행내 order shuffle, train-transform-only session 교차검증.

`MODEL_SELECTION`: section 6의 유한 menu만 `sub-02`에서 선택한다. confirmation에서는 PCA, scale, coefficients, threshold, window, dimension을 다시 맞추지 않는다. 고정 treatment coding과 effective df를 receipt에 남긴다. 각 scalar output의 최대 predictor 수는 최소 development training session의 유효 시행 수보다 작아야 하며 그렇지 않은 $(d,H)$는 fit 전에 kill한다.

`REVISION_TRIGGER`: byte offset, parser, causal-filter 구현의 명백한 코드 결함만 한 번 국소 수정할 수 있다. 실패 source·receipt를 보존하고 식·분할·threshold·feature menu·주장 상한을 바꾸지 않는다. 과학 endpoint 실패는 새 판본 사유이지 같은 판본 수정 사유가 아니다.

`CLAIM_CEILING`: `L3_REAL_HUMAN_EEG_OBSERVATION_QUOTIENT / WITHIN_DATASET_INNER_SPEECH_TEMPORAL_HISTORY_PILOT / SELF_CONSCIOUSNESS_INFINITE_DIMENSION_UNIDENTIFIED / POPULATION_GENERALIZATION_PROHIBITED`.

## 9. 선행 증거와 금지된 승격

`PREDECESSOR_EVIDENCE`:

| item | SHA-256 | 허용되는 상속 |
|---|---|---|
| brain route ledger | `8256c0eb6b48e5c9a83ba061049e5409044a1d90da9cef85f45027daf48c8c51` | 실제 자료 우선순위, 의식/해마/공통 4차원 금지, 관측 quotient 경계 |
| E3b `12-routes.md` | `b808a6c0d30b7b443289455e10f29123b6d1822c18af61c14353e7cdb296b77d` | 실제 endpoint가 후속으로만 열릴 수 있다는 경계 |
| E3b `31-validation.md` | `ad94ddd9dd20040652551bee797aa76731914c9bd475073dd953007508d787ac` | 고정 synthetic apparatus 결과만 상속 |
| E3b `40-final-report.md` | `5ace2967911092add9f2d4347d0eed5d01ef65e60f1277e4be5f25fc699bbf67` | compact history의 생물학·의식 승격 금지 |

E3b의 compact $C^\infty$ kernel 결과는 이 EEG 식의 참이라는 증거가 아니다. 이 실행은 별도의 실제 관측 시험이며, 유한 기록으로 무한차원 상태공간을 증명할 수 없다는 no-go를 유지한다. 경로 의존성은 충분히 큰 확장 상태의 Markov 표현과 관측적으로 동치일 수 있다.

## 10. 결과 라벨

- `PASS_L3_INNER_SPEECH_HISTORY_PILOT`: section 6의 두 계층과 모든 무결성 문 통과.
- `PASS_L3_GENERIC_HISTORY_ONLY`: 일반 순서 이득만 통과하고 task-rest 특이성은 실패.
- `STOP_NO_ORDERED_HISTORY_GAIN`: 무결성은 유효하나 경로식이 기준모형을 못 이김.
- `STOP_CONFOUND_OR_NONREPLICATION`: 개발 이득이 독립 참가자, session, rest 또는 adverse control에서 분리되지 않음.
- `APPARATUS_INVALID`: 입력·범위·타이밍·필터 leakage·QC·seal 위반으로 과학 해석 불가.

어떤 라벨도 `self_identified=true`, `consciousness_claim=true`, `infinite_dimension_proved=true`, `hippocampal_hash=true`, `brain_mechanism_established=true`, `population_generalization=true`를 허용하지 않는다.
