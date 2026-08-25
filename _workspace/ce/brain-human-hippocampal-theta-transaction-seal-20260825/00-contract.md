# BA-OBS-HPC3 research contract — authoritative transaction seal

Status: COMPLETE

PREDECESSOR: `_workspace/ce/brain-human-hippocampal-theta-author-qc-reanalysis-20260825`

Mode: light implementation successor. No scientific, cohort, source, measurement,
threshold, endpoint, statistical, or status-lattice choice changes.

## Inherited frozen science

HPC3 inherits verbatim from HPC2:

- OpenNeuro `ds006065` v1.0.0, release commit
  `14fdb3d852dcaba48a65d1185d3a6dfa2f83dba4`;
- the exact 18-object source lock SHA-256
  `66cac4202971cabb0838b3ddb93710c160c88325133411f58c8595c89e7c5810`;
- the author-code static receipt SHA-256
  `20008069771a37a7e7669e996d0bb799cabed1ad09e0e010c6c1f0ec33b93496`;
- author-order artifact-before-baseline QC, `(k,z,a)=(5,5,500)`, `MIN20`, first-999
  author grid, p17 low-pass, clinical and local-bipolar references;
- p20 joint clinical QC over ordered `D9,C1,C'1`, clinical endpoint `D9`, local
  endpoint/QC `D9-D10`;
- early/late/prestim windows, participant-equal TS(4)-PB(5) contrasts, PCG64 seed
  20260825 with 65,536 shared-participant bootstrap draws, seven LOO, p17/p19 paired
  sensitivity, and the HPC2 Section 6 status lattice.

HPC2 ended `BLOCKED_IMPLEMENTATION_TRANSACTION / NO_RAW_ATTEMPT / NO_ENDPOINT`.
Its clean counts and biological endpoint remain unknown. Nothing in this successor is
chosen from voltage, QC-count, or outcome information.

## Sole delta: transaction authority

The endpoint-bearing `artifacts/raw_result.json` is the sole authoritative successful
commit. It is assembled and JSON-serialized entirely in memory only after all 18 files
pass source identity and both `MIN20` apertures, then atomically replaced into place.
Once that file exists with its frozen receipt fields, the transaction state is
`RAW_COMPLETE`, even if the non-authoritative progress journal cannot be finalized.

`artifacts/qc_result.json` is the sole authoritative `QC_STOP_MIN20` commit and contains
only file identities, full-object integrity, clean counts, and exclusion reasons. It
contains no waveform, P2P, delta, bootstrap, LOO, status, or endpoint field.

Before either authoritative commit, `artifacts/raw_progress.json` is a resumeless,
non-authoritative journal. Source/network/decode failures terminalize it as
`SOURCE_STOP`; all preprocessing, invariant, endpoint-construction, serialization, and
aggregation failures terminalize it as `IMPLEMENTATION_STOP`. Those failure paths may
retain only already committed integrity/QC receipts and must have no authoritative
result file.

After `raw_result.json` is atomically committed, a progress-finalization failure must
never overwrite or relabel the authoritative result. The resolver precedence is:

1. valid `raw_result.json` -> `RAW_COMPLETE`;
2. else valid `qc_result.json` -> `QC_STOP_MIN20`;
3. else terminal `raw_progress.json` -> its source/implementation stop;
4. else `RAW_IN_PROGRESS` is an incomplete one-shot with no retry.

Every entry point rejects any pre-existing progress, QC, or result receipt. Exactly one
audited `ATTEMPT1` is available. No infrastructure, QC, processing, or journal failure
creates a retry budget.

## Required preflight tests

Without network or real voltage, tests must prove:

- inherited lock/static byte seals and version-pinned full-object loader remain exact;
- endpoint construction and aggregation exceptions produce terminal endpoint-free
  `IMPLEMENTATION_STOP` receipts;
- JSON serialization fails before result commit;
- an injected progress-finalization failure after atomic result commit leaves the
  result authoritative and is resolved as `RAW_COMPLETE`, never `IMPLEMENTATION_STOP`;
- prior receipts reject before loader/network construction;
- all inherited estimator and QC fixtures continue to pass.

## Falsifiers and claim ceiling

Any P0/P1 in the stable implementation audit blocks raw. Any raw source mismatch,
processing failure, or aperture failure ends the sole attempt under the authority rules
above. A successful endpoint remains only a same-public-data reanalysis of seven
epilepsy-surgery participants under direct electrical intervention. It is not an
independent confirmation, randomized population estimate, healthy generalization,
memory result, consciousness result, anatomical metric, or AGI evidence.
