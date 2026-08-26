# Implementation

Status: COMPLETE

`verified_dense_similarity_interval_residual.py` provides:

- exact two-sided inversion checks for one supplied `Q(i)` similarity;
- outward entry-magnitude matrices for `T` and `T^-1`;
- exact nonnegative multiplication for `|T^-1| D |T|`;
- induced `1/infinity` spectral-norm uppers and their product condition bound;
- transformed node residual certificates and condition-translated node lowers;
- best-of-untransformed/dense full-circle outputs plus a dense-only margin;
- honest flags stating that neither empirical provenance nor data-selected
  optimization was verified.

Block-diagonal similarities require no separate implementation because they are an
exact input subclass of the dense matrix contract.
