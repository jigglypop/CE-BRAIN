# Alternative routes lane

Status: COMPLETE

## Route A: expand modified tensors separately at every order

This reproduces the C1--C4 predecessor style but grows rapidly and hides the
single reusable implicit identity.  It remains useful for sharper low-order
cancellations, not as the primary arbitrary-order representation.

## Route B: differentiate a graph-dependent inverse directly

An inverse Bell recurrence for each graph is possible, but its two-graph
difference again requires inverse-slot telescoping and matched-coordinate raw
moduli.  It is algebraically equivalent but duplicates work.

## Selected route

Factor the problem into a raw-jet generator and the universal equation
`Y=T compose F`.  The selected solver enumerates partitions exactly, isolates
`(n,0,...,0)`, and records numerator and inverse-slot difference contributions
separately.  This is the smallest route whose theorem scope remains honest and
whose coefficients can be audited at every finite order.
