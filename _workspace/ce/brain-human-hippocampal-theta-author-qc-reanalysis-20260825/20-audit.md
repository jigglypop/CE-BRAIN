# BA-OBS-HPC2 status audit

Status: COMPLETE

Scope: stable light-successor audit of the contract, inherited source identity,
author-code static receipt, completed mathematics/routes lanes, and predecessor
terminal records. No raw voltage, network object, Nature Source Data, or
endpoint result was opened. This audit owns no implementation authorization
beyond the preflight conditions stated below.

## Final gate decision

Gate: BLOCKED

Final implementation authorization is blocked after `impl-engineer` revision 2/2.
The earlier stable-snapshot review authorized implementation preflight only; it did
not authorize raw access. The final implementation audit retained one P1 transaction
defect: endpoint-construction failures can leave `raw_progress.json` at
`RAW_IN_PROGRESS`, while a failure after result-first commit can be mislabeled as an
endpoint-free implementation stop. No `.eeg` request, voltage read, QC result, or
endpoint result occurred. A light successor may inherit the scientific contract and
source lock, but this implementation must not execute.

## Preflight decision retained for provenance

The successor is a legitimate source-defined author-order QC successor, not an
outcome-count tuning run. It changes one prespecified measurement transaction:
the archived artifact-before-baseline order plus an explicit `MIN20` aperture,
with QC counts sealed separately from the endpoint. It does not change cohort,
contacts, windows, reference roles, bootstrap seed, or endpoint after seeing an
outcome. The predecessor remains terminal
`STOP_MEASUREMENT_APERTURE / NO_ENDPOINT / NO_RETRY_IN_THIS_VERSION` and supplies
no clean-count estimate from which a favorable threshold could be selected.

## Findings

No open P0 or P1 finding remains in the stable snapshot.

### Source-defined QC and defect handling — PASS

`00-contract.md:PREDECESSOR_EVIDENCE`, sections 3–4, and
`artifacts/author-code-static-receipt.md:Identity, Line-semantic audit` bind the
public archive MD5 and all three source-file SHA-256 values. The receipt records
the four-argument QC signature, artifact tests before baseline subtraction, the
normal `(5,5,500)` calls, the p17/p19 omitted-kurtosis signature defect, and the
p20 ordered selection. The p17/p19 defect is not silently repaired: the contract
freezes `(k,z,a)=(5,5,500)` as an explicit measurement axiom and says this is
not literal archived-script execution. Any hash or semantic mismatch must stop
as `AUTHOR_QC_CALL_AMBIGUITY` before raw access.

The author-code order is therefore reproducible as a declared interpretation:
artifact decision precedes baseline subtraction. This is distinct from claiming
byte-for-byte MATLAB/FieldTrip parity.

### Time masks and measurement order — PASS

`00-contract.md:4.1` freezes the author-order time grid and preprocessing
sequence, including the first-999-sample input, latency `50..648`, baseline
`225..244`, early `257..274`, late `275..374`, and prestimulus `100..199`
masks. `11-math.md:Recomputed grid and dimensional checks` independently agrees
on counts, disjoint early/late windows, units, and the normalized-pulse
convention. `11-math.md:Measurement order and QC aperture` confirms why a
baseline-first implementation is a different aperture.

### p20 joint QC and endpoint — PASS

`00-contract.md:4.2` and `artifacts/author-code-static-receipt.md:Line-semantic
audit` jointly freeze clinical QC over `D9,C1,C'1` while retaining the first
ordered contact `D9` as the sole clinical endpoint. Local bipolar QC/endpoint is
the frozen `D9-D10` trace. The p20 channel union is explicit, and the
math-lane synthetic check records that a defect confined to a non-endpoint
channel rejects the trial; D9-only QC is not an allowed substitute.

### Aperture, transaction, and one-attempt budget — PASS

`00-contract.md:3 DATA_SPLIT`, `4.3 Aperture`, `5 OBSERVABLES`, and
`7 FALSIFIER` separate immediate non-voltage source/QC receipts from the
endpoint receipt. Every one of 18 files must pass both clinical and local-bipolar
references with at least 20 clean trials; a single failure yields
`QC_STOP_MIN20`, deletes the endpoint, and forbids cohort reduction or rerun.
The contract allows exactly one audited `ATTEMPT1`; infrastructure or QC failure
does not create a retry budget. This is consistent with predecessor
`40-final-report.md`, `20-audit.md`, `30-implementation.md`, and
`31-validation.md`, which record one completed raw object, no endpoint, and no
retry in that version.

Before raw access, implementation must perform and serialize a new header-only
source lock that includes the additional p20 QC indices (`D9,C1,C'1`) and the
local endpoint/QC index (`D9-D10`), plus units/scaling, full channel order,
annex SHA/size, S3 version/ETag, and canonical lock hash. The implementation
must also pass a no-voltage synthetic fixture covering author-grid masks,
artifact-before-baseline, the p20 channel union, and a transaction test proving
that QC-count/source-integrity receipts can survive a stop while no endpoint
summary is committed. These are mandatory preflight conditions, not permission
to inspect real endpoint data early.

### Estimand and status gates — PASS

`00-contract.md:5–6` and `12-routes.md:R1` keep the participant as the effective
unit, use P2P of the clean-trial mean for the primary late endpoint, and retain
the clinical primary plus local-bipolar robustness reference. The robust parent
requires both late participant-level lower bounds to be positive, clinical
paired sensitivity positive, prestimulus lower bound nonpositive, and all
clinical late LOO values positive. A local point/interval failure is not hidden;
it routes to sensitivity/uncertainty, while opposite published-model and
participant-equal directions route to `ESTIMAND_DISCORDANT`. R2/R3 are not
pooled independent evidence, and R4 is prohibited without a new successor.

### Finite-sample limitation and claim ceiling — PASS

`11-math.md:Findings` records the finite-sample geometry of the trial-axis
`z=5` rule: with 20 trials, one isolated extreme cannot exceed the threshold
under the stated maximum, so this rule must not be described as a guaranteed
outlier detector. The contract preserves this limitation rather than tuning the
threshold. `00-contract.md:8 CLAIM_CEILING` limits any eventual result to seven
epilepsy-surgery participants, real human iEEG, direct intervention, and a
same-public-data author-order QC reanalysis; it excludes independent
confirmation, randomized population causality, healthy generalization, memory,
anatomical metrics, consciousness, and AGI claims.

## Implementation handoff conditions

Gate PASS authorizes the implementation preflight only. The implementation
owner must, before any `.eeg` request or endpoint-visible artifact:

1. freeze and canonically hash the expanded 18-object source lock, including
   the p20 extra QC channels and all contact/unit/version fields;
2. run the no-voltage synthetic/transaction fixture described above; and
3. preserve the one-attempt, QC-count/endpoint-atomic seal and the exact
   contract masks/axiom/status rules.

Failure of any preflight condition is `IMPLEMENTATION_INVALID` or
`STOP_SOURCE_IDENTITY`, with no endpoint and no raw retry. Passing preflight does
not promote the result beyond the claim ceiling or make the analysis an
outcome-blind confirmation.

## Audit disposition

The stable snapshot contains no P0/P1 revision target. The successor may proceed
to implementation preflight under the frozen contract. No biological support
claim is authorized until all QC transactions pass and the endpoint receipt is
atomically committed.
