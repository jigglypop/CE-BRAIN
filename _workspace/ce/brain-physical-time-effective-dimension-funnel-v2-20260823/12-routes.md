# BA-SRM9 route decision

Status: COMPLETE

| Route | status | reason |
|---|---|---|
| BA-SRM9 dense JUMP mixing | `SELECTED_SUCCESSOR / PRE_FIXTURE` | Repairs only the zero observed-prefix variance caused by BA-SRM8 JUMP's sparse rank-$2\to8$ coordinate support. |
| BA-SRM8 F2-A result | `NOT_INHERITED` | No completed F2-A receipt exists. |
| F0-v3 / F1-v6 | `CARRIED_BY_EXACT_RECEIPT` | Allowed only when all frozen predecessor and promoted-array hashes match. |
| F2-B/C/D, F2R, behavior/model/real endpoint | `UNOPENED` | Fixture, math audit, status audit, then a new F2-A receipt are required first. |

The stop rule is intentionally narrow: a failed BA-SRM9 fixture stops this successor without revising BA-SRM8 into a success. `MISS50` remains descriptive only. No biological, consciousness, hippocampal, synaptic-edge, loop, or AGI interpretation is admitted.
