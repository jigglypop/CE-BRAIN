# Contract: exact held-out dimension time-series execution

Status: COMPLETE

## Objective

Recompute complete-menu window scores and moving-block bootstrap winners directly
from supplied exact held-out observation vectors and a frozen exact projector
menu, then feed only generated summaries into the temporal stability protocol.

## Acceptance conditions

1. Every session supplies the full frozen dimension menu.
2. Every projector is exactly symmetric, idempotent, and has trace equal to rank.
3. Held-out reconstruction scores include a frozen complexity penalty and require
   unique winners without post-hoc tie breaking.
4. Every bootstrap index chunk is a valid cyclic consecutive moving block.
5. Aggregate raw-data rank agrees with the base complete-menu certificate.
6. Generated summaries, not caller rank summaries, enter DSTAB.
7. External bytes and projector-training provenance remain false.
