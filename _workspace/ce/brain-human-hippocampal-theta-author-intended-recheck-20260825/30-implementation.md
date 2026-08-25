# HPC5 implementation

Status: COMPLETE

Implemented `examples/brain/ba_obs_hpc5_author_intended_recheck.py` and its
focused synthetic tests.  The module reuses HPC2 only for the frozen source
specifications and exact version-pinned full-object loader.  It defines its
own corrected `j/499.5-0.5` clock, masks, two DFT/LPF paths, QC masks,
available-clean endpoint, and aggregation.

Revision 1 additionally binds the current contract/source/math/routes files,
HPC2 source lock/static receipt, and HPC4 progress/QC receipts with a fixed
analysis-lock SHA-256.  It records the two predecessor target counts/reasons
side by side.  Diagnostics now include channel/trial reason hashes, union
hashes/counts, and trial amplitude/margin vectors.  `QC_RECHECK1` contains source/QC material only and rejects endpoint
family keys.  `ENDPOINT1` requires a valid recheck receipt, uses an atomic
authoritative receipt and refuses prior receipts.

No raw or network stage was run by this implementation task.

Revision 2 completes the authoritative endpoint receipt: clinical and, only
when wholly available, bipolar analyses now carry trial-mean and mean-waveform
estimands for all three windows, shared-weight bootstrap, seven-participant
LOO and the p17/p19 paired sensitivity.  Receipt validation reconstructs both
estimands from the file endpoints and rejects altered numeric or categorical
leaves.  Both stages now journal atomically before any loader call and bind
Stage E's two target rows byte-for-byte to Stage Q.
