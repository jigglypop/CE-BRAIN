# BA-OBS-HPC2 author-code static receipt

Status: COMPLETE

Scope: hash and line-semantic verification of the already downloaded public Zenodo
archive. No `.eeg` voltage, endpoint, Nature Source Data, or network object was opened.

## Identity

- Zenodo archive MD5: `6feba89b7c49fd661b39b589e8d9624a`.
- `tss/preprocessing/run_ep_preproc.m` SHA-256:
  `626a7467f803c28302ad712b24b891752b013fc471fec7f0057d529fc7ff0729`.
- `tss/analysis/run_group_ep.m` SHA-256:
  `d4a0ad2cee828c60fb87f91fc63a9c81b3588c974335350ed5fce10f2ac38da4`.
- `tss/analysis/compare_p2p.m` SHA-256:
  `c6ab8439b109b0b9cf1c046a8045c9fe2be3df72222921a7450c5515cf8d486c`.

## Line-semantic audit

- `run_ep_preproc.m:1-2` declares four trailing QC/filter arguments in the order
  kurtosis threshold, z threshold, amplitude threshold, low-pass flag.
- `run_ep_preproc.m:47-59` computes amplitude, kurtosis, and trial-axis z masks;
  `:63-69` applies baseline afterward. This verifies artifact-before-baseline order.
- `run_group_ep.m:62-64` assigns the global intended values kurtosis `5`, z `5`,
  amplitude `500`.
- Normal TS calls `:72-81`, p20 call `:87-95`, and UC004/UC005 call `:101-109`
  supply all four trailing arguments in the declared order.
- The p17/p19 control call `:116-123` omits the kurtosis argument and therefore does
  not match the function signature. It cannot be executed literally as a valid
  four-argument threshold call.
- `run_group_ep.m:84` orders p20 candidates as D9, C1, C'1, D'10; `:91` selects
  positions 1, 2, and 3 for QC. The successor therefore uses D9/C1/C'1 jointly for
  clinical QC and retains the first ordered channel D9 as the endpoint.

## Frozen interpretation

The successor treats the p17/p19 omission as a public-code defect and adopts the
globally declared and otherwise consistently passed intended tuple `(5,5,500)` as an
explicit measurement axiom. This is not described as exact archived-script execution.
`MIN20` is also an analyst-declared reliability aperture, not a claim about the author
code. Any mismatch in the hashes above is `AUTHOR_QC_CALL_AMBIGUITY` before raw access.
