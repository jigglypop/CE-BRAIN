# BA-SRM4 implementation

Status: COMPLETE

Scope is P0, signal-blind A0, and the single authorized R0-SMALL execution.
R0 opened exactly ten human-EEG task/rest pairs (twenty windows); no R1, R2,
or C split was opened.

- Contract SHA-256: `04ea2bb2166916120bebf25c546646dd59f4bd20b4c97c4e9ba5de28f70a174d`
- Frozen SELF1 range/parser SHA-256: `b075b9deb34c6a5e93ab58eabeb378a38c2e69045b4155d219252154baa3d559`
- Frozen SELF3 allocation SHA-256: `91fff95baa5ff309d2dda23e4206da8f7f04fd6341c6b1012b2dbb82bb95f1c2`
- Frozen A0 metadata receipt SHA-256: `5bc7fb8acebe366db84ba6f4aa9b95eae2051e3bf0f5760792c7ac9e6520a3f7`
- Implementation SHA-256: `6c8e3522c9b4a230196ee65f8eebc6dce58e2c030440cfa4a0c448ab7c3486ea`
- Test SHA-256: `511a1aeeed669277a4df0bcd0cd048b42cb150a63a06498dc7b80275d4e0a5e5`
- R0 receipt SHA-256: `3bd9db6c2c2519075437bdd142c742f361a6efabc68376a7c786fd9d6f9dd61b`

`srm4_real_eeg.py` implements fold-local median/MAD, bounded transform,
training-only PCA/whitening, exact all-pairs level-2 area,
unpenalized-intercept ridge using `lstsq`, constrained deterministic
increment-order shuffle, fail-closed domain checks, and deterministic
metadata-only allocation. The allocation receipt SHA-256 is
`6bcedcf784caa9570f4a46066e9badb9e6fc2a0605de8c4491b4fbf1f84df255`.

R0 verified every provenance hash and allocation-to-manifest link before the
reader was imported. With explicit `--execute` it accessed exactly five pairs
per session, task and rest once each. It fit only the frozen $p=5$ baseline;
area, ordered-history gain and word effects remained unopened. Partial failures
preserve truthful network/signal/endpoint flags and completed range receipts.
The R0 pass gate requires positive task baseline gain in both LOSO directions
and in the pooled loss; a positive pooled gain cannot mask a failed direction.
The real R0 gate failed, so R1 and R2 execute paths remain blocked and
C1/C2/C3 stay sealed.
