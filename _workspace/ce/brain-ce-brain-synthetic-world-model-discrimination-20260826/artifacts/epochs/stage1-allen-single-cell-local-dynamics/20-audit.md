# Stage 1 Allen local-dynamics pre-seal audit

Status: COMPLETE

Gate: PASS

Scope: official-source, outcome-blind contract, measurement, mathematics,
implementation and receipt audit. The schema smoke inspected dataset shapes,
attributes and epoch indices only; it did not load response/stimulus arrays or
compute development/confirmation endpoints.

## Provenance and measurement

- Official Allen API/SDK documentation fixes specimen, ephys result, NWB access,
  SI units and inclusive `index_range` semantics.
- Raw identity is 53,057,893 bytes with SHA-256
  `fd164a3091fbbb3be358238088afa2e2f08981d49edffa87d55309931a9853ab`.
- Schema receipt `0c3df6cf9c84b67a7debaad3825ea5b94be115ca2a80321baca814b1e9813fab`
  verifies NWB 1.0.5, IVSCC 1.0, specimen/session identity, all 33 selected
  sweeps, 200 kHz, Volts/Amps, conversion 1.0 and exact experiment ranges.
- Inclusive source indices are transformed to an explicit half-open aligned
  interval before factor-20 block means and mV/pA conversion.

## Mathematics and leakage

Independent audit verified `t=500,...,K-11`, target `V_(t+10)`, future crossing
indices `t,...,t+9`, strictly prior spike-history crossings and deterministic
fit thinning. Fit, Noise 1 development and Noise 2 confirmation sweep sets are
disjoint. Standardization and model parameters use fit rows only; neither
development nor confirmation can change features, horizon, thresholds or gates.

The unpenalized-intercept ridge/logistic equations, positive-scale checks,
degenerate-target and convergence stops, per-sweep metrics, Brier/persistence
denominators and exhaustive decision statuses were independently checked.

## Implementation and receipts

- Schema mode never indexes response/stimulus data values.
- Manifest binds the raw SHA, schema receipt SHA and all preregistration bytes.
- Stored results reload through `verify_result`: model arrays are reconstructed,
  parameter hashes recomputed, sweep/data/metric receipts revalidated and the
  Noise 2 decision recomputed.
- Existing result, raw/schema/manifest mutation, split/index/unit/rate/conversion
  mismatch, nonfinite values and result-link mutation fail closed.
- No raw sample is persisted in the result.

Stable-snapshot hashes before this audit file:

- contract: `2bbadc47a7bcfecc695a7639825ad564f540883b6c809e47fe0fca42b7ab9417`
- data lock: `87173ed46b4f0c21bb8f1ae903a533a146b6f1b86d7bdc18f16343431fdf2f30`
- sources: `047e33ff9aebdc2d202ed513d1162adb4cf1da621ab470d84358ff2d09b45e0e`
- implementation: `35d265888afa39d16c0e0f398302b179ae8399c8d16f38983f611147ef26d2de`
- test: `28e887a8474aa8f93667861b8692fa4822b56dc2280435eddf807067e9cf39c1`

Final preimplementation and code audits: `PASS`, P0/P1/P2 none. Seal is
authorized only after this file and `21-preexecution-validation.md` are bound.
The claim ceiling remains a one-cell public-recording predictive comparison.
