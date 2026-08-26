# State-reset immediate-challenge pre-seal audit

Status: COMPLETE

Gate: PASS

Scope: outcome-blind contract, mathematics, implementation and receipt audit.
No confirmation population, `_run_replicate`, `execute`, manifest or result was
opened during the audit.

## Parent and route integrity

- The sealed Stage 0 and matched-twin STOP results remain unchanged.
- The state-collapse counterexample is preserved as post-outcome exploratory evidence.
- Three structurally different routes were recorded; the selected route changes the
  observed boundary condition and intervention timing, not a predecessor threshold,
  seed, endpoint, coefficient law or model class.
- Parent source SHA-256 and the fresh root-label digest/seed are verified in code.

## Mathematics disposition

The stable route uses the paired-Hadamard bank `B=[V;-V]`, where `V` contains
Sylvester rows 0, 1, 2 and 4. Independent audit verified coordinate balance,
RMS 0.30, the exact train/validation assignment, `x0=x1=z`, immediate `1:5`
pulse indexing and scoring over samples 2--63. D/E use 999 block-local
Fisher--Yates product permutations and the registered Monte Carlo p-value;
A/B/C/F/G use the float64 twin-independence identity. Final mathematics verdict:
`PASS`, P0/P1/P2 none.

## Implementation disposition

- Frozen parent recurrences and candidates are imported only after source-hash verification.
- Winner descriptor and every candidate hash are serialized before confirmation construction.
- Main CRNs are shared within arm pairs, unique across twins, and excluded from model features.
- Train/validation assignment receipts are revalidated against the exact fixed formula.
- Every main reset and both arms' `x0=x1=z_cr` receipts are reconstructed and revalidated.
- Split trajectories and confirmation arms are hash-disjoint; result rows revalidate receipts.
- Common-state adverse controls use a shared across-twin innovation path and require identity.
- Missing/mutated manifest files, pre-serialization access, malformed populations,
  reset/assignment corruption, duplicate main CRNs, split-arm overlap, nonfinite values
  and zero scoring scale fail closed.

Stable-snapshot hashes before this audit file:

- contract: `4cd652b15b79ff1d529a467827bdff1437cc51065b7736e6c4969e3161c9aa85`
- route: `6d594186c85835f871520392bcdf09e65a177182809cc06f9aa6910dd49925bc`
- implementation: `676ea0ca459efd7c6df887cb479424755ed61b60c9d85be6658d67f0a0877574`
- focused test: `098ff1f3640cc7a54748025acbc7de943152a34e09a80cb729d423678f06b7f6`

Seal authorization is conditional only on binding this audit and
`21-preexecution-validation.md` in the actual manifest. Once bound, no listed
byte may change before the single confirmation execution.
