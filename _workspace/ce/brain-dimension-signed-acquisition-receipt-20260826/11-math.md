# Mathematics

Status: COMPLETE

## DSIGN.1 — Ed25519 verification

Use `p=2^255-19`, Edwards parameter `d=-121665/121666 mod p`, base point `B`, and
prime subgroup order `L=2^252+27742317777372353535851937790883648493`. Decode
`A` and signature `(R,S)`, compute

`h = LE(SHA512(ENC(R) || ENC(A) || M)) mod L`,

and require `[S]B = R + [h]A`.

## DSIGN.2 — strict input gate

Require canonical point re-encoding, `0 <= S < L`, `A != O`, `[L]A=O`, and
`[L]R=O`. These conditions strengthen parsing and exclude identity/small-order
public-key acceptance before using the sufficient non-cofactored equation.

## DSIGN.3 — signed CE message

Let `K` be the canonical signer key ID. Sign

`"CE-DIM-ACQUISITION-SIGNATURE-v1" || 0 || u16be(len(K)) || K || H_contract || H_bundle`.

Also require `SHA256(public_key)=H_key_frozen`. A successful signature therefore
binds the exact CE bundle, acquisition contract, and key label to the supplied key.

## DSIGN.4 — conditional composition

Only after bundle-root, key-fingerprint, and strict signature success is DBYTE
called. Its success composes the signature with every exact downstream calculation.
This does not prove that the frozen fingerprint was independently distributed by
an authorized institution or that the archive originated at a physical device.
