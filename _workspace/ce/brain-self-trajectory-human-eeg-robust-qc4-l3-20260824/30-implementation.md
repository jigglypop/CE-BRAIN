# BA-SRM4 implementation

Status: COMPLETE

Scope is P0 and signal-blind A0 only. No human EEG payload, decoded window,
target, or model outcome was opened.

- Contract SHA-256: `04ea2bb2166916120bebf25c546646dd59f4bd20b4c97c4e9ba5de28f70a174d`
- Frozen SELF1 range/parser SHA-256: `b075b9deb34c6a5e93ab58eabeb378a38c2e69045b4155d219252154baa3d559`
- Frozen SELF3 allocation SHA-256: `91fff95baa5ff309d2dda23e4206da8f7f04fd6341c6b1012b2dbb82bb95f1c2`
- Implementation SHA-256: `c56b67b5c3fb896f57a1ce0479ca798b4799c671baad3144eabd5bd9edcbabf4`
- Test SHA-256: `b6be519fbe9b3bad1ff218d838579f2dd679af38aacfab3d87eb899c98c0e0b4`

`srm4_real_eeg.py` implements fold-local median/MAD, bounded transform,
training-only PCA/whitening, level-2 area, unpenalized-intercept ridge using
`lstsq`, deterministic increment-order shuffle, fail-closed domain checks,
and deterministic metadata-only allocation. The allocation receipt SHA-256 is
`19143050282eb8534ea1aab09593051313a4e43bd9acc877a1bdb1eb0a46929c`.

The real stages remain offline unless explicitly executed by the main agent
after code audit; this implementation handoff does not open them.
