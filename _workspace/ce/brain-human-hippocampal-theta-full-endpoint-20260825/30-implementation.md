# Implementation

Status: COMPLETE

`ba_obs_hpc6_full_endpoint.py` implements the single `ENDPOINT_FULL1`
transaction. It freezes the H5 executor, H2 source loader, predecessor Q
receipt/progress, and the four current stage documents in `analysis_lock.json`.
It rejects any prior witness/result/progress before loading sources. For each
of the 18 locked source objects it validates the loader identity, runs H5
corrected dual-path QC once, persists both the complete selected QC-channel
tensor (including rejected trials) and bipolar trace as a compressed witness,
and records per-array dtype/shape/SHA-256 plus whole-file SHA-256.

Endpoint output contains clinical trial-mean and mean-waveform P2P for three
fixed windows, both references only when all bipolar cells remain available,
participant deltas, shared-PCG64 bootstrap, seven LOO contrasts, paired p17/p19
sensitivity, all QC diagnostics, and progress/result/witness hash binding.

`ba_obs_hpc6_full_endpoint_validator.py` does not call the producer endpoint
or aggregate functions. It validates witness manifest/file binding, reruns
dual QC from the persisted selected traces, recomputes endpoint and aggregate
leaves independently, checks predecessor-Q rows, and rejects all-or-none
bipolar violations.

No raw/network stage was run during implementation.

Revision 1 adds a separate execution lock (code/test hashes), same-directory
atomic `.tmp.npz` witness commit, independent validator pre-final content pass,
and a standalone offline validator CLI. `COMPLETE` is written only after that
pre-final pass; final validation then additionally requires the COMPLETE
progress binding.

Revision 2 closes the authoritative metadata forgery: validator reconstruction
now exact-checks every frozen source/QC record in SPECS order, fixed claim
labels, and H5 A/B diagnostic parity. The frozen execution lock is
`aefbec437279519bd568e77ffc0f5a01b1795b24843acb178abfdc9a1f57aa6b`.
