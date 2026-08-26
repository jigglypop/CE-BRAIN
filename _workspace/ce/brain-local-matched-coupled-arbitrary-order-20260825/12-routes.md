# Alternative routes lane

Status: COMPLETE

## Route A: reuse a core-only global certificate without collar coverage

Rejected.  Matched preimages may lie outside the core, and Dn comparison uses
its point modulus on the collar.

## Route B: declare exact contacts robust

Rejected.  Equality contacts have zero topological margin even when the
differential inequalities are strict.

## Selected route

Wrap one frozen global certificate, declare the highest covered collar order,
normalize all radii exactly, and separate local backward coverage from exact
matched forward retention.  This preserves the tested C4 semantics without
hard-coding C4.
