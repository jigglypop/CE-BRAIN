# BA-OBS-HPC3 implementation

Status: SKIPPED — final raw build authorization blocked after revision 2/2; static record retained

Active transaction-seal implementation; no raw/network execution.

HPC3 CLI paths use the active run artifacts while exact inherited HPC2 lock/static
bytes remain hash-bound. The executable supports only `raw-one-shot` and read-only
`status`; injected loaders are used only in no-network fixtures.

Revision 2/2 closes the transaction boundary: frozen 18-record identity maps, exact
receipt schemas, finite endpoint/analysis shapes, p20 endpoint/QC-order assertion,
and resolver precedence are checked before a receipt can authorize a state. Separate
authority, journal, and terminal writers preserve an already committed authority when
a later writer raises. No raw/network execution occurred.
