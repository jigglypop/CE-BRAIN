# Stage 2 timestamp-gap apparatus amendment

Status: COMPLETE / OUTCOME_BLIND / PRE_MANIFEST

## Preserved stop

The first local `--schema-only` invocation stopped with
`STAGE2_APPARATUS_STOP: timestamp rate or uniformity`. No
`ElectricalSeriesEEG/data` sample was opened, no raw-bound schema receipt was
written and no manifest or scientific result existed.

## Metadata-only diagnosis

- timestamp count: `6,217,728`;
- median interval: `0.0004000001291615263 s` (`2499.9991927407214 Hz`);
- one long interval after index `125307`:
  `0.0008000018083862415 s`, ratio `2.000003875156721`;
- maximum relative jitter after excluding that interval:
  `1.8729616249713033e-05`;
- gap-left time: `456.5734399981916 s`;
- first trial: `590.01039 s`, separation `133.43695000180844 s`.

## Frozen successor rule

Accept exactly one interval greater than `1.5*median` and require its index to
be `125307` and its ratio to lie in `[1.9999,2.0001]`. Require every other
interval's relative deviation from the median to be at most `2e-5`. Begin the
continuous filtering segment at index `125308`; convert all trial origins to
segment-relative indices. Require the earliest eligible stimulus to be at least
120 seconds after the segment begins. Artifact replacement, filtering,
baseline, response grid, split, statistics and decision rules are unchanged.

This is a source-apparatus amendment based only on timestamps and trial times.
It does not authorize any endpoint-dependent change.
