# BA-SRM4 implementation validation

Status: COMPLETE

Focused command:

` .codex\hooks\python.cmd pytest _workspace\ce\brain-self-trajectory-human-eeg-robust-qc4-l3-20260824\artifacts\test_srm4_real_eeg.py -q -p no:cacheprovider `

Result: `4 passed in 0.25s`.

The checks cover sealed 10/20/70 allocation, finite transform/area, nonfinite
and zero-scale fail-closed behavior, and synthetic Markov-null versus injected
area identifiability. P0 receipt reports Markov gain `-0.15195925486423464` and
injected-area gain `0.7849503198649899`; it records no signal access and leaves
R0/R1/R2/C1/C2/C3 unopened. No full suite and no real EEG stage was run.
