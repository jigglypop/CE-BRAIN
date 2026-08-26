# Stage 0 pre-execution audit

Status: COMPLETE

Scope: outcome-blind review before manifest sealing. Neither independent auditor
called `execute`, `_run_replicate_after_manifest`, `aggregate`, or unseen metrics.
Generation of the preregistered unseen arrays and their hashes is allowed by the
data lock; model selection used train and validation only.

## Provenance and isolation

- The predecessor CCEP run is provenance-only. Its measured effects, thresholds,
  and labels are absent from the synthetic generators and candidate selection.
- The manual attachment is bound by SHA-256
  `4a8080a7661aa97590b74733de7752a8604ad086f64eef3a36acab549c447730`.
- There was no manifest and no result receipt during either audit.

## Revision history

The first mathematics audit found outcome-independent design defects: World E
overflow, one World F coupling identity failure, weak D/G identifiability, an
incompatible draft margin, a non-operative overlap test, and a permutation
description that did not match code. The unsealed preregistration was revised.

The second draft still failed E/F class recovery. Before sealing, E was replaced
by an exactly representable finite-horizon polynomial generator and F by a
deterministic 24-hidden-node delay system. Direct premanifest replicate evaluation
was removed; `execute()` now fails closed without a verified manifest. No unseen
metric informed either redesign.

## Stable-snapshot findings

- All 84 generators are finite and identity-valid on the registered domain;
  maximum absolute generated state is `2.3530162760`.
- Every replicate has 192 unique trajectory hashes.
- F has `||Axh Ahx||_2 = 0.525` and full coupled spectral radius
  `0.8429089182`. G has lag-two norm `0.72` and companion spectral radius
  `0.9268362519`.
- Train/validation selection matches the expected class in 12/12 replicates for
  every world. Median margins are A `0.0024390357`, B `0.0057675282`,
  C `0.0318401738`, D `0.0621752497`, E `0.0037577647`,
  F `0.0389090390`, and G `0.0409970908`.
- World E is explicitly limited to registered-domain, 64-sample finite-horizon
  stability. No global nonlinear stability claim is made.
- Selection accepts train and validation only; winner serialization precedes
  the only unseen evaluation path.

## Frozen input hashes before this audit file

- `00-contract.md`: `e837e1a46ea832258d2579478970e3d36af0626a8fcf72b353fb091ca06cae1d`
- `artifacts/stage0_synthetic_discrimination.py`:
  `7589e09f1d647d78f6e0f315e09ff5af15730a05ae55e87b0928db7001184b60`
- `artifacts/test_stage0_synthetic_discrimination.py`:
  `7732a17a132148557dcc9af27114cfb4302802244db17ef3fcf1d0b0da728970`

Disposition: mathematical and capability P0s are cleared. The only reported
mechanical blocker was creation of this file and `21-preexecution-validation.md`;
both are required manifest inputs and must exist before sealing.
