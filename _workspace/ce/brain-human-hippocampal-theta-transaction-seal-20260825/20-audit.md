# BA-OBS-HPC3 pre-implementation status audit

Status: COMPLETE

Gate: BLOCKED

Final raw authorization is blocked after `impl-engineer` revision 2/2. The
pre-implementation PASS below was superseded by stable-code adversarial audit. The
authoritative raw validator accepts nonnumeric endpoint/analysis values and does not
recompute analysis from the committed file summaries; the QC validator also applies a
single-channel exclusion-reason bound to p20's three-channel joint QC. No raw request,
QC count, or endpoint occurred. Resume only in a transaction-validator successor that
fixes these two schema defects without changing the frozen science.

Scope: stable light-successor contract and lane snapshot only. No implementation,
network object, `.eeg` voltage, QC count, endpoint, or Nature Source Data was opened.
This PASS authorizes implementation preflight, not raw execution.

## Decision

HPC2 ended `BLOCKED_IMPLEMENTATION_TRANSACTION / NO_RAW_ATTEMPT / NO_ENDPOINT` after
its implementation revision budget reached 2/2. HPC3 changes only transaction
authority: a valid atomic `raw_result.json` is the sole successful endpoint commit,
`qc_result.json` is the sole aperture-stop commit, and progress is a non-authoritative
journal. Resolver precedence prevents a post-result journal failure from relabeling or
deleting an already committed endpoint.

No scientific choice changes. The 18 objects, contacts, p20 joint QC order, thresholds,
MIN20 aperture, time masks, reference roles, participant contrasts, bootstrap
seed/draws, LOO, paired sensitivity, and status lattice remain frozen. The inherited
source lock and author-code receipt bytes independently match their declared SHA-256
values:

- `66cac4202971cabb0838b3ddb93710c160c88325133411f58c8595c89e7c5810`;
- `20008069771a37a7e7669e996d0bb799cabed1ad09e0e010c6c1f0ec33b93496`.

The successor remains outcome-blind: HPC2 produced no raw attempt, clean count, or
endpoint. The selected route forbids ambiguous catch semantics, retry, threshold
tuning, cohort reduction, and endpoint reopening. Exactly one `ATTEMPT1` remains.

## Implementation handoff

Before raw authorization, the stable implementation must prove with no-network mocks:

1. endpoint construction, aggregation, and serialization fail terminally before any
   endpoint commit;
2. result-first commit followed by injected progress-finalization failure still resolves
   as `RAW_COMPLETE` and is never rewritten as `IMPLEMENTATION_STOP`;
3. any prior receipt rejects before loader construction;
4. inherited byte seals, full-object reader, QC, and estimator fixtures remain exact.

No P0/P1 finding is open at this pre-implementation gate. A new stable-snapshot audit is
required before the sole real raw attempt.
