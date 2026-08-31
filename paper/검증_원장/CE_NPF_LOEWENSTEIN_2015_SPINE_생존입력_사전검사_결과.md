# CE-NPF Loewenstein 2015 저자-catalogued 돌기 재관측 입력 사전검사 결과

Status: `CONTENT_IDENTITY_PASS / LONG_TERM_AVAILABILITY_NOT_LOCKED / PARTIAL_MODEL_ELIGIBILITY / FIT_NOT_RUN`

Claim ceiling: `INPUT_ELIGIBILITY_ONLY / BIO_EVIDENCE_L0`

Stage 10: `STAGE10_INTEGRATED_MODEL_NOT_IDENTIFIABLE`

판정일: 2026-08-31

## 1. 목표와 이번 gate

**최종 목표.** 발달 prior 위에서 연결·가중치·전도 지연이 국소 출력-상대
Riemann 계량을 어떻게 바꾸는지 생물학적 자료로 판정한다.

**이번 하위 목표.** marked-contact 수식을 실제 자료에 연결하기 전에 공개 종단
spine 표가 상수 CTMC, age-only semi-Markov, age+mark PDMP의 공통 관측우도를
지탱하는지 판정한다.

**왜 필요한가.** 동일 spine의 시간·상태·mark가 있어도 동물 대응, 검출오차,
위험집합, left truncation과 censoring이 없으면 생물학적 전이율과 관측상
등장·소실을 분리할 수 없다.

**목표 명료성과 이탈.** 이 문서는 입력 적격성 검사다. 행 수와 관측 전이의
기술통계를 열었지만 모델 적합이나 가설검정을 하지 않았다. 따라서 아래
`PARTIAL_MODEL_ELIGIBILITY`를 생물학적 CTMC/PDMP 지지로 읽으면 목표 이탈이다.

**다음 gate.** baseline 뒤 first-catalogued 공통 rowset, leave-one-cell-out 분할, train-only
표준화·frailty와 판정 문턱을 결과 전에 별도 계약으로 잠가야 한다. 그 전에는
어떤 model fit도 허가하지 않는다.

## 2. 원자료 잠금과 재사용 경계

저자 연구실의 [데이터 사전](https://decision-making-lab.com/data/spines/spines.html)은
13개 열의 의미와 4일 간격 6회 촬영을 설명하고, 같은 페이지가
[headerless CSV](https://decision-making-lab.com/data/spines/publication_data.csv)를
배포한다. 논문은 [Loewenstein, Yanover & Rumpel 2015](https://doi.org/10.1523/JNEUROSCI.2917-14.2015)다.

원자료는 저장소에 복제하지 않았다. 아래 hash는 2026-08-31에 저자 호스트에서
읽은 **내용의 동일성**만 잠근다. CSV와 데이터 사전에는 별도 dataset DOI,
판본 번호와 명시적 데이터 라이선스가 없으므로 장기 가용성이나 영구 판본은
잠기지 않았다. 이 거버넌스 한계와 아래 생물학적 식별 한계는 서로 다른 정지
사유이며, 재사용은 `metadata_and_hash_only_no_raw_vendoring`으로 제한한다.

| 대상 | bytes | SHA-256 |
|---|---:|---|
| headerless CSV | 569,938 | `2f6343606f62abb07b82491a71f0e4a4a898923d2bcf86aa4be8d596276d0062` |
| HTML 데이터 사전 | 4,850 | `995bdb601f6ff71cd5877486dfdd0576db576c15effcc8c52db560eb523d9657` |
| 정규화 source-column schema (upstream `spine` 용어) | — | `5f695db3ee5f4818e1e580d447e5d5bf1ac6f5fe64d3d3a16338cf91012bd718` |

CSV의 HTTP `ETag`는 `8b252-5cb8b404a82eb`, `Last-Modified`는
`2021-09-09T07:50:23Z`였다. 이는 공급자 판본 ID가 아니라 보조 잠금값이다.
위 schema hash는 원자료 열과 저자의 역사적 `spine` 명칭만 잠근다. 생물학적
endpoint의 좁은 의미는 auditor·receipt의 별도 `state_semantics`와
`biological_scope`가 잠그며 source-column schema hash로 대신하지 않는다.

논문이 정한 표본·선별 경계도 함께 잠근다. 자료는 약 6개월령 성체 수컷
GFP-M 마우스 6마리의 청각피질 L5 pyramidal neuron 8개에서 촬영한 apical
tuft를 대상으로 한다. 축방향 해상도 한계 때문에 측방으로 향한 돌기를
선별했고 filopodia를 spine과 분리하지 않았다. 따라서 이 문서의 endpoint는
“이 표본·영상·저자 추적절차에서 저자가 catalog한 측방 돌기가 다음 session에
다시 catalog되는가”이지, 모든 성숙 흥분성 spine이나 기능성 synapse의 생존이
아니다.

## 3. 실제 행 구조와 관측 기술통계

감사기는 `(cell,dendrite,spine,session)`을 복합키로 사용했다. 행이 있으면
“저자가 그 session에 측방 돌기로 catalog한 상태”이고, 같은 복합 spine ID의
union panel에 행이 없으면 “catalog되지 않음”이다. filopodia가 분리되지 않았고
검출도 보정되지 않았으므로 이것은 성숙 spine 또는 latent synaptic-contact
truth가 아니다.

| 검사 | 결과 |
|---|---:|
| 행 × 열 | 8,699 × 13 |
| cell / dendrite / spine | 8 / 48 / 3,688 |
| session | 1–6, protocol 간격 4일 |
| 중복 복합키 | 0 |
| 내부 `1→0→1` gap | 0 |
| session 1의 age-unknown prevalent spine | 1,420 |
| session 2–6 baseline 뒤 first-catalogued 돌기 | 2,268 |
| session 6까지 가시인 right-censored spine | 1,388 |
| 현재 가시 상태에서 시작한 4일 위험구간 | 7,311 |
| 다음 session에도 가시 / catalog에서 소실 | 5,011 / 2,300 |

각 4일 구간의 관측 집계는 다음과 같다. `first catalogued`는 birth event가
아니다. 전체 가능한 contact slot이나 branch length-time denominator가 없기
때문이다.

| session | 가시 at risk | 다음에도 가시 | 다음에 비가시 | 다음 session 첫 catalog |
|---:|---:|---:|---:|---:|
| 1→2 | 1,420 | 998 | 422 | 517 |
| 2→3 | 1,515 | 1,042 | 473 | 495 |
| 3→4 | 1,537 | 1,002 | 535 | 371 |
| 4→5 | 1,373 | 988 | 385 | 478 |
| 5→6 | 1,466 | 981 | 485 | 407 |

모든 48개 복합 dendrite ID는 매 session에 적어도 한 행이 있었지만, 이것은
동일 branch의 coverage mask나 길이 노출을 보장하지 않는다. 데이터 사전도
session마다 좌표 원점이 달라 절대 위치가 무의미하다고 명시하므로 XY를 등록된
공간 노출로 사용하지 않는다.

relative intensity, 두 PCA eigenvalue와 spine–dendrite 거리는 모든 catalogued
행에 수치로 존재했다. intensity는 임의단위이고 거리는 pixel이며, 측정오차
calibration은 없다. z-slice offset은 형태가 아니라 상대 위치·방향·검출의
nuisance로만 사용한다. 따라서 prospective association은 열 수 있어도 물리단위
mark drift나 jump kernel은 열 수 없다.

## 4. 이 자료에 맞는 정확한 축소 likelihood

복합 spine을 $q=(c,d,s)$, session을 $\ell$, 예정시간을

$$
t_\ell=4(\ell-1)\ {\rm day}
$$

로 둔다. $O_{q\ell}=1$은 해당 행이 존재한다는 관측 call이다. 현재 가시인
$O_{q\ell}=1$, $\ell<6$ 구간에서만

$$
Y_{q\ell}=1-O_{q,\ell+1}
$$

를 다음 방문 비카탈로그 indicator로 정의한다. 구간 누적 hazard가

$$
\Lambda_{q\ell}=\int_{t_\ell}^{t_{\ell+1}}
\lambda_q(u\mid\mathcal H_{q\ell})\,du
$$

이면 absorbing visible-state working model의 조건부 likelihood는

$$
\Pr(Y_{q\ell}=0\mid\mathcal H_{q\ell})=e^{-\Lambda_{q\ell}},
\qquad
\Pr(Y_{q\ell}=1\mid\mathcal H_{q\ell})=1-e^{-\Lambda_{q\ell}},
$$

$$
\ell_{\rm vis}
=\sum_{q,\ell:O_{q\ell}=1,\ell<6}
\left[-(1-Y_{q\ell})\Lambda_{q\ell}
+Y_{q\ell}\log\!\left(1-e^{-\Lambda_{q\ell}}\right)\right].
\tag{L2015.1}
$$

사건을 midpoint에 놓거나 한 번의 정확한 jump로 대치하지 않는다. 식
(L2015.1)은 interval event를 적분한 결과다. 다만 검출 kernel이 없으므로
latent biological disappearance likelihood가 아니라 catalogued visibility의
working likelihood다.

현재 4일 구간에서 hazard가 상수라는 축소모형을 쓸 때에는 단위를 숨기지 않고

$$
\lambda_q(u\mid\mathcal H_{q\ell})
=e^{\eta_{q\ell}}\ {\rm day}^{-1},\qquad
\Lambda_{q\ell}=4e^{\eta_{q\ell}},\qquad
\operatorname{cloglog}\Pr(Y_{q\ell}=1\mid\mathcal H_{q\ell})
=\log 4+\eta_{q\ell}
\tag{L2015.1a}
$$

로 둔다. 즉 Bernoulli cloglog 구현에는 day 단위의 exposure offset $\log 4$가
들어간다. 모든 구간이 4일이라 intercept에 흡수될 수 있어도 계약에서는 이를
명시한다.

공통 비교 입력은 session 1 prevalent 돌기를 제외하고 first catalog가 session
2–5인 돌기의 first-catalog 이후 현재-catalogued 구간으로 제한한다. prior
비검출과 검출 calibration 부재 때문에 first catalog는 biological birth의
구간경계가 아니며 true age의 하한·상한도 주지 않는다. 그 위에서

$$
a^{\rm cat}_{q\ell}=4(\ell-f_q)\ {\rm day},
\qquad
s_{q\ell}=\frac{\lambda_{1,q\ell}-\lambda_{2,q\ell}}
{\lambda_{1,q\ell}+\lambda_{2,q\ell}}
$$

를 두고 다음 세 working predictor를 비교할 수 있다.

$$
\begin{aligned}
V_0:\quad \eta_{q\ell}
&=\beta_0+u_c+v_{cd},\\
V_1:\quad \eta_{q\ell}
&=\beta_0+\sum_k\gamma_k B_k(a^{\rm cat}_{q\ell})+u_c+v_{cd},\\
V_2:\quad \eta_{q\ell}
&=\beta_0+\sum_k\gamma_k B_k(a^{\rm cat}_{q\ell})
+\beta_I\widetilde{\log I}_{q\ell}
+\beta_S\widetilde s_{q\ell}
+\beta_D\widetilde{\log D}_{q\ell}
+\beta_Z\widetilde z_{q\ell}+u_c+v_{cd}.
\end{aligned}
\tag{L2015.2}
$$

$u_c$와 $v_{cd}$는 training fold에서만 분포를 추정한다. heldout cell에서는 새
$u_c$뿐 아니라 그 cell에 속한 모든 새 $v_{cd}$를 계층분포에 대해 **공동 적분**해야
한다. tilde 변환과 $B_k$도 training에서만 고정한다. $a^{\rm cat}$는 first
catalog 뒤 경과시간이지 true spine age가 아니다. $V_2$는 현재 morphology가 다음
방문 재카탈로그를 예측하는지 묻고, $\beta_Z\widetilde z$는 생물학적 형태효과가
아니라 방향·검출 nuisance 조정항이다. 따라서 $V_2$는
$dm/dS=b_m$ 또는 전이 jump kernel $K_{rs}$를 식별하지 않는다.

세 식의 baseline 뒤 first-catalog 공통 입력은 2,723구간, 다음 방문
비카탈로그 1,459건이고
`comparison_rowset_sha256`은
`127bf184fe88cd04c727f39c719e7ee0931c6bd1264338bb1b9b30dfff38fcd4`다.
이 hash는 입력 후보를 잠글 뿐 split, basis, penalty와 판정 문턱을 아직 잠그지
않으므로 fit을 허가하는 사전등록 계약은 아니다.

## 5. 모델별 판정

| 대상 | 판정 | 허용 범위 | 닫힌 주장 |
|---|---|---|---|
| biological M0 constant contact CTMC | `NOT_IDENTIFIABLE` | 없음 | 검출오차와 biological disappearance 분리, $0\to1$ birth intensity |
| biological M1 age-only semi-Markov | `NOT_IDENTIFIABLE` | 없음 | prevalent true age, first-catalog 돌기의 biological birth time, continuous age hazard |
| biological M2 age+mark PDMP | `NOT_IDENTIFIABLE` | 없음 | mark drift $b_m$, 물리단위 효과, $K_{rs}$ |
| $V_0$ catalogued-protrusion 재관측 | `INPUT_ELIGIBLE` | 같은 표본·절차의 다음 방문 재카탈로그 cell-heldout 기술예측 | mature-spine endpoint·animal 일반화·synaptic-contact hazard |
| $V_1$ first-catalog elapsed time | `INPUT_ELIGIBLE` | baseline 뒤 first-catalog subset의 경과시간 예측 | biological birth·true age 효과 |
| $V_2$ current morphology + orientation nuisance | `INPUT_ELIGIBLE` | pre-next-visit 형태 association과 z-offset nuisance 조정 | z를 형태로 해석·conducting state·continuous PDMP |

주요 정지 코드는 `COMMON_SUPPORT_NOT_ESTABLISHED`,
`NI_DETECTION_TURNOVER_CONFOUNDING`, `NI_BIRTH_DENOMINATOR`,
`NI_LEFT_TRUNCATED_AGE`, `NI_ANIMAL_HELDOUT_FRAILTY`,
`NI_MARK_SCALE_ERROR`, `NI_FILOPODIA_SEPARATION`, `NI_CONDUCTING_STATE`,
`NI_BIPARENT_CONTACT`다.
8개 cell이 논문의 6마우스에 어떻게 대응하는지 CSV에는 없으므로 cell-heldout은
animal-heldout의 대체 증거가 아니다.
`ASCERTAINMENT_ADULT_MALE_GFP_M_AUDITORY_L5_APICAL_TUFT`,
`ASCERTAINMENT_LATERAL_ORIENTATION_SELECTION`,
`FILOPODIA_NOT_SEPARATED_FROM_SPINES`는 적용범위를 표시하며, 결과를 다른 성별·
연령·세포구획이나 일반 성숙 spine으로 외삽하지 못하게 한다.

## 6. 실행 영수증

- [source lock](../6_뇌/국소회로_상태다양체_흐름_대응/repro/loewenstein_2015_spine_source_lock.tsv)
- [읽기 전용 preflight auditor](../6_뇌/국소회로_상태다양체_흐름_대응/repro/audit_loewenstein_2015_spine_preflight.ps1)
- [기계 판독 receipt](../../artifacts/brain/ce_npf_loewenstein_spine_preflight_v1/receipt.json)

| 대상 | SHA-256 |
|---|---|
| source-lock manifest | `8209a09886b9322a02308f1dceff8d3805462c715135f79e28e1ab1e166b0630` |
| auditor | `a1b68ad6820055ba305058d7b5f646626df2842dd628a2401a95f785b4f600cc` |
| receipt | `2ce71a85cd25c5da3d26c74f14aeb6c2d23daafa7fe3485b77567ddce619f517` |

재실행에서 PowerShell parse error는 0개였고 live bytes는
`PARTIAL_MODEL_ELIGIBILITY`, 8,699행, 7,311구간과 동일 rowset hash를 재현했다.
manifest에 의미 없는 열 하나만 더한 음성검사도 exit 1,
`STOP_SOURCE_LOCK_MISMATCH`, `manifest_definition_pass=false`로 닫혔고 원자료를
다른 bytes로 바꾼 음성검사는 exit 1, `source_content_pass=false`로 닫혔다.

## 7. 결론과 다음 허용 행동

1. **원래 질문에 답했는가:** 일부만 답했다. 실제 생물학적 종단 행자료에 맞춘
   식 (L2015.1)–(L2015.2)와 정확한 주장 상한을 세웠지만 Riemann 계량이나
   기능적 접힘을 검정하지 않았다.
2. **무엇이 반증되었는가:** 이 공개 CSV만으로 full birth–death contact CTMC,
   true-age semi-Markov, continuous age+mark PDMP와 animal-heldout 일반화를
   식별할 수 있다는 명제는 기각된다. 생물학적 기전 자체가 기각된 것은 아니다.
3. **무엇이 살아 있는가:** 같은 관측의 공통 rowset에서 $V_0$–$V_2$가 다음 방문
   저자-catalogued 측방 돌기의 재카탈로그를 얼마나 예측하는지 비교하는 제한된
   cell-heldout 질문은 살아 있다. 이 범위는 약 6개월령 성체 수컷 GFP-M 마우스의
   청각피질 L5 pyramidal apical tuft와 해당 영상·선별·추적절차 안이다.
4. **다음 허용 행동:** 먼저 분할·basis·penalty·공통 missingness·주 지표를 잠근
   비교 계약을 작성한다. 그 계약 뒤에만 $V_0$–$V_2$를 실행한다. 생물학적
   CTMC/PDMP 승격에는 cell↔animal crosswalk, branch exposure, 실제 timestamp,
   visit·detection·censor QC, initial-age law, filopodia 분리가 필요하다. conducting
   전이는 양 parent identity와 반복 same-contact 기능 assay가 추가로 필요하다.
   이와 별개로 raw 재배포·release에는 명시적 재사용 라이선스와 versioned archive가
   필요하다.
