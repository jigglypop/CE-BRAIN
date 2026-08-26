# Stage 0 implementation record

Status: COMPLETE

The NumPy-only harness is `artifacts/stage0_synthetic_discrimination.py` with a
focused companion test. It implements seven fixed-seed synthetic worlds, five
candidate procedures, train/validation selection, post-serialization unseen
evaluation, persistence and permutation controls, atomic receipts, and
fail-closed manifest verification.

The implementation was revised only before manifest sealing in response to
outcome-blind mathematical audits. The stable version was sealed with source
SHA-256
`7589e09f1d647d78f6e0f315e09ff5af15730a05ae55e87b0928db7001184b60`.
No sealed file was modified after the manifest was written.

Manifest SHA-256:
`cadaefa5d746146967c6772a59b1ee5141fbed79b8d804c783b3775c62f9f12a`.

The only scientific execution entry point verifies that manifest, fits and
serializes one winner per world/replicate, and then evaluates unseen data. The
single execution produced result SHA-256
`44d059d3b0786b37738782d74a406eac3f77c46ee9286f72f449fc0700c38ab2`.

The implementation makes no real-brain geometry claim and stores no persistent
raw synthetic arrays (`persistent_raw_bytes=0`).
