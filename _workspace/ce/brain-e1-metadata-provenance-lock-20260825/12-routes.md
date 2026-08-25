# E1 metadata provenance: alternative routes

Status: COMPLETE

No empirical or biological route is executed here.  All routes preserve the
contract's ban on neural signals and scientific endpoints.

## R1 - pinned official session-only response (candidate implementation route)

**Entry condition.**  Source lane pins a released AllenSDK/source identity,
manifest version, host and data-use terms, and proves that the selected public
call graph obtains the session-only response without unit/channel/probe/NWB
or signal access.  The predecessor `0.2.1`/`get_session_table` instruction is
not reused if that source proof contradicts it.

**Fixed degrees of freedom.**  Release/tag/commit/hash, host/resource,
required-field mapping, canonicalization policy, salt, hash byte order,
integer thresholds, exact duplicate policy, strict RFC3339 grammar and the
built-in-`int` core boundary are frozen before response rows are read.  There
are no target-aware choices and no model parameters.

**Controls and falsifier.**  Record call graph and negative-access log;
canonicalize the same response twice; require equal table bytes, assignment
bytes and their separate SHA-256 values; run the adversarial fixture.  Any
hidden secondary metadata request, changed bytes, schema failure, or
cross-split specimen assignment is a named fail-closed result.  It establishes
apparatus evidence only, never biological evidence.

## R2 - source proves no safe session-only call (stop route)

**Entry condition.**  The pinned source shows every publicly available path
to the requested table opens unit/channel/probe metadata or another forbidden
resource, or its release/source identities disagree.

**Fixed degrees of freedom.**  Same frozen release and no substituted API,
release, scrape, cache or synthetic table.

**Falsifier/control.**  Preserve source evidence and return the exact
`E1_*` provenance failure.  No response data, score, or alternative endpoint
is opened.  This route is a valid protection of the boundary, not evidence
for or against the CE candidate.

## R3 - canonicalization rejection (local apparatus route)

**Entry condition.**  A permitted session-only response exists but violates a
required type, timezone, row-consistency, finite JSON or duplicate rule.

**Fixed degrees of freedom.**  The rules in `11-math.md`; no post-hoc field
coercion, identifier repair, timezone guess, sort change, rehash, or specimen
movement.

**Falsifier/control.**  Emit diagnostics without materializing a passing
receipt.  The synthetic fixture demonstrates the failure behavior for naive
timestamps, Booleans/floats, missing fields and conflicting duplicates.
No biological endpoint is accessed.

## R4 - later eligibility-small partition (future locked route)

**Entry condition.**  A passing metadata receipt is followed, in a separate
source-locked scientific contract, by a previously specified eligibility rule.

**Fixed degrees of freedom.**  The original assignment is immutable.  The
later contract must state its eligibility predicate and independently count
distinct specimens in calibration, development and held-out before any fit or
score.

**Falsifier/control.**  If any eligible partition has fewer than two
specimens, return `E1_SPLIT_APPARATUS_INVALID`; do not change salt,
thresholds, group key, time bin, filtering or subject placement.  This is the
only point at which the contract's minimum can be evaluated.  It still makes
no statement about recurrence, geometry, consciousness or a 4-6-dimensional
state.
