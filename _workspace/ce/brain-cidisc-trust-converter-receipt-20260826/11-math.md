# Mathematics

Status: COMPLETE

## TCIDISC.1 — root authorization

The root-signed anchor binds institution/root/coverage key IDs, the coverage public
key, and inclusive validity dates. Verification requires date inclusion, exact root
fingerprint, and strict Ed25519 root signature.
Dates are canonical zero-padded real Gregorian dates, not regex-only strings.

## TCIDISC.2 — converter content receipt

The coverage-key-signed message binds the anchor hash, native calibration and heldout
hashes, converter binary and contract hashes, and the SCIDISC canonical calibration
and heldout output hashes.

## TCIDISC.3 — composition

The chain succeeds only if SCIDISC already succeeds, its signer key exactly matches
the anchored coverage key, and both root and converter signatures pass. Any bound
content mutation invalidates at least one signature.

## TCIDISC.4 — boundary

The content receipt does not prove that the named converter binary actually executed.
A caller-supplied root fingerprint is not proof of independent external distribution.
