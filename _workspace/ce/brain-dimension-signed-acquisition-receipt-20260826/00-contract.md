# Contract: strict Ed25519 signed dimension acquisition bundle

Status: COMPLETE

## Objective

Verify a strict Ed25519 detached signature that binds a signer key ID, acquisition
contract digest, and canonical six-domain source bundle root before executing the
DBYTE/DMAN/DPREP/DPCA/DEXEC/DSTAB chain.

## Acceptance conditions

1. Ed25519 follows RFC 8032 field, group, hash, and signature equations.
2. Official RFC 8032 Ed25519 test vectors pass.
3. Point encodings are canonical, `S < L`, the public key is nonidentity, and
   public/R points lie in the prime-order subgroup.
4. Message, signature, scalar, and identity-key adversaries fail closed.
5. The signed message binds domain, signer key ID, contract hash, and bundle hash.
6. The supplied public key matches a frozen expected SHA-256 fingerprint.
7. Only a successful signature gate may invoke the canonical source-byte chain.
8. External trust-anchor identity, device conversion, and empirical flags stay false.
