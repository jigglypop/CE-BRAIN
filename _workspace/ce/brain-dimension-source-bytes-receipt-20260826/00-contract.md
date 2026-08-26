# Contract: canonical dimension source archive-byte receipt

Status: COMPLETE

## Objective

Reconstruct all six exact dimension payloads from canonical UTF-8 archive bytes,
verify byte-for-byte canonicality and a length-delimited bundle root, and execute
the complete DMAN/DPREP/DPCA/DEXEC/DSTAB chain using only reconstructed values and
hashes computed directly from those bytes.

## Acceptance conditions

1. Every archive payload parses through the exact tagged grammar.
2. Re-encoding the decoded value equals the supplied bytes exactly.
3. Unreduced rational tokens and semantically equivalent noncanonical JSON fail.
4. Six domain tags and tuple schemas are fixed.
5. A domain-separated length-prefixed bundle root matches its frozen expected hash.
6. Session identities and base execution contract agree across all payloads.
7. Schema-declared indices are converted to integers only after denominator-one proof.
8. External acquisition and empirical flags remain false.
