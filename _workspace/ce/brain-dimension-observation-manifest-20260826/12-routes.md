# Routes and counterexamples

Status: COMPLETE

## Closed routes

- Exact rational canonicalization removes `int` versus equivalent `Fraction` noise.
- Sorted mapping keys remove insertion-order dependence.
- Domain tags prevent cross-purpose payload tuples from sharing an intended role.
- Shape checks bind one observation ID to every supplied row.
- Global uniqueness rejects development/held-out reuse.
- Expected-hash comparison occurs before preprocessing execution.

## Adversarial routes

- Binary floats and booleans are rejected rather than silently rounded/coerced.
- Mutating one development coordinate invalidates the frozen development hash.
- Removing one row ID fails the shape gate.
- Reusing a development ID in control held-out fails the split gate.
- A caller-chosen matching expected hash still does not create an external signature.
