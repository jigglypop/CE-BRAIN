"""One-event development decoder smoke; no endpoint computation."""
from __future__ import annotations

import hashlib
import json
from typing import Any

import numpy as np

import id4_development_index_acquire as acquire
import id4_development_range_plan as planner
import id4_development_signal as signal


def run_sub1_lv1_event_smoke(transport: signal.RangeTransport, plan: dict[str, Any]) -> dict[str, Any]:
    if plan.get("subject") != "sub-1" or plan.get("snapshot") != planner.FROZEN_SNAPSHOT:
        raise ValueError("APPARATUS_DEVELOPMENT_SIGNAL_STOP:smoke plan")
    tsv: dict[str, bytes] = {}
    for name, path in acquire._tsv_paths("sub-1").items():
        body = transport.get(acquire._url(acquire.RAW_PREFIX, path), timeout=acquire.TIMEOUT_SECONDS,
                             max_bytes=acquire.MAX_TSV_BYTES)
        if hashlib.sha256(body).hexdigest() != plan["tsv_sha256"][name]:
            raise RuntimeError("APPARATUS_DEVELOPMENT_SIGNAL_STOP:smoke TSV")
        tsv[name] = body
    table = planner.development_event_table(snapshot=planner.FROZEN_SNAPSHOT, subject="sub-1",
                                            events_tsv=tsv["events"].decode(),
                                            channels_tsv=tsv["channels"].decode(),
                                            electrodes_tsv=tsv["electrodes"].decode(), fs_hz=2048)
    event = table[0]
    provenance = dict(next(row for row in plan["channel_provenance"] if row["channel"] == "LV1"))
    provenance.update(tmet_sha256="08f3b60859166f24bc44978de804300c9c30f3b0d277ccddb5a16a70171f8e2e",
                      tmet_bytes=16384)
    metadata = signal.acquire_channel_metadata(subject="sub-1", channel="LV1", expected=provenance,
                                               transport=transport)
    def summarize(values: np.ndarray, _events: Any) -> dict[str, Any]:
        canonical = np.ascontiguousarray(values, dtype=np.float64)
        return {"shape": list(values.shape), "physical_values_sha256": hashlib.sha256(canonical.tobytes()).hexdigest(),
                "min_microvolts": float(values.min()), "max_microvolts": float(values.max()),
                "mean_microvolts": float(values.mean())}
    summary, range_receipt = signal.process_eligible_event_windows(metadata, [event], transport=transport,
                                                                  processor=summarize)
    return {"status": "PASS_DEVELOPMENT_EVENT_DECODER_SMOKE", "scope": "sub-1-LV1-one-eligible-event-only",
            "snapshot": planner.FROZEN_SNAPSHOT, "commit": acquire.COMMIT,
            "event": {key: event[key] for key in ("source_row", "node", "center_sample", "trial_index", "half", "acquisition")},
            **summary, "range_receipt": range_receipt,
            "endpoint_evidence": False, "development_gate_computed": False, "sub5_opened": False,
            "confirmation_opened": False, "persistent_raw_bytes": 0, "cleanup": range_receipt["cleanup"]}


def compact_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, indent=2)
