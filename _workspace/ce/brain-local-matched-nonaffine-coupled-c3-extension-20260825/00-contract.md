# Research contract

Status: COMPLETE

PREDECESSOR:
- `_workspace/ce/brain-local-nonaffine-coupled-c2-extension-20260825`
- `_workspace/ce/brain-matched-local-nonaffine-coupled-c2-extension-20260825`
- `_workspace/ce/brain-nonaffine-coupled-c3-extension-20260825`

## Objective

Close the missing local and exact matched-domain nonaffine coupled C3 graph
transform by composing the already verified global C3 differential recurrence
with explicit core inverse coverage, a two-sided C3 extension collar, exact
forward/backward boundary contact, and boundary anchoring.

## Frozen claims

1. A local C3 certificate is valid only when the inverse of the core output
   ball stays in the core input ball and the inverse of the output C3 collar
   stays in the input C3 collar.
2. Both collar widths are strictly positive; zero collar is a named failure,
   because closed-boundary C3 derivatives otherwise lack an open-neighborhood
   extension premise.
3. The local wrapper changes no global C0--C3 coefficient or recurrence.
4. The matched wrapper additionally requires exact inverse and forward
   boundary contacts plus zero graph and fiber boundary residuals.
5. Exact matched contact has zero domain-contact margin, while differential
   and collar margins may remain strict.
6. The boundary-anchored cubic coupled interval is an exact rational witness;
   removing either collar coverage, graph anchoring, or fiber-boundary forcing
   kills only the corresponding conclusion.

## Definitions and units

All radii have base units before division by `base_reference_scale`. All map,
graph, derivative, and recurrence coefficients are the normalized
dimensionless quantities of the global predecessor. No exponential,
logarithmic, probability, or dimensional fixed-point argument is introduced.

## Scientific boundary

This is a conditional finite-dimensional theorem and an exact implementation
certificate. It uses no neural field, measurement model, brain data, fitted
constant, or dimensional-selection evidence. It cannot establish that human
consciousness is 4--6 dimensional.

## Falsifiers

- core inverse overrun;
- nonpositive input or output C3 collar;
- expanded inverse-image overrun of the input collar;
- any changed global C3 certificate or iteration coefficient;
- in the matched layer, nonexact inverse/forward contact or nonzero boundary
  graph/fiber residual;
- failure of scale covariance or exact rational witnesses.

## Validation

Use the repository Windows Python wrapper. Run focused local/matched C3 tests,
then the dimensionless test and only the adjacent local/global C2--C3 chain.
Do not run the full suite, benchmarks, network, or empirical analysis.
