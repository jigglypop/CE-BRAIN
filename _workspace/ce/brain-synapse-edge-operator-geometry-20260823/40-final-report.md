# BA-SRM4 최종 보고서 — 시냅스 간선 연산자 기하와 데이터 기반 후보식

Status: COMPLETE

Date: 2026-08-23

Final verdict: `DISCOVERY_CANDIDATE_FROZEN / VALIDATION_CONFIRMATION_SEALED`

## 결론

이번 판본은 두 가지를 분리해 확정했다.

첫째, 시냅스를 과거 자극·스파이크·전압·상태에 반응하는 함수로 두면 자연스러운 표현 공간은
무한차원 Hilbert history space가 될 수 있다. 그러나 16개 future-response output을 가진 현재
실험이 식별하는 것은 전체 공간이 아니라

$$
\mathscr H_E/\ker DM_x
$$

라는 유한 관측 몫뿐이다. 전체 무한차원 SPD metric, 전체 상태 복원, 무한 rank 관측은 수학적
no-go와 완전 반례 때문에 금지된다.

둘째, 실제 Allen Synaptic Physiology discovery data를 clamp mode와 단위를 바로잡아 다시 읽은
결과, IC→IC에서 안정적으로 남은 관측 방향은 현재 tolerance에서 ex와 in 모두 hard rank 4였다.
이는 뇌나 시냅스의 "참 차원이 4"라는 뜻이 아니다. 현재 target·noise·protocol·fitted chart가
구별한 finite quotient의 국소 방향 수가 4라는 뜻이다.

## 현재 위치

| 단계 | 상태 | 이번 판본의 의미 |
|---|---|---|
| 선행 BA-SRM3 | `INVALIDATED_CLAMP_UNIT_CONTRACT`로 종료 | IC/VC 단위 혼합 때문에 과거 rank/model 수치는 인용 금지 |
| source/schema | 완료 | observed response와 latent release/depletion을 분리 |
| 수학 정리·반례 | 완료 | infinite history 가능성과 finite quotient no-go 동시 확정 |
| group split·quarantine | V2 완료 | LIMS slice-specimen 원자성, 과거접촉 outcome만 discovery로 격리 |
| discovery equation | V2 stability core 동결 | `[경험식][미완성]` 후보 하나 |
| validation/development | `SEALED / NOT READ` | 후보 우세·재현성 주장 불가 |
| confirmation/test | `SEALED / NOT READ` | 예측 승격·생물학 법칙 주장 불가 |

따라서 우리는 “식을 만들 수 있는가?”에는 `가능`까지 왔고, “그 식이 새 데이터에서도 맞는가?”에는
아직 답하지 않았다.

## 간선 정보와 차원의 정확한 조건

[조건부 정리] noise-whitened sensitivity를

$$
z_{e\alpha}=R^{-1/2}\partial_{\xi_{e\alpha}}M
$$

라고 하면, 새 간선 속성 $\xi_{e\alpha}$가 hard observable dimension을 하나 늘리는 필요충분
조건은

$$
z_{e\alpha}
\notin
\overline{\operatorname{span}}\{z_{f\beta}:(f,\beta)\ne(e,\alpha)\}
$$

이다. 간선 수, feature 열 수, basis coefficient 수가 늘었다는 사실만으로 차원이 증가하지 않는다.

반드시 세 값을 따로 보고한다.

1. raw representation dimension: 기록하거나 전개한 coefficient 수;
2. hard observable rank: $\operatorname{rank}(R^{-1/2}DM_x)$;
3. noise-aware effective dimension:

$$
d_{\rm eff}(\lambda)
=\operatorname{Tr}[\widetilde G(\widetilde G+\lambda I)^{-1}]
=\sum_k\frac{\mu_k}{\mu_k+\lambda}.
$$

$d_{\rm eff}$는 fixed dimensionless reference와 trace-class 조건이 있을 때만 정의된다.

## 실제 데이터와 split

pinned medium DB SHA-256은
`dbf19786f9e0d0d73c26351dc29d69ef8c10a2e67e32e19ac73034a5624d48c5`다.

Allen source는 `slice.ext_id`를 unique DB slice-row ID, `slice.lims_specimen_name`을 LIMS
"slice specimen" 이름으로 정의한다. 후자는 donor/animal ID가 아니다. 같은 label의 반복
acquisition이 split을 가로지르지 않도록

```text
g = slice.lims_specimen_name
```

을 보수적인 slice-specimen equivalence class로 사용했다. donor/animal identity는
`UNRESOLVED_IDENTITY_KEY`이며 donor-held-out 주장은 금지된다.

4,259개 group은 discovery 2,308 / 과거오염 discovery 414 / validation 772 /
confirmation 765로 나뉘었다. outcome을 읽은 1,383개 sequence는 전부 과거접촉 414개 group
안에만 있다. validation/confirmation outcome은 한 행도 읽지 않았다.

mode-aware support는 다음과 같다.

| stratum | sequences | groups | fit status |
|---|---:|---:|---|
| ex pre-IC → post-IC | 713 | 168 | discovery candidate |
| in pre-IC → post-IC | 641 | 185 | discovery candidate |
| ex pre-VC → post-IC | 16 | 6 | abstain |
| in pre-VC → post-IC | 13 | 4 | abstain |

VC command를 전류로 바꾸어 IC와 합치지 않았다. pre-IC는 $I/I_0$, pre-VC는 $V/V_0$이고
빈 typed channel은 `NaN`으로 유지했다.

## 데이터에서 나온 frozen 후보식

future target은 pulse 8--11 각각의 amplitude, latency, rise, decay, 총 16 coordinates다.
history input은 pulse 0--7에만 의존한다. 모든 별표 좌표는 물리적 무차원화 뒤 discovery-fold
robust scale로 표준화한 값이다.

[경험식][미완성] 흥분성 IC→IC stability core:

$$
\widehat{\mathbf y}_{\mathrm{ex}}^*
=\mathbf b_{\mathrm{ex}}
+\mathbf B_{a,\mathrm{ex}}\bar a^*
+\mathbf B_{\ell,\mathrm{ex}}\bar\ell^*
+\mathbf B_{r,\mathrm{ex}}\bar r^*
+\mathbf B_{d,\mathrm{ex}}\bar d^*
+\mathbf B_{50,\mathrm{ex}}\Phi_{50}^*.
$$

[경험식][미완성] 억제성 IC→IC stability core:

$$
\widehat{\mathbf y}_{\mathrm{in}}^*
=\mathbf b_{\mathrm{in}}
+\mathbf B_{a,\mathrm{in}}\bar a^*
+\mathbf B_{\ell,\mathrm{in}}\bar\ell^*
+\mathbf B_{r,\mathrm{in}}\bar r^*
+\mathbf B_{d,\mathrm{in}}\bar d^*.
$$

$\bar a,\bar\ell,\bar r,\bar d$는 과거 8 pulses의 response amplitude, latency, rise,
decay 평균이다. ex의 causal trace는

$$
\Phi_{50}
=\sum_{k=0}^{7}\frac{a_k}{V_0}
\exp\!\left[-\frac{t_8-t_k}{50\,\mathrm{ms}}\right]
$$

이다. coefficient 16-vectors와 모든 normalization constant는
`artifacts/discovery-equation.v2.json`에 있다.

5 outer folds의 training selection에서 ex의 과거평균응답·latency는 5/5, decay·50 ms trace는
4/5, rise는 3/5에 남았다. in의 과거평균응답·latency·rise·decay는 모두 5/5였다. 최소 3/5
rule 밖의 noise, slope, spike-count, frequency, interaction은 frozen 후보에서 제거했다.

## 차원 결과

| quantity | ex IC→IC | in IC→IC |
|---|---:|---:|
| frozen stable terms | 5 | 4 |
| pointwise hard rank | 4 | 4 |
| $d_{\rm eff}(1)$ median | 3.2945 | 3.5620 |
| groups | 168 | 185 |

ex의 50 ms trace는 conditional hard-rank increment가 0/713이다. 즉 이 feature가 prediction
식에 들어가도 현재 output sensitivity span에 새 독립 방향을 추가하지 않았다. 이 사례가 바로
“간선 속성 수 = 차원”이 아닌 이유다. 다만 coefficient가 정확히 0이라는 뜻도, 다른 protocol과
측정에서 항상 불필요하다는 뜻도 아니다.

작은 $\lambda$에서 ex $d_{\rm eff}(10^{-4})=4.0279$가 hard rank 4보다 조금 큰 것은
relative rank cutoff 아래의 작은 mode를 연속적으로 세기 때문이다. 두 값을 같은 차원으로
부르지 않는다.

## 증거 지위

```text
D  pinned DB/schema/unit/split receipt                     PASS
I  discovery-only sparse equation inference               PASS
P  untouched validation prediction                        NOT RUN
C  mechanistic/raw-RBF/time-shuffle/clamp-swap controls   NOT RUN
B  LIMS slice-specimen boundary                            FIXED; donor unresolved
T  [경험식][미완성]                                        ACTIVE CEILING
```

discovery nested-OOF selector는 constant보다 낮은 group-mean standardized MSE를 보였지만,
이는 후보 생성 진단이다. source-mechanistic baseline, linear, raw-RBF 및 adverse controls를
validation에서 아직 비교하지 않았으므로 Route A의 승리라고 부를 수 없다.

## 사용자 아이디어를 식으로 바꾸는 규칙

아이디어를 주면 다음 순서로 처리할 수 있다.

1. 아이디어를 상태변수/history functional $\Phi_j$로 번역한다.
2. source unit과 무차원화 기준을 고정한다.
3. 미래 누출 없는 causal order를 확인한다.
4. 기존 sensitivity span 밖인지 조건부 rank increment로 검사한다.
5. 아이디어와 독립적인 falsifier를 함께 고정한다.
6. discovery에서 후보식을 만들고, 새 validation에서 한 번 비교한다.

필드가 없거나 다른 상태와 식별 불가능하면 `UNIDENTIFIABLE_IDEA`; 출처·기전과 충돌하면
`CONTRADICTED`; 기존 basis가 이미 포함하면 `ALREADY_CONTAINED`; 나머지만 `PLAUSIBLE` 후보식으로
만든다. 데이터 적합도가 높아도 independent confirmation 전에는 `[경험식]`이다.

## 출처

- [Allen `aisynphys` dataset structure](https://github.com/AllenInstitute/aisynphys/blob/current-release/doc/source/dataset_structure.rst)
- [Allen `aisynphys` Slice schema source](https://github.com/AllenInstitute/aisynphys/blob/current-release/aisynphys/database/schema/slice.py)
- [Allen `aisynphys` schema API](https://github.com/AllenInstitute/aisynphys/blob/current-release/doc/source/api_schema.rst)
- [Tsodyks & Markram 1997](https://pubmed.ncbi.nlm.nih.gov/9012851/)
- [Zucker & Regehr 2002](https://pubmed.ncbi.nlm.nih.gov/11826273/)

## 다음 unlock

다음 단계는 frozen V2 식을 바꾸지 않고 validation 772개 LIMS slice-specimen groups 중 사전
정의된 eligible support만 한 번 여는 것이다. constant, linear, source-mechanistic baseline,
raw-RBF를 각각 $\Delta\mathrm{ELPD}>2SE$로 이기고 time shuffle·clamp swap에서 이점이 사라져야
confirmation을 열 수 있다.

실패하면 식을 고쳐 같은 test를 반복하지 않는다. 현재 confirmation을 닫고 새 run-id와 split
salt로 재시작한다.

## 폐기 판본

`artifacts/split-groups.jsonl`, `discovery-dataset.npz`,
`discovery-dataset-receipt.json`, `discovery-equation.json`은 모두
`SUPERSEDED / DO NOT CITE`다. 활성 판본은 `.v2` artifact뿐이다.
