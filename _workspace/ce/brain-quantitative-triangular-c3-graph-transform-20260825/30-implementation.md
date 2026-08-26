# Implementation

Status: COMPLETE

`quantitative_c3_graph_transform.py` composes the exact C2 predecessor,
preserves predecessor failure ordering, rejects nonexact or negative inputs,
reports the C3 class and bunching margins, exposes all four recurrence
coefficients, and iterates the exact C0/C1/C2/C3 recurrence with `Fraction`.

`test_quantitative_c3_graph_transform.py` covers the strict fixture, exact
recurrence, the isolated D4-level modulus contribution, class equality,
bunching equality, the $|x|^3$ witness, predecessor failure, dimensions, and
invalid inputs.

