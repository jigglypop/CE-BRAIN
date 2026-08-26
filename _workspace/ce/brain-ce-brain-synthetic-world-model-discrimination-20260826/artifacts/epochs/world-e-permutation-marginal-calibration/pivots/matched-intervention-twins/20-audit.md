# Matched-intervention-twins pre-seal audit

Status: COMPLETE

Gate: PASS

Scope: outcome-blind contract, mathematics, implementation and receipt audit.
No confirmation population, `_run_replicate`, `execute`, manifest or result was
opened during the audit.

## Parent and route integrity

- Parent manifest, result and `STAGE0_STRUCTURE_DISCRIMINATION_STOP` are preserved.
- The counterexample locks the World E marginal-calibration witness.
- Three structurally different routes were recorded. The selected route changes
  the intervention design, not a threshold, seed, endpoint or decoder.
- Fresh root seed derivation is domain-separated and self-verified in code.

## Mathematics disposition

The initial all-world pairing formulation was rejected before implementation:
linear A/B/C/F/G contrasts are twin-independent under common random numbers.
The stable contract therefore tests D/E pairing only and uses A/B/C/F/G as an
analytic twin-independence negative control. Uniform full-group Fisher--Yates
product draws, the 999-draw Monte Carlo p-value, NRMSE flattening and D/E
identifiability gate were independently checked. Final mathematics verdict:
`PASS`, P0/P1/P2 none.

## Implementation disposition

- Parent source is hash-verified read-only.
- Selection and all candidate hashes are serialized before twin generation.
- Common initial, hidden and innovation arrays are receipt-only and excluded
  from model features.
- CRN receipts are nonempty and unique; arm hashes are unique while repeated
  linear contrast hashes are explicitly allowed.
- Train/validation trajectory hashes are disjoint from confirmation arm hashes.
- Aggregate revalidates root seed, selection serialization, candidate receipt,
  twin population, CRNs and split separation.
- Manifest absence, mutation, pre-serialization access, cross-block shape,
  receipt duplication, nonfinite values and zero contrast scale fail closed.

Stable-snapshot hashes before this audit file:

- contract: `69140de79ad1a0a91d096ca6f7a020200f7dae5ab5bc1b9d80c0e9e837816de3`
- route: `3bd3efaffdfd10ba7c5c6ff1885d404a2e4f225751b1a565b6c5400b366fc1db`
- implementation: `6900a26eeedda1c1294b4c692819a0fb86bdbaa22e0f9dc13b674f7646902f73`
- focused test: `9a933817c91e1761cde3bbe53c80c37ac433899068c398caad79d03bcc531255`

Seal authorization is conditional only on binding this audit and
`21-preexecution-validation.md` in `PREREG_FILES` and the actual manifest. Once
bound, no listed byte may change before the single confirmation execution.
