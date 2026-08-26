"""Rebuild the frozen sub-1 v4 signal-blind development index plan."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import id4_development_index_acquire as acquire


EXPECTED_TSV_SHA256 = {
    "channels": "0ba4731319483daa27503f75a67677418fc8ef696faa5249d032ea3e93cf952a",
    "electrodes": "03e3cf0cd89cf61ae2cf161d7e13aec5f01ade6e0e0e754a9d2f9754be33b3fe",
    "events": "f364e938ec1a7df35032a308b8309c37f55f6b50f6be2185abeaa14d369d90d2",
}
EXPECTED_PLAN_SHA256 = "cdb3385fcd936e6835e9e0ac2dd36d8af6c40f0be44f5307d5fdf1753d16be2b"
EXPECTED_CHECKPOINT_SHA256 = "54d6ec62cda6c5c3014ac2e10b9fbf7216ce8648c73595c5712dff0119faafa6"
EXPECTED_TSV_BYTES = 73_848


def _sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _plan_from_complete_checkpoint(checkpoint: Path) -> dict:
    body = checkpoint.read_bytes()
    if _sha(body) != EXPECTED_CHECKPOINT_SHA256:
        raise RuntimeError("APPARATUS_INDEX_ACQUIRE_STOP:complete checkpoint hash")
    state = json.loads(body)
    if state.get("status") != "COMPLETE" or len(state.get("completed", [])) != 154:
        raise RuntimeError("APPARATUS_INDEX_ACQUIRE_STOP:complete checkpoint state")
    completed = sorted(state["completed"], key=lambda row: row["channel"])
    return {
        "snapshot": state["snapshot"], "commit": state["commit"], "subject": state["subject"],
        "precision_convention": state["precision_convention"],
        "precision_convention_version": state["precision_convention_version"],
        "shared_first_uutc": state["shared_first_uutc"],
        "shared_start_sample": state["shared_start_sample"],
        "tsv_sha256": state["tsv_sha256"],
        "channel_provenance": [entry["provenance"] for entry in completed],
        "planned_ranges": completed,
        "aggregate": {
            "verified_unique_tsv_bytes": EXPECTED_TSV_BYTES,
            "verified_unique_pointer_bytes": sum(entry["pointer_bytes"] for entry in completed),
            "verified_unique_tidx_bytes": sum(entry["provenance"]["tidx_bytes"] for entry in completed),
            "planned_tdat_bytes": sum(entry["planned_tdat_bytes"] for entry in completed),
            "planned_persistent_raw_bytes": 0,
            "wire_transfer_bytes_status": "NOT_CLAIMED_RETRIES_AND_RESUME",
        },
        "signal_accessed": False, "development_index_opened": True,
        "development_signal_opened": False, "confirmation_opened": False,
        "concurrency": acquire.CONCURRENCY,
        "retry_policy": {"max_attempts": acquire.MAX_ATTEMPTS, "transient_only": True,
                         "backoff_seconds": list(acquire.BACKOFF_SECONDS)},
    }


def main() -> None:
    root = Path(__file__).parent
    checkpoint = root / "development-index-checkpoint-sub-1-v4.json"
    if checkpoint.exists() and _sha(checkpoint.read_bytes()) == EXPECTED_CHECKPOINT_SHA256:
        plan = _plan_from_complete_checkpoint(checkpoint)
    else:
        plan = acquire.acquire_development_index(
            snapshot=acquire.FROZEN_SNAPSHOT,
            subject="sub-1",
            expected_tsv_sha256=EXPECTED_TSV_SHA256,
            transport=acquire.CurlTransport(),
            checkpoint_path=checkpoint,
            progress=lambda count, total, channel: print(
                f"PROGRESS {count}/{total} {channel}", flush=True
            ),
        )
    candidates: dict[str, bytes] = {}
    for sort_keys in (False, True):
        for indent in (None, 0, 1, 2, 4):
            for newline in (False, True):
                name = f"sort={sort_keys},indent={indent},newline={newline}"
                text = json.dumps(plan, sort_keys=sort_keys, indent=indent)
                logical = text + ("\n" if newline else "")
                candidates[name + ",eol=LF"] = logical.encode()
                candidates[name + ",eol=CRLF"] = logical.replace("\n", "\r\n").encode()
        for newline in (False, True):
            name = f"sort={sort_keys},compact=True,newline={newline}"
            text = json.dumps(plan, sort_keys=sort_keys, separators=(",", ":"))
            logical = text + ("\n" if newline else "")
            candidates[name + ",eol=LF"] = logical.encode()
            candidates[name + ",eol=CRLF"] = logical.replace("\n", "\r\n").encode()
    matching = [(name, body) for name, body in candidates.items() if _sha(body) == EXPECTED_PLAN_SHA256]
    if len(matching) != 1:
        hashes = {name: _sha(body) for name, body in candidates.items()}
        raise RuntimeError(f"APPARATUS_INDEX_ACQUIRE_STOP:canonical receipt mismatch:{hashes}")
    encoding, body = matching[0]
    output = root / "development-index-plan-sub-1-v4.json"
    temporary = output.with_suffix(".json.tmp")
    temporary.write_bytes(body)
    temporary.replace(output)
    print("status=PASS_REBUILT_SUB1_V4_INDEX_PLAN")
    print(f"encoding={encoding}")
    print(f"plan={output}")
    print(f"plan_sha256={_sha(body)}")


if __name__ == "__main__":
    main()
