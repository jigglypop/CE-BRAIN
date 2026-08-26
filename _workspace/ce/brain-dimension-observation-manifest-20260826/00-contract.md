# Contract: content-addressed dimension observation manifest

Status: COMPLETE

## Objective

Bind every supplied development/held-out value, frozen preprocessing input,
eigenbasis witness, bootstrap schedule, and execution threshold to a computed
canonical SHA-256, while enforcing an immutable, globally disjoint observation-ID
split before the DPREP/DPCA/DEXEC/DSTAB chain runs.

## Acceptance conditions

1. Canonical encoding accepts only exact integers/Fractions, strings, sequences,
   and mappings; floats and booleans fail closed.
2. Equivalent rational values and mapping order produce the same hash.
3. Observation-ID shapes exactly match all row/window payloads.
4. Observation IDs are globally unique across development, conscious held-out,
   and control held-out splits.
5. Six computed hashes must equal their frozen expected values before execution.
6. Only computed hashes enter the downstream preprocessing chain.
7. Content addressing is not reported as an external signature or empirical result.
