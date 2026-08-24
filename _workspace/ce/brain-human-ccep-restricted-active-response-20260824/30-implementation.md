# BA-OBS-ID3 implementation receipt

Status: COMPLETE

Result: Frozen confirmation executed once after the range audit.

## Invalidated first implementation attempt

The first recorded synthetic stop is **IMPLEMENTATION_INVALID**, not a formula or
biological failure.  It used a scalar fixture surrogate, did not use the actual 24-site
52-pair mapping and half-specific counts, and did not enforce the two-readout composite.
Its reported 30/256 and 17/256 figures are retained only as an invalid diagnostic.

## Corrected scope implemented

`artifacts/ba_obs_id3.py` implements the frozen finite-response operations: normalized
disagreement, raw reciprocal/split-half ratio, direction/half-specific trial bootstrap,
reciprocal-location restricted null, source-head/marker pre-decode guards, and the
contract's synthetic fixture runner.  It has no parameter-selection or retuning mode.

The corrected fixture uses the frozen list-order 52 confirmation pairs, actual metadata
half counts (5--9), deterministic source/half streams shared only over receivers of that
source, independent 1:8 baseline scales and 1:16 noise scales, both mean and bipolar
readouts, and an executable full-window/mask equivalence fixture.  It passed before any
source signal request.  VMRK uses `^Mk\d+=`; all metadata hashes and marker crosswalk are
checked before HEAD.  Each real range is version-bound and checked for 206, exact
Content-Range, ETag, VersionId, length and SHA-256.

## Frozen inputs and environment

- Contract SHA-256: `80f10d1a1ff062da837dc2c852c7ea52baf89078089b50aae0249cb816802379`.
- Implementation SHA-256: `239861b1c78c671ad5f57d6906451a12a57cf8ec3581a09829a4e6061374bd3b`.
- Interpreter: `C:\\Users\\dongh\\AppData\\Local\\Programs\\Python\\Python311\\python.exe`, Python 3.11.9.
- NumPy: 2.4.6.  No virtual environment, `uv`, or package installation was used.
- Fixed fixture design: 52 confirmation-layout pairs; outer seeds 370800–371055
  (256); inner restricted-null resamples 2048; Gaussian and unit-variance centered
  $t_5$; direction/site heteroscedastic range 1:16; baseline-scale range 1:8;
  directed fixture log-gap $\log(1.6)$.

## Current boundary

The unversioned development attempt was terminated before any endpoint or receipt was
created; it is **IMPLEMENTATION_INVALID** and authorizes nothing.  The corrected
version-bound development pass is recorded in `artifacts/real-development-receipt.json`.
The first same-half confirmation serialization was **IMPLEMENTATION_INVALID** under the
cross-half audit and was replaced by the corrected cross-half B=8192 receipt after the
range audit.  No current result supports a metric, consciousness, self,
hippocampus, or AGI claim.

Claim ceiling if a future, separately frozen revision succeeds remains:
`SINGLE_SUBJECT_HUMAN_CCEP / FINITE_RESTRICTED_OBSERVED_RESPONSE_RECIPROCITY_FALSIFIER /
NO_AMBIENT_OR_INFINITE_DIMENSIONAL_METRIC_RECOVERY / NO_CONSCIOUSNESS_SELF_HIPPOCAMPUS_OR_AGI_VALIDATION`.
