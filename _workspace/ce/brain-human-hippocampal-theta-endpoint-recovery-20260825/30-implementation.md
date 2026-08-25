# Implementation

Status: COMPLETE

`ENDPOINT_RECOVERY1` is a read-only successor transaction. It binds all
predecessor artifacts, locks and code hashes before validating the terminal
`IMPLEMENTATION_STOP` record. It imports the frozen validator by file path,
uses its exact legacy validator-progress schema for pre-COMPLETE and COMPLETE
passes, and writes only successor progress/receipt artifacts. No loader,
producer, raw object, or network path is reachable.

The recovery receipt preserves rather than overwrites the predecessor STOP;
it establishes witness/result validator authority only.

Revision 1 makes a receipt explicitly content-only. `verify_authority` reloads
the frozen validator and accepts authority only when that receipt is bound by
an exact successor COMPLETE progress record; orphan or forged files are
invalid.

Revision 2 preserves the pre-COMPLETE and COMPLETE validator inputs as separate
immutable artifacts. Authority requires both artifacts, the content-only
receipt, and the final successor progress record; each is type-exactly checked
and both validator phases are rerun during verification.
