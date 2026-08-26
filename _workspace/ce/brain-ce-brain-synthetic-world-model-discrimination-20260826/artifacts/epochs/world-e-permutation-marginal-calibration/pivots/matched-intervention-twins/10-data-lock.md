# Twin confirmation data lock

Status: COMPLETE

- Parent source is read-only and must match SHA-256
  `7589e09f1d647d78f6e0f315e09ff5af15730a05ae55e87b0928db7001184b60`.
- Fresh root seed and its derivation are frozen in `contract.md`.
- Population: worlds A--G, replicates 0--11, train 96, validation 48,
  confirmation 8 protocol blocks x 8 matched twins x 2 arms.
- Train/validation are generated before selection. Confirmation generation is a
  separate call permitted only after descriptor serialization.
- Each arm, twin contrast, coefficient set, split and descriptor has a SHA-256
  identity in the result receipt. Duplicate identities fail closed.
- No persistent raw state/input arrays are written.
