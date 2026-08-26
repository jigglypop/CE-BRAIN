# Mathematics

Status: COMPLETE

## ARP.1 Exact invariant decomposition

Let `U in Q(i)^(n x n)`, normalized center `c`, radius `r>0`, and supplied
`P in Q(i)^(n x n)` satisfy
\[
 P^2=P,\qquad PU=UP.
\tag{ARP-1}
\]
Then `Q=I-P` gives the invariant direct sum
`C^n=ran(P) direct-sum ker(P)`.  Since an idempotent has eigenvalues zero or one,
its exact trace is the integer rank of `P`; the implementation also checks that
receipt explicitly.

## ARP.2 Inside certificate

Set `A=U-cI`.  Every generalized spectral value on `ran(P)` belongs to the spectrum
of `A|ran(P)`, and
\[
 \rho(A|_{\operatorname{ran}P})\le\|AP\|_2.
\]
Therefore the strict outward bound
\[
 \|AP\|_2^+<r
\tag{ARP-2}
\]
puts the entire possibly defective inside block strictly inside the circle.

## ARP.3 Exterior inverse certificate

Supply normalized `R in Q(i)^(n x n)` satisfying
\[
 R=RQ=QR=QRQ,\qquad RAQ=Q,qquad AR=Q.
\tag{ARP-3}
\]
Thus `R` is the two-sided inverse of `A` on `ker(P)` and vanishes on `ran(P)`.  If
\[
 r\|R\|_2^+<1,
\tag{ARP-4}
\]
then every exterior spectral value `mu` obeys
`|mu| >= 1/rho(R) >= 1/||R||_2^+ > r`.

Both norm uppers use the tighter outward value of the Frobenius bound and
`sqrt(|| |X|^+ ||_1 || |X|^+ ||_infinity)`.

## ARP.4 Algebraic Riesz-projector theorem

Under (ARP-1)--(ARP-4), the spectra of the two invariant summands lie strictly on
opposite sides of the circle.  Holomorphic functional calculus is one on the first
summand and zero on the second, hence the exact Riesz projector is precisely `P`,
with rank `tr(P)`.  No diagonalization, eigenvector basis, semisimplicity, or
rational eigenvalue list is required.  QED.

## ARP.5 Complete examples and boundaries

- An inside `2 x 2` nilpotent Jordan block and exterior eigenvalue four pass for
  radius two.
- The rational block `[[0,2],[1,0]]` has eigenvalues `+-sqrt(2)`; it passes inside
  radius three without representing those roots.
- Rank zero and full rank projectors pass with the expected empty summand.
- Nonidempotence, noncommutation, noninteger trace receipt, unsupported or one-sided
  exterior inverse, and equality in either strict norm gate fail closed.
