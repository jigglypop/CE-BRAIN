# Stage 0 data lock

Status: COMPLETE

No external biological dataset is used. Data are generated only by the seven
world definitions and seed derivation in `00-contract.md`.

- manual attachment SHA-256:
  `4a8080a7661aa97590b74733de7752a8604ad086f64eef3a36acab549c447730`
- worlds: `A,B,C,D,E,F,G`
- replicates per world: 12
- observed nodes: 8; hidden nodes in F: 24; samples per trajectory: 64
- train/validation/unseen trajectories: 96/48/48
- root seed: 26082600
- split families: train step/single-pulse; validation ramp/shifted-pulse;
  unseen chirp/paired-pulse with unseen intervals

Every generated array receives a SHA-256 over contiguous float64 bytes plus its
shape/dtype. Split hashes and every trajectory's state/input SHA-256 must be
disjoint and are serialized before fitting.
The unseen arrays may be generated and sealed with the others, but the fitting
API cannot receive them until winner serialization.
