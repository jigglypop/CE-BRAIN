# Routes and counterexamples

Status: COMPLETE

## Closed routes

- RFC 8032 vectors 1 and 2 establish standard-equation compatibility.
- Canonical point decoding and subgroup membership strengthen acceptance.
- The domain-separated signed message prevents cross-protocol interpretation.
- Signer ID, acquisition contract, and bundle root are jointly bound.
- A frozen public-key fingerprint detects key substitution relative to that anchor.
- Successful verification gates the full canonical archive execution chain.

## Adversarial routes

- Altered message and altered signature fail.
- Scalar `S=L` fails the canonical scalar range.
- Identity public key fails even if a malformed equation might exploit torsion.
- Stale bundle root, wrong fingerprint, and changed signer ID fail before DBYTE.
- A caller-controlled key plus caller-controlled expected fingerprint is not an
  independently established institutional trust anchor.
