# Alternative routes lane

Status: COMPLETE

## Route A: order-specific modified tensors

The explicit C1--C4 path can retain anisotropic cancellations and sharper
constants.  Extending it by hand to every order is error-prone and obscures
the invariant partition structure.

## Route B: same-preimage raw rows

Comparing `h` and `k` at one source point omits the displacement between
`F_h^-1(z)` and `F_k^-1(z)`.  It therefore misses both `H_b S_0 Delta_0` and
`Lambda_(j+1) r_x Delta_0` and is rejected for the coupled theorem.

## Selected route

Use matched preimages, one additional graph point modulus, and separate outer-
map and graph-slot telescoping.  Feed the resulting exact Bell rows into the
already audited implicit solver.  This route trades some low-order sharpness
for a transparent, mechanically checkable finite-order theorem.
