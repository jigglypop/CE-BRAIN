# Mathematics

Status: COMPLETE

## SCIDISC.1 — canonical exact vectors

Encode role, labels, exact scales, and exact nonnegative error rows using a fixed
domain, uint64 big-endian counts/lengths, UTF-8 strings, and reduced ASCII
`numerator/denominator` fractions. Calibration and held-out roles are separated.

## SCIDISC.2 — signed content message

Compute SHA-256 of calibration bytes, held-out bytes, and raw coverage-contract bytes.
The signed message is a fixed domain, length-prefixed signer key ID, and the three
ordered digests.

## SCIDISC.3 — strict Ed25519

Require canonical point encoding, scalar below subgroup order, nonidentity prime-order
points, the Ed25519 verification equation, and exact expected public-key fingerprint.

## SCIDISC.4 — fail-closed composition

CIDISC executes only if computed hashes equal frozen expected hashes and key/signature
checks pass. A valid signature cannot override downstream exchangeability,
undercoverage, interval, or rank failures.
