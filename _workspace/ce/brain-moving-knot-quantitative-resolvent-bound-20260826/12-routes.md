# Candidate routes

Status: COMPLETE

| Route | Decision | Reason |
|---|---|---|
| Exact squared-distance certificate | Implemented | Avoids irrational radii through a rational reverse-triangle lower bound. |
| Affine determinant/Frobenius singular-value lower bound | Implemented | Exact rational and valid for every invertible positive-orientation frame. |
| Exact-witness Frobenius conditioning | Implemented | Safely upper-bounds the nonnormal eigenvector condition factor. |
| Gap-only resolvent bound | Rejected | Nonnormal eigenvectors can make the resolvent arbitrarily larger. |
| Interval matrix family | Deferred | Requires a perturbation gate using the new uniform resolvent bound. |
| Defective/no-witness family | Deferred | Exact diagonalization is an explicit premise. |
