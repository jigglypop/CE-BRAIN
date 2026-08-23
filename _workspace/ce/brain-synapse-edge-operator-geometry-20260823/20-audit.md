# BA-SRM4 status audit — revised stable snapshot

Status: COMPLETE

Gate: PASS

Audit scope: revised `00-contract.md`, `10-sources.md`, and `12-routes.md`, with the stable `11-math.md`. No validation or confirmation outcome, residual, score, rank spectrum, or model-fit artifact was opened.

## 판정

P0 결함은 없다. 이번 grouping correction은 validation 이전의 schema-only 정정으로 일관된다. `g = slice.lims_specimen_name`은 LIMS의 slice-specimen equivalence class이며, `slice.ext_id`는 row identity일 뿐이다. donor/animal identity는 `UNRESOLVED_IDENTITY_KEY`로 남고 donor-held-out 주장은 금지된다.

Gate PASS는 수학적·생물학적 주장의 범위와 감사 규율에 대한 판정이다. V2 split/equation receipt가 동결된 현재는 discovery-only fit까지 허용되며, validation/confirmation은 여전히 닫혀 있다.

## Claim 감사

| Claim | 근거 | 판정 |
|---|---|---|
| Predecessor inheritance | `00-contract.md:29-37` | A6의 SPD/PSD 조건, BA-SRM2 quotient no-go, BA-SRM3 `INVALIDATED_CLAMP_UNIT_CONTRACT`와 hash를 계승한다. BA-SRM3 수치는 생물학적 반증으로 재사용하지 않는다. PASS. |
| Group identity | `00-contract.md:110-132`; `10-sources.md:20,29,103-116,127-132`; `12-routes.md:9-12,80,107-111` | 4,276 rows, 4,259 labels, 16 duplicated labels covering 33 rows를 반영한다. 14 duplicate-label groups가 ext_id hash buckets를 가로지를 수 있으므로 ext_id 기반 split은 금지하고 label equivalence class 전체를 함께 둔다. donor/animal은 unresolved. PASS, V2 receipt 필수. |
| Typed IC/VC units | `00-contract.md:72-79`; `10-sources.md:43-57`; `11-math.md:199-216` | IC는 $I/I_0$, VC는 $V/V_0$ 및 별도 type/scaler다. postsynaptic source unit과 structural missingness를 보존한다. 혼합 시 `STOP_DIMENSIONLESS`/invalidated. PASS. |
| Split sealing | `00-contract.md:102-141`; `10-sources.md:7-8,117-132`; `12-routes.md:9-13,103-111` | grouping correction은 pre-validation이다. discovery에서만 후보식/전처리를 허용하고 validation은 하나를 고정하며 confirmation은 한 번만 연다. 현재 outcome은 미접촉. PASS. |
| Observed vs latent biology | `10-sources.md:60-82,131-143`; `12-routes.md:52-68` | pulse/dynamics summaries는 observed proxy이고 release probability/resource state는 latent다. Route C는 source-locked template이지 fitted law나 causal intervention 결과가 아니다. PASS. |
| Finite-output quotient no-go | `11-math.md:57-105`; `00-contract.md:174-201`; `12-routes.md:90-97` | $\mathcal G_x=DM_x^*R^{-1}DM_x$의 PSD·finite-rank·kernel과 $\mathscr H_E/\ker DM_x$ quotient가 유지된다. $M(x)=x_1$ on $\ell^2$가 전체 SPD/복원의 완전 반례다. 전체 SPD, 전체 history 복원, 관측된 infinite rank는 활성 주장으로 남아 있지 않다. PASS. |
| Edge rank increment | `11-math.md:108-134`; `00-contract.md:181-187` | whitened sensitivity가 기존 closed span 밖일 때에만 hard rank가 1 증가한다. raw edge count를 observable dimension으로 동일시하지 않는다. PASS. |
| Effective dimension | `11-math.md:136-188`; `00-contract.md:188-206`; `12-routes.md:92-94` | positive trace-class reference operator, fixed chart/scale가 조건이다. trace-class가 없으면 `UNDEFINED_EFFECTIVE_DIMENSION`; $\widetilde G=I$ on $\ell^2$ 반례가 보존된다. PASS as a conditional definition; receipt 전 결과 보고 금지. |
| Dimensionless requirements | `00-contract.md:68-79,142-163,188-206`; `11-math.md:195-216` | typed source units, dimensionless time/kernel/log/exp arguments, whitening and $\lambda$ reference를 요구한다. PASS. |
| Route A/B/C falsifiers | `12-routes.md:15-68,74-97`; `00-contract.md:270-283` | sparse Volterra, FPCA/RKHS/RBF, source-verified mechanistic baseline의 controls와 time shuffle, clamp swap, missingness, raw-RBF, simple baselines가 유지된다. 어떤 route도 아직 승리하지 않았다. PASS. |
| Claim ceiling | `00-contract.md:13-24,303-312`; `10-sources.md:156-175`; `12-routes.md:90-111` | 최대 L3 slice-specimen-held-out candidate다. whole-brain, cognition, AGI, L4 causality, donor-held-out, infinite-dimensional SPD/recovery를 금지한다. PASS. |

## P1 조건과 구현 범위

1. V2 split receipt가 필요하다. receipt에는 `g=slice.lims_specimen_name`, all 16 duplicate-label groups, all 33 affected rows, the 14 cross-ext_id-bucket duplicate groups, frozen bucket assignment, missing/empty labels, and predecessor BA-SRM2/3 train-contact quarantine mapping을 포함해야 한다. label equivalence class 전체는 같은 split이어야 한다. 이 receipt 전에는 model fit을 시작하지 않는다.
2. `10-sources.md`의 pulses 8–11 × `{amplitude, latency, rise, decay}`는 predeclared target이며 complete same-mode support는 아직 `UNVERIFIED`다. support가 outcome 접촉 전에 고정되지 않으면 `BLOCKED_TARGET_DEFINITION`이다.
3. reference/whitening operator의 trace-class, basis, scale, and $\lambda$ grid receipt 전에는 $d_{\rm eff}$를 결과로 승격하지 않는다.

허용되는 구현은 schema-only identity inspection, typed IC/VC extraction, QC/missingness receipt, revised V2 group manifest/quarantine, 그리고 discovery partition 내부의 후보식 생성·nested-CV 준비까지다. validation/confirmation response·residual·score·rank-spectrum 접근, IC/VC 혼합, latent release/depletion의 observed 표기, 전체 SPD·무한 rank·전체 상태 복원·AGI 확장은 금지한다.

최종 판정: `Gate: PASS`; grouping correction은 coherent한 preregistered pre-validation revision이며, V2 split/equation receipt가 고정된 현재도 discovery-only다.

## P1 receipt-clearance — V2 discovery dataset

Read-only inspection of `artifacts/discovery-dataset-receipt.v2.json`,
`artifacts/split-groups.v2.jsonl`, and
`artifacts/prepare_discovery_dataset.py` clears the former grouping-receipt P1 for
discovery use:

- the split manifest has 4,276 slice rows and 4,259 unique
  `slice.lims_specimen_name` group IDs;
- no group is assigned to more than one split (`discovery=2308`,
  `discovery-contaminated=414`, `validation=772`, `confirmation=765`);
- all 414 predecessor-contact groups are `discovery-contaminated`, and the
  selected 1,383 sequences / 16,596 event rows are all predecessor-contacted;
- the selected source is exactly the frozen old eligible manifest, with its pinned
  SHA-256; no additional outcome source is admitted by the preparation code;
- typed columns remain separate: `pre_ic_command=A/I0`, `pre_vc_command=V/V0`,
  `post_ic_response=V/V0`, `post_vc_response=A/I0`, with no zero-fill before mode
  stratification;
- the receipt states `validation_outcomes_read=false`,
  `confirmation_outcomes_read=false`, and `waveform_blobs_read=false`. The
  preparation code also rejects validation/confirmation SQL and enforces
  predecessor quarantine. The focused test result is recorded as 7 passed.

Therefore discovery-only IC→IC model fitting may proceed, provided it consumes
only this frozen receipt/dataset and remains an empirical `[경험식]`/`[미완성]`
activity. It must not be described as validation, confirmation, donor-held-out,
causal, or general brain/AGI evidence.

VC must abstain from model fitting by default at this stage: the receipt has only
16 excitatory and 13 inhibitory pre-VC sequences, spanning 6 and 4
slice-specimen groups respectively. The 16-coordinate finite-target check passes
as a schema/data receipt, but this small VC group support is not enough to unlock
the planned model comparison. A separate preregistered minimum-support rule and
fresh discovery receipt would be required to enable VC; otherwise report VC as
unsupported/abstained and keep it out of fitted claims.

The remaining P1 gates are unchanged: complete target/support policy must remain
frozen, and the reference/whitening operator must receive its trace-class,
basis, scale, and λ-grid receipt before any $d_{\rm eff}$ result is reported.

## Post-implementation audit

The frozen implementation and both focused test files are coherent with the
receipt contract. The stated focused result is 7 passed for each focused test
file. The preparation code uses the LIMS slice-specimen group atomically, checks
the old eligible-manifest hash, keeps IC/VC channels typed, rejects validation or
confirmation SQL, and exposes VC strata only as `ABSTAIN_INSUFFICIENT_GROUPS`.
The equation discovery code consumes the V2 dataset/receipt hashes, uses 5 outer
and 4 inner group folds, retains only terms appearing in at least 3 of 5 outer
selections, and records the finite trace-class reference receipt. Its claim label
is `[경험식][미완성]`; it does not promote a route victory.

The full discovery-greedy candidate is explicitly recorded as “superseded by
stability core” inside `artifacts/discovery-equation.v2.json`. However,
`artifacts/discovery-equation.json` remains present as the V1 artifact, and the
canonical numbered documents do not yet contain a durable V1-superseded notice.
This is P1 documentation risk, not a Gate failure: before writing 30/31 or the
final report, mark V1 (`BA-SRM4-DISCOVERY-EQUATION-V1`) superseded by
`BA-SRM4-DISCOVERY-EQUATION-V2-STABILITY-CORE` and prohibit citing it. V1 and its
full-greedy terms must not be used as the selected equation or evidence.

Root may write `30-build-validation.md`, `31-validation.md`, and the final report
without opening validation/confirmation outcomes, provided those documents are
strictly implementation/discovery reports: they must cite only V2, retain the
VC abstention, label all fitted equations `[경험식][미완성]`, and state that no
validation or confirmation outcome exists. `31-validation.md` may document
schema, hash, split, test, leakage, unit, and discovery-receipt checks, but may
not report held-out validation scores or call discovery diagnostics validation
evidence. The final report must carry the same V1-superseded notice and the
finite-quotient/claim-ceiling limits.
