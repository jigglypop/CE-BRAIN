# Mathematics

Status: COMPLETE

## DBYTE.1 — unique canonical inverse

The decoder accepts only the tagged grammar emitted by `C`. Rational nodes require
a positive denominator, canonical decimal integer strings, and reduced numerator
and denominator. After recursive decoding it requires `C(D(b)) = b` byte-for-byte.
Thus semantic JSON equivalence is insufficient and the accepted representation is
unique within this grammar.

## DBYTE.2 — unambiguous bundle root

For six payloads `b_i`, compute each `h_i=SHA256(b_i)` and

`H=SHA256("CE-DIM-SOURCE-BUNDLE-v1" || 0 || concat_i(u64be(len(b_i)) || b_i))`.

The fixed domain and 64-bit lengths remove payload-boundary ambiguity. `H` must
equal a frozen lowercase expected SHA-256 before any downstream execution.

## DBYTE.3 — conditional execution composition

All domain tags/shapes, cross-domain session identities, and the menu/band/selected
rank fields of the base certificate must agree. A rational in an integer-only schema
is refined to a built-in integer iff its reduced denominator is one. The reconstructed
values and byte-derived domain hashes then enter DMAN and its full successor chain.
This proves canonical-archive value provenance, not acquisition authenticity.
