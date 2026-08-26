# Mathematics

Status: COMPLETE

## DMAN.1 — canonical exact encoding

Let `C(q)=[q,num(q),den(q)]` for a reduced rational, `C(s)=[s,s]` for a
string, `C(x)=[a,C(x1),...,C(xn)]` for a sequence, and let a mapping be encoded
as `[m,[C(k),C(v)],...]` after sorting by the canonical JSON key encoding.
Compact UTF-8 JSON is hashed by SHA-256. Floats and booleans are outside the
domain. Hence integer/Fraction equality and mapping-order invariance are exact.

## DMAN.2 — immutable split condition

ID tensors must have the same session/row/window shape as their payloads. If
`I_dev`, `I_con`, and `I_ctl` are their flattened ID sets, the implementation
requires every concatenated ID to be unique. Therefore all pairwise intersections
are empty and duplicates within a split are also excluded.

## DMAN.3 — conditional composition

Domain-separated hashes are computed for development, held-out, preprocessing,
eigenbasis, bootstrap, and execution-contract payloads. The downstream chain is
called iff all computed hashes equal frozen expected hashes and DMAN.2 holds.
Consequently a payload mutation with unchanged expected hashes fails before DPREP.
This implication is internal and conditional; it does not authenticate who supplied
the expected hashes or how external bytes became exact values.
