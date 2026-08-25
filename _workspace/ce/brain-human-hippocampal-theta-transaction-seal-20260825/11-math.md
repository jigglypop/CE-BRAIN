# BA-OBS-HPC3 mathematics inheritance check

Status: SKIPPED

Reason: HPC3 deliberately changes only transaction authority. It inherits, without
modification, HPC2's source lock, author-code measurement axiom, 18-object cohort,
first-999 grid and integer masks, QC thresholds and `MIN20` aperture, references,
P2P-of-mean estimator, TS(4)-PB(5) participant-equal contrast, PCG64 seed 20260825,
65,536 shared-participant bootstrap draws, LOO, paired sensitivity, and status lattice.
The predecessor's mathematics lane is therefore the controlling independent derivation;
recomputing it here would not test the stated delta.

Independent transaction check: the resolver only maps a completed computation to a
terminal receipt. It does not change any sample, retained-trial set, window, amplitude,
participant weight, contrast, uncertainty interval, control, or status predicate.
`raw_result.json` is permitted only after all source and both `MIN20` gates have passed;
`qc_result.json` is endpoint-free; and a terminal source/implementation receipt has no
endpoint. Thus each possible resolver branch either exposes the inherited fixed
estimand once, or exposes no estimand. There is no mathematical selection or retry
branch.

The post-atomic-commit progress-finalization rule is also estimand-neutral: it preserves
an already serialized fixed result rather than recomputing it. Conversely, every failure
before the atomic result replacement must remain endpoint-free. This preserves the
predecessor's no-voltage/outcome-blind transaction until a single valid commit. No P0/P1
mathematical finding is introduced by the authority delta.
