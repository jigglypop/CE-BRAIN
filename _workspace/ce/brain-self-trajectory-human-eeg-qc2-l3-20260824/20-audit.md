# BA-SELF2-L3 audit

Status: COMPLETE

Audit scope: the frozen `00-contract.md`, `10-sources.md`, `11-math.md`, and
`12-routes.md` only.  Snapshot hashes supplied to this audit are recorded in
`12-routes.md`: contract
`8eb85e4ce7218112c082b84e0f754ae3fa0afb1995374a9675c581164880517f`, sources
`54c318e3d42af474c253e97c2a9b56f83fe906959239b380c81365027defe55f`, math
`403c7d73d01d8d736aff2db220d74f985cbcf9b4ff3d6aeb1c7173c1e8d7f827`, and
routes
`b4cb7f0115a9158c9b9b02e2835845104eefaa4a7f398de8884ef2e8ece7206c`.

## Gate findings

P0: none found.  The proposed QC ratios are dimensionless and their stated
common-gain/time-independent channel-offset invariance is derived in
`11-math.md:32-53`; the channel-specific-gain limitation is explicitly
disclosed at `11-math.md:57-70`.  The strict nonfinite/zero-scale gate,
fixed-window limitation, and adverse synthetic-test requirement are explicit
in `00-contract.md:61-91`.  The reported dimensionless validation is accepted
as supporting evidence: `tests/test_dimensionless.py` 19 passed in 0.40 s and
the checker exited 0; this is a numerical integrity check, not biological
evidence.

P1: one intentional inferential limit remains.  A finite observed EEG
quotient cannot identify whether the underlying object is an instantaneous
state or an ordered path, nor establish self, consciousness, an
infinite-dimensional manifold, or a hippocampal hash.  This no-go and the
claim ceiling are explicit in `00-contract.md:13-18,170-174`,
`10-sources.md:46-58`, and `11-math.md:98-102`.  It is not a gate defect, but
must remain in every result report.

## Coherence and leakage checks

- Source lock is coherent: OpenNeuro `ds006033` v1.0.1, DOI, tag object,
  CC0, primary paper, five observed recordings, the 64-column header/binary
  authority, and the sidecar conflict are recorded in `10-sources.md:9-25`.
  The five recordings are not treated as five independent subjects.
- The sealed event accounting is internally consistent: 539 valid pairs,
  32 apparatus, 164 development, 250 confirmation, and 93 unused in
  `10-sources.md:24`; the contract expands this to D1 32, D2 132, and
  C1/C2/C3 25/50/175 at `00-contract.md:91-98,149`.
- A2 alone freezes the two cutoffs.  It has no endpoint, target, feature, or
  loss access, and the correlation/generalization limitation is disclosed in
  `11-math.md:74-78`; therefore the threshold rule is not target-aware.
- D1 is QC-only.  The contract and route both prohibit `z`, future targets,
  features, losses, and model selection in D1 and permanently exclude its 32
  pairs from model reuse (`00-contract.md:94-98,159`; `12-routes.md:43-48`).
  The 24/32 total and 12/16 per-session requirements are execution gates, not
  scientific effect thresholds.
- D2 has 73/59 pairs by session, 59-pair minimum training, 118 task/rest rows,
  and maximum `p_1=59`; SVD/ridge, whitening rank/condition gates, and
  development-only menu selection are fixed in `00-contract.md:119,123-125`
  and `11-math.md:80-84`.
- `sub-03` C1/C2/C3 remains sealed until D2 selection and adverse-control
  checks complete (`00-contract.md:96,123-137`; `12-routes.md:47-53`).
  No confirmation result may be used to revise QC, features, target, menu, or
  thresholds; such changes require a new contract (`00-contract.md:161`).
- Receipt requirements are sufficient but still implementation obligations:
  every range must record URL, ETag, Content-Range, byte count, SHA-256, and
  each D1 pair must record `Q_A`, `Q_D`, reason, and session/total counts
  (`00-contract.md:147`, `11-math.md:102`).  Missing receipts would block the
  implementation/final gate, not invalidate this frozen mathematical audit.

## Decision

The four frozen lanes are mutually coherent, source-locked, dimensionless
limitations are disclosed, and target awareness, D1 nonreuse, split counts,
development degrees of freedom, confirmation sealing, and ontology claim
ceiling are explicit.  No P0 or unresolved P1 requiring a contract revision
was found.

Gate: PASS
